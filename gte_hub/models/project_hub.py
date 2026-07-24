from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    gte_rfi_ids = fields.One2many("gte.rfi", "project_id", string="RFIs")
    gte_co_ids = fields.One2many("gte.change.order", "project_id",
                                 string="Change Orders")
    gte_submittal_ids = fields.One2many("gte.submittal", "project_id",
                                        string="Submittals")
    gte_dsl_ids = fields.One2many("gte.daily.log", "project_id",
                                  string="Daily Site Logs")
    gte_flha_ids = fields.One2many("gte.flha", "project_id", string="FLHAs")
    gte_incident_ids = fields.One2many("gte.incident", "project_id",
                                       string="Incidents")
    gte_ncr_ids = fields.One2many("gte.ncr", "project_id", string="NCRs")
