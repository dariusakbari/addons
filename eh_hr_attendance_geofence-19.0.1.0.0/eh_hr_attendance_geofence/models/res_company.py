# -*- encoding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    eh_hr_mobile_default_radius_m = fields.Integer(
        string='Mobile geofence radius (m)',
        default=100,
        help="Default radius applied to a site when mobile clock-in checks distance, if the site itself does not declare a custom radius. The kiosk path uses the site's own radius regardless.",
    )
