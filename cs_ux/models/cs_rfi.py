from odoo import api, fields, models


class CsRfi(models.Model):
    _inherit = "cs.rfi"

    # "To Do" hint shown in the list, mirroring the reference board's
    # next-action column. Non-stored: computed for the rows on screen.
    cs_next_action = fields.Char(
        string="To Do", compute="_compute_cs_next_action")

    @api.depends("state")
    def _compute_cs_next_action(self):
        labels = {
            "draft": "Issue RFI",
            "open": "Send to recipient",
            "sent": "Awaiting response",
            "answered": "Distribute response",
            "distributed": "Close out",
        }
        for rec in self:
            rec.cs_next_action = labels.get(rec.state, "")
