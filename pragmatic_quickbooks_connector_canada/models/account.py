# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

import requests

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = "account.account"

    qbo_id = fields.Char(
        "QBO Id", copy=False, help="QuickBooks database recordset id")
    qbo_acc_type = fields.Many2one(
        'qbo.account.type', string="QBO Type", help="QuickBooks account type")
    qbo_acc_subtype = fields.Many2one(
        'qbo.account.subtype', string="QBO Subtype", help="QuickBooks account subtype")

    @api.onchange('qbo_acc_type')
    def onchange_qbo_acc_type(self):
        self.qbo_acc_subtype = False
        return {'domain': {'qbo_acc_subtype': [('qbo_type_id', '=', self.qbo_acc_type.id)]}}

    @api.model
    def get_account_ref(self, qbo_account_id, company=None):
        try:
            if not company:
                company = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_id
                if not company:
                    raise ValidationError(f"Company not found for the current user while processing QBO Account ID: {qbo_account_id}")
        except Exception as e:
            raise ValidationError(f"Error fetching company for QBO Account ID {qbo_account_id}: {str(e)}")
        
        try:
            account = self.search([('qbo_id', '=', qbo_account_id), ('company_ids', '=', company.id)], limit=1)
        except Exception as e:
            raise ValidationError(f"Error searching account for QBO Account ID {qbo_account_id}: {str(e)}")

        # If account is not created in odoo then import from QBO and create.
        if not account:
            try:
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/account/' + qbo_account_id
                data = requests.request('GET', url, headers=url_str.get('headers'))
                if data.status_code == 200:
                    try:
                        account = self.create_account_account(data, company)
                    except Exception as e:
                        raise ValidationError(f"Error creating account from QBO for QBO Account ID {qbo_account_id}: {str(e)}")
                else:
                    raise ValidationError(f"Failed to fetch account from QBO for QBO Account ID {qbo_account_id}, status code: {data.status_code}")
            except Exception as e:
                raise ValidationError(f"Error during QBO API request for QBO Account ID {qbo_account_id}: {str(e)}")
        return account.id

    def get_account_type(self, type):
        brw_acc_type = False
        if type == 'Bank':
            brw_acc_type = 'asset_cash'
        elif type == 'Other Current Asset':
            brw_acc_type = 'asset_current'
        elif type == 'Fixed Asset':
            brw_acc_type = 'asset_fixed'
        elif type == 'Other Asset':
            brw_acc_type = 'asset_current'
        elif type == 'Accounts Receivable':
            brw_acc_type = 'asset_receivable'
        elif type == 'Equity':
            brw_acc_type = 'equity'
        elif type == 'Expense':
            brw_acc_type = 'expense'
        elif type == 'Other Expense':
            brw_acc_type = 'expense'
        elif type == 'Cost of Goods Sold':
            brw_acc_type = 'expense_direct_cost'
        elif type == 'Accounts Payable':
            brw_acc_type = 'liability_payable'
        elif type == 'Credit Card':
            brw_acc_type = 'liability_credit_card'
        elif type == 'Long Term Liability':
            brw_acc_type = 'liability_non_current'
        elif type == 'Other Current Liability':
            brw_acc_type = 'liability_current'
        elif type == 'Income':
            brw_acc_type = 'income'
        elif type == 'Other Income':
            brw_acc_type = 'income_other'
        return brw_acc_type

    @api.model
    def create_account_account(self, data, company=None):
        """Create account object in odoo
        :param data: account object response return by QBO
        :return int: last import QBO account Id
        """
        try:
            res = json.loads(str(data.text))
        except Exception as e:
            raise ValidationError(_("Invalid JSON response from QBO. Error: %s") % str(e))

        qbo_acc_type = self.env['qbo.account.type']
        qbo_acc_subtype = self.env['qbo.account.subtype']
        acc = False
        
        try:
            if 'QueryResponse' in res:
                Account = res.get('QueryResponse').get('Account', [])
            else:
                Account = [res.get('Account')] or []
        except Exception as e:
            raise ValidationError(_("Error extracting accounts from response: %s" % str(e)))
        if not Account:
            raise UserError(_("It seems that all of the Chart of Accounts are already imported."))
        max_reult = res.get('QueryResponse').get('maxResults') if res.get('QueryResponse') else company.last_acc_imported_id

    
        if len(Account) >= 1:
            for account in Account:
                try:
                    if not 'AcctNum' in account:
                        raise ValidationError(_("""
                            Account Number not set for {}
                            
                            Enable accounts numbers/assign your account numbers to your Chart of Accounts in QBO.
                            Follow below steps:
                            
                            First, turn on the Setting for using account numbers.
            
                                1. Choose  the Gear icon > Company Settings
                                2. Choose Advanced from the menu on the left.
                                3. In the Chart of Accounts section, click on the Edit icon.
                                4. Place a check mark in the box Enable accounts numbers, and Use account numbers.
                                    Click Save and Done.
                            
                            Next, assign your account numbers.
                            
                                1. Choose the Gear icon > Chart of Accounts.
                                2. Click on the Edit icon on the uppser right hand side.
                                3. Enter your Account Numbers in blank box (Account numbers can be up to 7-digits long).
                                4. Click the Save button (Upper right) when you're done with entering your account numbers.
                            """.format(account.get('Name'), account.get('Id'))))
                except Exception as e:
                    raise ValidationError(_("Error validating account AcctNum (QBO ID: %s): %s" % (account.get('Id'), str(e))))
                
        elif len(Account) == 0:
            raise UserError(
                "It seems that all of the Chart of Accounts are already imported.")

        for account in Account:
            try:
                _logger.info(f"Process Account is {account}.")
                if account.get('AccountType'):
                    brw_acc_type = self.get_account_type(account.get('AccountType'))
                    _logger.info(f"Account brw_acc_type {brw_acc_type}.")
                else:
                    _logger.info("Account Type not found.")

                brw_qbo_acc_type = qbo_acc_type.search([('name', '=', account.get('AccountType'))], limit=1)
                _logger.info(f"Account brw_qbo_acc_type {brw_qbo_acc_type}.")
                brw_qbo_acc_subtype = qbo_acc_subtype.search([('internal_name', '=', account.get('AccountSubType'))],
                                                            limit=1)
                _logger.info(f"Account brw_qbo_acc_subtype {brw_qbo_acc_subtype}.")
                if not company:
                    company = self.env.user.company_id
                vals = {
                    'qbo_id': int(account.get('Id')),
                    'name': account.get('Name', ''),
                    'code': account.get('AcctNum', ''),
                    'qbo_acc_type': brw_qbo_acc_type.id if brw_qbo_acc_type else False,
                    'qbo_acc_subtype': brw_qbo_acc_subtype.id if brw_qbo_acc_subtype else False,
                }
                _logger.info(f"Account Processs valsvalsvalsvalsvalsvals {vals}.")

                acc = self.env['account.account'].search(
                    ['|', ('code', '=', account.get('AcctNum', '')),
                    ('qbo_id', '=', int(account.get('Id'))), ('company_ids', '=', company.id)],
                    limit=1)
                _logger.info(f"FOUND ACCOUNT iSSSSSSSSSS {acc}.")
                if not acc:
                    vals.update({'account_type': brw_acc_type if brw_acc_type else False})
                    _logger.info(f"CREATE VALS BEFOREEE RECONCILEEEEEEE {vals}.")
                    if brw_acc_type == 'Receivable' or brw_acc_type == 'Payable':
                        vals.update({'reconcile': True})
                    _logger.info(f"CREATE VALSSSSSSSSS IS {vals}.")
                    acc = self.env['account.account'].create(vals)
                    _logger.info(
                        _("Account created sucessfully! Account Id: %s %s" % (acc.id, acc.qbo_id)))

                    if company.import_account_by_date:
                        try:
                            date_format = '%Y-%m-%d'
                            if company.account_import_by == 'crt_dt':
                                date_string = account.get('MetaData').get(
                                    'CreateTime')[:10]
                            else:
                                date_string = account.get('MetaData').get(
                                    'LastUpdatedTime')[:10]

                            date_object = datetime.strptime(date_string,
                                                            date_format).date()
                            company.import_account_date = date_object
                        except Exception as e:
                            raise ValidationError(_("Error parsing date for QBO ID: %s - %s" % (account.get('Id'), str(e))))
                    self._cr.commit()
                else:
                    if not company:
                        company = self.env['res.users'].search(
                            [('id', '=', self._uid)]).company_id
                    update_account_import = company.update_account_import
                    if update_account_import:
                        _logger.info(f"UPDATEE VALSSSSSSSSS IS {vals}.")
                        acc.write(vals)
                        _logger.info(
                            _("Account updated sucessfully! Account Id: %s %s" % (acc.id, acc.qbo_id)))
                        if not company:
                            company = self.env.user.company_id
                        if company.import_account_by_date:
                            try:
                                date_format = '%Y-%m-%d'
                                if company.account_import_by == 'crt_dt':
                                    date_string = account.get('MetaData').get(
                                        'CreateTime')[:10]
                                else:
                                    date_string = account.get('MetaData').get(
                                        'LastUpdatedTime')[:10]

                                date_object = datetime.strptime(date_string,
                                                                date_format).date()
                                company.import_account_date = date_object
                            except Exception as e:
                                raise ValidationError(_("Error updating date for QBO ID: %s - %s" % (account.get('Id'), str(e))))
                    self._cr.commit()
            except ValidationError:
                raise  # Re-raise known validation errors untouched
            except Exception as e:
                raise ValidationError(_("Unexpected error while processing QBO ID: %s - %s" % (account.get('Id'), str(e))))
        _logger.info(f"RETURN ACCOUNT IS ----------------->{acc} : {acc.qbo_id}")
        return max_reult

    @api.model
    def qbo_pop_type(self):
        if self._context.get('active_ids'):
            accounts = self.env['account.account'].browse(
                self._context.get('active_ids'))
            
            from_button = self._context.get('from_button', False)

            if from_button:
                for account in accounts:
                    if not account.qbo_acc_type:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': f'{account.name}',
                            'odoo_object': 'account.account',
                            'message': f'"QBO type is required for account11":  {account.name}',
                            'activity': 'Exporting account from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
            else:
                for account in accounts:
                    if not account.qbo_acc_type:
                        raise UserError(
                            _("QBO type is required for account: %s" % account.name))


    @api.model
    def export_to_qbo(self):
        """export account to QBO"""
        self.qbo_pop_type()
        if self._context.get('active_ids'):
            accounts = self.env['account.account'].browse(
                self._context.get('active_ids'))

        else:
            accounts = self

        self.export_to_qbo_main(accounts)
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

    @api.model
    def export_single_account(self):
        """export account to QBO"""
        accounts = self
        self.export_to_qbo_main(accounts)


    def export_to_qbo_main(self, accounts):
        from_button = self._context.get('from_button', False)

        
        for account in accounts:
            try:
                vals = {
                    'Name': account.name,
                    'AcctNum': account.code,
                }

                if account.qbo_acc_type:
                    if account.qbo_acc_type.name == 'Other Expense':
                        acc_type = 'Other Expense'
                    elif account.qbo_acc_type.name == 'Cost of Goods Sold':
                        acc_type = 'Cost of Goods Sold'
                    elif account.qbo_acc_type.name == 'Credit Card':
                        acc_type = 'Credit Card'
                    elif account.qbo_acc_type.name == 'Long Term Liability':
                        acc_type = 'Long Term Liability'
                    elif account.qbo_acc_type.name == 'Other Current Liability':
                        acc_type = 'Other Current Liability'
                    elif account.qbo_acc_type.name == 'Other Income':
                        acc_type = 'Other Income'
                    else:
                        acc_type = account.qbo_acc_type.name

                    vals.update({'AccountType': acc_type})

                elif not account.qbo_acc_subtype:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': f'{account.name}',
                            'odoo_object': 'account.account',
                            'message': f'"QBO type is required for account":  {account.name}',
                            'activity': 'Exporting account from Odoo',
                            'created_date': fields.Datetime.now(),
                        })

                        # Ensure the transaction is committed
                        self.env.cr.commit()
                        continue
                    else:
                        raise ValidationError(f"Missing QBO Subtype for Account: {account.name}")

                if account.qbo_acc_subtype:
                    vals.update(
                        {'AccountSubType': account.qbo_acc_subtype.internal_name})

                elif not account.qbo_acc_type:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'account account',
                            'odoo_object': 'account.account',
                            'message': f'"QBO type is required for account : {account.name}"',
                            'activity': 'Exporting account from Odoo',
                            'created_date': fields.Datetime.now(),
                        })

                        # Ensure the transaction is committed
                        self.env.cr.commit()
                        continue
                    else:
                        raise ValidationError(
                            _("QBO Type is required for account: %s " % account.name))

                if account.qbo_id:
                    _logger.info("CHART OF ACCCOUNT EXISTS IN QBO,NEED TO UPDATE!")
                    company = self.env['res.users'].search(
                        [('id', '=', self._uid)]).company_id
                    update_account_export = company.update_account_export
                    if update_account_export:
                        vals.update({'Id': account.qbo_id})
                        account.update_account_to_qbo(vals)

                else:
                    _logger.info("EXPORTING ACCOUNT TO QBO")
                    account.send_account_to_qbo(vals)
            except UserError as e:
                if not from_button:
                    raise
                _logger.warning(str(e))
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': account.name,
                    'odoo_object': 'account.account',
                    'message': str(e),
                    'activity': 'Exporting account (Validation)',
                    'created_date': fields.Datetime.now(),
                })

            except Exception as e:
                _logger.exception(f"Unexpected error for account {account.name}")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': account.name,
                    'odoo_object': 'account.account',
                    'message': str(e),
                    'activity': 'Exporting account (Exception)',
                    'created_date': fields.Datetime.now(),
                })



    def update_account_to_qbo(self, vals):
        _logger.info("UPDATING ACCOUNT IN QBO")
        from_button = self._context.get('from_button', False)
        parsed_dict = json.dumps(vals)

        quickbook_config = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id
        access_token = None
        realmId = None
        if quickbook_config.access_token:
            access_token = quickbook_config.access_token
        if quickbook_config.realm_id:
            realmId = quickbook_config.realm_id
        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            synctoken = '0'
            # FIRST NEED TO READ THE ACCOUNT FROM QUICKBOOKS
            _logger.info("ACCOUNT TO UPDATE IS ---> {}".format(vals.get('Id')))
            res = requests.request('GET', quickbook_config.url + str(realmId) + "/account/{}?minorversion=75".format(
                vals.get('Id')), headers=headers, data=parsed_dict)
            if res.status_code == 200:
                response = quickbook_config.convert_xmltodict(res.text)
                _logger.info("RESPONSE IS ---> {}".format(response))
                synctoken = response.get('IntuitResponse').get(
                    'Account').get('SyncToken')
            if res.status_code == 400:
                _logger.info(_("STATUS CODE : %s" % (res.status_code)))
                _logger.info(_("RESPONSE DICT : %s" % (res.text)))
                response = json.loads(res.text)
                if response.get('Fault'):
                    if response.get('Fault').get('Error'):
                        for message in response.get('Fault').get('Error'):
                            if message.get('Detail') and message.get('Message'):
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': 'Error Occured',
                                        'odoo_object': 'account.account',
                                        'message': message.get('Message') + "\n\n" + message.get('Detail'),
                                        'activity': 'Exporting account from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise UserError(message.get('Message') + "\n\n" + message.get('Detail'))

                return False
            # ATTEMPTING TO UPDATE THE ACCOUNT
            vals.update({'SyncToken': synctoken})
            _logger.info("VALS FOR UPDATE IS ---> {}".format(vals))
            updated_data = json.dumps(vals)
            result = requests.request('POST', quickbook_config.url + str(realmId) + "/account?minorversion=75",
                                      headers=headers, data=updated_data)
            if result.status_code == 200:
                response = quickbook_config.convert_xmltodict(result.text)
                # update agency id and last sync id
                self.qbo_id = response.get(
                    'IntuitResponse').get('Account').get('Id')
                rec = response.get('IntuitResponse').get('Account')
                if quickbook_config.import_account_by_date:
                    date_format = '%Y-%m-%d'
                    if quickbook_config.account_import_by == 'crt_dt':
                        date_string = rec.get('MetaData').get(
                            'CreateTime')[:10]
                    else:
                        date_string = rec.get('MetaData').get(
                            'LastUpdatedTime')[:10]

                    date_object = datetime.strptime(date_string,
                                                    date_format).date()
                    quickbook_config.import_account_date = date_object

                self._cr.commit()
                _logger.info(_("%s Updated successfully to QBO" % (self.name)))
                return True
            # else:
            if result.status_code == 400:
                _logger.info(_("STATUS CODE : %s" % (result.status_code)))
                _logger.info(_("RESPONSE DICT : %s" % (result.text)))
                response = json.loads(result.text)
                if response.get('Fault'):
                    if response.get('Fault').get('Error'):
                        for message in response.get('Fault').get('Error'):
                            if message.get('Detail') and message.get('Message'):
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': 'Error Occured',
                                        'odoo_object': 'account.account',
                                        'message': message.get('Message') + "\n\n" + message.get('Detail'),
                                        'activity': 'Exporting account from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise UserError(
                                        message.get('Message') + "\n\n" + message.get('Detail'))
                return False

    def send_account_to_qbo(self, vals):
        from_button = self._context.get('from_button', False)
        parsed_dict = json.dumps(vals)
        quickbook_config = self.company_ids
        if not quickbook_config:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'account.account',
                    'message': f"Set Company for Account {self.name}",
                    'activity': 'Exporting account from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_(f"Set Company for Account {self.name}"))

        access_token = None
        realmId = None
        if quickbook_config.access_token:
            access_token = quickbook_config.access_token
        if quickbook_config.realm_id:
            realmId = quickbook_config.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            result = requests.request('POST', quickbook_config.url + str(realmId) + "/account", headers=headers,
                                      data=parsed_dict)

            if result.status_code == 200:
                response = quickbook_config.convert_xmltodict(result.text)
                # update agency id and last sync id
                self.qbo_id = response.get(
                    'IntuitResponse').get('Account').get('Id')
                rec = response.get('IntuitResponse').get('Account')

                self._cr.commit()
                _logger.info(
                    _("%s exported successfully to QBO" % (self.name)))
                return True
            # else:
            if result.status_code == 400:
                _logger.info(_("STATUS CODE : %s" % (result.status_code)))
                _logger.info(_("RESPONSE DICT : %s" % (result.text)))



                tax_err_act = self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'[{self.code}]{self.name}',
                    'odoo_object': 'account.account',
                    'message': result.text,
                    'activity': 'Export Account  from odoo',
                    'created_date': fields.Datetime.now(),

                })


                tax_err_act = self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'[{self.code}]{self.name}',
                    'odoo_object': 'account.account',
                    'message': f'Dublicate record: {self.name}',
                    'activity': 'Export Account  from odoo',
                    'created_date': fields.Datetime.now(),

                })

                return False


class QBOAccountType(models.Model):
    _name = 'qbo.account.type'
    _description = 'QBO account type'

    name = fields.Char('Name', required=True, help='')


class QBOAccountSubtype(models.Model):
    _name = 'qbo.account.subtype'
    _description = 'QBO account subtype'

    name = fields.Char('Name', required=True, help='Display name')
    internal_name = fields.Char('Internal use', help="Internally used name")
    qbo_type_id = fields.Many2one(
        'qbo.account.type', string='QBO Type', help="Reference to QBO account type")
