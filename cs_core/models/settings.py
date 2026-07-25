from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cs_co_approval_limit = fields.Float(
        string="CO approval limit",
        config_parameter="cs.co_approval_limit",
        help="Change orders approved above this amount require a "
             "Construction Administrator. 0 disables the threshold.")
    cs_rfi_reminder_days = fields.Integer(
        string="RFI reminder lead (days)",
        config_parameter="cs.rfi_reminder_days", default=2)
    cs_submittal_reminder_days = fields.Integer(
        string="Submittal reminder lead (days)",
        config_parameter="cs.submittal_reminder_days", default=7)
    cs_holdback_percent = fields.Float(
        string="Default holdback %",
        config_parameter="cs.holdback_percent", default=10.0,
        help="Percentage withheld on progress billing. Overridable per project.")
