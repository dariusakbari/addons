from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CsDelayEvent(models.Model):
    _name = "cs.delay.event"
    _description = "Delay Event"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    date = fields.Date(string="Start Date", required=True,
                       default=fields.Date.context_today, tracking=True)
    date_end = fields.Date(string="End Date", tracking=True)
    cause = fields.Selection([
        ("rfi", "Awaiting RFI Response"), ("change", "Change Order"),
        ("weather", "Weather"), ("access", "Site Access"),
        ("material", "Material / Delivery"), ("owner", "Owner Directed"),
        ("design", "Design / Consultant"), ("labour", "Labour"),
        ("other", "Other")], required=True, default="other", tracking=True)
    days_impact = fields.Integer(string="Schedule Impact (days)", tracking=True)
    critical_path = fields.Boolean(string="On Critical Path", tracking=True,
                                   help="Does this delay push the project "
                                        "completion date?")
    delay_type = fields.Selection([
        ("exc_comp", "Excusable & Compensable"),
        ("exc_noncomp", "Excusable, Non-Compensable"),
        ("non_exc", "Non-Excusable")],
        string="Entitlement", tracking=True,
        help="Contractual classification: compensable delays carry a time "
             "and money claim; excusable non-compensable carry time only; "
             "non-excusable are the contractor's own risk.")
    description = fields.Text()

    # Responsibility
    responsible_id = fields.Many2one(
        "res.partner", string="Responsible Party", tracking=True,
        help="The party whose action or inaction caused the delay.")
    liable_party = fields.Selection([
        ("owner", "Owner"), ("consultant", "Consultant / Design"),
        ("contractor", "Contractor (us)"), ("subcontractor", "Subcontractor"),
        ("supplier", "Supplier"), ("force_majeure", "Force Majeure / Weather"),
        ("shared", "Shared"), ("tbd", "To Be Determined")],
        string="Liability", default="tbd", tracking=True)

    # Mitigation / recovery
    mitigation_plan = fields.Text(
        string="Mitigation Plan",
        help="Steps to reduce or absorb the delay's impact.")
    recovery_plan = fields.Text(
        string="Recovery Plan",
        help="Steps to recover lost time (resequencing, acceleration, etc.).")

    # Contractual notice
    notice_required = fields.Boolean(
        string="Notice Required", default=True,
        help="Does the contract require formal notice of this delay?")
    notice_recipient_id = fields.Many2one("res.partner",
                                          string="Notice To")
    notice_deadline = fields.Date(
        string="Notice Deadline",
        help="Contractual deadline to serve notice of the delay.")
    notice_given = fields.Boolean(readonly=True, copy=False, tracking=True)
    date_notice_given = fields.Date(readonly=True, copy=False)
    notice_overdue = fields.Boolean(compute="_compute_notice_overdue")

    # Cost impact
    cost_impact = fields.Selection([
        ("none", "None"), ("tbd", "To Be Determined"), ("yes", "Yes")],
        default="tbd", tracking=True)
    cost_amount = fields.Monetary(currency_field="currency_id", tracking=True)

    rfi_id = fields.Many2one("cs.rfi", string="Related RFI")
    change_order_id = fields.Many2one("cs.change.order", string="Related Change")
    daily_log_id = fields.Many2one("cs.daily.log", string="From Daily Log")
    field_issue_id = fields.Many2one("cs.field.issue", string="From Field Issue")
    state = fields.Selection([
        ("open", "Open"), ("mitigated", "Mitigated"),
        ("closed", "Closed")], default="open", tracking=True, index=True)

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = (rec.company_id.currency_id
                               or rec.env.company.currency_id)

    @api.depends("notice_required", "notice_given", "notice_deadline", "state")
    def _compute_notice_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.notice_overdue = bool(
                rec.notice_required and not rec.notice_given
                and rec.state != "closed" and rec.notice_deadline
                and rec.notice_deadline < today)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.delay.event", "DLY")
        return super().create(vals_list)

    def action_give_notice(self):
        for rec in self:
            if not rec.notice_recipient_id:
                raise ValidationError(
                    "%s: set who the notice goes to before recording it."
                    % rec.name)
            rec.write({"notice_given": True,
                       "date_notice_given": fields.Date.context_today(self)})

    def action_mitigate(self):
        for rec in self:
            if not rec.mitigation_plan:
                raise ValidationError(
                    "%s: record a mitigation plan before marking it mitigated."
                    % rec.name)
        self.write({"state": "mitigated"})

    def action_close(self):
        self.write({"state": "closed"})
