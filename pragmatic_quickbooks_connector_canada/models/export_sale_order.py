from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
# from openerp.exceptions import UserError, ValidationError
import requests
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class Sales_Order(models.Model):
    _inherit = "sale.order"

    @api.model
    def _prepare_saleorder_export_line_dict(self, line):
        #         line = self
        from_button = self._context.get('from_button', False)
        try:
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
            vals = {
                'Description': line.name,
                'Amount': line.price_subtotal,
            }
            if line.tax_ids:
                # raise UserError("QBO does not have taxable Sale orders, Taxable sale orders cannot be exported.")
                # taxCodeRefValue = 'TAX'
                taxCodeRefValue = self.env['account.tax'].get_qbo_tax_code(line.tax_ids)
            else:
                taxCodeRefValue = 'NON'

            unit_price = line.price_unit
            #  When discount is available in sale order
            if line.discount > 0:
                unit_price = line.price_unit - \
                             (line.price_unit * (line.discount / 100))
                vals.update({'Amount': unit_price * line.product_uom_qty})

            if self.partner_id.customer_rank:
                vals.update({
                    'DetailType': 'SalesItemLineDetail',
                    'SalesItemLineDetail': {
                        'ItemRef': {'value': self.env['product.template'].get_qbo_product_ref(line.product_id)},
                        'TaxCodeRef': {'value': taxCodeRefValue},
                        'UnitPrice': unit_price,  # line.price_unit
                        'Qty': line.product_uom_qty,
                    }
                })

            return vals
        except Exception as e:
            _logger.exception("Error preparing sale order line export dictionary for line ID %s", line.id)
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'sale.order',
                    'message': f"An error occurred while preparing the sale order line for export: {str(e)}",
                    'activity': 'Export Sale Order from Odoo',
                    'created_date': fields.Datetime.now(),
                })
                return {}
            else:
                raise UserError(_("An error occurred while preparing the sale order line for export: %s") % str(e))

    @api.model
    def _prepare_saleorder_export_dict(self):
        from_button = self._context.get('from_button', False)
        try:
            vals = {
                'DocNumber': self.name,
                'TxnDate': str(self.date_order),
                # 'DueDate': self.date_due,
            }
            if self.partner_id.customer_rank:
                vals.update({'CustomerRef': {
                            'value': self.env['res.partner'].get_qbo_partner_ref(self.partner_id)}})


            total_tax_id = 0
            lst_line = []
            arr = []
            tax_id = 0
            for line in self.order_line:
                line_vals = self._prepare_saleorder_export_line_dict(line)
                lst_line.append(line_vals)
                if line.tax_ids:
                    for rec in line.tax_ids:
                        if rec.qbo_tax_id:
                            tax_id = rec.id
                            arr.append(tax_id)
                        elif not rec.qbo_tax_id:
                            exported = self.env[
                                'account.tax'].export_one_tax_at_a_time(rec)

                            is_exported = self.env['account.tax'].search(
                                [('id', '=', rec.id)])
                            if is_exported:
                                if rec.qbo_tax_id:
                                    tax_id = rec.id
                                    arr.append(tax_id)

            vals.update({'Line': lst_line})

            if tax_id:
                j = 0
                # Set Tax type Like Inclusive or Exclusive or Out of scope Tax
                if self.tax_state:
                    if self.tax_state == 'exclusive':
                        vals.update({"GlobalTaxCalculation": "TaxExcluded"})
                    elif self.tax_state == 'inclusive':
                        vals.update({"GlobalTaxCalculation": "TaxInclusive"})
                    elif self.tax_state == 'notapplicable':
                        vals.update({"GlobalTaxCalculation": "NotApplicable"})

                for i in arr:
                    if len(arr) == 1:
                        tax_added = self.env['account.tax'].search(
                            [('id', '=', tax_id)])

                        vals.update({"TxnTaxDetail": {
                            "TxnTaxCodeRef": {
                                "value": tax_added.qbo_tax_id
                            }}})
                    if j < len(arr) - 1:
                        tax_added = self.env['account.tax'].search(
                            [('id', '=', tax_id)])

                        vals.update({"TxnTaxDetail": {
                            "TxnTaxCodeRef": {
                                "value": tax_added.qbo_tax_id
                            }}})
            if self.amount_tax and vals.get("TxnTaxDetail"):
                vals.get("TxnTaxDetail").update({"TotalTax": self.amount_tax})

            return vals
        except Exception as e:
            _logger.exception("Error while preparing sale order export dict.")
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'sale.order',
                    'message': f"Error while exporting sale order: {str(e)}",
                    'activity': 'Export Sale Order from Odoo',
                    'created_date': fields.Datetime.now(),
                })
                return {}
            else:
                raise UserError(f"Error while exporting sale order: {str(e)}")

    @api.model
    def exportSaleOrder(self, cron=None, company=None):
        """Export account invoice to QBO"""
        from_button = self._context.get('from_button', False)
        if not company:
            quickbook_config = self.company_id
        else:
            quickbook_config = company

        if not quickbook_config:
            quickbook_config = self.env.company

        access_token = quickbook_config.access_token if quickbook_config.access_token else None
        realmId = quickbook_config.realm_id if quickbook_config.realm_id else None

        # Fetch the selected sale orders (this could be multiple sale orders)
        if self._context.get('active_ids'):
            sales = self.browse(self._context.get('active_ids'))
        else:
            sales = self

        failed_sales = []  # Store failed exports for later review

        # Iterate through all sales orders to export them
        for sale in sales:
            try:
                # Skip already exported sales orders
                if sale.quickbook_id:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': sale.name,
                        'odoo_object': 'sale.order',
                        'message': f"Sale order {sale.name} is already exported to QBO.",
                        'activity': 'Exporting Sale Order from Odoo',
                        'created_date': fields.Datetime.now(),
                    })
                    continue  # Skip already exported sales orders

                # Check if the sale order is in a valid state for export (only 'done' or 'sale')
                if sale.state not in ['done', 'sale']:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': sale.name,
                        'odoo_object': 'sale.order',
                        'message': f"Sale order {sale.name} is not in 'done' or 'sale' state.",
                        'activity': 'Exporting Sale Order from Odoo',
                        'created_date': fields.Datetime.now(),
                    })
                    continue  # Skip orders not ready for export

                # Prepare the sale order data for export
                vals = sale._prepare_saleorder_export_dict()
                parsed_dict = json.dumps(vals)
                _logger.info(f"Export SALE ORDER DICT for {sale.name}: {parsed_dict}.")

                if access_token:
                    headers = {
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }

                    # Perform the export request to QuickBooks Online for each sale order
                    result = requests.request('POST', quickbook_config.url + str(realmId) + "/estimate",
                                              headers=headers, data=parsed_dict)

                    # Check the response status from the API
                    if result.status_code == 200:
                        response = quickbook_config.convert_xmltodict(result.text)
                        sale.quickbook_id = response.get('IntuitResponse').get('Estimate').get('Id')
                        self._cr.commit()
                        _logger.info(f"Sale order {sale.name} exported successfully to QBO.")
                    else:
                        # Record failed export attempt for this sale order
                        failed_sales.append({'sale_order': sale.name, 'error': result.text})
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': sale.name,
                                'odoo_object': 'sale.order',
                                'message': f"Error exporting sale order {sale.name}: {result.text}",
                                'activity': 'Exporting Sale Order from Odoo',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise ValidationError(f"Error exporting sale order {sale.name}: {result.text}")
            except Exception as e:
                # Log any exceptions that occur during export
                failed_sales.append({'sale_order': sale.name, 'error': str(e)})
                _logger.error(f"Exception while exporting sale order {sale.name}: {str(e)}")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': sale.name,
                    'odoo_object': 'sale.order',
                    'message': f"Exception while exporting sale order {sale.name}: {str(e)}",
                    'activity': 'Exporting Sale Order from Odoo',
                    'created_date': fields.Datetime.now(),
                })

        # After processing all sale orders, check if there were any failed exports
        if failed_sales:
            failed_sales_msg = "\n".join([f"Order {fs['sale_order']}: {fs['error']}" for fs in failed_sales])
            _logger.error(f"Failed to export the following orders:\n{failed_sales_msg}")
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Failed Exports',
                    'odoo_object': 'sale.order',
                    'message': f"The following orders failed to export to QBO:\n{failed_sales_msg}",
                    'activity': 'Exporting Sale Order from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise UserError(f"The following orders failed to export to QBO:\n{failed_sales_msg}")

        # If everything succeeded, show a success message
        success_form = self.env.ref('pragmatic_quickbooks_connector_canada.export_successfull_view', False)
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.company.message',
            'views': [(success_form.id, 'form')],
            'view_id': success_form.id,
            'target': 'new',
        }

