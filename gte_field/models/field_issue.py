from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteFieldIssue(models.Model):
    """Field-originated item. Field crews raise issues from site; the PM
    reviews and, where warranted, releases an RFI from the issue. Field
    employees never touch RFIs directly."""

    _name = "gte.field.issue"
    _description = "Field Issue"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    raised_by_id = fields.Many2one("res.users", string="Raised By",
                                   default=lambda self: self.env.user, tracking=True)
    issue_type = fields.Selection([
        ("question", "Question for Consultant"),
        ("obstruction", "Obstruction / Site Condition"),
        ("design", "Design Conflict"),
        ("material", "Material / Product Issue"),
        ("other", "Other")], required=True, default="question", tracking=True)
    title = fields.Char(required=True, tracking=True)
    description = fields.Text(string="Details")
    location = fields.Char()
    drawing_refs = fields.Char(string="Drawing References")
    photo_ids = fields.Many2many("ir.attachment", string="Photos")
    rfi_id = fields.Many2one("gte.rfi", string="Released RFI", readonly=True,
                             copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("submitted", "Sent to PM"),
        ("converted", "RFI Released"), ("resolved", "Resolved"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.field.issue", "FI")
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if not rec.description:
                raise ValidationError(
                    "Describe the issue before sending it to the PM (%s)." % rec.name)
            rec.state = "submitted"
            pm = rec.project_id.user_id
            if pm:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Field issue %s — review and release RFI if needed" % rec.name,
                    user_id=pm.id)

    def action_release_rfi(self):
        """PM releases an RFI prefilled from the field issue."""
        self.ensure_one()
        if self.state != "submitted":
            raise ValidationError("Only submitted issues can be released as RFIs.")
        rfi = self.env["gte.rfi"].create({
            "subject": self.title,
            "project_id": self.project_id.id,
            "question": "<p>%s</p><p><em>Raised from field issue %s by %s on %s "
                        "(%s).</em></p>" % (
                            (self.description or "").replace("\n", "<br/>"),
                            self.name, self.raised_by_id.name, self.date,
                            self.location or "location n/a"),
            "drawing_refs": self.drawing_refs,
            "date_raised": fields.Date.context_today(self),
            "coordinator_id": self.env.user.id,
        })
        if self.photo_ids:
            for att in self.photo_ids:
                att.copy({"res_model": "gte.rfi", "res_id": rfi.id})
        self.write({"state": "converted", "rfi_id": rfi.id})
        self.message_post(body="RFI %s released by %s." % (rfi.name, self.env.user.name))
        return {
            "type": "ir.actions.act_window", "res_model": "gte.rfi",
            "res_id": rfi.id, "view_mode": "form",
        }

    def action_resolve(self):
        self.write({"state": "resolved"})

    def action_cancel(self):
        for rec in self:
            if rec.state == "converted":
                raise ValidationError("Issues with a released RFI cannot be cancelled.")
            rec.state = "cancelled"
