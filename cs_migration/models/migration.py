import logging
import re
from datetime import datetime

from odoo import fields, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

RFI_MANDATORY = ["question", "raised_by_id", "addressed_to_id", "date_raised",
                 "response", "attachments"]
CO_MANDATORY = ["scope", "line_ids", "amount_proposed", "date_submitted",
                "client_response", "attachments"]
SUB_MANDATORY = ["supplier_id", "reviewer_id", "revision_ids", "date_submitted",
                 "attachments"]


class GteMigrationWizard(models.TransientModel):
    """Converts tagged project tasks into dedicated Construction control records.

    Safeguards implemented:
    - Idempotent: keyed on ir.model.data external IDs; re-running updates
      nothing and creates no duplicates.
    - Non-destructive: original tasks are never modified, archived or deleted.
    - No fabrication: missing mandatory data sets migration_incomplete and
      lists the missing fields.
    - Dry-run mode reports without writing.
    """

    _name = "cs.migration.wizard"
    _description = "Construction Tagged-Task Migration"

    dry_run = fields.Boolean(default=True)
    result = fields.Text(readonly=True)

    # ------------------------------------------------------------------
    def _xmlid_exists(self, name):
        return bool(self.env["ir.model.data"].sudo().search_count(
            [("module", "=", "__cs_migration__"), ("name", "=", name)]))

    def _register_xmlid(self, name, record):
        self.env["ir.model.data"].sudo().create({
            "module": "__cs_migration__", "name": name,
            "model": record._name, "res_id": record.id, "noupdate": True})

    @staticmethod
    def _parse_desc(desc_html):
        text = html2plaintext(desc_html or "")
        out = {"text": text}
        m = re.search(r"SmartBuild\s+RFI\s*#?\s*([\w-]+)", text, re.I)
        if m:
            out["sb_rfi"] = m.group(1)
        m = re.search(r"SmartBuild\s+Submittal[^\d]*(\d{6})", text, re.I)
        if m:
            out["sb_spec"] = m.group(1)
        m = re.search(r"Received:\s*(\d{2}/\d{2}/\d{4})", text)
        if m:
            try:
                out["received"] = datetime.strptime(m.group(1), "%m/%d/%Y").date()
            except ValueError:
                pass
        m = re.search(r"Next step:\s*([^\n]+)", text)
        if m:
            out["next_step"] = m.group(1).strip()
        return out

    def _common_vals(self, task, parsed, kind):
        legacy = parsed.get("sb_rfi") or parsed.get("sb_spec") or ""
        return {
            "project_id": task.project_id.id,
            "origin_task_id": task.id,
            "legacy_source_id": ("SB-%s-%s" % (kind, legacy)) if legacy
                                 else ("task-%s" % task.id),
            "migration_incomplete": True,
        }

    def _post_create(self, record, task, missing):
        record.migration_missing_fields = ", ".join(missing)
        followers = task.message_partner_ids
        if followers:
            record.message_subscribe(partner_ids=followers.ids)
        record.message_post(body=(
            "Migrated from task #%s (%s). Missing mandatory data: %s. "
            "To be enriched from the SmartBuild export — do not fabricate."
            % (task.id, task.display_name, ", ".join(missing) or "none")))

    # ------------------------------------------------------------------
    def action_run(self):
        self.ensure_one()
        Task = self.env["project.task"]
        Tag = self.env["project.tags"]
        stats = {}
        lines = []

        def tag_tasks(tag_name):
            tag = Tag.search([("name", "=", tag_name)], limit=1)
            return Task.search([("tag_ids", "in", tag.ids)]) if tag else Task

        # --- RFIs -----------------------------------------------------
        created = skipped = 0
        for task in tag_tasks("RFI"):
            xid = "rfi_task_%s" % task.id
            if self._xmlid_exists(xid):
                skipped += 1
                continue
            parsed = self._parse_desc(task.description)
            if not self.dry_run:
                vals = self._common_vals(task, parsed, "RFI")
                vals.update({
                    "subject": task.name,
                    "question": task.description or False,
                    "date_raised": parsed.get("received"),
                    "date_required": task.date_deadline
                        and fields.Date.to_date(task.date_deadline),
                    "coordinator_id": task.user_ids[:1].id or self.env.user.id,
                    "state": "closed" if (task.stage_id.name or "") == "Completed"
                             else "open",
                })
                rec = self.env["cs.rfi"].create(vals)
                missing = [f for f in RFI_MANDATORY
                           if f in ("attachments",) or not rec[f]]
                self._post_create(rec, task, missing)
                self._register_xmlid(xid, rec)
            created += 1
        stats["RFI"] = (created, skipped)

        # --- Change Orders -------------------------------------------
        created = skipped = 0
        for task in tag_tasks("Change Order"):
            xid = "co_task_%s" % task.id
            if self._xmlid_exists(xid):
                skipped += 1
                continue
            parsed = self._parse_desc(task.description)
            m = re.search(r"CCO\s*#?\s*(\d+)", task.name or "", re.I)
            if not self.dry_run:
                vals = self._common_vals(task, parsed, "CO")
                if m:
                    vals["legacy_source_id"] = "SB-CO-CCO%s" % m.group(1)
                vals.update({
                    "title": task.name,
                    "scope": task.description or False,
                    "date_quote": parsed.get("received"),
                    "date_required": task.date_deadline
                        and fields.Date.to_date(task.date_deadline),
                    "user_id": task.user_ids[:1].id or self.env.user.id,
                    "state": "closed" if (task.stage_id.name or "") == "Completed"
                             else "draft",
                })
                rec = self.env["cs.change.order"].create(vals)
                missing = [f for f in CO_MANDATORY
                           if f in ("attachments",) or not rec[f]]
                self._post_create(rec, task, missing)
                self._register_xmlid(xid, rec)
            created += 1
        stats["Change Order"] = (created, skipped)

        # --- Submittals ----------------------------------------------
        created = skipped = 0
        for task in tag_tasks("Submittal"):
            xid = "sub_task_%s" % task.id
            if self._xmlid_exists(xid):
                skipped += 1
                continue
            parsed = self._parse_desc(task.description)
            if not self.dry_run:
                vals = self._common_vals(task, parsed, "SUB")
                spec = False
                if parsed.get("sb_spec"):
                    spec = self.env["cs.submittal.spec"].search(
                        [("number", "=", parsed["sb_spec"])], limit=1)
                vals.update({
                    "title": task.name,
                    "spec_section": parsed.get("sb_spec") or False,
                    "spec_id": spec and spec.id,
                    "date_received": parsed.get("received"),
                    "date_required_submit": task.date_deadline
                        and fields.Date.to_date(task.date_deadline),
                    "coordinator_id": task.user_ids[:1].id or self.env.user.id,
                    "state": "closed" if (task.stage_id.name or "") == "Completed"
                             else "requested",
                })
                rec = self.env["cs.submittal"].create(vals)
                missing = [f for f in SUB_MANDATORY
                           if f in ("attachments",) or not rec[f]]
                self._post_create(rec, task, missing)
                self._register_xmlid(xid, rec)
            created += 1
        stats["Submittal"] = (created, skipped)

        # --- Standard submittal specs from Studio model ---------------
        created = skipped = 0
        if "x_submittal_spec" in self.env:
            for old in self.env["x_submittal_spec"].sudo().search([]):
                xid = "spec_%s" % old.id
                if self._xmlid_exists(xid):
                    skipped += 1
                    continue
                if not self.dry_run:
                    number = getattr(old, "x_number", False) or \
                        getattr(old, "x_name", False) or str(old.id)
                    rec = self.env["cs.submittal.spec"].create({
                        "number": str(number),
                        "name": getattr(old, "x_name", False) or str(number),
                        "legacy_source_id": "x_submittal_spec-%s" % old.id,
                    })
                    self._register_xmlid(xid, rec)
                created += 1
        stats["Submittal Spec"] = (created, skipped)

        mode = "DRY RUN — nothing written" if self.dry_run else "EXECUTED"
        lines.append("Migration %s at %s" % (mode, fields.Datetime.now()))
        for k, (c, s) in stats.items():
            lines.append("%s: %s to migrate/migrated, %s already done (skipped)"
                         % (k, c, s))
        lines.append("Original tasks untouched. Archive only after "
                     "reconciliation sign-off.")
        self.result = "\n".join(lines)
        _logger.info("Construction migration: %s", self.result)
        return {
            "type": "ir.actions.act_window", "res_model": self._name,
            "res_id": self.id, "view_mode": "form", "target": "new",
        }
