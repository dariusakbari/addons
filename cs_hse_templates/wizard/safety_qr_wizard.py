from odoo import api, fields, models


class CsSafetyQrWizard(models.TransientModel):
    _name = "cs.safety.qr.wizard"
    _description = "Safety QR Poster"

    template_id = fields.Many2one(
        "cs.safety.template", string="Template", required=True,
        domain="[('state','=','published')]")
    project_id = fields.Many2one(
        "project.project", string="Project (optional)",
        help="Leave empty for a generic QR; pick a project to pre-fill it on "
             "the report.")
    url = fields.Char(compute="_compute_qr", readonly=True)
    qr_image = fields.Image(compute="_compute_qr", readonly=True)

    @api.depends("template_id", "project_id")
    def _compute_qr(self):
        from odoo.addons.cs_hse.models.registers import _cs_make_qr
        for wiz in self:
            if wiz.template_id:
                url = wiz.template_id._qr_target_url(
                    project_id=wiz.project_id.id or False)
                wiz.url = url
                wiz.qr_image = _cs_make_qr(url)
            else:
                wiz.url = False
                wiz.qr_image = False
