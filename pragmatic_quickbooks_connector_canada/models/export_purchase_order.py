from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
# from openerp.exceptions import UserError, ValidationError
import requests
import json
import logging
import datetime

_logger = logging.getLogger(__name__)


class Purchase_Order(models.Model):
    _inherit = "purchase.order"



    @api.model
    def _prepare_purchaseorder_export_line_dict(self, line):
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

            # if line.taxes_id:
            #     if from_button:
            #         self.env['qbo.logger'].sudo().create({
            #             'odoo_name': 'Purchase Order Export',
            #             'odoo_object': 'purchase.order',
            #             'message': f'QBO does not have taxable purchase orders, Taxable purchase orders cannot be exported',
            #             'activity': 'Exporting Purchase Order from Odoo',
            #             'created_date': fields.Datetime.now(),
            #         })
            #
            #         #1.00 Ensure the transaction is committed
            #         self.env.cr.commit()
            #     else:
            #         raise UserError(
            #             "QBO does not have taxable purchase orders, Taxable purchase orders cannot be exported")

            if self.partner_id.supplier_rank:
                vals.update({
                    'DetailType': 'ItemBasedExpenseLineDetail',
                    'ItemBasedExpenseLineDetail': {
                        'ItemRef': {'value': self.env['product.template'].get_qbo_product_ref(line.product_id)},
                        'UnitPrice': line.price_unit,
                        'Qty': line.product_qty,
                        'TaxCodeRef': {'value': taxCodeRefValue},
                        # 'Amount': line.price_subtotal,
                    },
                })
            return vals
        except Exception as e:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': line.name if line else 'Unknown Line',
                    'odoo_object': 'purchase.order',
                    'message': str(e),
                    'activity': 'Error while preparing export line dict',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise UserError(f"An unexpected error occurred while preparing the purchase order line for export: {str(e)}")

    @api.model
    def _prepare_purchaseorder_export_dict(self):
        from_button = self._context.get('from_button', False)
        try:
            vals = {
                'DocNumber': self.name,
                'TxnDate': str(self.date_order)
            }

            if self.partner_id.supplier_rank:
                vals.update({'VendorRef': {
                            'value': self.env['res.partner'].get_qbo_partner_ref(self.partner_id)}})

            lst_line = []

            for line in self.order_line:
                line_vals = self._prepare_purchaseorder_export_line_dict(line)

                lst_line.append(line_vals)
            vals.update({'Line': lst_line})
            if self.partner_id.property_account_payable_id:
                account_payable = self.partner_id.property_account_payable_id
                if account_payable.qbo_id:
                    _logger.info("ACCOUNT IS SYNCED FROM QBO!")
                    vals.update({"APAccountRef": {
                        "name": account_payable.name,
                        "value": account_payable.qbo_id,
                    }})
                else:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'Error',
                            'odoo_object': 'purchase.order',
                            'message': "Please export the Account Payable associated with vendor to QBO,and then export Purchase Order",
                            'activity': 'Exporting Purchase Order from QBO',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(
                            _("Please export the Account Payable associated with vendor to QBO,and then export Purchase Order"))
            return vals
        except Exception as e:
            error_msg = f"Unexpected error during PO export preparation: {str(e)}"
            _logger.exception(error_msg)

            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': self.name or 'Unknown',
                    'odoo_object': 'purchase.order',
                    'message': error_msg,
                    'activity': 'Exporting Purchase Order from QBO',
                    'created_date': fields.Datetime.now(),
                })
                return False
            else:
                raise ValidationError(_(error_msg))

    def is_product_exported_to_qbo(self, product_id, quickbook_config, realmId, headers):
        """Check if a product is exported to QBO"""
        url = f"{quickbook_config.url}{realmId}/item/{product_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True
        return False

    @api.model
    def exportPurchaseOrder(self,cron=None,company=None):
        from_button = self._context.get('from_button', False)
        """export Purchase Order to QBO"""
        if company:
            quickbook_config = company
        else:
            quickbook_config = self.company_id
        if not quickbook_config:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'purchase.order',
                    'message': f'Set Company for Partner: {self.name}',
                    'activity': 'Exporting Purchase Order from QBO',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_(f"Set Company for Partner {self.name}"))
        # quickbook_config = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        if not quickbook_config:
            quickbook_config = self.env.company
        access_token = None
        realmId = None
        headers = {}

        try:
            if quickbook_config.access_token:
                access_token = quickbook_config.access_token
            if quickbook_config.realm_id:
                realmId = quickbook_config.realm_id

            if not realmId or not access_token:
                if from_button:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': 'Token Issue',
                        'odoo_object': 'purchase.order',
                        'message': 'Refresh token again...!',
                        'activity': 'Exporting Purchase Order from QBO',
                        'created_date': fields.Datetime.now(),
                    })
                else:
                    raise ValidationError('Refresh token again...!')

            if access_token:
                headers['Authorization'] = 'Bearer ' + str(access_token)
                headers['Content-Type'] = 'application/json'
                _logger.info("Headers : -------------->{}".format(headers))

            if self._context.get('active_ids'):
                purchase_orders = self.browse(self._context.get('active_ids'))
            else:
                purchase_orders = self

            for purchase_order in purchase_orders:
                if purchase_order.state == 'purchase':
                    vals = purchase_order._prepare_purchaseorder_export_dict()
                    # Check if all products are exported to QBO
                    filtered_lines = []
                    for line in vals.get('Line', []):
                        item_ref = line.get('ItemBasedExpenseLineDetail', {}).get('ItemRef', {}).get('value')
                        if self.is_product_exported_to_qbo(item_ref, quickbook_config, realmId, headers):
                            filtered_lines.append(line)
                        else:
                            _logger.info(f"Product {item_ref} is not exported to QBO. Skipping this product.")
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': 'Product is not exported',
                                'odoo_object': 'purchase.order',
                                'message': f"Product {item_ref} is not exported to QBO. Skipping this product.",
                                'activity': 'Exporting Purchase Order from QBO',
                                'created_date': fields.Datetime.now(),
                            })

                    vals['Line'] = filtered_lines
                    if purchase_order.quickbook_id:
                        """
                            Update Info for Record
                        """
                        SyncToken = self.read_QBO_record_object(quickbook_config, realmId, headers,
                                                                purchase_order.quickbook_id)
                        _logger.info(
                            'SyncToken : ------> {}'.format(SyncToken))
                        vals.update({
                            'Id': str(purchase_order.quickbook_id),
                            "SyncToken": SyncToken,
                            'CurrencyRef': {
                                'value': str(purchase_order.currency_id.name)
                            },
                        })

                    parsed_dict = json.dumps(vals)
                    if purchase_order.partner_id.supplier_rank:
                        _logger.info(
                            "Dict For Create/Update Record=================> {} ".format(parsed_dict))
                        _logger.info('Response : {}'.format(realmId))
                        _logger.info('Response : {}'.format(quickbook_config.url))
                        _logger.info('Response : {}'.format(parsed_dict))


                        result = requests.request('POST', quickbook_config.url + str(realmId) + "/purchaseorder",
                                                  headers=headers, data=parsed_dict)
                        _logger.info('Response : {}'.format(result))
                        if result.status_code == 200:
                            response = quickbook_config.convert_xmltodict(
                                result.text)
                            # update QBO invoice id
                            if purchase_order.partner_id.supplier_rank:
                                purchase_order.quickbook_id = response.get('IntuitResponse').get(
                                    'PurchaseOrder').get('Id')
                                self._cr.commit()
                            _logger.info(
                                _("%s exported successfully to QBO" % (purchase_order.name)))
                        elif result.status_code == 401:
                            tax_err_act = self.env['qbo.logger'].sudo().create({
                                'odoo_name': f'{purchase_order.name}',
                                'odoo_object': 'purchase.order',
                                'message': result.text,
                                'activity': 'Exporting Purchase Order',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            _logger.info(
                                _("STATUS CODE : %s" % (result.status_code)))
                            _logger.info(
                                _("RESPONSE DICT : %s" % (result.text)))
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': f'{result.status_code}',
                                    'odoo_object': 'purchase.order',
                                    'message': result.text,
                                    'activity': 'Exporting Purchase Order',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(_(f"STATUS CODE : {result.status_code}, RESPONSE DICT : {result.text}"))
                else:
                    if len(purchase_orders) == 1:
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': 'Only Confirmed Purchase',
                                'odoo_object': 'purchase.order',
                                'message': "Only Confirmed Purchase Order is exported to QBO.",
                                'activity': 'Exporting Purchase Order',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise ValidationError(
                                _("Only Confirmed Purchase Order is exported to QBO."))

            success_form = self.env.ref(
                'pragmatic_quickbooks_connector_canada.export_successfull_view', False)
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
        except Exception as e:
            _logger.info('{}'.format(e))
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Error Occured',
                    'odoo_object': 'purchase.order',
                    'message': '{}'.format((e)),
                    'activity': 'Exporting Purchase Order',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError('{}'.format((e)))

    def read_QBO_record_object(self, quickbook_config, realmId, headers, quickbooks_id):
        from_button = self._context.get('from_button', False)
        try:
            result = requests.request('GET',
                                      quickbook_config.url +
                                      str(realmId) + "/purchaseorder/" +
                                      str(quickbooks_id),
                                      headers=headers)
            if result.status_code == 200:
                response = quickbook_config.convert_xmltodict(result.text)
                SyncToken = response.get('IntuitResponse').get(
                    'PurchaseOrder').get('SyncToken') or 0
                return SyncToken
            else:
                _logger.info(_("STATUS CODE : %s" % (result.status_code)))
                _logger.info(_("RESPONSE DICT : %s" % (result.text)))
                response = json.loads(result.text)
                if response.get('Fault'):
                    if response.get('Fault').get('Error'):
                        for message in response.get('Fault').get('Error'):
                            if message.get('Detail') and message.get('Message'):
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': result.status_code,
                                        'odoo_object': 'purchase.order',
                                        'message': message.get('Message') + "\n\n" + message.get('Detail'),
                                        'activity': 'Exporting Purchase Order',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise UserError(
                                        message.get('Message') + "\n\n" + message.get('Detail'))
        except Exception as e:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Error Occured',
                    'odoo_object': 'purchase.order',
                    'message': '{}'.format(e),
                    'activity': 'Exporting Purchase Order',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError('{}'.format(e))


