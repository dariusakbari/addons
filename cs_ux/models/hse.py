from odoo import fields, models


class CsFlha(models.Model):
    _inherit = "cs.flha"

    # Pre-fill the foreman with the person completing the FLHA.
    foreman_id = fields.Many2one(default=lambda self: self.env.user)


class CsToolboxTalk(models.Model):
    _inherit = "cs.toolbox.talk"

    # Pre-fill the presenter with the person logging the toolbox talk.
    presenter_id = fields.Many2one(default=lambda self: self.env.user)
