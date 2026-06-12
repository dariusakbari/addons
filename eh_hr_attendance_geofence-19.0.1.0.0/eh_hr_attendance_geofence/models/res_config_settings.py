# -*- encoding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    eh_hr_mobile_default_radius_m = fields.Integer(
        related='company_id.eh_hr_mobile_default_radius_m',
        readonly=False,
    )
