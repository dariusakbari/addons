from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GtePunchItem(models.Model):
    _name = "cs.punch.item"
    _description = "Deficiency / Punch List Item"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "priority desc, date_identified desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    location = fields.Char()
    description = fields.Text(required=True)
    responsible_id = fields.Many2one("res.partner",
                                     string="Responsible Contractor / Person",
                                     tracking=True)
    priority = fields.Selection([("0", "Low"), ("1", "Medium"), ("2", "High")],
                                default="1", tracking=True)
    date_identified = fields.Date(default=fields.Date.context_today, required=True)
    date_required = fields.Date(string="Required Completion")
    photo_before_ids = fields.Many2many(
        "ir.attachment", "cs_punch_before_rel", string="Before Photos")
    photo_after_ids = fields.Many2many(
        "ir.attachment", "cs_punch_after_rel", string="After Photos")
    corrective_action = fields.Text()
    verified_by_id = fields.Many2one("res.users", string="Verified By",
                                     readonly=True, copy=False)
    closed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    date_closed = fields.Date(readonly=True, copy=False)
    inspection_id = fields.Many2one("cs.inspection", string="From Inspection")
    state = fields.Selection([
        ("open", "Open"), ("in_progress", "In Progress"),
        ("verify", "Ready to Verify"), ("closed", "Closed"),
        ("cancelled", "Cancelled")],
        default="open", tracking=True, index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.punch.item", "PL")
        return super().create(vals_list)

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_ready(self):
        for rec in self:
            if not rec.corrective_action:
                raise ValidationError(
                    "Record the corrective action before marking ready (%s)." % rec.name)
        self.write({"state": "verify"})

    def action_close(self):
        for rec in self:
            if not rec.photo_after_ids:
                raise ValidationError(
                    "An 'after' photo is required to close %s." % rec.name)
            rec.write({"state": "closed",
                       "verified_by_id": self.env.user.id,
                       "closed_by_id": self.env.user.id,
                       "date_closed": fields.Date.context_today(self)})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteMeeting(models.Model):
    _name = "cs.meeting"
    _description = "Meeting Minutes"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    meeting_type = fields.Selection([
        ("progress", "Progress"), ("coordination", "Coordination"),
        ("safety", "Safety"), ("preconstruction", "Pre-Construction"),
        ("closeout", "Closeout"), ("other", "Other")],
        default="progress", required=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    location = fields.Char()
    attendee_ids = fields.Many2many("res.partner", string="Attendees")
    chair_id = fields.Many2one("res.users", string="Chaired By",
                               default=lambda self: self.env.user)
    agenda = fields.Html()
    discussion = fields.Html(string="Discussion & Decisions")
    action_ids = fields.One2many("cs.meeting.action", "meeting_id")
    state = fields.Selection([
        ("draft", "Draft"), ("issued", "Issued"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.meeting", "MIN")
        return super().create(vals_list)

    def action_issue(self):
        for rec in self:
            if not rec.attendee_ids:
                raise ValidationError("Record attendees before issuing %s." % rec.name)
            rec.state = "issued"
            for action in rec.action_ids.filtered(
                    lambda a: a.owner_user_id and a.state == "open"):
                action.owner_user_id  # ensure loaded
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Action from %s: %s" % (rec.name, action.description[:60]),
                    date_deadline=action.due_date,
                    user_id=action.owner_user_id.id)

    def action_cancel(self):
        self.write({"state": "cancelled"})


class GteMeetingAction(models.Model):
    _name = "cs.meeting.action"
    _description = "Meeting Action Item"
    _order = "due_date"

    meeting_id = fields.Many2one("cs.meeting", required=True, ondelete="cascade")
    description = fields.Char(required=True)
    owner_user_id = fields.Many2one("res.users", string="Owner")
    owner_partner_id = fields.Many2one("res.partner", string="External Owner")
    due_date = fields.Date()
    state = fields.Selection([("open", "Open"), ("done", "Done")],
                             default="open")
    related_rfi_id = fields.Many2one("cs.rfi", string="Related RFI")
    related_co_id = fields.Many2one("cs.change.order", string="Related Change")


class GteCloseoutItem(models.Model):
    _name = "cs.closeout.item"
    _description = "Closeout Register Item"
    _inherit = ["mail.thread", "cs.legacy.mixin"]
    _order = "project_id, category, id"

    name = fields.Char(string="Item", required=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    category = fields.Selection([
        ("om", "O&M Manual"), ("asbuilt", "As-Built Drawing"),
        ("warranty", "Warranty"), ("training", "Training"),
        ("commissioning", "Testing & Commissioning"),
        ("esa", "ESA / Inspection"), ("deficiency", "Deficiency Completion"),
        ("other", "Other")], required=True, default="om", tracking=True)
    responsible_id = fields.Many2one("res.partner", string="Responsible")
    date_required = fields.Date(string="Required")
    date_received = fields.Date()
    date_reviewed = fields.Date()
    date_accepted = fields.Date()
    attachment_ids = fields.Many2many("ir.attachment", string="Documents")
    state = fields.Selection([
        ("required", "Required"), ("received", "Received"),
        ("reviewed", "Reviewed"), ("accepted", "Accepted"),
        ("na", "N/A")], default="required", tracking=True, index=True)

    def action_received(self):
        self.write({"state": "received",
                    "date_received": fields.Date.context_today(self)})

    def action_reviewed(self):
        self.write({"state": "reviewed",
                    "date_reviewed": fields.Date.context_today(self)})

    def action_accepted(self):
        for rec in self:
            if not rec.attachment_ids:
                raise ValidationError(
                    "Attach the document before accepting %s." % rec.name)
            rec.write({"state": "accepted",
                       "date_accepted": fields.Date.context_today(self)})

    def action_na(self):
        self.write({"state": "na"})


class GteInspection(models.Model):
    _inherit = "cs.inspection"

    punch_item_ids = fields.One2many("cs.punch.item", "inspection_id",
                                     string="Deficiencies")
    punch_count = fields.Integer(compute="_compute_punch_count")

    def _compute_punch_count(self):
        for rec in self:
            rec.punch_count = len(rec.punch_item_ids)

    def action_create_deficiency(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.punch.item",
            "view_mode": "form", "target": "current",
            "context": {"default_project_id": self.project_id.id,
                        "default_inspection_id": self.id,
                        "default_date_identified": fields.Date.context_today(self)},
        }

    def action_view_deficiencies(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "cs.punch.item",
            "view_mode": "list,form", "domain": [("inspection_id", "=", self.id)],
            "context": {"default_project_id": self.project_id.id,
                        "default_inspection_id": self.id},
        }
