from odoo import api, fields, models


class GteLegacyMixin(models.AbstractModel):
    """Shared fields for every Construction construction-control record.

    Carries the legacy-source identifier and the migration-completeness
    flag required by the remediation safeguards. Never fabricate values:
    when mandatory data is missing, set migration_incomplete and list the
    missing fields instead.
    """

    _name = "cs.legacy.mixin"
    _description = "Construction Legacy Source Mixin"

    legacy_source_id = fields.Char(
        string="Legacy Source ID", copy=False, index=True,
        help="Identifier of the originating SmartBuild / legacy Odoo record.")
    origin_task_id = fields.Many2one(
        "project.task", string="Original Task", copy=False, ondelete="set null",
        help="Tagged project.task this record was migrated from. The task is "
             "kept (archived after reconciliation), never deleted.")
    migration_incomplete = fields.Boolean(copy=False, default=False, index=True)
    migration_missing_fields = fields.Text(copy=False)

    @api.model
    def _cs_next_number(self, project, code, prefix):
        """Project-scoped sequence producing {project_code}-{TYPE}-###
        (e.g. 0476-RFI-001). Created on first use; prefix follows the
        project code if it changes. Idempotent."""
        seq_code = "%s.p%s" % (code, project.id)
        full_prefix = "%s-%s-" % (project.cs_code or "PRJ", prefix)
        seq = self.env["ir.sequence"].sudo().search(
            [("code", "=", seq_code)], limit=1)
        if not seq:
            seq = self.env["ir.sequence"].sudo().create({
                "name": "%s %s" % (prefix, project.display_name),
                "code": seq_code,
                "prefix": full_prefix,
                "padding": 3,
                "company_id": project.company_id.id or False,
            })
        elif seq.prefix != full_prefix:
            seq.prefix = full_prefix
        return seq.next_by_id()

    def _cs_unlink_guard(self, deletable_states=("draft", "cancelled")):
        from odoo.exceptions import ValidationError
        for rec in self:
            if rec.state not in deletable_states:
                raise ValidationError(
                    "%s is issued/active and cannot be deleted. Archive it "
                    "instead (a Construction Administrator can archive from "
                    "the record's action menu)." % rec.display_name)

    def action_open_reason_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.reason.wizard",
            "view_mode": "form", "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_action": self.env.context.get("cs_action", "cancel"),
            },
        }
