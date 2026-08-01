from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Shared selection so template questions and report answers stay in lock-step.
QTYPE = [
    ("passfailna", "Pass / Fail / N-A"),
    ("yesno", "Yes / No / N-A"),
    ("rating", "Rating (1-5)"),
    ("number", "Number"),
    ("text", "Text / Observation"),
]


class CsSafetyTemplate(models.Model):
    """A reusable, version-controlled safety report template.

    A template is edited while in Draft, then Published (which locks its
    structure so historical reports stay reproducible). Editing a published
    template is done by creating a new version, which supersedes the old one.
    """

    _name = "cs.safety.template"
    _description = "Safety Report Template"
    _inherit = ["cs.qr.mixin"]
    _order = "name, version desc"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(help="Short code used in report numbering, e.g. TBT, INSP.")
    template_type = fields.Selection([
        ("toolbox", "Toolbox Talk"),
        ("inspection", "Inspection"),
        ("hazard", "Hazard Assessment"),
        ("checklist", "Site Checklist"),
        ("other", "Other")], required=True, default="checklist")
    version = fields.Integer(default=1, readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived")], default="draft", copy=False, index=True)
    active = fields.Boolean(default=True)
    intro = fields.Html(
        string="Instructions",
        help="Optional guidance shown at the top of the report and PDF.")
    section_ids = fields.One2many(
        "cs.safety.template.section", "template_id", copy=True)
    question_count = fields.Integer(compute="_compute_counts", store=True)
    section_count = fields.Integer(compute="_compute_counts", store=True)
    report_count = fields.Integer(compute="_compute_report_count")
    supersedes_id = fields.Many2one(
        "cs.safety.template", string="Previous Version", readonly=True,
        copy=False, ondelete="set null")
    superseded_by_id = fields.Many2one(
        "cs.safety.template", string="Replaced By", readonly=True, copy=False)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company)
    require_photo_default = fields.Boolean(
        string="Photos required by default",
        help="When ticked, new questions default to requiring a photo.")

    @api.depends("section_ids", "section_ids.question_ids")
    def _compute_counts(self):
        for tpl in self:
            tpl_sections = tpl.section_ids
            tpl.section_count = len(tpl_sections)
            tpl.question_count = sum(len(s.question_ids) for s in tpl_sections)

    def _compute_report_count(self):
        Report = self.env["cs.safety.report"]
        for tpl in self:
            tpl.report_count = Report.search_count(
                [("template_id", "=", tpl.id)]) if isinstance(tpl.id, int) else 0

    # ------------------------------------------------------------------ guards
    def _check_editable(self):
        for tpl in self:
            if tpl.state != "draft":
                raise ValidationError(
                    "'%s' is %s. Published templates are locked so past "
                    "reports stay reproducible — use 'New Version' to change "
                    "it." % (tpl.name, dict(self._fields["state"].selection)[
                        tpl.state].lower()))

    def write(self, vals):
        # Allow lifecycle/administrative fields on a published template, block
        # structural edits.
        structural = set(vals) - {"state", "active", "superseded_by_id",
                                  "supersedes_id"}
        if structural:
            self.filtered(lambda t: t.state != "draft")._check_editable()
        return super().write(vals)

    # --------------------------------------------------------------- lifecycle
    def action_publish(self):
        for tpl in self:
            if tpl.state != "draft":
                continue
            if not tpl.section_ids or not tpl.question_count:
                raise ValidationError(
                    "Add at least one section with one question before "
                    "publishing '%s'." % tpl.name)
            empty = tpl.section_ids.filtered(lambda s: not s.question_ids)
            if empty:
                raise ValidationError(
                    "These sections have no questions: %s."
                    % ", ".join(empty.mapped("name")))
            tpl.state = "published"
            if tpl.supersedes_id and tpl.supersedes_id.state == "published":
                tpl.supersedes_id.write({"state": "archived",
                                         "superseded_by_id": tpl.id})

    def action_archive_template(self):
        self.write({"state": "archived", "active": False})

    def action_restore_draft(self):
        # Only for archived templates that were never used, to keep history
        # honest; otherwise make a new version.
        for tpl in self:
            if tpl.report_count:
                raise ValidationError(
                    "'%s' already has reports; create a new version instead "
                    "of editing it." % tpl.name)
        self.write({"state": "draft", "active": True})

    def action_new_version(self):
        self.ensure_one()
        new = self.copy({
            "version": self.version + 1,
            "state": "draft",
            "active": True,
            "supersedes_id": self.id,
            "name": self.name,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.safety.template",
            "res_id": new.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_reports(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reports",
            "res_model": "cs.safety.report",
            "view_mode": "list,form",
            "domain": [("template_id", "=", self.id)],
            "context": {"default_template_id": self.id},
        }

    # -------------------------------------------------------------------- QR
    def _qr_target_url(self, project_id=False):
        base = self.env["ir.config_parameter"].sudo().get_param(
            "web.base.url") or ""
        url = "%s/safety/new?template_id=%s" % (base, self.id)
        if project_id:
            url += "&project_id=%s" % project_id
        return url

    def _compute_qr_image(self):
        # Override the mixin: point the QR at the "new report" deep link
        # rather than at the template form.
        from odoo.addons.cs_hse.models.registers import _cs_make_qr
        for tpl in self:
            if isinstance(tpl.id, int):
                tpl.qr_image = _cs_make_qr(tpl._qr_target_url())
            else:
                tpl.qr_image = False

    def action_print_qr(self):
        """Open the QR poster wizard (optionally scoped to a project)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Safety QR Poster",
            "res_model": "cs.safety.qr.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_template_id": self.id},
        }


class CsSafetyTemplateSection(models.Model):
    _name = "cs.safety.template.section"
    _description = "Safety Template Section"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "cs.safety.template", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    instruction = fields.Text(help="Optional note shown under the section title.")
    question_ids = fields.One2many(
        "cs.safety.template.question", "section_id", copy=True)

    def _guard(self):
        self.mapped("template_id")._check_editable()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._guard()
        return records

    def write(self, vals):
        self._guard()
        res = super().write(vals)
        self._guard()
        return res

    def unlink(self):
        self._guard()
        return super().unlink()


class CsSafetyTemplateQuestion(models.Model):
    _name = "cs.safety.template.question"
    _description = "Safety Template Question"
    _order = "sequence, id"

    section_id = fields.Many2one(
        "cs.safety.template.section", required=True, ondelete="cascade",
        index=True)
    template_id = fields.Many2one(
        related="section_id.template_id", store=True, index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Question / Item", required=True)
    help_text = fields.Char(string="Guidance")
    qtype = fields.Selection(QTYPE, string="Answer Type", required=True,
                             default="passfailna")
    required = fields.Boolean(default=True)
    requires_photo = fields.Boolean(string="Photo Required")
    corrective_on_fail = fields.Boolean(
        string="Corrective Action if Failed", default=True,
        help="Require a written corrective action when the answer is a "
             "Fail / No.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped("template_id")._check_editable()
        return records

    def write(self, vals):
        self.mapped("template_id")._check_editable()
        res = super().write(vals)
        self.mapped("template_id")._check_editable()
        return res

    def unlink(self):
        self.mapped("template_id")._check_editable()
        return super().unlink()
