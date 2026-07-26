from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CsSiteInstruction(models.Model):
    """Formal Field Memo / Site Instruction — a numbered, issued, acknowledged
    field-direction record (distinct from internal Field Issues)."""
    _name = "cs.site.instruction"
    _description = "Field Memo / Site Instruction"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "project_id, name desc"

    name = fields.Char(string="Instruction No.", readonly=True, copy=False,
                       default="New")
    title = fields.Char(required=True, tracking=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency",
                                  compute="_compute_currency_id")
    instruction = fields.Html(string="Instruction / Direction")
    issued_by_id = fields.Many2one("res.users", string="Issued By",
                                   default=lambda self: self.env.user,
                                   tracking=True)
    issued_to_id = fields.Many2one("res.partner", string="Issued To",
                                   tracking=True,
                                   help="Contractor / party receiving the direction.")
    date_issued = fields.Date(tracking=True)
    required_by = fields.Date(string="Action Required By", tracking=True)
    acknowledged_by = fields.Char(tracking=True)
    date_acknowledged = fields.Date(tracking=True)
    response = fields.Html(string="Acknowledgement / Response")
    cost_impact = fields.Selection([
        ("none", "None"), ("tbd", "To Be Determined"), ("yes", "Yes")],
        default="none", tracking=True)
    cost_amount = fields.Monetary(currency_field="currency_id")
    schedule_impact_days = fields.Integer(string="Schedule Impact (days)",
                                          tracking=True)
    origin_rfi_id = fields.Many2one("cs.rfi", string="Related RFI", copy=False)
    change_order_id = fields.Many2one("cs.change.order",
                                      string="Resulting Change Order",
                                      copy=False)
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ("draft", "Draft"), ("issued", "Issued"),
        ("acknowledged", "Acknowledged"), ("closed", "Closed"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    _si_number_project_uniq = models.Constraint(
        "unique(project_id, name)",
        "Instruction number must be unique per project.",
    )

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = (rec.company_id.currency_id
                               or rec.env.company.currency_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(
                    project, "cs.site.instruction", "SI")
        return super().create(vals_list)

    def _set_state(self, allowed_from, new_state, extra=None):
        for rec in self:
            if rec.state not in allowed_from:
                raise ValidationError(
                    "Invalid transition %s -> %s on %s"
                    % (rec.state, new_state, rec.name))
            rec.write(dict(extra or {}, state=new_state))

    def action_issue(self):
        for rec in self:
            missing = []
            if not rec.instruction:
                missing.append("instruction text")
            if not rec.issued_to_id:
                missing.append("recipient (Issued To)")
            if missing:
                raise ValidationError(
                    "%s cannot be issued. Missing: %s."
                    % (rec.name, ", ".join(missing)))
        self._set_state(("draft",), "issued",
                        {"date_issued": fields.Date.context_today(self)})

    def action_acknowledge(self):
        for rec in self:
            if not rec.acknowledged_by:
                raise ValidationError(
                    "%s needs who acknowledged it before recording "
                    "acknowledgement." % rec.name)
            if not rec.date_acknowledged:
                rec.date_acknowledged = fields.Date.context_today(self)
        self._set_state(("issued",), "acknowledged")

    def action_close(self):
        self._set_state(("acknowledged", "issued"), "closed")

    def action_cancel(self):
        self._set_state(("draft", "issued"), "cancelled")

    def action_reset(self):
        if not self.env.user.has_group("cs_core.group_cs_pm"):
            raise ValidationError(
                "Only project managers can reopen an instruction.")
        self._set_state(("cancelled", "closed"), "draft")

    def action_make_change_order(self):
        self.ensure_one()
        co = self.env["cs.change.order"].create({
            "project_id": self.project_id.id,
            "title": "From %s: %s" % (self.name, self.title or ""),
            "source_type": "site",
        })
        self.change_order_id = co
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.change.order",
            "res_id": co.id, "view_mode": "form",
        }

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()
