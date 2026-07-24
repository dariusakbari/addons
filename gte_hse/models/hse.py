from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteFlha(models.Model):
    _name = "gte.flha"
    _description = "Field Level Hazard Assessment"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    foreman_id = fields.Many2one("res.users", string="Foreman",
                                 default=lambda self: self.env.user, tracking=True)
    location = fields.Char(string="Work Location")
    site_contact = fields.Char()
    task_description = fields.Text(string="Task / Activity")
    overall_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        tracking=True)
    # PPE — deliberately NOT preselected (audit finding: all boxes were preticked)
    ppe_hard_hat = fields.Boolean("Hard Hat")
    ppe_safety_glasses = fields.Boolean("Safety Glasses")
    ppe_gloves = fields.Boolean("Gloves")
    ppe_boots = fields.Boolean("Safety Boots")
    ppe_vest = fields.Boolean("Hi-Vis Vest")
    ppe_hearing = fields.Boolean("Hearing Protection")
    ppe_other = fields.Char("Other PPE")
    hazard_ids = fields.One2many("gte.flha.hazard", "flha_id", copy=True)
    signoff_ids = fields.One2many("gte.flha.signoff", "flha_id")
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    reviewed_date = fields.Date(readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("submitted", "Submitted"),
        ("reviewed", "Reviewed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.flha", "FLHA")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            problems = []
            if not rec.task_description:
                problems.append("task/activity description")
            if not rec.overall_risk:
                problems.append("overall risk level")
            if not rec.hazard_ids:
                problems.append("at least one hazard")
            elif any(not h.control for h in rec.hazard_ids):
                problems.append("a control for every hazard")
            if not rec.signoff_ids or all(not s.signature for s in rec.signoff_ids):
                problems.append("at least one signed crew acknowledgement")
            if problems:
                raise ValidationError(
                    "This FLHA cannot be finalized. Missing: %s." % ", ".join(problems))
            rec.state = "submitted"
            supervisor = rec.project_id.user_id or rec.foreman_id
            if rec.overall_risk == "high" and supervisor:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="HIGH RISK FLHA — review required",
                    user_id=supervisor.id)

    def action_review(self):
        for rec in self:
            if rec.state != "submitted":
                raise ValidationError("Only submitted FLHAs can be reviewed.")
            rec.write({"state": "reviewed",
                       "reviewed_by_id": self.env.user.id,
                       "reviewed_date": fields.Date.context_today(self)})

    def action_cancel(self):
        for rec in self:
            if rec.state == "reviewed":
                raise ValidationError("Reviewed FLHAs cannot be cancelled.")
            rec.state = "cancelled"


class GteFlhaHazard(models.Model):
    _name = "gte.flha.hazard"
    _description = "FLHA Hazard Line"

    flha_id = fields.Many2one("gte.flha", required=True, ondelete="cascade")
    description = fields.Char(string="Hazard", required=True)
    risk = fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High")],
                            required=True, default="low")
    control = fields.Char(string="Control Measure")


class GteFlhaSignoff(models.Model):
    _name = "gte.flha.signoff"
    _description = "FLHA Crew Sign-off"

    flha_id = fields.Many2one("gte.flha", required=True, ondelete="cascade")
    worker_name = fields.Char(required=True)
    signature = fields.Binary(string="Signature")
    signed_on = fields.Datetime(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("signature"):
                vals["signed_on"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("signature"):
            vals["signed_on"] = fields.Datetime.now()
        return super().write(vals)


class GteToolboxTalk(models.Model):
    _name = "gte.toolbox.talk"
    _description = "Toolbox Talk"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    topic = fields.Char(required=True, tracking=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    presenter_id = fields.Many2one("res.users", string="Presenter",
                                   default=lambda self: self.env.user)
    duration_minutes = fields.Integer(string="Duration (min)")
    notes = fields.Html()
    attendee_ids = fields.One2many("gte.toolbox.attendee", "talk_id")
    state = fields.Selection([
        ("draft", "Draft"), ("submitted", "Submitted"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.toolbox.talk", "TBT")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            problems = []
            if not rec.attendee_ids:
                problems.append("at least one attendee")
            elif all(not a.signature for a in rec.attendee_ids):
                problems.append("at least one attendee signature")
            if problems:
                raise ValidationError(
                    "This toolbox talk cannot be finalized. Missing: %s." % ", ".join(problems))
            rec.state = "submitted"

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteToolboxAttendee(models.Model):
    _name = "gte.toolbox.attendee"
    _description = "Toolbox Talk Attendee"

    talk_id = fields.Many2one("gte.toolbox.talk", required=True, ondelete="cascade")
    worker_name = fields.Char(required=True)
    signature = fields.Binary(string="Signature")
