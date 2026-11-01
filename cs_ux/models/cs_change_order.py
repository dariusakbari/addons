from odoo import api, fields, models
from .lifecycle import build_lifecycle_html


class CsChangeOrder(models.Model):
    _inherit = "cs.change.order"

    _OPEN_STATES = ("draft", "pricing", "review", "submitted", "changes")

    # Overdue = a decision is still pending past its required-decision date.
    is_overdue = fields.Boolean(compute="_compute_is_overdue")
    cs_next_action = fields.Char(
        string="To Do", compute="_compute_cs_next_action")
    cs_lifecycle = fields.Html(
        string="Workflow", compute="_compute_cs_lifecycle", sanitize=False)

    @api.depends("state", "date_quote", "date_submitted",
                 "date_required", "date_decision", "date_billed")
    def _compute_cs_lifecycle(self):
        today = fields.Date.context_today(self)
        quoted = ("submitted", "changes", "approved", "rejected",
                  "billed", "paid", "closed")
        approved = ("approved", "billed", "paid", "closed")
        ordered = ("billed", "paid", "closed")
        for rec in self:
            st = rec.state
            steps = [
                {"name": "Change Received", "due": rec.date_quote,
                 "done": True, "completed": rec.date_quote},
                {"name": "Issue Quotation", "due": rec.date_quote,
                 "done": st in quoted, "completed": rec.date_submitted},
                {"name": "Obtain Approval", "due": rec.date_required,
                 "done": st in approved, "completed": rec.date_decision},
                {"name": "Issue Change Order", "due": rec.date_decision,
                 "done": st in ordered, "completed": rec.date_billed},
            ]
            rec.cs_lifecycle = build_lifecycle_html(steps, today)

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
