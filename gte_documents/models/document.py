import base64
import io
import zipfile

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Document type -> project template folder name
TYPE_FOLDER = {
    "contract": "01 Contracts and Purchase Orders",
    "drawing": "02 Drawings",
    "specification": "03 Specifications",
    "submittal": "06 Submittals",
    "report": "07 Daily Reports",
    "photo": "09 Photos",
    "closeout": "11 Closeout and As-Builts",
}


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

    def gte_auto_folder(self):
        """Move each document into the correct project subfolder based on
        its type, when a matching subfolder exists under the document's
        current project root."""
        moved = 0
        for doc in self:
            target_name = TYPE_FOLDER.get(doc.gte_doc_type)
            if not target_name or not doc.folder_id:
                continue
            # find the project root: walk up until parent is "Projects"
            root = doc.folder_id
            while root.folder_id and root.folder_id.name != "Projects":
                root = root.folder_id
            target = self.env["documents.document"].search(
                [("type", "=", "folder"), ("name", "=", target_name),
                 ("folder_id", "=", root.id)], limit=1)
            if target and doc.folder_id != target:
                doc.folder_id = target
                moved += 1
        return moved

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
        "documents.document", string="New Revision (existing document)",
        domain="[('type', '=', 'binary')]",
        help="Either pick an already-uploaded document or upload the file below.")
    predecessor_id = fields.Many2one(
        "documents.document", string="Supersedes", required=True,
        domain="[('type', '=', 'binary'), ('gte_doc_status', '=', 'current')]")
    revision = fields.Char(string="New Revision Label")

    new_file = fields.Binary(string="Upload New Revision File",
                             help="Optional: upload the file here and the new "
                                  "revision document is created for you.")
    new_file_name = fields.Char()

    @api.onchange("predecessor_id")
    def _onchange_predecessor(self):
        if self.predecessor_id and not self.revision:
            old = self.predecessor_id.gte_revision or "0"
            self.revision = str(int(old) + 1) if old.isdigit() else ""

    def action_apply(self):
        self.ensure_one()
        new = self.new_document_id
        if not new and self.new_file:
            new = self.env["documents.document"].create({
                "name": self.new_file_name or "%s rev %s" % (
                    self.predecessor_id.name, self.revision or "?"),
                "type": "binary",
                "datas": self.new_file,
                "folder_id": self.predecessor_id.folder_id.id,
            })
        if not new:
            raise ValidationError("Select an existing document or upload a file.")
        old = self.predecessor_id
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


class GteDocumentMetadataWizard(models.TransientModel):
    """Mass-set construction metadata on selected documents, then auto-file
    them into the correct project subfolder."""

    _name = "gte.document.metadata.wizard"
    _description = "Set Document Metadata"

    document_ids = fields.Many2many("documents.document", required=True)
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
    gte_issue_date = fields.Date(string="Issue Date")
    gte_source = fields.Char(string="Author / Source")
    auto_folder = fields.Boolean(string="File into project subfolder", default=True)

    def action_apply(self):
        self.ensure_one()
        vals = {}
        for f in ("gte_doc_type", "gte_discipline", "gte_issue_date", "gte_source"):
            if self[f]:
                vals[f] = self[f] if f != "gte_issue_date" else self.gte_issue_date
        docs = self.document_ids
        if vals:
            docs.write(vals)
        if self.auto_folder:
            docs.gte_auto_folder()
        return {"type": "ir.actions.act_window_close"}


class GteIssuePackageWizard(models.TransientModel):
    """Zip the CURRENT revisions of the selected documents into a single
    downloadable issue package. Superseded revisions are excluded."""

    _name = "gte.issue.package.wizard"
    _description = "Download Issue Package"

    document_ids = fields.Many2many("documents.document", required=True)
    name = fields.Char(string="Package Name", required=True,
                       default=lambda self: "Issue Package %s" %
                       fields.Date.context_today(self))

    def action_download(self):
        self.ensure_one()
        docs = self.document_ids.filtered(
            lambda d: d.type == "binary" and d.gte_doc_status != "superseded")
        if not docs:
            raise ValidationError(
                "No current-revision files in the selection (superseded "
                "revisions are excluded from issue packages).")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for d in docs:
                if not d.datas:
                    continue
                label = d.gte_doc_number or d.name
                rev = d.gte_revision or "0"
                fname = "%s_rev%s_%s" % (label, rev, d.name)
                zf.writestr(fname, base64.b64decode(d.datas))
        att = self.env["ir.attachment"].create({
            "name": "%s.zip" % self.name,
            "datas": base64.b64encode(buf.getvalue()),
            "res_model": self._name, "res_id": self.id,
            "mimetype": "application/zip",
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % att.id,
            "target": "self",
        }


class DocumentsDocumentTransmittal(models.Model):
    _inherit = "documents.document"

    def action_gte_create_transmittal(self):
        """Create a transmittal from the selected documents, freezing the
        exact revisions included. Superseded revisions are refused."""
        docs = self.filtered(lambda d: d.type == "binary")
        if not docs:
            raise ValidationError("Select at least one file.")
        superseded = docs.filtered(lambda d: d.gte_doc_status == "superseded")
        if superseded:
            raise ValidationError(
                "Superseded revisions cannot be transmitted: %s" %
                ", ".join(superseded.mapped("name")))
        # project: from the folder tree of the first doc
        root = docs[0].folder_id
        while root and root.folder_id and root.folder_id.name != "Projects":
            root = root.folder_id
        project = self.env["project.project"].search(
            [("name", "=", root.name)], limit=1) if root else None
        if not project:
            raise ValidationError(
                "Could not determine the project from the document folder. "
                "File the documents under a project folder first.")
        tr = self.env["gte.transmittal"].create({
            "project_id": project.id,
            "description": "Issued from Drawings & Documents register.",
        })
        for d in docs:
            self.env["gte.transmittal.line"].create({
                "transmittal_id": tr.id,
                "description": "%s — %s" % (d.gte_doc_number or "n/a", d.name),
                "quantity": 1,
                "doc_format": d.mimetype or "",
                "revision": d.gte_revision or "0",
            })
            att = self.env["ir.attachment"].create({
                "name": d.name, "datas": d.datas,
                "res_model": "gte.transmittal", "res_id": tr.id,
            })
            tr.attachment_ids = [(4, att.id)]
        tr.message_post(body="Created from document register with frozen "
                             "revisions: %s" % ", ".join(
                                 "%s rev %s" % (d.name, d.gte_revision or "0")
                                 for d in docs))
        return {"type": "ir.actions.act_window", "res_model": "gte.transmittal",
                "res_id": tr.id, "view_mode": "form"}
