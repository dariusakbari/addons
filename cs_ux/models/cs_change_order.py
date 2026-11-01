from odoo import api, fields, models


class CsChangeOrder(models.Model):
    _inherit = "cs.change.order"

    _OPEN_STATES = ("draft", "pricing", "review", "submitted", "changes")

    # Overdue = a decision is still pending past its required-decision date.
    is_overdue = fields.Boolean(compute="_compute_is_overdue")
    cs_next_action = fields.Char(
        string="To Do", compute="_compute_cs_next_action")

    @api.depends("date_required", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_overdue = bool(
                rec.date_required and rec.date_required < today
                and rec.state in self._OPEN_STATES)

    @api.depends("state")
    def _compute_cs_next_action(self):
        labels = {
            "draft": "Price the change",
            "pricing": "Internal review",
            "review": "Submit to client",
            "submitted": "Awaiting client decision",
            "changes": "Revise & resubmit",
            "approved": "Bill the change",
            "billed": "Collect payment",
        }
        for rec in self:
            rec.cs_next_action = labels.get(rec.state, "")
