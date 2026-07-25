from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_baseline_start = fields.Date(string="Baseline Start")
    cs_baseline_end = fields.Date(string="Baseline Finish")
    cs_forecast_start = fields.Date(string="Forecast Start")
    cs_forecast_end = fields.Date(string="Forecast Finish")
    cs_delay_event_ids = fields.One2many("cs.delay.event", "project_id")
    cs_delay_count = fields.Integer(compute="_compute_cs_schedule")
    cs_schedule_impact_days = fields.Integer(
        string="Total Schedule Impact (days)", compute="_compute_cs_schedule",
        help="Open delay-event days + schedule-impact days from open RFIs, "
             "change orders and field issues on this project.")

    def _compute_cs_schedule(self):
        for rec in self:
            delays = rec.cs_delay_event_ids.filtered(lambda d: d.state == "open")
            rec.cs_delay_count = len(rec.cs_delay_event_ids)
            days = sum(delays.mapped("days_impact"))
            rfi_days = sum(self.env["cs.rfi"].search([
                ("project_id", "=", rec.id), ("schedule_impact", "=", "yes"),
                ("state", "in", ("draft", "open", "sent", "answered")),
            ]).mapped("schedule_days"))
            co_days = sum(self.env["cs.change.order"].search([
                ("project_id", "=", rec.id),
                ("state", "not in", ("closed", "cancelled", "rejected")),
            ]).mapped("schedule_days"))
            fi_days = sum(self.env["cs.field.issue"].search([
                ("project_id", "=", rec.id), ("schedule_impact", "=", "yes"),
                ("state", "not in", ("cancelled",)),
            ]).mapped("schedule_days"))
            rec.cs_schedule_impact_days = days + rfi_days + co_days + fi_days

    def action_view_cs_delays(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "cs.delay.event",
            "name": "Delay Events", "view_mode": "list,form,calendar",
            "domain": [("project_id", "=", self.id)],
            "context": {"default_project_id": self.id},
        }
