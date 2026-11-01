from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _cs_linked_change_orders(self):
        """Change orders tied to this customer invoice — either linked
        directly (invoice_ids) or through the invoice's sale-order lines."""
        self.ensure_one()
        CO = self.env["cs.change.order"]
        if self.move_type != "out_invoice":
            return CO
        cos = CO.search([("invoice_ids", "in", self.id)])
        sale_lines = self.invoice_line_ids.sale_line_ids
        if sale_lines:
            cos |= CO.search([("sale_line_id", "in", sale_lines.ids)])
        return cos

    def _cs_sync_change_order_billing(self):
        """Advance linked change orders to match the invoice:
        Approved -> Billed once the invoice is posted, and
        Billed -> Paid once the invoice is (being) paid.
        Keeps the manual 'Mark Billed' action as a fallback; this just makes
        the common 'invoice the sales order' path update the COs automatically.
        """
        today = fields.Date.context_today(self)
        for move in self.filtered(
                lambda m: m.move_type == "out_invoice" and isinstance(m.id, int)
                and m.state == "posted"):
            cos = move._cs_linked_change_orders()
            if not cos:
                continue
            to_bill = cos.filtered(lambda c: c.state == "approved")
            if to_bill:
                to_bill.write({
                    "state": "billed",
                    "billing_status": "billed",
                    "date_billed": today,
                })
                for co in to_bill:
                    if move not in co.invoice_ids:
                        co.invoice_ids = [(4, move.id)]
            if move.payment_state in ("paid", "in_payment"):
                to_pay = cos.filtered(lambda c: c.state == "billed")
                if to_pay:
                    to_pay.write({"state": "paid", "payment_status": "paid"})

    def action_post(self):
        res = super().action_post()
        self._cs_sync_change_order_billing()
        return res

    def _compute_payment_state(self):
        res = super()._compute_payment_state()
        # When an invoice becomes paid/in-payment, advance its change orders.
        paid = self.filtered(
            lambda m: isinstance(m.id, int) and m.move_type == "out_invoice"
            and m.state == "posted"
            and m.payment_state in ("paid", "in_payment"))
        if paid:
            paid._cs_sync_change_order_billing()
        return res
