from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_flha_count = fields.Integer(compute="_compute_cs_hse_counts")
    cs_tbt_count = fields.Integer(compute="_compute_cs_hse_counts")
    cs_incident_count = fields.Integer(compute="_compute_cs_hse_counts")

    def _compute_cs_hse_counts(self):
        for rec in self:
            rec.cs_flha_count = self.env["cs.flha"].search_count(
                [("project_id", "=", rec.id)])
            rec.cs_tbt_count = self.env["cs.toolbox.talk"].search_count(
                [("project_id", "=", rec.id)])
            rec.cs_incident_count = self.env["cs.incident"].search_count(
                [("project_id", "=", rec.id)])

    def action_view_cs_flhas(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("cs_hse.action_cs_flha")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action

    def action_view_cs_tbts(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("cs_hse.action_cs_tbt")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action

    def action_view_cs_incidents(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("cs_hse.action_cs_incident")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action
