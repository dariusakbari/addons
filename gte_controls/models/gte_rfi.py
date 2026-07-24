from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteRfi(models.Model):
    _name = "gte.rfi"
    _description = "Request for Information"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "project_id, name desc"

    name = fields.Char(string="RFI Number", readonly=True, copy=False, default="New")
    subject = fields.Char(required=True, tracking=True)
    question = fields.Html(string="Full Question")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    task_ids = fields.Many2many("project.task", string="Related Tasks")
    raised_by_id = fields.Many2one("res.partner", string="Raised By", tracking=True)
    addressed_to_id = fields.Many2one("res.partner", string="Addressed To", tracking=True)
    coordinator_id = fields.Many2one("res.users", string="Responsible Coordinator",
                                     default=lambda self: self.env.user, tracking=True)
    date_raised = fields.Date(tracking=True)
    date_required = fields.Date(string="Required Response Date", tracking=True)
    date_answered = fields.Date(tracking=True)
    date_distributed = fields.Date(tracking=True)
    drawing_refs = fields.Char(string="Drawing References")
    spec_refs = fields.Char(string="Specification References")
    response = fields.Html(string="Formal Response")
    distribution_ids = fields.Many2many("res.partner", "gte_rfi_distribution_rel",
                                        string="Distribution Recipients")
    cost_impact = fields.Selection(
        [("none", "No Cost Impact"), ("tbd", "To Be Determined"), ("yes", "Cost Impact")],
        default="tbd", tracking=True)
    cost_amount = fields.Monetary(currency_field="currency_id", tracking=True)
    schedule_impact = fields.Selection(
        [("none", "No Schedule Impact"), ("tbd", "To Be Determined"), ("yes", "Schedule Impact")],
        default="tbd", tracking=True)
    schedule_days = fields.Integer(string="Schedule Impact (days)")
    change_order_id = fields.Many2one("gte.change.order", string="Linked Change Order",
                                      copy=False)
    priority = fields.Selection([("0", "Normal"), ("1", "High")], default="0")
    state = fields.Selection([
        ("draft", "Draft"), ("open", "Open"), ("sent", "Sent"),
        ("answered", "Answered"), ("distributed", "Distributed"),
        ("closed", "Closed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)
    is_overdue = fields.Boolean(compute="_compute_is_overdue", search="_search_is_overdue")

    _sql_constraints = [
        ("rfi_number_project_uniq", "unique(project_id, name)",
         "RFI number must be unique per project."),
    ]

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id or rec.env.company.currency_id

    @api.depends("date_required", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_overdue = bool(
                rec.date_required and rec.date_required < today
                and rec.state in ("draft", "open", "sent"))

    def _search_is_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        domain = [("date_required", "<", today),
                  ("state", "in", ("draft", "open", "sent"))]
        if (operator == "=") == bool(value):
            return domain
        return ["!"] + domain

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.rfi", "RFI")
        return super().create(vals_list)

    # --- state transitions -------------------------------------------------
    def _set_state(self, allowed_from, new_state, extra_vals=None):
        for rec in self:
            if rec.state not in allowed_from:
                raise ValidationError(
                    "Invalid transition %s -> %s on %s" % (rec.state, new_state, rec.name))
            rec.write(dict(extra_vals or {}, state=new_state))

    def action_open(self):
        self._set_state(("draft",), "open")

    def action_send(self):
        for rec in self:
            if not rec.question or not rec.addressed_to_id:
                raise ValidationError(
                    "Question and Addressed To are required before sending %s." % rec.name)
        self._set_state(("open",), "sent")

    def action_answer(self):
        for rec in self:
            if not rec.response:
                raise ValidationError("A formal response is required on %s." % rec.name)
        self._set_state(("sent",), "answered",
                        {"date_answered": fields.Date.context_today(self)})

    def action_distribute(self):
        for rec in self:
            if not rec.distribution_ids:
                raise ValidationError("Distribution recipients required on %s." % rec.name)
        self._set_state(("answered",), "distributed",
                        {"date_distributed": fields.Date.context_today(self)})

    def action_close(self):
        self._set_state(("distributed", "answered"), "closed")

    def action_cancel(self):
        self._set_state(("draft", "open", "sent"), "cancelled")

    # --- overdue escalation ------------------------------------------------
    @api.model
    def _cron_overdue_activities(self):
        overdue = self.search([("is_overdue", "=", True)])
        for rec in overdue:
            existing = rec.activity_ids.filtered(
                lambda a: a.summary and a.summary.startswith("Overdue RFI"))
            if not existing and rec.coordinator_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Overdue RFI response",
                    user_id=rec.coordinator_id.id)
