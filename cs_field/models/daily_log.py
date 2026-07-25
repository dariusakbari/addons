from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteDailyLog(models.Model):
    _name = "cs.daily.log"
    _description = "Daily Site Log"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    foreman_id = fields.Many2one("res.users", string="Foreman",
                                 default=lambda self: self.env.user, tracking=True)
    weather = fields.Selection([
        ("sunny", "Sunny"), ("cloudy", "Cloudy"), ("rain", "Rain"),
        ("snow", "Snow"), ("wind", "High Wind"), ("extreme", "Extreme")])
    temperature = fields.Char(string="Temperature")
    labour_ids = fields.One2many("cs.daily.log.labour", "log_id")
    total_hours = fields.Float(compute="_compute_total_hours", store=True)
    work_done = fields.Text(string="Work Completed")
    quantities = fields.Text(string="Quantities Installed")
    equipment = fields.Text(string="Equipment Used")
    deliveries = fields.Text()
    visitors = fields.Text()
    delays = fields.Text(string="Delays and Causes")
    safety_observations = fields.Text()
    photo_ids = fields.Many2many("ir.attachment", string="Photos")
    signature = fields.Binary(string="Foreman Signature")
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    reviewed_date = fields.Date(readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("submitted", "Submitted"),
        ("reviewed", "Reviewed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    _daily_log_uniq = models.Constraint(
        "unique(project_id, date, foreman_id)",
        "A daily log already exists for this project, date and foreman.",
    )

    @api.depends("labour_ids.hours")
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = sum(rec.labour_ids.mapped("hours"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.daily.log", "DSL")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            problems = []
            if not rec.work_done:
                problems.append("work completed")
            if not rec.labour_ids:
                problems.append("at least one labour line")
            if not rec.signature:
                problems.append("foreman signature")
            if problems:
                raise ValidationError(
                    "This daily log cannot be finalized. Missing: %s." % ", ".join(problems))
            rec.state = "submitted"
            supervisor = rec.project_id.user_id
            if supervisor and supervisor != rec.foreman_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Daily site log ready for review",
                    user_id=supervisor.id)

    def action_review(self):
        for rec in self:
            if rec.state != "submitted":
                raise ValidationError("Only submitted logs can be reviewed.")
            rec.write({"state": "reviewed",
                       "reviewed_by_id": self.env.user.id,
                       "reviewed_date": fields.Date.context_today(self)})

    def action_cancel(self):
        for rec in self:
            if rec.state == "reviewed":
                raise ValidationError("Reviewed logs cannot be cancelled.")
            rec.state = "cancelled"


class GteDailyLogLabour(models.Model):
    _name = "cs.daily.log.labour"
    _description = "Daily Log Labour Line"

    log_id = fields.Many2one("cs.daily.log", required=True, ondelete="cascade")
    worker_name = fields.Char(required=True)
    classification = fields.Char(string="Classification")
    hours = fields.Float(required=True)
    notes = fields.Char()
