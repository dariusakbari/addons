from odoo import api, fields, models


class CsSubmittal(models.Model):
    _inherit = "cs.submittal"

    _PENDING_STATES = ("draft", "requested", "received", "review",
                       "submitted", "revise")

    # Overdue = still not submitted past its required-submission date.
    is_submit_overdue = fields.Boolean(compute="_compute_is_submit_overdue")
    cs_next_action = fields.Char(
        string="To Do", compute="_compute_cs_next_action")

    @api.depends("date_required_submit", "state")
    def _compute_is_submit_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_submit_overdue = bool(
                rec.date_required_submit and rec.date_required_submit < today
                and rec.state in self._PENDING_STATES)

    @api.depends("state")
    def _compute_cs_next_action(self):
        labels = {
            "draft": "Prepare submittal",
            "requested": "Receive from supplier",
            "received": "Internal review",
            "review": "Submit to consultant",
            "submitted": "Awaiting review",
            "revise": "Revise & resubmit",
        }
        for rec in self:
            rec.cs_next_action = labels.get(rec.state, "")
