from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteNcr(models.Model):
    _name = "gte.ncr"
    _description = "Non-Conformance Report"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    raised_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    location = fields.Char()
    severity = fields.Selection([("minor", "Minor"), ("major", "Major"),
                                 ("critical", "Critical")], tracking=True)
    description = fields.Text(string="Non-Conformance Description")
    root_cause = fields.Text()
    corrective_action = fields.Text()
    assigned_to_id = fields.Many2one("res.users", string="Assigned To", tracking=True)
    due_date = fields.Date(string="Correction Due")
    photo_ids = fields.Many2many("ir.attachment", string="Photos")
    state = fields.Selection([
        ("draft", "Draft"), ("open", "Open"), ("action", "Corrective Action"),
        ("closed", "Closed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.ncr", "NCR")
        return super().create(vals_list)

    def action_open(self):
        for rec in self:
            if not rec.description or not rec.severity:
                raise ValidationError(
                    "Description and severity are required before opening %s." % rec.name)
            rec.state = "open"
            if rec.assigned_to_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="NCR %s assigned — corrective action required" % rec.name,
                    date_deadline=rec.due_date,
                    user_id=rec.assigned_to_id.id)

    def action_corrective(self):
        self.write({"state": "action"})

    def action_close(self):
        for rec in self:
            if not rec.corrective_action:
                raise ValidationError(
                    "A corrective action is required before closing %s." % rec.name)
            rec.state = "closed"

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteInspection(models.Model):
    _name = "gte.inspection"
    _description = "General Inspection"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    inspector_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    inspection_type = fields.Char(string="Inspection Type")
    line_ids = fields.One2many("gte.inspection.line", "inspection_id", copy=True)
    overall_result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        compute="_compute_overall", store=True)
    notes = fields.Text()
    photo_ids = fields.Many2many("ir.attachment", string="Photos")
    state = fields.Selection([
        ("draft", "Draft"), ("done", "Completed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, copy=False)

    @api.depends("line_ids.result")
    def _compute_overall(self):
        for rec in self:
            results = rec.line_ids.mapped("result")
            rec.overall_result = "fail" if "fail" in results else (
                "pass" if results else False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.inspection", "GI")
        return super().create(vals_list)

    def action_done(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(
                    "At least one checklist item is required on %s." % rec.name)
            rec.state = "done"
            supervisor = rec.project_id.user_id
            if rec.overall_result == "fail" and supervisor:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="FAILED inspection %s — follow-up required" % rec.name,
                    user_id=supervisor.id)

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteInspectionLine(models.Model):
    _name = "gte.inspection.line"
    _description = "Inspection Checklist Item"

    inspection_id = fields.Many2one("gte.inspection", required=True,
                                    ondelete="cascade")
    item = fields.Char(required=True)
    result = fields.Selection([("pass", "Pass"), ("fail", "Fail"),
                               ("na", "N/A")], required=True, default="pass")
    notes = fields.Char()


class GteAttendance(models.Model):
    _name = "gte.site.attendance"
    _description = "Site Attendance Sheet"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    foreman_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    line_ids = fields.One2many("gte.site.attendance.line", "sheet_id")
    total_hours = fields.Float(compute="_compute_total", store=True)
    state = fields.Selection([("draft", "Draft"), ("submitted", "Submitted"),
                              ("cancelled", "Cancelled")],
                             default="draft", tracking=True, copy=False)

    _attendance_uniq = models.Constraint(
        "unique(project_id, date)",
        "An attendance sheet already exists for this project and date.",
    )

    @api.depends("line_ids.hours")
    def _compute_total(self):
        for rec in self:
            rec.total_hours = sum(rec.line_ids.mapped("hours"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.site.attendance", "ATT")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("At least one worker line is required.")
            rec.state = "submitted"

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteAttendanceLine(models.Model):
    _name = "gte.site.attendance.line"
    _description = "Attendance Line"

    sheet_id = fields.Many2one("gte.site.attendance", required=True,
                               ondelete="cascade")
    worker_name = fields.Char(required=True)
    company = fields.Char(string="Employer")
    time_in = fields.Float(string="In")
    time_out = fields.Float(string="Out")
    hours = fields.Float(compute="_compute_hours", store=True)

    @api.depends("time_in", "time_out")
    def _compute_hours(self):
        for rec in self:
            rec.hours = max(0.0, (rec.time_out or 0.0) - (rec.time_in or 0.0))


class GteVisitor(models.Model):
    _name = "gte.visitor.log"
    _description = "Visitor Log"
    _inherit = ["mail.thread", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    visitor_name = fields.Char(required=True)
    visitor_company = fields.Char(string="Company")
    host_id = fields.Many2one("res.users", string="Host",
                              default=lambda self: self.env.user)
    purpose = fields.Char()
    time_in = fields.Float(string="In")
    time_out = fields.Float(string="Out")
    badge = fields.Char(string="Badge No.")
    state = fields.Selection([("in", "On Site"), ("out", "Signed Out")],
                             default="in", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.visitor.log", "VIS")
        return super().create(vals_list)

    def action_sign_out(self):
        self.write({"state": "out"})


class GteTransmittal(models.Model):
    _name = "gte.transmittal"
    _description = "Transmittal"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one("res.partner", string="To", tracking=True)
    sent_by_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    via = fields.Selection([("email", "Email"), ("courier", "Courier"),
                            ("hand", "Hand Delivered"), ("portal", "Portal")],
                           default="email")
    description = fields.Text(string="Remarks")
    line_ids = fields.One2many("gte.transmittal.line", "transmittal_id", copy=True)
    attachment_ids = fields.Many2many("ir.attachment", string="Files")
    distribution_ids = fields.Many2many("res.partner",
                                        "gte_transmittal_dist_rel", string="CC")
    state = fields.Selection([("draft", "Draft"), ("sent", "Sent"),
                              ("acknowledged", "Acknowledged"),
                              ("cancelled", "Cancelled")],
                             default="draft", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.transmittal", "TR")
        return super().create(vals_list)

    def action_send(self):
        for rec in self:
            if not rec.partner_id or not rec.line_ids:
                raise ValidationError(
                    "Recipient and at least one item are required on %s." % rec.name)
            rec.state = "sent"

    def action_acknowledge(self):
        self.write({"state": "acknowledged"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteTransmittalLine(models.Model):
    _name = "gte.transmittal.line"
    _description = "Transmittal Item"

    transmittal_id = fields.Many2one("gte.transmittal", required=True,
                                     ondelete="cascade")
    description = fields.Char(required=True)
    quantity = fields.Integer(default=1)
    doc_format = fields.Char(string="Format")
    revision = fields.Char()


class GteShopDrawing(models.Model):
    _name = "gte.shop.drawing"
    _description = "Shop Drawing"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    title = fields.Char(required=True, tracking=True)
    drawing_no = fields.Char(string="Drawing No.")
    revision = fields.Char(default="0", tracking=True)
    supplier_id = fields.Many2one("res.partner", string="Supplier")
    submittal_id = fields.Many2one("gte.submittal", string="Linked Submittal")
    date_received = fields.Date(tracking=True)
    date_sent = fields.Date(tracking=True)
    attachment_ids = fields.Many2many("ir.attachment", string="Files")
    state = fields.Selection([
        ("draft", "Draft"), ("received", "Received"), ("under_review", "Under Review"),
        ("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.shop.drawing", "SD")
        return super().create(vals_list)

    def action_receive(self):
        self.write({"state": "received",
                    "date_received": fields.Date.context_today(self)})

    def action_review(self):
        self.write({"state": "under_review"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteGatePass(models.Model):
    _name = "gte.gate.pass"
    _description = "Gate Pass"
    _inherit = ["mail.thread", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    pass_type = fields.Selection([("in", "Material In"), ("out", "Material Out")],
                                 required=True, default="out")
    person = fields.Char(string="Carried By", tracking=True)
    person_company = fields.Char(string="Company")
    vehicle = fields.Char(string="Vehicle / Plate")
    material_description = fields.Text()
    authorized_by_id = fields.Many2one("res.users", string="Authorized By",
                                       readonly=True, copy=False)
    state = fields.Selection([("draft", "Draft"), ("authorized", "Authorized"),
                              ("completed", "Completed"), ("cancelled", "Cancelled")],
                             default="draft", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.gate.pass", "GP")
        return super().create(vals_list)

    def action_authorize(self):
        for rec in self:
            if not rec.material_description or not rec.person:
                raise ValidationError(
                    "Material description and carrier are required on %s." % rec.name)
            rec.write({"state": "authorized",
                       "authorized_by_id": self.env.user.id})

    def action_complete(self):
        self.write({"state": "completed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})
