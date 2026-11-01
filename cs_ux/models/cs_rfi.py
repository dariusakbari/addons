from odoo import api, fields, models
from .lifecycle import build_lifecycle_html


class CsRfi(models.Model):
    _inherit = "cs.rfi"

    # "To Do" hint shown in the list, mirroring the reference board's
    # next-action column. Non-stored: computed for the rows on screen.
    cs_next_action = fields.Char(
        string="To Do", compute="_compute_cs_next_action")

    # SmartBuild-style workflow timeline, derived from state + existing dates
    # (no double entry — the header buttons remain the way to advance).
    cs_lifecycle = fields.Html(
        string="Workflow", compute="_compute_cs_lifecycle", sanitize=False)

    @api.depends("state", "date_raised", "date_required",
                 "date_answered", "date_distributed")
    def _compute_cs_lifecycle(self):
        today = fields.Date.context_today(self)
        for rec in self:
            st = rec.state
            issued = st not in ("draft", "open")
            steps = [
                {"name": "Issue RFI", "due": rec.date_raised,
                 "done": issued,
                 "completed": rec.date_raised if issued else False},
                {"name": "Obtain Response", "due": rec.date_required,
                 "done": st in ("answered", "distributed", "closed"),
                 "completed": rec.date_answered},
                {"name": "Distribute Response", "due": rec.date_required,
                 "done": st in ("distributed", "closed"),
                 "completed": rec.date_distributed},
            ]
            rec.cs_lifecycle = build_lifecycle_html(steps, today)

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
