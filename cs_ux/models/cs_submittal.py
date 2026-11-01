from odoo import api, fields, models
from .lifecycle import build_lifecycle_html


class CsSubmittal(models.Model):
    _inherit = "cs.submittal"

    _PENDING_STATES = ("draft", "requested", "received", "review",
                       "submitted", "revise")

    # Overdue = still not submitted past its required-submission date.
    is_submit_overdue = fields.Boolean(compute="_compute_is_submit_overdue")
    cs_next_action = fields.Char(
        string="To Do", compute="_compute_cs_next_action")
    cs_lifecycle = fields.Html(
        string="Workflow", compute="_compute_cs_lifecycle", sanitize=False)

    @api.depends("state", "date_received", "date_submitted",
                 "date_returned", "date_required_submit",
                 "date_required_onsite")
    def _compute_cs_lifecycle(self):
        today = fields.Date.context_today(self)
        requested = ("requested", "received", "review", "submitted",
                     "approved", "approved_noted", "revise", "rejected",
                     "closed")
        received = ("received", "review", "submitted", "approved",
                    "approved_noted", "revise", "rejected", "closed")
        submitted = ("submitted", "approved", "approved_noted", "revise",
                     "rejected", "closed")
        approved = ("approved", "approved_noted", "closed")
        for rec in self:
            st = rec.state
            steps = [
                {"name": "Request from Supplier",
                 "due": rec.date_required_submit, "done": st in requested,
                 "completed": False},
                {"name": "Receive from Supplier", "due": False,
                 "done": st in received, "completed": rec.date_received},
                {"name": "Submit for Review",
                 "due": rec.date_required_submit, "done": st in submitted,
                 "completed": rec.date_submitted},
                {"name": "Obtain Approval",
                 "due": rec.date_required_onsite, "done": st in approved,
                 "completed": rec.date_returned},
            ]
            rec.cs_lifecycle = build_lifecycle_html(steps, today)

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
