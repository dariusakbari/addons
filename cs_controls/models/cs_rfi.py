from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteRfi(models.Model):
    _name = "cs.rfi"
    _description = "Request for Information"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
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
    distribution_ids = fields.Many2many("res.partner", "cs_rfi_distribution_rel",
                                        string="Distribution Recipients")
    cost_impact = fields.Selection(
        [("none", "No Cost Impact"), ("tbd", "To Be Determined"), ("yes", "Cost Impact")],
        default="tbd", tracking=True)
    cost_amount = fields.Monetary(currency_field="currency_id", tracking=True)
    schedule_impact = fields.Selection(
        [("none", "No Schedule Impact"), ("tbd", "To Be Determined"), ("yes", "Schedule Impact")],
        default="tbd", tracking=True)
    schedule_days = fields.Integer(string="Schedule Impact (days)")
    change_order_id = fields.Many2one("cs.change.order", string="Linked Change Order",
                                      copy=False)
    priority = fields.Selection([("0", "Normal"), ("1", "High")], default="0")
    state = fields.Selection([
        ("draft", "Draft"), ("open", "Open"), ("sent", "Sent"),
        ("answered", "Answered"), ("distributed", "Distributed"),
        ("closed", "Closed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)
    is_overdue = fields.Boolean(compute="_compute_is_overdue", search="_search_is_overdue")
    responded_by_id = fields.Many2one("res.partner", string="Responder", tracking=True)
    not_distributed_reason = fields.Char(
        string="Reason Not Distributed", tracking=True,
        help="Required to close an RFI that was never distributed.")
    active = fields.Boolean(default=True)

    _rfi_number_project_uniq = models.Constraint(
        "unique(project_id, name)",
        "RFI number must be unique per project.",
    )

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

    _OVERDUE_STATES = ["draft", "open", "sent"]

    def _search_is_overdue(self, operator, value):
        today = fields.Date.today()
        overdue = ["&", ("date_required", "<", today),
                   ("state", "in", self._OVERDUE_STATES)]
        if (operator == "=") == bool(value):
            return overdue
        # NOT overdue (De Morgan): no due date, or not yet due, or responded/closed
        return ["|", "|",
                ("date_required", "=", False),
                ("date_required", ">=", today),
                ("state", "not in", self._OVERDUE_STATES)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.rfi", "RFI")
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
            missing = []
            if not rec.subject: missing.append("subject")
            if not rec.question: missing.append("complete question")
            if not rec.raised_by_id: missing.append("raised by")
            if not rec.addressed_to_id: missing.append("addressed to")
            if not rec.coordinator_id: missing.append("coordinator")
            if not rec.date_required: missing.append("required response date")
            if not rec.distribution_ids: missing.append("distribution recipients")
            if missing:
                raise ValidationError(
                    "%s cannot be sent. Missing: %s." % (rec.name, ", ".join(missing)))
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
        for rec in self:
            missing = []
            if not rec.response: missing.append("response")
            if not rec.responded_by_id: missing.append("responder")
            if not rec.date_answered: missing.append("response date")
            if not rec.date_distributed and not rec.not_distributed_reason:
                missing.append("distribution date or a documented reason not distributed")
            if missing:
                raise ValidationError(
                    "%s cannot be closed. Missing: %s." % (rec.name, ", ".join(missing)))
        self._set_state(("distributed", "answered"), "closed")

    def action_reopen(self):
        if not self.env.user.has_group("cs_core.group_cs_pm"):
            raise ValidationError("Only project managers can reopen an RFI.")
        self._set_state(("closed", "cancelled"), "open")

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()

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
