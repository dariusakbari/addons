from odoo import api, fields, models
from odoo.exceptions import ValidationError

TRADES = [
    ("electrical", "Electrical"), ("low_voltage", "Low Voltage / Data"),
    ("fire_alarm", "Fire Alarm"), ("controls", "Controls / BMS"),
    ("mechanical", "Mechanical"), ("plumbing", "Plumbing"),
    ("hvac", "HVAC"), ("structural", "Structural / Steel"),
    ("concrete", "Concrete"), ("framing", "Framing"),
    ("drywall", "Drywall"), ("finishing", "Finishing"),
    ("sitework", "Sitework"), ("general", "General / Multi-Trade"),
    ("other", "Other"),
]

HORIZONS = [("2", "2 Weeks"), ("3", "3 Weeks"), ("6", "6 Weeks")]


class CsLookahead(models.Model):
    _name = "cs.lookahead"
    _description = "Short-Interval / Look-Ahead Plan"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "week_start desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    week_start = fields.Date(
        string="Week Starting", required=True, tracking=True,
        default=lambda self: self._default_week_start(),
        help="The Monday the look-ahead window begins on.")
    horizon = fields.Selection(HORIZONS, default="3", required=True,
                               tracking=True)
    prepared_by_id = fields.Many2one("res.users", string="Prepared By",
                                     default=lambda self: self.env.user)
    notes = fields.Html()
    line_ids = fields.One2many("cs.lookahead.line", "lookahead_id", copy=True)
    date_issued = fields.Datetime(readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("issued", "Issued"), ("archived", "Archived")],
        default="draft", tracking=True, index=True, copy=False)

    activity_count = fields.Integer(compute="_compute_stats")
    manpower_peak = fields.Integer(string="Peak Manpower",
                                   compute="_compute_stats")
    ppc = fields.Float(string="PPC %", compute="_compute_stats",
                       help="Percent Plan Complete: committed activities "
                            "completed as planned, over all commitments.")

    @api.model
    def _default_week_start(self):
        today = fields.Date.context_today(self)
        return fields.Date.subtract(today, days=today.weekday())

    @api.depends("line_ids.manpower", "line_ids.week_no", "line_ids.committed",
                 "line_ids.status")
    def _compute_stats(self):
        for rec in self:
            rec.activity_count = len(rec.line_ids)
            by_week = {}
            for line in rec.line_ids:
                by_week[line.week_no] = by_week.get(line.week_no, 0) \
                    + (line.manpower or 0)
            rec.manpower_peak = max(by_week.values()) if by_week else 0
            commitments = rec.line_ids.filtered("committed")
            if commitments:
                done = commitments.filtered(lambda l: l.status == "done")
                rec.ppc = 100.0 * len(done) / len(commitments)
            else:
                rec.ppc = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.lookahead",
                                                    "LA")
        return super().create(vals_list)

    def action_pull_tasks(self):
        """Pre-fill the plan from project tasks whose deadline falls inside the
        look-ahead window."""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(
                "%s: pull tasks while the plan is still in draft." % self.name)
        end = fields.Date.add(self.week_start, days=int(self.horizon) * 7)
        tasks = self.env["project.task"].search([
            ("project_id", "=", self.project_id.id),
            ("date_deadline", ">=", self.week_start),
            ("date_deadline", "<", end),
        ])
        existing = self.line_ids.mapped("task_id").ids
        vals = []
        seq = (max(self.line_ids.mapped("sequence") or [0])) + 10
        for task in tasks:
            if task.id in existing:
                continue
            start = task.date_deadline
            if "planned_date_begin" in task._fields and task.planned_date_begin:
                start = fields.Date.to_date(task.planned_date_begin)
            vals.append((0, 0, {
                "sequence": seq,
                "activity": task.name,
                "planned_start": start,
                "planned_finish": task.date_deadline,
                "task_id": task.id,
            }))
            seq += 10
        if not vals:
            raise ValidationError(
                "%s: no un-added tasks with a deadline in the window." %
                self.name)
        self.write({"line_ids": vals})
        return True

    def action_issue(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(
                    "%s needs at least one activity before it can be issued."
                    % rec.name)
            problems = []
            for line in rec.line_ids:
                missing = []
                if not line.planned_start:
                    missing.append("planned start")
                if not line.planned_finish:
                    missing.append("planned finish")
                if not line.trade:
                    missing.append("trade")
                if not line.manpower:
                    missing.append("manpower")
                if (line.planned_start and line.planned_finish
                        and line.planned_finish < line.planned_start):
                    missing.append("finish on/after start")
                if missing:
                    problems.append("• %s: %s" % (
                        line.activity or "(untitled)", ", ".join(missing)))
            if problems:
                raise ValidationError(
                    "%s can't be issued until every activity has a planned "
                    "start, planned finish, trade and manpower:\n%s"
                    % (rec.name, "\n".join(problems)))
            rec.write({"state": "issued",
                       "date_issued": fields.Datetime.now()})

    def action_reset(self):
        self.write({"state": "draft"})

    def action_archive_plan(self):
        self.write({"state": "archived"})

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()


class CsLookaheadLine(models.Model):
    _name = "cs.lookahead.line"
    _description = "Look-Ahead Planned Activity"
    _order = "lookahead_id, week_no, sequence, id"

    lookahead_id = fields.Many2one("cs.lookahead", required=True,
                                   ondelete="cascade", index=True)
    project_id = fields.Many2one(related="lookahead_id.project_id", store=True)
    sequence = fields.Integer(default=10)
    activity = fields.Char(required=True)
    trade = fields.Selection(TRADES, default="electrical")
    subcontractor_id = fields.Many2one("res.partner", string="Subcontractor")
    planned_start = fields.Date()
    planned_finish = fields.Date()
    week_no = fields.Integer(string="Week #", compute="_compute_week_no",
                             store=True,
                             help="Which week of the look-ahead window the "
                                  "activity starts in (0 = before/unscheduled).")
    week_label = fields.Char(compute="_compute_week_no", store=True)
    manpower = fields.Integer(string="Crew", help="Planned headcount.")
    constraint = fields.Char(help="What must be resolved for this to proceed "
                                  "(material, RFI, access, permit, predecessor).")
    constraint_status = fields.Selection([
        ("clear", "Clear"), ("at_risk", "At Risk"), ("blocked", "Blocked")],
        default="clear")
    committed = fields.Boolean(string="Committed",
                               help="A firm commitment for this week (Last "
                                    "Planner).")
    status = fields.Selection([
        ("planned", "Planned"), ("in_progress", "In Progress"),
        ("done", "Done"), ("missed", "Missed / Carried")],
        default="planned")
    variance_reason = fields.Char(
        string="Variance Reason",
        help="If missed: why the commitment was not met.")
    task_id = fields.Many2one("project.task", string="Linked Task")

    @api.depends("planned_start", "lookahead_id.week_start")
    def _compute_week_no(self):
        for line in self:
            start = line.lookahead_id.week_start
            if start and line.planned_start and line.planned_start >= start:
                no = ((line.planned_start - start).days // 7) + 1
                line.week_no = no
                line.week_label = "Week %d" % no
            else:
                line.week_no = 0
                line.week_label = "Unscheduled"
