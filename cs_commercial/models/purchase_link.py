from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    cs_po_kind = fields.Selection(
        [("material", "Material PO"), ("subcontract", "Subcontract")],
        string="Purchase Type", default="material", index=True, tracking=True,
        help="Classifies this purchase document as a material purchase order "
             "or a subcontract agreement. Drives the Subcontracts / Material "
             "POs buttons on the project.")

    # --- Subcontract-only construction fields --------------------------------
    cs_holdback_applies = fields.Boolean(string="Holdback Applies")
    cs_holdback_percent = fields.Float(
        string="Holdback %",
        help="Percentage withheld from the subcontractor on each payment. "
             "Applied only when 'Holdback Applies' is on.")
    cs_scope_of_work = fields.Html(
        string="Scope of Work",
        help="Contracted scope for this subcontract agreement.")
    cs_sov_line_ids = fields.One2many(
        "cs.po.sov.line", "order_id", string="Schedule of Values",
        copy=True)
    cs_sov_total = fields.Monetary(
        string="Schedule of Values Total", currency_field="currency_id",
        compute="_compute_cs_sov_total", store=True)

    @api.depends("cs_sov_line_ids.amount")
    def _compute_cs_sov_total(self):
        for rec in self:
            rec.cs_sov_total = sum(rec.cs_sov_line_ids.mapped("amount"))

    @api.onchange("project_id", "cs_po_kind")
    def _onchange_cs_seed_holdback(self):
        """Seed a subcontract's holdback from the project's own holdback
        setting, so subcontracts inherit the job's terms by default."""
        if self.cs_po_kind == "subcontract" and self.project_id:
            self.cs_holdback_applies = self.project_id.cs_holdback_applies
            self.cs_holdback_percent = self.project_id.cs_holdback_percent

    @api.onchange("cs_holdback_applies")
    def _onchange_cs_holdback_applies(self):
        if not self.cs_holdback_applies:
            self.cs_holdback_percent = 0.0
        elif not self.cs_holdback_percent:
            self.cs_holdback_percent = (
                self.project_id.cs_holdback_percent or 10.0)


class CsPoSovLine(models.Model):
    _name = "cs.po.sov.line"
    _description = "Subcontract Schedule of Values Line"
    _order = "sequence, id"

    order_id = fields.Many2one(
        "purchase.order", required=True, ondelete="cascade", index=True)
    currency_id = fields.Many2one(related="order_id.currency_id")
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Description", required=True)
    amount = fields.Monetary(currency_field="currency_id")


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_subcontract_count = fields.Integer(compute="_compute_cs_po_counts")
    cs_material_po_count = fields.Integer(compute="_compute_cs_po_counts")

    def _compute_cs_po_counts(self):
        PO = self.env["purchase.order"]
        for rec in self:
            rec.cs_subcontract_count = PO.search_count(
                [("project_id", "=", rec.id),
                 ("cs_po_kind", "=", "subcontract")])
            rec.cs_material_po_count = PO.search_count(
                [("project_id", "=", rec.id),
                 ("cs_po_kind", "=", "material")])

    def _cs_po_action(self, kind, name):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s — %s" % (self.display_name, name),
            "res_model": "purchase.order",
            "view_mode": "list,form",
            "domain": [("project_id", "=", self.id),
                       ("cs_po_kind", "=", kind)],
            "context": {
                "default_project_id": self.id,
                "default_cs_po_kind": kind,
            },
        }

    def action_view_cs_subcontracts(self):
        return self._cs_po_action("subcontract", "Subcontracts")

    def action_view_cs_material_pos(self):
        return self._cs_po_action("material", "Material POs")
