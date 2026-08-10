from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_rfi_count = fields.Integer(compute="_compute_cs_counts")
    cs_co_count = fields.Integer(compute="_compute_cs_counts")
    cs_submittal_count = fields.Integer(compute="_compute_cs_counts")
    cs_co_exposure = fields.Monetary(compute="_compute_cs_counts",
                                      currency_field="currency_id")

    def _compute_cs_counts(self):
        for rec in self:
            rec.cs_rfi_count = self.env["cs.rfi"].search_count(
                [("project_id", "=", rec.id)])
            rec.cs_co_count = self.env["cs.change.order"].search_count(
                [("project_id", "=", rec.id)])
            rec.cs_submittal_count = self.env["cs.submittal"].search_count(
                [("project_id", "=", rec.id)])
            cos = self.env["cs.change.order"].search(
                [("project_id", "=", rec.id),
                 ("state", "not in", ("closed", "cancelled", "rejected"))])
            rec.cs_co_exposure = sum(cos.mapped("exposure"))

    def _cs_action(self, xmlid, name):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("project_id", "=", self.id)]
        action["context"] = {"default_project_id": self.id}
        action["display_name"] = "%s — %s" % (self.display_name, name)
        return action

    def action_view_cs_rfis(self):
        return self._cs_action("cs_controls.action_cs_rfi", "RFIs")

    def action_view_cs_cos(self):
        return self._cs_action("cs_controls.action_cs_co", "Change Orders")

    def action_view_cs_submittals(self):
        return self._cs_action("cs_controls.action_cs_submittal", "Submittals")


class ProjectTask(models.Model):
    _inherit = "project.task"

    cs_rfi_count = fields.Integer(compute="_compute_cs_counts")
    cs_co_count = fields.Integer(compute="_compute_cs_counts")
    cs_submittal_count = fields.Integer(compute="_compute_cs_counts")

    def _cs_task_domain(self, model):
        """Records of `model` linked to this task. Only RFIs and submittals
        carry a many2many `task_ids`; change orders link through the single
        `origin_task_id`. Building the domain from the fields that actually
        exist avoids "Invalid field" errors when a model lacks `task_ids`."""
        self.ensure_one()
        if "task_ids" in self.env[model]._fields:
            return ["|", ("task_ids", "in", self.id),
                    ("origin_task_id", "=", self.id)]
        return [("origin_task_id", "=", self.id)]

    def _compute_cs_counts(self):
        for rec in self:
            rec.cs_rfi_count = rec.env["cs.rfi"].search_count(
                rec._cs_task_domain("cs.rfi"))
            rec.cs_co_count = rec.env["cs.change.order"].search_count(
                rec._cs_task_domain("cs.change.order"))
            rec.cs_submittal_count = rec.env["cs.submittal"].search_count(
                rec._cs_task_domain("cs.submittal"))

    def _cs_task_action(self, xmlid, name, model):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = self._cs_task_domain(model)
        action["context"] = {"default_project_id": self.project_id.id}
        action["display_name"] = "%s — %s" % (self.display_name, name)
        return action

    def action_view_cs_rfis(self):
        return self._cs_task_action(
            "cs_controls.action_cs_rfi", "RFIs", "cs.rfi")

    def action_view_cs_cos(self):
        return self._cs_task_action(
            "cs_controls.action_cs_co", "Change Orders", "cs.change.order")

    def action_view_cs_submittals(self):
        return self._cs_task_action(
            "cs_controls.action_cs_submittal", "Submittals", "cs.submittal")
