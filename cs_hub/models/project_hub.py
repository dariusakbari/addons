from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_rfi_ids = fields.One2many("cs.rfi", "project_id", string="RFIs")
    cs_co_ids = fields.One2many("cs.change.order", "project_id",
                                 string="Change Orders")
    cs_submittal_ids = fields.One2many("cs.submittal", "project_id",
                                        string="Submittals")
    cs_dsl_ids = fields.One2many("cs.daily.log", "project_id",
                                  string="Daily Site Logs")
    cs_flha_ids = fields.One2many("cs.flha", "project_id", string="FLHAs")
    cs_incident_ids = fields.One2many("cs.incident", "project_id",
                                       string="Incidents")
    cs_ncr_ids = fields.One2many("cs.ncr", "project_id", string="NCRs")
    cs_si_ids = fields.One2many("cs.site.instruction", "project_id",
                                string="Field Memos / Site Instructions")
    cs_meeting_ids = fields.One2many("cs.meeting", "project_id",
                                     string="Meeting Minutes")
    cs_lookahead_ids = fields.One2many("cs.lookahead", "project_id",
                                       string="Look-Ahead Plans")
    cs_delay_ids = fields.One2many("cs.delay.event", "project_id",
                                   string="Delay Events")
    cs_message_count = fields.Integer(
        string="Communications", compute="_compute_cs_message_count")

    def _cs_comm_sources(self):
        """Map of model -> record ids that make up this project's paper
        trail, used to consolidate their chatter/emails/activities."""
        self.ensure_one()
        return {
            "project.project": [self.id],
            "project.task": self.task_ids.ids,
            "cs.rfi": self.cs_rfi_ids.ids,
            "cs.change.order": self.cs_co_ids.ids,
            "cs.submittal": self.cs_submittal_ids.ids,
            "cs.daily.log": self.cs_dsl_ids.ids,
            "cs.flha": self.cs_flha_ids.ids,
            "cs.incident": self.cs_incident_ids.ids,
            "cs.ncr": self.cs_ncr_ids.ids,
            "cs.site.instruction": self.cs_si_ids.ids,
            "cs.meeting": self.cs_meeting_ids.ids,
            "cs.lookahead": self.cs_lookahead_ids.ids,
            "cs.delay.event": self.cs_delay_ids.ids,
        }

    def _cs_message_domain(self):
        self.ensure_one()
        leaves = []
        for model, ids in self._cs_comm_sources().items():
            if ids:
                leaves.append(["&", ("model", "=", model),
                               ("res_id", "in", list(ids))])
        if not leaves:
            return [("id", "=", 0)]
        domain = ["|"] * (len(leaves) - 1)
        for leaf in leaves:
            domain += leaf
        return domain

    def _compute_cs_message_count(self):
        for project in self:
            project.cs_message_count = self.env["mail.message"].search_count(
                project._cs_message_domain()) if project.id else 0

    def action_view_communications(self):
        """Consolidated feed of chatter, emails and logged activities across
        every construction record on this project (plus the project itself)."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Communications — %s" % (self.name or ""),
            "res_model": "mail.message",
            "views": [
                [self.env.ref("cs_hub.view_cs_project_message_list").id, "list"],
                [False, "form"],
            ],
            "domain": self._cs_message_domain(),
            "context": {"create": False},
        }
