from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    gte_dsl_count = fields.Integer(compute="_compute_gte_dsl_count")

    def _compute_gte_dsl_count(self):
        for rec in self:
            rec.gte_dsl_count = self.env["gte.daily.log"].search_count(
                [("project_id", "=", rec.id)])

    def action_view_gte_dsls(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("gte_field.action_gte_dsl")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action
