from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gte_co_approval_limit = fields.Float(
        string="CO approval limit",
        config_parameter="gte.co_approval_limit",
        help="Change orders approved above this amount require a "
             "Construction Administrator. 0 disables the threshold.")
    gte_rfi_reminder_days = fields.Integer(
        string="RFI reminder lead (days)",
        config_parameter="gte.rfi_reminder_days", default=2)
    gte_submittal_reminder_days = fields.Integer(
        string="Submittal reminder lead (days)",
        config_parameter="gte.submittal_reminder_days", default=7)
