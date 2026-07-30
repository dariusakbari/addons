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
