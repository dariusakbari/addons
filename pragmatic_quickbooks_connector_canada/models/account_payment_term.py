import json
import logging

import requests
from odoo.exceptions import ValidationError
from odoo import api, fields, models,_

_logger = logging.getLogger(__name__)


class PaymentTermCustomization(models.Model):
    _inherit = 'account.payment.term'

    x_quickbooks_id = fields.Integer('Quickbooks ID', copy=False)
    x_quickbooks_exported = fields.Boolean(
        "Exported to Quickbooks ? ", default=False, copy=False)
    x_quickbooks_updated = fields.Boolean(
        "Updated in Quickbook ?", default=False)
    line_ids = fields.One2many(
        'account.payment.term.line', 'payment_id', string='Terms', copy=True)

    @api.model
    def export_payment_term_to_quickbooks(self):
        from_button = self._context.get('from_button', False)
        # Check if at least one record is selected
        if len(self) == 0:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Error Occured',
                    'odoo_object': 'account.payment.term',
                    'message': "Please select at least one record to export.",
                    'activity': 'Exporting Payment Term from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError("Please select at least one record to export.")

        # QuickBooks config
        quickbook_config = self.env['res.users'].search([('id', '=', self._uid)]).company_id
        access_token = quickbook_config.access_token
        realmId = quickbook_config.realm_id

        if not access_token or not realmId:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Error Occured',
                    'odoo_object': 'account.payment.term',
                    'message': "QuickBooks authentication details are missing.",
                    'activity': 'Exporting Payment Term from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError("QuickBooks authentication details are missing.")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        success_count = 0
        error_count = 0

        # Iterate over all selected records
        for record in self:
            try:
                payment_term_line = self.env['account.payment.term.line'].search([('payment_id', '=', record.id)])

                # Ensure only one payment term line exists for each record
                if len(payment_term_line) > 1:
                    error_count += 1
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': f'{record.name}',
                            'odoo_object': 'account.payment.term.line',
                            'message': f"Term Name [{record.name}] has multiple payment term lines. Only one is allowed.",
                            'activity': 'Exporting Payment Term from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                        continue
                    else:
                        raise ValidationError(f"Term Name [{record.name}] has multiple payment term lines. Only one is allowed.")

                # Prepare data for export
                term_data = {
                    'Name': record.name,
                    'Active': "true" if record.active else "false",
                    'DueDays': payment_term_line.nb_days if payment_term_line else None,
                }

                if record.discount_days and record.discount_percentage:
                    term_data['DiscountPercent'] = record.discount_percentage
                    term_data['DiscountDays'] = record.discount_days

                # Check if the term is already in QuickBooks
                sql_query = f"select Id, SyncToken from term Where Id = '{record.x_quickbooks_id}'"
                result = requests.request('GET', f"{quickbook_config.url}{realmId}/query?query={sql_query}",
                                        headers=headers)

                if result.status_code == 200:
                    parsed_result = result.json()
                    if parsed_result.get('QueryResponse') and parsed_result['QueryResponse'].get('Term'):
                        # Record already exists, update it
                        term_data['Id'] = record.x_quickbooks_id
                        term_data['SyncToken'] = parsed_result['QueryResponse']['Term'][0]['SyncToken']
                        term_data['sparse'] = 'true'
                        response = requests.request('POST', f"{quickbook_config.url}{realmId}/term?operation=update",
                                                    headers=headers, data=json.dumps(term_data))
                        if response.status_code == 200:
                            success_count += 1
                            record.x_quickbooks_updated = True
                        else:
                            error_count += 1
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': f'{record.name}',
                                    'odoo_object': 'account.payment.term',
                                    'message': f"Failed to update term [{record.name}] in QuickBooks. Status Code: {response.status_code}",
                                    'activity': 'Exporting Payment Term from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    f"Failed to update term [{record.name}] in QuickBooks. Status Code: {response.status_code}")
                    else:
                        # Record does not exist, create it
                        response = requests.request('POST', f"{quickbook_config.url}{realmId}/term", headers=headers,
                                                    data=json.dumps(term_data))
                        if response.status_code == 200:
                            parsed_result = response.json()
                            if parsed_result.get('Term').get('Id'):
                                record.x_quickbooks_exported = True
                                record.x_quickbooks_id = parsed_result['Term']['Id']
                                success_count += 1
                            else:
                                error_count += 1
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': f'{record.name}',
                                        'odoo_object': 'account.payment.term',
                                        'message': f"Failed to create term [{record.name}] in QuickBooks. Status Code: {response.status_code}",
                                        'activity': 'Exporting Payment Term from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise ValidationError(
                                        f"Failed to create term [{record.name}] in QuickBooks. Status Code: {response.status_code}")
                        else:
                            error_count += 1
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': f'{record.name}',
                                    'odoo_object': 'account.payment.term',
                                    'message': f"Failed to create term [{record.name}] in QuickBooks. Status Code: {response.status_code}",
                                    'activity': 'Exporting Payment Term from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    f"Failed to create term [{record.name}] in QuickBooks. Status Code: {response.status_code}")

                else:
                    error_count += 1
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': f'{record.name}',
                            'odoo_object': 'account.payment.term',
                            'message': f"Failed to check existence of term [{record.name}] in QuickBooks. Status Code: {result.status_code}",
                            'activity': 'Exporting Payment Term from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(
                            f"Failed to check existence of term [{record.name}] in QuickBooks. Status Code: {result.status_code}")
            except Exception as e:
                error_count += 1
                _logger.exception(f"Error during payment term export: {str(e)}")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': record.name,
                    'odoo_object': 'account.payment.term',
                    'message': str(e),
                    'activity': 'Exporting Payment Term from Odoo',
                    'created_date': fields.Datetime.now(),
                })

        # Report success and failure counts
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.company.message',
            'views': [(self.env.ref('pragmatic_quickbooks_connector_canada.export_successfull_view').id, 'form')],
            'view_id': self.env.ref('pragmatic_quickbooks_connector_canada.export_successfull_view').id,
            'target': 'new',
            'context': {
                'success_count': success_count,
                'error_count': error_count,
            }
        }

    # def export_payment_term_to_quickbooks(self):
    #     # try:
    #     if len(self) > 1:
    #         raise ValidationError('Please Select 1 Record to export')
    #     ''' Check self.name if there in quickbooks name field or not '''
    #     # quickbook_config = self.env['quickbook.config'].search([], limit=1)
    #     quickbook_config = self.env['res.users'].search(
    #         [('id', '=', self._uid)]).company_id
    #
    #     ''' GET ACCESS TOKEN '''
    #     access_token = None
    #     realmId = None
    #     if quickbook_config.access_token:
    #         access_token = quickbook_config.access_token
    #     if quickbook_config.realm_id:
    #         realmId = quickbook_config.realm_id
    #
    #     if access_token:
    #         headers = {}
    #         headers['Authorization'] = 'Bearer ' + str(access_token)
    #         headers['Content-Type'] = 'application/json'
    #         headers['Accept'] = 'application/json'
    #
    #         sql_query = "select Id,SyncToken from term Where Id = '{}'".format(
    #             self.x_quickbooks_id)
    #
    #         result = requests.request(
    #             'GET', quickbook_config.url + str(realmId) + "/query?query=" + sql_query, headers=headers)
    #         if result.status_code == 200:
    #             parsed_result = result.json()
    #             if parsed_result.get('QueryResponse'):
    #                 if parsed_result.get('QueryResponse').get('Term') and \
    #                         parsed_result.get('QueryResponse').get('Term')[0]:
    #
    #                     dict = {}
    #                     ''' Record is not present in Quickbooks, Hence we can insert it '''
    #                     dict['Name'] = str(self.name)
    #
    #                     if self.active:
    #                         dict['Active'] = "true"
    #                     else:
    #                         dict['Active'] = "false"
    #
    #                     payment_term_line = self.env['account.payment.term.line'].search(
    #                         [('payment_id', '=', self.id)])
    #                     if len(payment_term_line) >= 2:
    #                         raise ValidationError(
    #                             f"Term Name1 [{self.name}]we cannot export 2 lines for payment term on qbo")
    #
    #                     if payment_term_line and payment_term_line.nb_days:
    #                         dict['DueDays'] = payment_term_line.nb_days
    #
    #                     if self.x_quickbooks_id:
    #                         dict['Id'] = self.x_quickbooks_id
    #                         dict['sparse'] = 'true'
    #                         if self.discount_days and self.discount_percentage:
    #                             dict['DiscountPercent'] = self.discount_percentage
    #                             dict['DiscountDays'] = self.discount_days
    #                         dict['SyncToken'] = parsed_result.get(
    #                             'QueryResponse').get('Term')[0].get('SyncToken')
    #                         dict = json.dumps(dict)
    #                         result = requests.request('POST',
    #                                                   quickbook_config.url + str(realmId) + "/term?operation=update",
    #                                                   headers=headers,
    #                                                   data=dict)
    #                         if result.status_code == 200:
    #                             self.x_quickbooks_updated = True
    #                         elif result.status_code == 400:
    #                             error_message = result.text
    #                             try:
    #                                 error_data = json.loads(error_message)
    #                                 error_detail = error_data.get('Fault', {}).get('Error', [{}])[0].get('Detail', '')
    #                                 error_id = error_detail.split('=')[1].split(',')[0]
    #                             except Exception as e:
    #                                 _logger.info(f"An unexpected error occurred: - {e}")
    #                             if error_id:
    #                                 # _logger.info(_(f"Duplicate Name For Method Name - {method.name}"))
    #                                 data = requests.request('GET', quickbook_config.url + str(
    #                                     quickbook_config.realm_id) + "/query?query=select * from term where Id = '{}'".format(
    #                                     str(error_id)), headers=headers)
    #                                 if data.status_code == 200:
    #                                     response = data.text
    #                                     try:
    #                                         data = json.loads(response)
    #                                         term_name = data['QueryResponse']['Term'][0]['Name']
    #
    #                                     except json.JSONDecodeError as e:
    #                                         _logger.info(f"Error decoding JSON:{e}")
    #                                     raise ValidationError(
    #                                         f"Duplicate Name22 - [{term_name}] is already exist in quickbook "
    #                                     )
    #             else:
    #                 dict = {}
    #                 ''' Record is not present in Quickbooks, Hence we can insert it '''
    #                 dict['Name'] = str(self.name)
    #                 if self.active:
    #                     dict['Active'] = "true"
    #                 else:
    #                     dict['Active'] = "false"
    #
    #                 payment_term_line = self.env['account.payment.term.line'].search(
    #                     [('payment_id', '=', self.id)])
    #                 if len(payment_term_line) >= 2:
    #                     raise ValidationError(
    #                         f"Term Name2 [{self.name}] we cannot export 2 lines for payment term on qbo")
    #                 if payment_term_line:
    #                     dict['DueDays'] = payment_term_line.nb_days
    #                 if self.discount_days and self.discount_percentage:
    #                     dict['DiscountPercent'] = self.discount_percentage
    #                     dict['DiscountDays'] = self.discount_days
    #
    #                 dict = json.dumps(dict)
    #                 result = requests.request(
    #                     'POST', quickbook_config.url + str(realmId) + "/term", headers=headers, data=dict)
    #                 if result.status_code == 200:
    #                     parsed_result = result.json()
    #                     if parsed_result.get('Term').get('Id'):
    #                         self.x_quickbooks_exported = True
    #                         self.x_quickbooks_id = parsed_result.get(
    #                             'Term').get('Id')
    #                         success_form = self.env.ref(
    #                             'pragmatic_quickbooks_connector_canada.export_successfull_view', False)
    #                         return {
    #                             'name': _('Notification'),
    #                             'type': 'ir.actions.act_window',
    #                             'view_type': 'form',
    #                             'view_mode': 'form',
    #                             'res_model': 'res.company.message',
    #                             'views': [(success_form.id, 'form')],
    #                             'view_id': success_form.id,
    #                             'target': 'new',
    #                         }
    #
    #                 elif result.status_code == 400:
    #                     error_message = result.text
    #                     try:
    #                         error_data = json.loads(error_message)
    #                         error_detail = error_data.get('Fault', {}).get('Error', [{}])[0].get('Detail', '')
    #                         error_id = error_detail.split('=')[1].split(',')[0]
    #                     except Exception as e:
    #                         _logger.info(f"An unexpected error occurred::{e}")
    #                     if error_id:
    #
    #                         data = requests.request('GET', quickbook_config.url + str(
    #                             quickbook_config.realm_id) + "/query?query=select * from term where Id = '{}'".format(
    #                             str(error_id)), headers=headers)
    #                         if data.status_code == 200:
    #                             response = data.text
    #                             try:
    #                                 data = json.loads(response)
    #                                 term_name = data['QueryResponse']['Term'][0]['Name']
    #                             except json.JSONDecodeError as e:
    #                                 _logger.info(f"Error decoding JSON:{e}")
    #                                 payment_term = self.env['qbo.logger'].sudo().create({
    #                                     'odoo_name': 'payment Trem Export',
    #                                     'odoo_object': 'account.payment.term',
    #                                     'message': f'Duplicate Name - [{term_name}] is already exist in quickbook',
    #                                     'activity': 'Exporting account payment term from Odoo',
    #                                     'created_date': fields.Datetime.now(),
    #                                     # 'company_id': company.id,
    #                                 })
    #
    #                                 # Ensure the transaction is committed
    #                                 self.env.cr.commit()
    #                                 raise ValidationError(
    #                                     f"Duplicate Name - [{term_name}] is already exist in quickbook ")
    #
    #
    #
    #                 else:
    #                     raise ValidationError(f"{result.status_code}[{result.text}]")
    #         else:
    #             pass
