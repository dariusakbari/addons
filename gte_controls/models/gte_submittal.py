from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteSubmittalSpec(models.Model):
    _name = "gte.submittal.spec"
    _description = "Standard Submittal Specification"
    _order = "number"

    number = fields.Char(string="Spec Section", required=True, index=True)
    name = fields.Char(string="Title", required=True)
    division = fields.Char()
    active = fields.Boolean(default=True)
    legacy_source_id = fields.Char(copy=False, index=True)


class GteSubmittal(models.Model):
    _name = "gte.submittal"
    _description = "Submittal"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "project_id, name desc"

    name = fields.Char(string="Submittal Number", readonly=True, copy=False, default="New")
    title = fields.Char(required=True, tracking=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    spec_id = fields.Many2one("gte.submittal.spec", string="Standard Spec")
    spec_section = fields.Char(string="Specification Section", tracking=True)
    supplier_id = fields.Many2one("res.partner", string="Supplier", tracking=True)
    contractor_id = fields.Many2one("res.partner", string="Responsible Contractor")
    coordinator_id = fields.Many2one("res.users", string="Project Coordinator",
                                     default=lambda self: self.env.user, tracking=True)
    reviewer_id = fields.Many2one("res.partner", string="Reviewer", tracking=True)
    revision_ids = fields.One2many("gte.submittal.revision", "submittal_id", copy=False)
    current_revision = fields.Integer(compute="_compute_current_revision", store=True)
    date_required_onsite = fields.Date(string="Required On Site", tracking=True)
    date_required_submit = fields.Date(string="Required Submission", tracking=True)
    date_received = fields.Date(tracking=True)
    date_submitted = fields.Date(tracking=True)
    date_returned = fields.Date(tracking=True)
    outcome = fields.Selection([
        ("approved", "Approved"), ("approved_noted", "Approved as Noted"),
        ("revise", "Revise and Resubmit"), ("rejected", "Rejected")],
        tracking=True, copy=False)
    comments = fields.Html(string="Reviewer Comments")
    drawing_ref = fields.Char(string="Linked Drawing")
    rfi_id = fields.Many2one("gte.rfi", string="Linked RFI", copy=False)
    task_ids = fields.Many2many("project.task", string="Related Tasks")
    distribution_ids = fields.Many2many("res.partner", "gte_submittal_distribution_rel",
                                        string="Distribution List")
    state = fields.Selection([
        ("draft", "Draft"), ("requested", "Requested"), ("received", "Received"),
        ("review", "Internal Review"), ("submitted", "Submitted"),
        ("approved", "Approved"), ("approved_noted", "Approved as Noted"),
        ("revise", "Revise and Resubmit"), ("rejected", "Rejected"),
        ("closed", "Closed"), ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    _submittal_number_project_uniq = models.Constraint(
        "unique(project_id, name)",
        "Submittal number must be unique per project.",
    )

    @api.depends("revision_ids.revision")
    def _compute_current_revision(self):
        for rec in self:
            rec.current_revision = max(rec.revision_ids.mapped("revision"), default=0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._gte_next_number(project, "gte.submittal", "SUB")
        return super().create(vals_list)

    def _set_state(self, allowed_from, new_state, extra_vals=None):
        for rec in self:
            if rec.state not in allowed_from:
                raise ValidationError(
                    "Invalid transition %s -> %s on %s" % (rec.state, new_state, rec.name))
            rec.write(dict(extra_vals or {}, state=new_state))

    def action_request(self):
        for rec in self:
            if not rec.supplier_id and not rec.contractor_id:
                raise ValidationError(
                    "Supplier or responsible contractor required on %s." % rec.name)
        self._set_state(("draft", "revise"), "requested")

    def action_receive(self):
        self._set_state(("requested",), "received",
                        {"date_received": fields.Date.context_today(self)})

    def action_review(self):
        self._set_state(("received",), "review")

    def action_submit(self):
        """Submitting creates a new immutable revision. A resubmission never
        overwrites the previous revision's files or response."""
        today = fields.Date.context_today(self)
        for rec in self:
            rec.env["gte.submittal.revision"].create({
                "submittal_id": rec.id,
                "revision": rec.current_revision + (1 if rec.revision_ids else 0),
                "date_submitted": today,
            })
        self._set_state(("review",), "submitted", {"date_submitted": today})

    def _action_return(self, outcome):
        today = fields.Date.context_today(self)
        for rec in self:
            rev = rec.revision_ids.sorted("revision")[-1:]
            if rev:
                rev.write({"outcome": outcome, "date_returned": today,
                           "comments": rec.comments})
        self._set_state(("submitted",), outcome,
                        {"outcome": outcome, "date_returned": today})

    def action_approve(self):
        self._action_return("approved")

    def action_approve_noted(self):
        self._action_return("approved_noted")

    def action_revise(self):
        self._action_return("revise")

    def action_reject(self):
        self._action_return("rejected")

    def action_close(self):
        self._set_state(("approved", "approved_noted", "rejected"), "closed")

    def action_cancel(self):
        self._set_state(("draft", "requested", "received"), "cancelled")


class GteSubmittalRevision(models.Model):
    _name = "gte.submittal.revision"
    _description = "Submittal Revision"
    _order = "submittal_id, revision"

    submittal_id = fields.Many2one("gte.submittal", required=True, ondelete="cascade")
    revision = fields.Integer(required=True, default=0)
    date_submitted = fields.Date()
    date_returned = fields.Date()
    outcome = fields.Selection([
        ("approved", "Approved"), ("approved_noted", "Approved as Noted"),
        ("revise", "Revise and Resubmit"), ("rejected", "Rejected")])
    comments = fields.Html()
    attachment_ids = fields.Many2many("ir.attachment", string="Files")

    _revision_uniq = models.Constraint(
        "unique(submittal_id, revision)",
        "Revision numbers must be unique per submittal.",
    )
