from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    gte_flha_count = fields.Integer(compute="_compute_gte_hse_counts")
    gte_tbt_count = fields.Integer(compute="_compute_gte_hse_counts")
    gte_incident_count = fields.Integer(compute="_compute_gte_hse_counts")

    def _compute_gte_hse_counts(self):
        for rec in self:
            rec.gte_flha_count = self.env["gte.flha"].search_count(
                [("project_id", "=", rec.id)])
            rec.gte_tbt_count = self.env["gte.toolbox.talk"].search_count(
                [("project_id", "=", rec.id)])
            rec.gte_incident_count = self.env["gte.incident"].search_count(
                [("project_id", "=", rec.id)])

    def action_view_gte_flhas(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("gte_hse.action_gte_flha")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action

    def action_view_gte_tbts(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("gte_hse.action_gte_tbt")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action

    def action_view_gte_incidents(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("gte_hse.action_gte_incident")
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        return action
