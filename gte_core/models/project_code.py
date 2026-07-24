import re

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    gte_code = fields.Char(
        string="Project Code", compute="_compute_gte_code", store=True,
        readonly=False, index=True,
        help="Short code used in record numbering, e.g. 0476 → 0476-RFI-001.")

    @api.depends("name")
    def _compute_gte_code(self):
        for rec in self:
            if rec.gte_code:
                continue
            name = rec.name or ""
            m = re.search(r"\d[\w-]*", name)
            code = m.group(0) if m else re.sub(r"[^A-Za-z0-9]", "", name)[:6].upper()
            rec.gte_code = code or "PRJ"
