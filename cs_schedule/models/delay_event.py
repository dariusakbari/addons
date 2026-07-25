from odoo import api, fields, models


class CsDelayEvent(models.Model):
    _name = "cs.delay.event"
    _description = "Delay Event"
    _inherit = ["mail.thread", "cs.legacy.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today,
                       tracking=True)
    cause = fields.Selection([
        ("rfi", "Awaiting RFI Response"), ("change", "Change Order"),
        ("weather", "Weather"), ("access", "Site Access"),
        ("material", "Material / Delivery"), ("owner", "Owner Directed"),
        ("design", "Design / Consultant"), ("labour", "Labour"),
        ("other", "Other")], required=True, default="other", tracking=True)
    days_impact = fields.Integer(string="Schedule Impact (days)", tracking=True)
    description = fields.Text()
    rfi_id = fields.Many2one("cs.rfi", string="Related RFI")
    change_order_id = fields.Many2one("cs.change.order", string="Related Change")
    daily_log_id = fields.Many2one("cs.daily.log", string="From Daily Log")
    field_issue_id = fields.Many2one("cs.field.issue", string="From Field Issue")
    state = fields.Selection([
        ("open", "Open"), ("mitigated", "Mitigated"),
        ("closed", "Closed")], default="open", tracking=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.delay.event", "DLY")
        return super().create(vals_list)

    def action_mitigate(self):
        self.write({"state": "mitigated"})

    def action_close(self):
        self.write({"state": "closed"})
