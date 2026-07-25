from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_dsl_count = fields.Integer(compute="_compute_cs_dsl_count")

    def _compute_cs_dsl_count(self):
        for rec in self:
            rec.cs_dsl_count = self.env["cs.daily.log"].search_count(
                [("project_id", "=", rec.id)])

    def action_view_cs_dsls(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("cs_field.action_cs_dsl")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action
