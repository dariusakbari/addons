import base64
from io import BytesIO

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def _cs_make_qr(value):
    """Return a base64 PNG QR for a value, or False if generation is
    unavailable (missing qrcode library, etc.). Never raises."""
    try:
        import qrcode
    except Exception:
        return False
    try:
        img = qrcode.make(value)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue())
    except Exception:
        return False


class CsQrMixin(models.AbstractModel):
    """Adds a scan-to-open QR image pointing at the record's form."""
    _name = "cs.qr.mixin"
    _description = "Construction QR Mixin"

    qr_image = fields.Image(compute="_compute_qr_image", store=True,
                            readonly=True)

    @api.depends("name")
    def _compute_qr_image(self):
        base = self.env["ir.config_parameter"].sudo().get_param(
            "web.base.url") or ""
        for rec in self:
            if isinstance(rec.id, int) and base:
                url = "%s/web#id=%s&model=%s&view_type=form" % (
                    base, rec.id, rec._name)
                rec.qr_image = _cs_make_qr(url)
            else:
                rec.qr_image = False


class GteIncident(models.Model):
    _name = "cs.incident"
    _description = "Incident Report"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    location = fields.Char()
    reported_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    incident_type = fields.Selection([
        ("injury", "Injury"), ("near_miss", "Near Miss"),
        ("property", "Property Damage"), ("environmental", "Environmental"),
        ("other", "Other")], required=True, tracking=True)
    severity = fields.Selection([
        ("minor", "Minor"), ("moderate", "Moderate"),
        ("serious", "Serious"), ("critical", "Critical")],
        tracking=True)
    description = fields.Text()
    people_involved = fields.Text()
    injuries = fields.Text(string="Injuries / First Aid Provided")
    immediate_actions = fields.Text()
    root_cause = fields.Text()
    corrective_actions = fields.Text()
    corrective_due = fields.Date(string="Corrective Actions Due")
    photo_ids = fields.Many2many("ir.attachment", string="Photos / Evidence")
    reviewed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    reviewed_date = fields.Date(readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("submitted", "Submitted"),
        ("investigation", "Under Investigation"), ("closed", "Closed"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.incident", "INC")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            problems = []
            if not rec.description:
                problems.append("description of what happened")
            if not rec.severity:
                problems.append("severity")
            if not rec.immediate_actions:
                problems.append("immediate actions taken")
            if problems:
                raise ValidationError(
                    "This incident cannot be submitted. Missing: %s." % ", ".join(problems))
            rec.state = "submitted"
            supervisor = rec.project_id.user_id or rec.reported_by_id
            if supervisor:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Incident %s (%s) — review required" % (
                        rec.name, dict(rec._fields["severity"].selection).get(rec.severity)),
                    user_id=supervisor.id)

    def action_investigate(self):
        self.write({"state": "investigation"})

    def action_close(self):
        for rec in self:
            if rec.severity in ("serious", "critical") and not rec.root_cause:
                raise ValidationError(
                    "Serious/critical incidents need a root cause before closing.")
            rec.write({"state": "closed",
                       "reviewed_by_id": self.env.user.id,
                       "reviewed_date": fields.Date.context_today(self)})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteEquipmentInspection(models.Model):
    _name = "cs.equipment.inspection"
    _description = "Equipment Inspection"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin",
                "cs.qr.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    equipment_name = fields.Char(required=True)
    serial_no = fields.Char(string="Serial / Asset No.")
    inspector_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    result = fields.Selection([("pass", "Pass"), ("fail", "Fail")], tracking=True)
    defects = fields.Text(string="Defects Found")
    action_taken = fields.Text()
    next_due = fields.Date(string="Next Inspection Due")
    photo_ids = fields.Many2many("ir.attachment", string="Photos")
    state = fields.Selection([
        ("draft", "Draft"), ("done", "Completed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(
                    project, "cs.equipment.inspection", "EQI")
        return super().create(vals_list)

    def action_done(self):
        for rec in self:
            problems = []
            if not rec.result:
                problems.append("pass/fail result")
            if rec.result == "fail" and not rec.defects:
                problems.append("defects found (result is Fail)")
            if problems:
                raise ValidationError(
                    "This inspection cannot be completed. Missing: %s." % ", ".join(problems))
            rec.state = "done"
            supervisor = rec.project_id.user_id
            if rec.result == "fail" and supervisor:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="FAILED equipment inspection %s — %s" % (
                        rec.name, rec.equipment_name),
                    user_id=supervisor.id)

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteWorkPermit(models.Model):
    _name = "cs.work.permit"
    _description = "Work Permit"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin",
                "cs.qr.mixin"]
    _order = "valid_from desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    permit_type = fields.Selection([
        ("hot_work", "Hot Work"), ("confined", "Confined Space"),
        ("height", "Work at Height"), ("electrical", "Electrical / LOTO"),
        ("excavation", "Excavation"), ("other", "Other")],
        required=True, tracking=True)
    description = fields.Text(string="Work Description")
    valid_from = fields.Datetime(required=True, default=fields.Datetime.now)
    valid_to = fields.Datetime(required=True)
    issued_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    issued_to = fields.Char(string="Issued To (crew/contractor)")
    conditions = fields.Text(string="Conditions / Precautions")
    state = fields.Selection([
        ("draft", "Draft"), ("active", "Active"),
        ("closed", "Closed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    @api.constrains("valid_from", "valid_to")
    def _check_dates(self):
        for rec in self:
            if rec.valid_to and rec.valid_from and rec.valid_to <= rec.valid_from:
                raise ValidationError("Permit end must be after start.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.work.permit", "WP")
        return super().create(vals_list)

    def action_activate(self):
        for rec in self:
            problems = []
            if not rec.description:
                problems.append("work description")
            if not rec.conditions:
                problems.append("conditions / precautions")
            if not rec.issued_to:
                problems.append("issued to")
            if problems:
                raise ValidationError(
                    "This permit cannot be activated. Missing: %s." % ", ".join(problems))
            rec.state = "active"

    def action_close(self):
        self.write({"state": "closed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    @api.model
    def _cron_expire_permits(self):
        expired = self.search([("state", "=", "active"),
                               ("valid_to", "<", fields.Datetime.now())])
        for rec in expired:
            if rec.issued_by_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Work permit %s expired — close or renew" % rec.name,
                    user_id=rec.issued_by_id.id)


class GteRisk(models.Model):
    _name = "cs.risk"
    _description = "Risk Register Entry"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "score desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    title = fields.Char(string="Risk", required=True, tracking=True)
    category = fields.Selection([
        ("safety", "Safety"), ("schedule", "Schedule"), ("cost", "Cost"),
        ("quality", "Quality"), ("environment", "Environment"), ("other", "Other")],
        default="safety")
    likelihood = fields.Selection(
        [("1", "Rare"), ("2", "Unlikely"), ("3", "Possible"),
         ("4", "Likely"), ("5", "Almost Certain")], default="3")
    impact = fields.Selection(
        [("1", "Negligible"), ("2", "Minor"), ("3", "Moderate"),
         ("4", "Major"), ("5", "Severe")], default="3")
    score = fields.Integer(compute="_compute_score", store=True)
    mitigation = fields.Text()
    owner_id = fields.Many2one("res.users", string="Risk Owner",
                               default=lambda self: self.env.user, tracking=True)
    review_date = fields.Date(string="Next Review")
    state = fields.Selection([
        ("open", "Open"), ("mitigated", "Mitigated"), ("closed", "Closed")],
        default="open", tracking=True, index=True, copy=False)

    @api.depends("likelihood", "impact")
    def _compute_score(self):
        for rec in self:
            rec.score = int(rec.likelihood or 0) * int(rec.impact or 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.risk", "RSK")
        return super().create(vals_list)

    def action_mitigate(self):
        for rec in self:
            if not rec.mitigation:
                raise ValidationError("A mitigation plan is required.")
            rec.state = "mitigated"

    def action_close(self):
        self.write({"state": "closed"})
