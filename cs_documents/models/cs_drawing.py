from odoo import api, fields, models
from odoo.exceptions import ValidationError

DOC_TYPES = [
    ("drawing", "Drawing"), ("spec", "Specification"),
    ("submittal", "Submittal"), ("rfi", "RFI Response"),
    ("permit", "Permit"), ("report", "Report"), ("other", "Other"),
]
DISCIPLINES = [
    ("architectural", "Architectural"), ("structural", "Structural"),
    ("mechanical", "Mechanical"), ("electrical", "Electrical"),
    ("plumbing", "Plumbing"), ("civil", "Civil"), ("other", "Other"),
]


class CsDrawing(models.Model):
    """Construction drawing / document register — a dedicated, controllable
    register (independent of the Enterprise Documents app), with revision
    control: a new revision supersedes the prior one."""
    _name = "cs.drawing"
    _description = "Drawing / Document Register"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "project_id, cs_doc_number, revision desc"

    cs_doc_number = fields.Char(string="Document No.", required=True,
                                index=True, tracking=True)
    title = fields.Char(required=True, tracking=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    doc_type = fields.Selection(DOC_TYPES, string="Type", default="drawing",
                                required=True)
    discipline = fields.Selection(DISCIPLINES)
    revision = fields.Char(default="0", required=True, tracking=True)
    status = fields.Selection([("current", "Current"),
                               ("superseded", "Superseded")],
                              default="current", required=True, index=True,
                              tracking=True)
    issue_date = fields.Date(tracking=True)
    source = fields.Char(string="Author / Source")
    file = fields.Binary(string="File", attachment=True)
    file_name = fields.Char()
    predecessor_id = fields.Many2one("cs.drawing", string="Supersedes",
                                     copy=False)
    superseded_by_id = fields.Many2one("cs.drawing", string="Superseded By",
                                       readonly=True, copy=False)
    rfi_id = fields.Many2one("cs.rfi", string="Linked RFI")
    co_id = fields.Many2one("cs.change.order", string="Linked Change Order")
    submittal_id = fields.Many2one("cs.submittal", string="Linked Submittal")
    task_id = fields.Many2one("project.task", string="Linked Task")
    active = fields.Boolean(default=True)

    _doc_rev_uniq = models.Constraint(
        "unique(project_id, cs_doc_number, revision)",
        "That document number and revision already exist on this project.",
    )

    @api.depends("cs_doc_number", "title", "revision")
    def _compute_display_name(self):
        for rec in self:
            parts = [p for p in (rec.cs_doc_number, rec.title) if p]
            label = " — ".join(parts) or "Drawing"
            rec.display_name = "%s (Rev %s)" % (label, rec.revision or "0")

    def action_new_revision(self):
        self.ensure_one()
        if self.status == "superseded":
            raise ValidationError(
                "%s is already superseded by a newer revision." % self.display_name)
        try:
            new_rev = str(int(self.revision or "0") + 1)
        except (TypeError, ValueError):
            new_rev = "%s+" % (self.revision or "0")
        new = self.copy({
            "revision": new_rev, "status": "current",
            "predecessor_id": self.id, "superseded_by_id": False,
            "file": False, "file_name": False,
        })
        self.status = "superseded"
        self.superseded_by_id = new.id
        self.message_post(body="Superseded by revision %s." % new_rev)
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.drawing",
            "res_id": new.id,
            "view_mode": "form",
        }
