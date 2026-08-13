from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project(self):
        """Reuse the sales order's linked project instead of spawning a new one,
        and otherwise keep a clean project name.

        Reuse: Odoo core (`sale_project`) never consults the Project chosen on
        the sales-order header when deciding whether to create a project on
        confirmation — it only looks at the order line's own generated project.
        So confirming an SO that is already linked to a project still spawns a
        brand-new one. When the order already has a project, we generate the
        task inside THAT project and return it, so no duplicate is created. A
        fresh project is only built when the SO has no project linked yet.

        Naming: for newly created projects, core appends the *template*
        project's name, leaving live jobs reading like "133 Torresdale Ave -
        S00016 - TEMPLATE — Electrical Job". We let core build and link the
        project, then restore the intended base name — the same formula core
        uses in ``_timesheet_create_project_prepare_values``:
        ``<Customer PO ref> - <SO reference>`` (falling back to the SO reference
        alone when there is no customer PO ref).
        """
        order = self.order_id
        # Reuse the project already linked on the sales order, if any.
        if order.project_id:
            project = order.project_id
            self.write({"project_id": project.id})
            if not project.reinvoiced_sale_order_id:
                project.reinvoiced_sale_order_id = order
            # Seed a blank Original Contract from the SO untaxed total, same as
            # the create path below. Guarded so a manually set value is kept.
            if "cs_contract_amount" in project._fields and not project.cs_contract_amount:
                project.cs_contract_amount = order.amount_untaxed
            return project

        project = super()._timesheet_create_project()
        if project and self.product_id.project_template_id:
            order = self.order_id
            base_name = (
                "%s - %s" % (order.client_order_ref, order.name)
                if order.client_order_ref
                else order.name
            )
            if base_name and project.name != base_name:
                project.name = base_name
            # Seed the Original Contract with the sales order's untaxed total
            # (net of sales tax). Change orders add to it via cs_contract_value.
            if "cs_contract_amount" in project._fields and not project.cs_contract_amount:
                project.cs_contract_amount = order.amount_untaxed
        return project
