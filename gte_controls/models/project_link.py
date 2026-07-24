from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    gte_rfi_count = fields.Integer(compute="_compute_gte_counts")
    gte_co_count = fields.Integer(compute="_compute_gte_counts")
    gte_submittal_count = fields.Integer(compute="_compute_gte_counts")
    gte_co_exposure = fields.Monetary(compute="_compute_gte_counts",
                                      currency_field="currency_id")

    def _compute_gte_counts(self):
        for rec in self:
            rec.gte_rfi_count = self.env["gte.rfi"].search_count(
                [("project_id", "=", rec.id)])
            rec.gte_co_count = self.env["gte.change.order"].search_count(
                [("project_id", "=", rec.id)])
            rec.gte_submittal_count = self.env["gte.submittal"].search_count(
                [("project_id", "=", rec.id)])
            cos = self.env["gte.change.order"].search(
                [("project_id", "=", rec.id),
                 ("state", "not in", ("closed", "cancelled", "rejected"))])
            rec.gte_co_exposure = sum(cos.mapped("exposure"))

    def _gte_action(self, xmlid, name):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        action["display_name"] = "%s — %s" % (self.display_name, name)
        return action

    def action_view_gte_rfis(self):
        return self._gte_action("gte_controls.action_gte_rfi", "RFIs")

    def action_view_gte_cos(self):
        return self._gte_action("gte_controls.action_gte_co", "Change Orders")

    def action_view_gte_submittals(self):
        return self._gte_action("gte_controls.action_gte_submittal", "Submittals")


class ProjectTask(models.Model):
    _inherit = "project.task"

    gte_rfi_count = fields.Integer(compute="_compute_gte_counts")
    gte_co_count = fields.Integer(compute="_compute_gte_counts")
    gte_submittal_count = fields.Integer(compute="_compute_gte_counts")

    def _compute_gte_counts(self):
        for rec in self:
            dom = ["|", ("task_ids", "in", rec.id), ("origin_task_id", "=", rec.id)]
            rec.gte_rfi_count = self.env["gte.rfi"].search_count(dom)
            rec.gte_co_count = self.env["gte.change.order"].search_count(dom)
            rec.gte_submittal_count = self.env["gte.submittal"].search_count(dom)

    def _gte_task_action(self, xmlid, name):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = ["|", ("task_ids", "in", self.id),
                            ("origin_task_id", "=", self.id)]
        action["context"] = {"default_project_id": self.project_id.id}
        action["display_name"] = "%s — %s" % (self.display_name, name)
        return action

    def action_view_gte_rfis(self):
        return self._gte_task_action("gte_controls.action_gte_rfi", "RFIs")

    def action_view_gte_cos(self):
        return self._gte_task_action("gte_controls.action_gte_co", "Change Orders")

    def action_view_gte_submittals(self):
        return self._gte_task_action("gte_controls.action_gte_submittal", "Submittals")
