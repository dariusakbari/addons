from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    gte_doc_number = fields.Char(string="Document No.", index=True)
    gte_doc_type = fields.Selection([
        ("drawing", "Drawing"), ("specification", "Specification"),
        ("contract", "Contract / PO"), ("submittal", "Submittal"),
        ("report", "Report"), ("photo", "Photo"),
        ("closeout", "Closeout / As-Built"), ("other", "Other")],
        string="Document Type")
    gte_discipline = fields.Selection([
        ("electrical", "Electrical"), ("mechanical", "Mechanical"),
        ("structural", "Structural"), ("architectural", "Architectural"),
        ("civil", "Civil"), ("other", "Other")], string="Discipline")
    gte_revision = fields.Char(string="Revision", default="0")
    gte_doc_status = fields.Selection([
        ("current", "Current"), ("superseded", "Superseded")],
        string="Revision Status", default="current", index=True)
    gte_superseded_by_id = fields.Many2one(
        "documents.document", string="Superseded By", readonly=True, copy=False)
    gte_issue_date = fields.Date(string="Issue Date")
    gte_source = fields.Char(string="Author / Source")
    gte_rfi_id = fields.Many2one("gte.rfi", string="Linked RFI")
    gte_co_id = fields.Many2one("gte.change.order", string="Linked Change Order")
    gte_submittal_id = fields.Many2one("gte.submittal", string="Linked Submittal")
    gte_task_id = fields.Many2one("project.task", string="Linked Task")

    def action_gte_register_revision(self):
        """Open the revision wizard with this (new) document preselected."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "gte.document.revision.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_new_document_id": self.id},
        }


class GteDocumentRevisionWizard(models.TransientModel):
    _name = "gte.document.revision.wizard"
    _description = "Register Document Revision"

    new_document_id = fields.Many2one(
        "documents.document", string="New Revision (this file)", required=True,
        domain="[('type', '=', 'binary')]")
    predecessor_id = fields.Many2one(
        "documents.document", string="Supersedes", required=True,
        domain="[('type', '=', 'binary'), ('gte_doc_status', '=', 'current')]")
    revision = fields.Char(string="New Revision Label")

    @api.onchange("predecessor_id")
    def _onchange_predecessor(self):
        if self.predecessor_id and not self.revision:
            old = self.predecessor_id.gte_revision or "0"
            self.revision = str(int(old) + 1) if old.isdigit() else ""

    def action_apply(self):
        self.ensure_one()
        new, old = self.new_document_id, self.predecessor_id
        if new == old:
            raise ValidationError("A document cannot supersede itself.")
        if old.gte_superseded_by_id:
            raise ValidationError(
                "%s is already superseded by %s." % (
                    old.display_name, old.gte_superseded_by_id.display_name))
        if not self.revision:
            raise ValidationError("A new revision label is required.")
        # Never overwrite: the old file and record stay exactly as they are,
        # only status and link change. Metadata carries forward to the new rev.
        new.write({
            "gte_doc_number": old.gte_doc_number,
            "gte_doc_type": old.gte_doc_type,
            "gte_discipline": old.gte_discipline,
            "gte_revision": self.revision,
            "gte_doc_status": "current",
            "gte_rfi_id": old.gte_rfi_id.id,
            "gte_co_id": old.gte_co_id.id,
            "gte_submittal_id": old.gte_submittal_id.id,
            "gte_task_id": old.gte_task_id.id,
            "folder_id": old.folder_id.id,
        })
        old.write({"gte_doc_status": "superseded", "gte_superseded_by_id": new.id})
        old.message_post(body="Superseded by %s (rev %s)." % (
            new.display_name, self.revision))
        new.message_post(body="Registered as revision %s, superseding %s (rev %s)." % (
            self.revision, old.display_name, old.gte_revision or "0"))
        return {"type": "ir.actions.act_window_close"}
