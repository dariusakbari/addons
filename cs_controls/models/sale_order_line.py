from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project(self):
        """Create the project from the estimate as usual, but keep a clean
        project name.

        Odoo core (`sale_project`) appends the *template* project's name to the
        generated project, which leaves live jobs reading like
        "133 Torresdale Ave - S00016 - TEMPLATE — Electrical Job".

        We let core build and link the project (template copy, tasks, analytic
        account, etc.), then restore the intended base name — the same formula
        core uses in ``_timesheet_create_project_prepare_values``:
        ``<Customer PO ref> - <SO reference>`` (falling back to the SO
        reference alone when there is no customer PO ref).
        """
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
        return project
