from odoo import fields, models


class CsDailyLog(models.Model):
    _inherit = "cs.daily.log"

    # Default the foreman to the person filling the log in — less typing when
    # creating a daily site report from the field.
    foreman_id = fields.Many2one(default=lambda self: self.env.user)
