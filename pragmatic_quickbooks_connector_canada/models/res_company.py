# -*- coding: utf-8 -*-
import base64
import json
import logging
from datetime import datetime, timedelta, date
import requests
import xmltodict
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning, AccessError
from xmltodict import ParsingInterrupted
import pytz
import traceback
import datetime as DT

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    product_id = fields.Many2one('product.product', string='Product', help="Select a product for export")
    quickbooks_company_name = fields.Char(string='QuickBooks Company Name', readonly=True)

    def import_all(self):
        company = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id
        _logger.info("Cron company is-> {}".format(company))

        '''
        This function will call other functions for importing all functionalities
        '''

        # 1.For importing chart_of_accounts
        company.import_chart_of_accounts()
        _logger.info("Chart of accounts imported successfully.")
        self._cr.commit()
        # 2.For importing Account Tax
        company.import_tax()
        _logger.info("Taxes imported successfully.")
        self._cr.commit()
        # 3 For importing customers
        company.import_customers()
        _logger.info("Customers imported successfully.")
        self._cr.commit()
        # 4.For importing vendors
        company.import_vendors()
        _logger.info("Vendors imported successfully.")
        self._cr.commit()
        # 5.For importing product category
        company.import_product_category()
        _logger.info("Product Categories imported successfully.")
        self._cr.commit()
        # 6.For importing products
        company.import_product()
        _logger.info("Product imported successfully.")
        self._cr.commit()
        # 7.for importing inventory
        company.import_inventory()
        _logger.info("Inventory imported successfully.")
        self._cr.commit()

        # 8.For importing payment method
        company.import_payment_method()
        _logger.info("Payment methods imported successfully.")
        self._cr.commit()

        # 9.For importing payment terms from quickbooks
        company.import_payment_term_from_quickbooks()
        _logger.info("Payment terms imported successfully.")
        self._cr.commit()

        # 10.For importing sale order
        company.import_sale_order()
        _logger.info("Sale Orders imported successfully.")
        self._cr.commit()

        # 11.For importing invoice
        invoice_obj = self.env['account.move']
        invoice_obj.import_invoice()
        _logger.info("Invoice imported successfully.")
        self._cr.commit()

        creditmemo_obj = self.env['account.move']
        creditmemo_obj.import_credit_memo()
        _logger.info("Credit Memo imported successfully.")
        self._cr.commit()

        # 12.For importing purchase order
        company.import_purchase_order()
        _logger.info("Purchase Order imported successfully.")
        self._cr.commit()

        # 13.For importing vendor bill
        vendorbill_obj = self.env['account.move']
        vendorbill_obj.import_vendor_bill()
        _logger.info("Vendor Bills imported successfully.")
        self._cr.commit()

        # 14.For importing payment
        company.import_payment()
        _logger.info("Vendors imported successfully.")
        self._cr.commit()

        # 15.For importing bill payment
        company.import_bill_payment()
        _logger.info("Bill payments imported successfully.")
        self._cr.commit()

        # 16.For importing department
        company.import_department()
        _logger.info("Department imported successfully.")
        self._cr.commit()

        # 17.For importing Employee
        company.import_employee()
        _logger.info("Employees imported successfully.")
        self._cr.commit()

        success_form = self.env.ref(
            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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

    def import_customer_vendor_cron(self):
        # companys = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_ids
        companys = self.env['res.company'].search(
            [])
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            if not company:
                company = self.env.company

            '''
            This function will import customers and vendors from qbo
            '''
            # For importing customers
            company.import_customers(call_from='cron', company=company)
            _logger.info("Customers imported successfully.")
            self._cr.commit()
            # For importing vendors
            company.import_vendors(call_from='cron', company=company)
            _logger.info("Vendors imported successfully.")
            self._cr.commit()

    def import_product_cron(self):
        companys = self.env.companies
        if not companys:
            company = self.env.company
            company.import_product(call_from='cron')
            _logger.info("Products imported successfully.")
            self._cr.commit()
        if companys:
            for company in companys:
                _logger.info("Cron company is-> {}".format(company))
                '''
                This function will import products from qbo
                '''
                # For importing customers
                company.import_product(call_from='cron', company=company)
                _logger.info("Products imported successfully.")
                self._cr.commit()

    def import_customer_invoice_cron(self):
        # companys = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_ids
        companys = self.env.companies
        # for company in companys:
        # companys = self.env['res.company'].search(
        #     [])
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))

            '''
            This function will import invoices from qbo
            '''
            # For importing invoices
            invoice_obj = self.env['account.move']
            invoice_obj.import_invoice(call_from='cron', company=company)
            _logger.info("Invoice imported successfully.")
            self._cr.commit()

    def import_purchase_order_cron(self):
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        companys = self.env.companies
        if not companys:
            company = self.env.company

        '''
        This function will import purchase orders from qbo
        '''
        # For importing purchase order from qbo
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            company.import_purchase_order()
            _logger.info("Purchase Order imported successfully.")
            self._cr.commit()

    def import_vendor_bill_cron(self):
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        companys = self.env.companies
        if not companys:
            company = self.env.company
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            # 13.For importing vendor bill
            vendorbill_obj = self.env['account.move']
            vendorbill_obj.import_vendor_bill(call_from='cron', company=company)
            _logger.info("Vendor Bills imported successfully.")
            self._cr.commit()

    def import_customer_payment_cron(self):
        # companys = self.env['res.company'].search([]).company_ids
        companys = self.env.companies

        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            # For importing payment
            company.import_payment(company)
            _logger.info("Customer Payments imported successfully.")
            self._cr.commit()

    def import_vendor_payment_cron(self):
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        companys = self.env.companies
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            # .For importing bill payment
            company.import_bill_payment(cron=True)
            _logger.info("Bill payments imported successfully.")
            self._cr.commit()

    def export_customer_payment_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_customer_payment()

        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        # company.export_customer_payment()

    def export_vendor_payment_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_vendor_payment(cron=1)

    def export_vendor_payment_button(self):
        companys = self.env.companies
        for company in companys:
            company.export_vendor_payment()
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

    def export_customer_vendor_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_customers(cron=1)
            company.export_vendors(cron=1)

        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        # company.export_customers()
        # company.export_vendors()
        # company.export_products()

    def export_product_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_products(cron=1)
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        # company.export_products()

    # def export_account_cron(self):
    #     company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
    #     company.export_accounts()
    #     company.tax()

    def export_saleorder_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_sale_order(cron=1)
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        # company.export_sale_order()

    def export_purchaseorder_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_purchase_order(cron=1)
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        # company.export_purchase_order()

    def export_customer_invoice_cron(self):
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        companys = self.env.companies
        for company in companys:
            company.export_invoice()

    def export_vendor_bill_cron(self):
        companys = self.env.companies
        for company in companys:
            company.export_vendor_bill(cron=1)
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        # company.export_vendor_bill()

    def import_invoice_custom(self):

        invoice_obj = self.env['account.move']
        try:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user. QBO Invoice ID: %s") % (self.quickbooks_last_invoice_imported_id or 'N/A'))

            if self.import_mapping_inv_field and self.env.context.get('mapping'):
                headers = {}
                headers['Authorization'] = 'Bearer ' + self.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'

                try:
                    if self.env.context.get('credit'):
                        if company.import_credit_memo_by_date:
                            query = "select * from CreditMemo WHERE Metadata.CreateTime > '%s' AND ID >= '%s' order by Id STARTPOSITION %s MAXRESULTS %s " % (
                                self.import_credit_memo_date, self.quickbooks_last_invoice_imported_id, self.start,
                                self.limit)
                        else:
                            query = "select * from CreditMemo WHERE Id > '%s' order by Id STARTPOSITION %s MAXRESULTS %s " % (
                                self.quickbooks_last_invoice_imported_id, self.start, self.limit)
                    else:
                        if company.import_invoice_by_date:
                            if self.invoice_import_by == 'crt_dt':
                                query = "select * from invoice WHERE Metadata.CreateTime >= '%s' AND ID >= '%s' order by Id STARTPOSITION %s MAXRESULTS %s " % (
                                    self.import_invoice_date, self.quickbooks_last_invoice_imported_id, self.start,
                                    self.limit)
                            else:
                                query = "select * from invoice WHERE Metadata.LastUpdatedTime >= '%s' AND ID >= '%s' order by Id STARTPOSITION %s MAXRESULTS %s " % (
                                    self.import_invoice_date, self.quickbooks_last_invoice_imported_id, self.start,
                                    self.limit)
                        else:
                            query = "select * from invoice WHERE Id > '%s' order by Id STARTPOSITION %s MAXRESULTS %s " % (
                                self.quickbooks_last_invoice_imported_id, self.start, self.limit)
                    data = requests.request('GET', self.url + str(self.realm_id) + "/query?query=" + query, headers=headers)
                    if data:
                        parsed_data = json.loads(str(data.text))
                        if parsed_data:
                            if self.env.context.get('credit'):
                                if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('CreditMemo'):
                                    self.import_mapping_credit_id.with_context(
                                        {'import': True}).json_data = parsed_data.get('QueryResponse').get('CreditMemo')
                                else:
                                    raise ValidationError(
                                        _("No Credit Memo data found for QBO Invoice ID: %s") % (self.quickbooks_last_invoice_imported_id or 'N/A'))
                            else:
                                if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Invoice'):
                                    self.import_mapping_inv_id.with_context({'import': True}).json_data = parsed_data.get(
                                        'QueryResponse').get('Invoice')
                                else:
                                    raise ValidationError(
                                        _("No Invoice data found for QBO Invoice ID: %s") % (self.quickbooks_last_invoice_imported_id or 'N/A'))
                    return
                except requests.exceptions.RequestException as req_err:
                    raise ValidationError(
                        _("HTTP Request failed for QBO Invoice ID: %s. Error: %s") % (
                            self.quickbooks_last_invoice_imported_id or 'N/A', str(req_err)))
                except json.JSONDecodeError as json_err:
                    raise ValidationError(
                        _("Failed to parse response for QBO Invoice ID: %s. Error: %s") % (
                            self.quickbooks_last_invoice_imported_id or 'N/A', str(json_err)))
                except Exception as inner_e:
                    raise ValidationError(
                        _("Unexpected error occurred while importing QBO Invoice ID: %s. Error: %s") % (
                            self.quickbooks_last_invoice_imported_id or 'N/A', str(inner_e)))
            invoice_obj.import_invoice(company=company)
            _logger.info("Invoice imported successfully.")
            self._cr.commit()
            success_form = self.env.ref(
                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
        except (UserError, ValidationError):
            raise
        except Exception as e:
            _logger.error('Unexpected Error : {}'.format(e))
            raise UserError(_("An error occurred while importing invoice. QBO Invoice ID: %s. Error: %s") %
                            (self.quickbooks_last_invoice_imported_id or 'N/A', str(e)))


    def import_credit_memo_custom(self):
        company = self
        if not company:
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user"))
        creditmemo_obj = self.env['account.move']
        creditmemo_obj.import_credit_memo(company=company)
        _logger.info("Credit Memo imported successfully.")
        self._cr.commit()
        success_form = self.env.ref(
            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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

    def import_vendor_bill_custom(self):
        _logger.info("=======vendor bill ===========")
        try:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(_("Company is not allowed for user (Company ID: {})").format(company.id))
            if self.import_mapping_bill_field and self.env.context.get('mapping'):
                headers = {}
                headers['Authorization'] = 'Bearer ' + self.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'

                if company.import_bills_by_date:
                    if company.vendor_bill_import_by == 'crt_dt':
                        query = f"select * from Bill WHERE Metadata.CreateTime >= '{company.import_bills_date}' order by Id MAXRESULTS {company.limit}"
                    elif company.vendor_bill_import_by == 'other_dt':
                        query = f"select * from Bill WHERE TxnDate >= '{company.import_bills_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Bill WHERE Metadata.LastUpdatedTime >= '{company.import_bills_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Bill order by Id STARTPOSITION {company.quickbooks_last_vendor_bill_imported_id} MAXRESULTS {company.limit}"
                
                try:
                    data = requests.request('GET', self.url + str(self.realm_id) + "/query?query=" + query, headers=headers)
                except requests.exceptions.RequestException as re:
                    raise UserError(_("Failed to connect to QuickBooks API: {}").format(str(re)))

                if data:
                    recs = []
                    try:
                        parsed_data = json.loads(str(data.text))
                    except json.JSONDecodeError as je:
                        raise ValidationError(_("Failed to parse JSON response from QuickBooks API: {}").format(str(je)))

                    if parsed_data:
                        try:
                            if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Bill'):
                                self.import_mapping_bill_id.with_context({'import': True}).json_data = parsed_data.get(
                                    'QueryResponse').get('Bill')
                        except Exception as e:
                            raise ValidationError(_("Error processing vendor bill data (Last Imported QBO ID: %s): %s") % (
                                self.quickbooks_last_vendor_bill_imported_id, str(e)))

                return
            
            try:
                vendorbill_obj = self.env['account.move']
                vendorbill_obj.import_vendor_bill(company=company)
            except (UserError, ValidationError):
                raise
            except Exception as ve:
                raise ValidationError(_("Failed to import vendor bill into Odoo (QBO Last Imported ID: %s): %s") % (
                    self.quickbooks_last_vendor_bill_imported_id, str(ve)))
            
            _logger.info("Vendor Bill imported successfully.")
            self._cr.commit()

            success_form = self.env.ref(
                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
        except ValidationError as ve:
            _logger.error('ValidationError: {}'.format(str(ve)))
            raise
        except UserError as ue:
            _logger.error('UserError: {}'.format(str(ue)))
            raise
        except Exception as e:
            _logger.error('Unhandled Error: {}'.format(e))
            raise UserError(_("Unexpected error occurred while importing vendor bills (QBO Last Imported ID: %s): %s") % (
                self.quickbooks_last_vendor_bill_imported_id, str(e)))

    @api.model
    def convert_xmltodict(self, response):
        """Return dictionary object"""
        try:
            # convert xml response to OrderedDict collections, return collections.OrderedDict type
            if type(response) != dict:
                order_dict = xmltodict.parse(response)
            else:
                order_dict = response
        except ParsingInterrupted as e:
            _logger.error(e)
            raise e
        # convert OrderedDict to regular dictionary object
        response_dict = json.loads(json.dumps(order_dict))
        return response_dict

    # Company level QuickBooks Configuration fields
    client_id = fields.Char(
        'Client Id', copy=False, help="The client ID you obtain from the developer dashboard.")
    client_secret = fields.Char('Client Secret', copy=False,
                                help="The client secret you obtain from the developer dashboard.")

    auth_base_url = fields.Char('Authorization URL', default="https://appcenter.intuit.com/connect/oauth2",
                                help="User authenticate uri")
    access_token_url = fields.Char('Authorization Token URL',
                                   default="https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
                                   help="Exchange code for refresh and access tokens")
    request_token_url = fields.Char('Redirect URL', default="http://localhost:5000/get_auth_code",
                                    help="One of the redirect URIs listed for this project in the developer dashboard.")
    url = fields.Char('API URL', default="https://sandbox-quickbooks.api.intuit.com/v3/company/",
                      help="Intuit API URIs, use access token to call Intuit API's")

    # used for api calling, generated during authorization process.
    realm_id = fields.Char('Company Id/ Realm Id', copy=False, help="A unique company Id returned from QBO",
                           company_dependent=False)
    auth_code = fields.Char(
        'Auth Code', copy=False, help="An authenticated code", company_dependent=False)
    access_token = fields.Char('Access Token', copy=False, company_dependent=False,
                               help="The token that must be used to access the QuickBooks API. Access token expires in 3600 seconds.")
    minorversion = fields.Char('Minor Version', copy=False, default="75",
                               help="QuickBooks minor version information, used in API calls.")
    access_token_expire_in = fields.Datetime(
        'Access Token Expire In', copy=False, help="Access token expire time.")
    qbo_refresh_token = fields.Char('Refresh Token', copy=False, company_dependent=False,
                                    help="The token that must be used to access the QuickBooks API. Refresh token expires in 8726400 seconds.")
    refresh_token_expire_in = fields.Datetime(
        'Refresh Token Expire In', copy=False, help="Refresh token expire time.")

    #     '''  Tracking Fields for Customer'''
    #     x_quickbooks_last_customer_sync = fields.Datetime('Last Synced On', copy=False,)
    #     x_quickbooks_last_customer_imported_id = fields.Integer('Last Imported ID', copy=False,)
    '''  Tracking Fields for Account'''
    # last_customer_imported_id = fields.Char('Last Imported Customer Id', copy=False, default=0)
    last_acc_imported_id = fields.Char(
        'Last Imported Account Position', copy=False, default=0)
    last_imported_tax_id = fields.Char(
        'Last Imported Tax Position', copy=False, default=0)
    last_imported_tax_agency_id = fields.Char(
        'Last Imported Tax Agency Position', copy=False, default=0)
    last_imported_product_category_id = fields.Char(
        'Last Imported Product Category Position', copy=False, default=0)
    last_imported_product_id = fields.Char('Last Imported Product Position', copy=False, default=0,
                                           help="SKU ID should be Unique in QBO")
    last_imported_inv_product_id = fields.Char('Last Imported Inventory Product Position', copy=False, default=0,
                                               help="SKU ID should be Unique in QBO")
    last_imported_customer_id = fields.Char(
        'Last Imported Customer Position', copy=False, default=0)
    last_imported_vendor_id = fields.Char(
        'Last Imported Vendor Position', copy=False, default=0)
    last_imported_payment_method_id = fields.Char(
        'Last Imported Payment Method Position', copy=False, default=0)
    last_imported_payment_id = fields.Char(
        'Last Imported Payment Position', copy=False, default=0)
    last_imported_bill_payment_id = fields.Char(
        'Last Imported Bill Payment Position', copy=False, default=0)
    quickbooks_last_employee_imported_id = fields.Integer('Last Employee Position')
    quickbooks_last_dept_imported_id = fields.Integer('Last Department Position')
    quickbooks_last_sale_imported_id = fields.Integer('Last Sale Order Position')
    quickbooks_last_invoice_imported_id = fields.Integer('Last Invoice Position')
    quickbooks_last_purchase_imported_id = fields.Integer(
        'Last Purchase Order Position')
    quickbooks_last_vendor_bill_imported_id = fields.Integer(
        'Last Vendor Bill Position')
    quickbooks_last_credit_note_imported_id = fields.Integer(
        'Last Credit Note Position')
    quickbooks_last_journal_entry_imported_id = fields.Integer(
        'Last Journal Entry Position')
    quickbooks_last_sales_receipt_imported_id = fields.Integer(
        'Last Sales Receipt Position')
    quickbooks_last_trns_imported_id = fields.Integer(
        'Last Transfer Position')
    quickbooks_last_expns_imported_id = fields.Integer(
        'Last Expense Position')
    # quickbooks_last_vendor_credit_imported_id = fields.Integer(
    #     'Last Vendor Credit Id')
    quickbooks_last_dp_imported_id = fields.Integer(
        'Last Deposit Position')

    start = fields.Integer('Start', default=1)
    limit = fields.Integer('Limit', default=100)
    '''  Tracking Fields for Payment Term'''
    x_quickbooks_last_paymentterm_sync = fields.Datetime(
        'Last Synced On', copy=False)
    x_quickbooks_last_paymentterm_imported_id = fields.Integer(
        'Last Imported Position', copy=False)

    # suppress_warning = fields.Boolean('Suppress Warning', default=False, copy=False,help="If you all Suppress Warnings,all the warnings will be suppressed and logs will be created instead of warnings")
    qbo_domain = fields.Selection([('sandbox', 'Sandbox'), ('production', 'Production')],
                                  string='QBO Domain', default='sandbox')
    qb_account_recievable = fields.Many2one('account.account', 'Account Recievable',
                                            domain="[('account_type', '=', 'asset_receivable'), ('qbo_id', '!=', False)]")
    qb_account_payable = fields.Many2one('account.account', 'Account Payable',
                                         domain="[('account_type', '=', 'liability_payable'), ('qbo_id', '!=', False)]")
    qb_income_account = fields.Many2one('account.account', 'Income Account',
                                        domain="[('account_type', '=', 'income'), ('qbo_id', '!=', False)]")
    qb_expense_account = fields.Many2one('account.account', 'Expense Account',
                                         domain="[('account_type', '=', 'expense'), ('qbo_id', '!=', False)]")
    journal_entry = fields.Many2one('account.journal', help="Journal Entry")
    transfer_journal_entry = fields.Many2one('account.journal', help="Transfer Journal Entry")
    deposit_journal_entry = fields.Many2one('account.journal', help="Deposit Journal Entry")
    expense_journal_entry = fields.Many2one('account.journal', help="Expenses Journal Entry")

    # Quickbooks config
    import_inactive_customer = fields.Boolean('Import Inactive Customer', default=False)
    export_bill_without_product = fields.Boolean('Export Bill Without Product', default=False)
    update_customer_export = fields.Boolean('Update Customer While Export', default=False)
    update_customer_import = fields.Boolean('Update Customer While Import', default=True)
    update_vendor_export = fields.Boolean('Update Vendor While Export', default=False)
    update_vendor_import = fields.Boolean('Update Vendor While Import', default=True)
    update_product_export = fields.Boolean('Update Product While Export', default=False)
    update_product_import = fields.Boolean('Update Product While Import', default=True)
    update_account_import = fields.Boolean('Update Account While Import', default=True)
    non_tracked_item = fields.Boolean(
        'Export Stockable Product as Non Tracked Items', copy=False)
    partner_individual_records = fields.Boolean(
        'Company Record Only Export', copy=False)
    separate_invoice_export = fields.Boolean(
        'Separate Invoice Export', copy=False)
    import_inactive_product = fields.Boolean(
        'Import Inactive Product', copy=False)
    export_seprate_payment = fields.Boolean(
        'Export Seprate Payment', copy=False)
    export_pos_payment = fields.Boolean('Export POS Payment', copy=False)
    export_pos_journal = fields.Many2one('account.journal', help="we check if journal is POS Journal then this entry export as payment in qbo", String="POS Journal")
    export_pos_payment_account = fields.Many2one('account.account',
                                         help="Deposit to this Account while export ",
                                         String="POS Payment Account",domain="[('account_type', '=', 'asset_cash'), ('qbo_id', '!=', False)]")
    update_tax_invoice_export = fields.Boolean(
        'Update Tax while export Invoice/Bill And Update Payment', copy=False)
    export_product_wo_sku = fields.Boolean(
        'Export Product Without Internal Reference', copy=False)
    update_account_export = fields.Boolean('Update Account While Export', default=False)

    import_mapping_customer_field = fields.Boolean('Import Mapping Customer?')
    import_mapping_customer_id = fields.Many2one('mapping.fields', 'Import Customer Mapping')
    import_mapping_vendor_field = fields.Boolean('Import Mapping Vendor?')
    import_mapping_vendor_id = fields.Many2one('mapping.fields', 'Import Vendor Mapping')
    import_mapping_so_field = fields.Boolean('Import Mapping Sale Order?')
    import_mapping_so_id = fields.Many2one('mapping.fields', 'Import Sale Order Mapping')
    import_mapping_po_field = fields.Boolean('Import Mapping Purchase Order?')
    import_mapping_po_id = fields.Many2one('mapping.fields', 'Import Purchase Order')
    import_mapping_inv_field = fields.Boolean('Import Mapping Invoice?')
    import_mapping_inv_id = fields.Many2one('mapping.fields', 'Import Invoice Mapping')
    import_mapping_bill_field = fields.Boolean('Import Mapping Bills?')
    import_mapping_bill_id = fields.Many2one('mapping.fields', 'Import Bills Mapping')

    export_mapping_customer_field = fields.Boolean('Export Mapping Customer?')
    export_mapping_customer_id = fields.Many2one('mapping.fields', 'Export Customer Mapping')
    last_customer_mapping_export = fields.Datetime('Last Customer Export Mapping On')

    export_mapping_vendor_field = fields.Boolean('Export Mapping Vendor?')
    export_mapping_vendor_id = fields.Many2one('mapping.fields', 'Export Vendor Mapping')
    last_vendor_mapping_export = fields.Datetime('Last Vendor Export Mapping On')

    export_mapping_so_field = fields.Boolean('Export Mapping Sale Order?')
    export_mapping_so_id = fields.Many2one('mapping.fields', 'Export Sale Order')
    last_so_mapping_export = fields.Datetime('Last SO Export Mapping On')

    export_mapping_po_field = fields.Boolean('Export Mapping Purchase Order?')
    export_mapping_po_id = fields.Many2one('mapping.fields', 'Export Purchase Order')
    last_po_mapping_export = fields.Datetime('Last PO Export Mapping On')

    export_mapping_inv_field = fields.Boolean('Export Mapping Invoice?')
    export_mapping_inv_id = fields.Many2one('mapping.fields', 'Export Invoice')
    last_inv_mapping_export = fields.Datetime('Last Invoice Export Mapping On')

    export_mapping_bill_field = fields.Boolean('Export Mapping Bill?')
    export_mapping_bill_id = fields.Many2one('mapping.fields', 'Export Bill')
    last_bill_mapping_export = fields.Datetime('Last Bill Export Mapping On')

    import_mapping_product_field = fields.Boolean('Import Mapping Product?')
    import_mapping_product_id = fields.Many2one('mapping.fields', 'Import Product Mapping')
    export_mapping_product_field = fields.Boolean('Export Mapping Product?')
    export_mapping_product_id = fields.Many2one('mapping.fields', 'Export Product')
    last_product_mapping_export = fields.Datetime('Last Product Export Mapping On')

    import_mapping_account_field = fields.Boolean('Import Mapping Account?')
    import_mapping_account_id = fields.Many2one('mapping.fields', 'Import Account Mapping')
    export_mapping_account_field = fields.Boolean('Export Mapping Account?')
    export_mapping_account_id = fields.Many2one('mapping.fields', 'Export Account')
    last_account_mapping_export = fields.Datetime('Last Account Export Mapping On')

    import_mapping_tax_field = fields.Boolean('Import Mapping Tax?')
    import_mapping_tax_id = fields.Many2one('mapping.fields', 'Import Tax Mapping')
    export_mapping_tax_field = fields.Boolean('Export Mapping Tax?')
    export_mapping_tax_id = fields.Many2one('mapping.fields', 'Export Tax')
    last_tax_mapping_export = fields.Datetime('Last Tax Export Mapping On')

    import_mapping_product_category_field = fields.Boolean('Import Mapping Product Category?')
    import_mapping_product_category_id = fields.Many2one('mapping.fields', 'Import Product Category')
    export_mapping_product_category_field = fields.Boolean('Export Mapping Product Category?')
    export_mapping_product_category_id = fields.Many2one('mapping.fields', 'Export Product Category')
    last_product_category_mapping_export = fields.Datetime('Last Product Category Export Mapping On')

    import_mapping_payment_term_field = fields.Boolean('Import Mapping Payment Term Category?')
    import_mapping_payment_term_id = fields.Many2one('mapping.fields', 'Import Payment Term')
    export_mapping_payment_term_field = fields.Boolean('Export Mapping Payment Term?')
    export_mapping_payment_term_id = fields.Many2one('mapping.fields', 'Export Payment Term')
    last_payment_term_mapping_export = fields.Datetime('Last Payment Term Export Mapping On')

    import_mapping_credit_field = fields.Boolean('Import Mapping Credit Memo?')
    import_mapping_credit_id = fields.Many2one('mapping.fields', 'Import Credit Memo Mapping')
    export_mapping_credit_field = fields.Boolean('Export Mapping Credit Memo?')
    export_mapping_credit_id = fields.Many2one('mapping.fields', 'Export Credit Memo')
    last_credit_mapping_export = fields.Datetime('Last Credit Memo Export Mapping On')

    import_mapping_cust_payment_field = fields.Boolean('Import Mapping Customer Payment?')
    import_mapping_cust_payment_id = fields.Many2one('mapping.fields', 'Import Customer Payment')

    import_mapping_vendor_payment_field = fields.Boolean('Import Mapping Vendor Payment?')
    import_mapping_vendor_payment_id = fields.Many2one('mapping.fields', 'Import Vendor Payment')

    import_mapping_department_field = fields.Boolean('Import Mapping Department?')
    import_mapping_department_id = fields.Many2one('mapping.fields', 'Import Department Mapping')
    export_mapping_department_field = fields.Boolean('Export Mapping Department?')
    export_mapping_department_id = fields.Many2one('mapping.fields', 'Export Department')
    last_department_mapping_export = fields.Datetime('Last Department Export Mapping On')

    import_mapping_employee_field = fields.Boolean('Import Mapping Employee?')
    import_mapping_employee_id = fields.Many2one('mapping.fields', 'Import Employee Mapping')
    export_mapping_employee_field = fields.Boolean('Export Mapping Employee?')
    export_mapping_employee_id = fields.Many2one('mapping.fields', 'Export Employee')
    last_employee_mapping_export = fields.Datetime('Last Employee Export Mapping On')

    import_category_detail = fields.Boolean(string="Import Category Details", copy=False)

    import_account_by_date = fields.Boolean('Import Account By Custom Date?')
    account_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt", help="Define the criteria for importing accounts based on dates.")
    tax_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt", help="Define the criteria for importing taxes based on dates.")
    cutomer_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    vendor_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    prodct_catgry_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    prodct_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    paymnt_method_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    paymnt_term_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    sale_order_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")

    invoice_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")
    credit_memo_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")
    purchase_order_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")
    vendor_bill_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")
    customer_paymnt_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")

    vendor_paymnt_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")
    department_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    employee_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date')],
        default="crt_dt")
    journal_entry_import_by = fields.Selection(
        [('crt_dt', 'Create Date'), ('updt_dt', 'Update Date'), ('other_dt', 'Document Date')],
        default="crt_dt")

    import_account_date = fields.Date('Import Account Date')

    import_tax_by_date = fields.Boolean('Import Tax By Custom Date?')
    import_tax_date = fields.Date('Import Tax Date')

    import_customer_by_date = fields.Boolean('Import Customer By Custom Date?')
    import_customer_date = fields.Date('Import Customer Date')

    import_vendor_by_date = fields.Boolean('Import Vendor By Custom Date?')
    import_vendor_date = fields.Date('Import Vendor Date')

    import_pc_by_date = fields.Boolean('Import Product Category By Custom Date?')
    import_pc_date = fields.Date('Import Product Category Date')

    import_product_by_date = fields.Boolean('Import Product By Custom Date?')
    import_product_date = fields.Date('Import Product Date')

    import_payment_method_by_date = fields.Boolean('Import Payment Method By Custom Date?')
    import_payment_method_date = fields.Date('Import Payment Method Date')

    import_payment_term_by_date = fields.Boolean('Import Payment Term By Custom Date?')
    import_payment_term_date = fields.Date('Import Payment Term Date')

    import_sale_order_by_date = fields.Boolean('Import Sale Order By Custom Date?')
    import_sale_order_date = fields.Date('Import Sale Order Date')

    import_invoice_by_date = fields.Boolean('Import Invoice By Custom Date?')
    import_invoice_date = fields.Date('Import Invoice Date')

    import_credit_memo_by_date = fields.Boolean('Import Credit Memo By Custom Date?')
    import_credit_memo_date = fields.Date('Import Credit Memo Date')

    import_purchase_order_by_date = fields.Boolean('Import Purchase Order By Custom Date?')
    import_purchase_order_date = fields.Date('Import Purchase Order Date')

    import_bills_by_date = fields.Boolean('Import Bills By Custom Date?')
    import_bills_date = fields.Date('Import Bills Date')

    import_cp_by_date = fields.Boolean('Import Customer Payment By Custom Date?')
    import_cp_date = fields.Date('Import Customer Payment Date')

    import_vp_by_date = fields.Boolean('Import Vendor Payment By Custom Date?')
    import_vp_date = fields.Date('Import Vendor Payment Date')

    import_department_by_date = fields.Boolean('Import Department By Custom Date?')
    import_department_date = fields.Date('Import Department Date')

    import_employee_by_date = fields.Boolean('Import Employee By Custom Date?')
    import_employee_date = fields.Date('Import Employee Date')

    import_je_by_date = fields.Boolean('Import Journal Entry By Custom Date?')
    import_je_date = fields.Date('Import Journal Entry Date')
    import_sr_by_date = fields.Boolean('Import Sales Receipt By Custom Date?')
    import_sr_date = fields.Date('Import Sales Receipt Date')
    import_trns_by_date = fields.Boolean('Import Transfer By Custom Date?')
    import_trns_date = fields.Date('Import Transfer Date')
    import_expns_by_date = fields.Boolean('Import Expense By Custom Date?')
    # import_vendor_credit_by_date = fields.Boolean('Import Vendor Credit By Custom Date?')
    import_expns_date = fields.Date('Import Expense Date')
    # import_vendor_credit_date = fields.Date('Import Vendor Credit Date')
    import_dp_by_date = fields.Boolean('Import Deposit By Custom Date?')
    import_dp_date = fields.Date('Import Deposit Date')

    delivery_carrier_id = fields.Many2one('delivery.carrier', 'Shipping Method')
    default_customer_journal_entry = fields.Many2one('res.partner', 'Default Customer Journal Entry')
    import_timesheet_by_date = fields.Boolean('Import Timesheet By Custom Date?')
    import_timesheet_date = fields.Date('Import Timesheet Date')
    quickbooks_last_timesheet_imported_id = fields.Integer('Last Timesheet Id')
    default_project_id = fields.Many2one('project.project', string='Default Project(Timesheet)')

    import_project_by_date = fields.Boolean('Import Project By Custom Date?')
    import_project_date = fields.Date('Import Project Date')
    quickbooks_last_project_imported_id = fields.Integer('Last Project Id')
    timesheet_access = fields.Boolean('Enble Timesheet Functionality')

    def import_timesheet(self, call_from=None, company=None):
        try:
            if self:
                company = self
                if not company:
                    companys = self.env['res.users'].search([('id', '=', self._uid)]).company_ids
                    if not company in companys:
                        raise ValidationError(_("Company is not allowed for user"))
                if not company:
                    company = self.env.company
                if company.import_timesheet_by_date:
                    query = f"select * from TimeActivity WHERE TxnDate >= '{company.import_timesheet_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from TimeActivity order by Id STARTPOSITION {company.quickbooks_last_timesheet_imported_id} MAXRESULTS {company.limit}"
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/query?%squery=%s' % (
                    'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
                data = requests.request('GET', url, headers=url_str.get('headers'))
                if data.status_code == 200:
                    max_result = self.env['account.analytic.line'].create_timesheet(data, company=company)
                    if max_result:
                        company.quickbooks_last_timesheet_imported_id = max_result + int(
                            company.quickbooks_last_timesheet_imported_id)
                        success_form = self.env.ref('pragmatic_quickbooks_connector_canada.import_successfull_view', False)
                        return {'name': _('Notification'),
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'res.company.message',
                                'views': [(success_form.id, 'form')],
                                'view_id': success_form.id,
                                'target': 'new', }
                else:
                    raise UserError("Empty data")
            else:
                companys = self.env.companies
                for company in companys:
                    if company.import_timesheet_by_date:
                        query = "select * from TimeActivity WHERE TxnDate >= '%s' order by Id " % (
                            company.import_timesheet_date)
                        company.import_timesheet_date = fields.Date.today()
                    else:
                        query = "select * From TimeActivity WHERE Id > '%s' order by Id" % (
                            company.quickbooks_last_timesheet_imported_id)
                    url_str = company.get_import_query_url()
                    url = url_str.get('url') + '/query?%squery=%s' % (
                        'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '',
                        query)
                    data = requests.request('GET', url, headers=url_str.get('headers'))
                    if data.status_code == 200:
                        max_result = self.env['account.analytic.line'].create_timesheet(data, company=company)
                        if max_result:
                            company.quickbooks_last_timesheet_imported_id = max_result + int(
                                company.quickbooks_last_timesheet_imported_id)
                            success_form = self.env.ref('pragmatic_quickbooks_connector_canada.import_successfull_view',
                                                        False)
                            return {'name': _('Notification'),
                                    'type': 'ir.actions.act_window',
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_model': 'res.company.message',
                                    'views': [(success_form.id, 'form')],
                                    'view_id': success_form.id,
                                    'target': 'new', }
                    else:
                        raise UserError("Empty data")
        except Exception as e:
            raise UserError(e)

    def export_timesheet(self, cron=None, company=None):  # @api.multi
        if not company:
            company = self
        timesheets = self.env['account.analytic.line'].search(
            [('qbo_timeactivity_id', '!=', True), ('company_id', '=', company.id)])
        if not timesheets:
            raise UserError('There is no any record to be exported.')
        for timesheet in timesheets:
            try:
                if not timesheet.qbo_timeactivity_id:
                    if cron:
                        timesheet.with_context(from_button=True).export_timesheet_to_qbo(company=company, cron=1)
                    else:
                        timesheet.with_context(from_button=True).export_timesheet_to_qbo()
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': timesheet.name,
                    'odoo_object': 'account.analytic.line(TIMESHEET)',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(), })
        success_form = self.env.ref('pragmatic_quickbooks_connector_canada.export_successfull_view', False)
        return {'name': _('Notification'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.company.message',
                'views': [(success_form.id, 'form')],
                'view_id': success_form.id,
                'target': 'new', }

    def import_project(self, call_from=None, company=None):
        # CHNGE LOGIC FOR PROJECT
        try:
            if not company:
                company = self
                companys = self.env['res.users'].search([('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user. QBO ID: %s") % company.last_imported_customer_id)
            if not company:
                company = self.env.company
            if company.import_project_by_date:
                if self.import_project_by_date == 'crt_dt':
                    query = f"select * from Customer WHERE Metadata.CreateTime >= '{company.import_project_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Customer WHERE Metadata.LastUpdatedTime >= '{company.import_project_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from Customer order by Id STARTPOSITION {company.quickbooks_last_project_imported_id} MAXRESULTS {company.limit}"
            if call_from == 'cron':
                url_str = company.get_import_query_url(call_from='cron')
            else:
                url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            data = requests.request('GET', url, headers=url_str.get('headers'), verify=False)
            if data.status_code == 200:
                _logger.info("Customer data is ------------> {}".format(data))
                res = json.loads(str(data.text))

                max_result = self.env['project.project'].create_project(data, company)
                if max_result:
                    company.quickbooks_last_project_imported_id = max_result + int(
                        company.quickbooks_last_project_imported_id)
                    success_form = self.env.ref('pragmatic_quickbooks_connector_canada.import_successfull_view', False)
                    return {'name': _('Notification'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'res.company.message',
                            'views': [(success_form.id, 'form')],
                            'view_id': success_form.id,
                            'target': 'new', }
            else:
                if call_from == 'cron':
                    log = self.env['qbo.logger'].create({
                        'odoo_name': 'Authantication',
                        'odoo_object': 'Res Company',
                        'message': "Empty Data",
                        'created_date': datetime.now(), })
                else:
                    log_response = self.env['qbo.logger'].create({
                        'odoo_name': f"Project Status Code: {data.status_code}",
                        'odoo_object': 'project.project',
                        'activity': 'Import Project',
                        'message': f"Response : {data.text}",
                        'created_date': datetime.now(), })
                    self.env.cr.commit()  # Commit the transaction so the log entry is saved before the exception
                    raise UserError("Empty Data. QBO ID: %s" % company.last_imported_customer_id)
        except (UserError, ValidationError) as e:
            if call_from == 'cron':
                _logger.exception("Unexpected error occurred while importing customers.")
            else:
                raise e
        except Exception as e:
            raise ValidationError(
                _("Unexpected error while importing customers. Last Imported Vendor ID: %s. Error: %s") % (
                    company.last_imported_customer_id if company else 'Unknown', str(e)))

    def import_timesheet_cron(self):  # This function will import Timesheet from qbo
        companys = self.env['res.company'].search([])
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            if not company:
                company = self.env.company
            company.import_timesheet(call_from='cron', company=company)  # For importing Timesheet
            _logger.info("Timesheet imported successfully.")
            self._cr.commit()

    def export_timesheet_cron(self):  # This function will Export Timesheet from qbo
        companys = self.env['res.company'].search([])
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))
            if not company:
                company = self.env.company
            company.export_timesheet(cron='cron', company=company)  # For Export Timesheet
            _logger.info("Timesheet imported successfully.")
            self._cr.commit()

    # setting up the Account Receivable for Partners
    #     @api.onchange('qb_account_recievable')
    #     def onchange_qb_account_recievable(self):
    #         acc_dict={}
    #         acc_dict.update({'name':'property_account_receivable_id'})
    #         model_id = self.env['ir.model'].search([('name','=','Contact')])
    #         if model_id:
    #             field_id = self.env['ir.model.fields'].search([('name','=','property_account_receivable_id'),('field_description','=','Account Receivable'),('model_id','=',model_id.id)])
    #             if field_id:
    #                 acc_dict.update({'fields_id':field_id[0].id})
    #         account_id = self.env['account.account'].search([('name','=',self.qb_account_recievable.name)])
    #         if account_id:
    #             acc_dict.update({'value_reference':'account.account,'+str(account_id[0].id)})
    #         if acc_dict:
    # if  not self.qb_account_recievable:
    #             self.env['ir.property'].create(acc_dict)
    #         else:
    #             raise ValidationError(_('You have already set Account Receivable !changing it may cause inconsistency'))

    # Setting Up the Account Payable for Partners
    #     @api.onchange('qb_account_payable')
    #     def onchange_qb_account_payable(self):
    #         ap_dict={}
    #         ap_dict.update({'name':'property_account_payable_id'})
    #         model_id = self.env['ir.model'].search([('name','=','Contact')])
    #         if model_id:
    #             field_id = self.env['ir.model.fields'].search([('name','=','property_account_payable_id'),('field_description','=','Account Payable'),('model_id','=',model_id.id)])
    #             if field_id:
    #                 ap_dict.update({'fields_id':field_id[0].id})
    #         account_id = self.env['account.account'].search([('name','=',self.qb_account_payable.name)])
    #         if account_id:
    #             ap_dict.update({'value_reference':'account.account,'+str(account_id[0].id)})
    # if  not self.qb_account_payable:
    #         if ap_dict:
    #             self.env['ir.property'].create(ap_dict)
    #         else:
    #             raise ValidationError(_('You have already set Account Payable !changing it may cause inconsistency'))

    # Setting Up the Income Account for Product Category
    #     @api.onchange('qb_income_account')
    #     def onchange_qb_income_account(self):
    #         in_dict={}
    #         in_dict.update({'name':'property_account_income_categ_id'})
    #         model_id = self.env['ir.model'].search([('name','=','Product Category')])
    #         if model_id:
    #             field_id = self.env['ir.model.fields'].search([('name','=','property_account_income_categ_id'),('field_description','=','Income Account'),('model_id','=',model_id.id)])
    #             if field_id:
    #                 in_dict.update({'fields_id':field_id[0].id})
    #         account_id = self.env['account.account'].search([('name','=',self.qb_income_account.name)])
    #         if account_id:
    #             in_dict.update({'value_reference':'account.account,'+str(account_id[0].id)})
    #         if  in_dict:
    #             self.env['ir.property'].create(in_dict)
    #         else:
    #             raise ValidationError(_('You have already set Income Account !changing it may cause inconsistency'))

    # Setting Up the Expense Account for Product Category
    #     @api.onchange('qb_expense_account')
    #     def onchange_qb_expense_account(self):
    #         ex_dict={}
    #         ex_dict.update({'name':'property_account_expense_categ_id'})
    #         model_id = self.env['ir.model'].search([('name','=','Product Category')])
    #         if model_id:
    #             field_id = self.env['ir.model.fields'].search([('name','=','property_account_expense_categ_id'),('field_description','=','Expense Account'),('model_id','=',model_id.id)])
    #             if field_id:
    #                 ex_dict.update({'fields_id':field_id[0].id})
    #         account_id = self.env['account.account'].search([('name','=',self.qb_expense_account.name)])
    #         if account_id:
    #             ex_dict.update({'value_reference':'account.account,'+str(account_id[0].id)})
    #         if  ex_dict:
    #             self.env['ir.property'].create(ex_dict)
    #         else:
    #             raise ValidationError(_('You have already set Expense Account !changing it may cause inconsistency'))

    # @api.onchange('by_updatedate')
    # def onchange_by_createdate(self):
    #     if not (self.by_updatedate or self.by_createdate):
    #         raise ValidationError(_('Select By Create Date or By Update Date..!'))
    #     elif self.by_updatedate:
    #         self.by_createdate = False

    # @api.onchange('by_createdate')
    # def onchange_by_updatedate(self):
    #     if not (self.by_updatedate or self.by_createdate):
    #         raise ValidationError(_('Select By Create Date or By Update Date..!'))
    #
    #     elif self.by_createdate:
    #         self.by_updatedate = False

    # @api.multi
    def login(self):
        if not self.client_id:
            raise AccessError('Please add your Client Id')
        url = self.auth_base_url + '?client_id=' + self.client_id + \
              '&scope=com.intuit.quickbooks.accounting&redirect_uri=' + \
              self.request_token_url + '&response_type=code&state=abccc'
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new"
        }

    def refresh_token(self):
        """Get new access token from existing refresh token"""
        if not self:
            self = self.search([])
        _logger.info(
            "Current Context is ---> {}---{}".format(self, self._context))

        for company_id in self:
            try:
                if company_id:
                    _logger.info(
                        'Start ====> Trying to get access token for company {} '.format(company_id.name))
                    client_id = company_id.client_id
                    client_secret = company_id.client_secret
                    if not client_id:
                        raise AccessError("Please Configure Server Details")
                    raw_b64 = str(client_id + ":" + client_secret)
                    raw_b64 = raw_b64.encode('utf-8')
                    converted_b64 = base64.b64encode(raw_b64).decode('utf-8')
                    auth_header = 'Basic ' + converted_b64
                    headers = {}
                    headers['Authorization'] = str(auth_header)
                    headers['accept'] = 'application/json'
                    payload = {'grant_type': 'refresh_token',
                               'refresh_token': company_id.qbo_refresh_token}
                    _logger.info(
                        "Payload is --------------> {}".format(payload))
                    access_token = requests.post(
                        company_id.access_token_url, data=payload, headers=headers)
                    _logger.info(
                        "Access token is --------------> {}".format(access_token.text))
                    if access_token.status_code == 200:
                        parsed_token_response = json.loads(access_token.text)
                        _logger.info(
                            "Parsed response is ------------------> {}".format(parsed_token_response))
                        if parsed_token_response:
                            company_id.write({
                                'access_token': parsed_token_response.get('access_token'),
                                'qbo_refresh_token': parsed_token_response.get('refresh_token'),
                                'access_token_expire_in': datetime.now() + timedelta(
                                    seconds=parsed_token_response.get('expires_in')),
                                'refresh_token_expire_in': datetime.now() + timedelta(
                                    seconds=parsed_token_response.get('x_refresh_token_expires_in'))
                            })
                            _logger.info(
                                _("Success =====> Token refreshed successfully!"))
                    else:
                        response = json.loads(access_token.text)
                        if response.get('error_description'):
                            raise UserError(
                                f'Quickbooks Online Exception[{access_token.status_code}] Reason : {response.get("error_description")}')
                        else:
                            raise UserError(
                                f'Quickbooks Online Exception {access_token.status_code}')
            except Exception as e:
                _logger.error('Error =====> : {}  {}'.format(e, len(self)))
                if len(self) == 1:
                    raise ValidationError(e)

    @api.model
    @api.onchange('qbo_domain')
    def onchange_qbo_domain(self):
        if self.qbo_domain == 'sandbox':
            self.url = 'https://sandbox-quickbooks.api.intuit.com/v3/company/'
        else:
            self.url = 'https://quickbooks.api.intuit.com/v3/company/'

    @api.model
    def get_import_query_url(self, call_from=None):
        if not self:
            self = self.env.company

        if self.access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(self.access_token)
            headers['accept'] = 'application/json'
            headers['Content-Type'] = 'text/plain'
            if self.url:
                url = str(self.url) + str(self.realm_id)
                return {'url': url, 'headers': headers, 'minorversion': self.minorversion}
            else:
                if call_from == 'cron':
                    _logger.info('Url not configure')
                    log = self.env['qbo.logger'].create({
                        'odoo_name': 'Authantication',
                        'odoo_object': 'Res Company',
                        'message': "Url not configure",
                        'created_date': datetime.now(),
                    })
                    return False
                else:
                    raise ValidationError(_('Url not configure'))
        else:
            if call_from == 'cron':
                _logger.info('Invalid access token')
                log = self.env['qbo.logger'].create({
                    'odoo_name': 'Authantication',
                    'odoo_object': 'Res Company',
                    'message': "Invalid access token",
                    'created_date': datetime.now(),
                })
                return False
            else:
                raise ValidationError(_('Invalid access token'))

    @api.model
    def get_import_query_url_1(self):
        if self.access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(self.access_token)
            headers['accept'] = 'application/json'
            headers['Content-Type'] = 'application/json'
            if self.url:
                url = str(self.url) + str(self.realm_id)
            else:
                raise ValidationError(_('Url not configure'))
            return {'url': url, 'headers': headers, 'minorversion': self.minorversion}
        else:
            raise ValidationError(_('Invalid access token'))

    # @api.multi
    def import_customers(self, call_from=None, company=None):
        if not company:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                _("Company is not allowed for user. QBO ID: %s") % company.last_imported_customer_id)
        if not company:
            company = self.env.company
        _logger.info("Company is   :-> {} ".format(company))

        # try:
        if company.import_inactive_customer:  # Only import inactive customers
            query = f"select * from Customer WHERE Active = false order by Id STARTPOSITION {company.last_imported_customer_id} MAXRESULTS {company.limit}"
        else:
            if company.import_customer_by_date:
                if self.cutomer_import_by == 'crt_dt':
                    query = f"select * from Customer WHERE Metadata.CreateTime >= '{company.import_customer_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Customer WHERE Metadata.LastUpdatedTime >= '{company.import_customer_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from Customer order by Id STARTPOSITION {company.last_imported_customer_id} MAXRESULTS {company.limit}"
        if call_from == 'cron':
            url_str = company.get_import_query_url(call_from='cron')
        else:
            url_str = company.get_import_query_url()
        url = url_str.get('url') + '/query?%squery=%s' % (
            'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)

        try:
            data = requests.request(
                'GET', url, headers=url_str.get('headers'), verify=False)
        except Exception as e:
            raise ValidationError(
                _("Failed to make HTTP request for importing customers. QBO ID: %s. Error: %s") % (
                    company.last_imported_customer_id, str(e)))
        
        _logger.info("Customer data is ******111********* {}".format(data.text))

        if data.status_code == 200:
            _logger.info("Customer data is ------------> {}".format(data))
            try:
                res = json.loads(str(data.text))
            except Exception as e:
                raise ValidationError(
                    _("Failed to parse response JSON. QBO ID: %s. Error: %s") % (
                        company.last_imported_customer_id, str(e)))
            _logger.info(f"Customer data is 1111111------------> {res}")

            if self.import_mapping_customer_field and self.env.context.get('mapping'):
                if res.get('QueryResponse', False) and res.get('QueryResponse').get('Customer', []):
                    result = self.import_mapping_customer_id.with_context(
                        {'import': True, 'mapping_customer': True}).json_data = res.get('QueryResponse').get('Customer',[])
                else:
                    # Create log entry first
                    self.env['qbo.logger'].create({
                        'odoo_name': 'Authentication',
                        'odoo_object': 'Res Company',
                        'message': "Empty Data - No QueryResponse or Customer data found",
                        'created_date': datetime.now(),
                    })
                    # Then raise the error
                    raise UserError("Empty Data. QBO ID: %s" % company.last_imported_customer_id)
            else:
                try:
                    max_result = self.env['res.partner'].create_partner(data, is_customer=True, company=company)
                except Exception as e:
                    raise ValidationError(
                        _("Failed to create partner. QBO ID: %s. Error: %s") % (
                            company.last_imported_customer_id, str(e)))
                if max_result:
                    company.last_imported_customer_id = max_result + int(company.last_imported_customer_id)
                    success_form = self.env.ref(
                        'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
        else:
            if call_from == 'cron':
                _logger.info('Empty Data')
                log = self.env['qbo.logger'].create({
                    'odoo_name': 'Authantication',
                    'odoo_object': 'Res Company',
                    'message': "Empty Data",
                    'created_date': datetime.now(),
                })
            else:
                # raise UserError("Empty Data")
                # Create log entry first
                log_response = self.env['qbo.logger'].create({
                    'odoo_name': f"Customer Status Code: {data.status_code}",
                    'odoo_object': 'res.partner',
                    'activity': 'Import Customer',
                    'message': f"Response : {data.text}",
                    'created_date': datetime.now(),
                })
                # Commit the transaction so the log entry is saved before the exception
                self.env.cr.commit()  # Commit the current transaction
                # Then raise the error
                raise UserError("Empty Data. QBO ID: %s" % company.last_imported_customer_id)
                # This line won't be executed due to the error being raised
                _logger.warning(_('Empty data'))
        # except (UserError, ValidationError):
        #     raise
        # except Exception as final_err:
        #     raise ValidationError(
        #         _("Unhandled Exception while importing customers. QBO ID: %s. Error: %s") % (
        #             company.last_imported_customer_id, str(final_err)))

    def import_vendors(self, call_from=None, company=None):
        try:
            if not company:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)], limit=1).company_ids
                if not company in companys:
                    raise ValidationError(
                _("Company is not allowed for user. QBO ID: %s") % company.last_imported_vendor_id)
            if not company:
                company = self.env.company

            # Inactive vendor is imported
            if company.import_inactive_customer:  # Inactive vendor is imported
                _logger.info("Importing inactive vendors")
                query = f"select * from Vendor WHERE Active = false order by Id STARTPOSITION {company.last_imported_vendor_id} MAXRESULTS {company.limit}"
            else:
                if company.import_vendor_by_date:  # Handle vendor import by date
                    if self.vendor_import_by == 'crt_dt':
                        query = f"select * from Vendor WHERE Metadata.CreateTime >= '{company.import_vendor_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Vendor WHERE Metadata.LastUpdatedTime >= '{company.import_vendor_date}' order by Id MAXRESULTS {company.limit}"
                else:  # Default query
                    query = f"select * from Vendor order by Id STARTPOSITION {company.last_imported_vendor_id} MAXRESULTS {company.limit}"
            # if company.import_vendor_by_date:
            #     if self.vendor_import_by == 'crt_dt':
            #         query = "select * from vendor WHERE Metadata.CreateTime >= '%s' AND ID >= '%s' " % (
            #             company.import_vendor_date, company.last_imported_vendor_id)
            #     else:
            #         query = "select * from vendor WHERE Metadata.LastUpdatedTime >= '%s' AND ID >= '%s' " % (
            #             company.import_vendor_date, company.last_imported_vendor_id)
            # else:
            #     query = "select * from vendor WHERE Id > '%s' order by Id" % (company.last_imported_vendor_id)
            if call_from == 'cron':
                url_str = company.get_import_query_url(call_from='cron')
            else:
                url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            
            try:
                data = requests.request('GET', url, headers=url_str.get('headers'))
            except Exception as req_err:
                raise ValidationError(_("Failed to fetch vendor data from QBO. Error: %s") % str(req_err))
        
            if data.status_code == 200:
                _logger.info(
                    "Vendor data is ---------------> {}".format(data.text))
                # partner = self.env['res.partner'].create_vendor(data, is_vendor=True)
                res = json.loads(str(data.text))

                if self.import_mapping_vendor_field and self.env.context.get('mapping'):
                    if res.get('QueryResponse', False).get('Vendor', False):
                        self.import_mapping_vendor_id.with_context({'import': True}).json_data = res.get(
                            'QueryResponse').get('Vendor', [])
                    else:
                        raise UserError(_("Empty data returned from QBO Vendor query. Last Imported Vendor ID: %s") % company.last_imported_vendor_id)
                else:
                    try:
                        max_result = self.env['res.partner'].create_partner(data, is_vendor=True, company=company)
                    except Exception as create_err:
                        raise ValidationError(_("Failed to create vendor partner. Last Imported Vendor ID: %s. Error: %s") % (company.last_imported_vendor_id, str(create_err)))

                    if max_result:
                        self.last_imported_vendor_id = max_result + int(self.last_imported_vendor_id)
                        self._cr.commit()

                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
            else:
                if call_from == 'cron':
                    self.env['qbo.logger'].create({
                        'odoo_name': 'Empaty Data',
                        'odoo_object': 'Res Company',
                        'message': "Empty Data",
                        'created_date': datetime.now(),
                    })
                else:
                    raise UserError(_("Empty Data returned from QBO Vendor API. Last Imported Vendor ID: %s") % company.last_imported_vendor_id)
                
        except UserError as ue:
            if call_from == 'cron':
                _logger.exception("Unexpected error occurred while importing vendors.")
            else:
                raise ue
        except ValidationError as ve:
            if call_from == 'cron':
                _logger.exception("Unexpected error occurred while importing vendors.")
            else:
                raise ve
        except Exception as e:
            _logger.exception("Unexpected error occurred while importing vendors.")
            raise ValidationError(_("Unexpected error while importing vendors. Last Imported Vendor ID: %s. Error: %s") % (company.last_imported_vendor_id if company else 'Unknown', str(e)))

    def import_chart_of_accounts(self):
        try:
            company = self
            qbo_id = getattr(company, 'last_acc_imported_id', 'Unknown')

            try:
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(_(
                    "Company is not allowed for the user. Chart of Account QBO ID: %s") % qbo_id)
            except Exception as e:
                raise UserError(_("Failed to validate company access. Chart of Account QBO ID: %s. Reason: %s") % (qbo_id, str(e)))

            try:
                if self.import_account_by_date:
                    if self.account_import_by == 'crt_dt':
                        query = f"select * from Account WHERE Metadata.CreateTime >= '{self.import_account_date}' order by Id MAXRESULTS {self.limit}"
                    else:
                        query = f"select * from Account WHERE Metadata.LastUpdatedTime >= '{self.import_account_date}' order by Id MAXRESULTS {self.limit}"
                else:
                    query = f"select * from Account order by Id STARTPOSITION {self.last_acc_imported_id} MAXRESULTS {self.limit}"
            except Exception as e:
                raise UserError(_("Error creating query for Chart of Account QBO ID: %s. Reason: %s") % (qbo_id, str(e)))

            try:
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/query?query=' + query
                headers = url_str.get('headers')
            except Exception as e:
                raise UserError(_("Failed to get import URL or headers. Chart of Account QBO ID: %s. Reason: %s") % (qbo_id, str(e)))
            
            try:
                data = requests.request('GET', url, headers=headers)
                if data.status_code == 200:
                    _logger.info(
                        "Charts of accounts data is ----------------> {}".format(data.text))
                    if self.import_mapping_account_field and self.env.context.get('mapping'):
                        res = json.loads(str(data.text))
                        if res.get('QueryResponse', False).get('Account', False):
                            self.import_mapping_account_id.with_context({'import': True}).json_data = res.get(
                                'QueryResponse').get('Account', [])
                            return
                    max_result = self.env['account.account'].create_account_account(data, company)
                    if max_result:
                        self.last_acc_imported_id = max_result + int(
                            self.last_acc_imported_id)

                        self._cr.commit()
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                else:
                    _logger.warning(_('Empty data response from QuickBooks API'))
                    raise UserError(_("Empty Data returned from API. Chart of Account QBO ID: %s") % qbo_id)
            except (UserError, ValidationError):
                raise
            except Exception as e:
                raise UserError(_("Failed to process account data. Chart of Account QBO ID: %s. Reason: %s") % (qbo_id, str(e)))
        # ONLY catch truly unexpected errors here
        except ValidationError as ve:
            raise ve
        except UserError as ue:
            raise ue
        except Exception as final_exception:
            _logger.error("Exception occurred during chart of account import: %s", str(final_exception))
            raise UserError(_("An error occurred during Chart of Account import. Chart of Account QBO ID: %s. Reason: %s") %
                            (getattr(self, 'last_acc_imported_id', 'Unknown'), str(final_exception)))

    def error_message_from_quickbook(self, result, name, object_name):
        _logger.error(_("[%s] %s" % (result.status_code, result.text)))
        response = json.loads(result.text)

        if response.get('Fault'):
            if response.get('Fault').get('Error'):
                for message in response.get('Fault').get('Error'):
                    if message.get('Detail'):
                        self.env['qbo.logger'].create({
                            'odoo_name': name,
                            'odoo_object': object_name,
                            'message': 'Quickbooks Online Exception \n\n' + message.get('Detail'),
                            'created_date': datetime.now(),
                        })
                        raise UserError('Quickbooks Online Exception \n\n' + message.get('Detail'))

    def export_account_mapping(self):
        if self.last_account_mapping_export:
            account_ids = self.env['account.account'].search([
                ('write_date', '>=', self.last_account_mapping_export),
                ('qbo_acc_type', '!=', False),
                ('qbo_acc_subtype', '!=', False),
            ])
        else:
            account_ids = self.env['account.account'].search([
                ('qbo_id', '=', False),
                ('qbo_acc_type', '!=', False),
                ('qbo_acc_subtype', '!=', False),
            ])
        if self.export_mapping_account_field and self.export_mapping_account_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for account_id in account_ids:
                outdict = {}
                for fields_line_id in self.export_mapping_account_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(account_id, fields_line_id.col1.name)
                    if not attr:
                        attr = ''
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'selection' and fields_line_id.col1.name == 'qbo_acc_type':
                        values = account_id.qbo_acc_type.name
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(account_id, fields_line_id.col1.name)
                        attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                        values = attr or ''
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values

                if account_id.qbo_id:
                    res = requests.request(
                        'GET', url + "/account/{}?minorversion=75".format(account_id.qbo_id), headers=headers,
                        data=outdict)
                    synctoken = '0'
                    if res.status_code == 200:
                        response = res.json()  # self.convert_xmltodict(res.text)
                        _logger.info("RESPONSE IS ---> {}".format(response))
                        synctoken = response.get('Account').get(
                            'SyncToken')  # response.get('IntuitResponse').get('Account').get('SyncToken')
                    outdict.update({
                        'Id': account_id.qbo_id,
                        'SyncToken': synctoken
                    })
                parsed_dict = json.dumps(outdict)
                result = requests.request('POST', url + "/account?minorversion=75", headers=headers, data=parsed_dict)
                if result.status_code == 200:
                    response = result.json()  # self.convert_xmltodict(result.text)
                    qbo_id = int(response.get('Account').get('Id'))
                    account_id.qbo_id = qbo_id
                    _logger.info(
                        _("Account exported sucessfully! product template Id: %s" % (account_id.qbo_id)))
                    self._cr.commit()
                else:
                    self.error_message_from_quickbook(result, account_id.name, 'Account')

    def import_tax(self):
        try:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                _("Company is not allowed for user. [QBO Tax ID: %s]") % (company.last_imported_tax_id or 'Unknown'))
            
            if not company.country_id:
                raise UserError(
                _("Please set the country in the company! [QBO Tax ID: %s]") % (company.last_imported_tax_id or 'Unknown'))

            if company.import_tax_by_date:
                if company.account_import_by == 'crt_dt':
                    query = f"select * from TaxCode WHERE Metadata.CreateTime >= '{company.import_tax_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from TaxCode WHERE Metadata.LastUpdatedTime >= '{company.import_tax_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from TaxCode order by Id STARTPOSITION {company.last_imported_tax_id} MAXRESULTS {company.limit}"
                
            url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?query=' + query

            try:
                data = requests.request('GET', url, headers=url_str.get('headers'))
            except requests.RequestException as e:
                raise UserError(
                    _("Request failed while importing tax data. [QBO Tax ID: %s] Error: %s") %
                    (company.last_imported_tax_id or 'Unknown', str(e)))
            
            _logger.info("Tax data is ---------------> {}".format(data))

            if data.status_code == 200:
                try:
                    if self.import_mapping_tax_field and self.env.context.get('mapping'):
                        res = json.loads(str(data.text))
                        if res.get('QueryResponse', False) and res.get('QueryResponse').get('TaxCode', []):
                            self.import_mapping_tax_id.with_context({'import': True}).json_data = res.get(
                                'QueryResponse').get('TaxCode', [])
                    else:
                        max_result = self.env['account.tax'].create_account_tax(data, company)
                        if max_result:
                            company.last_imported_tax_id = max_result + int(
                                company.last_imported_tax_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                except (UserError, ValidationError):
                    raise
                except Exception as e:
                    raise UserError(
                        _("Failed while processing tax data. [QBO Tax ID: %s] Error: %s") %
                        (company.last_imported_tax_id or 'Unknown', str(e)))
            else:
                _logger.warning(_('Empty data'))
                raise UserError(_("Empty Data received. [QBO Tax ID: %s]") % (company.last_imported_tax_id or 'Unknown'))
        except ValidationError as ve:
            _logger.error("Validation error in import_tax: %s", str(ve))
            raise ve
        except UserError as ue:
            raise ue
        except Exception as e:
            _logger.exception("Unexpected error in import_tax")
            raise UserError(_("Unexpected error occurred during tax import. [QBO Tax ID: %s] Error: %s") %
                            (company.last_imported_tax_id or 'Unknown', str(e)))

    def export_tax_mapping(self):
        try:
            if self.last_tax_mapping_export:
                tax_ids = self.env['account.tax'].search([
                    ('write_date', '>=', self.last_tax_mapping_export),
                    ('amount_type', '!=', 'group'),
                ])
            else:
                tax_ids = self.env['account.tax'].search([
                    ('qbo_tax_rate_id', '=', False),
                    ('amount_type', '!=', 'group'),
                ])
            if self.export_mapping_tax_field and self.export_mapping_tax_id:
                url_str = self.get_import_query_url_1()
                url = url_str.get('url')
                headers = url_str.get('headers')
                for tax_id in tax_ids:
                    outdict = {}

                    for fields_line_id in self.export_mapping_tax_id.fields_lines:
                        split_key = fields_line_id.value.split('.')
                        attr = getattr(tax_id, fields_line_id.col1.name)
                        if not attr:
                            attr = ''
                        if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                            values = attr
                        elif fields_line_id.ttype == 'datetime':
                            values = fields.Datetime.to_string(attr)
                        elif fields_line_id.ttype == 'date':
                            values = fields.Date.to_string(attr)
                        elif fields_line_id.ttype in ['many2one']:
                            m2o_ref = getattr(tax_id, fields_line_id.col1.name)
                            attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                            values = attr or ''
                        elif fields_line_id.ttype in ['one2many', 'many2many']:
                            line_list = []
                            if attr:
                                for line in attr:
                                    qbo_id = getattr(line, 'qbo_tax_rate_id')

                                    if not qbo_id:
                                        line_val = {'TaxApplicableOn': 'Purchase'}
                                        if tax_id.type_tax_use == 'sale':
                                            outdict.update({'TaxApplicableOn': 'Sales'})
                                        for sub_field in fields_line_id.sub_field_object_id.sub_field_ids:
                                            sub_split_key = sub_field.qb_field.split('.')
                                            sub_attr = getattr(line, sub_field.field_id.name)
                                            if sub_field.ttype == 'many2one':
                                                sub_attr = getattr(sub_attr, sub_field.relation_field.name)
                                                value = sub_attr or ""
                                            else:
                                                value = sub_attr or ""
                                            if len(sub_split_key) == 1:
                                                line_val.update({sub_field.qb_field: value})
                                            elif len(sub_split_key) == 2:
                                                if sub_split_key[0] not in line_val:
                                                    line_val.update({sub_split_key[0]: {sub_split_key[1]: value}})
                                                else:
                                                    line_val[sub_split_key[0]].update({sub_split_key[1]: value})
                                            sub_attr = getattr(line, sub_field.field_id.name)
                                        line_list.append(line_val)
                                    else:
                                        line_list.append({'TaxRateId': qbo_id})
                            else:
                                line_val = {'TaxApplicableOn': 'Purchase'}
                                if tax_id.type_tax_use == 'sale':
                                    line_val.update({'TaxApplicableOn': 'Sales'})
                                for sub_field in fields_line_id.sub_field_object_id.sub_field_ids:
                                    if sub_field.qb_field == 'TaxApplicableOn':
                                        continue
                                    sub_split_key = sub_field.qb_field.split('.')
                                    sub_attr = getattr(tax_id, sub_field.field_id.name)
                                    if sub_field.ttype == 'many2one':
                                        sub_attr = getattr(sub_attr, sub_field.relation_field.name)
                                        value = sub_attr or ""
                                    else:
                                        value = sub_attr or ""
                                    if len(sub_split_key) == 1:
                                        line_val.update({sub_field.qb_field: value})
                                    elif len(sub_split_key) == 2:
                                        if sub_split_key[0] not in line_val:
                                            line_val.update({sub_split_key[0]: {sub_split_key[1]: value}})
                                        else:
                                            line_val[sub_split_key[0]].update({sub_split_key[1]: value})
                                line_list.append(line_val)
                            values = line_list
                        if len(split_key) > 1:
                            if split_key[0] not in outdict:
                                outdict[split_key[0]] = {split_key[1]: values}
                            else:
                                outdict[split_key[0]].update({split_key[1]: values})
                        else:
                            outdict[split_key[0]] = values
                    parsed_dict = json.dumps(outdict)

                    result = requests.request('POST', url + "/taxservice/taxcode", headers=headers, data=parsed_dict)
                    if result.status_code == 200:
                        response = result.json()
                        qbo_id = int(response.get('TaxCodeId'))
                        for i in response.get('TaxRateDetails'):
                            t_type = 'purchase'
                            if i.get('TaxApplicableOn') == 'Sales':
                                t_type = 'sale'
                            tax_rate = self.env['account.tax'].search([
                                ('name', '=', i.get('TaxRateName')),
                                ('type_tax_use', '=', t_type),
                                ('qbo_tax_rate_id', '=', False)], limit=1, order="id Desc")
                            if tax_rate:
                                tax_rate.qbo_tax_rate_id = i.get('TaxRateId')
                        tax_id.qbo_tax_rate_id = qbo_id
                        _logger.info(
                            _("Tax exported sucessfully! %s" % (qbo_id)))
                        self._cr.commit()
                        self.last_tax_mapping_export = fields.Datetime.now()
                    else:
                        self.error_message_from_quickbook(result, tax_id.name, 'Tax')
        except Exception as e:
            raise UserError(e)

    # @api.multi
    def import_tax_agency(self):
        try:
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
            #         self.ensure_one()
            query = "select * From TaxAgency WHERE Id > '%s' order by Id" % (
                company.last_imported_tax_agency_id)
            url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?query=' + query
            data = requests.request('GET', url, headers=url_str.get('headers'))
            _logger.info("Tax agency data is ---------------> {}".format(data))

            if data.status_code == 200:
                agency = self.env[
                    'account.tax.agency'].create_account_tax_agency(data)
                if agency:
                    self.last_imported_tax_agency_id = agency.qbo_agency_id
                    success_form = self.env.ref(
                        'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
            else:
                raise UserError("Empty data")
                _logger.warning(_('Empty data'))
        except Exception as e:
            raise UserError(e)

    # @api.multi
    def import_product_category(self):
        #         self.ensure_one()
        try:
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
            if company.import_pc_by_date:
                if self.prodct_catgry_import_by == 'crt_dt':
                    query = f"select * from Item WHERE Type='Category' AND Metadata.CreateTime >= '{company.import_pc_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Item WHERE Type='Category' AND Metadata.LastUpdatedTime >= '{company.import_pc_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from Item WHERE Type='Category' order by Id STARTPOSITION {company.last_imported_product_category_id} MAXRESULTS {company.limit}"
                
            url_str = company.get_import_query_url()
            if not url_str or not url_str.get('url') or not url_str.get('headers'):
                raise ValidationError("Missing URL or headers for QuickBooks query.")
        
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            
            try:
                data = requests.request('GET', url, headers=url_str.get('headers'))
            except Exception as request_err:
                raise ValidationError(f"Request to QuickBooks API failed: {str(request_err)}")
            
            _logger.info(
                "Product category  data is ---------------> {}".format(data))
            
            if data.status_code == 200:
                if self.import_mapping_product_category_field and self.env.context.get('mapping'):

                    try:
                        res = json.loads(str(data.text))
                    except json.JSONDecodeError as json_err:
                        raise ValidationError(f"Failed to parse JSON from QuickBooks response: {str(json_err)}")
        
                    if 'QueryResponse' in res:
                        categories = res.get('QueryResponse').get('Item', [])
                    else:
                        categories = [res.get('Item')] or []
                    if categories:
                        self.import_mapping_product_category_id.with_context({'import': True}).json_data = categories
                else:
                    max_result = self.env['product.category'].create_product_category(data)
                    if max_result:
                        company.last_imported_product_category_id = max_result + int(
                            company.last_imported_product_category_id)
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                    else:
                        raise ValidationError(f"All Categories are already imported.")
            else:
                _logger.warning(_('Empty data'))
                raise ValidationError("Empty response received from QuickBooks API.")
        # ONLY catch truly unexpected errors here
        except ValidationError as ve:
            # Let ValidationError show its actual message (user-friendly)
            raise ve
        except Exception as e:
            # Unexpected, log + show generic
            raise UserError(
                _("An error occurred while importing product categories.\nLast QBO ID: %s\nDetails: %s")
                % (company.last_imported_product_category_id if company else 'Unknown', str(e)))
    def export_product_category_mapping(self):
        if self.last_product_category_mapping_export:
            product_category_ids = self.env['product.category'].search([
                ('write_date', '>=', self.last_product_category_mapping_export),
            ])
        else:
            product_category_ids = self.env['product.category'].search([
                ('qbo_product_category_id', '=', False),
            ])
        if self.export_mapping_product_category_field and self.export_mapping_product_category_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for product_category_id in product_category_ids:
                outdict = {
                    "Type": "Category",
                    "Name": product_category_id.name,
                }

                for fields_line_id in self.export_mapping_product_category_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(product_category_id, fields_line_id.col1.name)
                    if not attr:
                        continue
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(product_category_id, fields_line_id.col1.name)
                        attr = ''
                        if m2o_ref:
                            attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                            if attr:
                                outdict.update({"SubItem": True})
                        values = attr or ''
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                parsed_dict = json.dumps(outdict)

                if product_category_id.qbo_product_category_id:
                    res = requests.request('GET', url + "/item/{}?minorversion=75".format(
                        product_category_id.qbo_product_category_id), headers=headers, data=parsed_dict)
                    synctoken = '0'
                    if res.status_code == 200:
                        response = res.json()
                        _logger.info("RESPONSE IS ---> {}".format(response))
                        synctoken = response.get('Item').get('SyncToken')
                    outdict.update({
                        'Id': product_category_id.qbo_product_category_id,
                        'SyncToken': synctoken
                    })
                parsed_dict = json.dumps(outdict)
                result = requests.request('POST',
                                          url + "/item?operation=update&minorversion=75",
                                          headers=headers,
                                          data=parsed_dict)
                if result.status_code == 200:
                    response = result.json()
                    qbo_id = int(response.get('Item').get('Id'))
                    product_category_id.qbo_product_category_id = qbo_id
                    self.last_product_category_mapping_export = datetime.now()
                    _logger.info(
                        _("Product exported sucessfully! product template Id: %s" % (
                            product_category_id.qbo_product_category_id)))
                    self._cr.commit()
                else:
                    self.error_message_from_quickbook(result, product_category_id.name, 'Product Category')

    # @api.multi
    def import_product(self, call_from=None, company=None):
        try:
            if not call_from:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                    _(f"Company '{company.name}' (QBO ID: {company.last_imported_product_id}) is not allowed for user"))
            else:
                if not company:
                    company = self
            if not company:
                company = self.env.company
            # if company.import_inactive_product:
            #     start_position = 1
            #     max_results = 100
            #     while True:
            #         query = f"select * from Item where Active = false startPosition {start_position} maxResults {max_results}"
            #         url_str = company.get_import_query_url()
            #         url = url_str.get('url') + '/query?%squery=%s' % (
            #             'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '',
            #             query)
            #         data = requests.request('GET', url, headers=url_str.get('headers'))
            #         _logger.info(
            #             "Product Data is --------------------> {}".format(data))
            #         if data.status_code != 200:
            #             _logger.info(f"Error: {data.status_code}, {data.text}")
            #             break
            #         product = self.env['product.template'].create_product(data, company=company)
            #         data = data.json()
            #         # Extract items from the response
            #         items = data.get('QueryResponse', {}).get('Item', [])
            #         # Check if we have reached the end of the list
            #         if len(items) < max_results:
            #             break
            #         # Move to the next page
            #         start_position += max_results
            if company.import_product_by_date:
                if company.prodct_import_by == 'crt_dt':
                    query = f"select * from Item WHERE Metadata.CreateTime >= '{company.import_product_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Item WHERE Metadata.LastUpdatedTime >= '{company.import_product_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from Item order by Id STARTPOSITION {company.last_imported_product_id} MAXRESULTS {company.limit}"
                
            url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            data = requests.request('GET', url, headers=url_str.get('headers'))
            _logger.info(
                "Product Data is --------------------> {}".format(data))
            if data.status_code == 200:
                if self.import_mapping_product_field and self.env.context.get('mapping'):
                    try:
                        res = json.loads(str(data.text))
                        if 'QueryResponse' in res:
                            product = res.get('QueryResponse').get('Item', [])
                        else:
                            product = [res.get('Item')] or []
                        if product:
                            self.import_mapping_product_id.with_context({'import': True}).json_data = product
                    except Exception as map_exc:
                            raise ValidationError(f"Mapping Error in QBO product import: {map_exc}")
                else:
                    try:
                        if call_from:
                            max_result = self.env['product.template'].create_product(data, call_from='cron',
                                                                                     company=company)
                        else:
                            max_result = self.env['product.template'].create_product(data, company=company)
                        if max_result:
                            company.last_imported_product_id = max_result + int(company.last_imported_product_id)
                            success_form = self.env.ref('pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                        else:
                            raise UserError("It seems that all of the Products are already imported.")
                    except (UserError, ValidationError):
                        raise  # re-raise known Odoo errors without modification

                    except Exception as create_exc:
                        raise ValidationError(f"Product creation failed from QBO data: {create_exc}")
            else:
                if call_from == 'cron':
                    log = self.env['qbo.logger'].create({
                        'odoo_name': 'PRODUCT',
                        'odoo_object': 'Product',
                        'message': "Empty data",
                        'created_date': datetime.now(),
                    })
                else:
                    raise UserError("Empty data")
                    _logger.warning(_('Empty data in product!!!!!'))
        except UserError as ue:
            if call_from == 'cron':
                _logger.exception("Unhandled exception in import_product: %s" % str(ue))
            else:
                raise ue
        except ValidationError as ve:
            if call_from == 'cron':
                _logger.exception("Unhandled exception in import_product: %s" % str(ve))
            else:
                raise ve
        except Exception as e:
            _logger.exception("Unhandled exception in import_product: %s" % str(e))
            raise UserError(f"An unexpected error occurred during product import: {str(e)}")

    def inactive_product_import(self, call_from=None, company=None):
        try:
            if not call_from:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user"))
            else:
                if not company:
                    company = self
            if not company:
                company = self.env.company
            if company.import_inactive_product:
                start_position = 1
                max_results = 100
                while True:
                    query = f"select * from Item where Active = false startPosition {start_position} maxResults {max_results}"
                    url_str = company.get_import_query_url()
                    url = url_str.get('url') + '/query?%squery=%s' % (
                        'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '',
                        query)
                    data = requests.request('GET', url, headers=url_str.get('headers'))
                    _logger.info(
                        "Product Data is --------------------> {}".format(data))
                    if data.status_code != 200:
                        _logger.info(f"Error: {data.status_code}, {data.text}")
                        break
                    product = self.env['product.template'].create_product(data, company=company)
                    data = data.json()
                    # Extract items from the response
                    items = data.get('QueryResponse', {}).get('Item', [])
                    # Check if we have reached the end of the list
                    if len(items) < max_results:
                        break
                    # Move to the next page
                    start_position += max_results
        except Exception as e:
            raise UserError(e)

    def export_product_mapping(self):
        if self.last_product_mapping_export:
            product_ids = self.env['product.product'].search([
                ('write_date', '>=', self.last_product_mapping_export),
                # ('qbo_product_id', '=', False),
            ])
        else:
            product_ids = self.env['product.product'].search([
                ('qbo_product_id', '=', False),
            ])
        if self.export_mapping_product_field and self.export_mapping_product_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for product_id in product_ids:
                outdict = {
                    "InvStartDate": str(date.today()),
                    'TrackQtyOnHand': False,
                    'QtyOnHand': product_id.qty_available,
                    'SubItem': True,
                    'ParentRef': {
                        'value': product_id.categ_id.qbo_product_category_id
                    },
                    'AssetAccountRef': {
                        'value': product_id.categ_id.property_stock_valuation_account_id.qbo_id
                    }

                }

                #
                if product_id.type == 'consu' and product_id.is_storable:
                    outdict.update({'TrackQtyOnHand': True})
                for fields_line_id in self.export_mapping_product_id.fields_lines:

                    split_key = fields_line_id.value.split('.')

                    # Initialize attr with a default value
                    attr = None

                    # Safely get the attribute, with a default of None if not found
                    attr = getattr(product_id, fields_line_id.col1.name, None)

                    # Initialize values with a default
                    values = attr if attr is not None else ''

                    # attr = getattr(product_id, fields_line_id.col1.name)
                    if not attr:
                        attr = ''
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'selection' and fields_line_id.value == 'Type':
                        values = 'Inventory'
                        if product_id.type == "consu":
                            values = 'NonInventory'
                        elif product_id.type == "service":
                            values = 'Service'
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(product_id, fields_line_id.col1.name)
                        attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                        values = attr or ''
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                if product_id.qbo_product_id:
                    outdict.update({
                        'SyncToken': product_id.product_tmpl_id.getSyncToken(product_id.qbo_product_id),
                        'Id': product_id.qbo_product_id,
                    })
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(self.access_token)
                headers['Content-Type'] = 'application/json'
                parsed_dict = json.dumps(outdict)

                result = requests.request('POST', url + "/item?operation=update&minorversion=75", headers=headers,
                                          data=parsed_dict)
                if result.status_code == 200:
                    response = self.convert_xmltodict(result.text)
                    qbo_id = int(response.get('IntuitResponse').get('Item').get('Id'))
                    product_id.qbo_product_id = qbo_id
                    self.last_product_mapping_export = datetime.now()
                    _logger.info(
                        _("Product exported sucessfully! product template Id: %s" % (product_id.qbo_product_id)))
                    self._cr.commit()
                else:
                    self.error_message_from_quickbook(result, product_id.name, 'Product')

    # @api.multi
    def import_inventory(self):  # @api.multi
        company = self
        companys = self.env['res.users'].search([('id', '=', self._uid)]).company_ids
        if not company in companys:
            raise ValidationError(_("Company is not allowed for user"))
        _logger.info("COMPANY CATEGORY IS-------------> {} ".format(company))
        try:
            last_inv_id = company.last_imported_inv_product_id if company.last_imported_inv_product_id else 0
            query = f"select * from Item order by Id STARTPOSITION {last_inv_id} MAXRESULTS {company.limit}"
            url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            data = requests.request('GET', url, headers=url_str.get('headers'))
            if data.status_code == 200:
                parsed_data = data.json()
                _logger.info("Inventory data is -----------------> {}".format(parsed_data))
                if parsed_data.get("QueryResponse"):
                    inventory_updated = False
                    for recs in parsed_data.get("QueryResponse").get('Item'):
                        _logger.info("ID IS  ---> {}".format(recs.get('Id')))
                        product_exists = self.env['product.product'].search(
                            [('qbo_product_id', '=', recs.get('Id')), ('company_id', '=', company.id)])
                        _logger.info("Product exists -----------> {}".format(product_exists))
                        if product_exists and product_exists.type == 'consu' and product_exists.is_storable:
                            if product_exists.qty_available != recs.get('QtyOnHand') and recs.get('QtyOnHand') >= 0:
                                location_id = self.env['stock.warehouse'].search(
                                    [('company_id', '=', company.id)], limit=1
                                ).lot_stock_id
                                self.env['stock.quant'].create({
                                    'location_id': location_id.id,
                                    'product_id': product_exists.id,
                                    'inventory_quantity': recs.get('QtyOnHand')
                                }).action_apply_inventory()
                            inventory_updated = True
                    if inventory_updated:
                        max_result = parsed_data.get('QueryResponse').get('maxResults')
                        company.last_imported_inv_product_id = max_result + int(company.last_imported_inv_product_id)
                        success_form = self.env.ref('pragmatic_quickbooks_connector_canada.import_successfull_view', False)
                        return {'name': _('Notification'),
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'res.company.message',
                                'views': [(success_form.id, 'form')],
                                'view_id': success_form.id,
                                'target': 'new', }
                    else:
                        raise UserError(_("It seems that all of the Inventory are already imported."))
                else:
                    raise UserError(_("It seems that all of the Inventory are already imported."))
        except Exception as e:
            raise ValidationError(_('Inventory Update Failed due to %s' % str(e)))

    def import_payment_method(self):
        try:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user"))
            if company.import_payment_method_by_date:
                if self.paymnt_method_import_by == 'crt_dt':
                    query = f"select * from PaymentMethod WHERE Metadata.CreateTime >= '{company.import_payment_method_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from PaymentMethod WHERE Metadata.LastUpdatedTime >= '{company.import_payment_method_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from PaymentMethod order by Id STARTPOSITION {company.last_imported_payment_method_id} MAXRESULTS {company.limit}"

            url_str = self.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            data = requests.request('GET', url, headers=url_str.get('headers'))
            _logger.info(
                "\n\n\n\n\nPayment method data is ---------------> {}".format(data.text))
            if data.status_code == 200:
                max_result = self.env['account.journal'].create_payment_method(data, company=company)
                if max_result:
                    company.last_imported_payment_method_id = max_result + int(company.last_imported_payment_method_id)

                    success_form = self.env.ref(
                        'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
            else:
                _logger.warning(_('Empty data'))
                raise UserError("Empty data")
        except Exception as e:
            raise UserError(e)

    def import_payment(self, company=None):
        try:
            if not company:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(_("Company is not allowed for user (Company ID: {})").format(company.id))
            if not company:
                company = self.env['res.company'].search([('id', '=', 1)], limit=1)
            if company.import_cp_by_date:
                if company.customer_paymnt_import_by == 'crt_dt':
                    query = f"select * from Payment WHERE Metadata.CreateTime >= '{company.import_cp_date}' order by Id MAXRESULTS {company.limit}"
                elif company.customer_paymnt_import_by == 'other_dt':
                    query = f"select * from Payment WHERE TxnDate >= '{company.import_cp_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Payment WHERE Metadata.LastUpdatedTime >= '{company.import_cp_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from Payment order by Id STARTPOSITION {company.last_imported_payment_id} MAXRESULTS {company.limit}"
            url_str = self.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            data = requests.request('GET', url, headers=url_str.get('headers'))
            _logger.info(
                "Payment data is ---------------> {}".format(data.text))

            if data.status_code == 200:
                _logger.info(
                    "Data for importing customer payments in odoo is ---> {}".format(data.text))
                # try:
                if self.import_mapping_cust_payment_id and self.env.context.get('mapping'):
                    res = json.loads(str(data.text))
                    if res.get('QueryResponse', False) and res.get('QueryResponse').get('Payment', []):
                        self.import_mapping_cust_payment_id.with_context({'import': True}).json_data = res.get(
                            'QueryResponse').get('Payment', [])
                else:
                    max_result = self.env['account.payment'].create_payment(data, is_customer=True,
                                                                            company=company)
                    if max_result:
                        company.last_imported_payment_id = max_result + int(
                            company.last_imported_payment_id)
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                # except Exception as mapping_error:
                #     raise ValidationError(_("Failed to process payment data mapping. Error: %s. [QBO Payment ID: %s]") %
                #                         (str(mapping_error), company.last_imported_payment_id or "Unknown"))
            else:
                _logger.warning(_('Empty data'))
                raise ValidationError(_("Empty response received from QBO. [QBO Payment ID: %s]") %
                                  (company.last_imported_payment_id or "Unknown"))
        except ValidationError as ve:
            raise ve
        except UserError as ue:
            raise ue
        except Exception as e:
            raise ValidationError(_("Unexpected error occurred while importing payment. Error: %s [QBO Payment ID: %s]") %
                                (str(e), company.last_imported_payment_id if company else "Unknown"))

    # @api.multi
    def import_bill_payment(self, cron=None):
        try:
            if not cron:
                # try:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user (QBO ID: %s)") % (company.last_imported_bill_payment_id or 'Unknown'))
                # except Exception as e:
                #     raise ValidationError(_("Company validation failed for QBO ID: %s. Error: %s") % (self.last_imported_bill_payment_id or 'Unknown', str(e)))
            else:
                company = self

            # try:
            if company.import_vp_by_date:
                if company.vendor_paymnt_import_by == 'crt_dt':
                    query = f"select * from BillPayment WHERE Metadata.CreateTime >= '{company.import_vp_date}' order by Id MAXRESULTS {company.limit}"
                elif company.vendor_paymnt_import_by == 'other_dt':
                    query = f"select * from BillPayment WHERE TxnDate >= '{company.import_vp_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from BillPayment WHERE Metadata.LastUpdatedTime >= '{company.import_vp_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from BillPayment order by Id STARTPOSITION {company.last_imported_bill_payment_id} MAXRESULTS {company.limit}"
            # except Exception as e:
            #     raise ValidationError(_("Query formation failed for QBO ID: %s. Error: %s") % (company.last_imported_bill_payment_id or 'Unknown', str(e)))
        
            # try:
            url_str = company.get_import_query_url()
            url = url_str.get('url') + '/query?%squery=%s' % (
                'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
            data = requests.request('GET', url, headers=url_str.get('headers'))
            _logger.info(
                " Bill payment data is -----------------> {}".format(data.text))
            # except Exception as e:
            #     raise ValidationError(_("Request to QuickBooks failed for QBO ID: %s. Error: %s") % (company.last_imported_bill_payment_id or 'Unknown', str(e)))
        
            if data.status_code == 200:
                # try:
                if self.import_mapping_vendor_payment_id and self.env.context.get('mapping'):
                    res = json.loads(str(data.text))
                    if res.get('QueryResponse', False) and res.get('QueryResponse').get('BillPayment', []):
                        self.import_mapping_vendor_payment_id.with_context({'import': True}).json_data = res.get(
                            'QueryResponse').get('BillPayment', [])
                else:
                    max_result = self.env['account.payment'].create_payment(data, is_vendor=True, company=company)
                    if max_result:
                        company.last_imported_bill_payment_id = max_result + int(
                            company.last_imported_bill_payment_id)
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                # except Exception as e:
                #     raise ValidationError(_("Processing response failed for QBO ID: %s. Error: %s") % (company.last_imported_bill_payment_id or 'Unknown', str(e)))
            else:
                _logger.warning(_('Empty data'))
                raise UserError(_("Empty data returned for QBO ID: %s") % (company.last_imported_bill_payment_id or 'Unknown'))
        except ValidationError as ve:
            raise ve
        except UserError as ue:
            raise ue
        except Exception as e:
            raise UserError(_("Unexpected error for QBO ID: %s. Error: %s") % (self.last_imported_bill_payment_id or 'Unknown', str(e)))

    def import_payment_term_from_quickbooks(self):
        company = self
        companys = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_ids
        if not company in companys:
            raise ValidationError(
                _("Company is not allowed for user"))

        payment_term = self.env['account.payment.term']
        payment_term_line = self.env['account.payment.term.line']

        if company.access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(self.access_token)
            headers['Accept'] = 'application/json'
            headers['Content-Type'] = 'text/plain'
            if company.import_payment_term_by_date:
                if company.paymnt_term_import_by == 'crt_dt':
                    data = requests.request(
                        'GET',
                        company.url + str(company.realm_id) +
                        f"/query?query=select * from Term WHERE Metadata.CreateTime >= '{company.import_payment_term_date}' order by Id MAXRESULTS {company.limit}",
                        headers=headers
                    )
                else:
                    data = requests.request(
                        'GET',
                        company.url + str(company.realm_id) +
                        f"/query?query=select * from Term WHERE Metadata.LastUpdatedTime >= '{company.import_payment_term_date}' order by Id MAXRESULTS {company.limit}",
                        headers=headers
                    )
            else:
                data = requests.request(
                    'GET',
                    company.url + str(company.realm_id) +
                    f"/query?query=select * from Term order by Id STARTPOSITION {company.x_quickbooks_last_paymentterm_imported_id} MAXRESULTS {company.limit}",
                    headers=headers
                )
            if data.status_code == 200:
                ''' Holds quickbookIds which are inserted '''
                recs = []
                parsed_data = json.loads(str(data.text))
                if parsed_data:
                    _logger.info(
                        "Payment term from qbo data is ---------------> {}".format(parsed_data))
                    if self.import_mapping_product_category_field and self.env.context.get('mapping'):
                        res = json.loads(str(data.text))
                        self.import_mapping_payment_term_id.with_context({'import': True}).json_data = res.get(
                            'QueryResponse').get('Term', [])
                    else:
                        if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Term'):
                            for term in parsed_data.get('QueryResponse', False).get('Term', False):
                                vals = {}
                                dict_ptl = {}
                                exists = payment_term.search(
                                    [('name', '=', term.get('Name')), ('company_id', '=', company.id)], limit=1)
                                if not exists:
                                    ''' Loop and create Data '''
                                    vals['company_id'] = company.id
                                    if term.get('Active'):
                                        vals['active'] = term.get('Active')
                                    if term.get('Name'):
                                        vals['note'] = term.get('Name')
                                        vals['name'] = term.get('Name')
                                    if term.get('DiscountPercent') and term.get('DiscountDays'):
                                        vals['early_discount'] = True
                                        vals['discount_percentage'] = term.get('DiscountPercent')
                                        vals['discount_days'] = term.get('DiscountDays')

                                    '''  Insert data in account payment term line and attach its id to payment term create'''
                                    #                                 if term.get('DueDays'):
                                    #                                     dict_ptl['value'] = 'balance'
                                    #                                     dict_ptl['days'] = term.get('DueDays')

                                    vals.update(
                                        {'line_ids': [(0, 0, {'value': 'percent', 'nb_days': term.get('DueDays')})]})
                                    payment_term_create = payment_term.create(vals)
                                    if payment_term_create:
                                        payment_term_create.x_quickbooks_id = term.get(
                                            'Id')
                                        recs.append(term.get('Id'))
                                        #                                     self.x_quickbooks_last_paymentterm_imported_id = term.get('Id')
                                        company.x_quickbooks_last_paymentterm_sync = datetime.now()
                                        # company.x_quickbooks_last_paymentterm_sync = fields.datetime.now()

                                        #                                     dict_ptl['payment_id'] = payment_term_create.id
                                        #                                     payment_term_line_create = payment_term_line.create(dict_ptl)
                                        # if payment_term_line_create:
                                        # company.x_quickbooks_last_paymentterm_imported_id = max(
                                        #     recs)
                                        if company.import_payment_term_by_date:
                                            date_format = '%Y-%m-%d'
                                            if company.paymnt_term_import_by == 'crt_dt':
                                                date_string = term.get('MetaData').get(
                                                    'CreateTime')[:10]
                                            else:
                                                date_string = term.get('MetaData').get(
                                                    'LastUpdatedTime')[:10]

                                            date_object = datetime.strptime(date_string,
                                                                            date_format).date()
                                            company.import_payment_term_date = date_object
                                        _logger.info(
                                            _("Payment term line was created %s" % payment_term_create.line_ids.ids))

                                else:
                                    recs.append(term.get('Id'))
                                    _logger.info(
                                        _("REC Exists %s" % term.get('Name')))
                                    if not exists.x_quickbooks_id:
                                        exists.x_quickbooks_id = term.get(
                                            'Id')
                                    recs.append(term.get('Id'))
                                _logger.info(
                                    "Records are -----------> {}".format(recs))
                                if recs:
                                    if company.import_payment_term_by_date:
                                        date_format = '%Y-%m-%d'
                                        if company.paymnt_term_import_by == 'crt_dt':
                                            date_string = term.get('MetaData').get(
                                                'CreateTime')[:10]
                                        else:
                                            date_string = term.get('MetaData').get(
                                                'LastUpdatedTime')[:10]

                                        date_object = datetime.strptime(date_string,
                                                                        date_format).date()
                                        company.import_payment_term_date = date_object
                            max_result = parsed_data.get('QueryResponse').get('maxResults')

                            company.x_quickbooks_last_paymentterm_imported_id = max_result + int(
                                company.x_quickbooks_last_paymentterm_imported_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                        else:
                            raise UserError(
                                "It seems that all of the Payment Trems are already imported.")
                else:
                    raise UserError(
                        "It seems that all of the Payment Trems are already imported.")

    # function called when clicked on sync employee button
    # @api.multi
    def import_employee(self):
        try:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user"))

            if company.access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + company.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'

                '''ALL EMPLOYEES WITH ALL THE INFO'''
                if company.import_employee_by_date:  # ALL EMPLOYEES WITH ALL THE INFO
                    if self.employee_import_by == 'crt_dt':
                        query = f"select * from Employee WHERE Metadata.CreateTime > '{company.import_employee_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Employee WHERE Metadata.LastUpdatedTime > '{company.import_employee_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Employee order by Id STARTPOSITION {company.quickbooks_last_employee_imported_id} MAXRESULTS {company.limit}"
                data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                        headers=headers)
                if data.status_code == 200:
                    recs = []
                    parsed_data = json.loads(str(data.text))
                    if parsed_data:
                        _logger.info(
                            "Employee data  is ------------------->{}".format(parsed_data))

                        if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Employee'):
                            for emp in parsed_data.get('QueryResponse').get('Employee'):

                                # ''' This will avoid duplications'''
                                hr_employee = self.env['hr.employee'].search(
                                    ['|', ('quickbook_id', '=', emp.get('Id')), ('name', '=', emp.get('DisplayName')),
                                     ('company_id', '=', company.id)], limit=1)

                                dict_e = {}

                                if emp.get('DisplayName'):
                                    dict_e['name'] = emp.get('DisplayName')

                                if emp.get('PrimaryPhone'):
                                    dict_e['mobile_phone'] = emp.get(
                                        'PrimaryPhone').get('FreeFormNumber')

                                if emp.get('PrimaryEmailAddr'):
                                    dict_e['work_email'] = emp.get(
                                        'PrimaryEmailAddr').get('Address', ' ')

                                if emp.get('Id'):
                                    dict_e['quickbook_id'] = emp.get('Id')
                                    dict_e['company_id'] = company.id

                                if emp.get('Mobile'):
                                    dict_e['work_phone'] = emp.get(
                                        'Mobile').get('FreeFormNumber')

                                if emp.get('EmployeeNumber'):
                                    dict_e['employee_no'] = emp.get(
                                        'EmployeeNumber')

                                if emp.get('BirthDate'):
                                    dict_e['birthday'] = emp.get('BirthDate')

                                if emp.get('Gender'):
                                    if emp.get('Gender') == 'Female':
                                        dict_e['gender'] = 'female'
                                    if emp.get('Gender') == 'Male':
                                        dict_e['gender'] = 'male'
                                    if emp.get('Gender') == 'Other':
                                        dict_e['gender'] = 'other'

                                if emp.get('Notes'):
                                    dict_e['notes'] = emp.get('Notes')

                                if emp.get('HiredDate'):
                                    dict_e['hired_date'] = emp.get('HiredDate')

                                if emp.get('ReleasedDate'):
                                    dict_e['released_date'] = emp.get(
                                        'ReleasedDate')

                                if emp.get('BillRate'):
                                    dict_e['billing_rate'] = emp.get(
                                        'BillRate')

                                if emp.get('SSN'):
                                    dict_e['ssn'] = emp.get('SSN')

                                if not hr_employee:

                                    '''If employee is not present we create it'''

                                    employee_create = hr_employee.create(
                                        dict_e)

                                    if employee_create:
                                        _logger.info(
                                            'Employee Created Sucessfully..!!')

                                        recs.append(employee_create.id)
                                        if emp.get('PrimaryAddr'):

                                            dict_c = {}

                                            if emp.get('PrimaryAddr').get('CountrySubDivisionCode'):

                                                state_id = self.State(
                                                    emp.get('PrimaryAddr').get(
                                                        'CountrySubDivisionCode'),
                                                    emp.get('PrimaryAddr').get('Country'))
                                                if state_id:
                                                    dict_c[
                                                        'state_id'] = state_id
                                            country_id = self.env['res.country'].search([
                                                ('code', '=', emp.get('PrimaryAddr').get('CountrySubDivisionCode'))],
                                                limit=1)
                                            if country_id:
                                                dict_c[
                                                    'country_id'] = country_id.id
                                            if emp.get('DisplayName'):
                                                dict_c['name'] = emp.get(
                                                    'DisplayName')
                                            if emp.get('PrimaryAddr').get('Id'):
                                                dict_c['qbo_customer_id'] = emp.get(
                                                    'PrimaryAddr').get('Id')

                                            if emp.get('PrimaryAddr').get('PostalCode', ' '):
                                                dict_c['zip'] = emp.get(
                                                    'PrimaryAddr').get('PostalCode', ' ')
                                            if emp.get('PrimaryAddr').get('City'):
                                                dict_c['city'] = emp.get(
                                                    'PrimaryAddr').get('City')

                                            if emp.get('PrimaryAddr').get('Line1'):
                                                dict_c['street'] = emp.get(
                                                    'PrimaryAddr').get('Line1')

                                            if emp.get('PrimaryAddr'):
                                                check_id = emp.get(
                                                    'PrimaryAddr').get('Id')

                                                cust_obj = self.env['res.partner'].search(
                                                    [['qbo_customer_id', 'ilike', check_id],
                                                     ['company_id', '=', company.id]])

                                                if cust_obj:
                                                    for cust_id in cust_obj:
                                                        cust_id.write(dict_c)
                                                        '''CREATING NEW EMP'S EXISTING ADDRESS'''

                                                        employee_obj = self.env['hr.employee'].search(
                                                            [['quickbook_id', '=', emp.get('Id')]])
                                                        _logger.info(
                                                            "Employee object is --------------------> {}".format(
                                                                employee_obj))
                                                        if employee_obj:
                                                            # for check in
                                                            # employee_obj:
                                                            res = employee_obj.update({

                                                                'address_id': cust_id.id
                                                            })
                                                else:
                                                    '''CREATING NEW EMP'S NEW ADDRESS'''

                                                    address_create = self.env[
                                                        'res.partner'].create(dict_c)
                                                    # for addr_create in
                                                    # address_create:
                                                    dict_c[
                                                        'address_id'] = address_create.id

                                            # self.quickbooks_last_employee_sync = fields.Datetime.now()
                                            # company.quickbooks_last_employee_imported_id = int(
                                            #     emp.get('Id'))
                                            if self.import_employee_by_date:
                                                date_format = '%Y-%m-%d'
                                                if self.employee_import_by == 'crt_dt':
                                                    date_string = emp.get('MetaData').get(
                                                        'CreateTime')[:10]
                                                else:
                                                    date_string = emp.get('MetaData').get(
                                                        'LastUpdatedTime')[:10]

                                                date_object = datetime.strptime(date_string,
                                                                                date_format).date()
                                                self.import_employee_date = date_object


                                else:
                                    if 'PrimaryAddr' in emp and emp.get('PrimaryAddr'):
                                        dict_c = {}

                                        if emp.get('PrimaryAddr').get('CountrySubDivisionCode'):

                                            state_id = self.State(
                                                emp.get('PrimaryAddr').get(
                                                    'CountrySubDivisionCode'),
                                                emp.get('PrimaryAddr').get('Country'))
                                            if state_id:
                                                dict_c['state_id'] = state_id
                                        country_id = self.env['res.country'].search([
                                            ('code', '=', emp.get('PrimaryAddr').get('CountrySubDivisionCode'))],
                                            limit=1)
                                        if country_id:
                                            dict_c[
                                                'country_id'] = country_id.id
                                        # dict['parent_id'] = create.id

                                        if emp.get('DisplayName'):
                                            dict_c['name'] = emp.get(
                                                'DisplayName')
                                        if emp.get('PrimaryAddr').get('Id'):
                                            dict_c['qbo_customer_id'] = emp.get(
                                                'PrimaryAddr').get('Id')
                                        if emp.get('PrimaryAddr').get('PostalCode', ' '):
                                            dict_c['zip'] = emp.get(
                                                'PrimaryAddr').get('PostalCode', ' ')
                                        if emp.get('PrimaryAddr').get('City'):
                                            dict_c['city'] = emp.get(
                                                'PrimaryAddr').get('City')

                                        if emp.get('PrimaryAddr').get('Line1'):
                                            dict_c['street'] = emp.get(
                                                'PrimaryAddr').get('Line1')

                                    '''If employee is present we update it'''
                                    employee_write = hr_employee.write(dict_e)

                                    if 'PrimaryAddr' in emp and emp.get('PrimaryAddr'):
                                        check_id = emp.get(
                                            'PrimaryAddr').get('Id')
                                        cust_obj = self.env['res.partner'].search(
                                            [['qbo_customer_id', '=', check_id]])

                                        if cust_obj:

                                            '''UPDATING EXISTING EMP'S EXISTING ADDRESS'''

                                            cust_obj.write(dict_c)
                                            employee_obj = self.env['hr.employee'].search(
                                                [['quickbook_id', '=', emp.get('Id')]])
                                            if employee_obj:
                                                res = employee_obj.update({

                                                    'address_id': cust_obj.id
                                                })

                                        else:
                                            '''UPDATING EXISTING EMP'S NEW ADDRESS'''

                                            address = self.env[
                                                'res.partner'].create(dict_c)
                                            dict_c['address_id'] = address.id

                                            employee_obj = self.env['hr.employee'].search(
                                                [['quickbook_id', '=', emp.get('Id')]])
                                            if employee_obj:
                                                res = employee_obj.update({

                                                    'address_id': address.id
                                                })

                                    if employee_write:
                                        # company.quickbooks_last_employee_imported_id = int(
                                        #     emp.get('Id'))
                                        _logger.info(
                                            'Employee Updated Successfully :: %s', emp.get('Id'))
                                        if self.import_employee_by_date:
                                            date_format = '%Y-%m-%d'
                                            if self.employee_import_by == 'crt_dt':
                                                date_string = emp.get('MetaData').get(
                                                    'CreateTime')[:10]
                                            else:
                                                date_string = emp.get('MetaData').get(
                                                    'LastUpdatedTime')[:10]

                                            date_object = datetime.strptime(date_string,
                                                                            date_format).date()
                                            self.import_employee_date = date_object
                            company.quickbooks_last_employee_imported_id = parsed_data.get('QueryResponse').get(
                                'maxResults') + int(
                                company.quickbooks_last_employee_imported_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                        else:
                            raise UserError(
                                "It seems that all of the Employees are already imported!")
                            _logger.warning(_('Empty data'))
        except Exception as e:
            raise UserError(e)

    def export_employee_mapping(self):
        if self.last_employee_mapping_export:
            employee_ids = self.env['hr.employee'].search([
                ('write_date', '>=', self.last_employee_mapping_export),
                ('quickbook_id', '=', False),
                # ('qbo_product_id', '=', False),
            ])
        else:
            employee_ids = self.env['hr.employee'].search([
                ('quickbook_id', '=', False),
            ])
        if self.export_mapping_employee_field and self.export_mapping_employee_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for employee_id in employee_ids:
                outdict = {}
                for fields_line_id in self.export_mapping_employee_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(employee_id, fields_line_id.col1.name)
                    if not attr:
                        attr = ''
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'selection' and fields_line_id.value == 'Gender':
                        if employee_id.gender == 'female':
                            values = 'Female' or ''
                        elif employee_id.gender == 'male':
                            values = 'Male' or ''
                        elif employee_id.gender == 'other':
                            values = 'Other' or ''
                        # if not values:
                        #     continue
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(employee_id, fields_line_id.col1.name)
                        attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                        values = attr or ''
                    if not values:
                        continue
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        if fields_line_id.value == 'DisplayName':
                            name_split = values.split()
                            if len(name_split) > 1:
                                outdict['MiddleName'] = name_split[0]
                                outdict['FamilyName'] = name_split[1]
                            else:
                                outdict['MiddleName'] = name_split[0]
                                outdict['FamilyName'] = name_split[0]
                        outdict[split_key[0]] = values
                parsed_dict = json.dumps(outdict)
                if employee_id.quickbook_id:
                    res = employee_id.getSyncToken(employee_id.quickbook_id)
                    outdict.update({
                        'SyncToken': str(res),
                        'Id': employee_id.quickbook_id,
                    })
                    result = requests.request('POST', url + "/employee?operation=update", headers=headers,
                                              data=parsed_dict)
                else:
                    result = requests.request('POST', url + "/employee", headers=headers, data=parsed_dict)
                if result.status_code == 200:
                    response = result.json()
                    qbo_id = int(response.get('Employee').get('Id'))
                    employee_id.quickbook_id = qbo_id
                    self.last_employee_mapping_export = datetime.now()
                    _logger.info(
                        _("Employee exported sucessfully! Employee Id: %s" % (employee_id.quickbook_id)))
                    self._cr.commit()
                else:
                    self.error_message_from_quickbook(result, employee_id.name, 'Employee')

    def State(self, state, country):

        state_id = False
        if state and country:
            country_id = self.env['res.country'].search(
                [('name', '=', country)], limit=1)
            if country_id:
                state_id = self.env['res.country.state'].search(
                    [('name', '=', state)], limit=1)
                if state_id and state_id.country_id.id == country_id.id:
                    return state_id.id
                else:
                    new_state_id = self.env['res.country.state'].create({
                        'country_id': country_id.id,
                        'code': state[:2],
                        'name': state
                    })
                    if new_state_id:
                        return new_state_id.id

    # -------------------------------------DEPARTMENT-----------------------------------------

    # function called when clicked on sync dept button
    # @api.multi
    def import_department(self):
        try:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user"))

            if company.access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + company.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'
                if company.import_department_by_date:
                    if self.department_import_by == 'crt_dt':
                        query = f"select * from Department WHERE Metadata.CreateTime > '{company.import_department_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Department WHERE Metadata.LastUpdatedTime > '{company.import_department_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from Department order by Id STARTPOSITION {company.quickbooks_last_dept_imported_id} MAXRESULTS {company.limit}"
                data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                        headers=headers)
                if data.status_code == 200:
                    recs = []
                    parsed_data = json.loads(str(data.text))
                    if parsed_data:
                        _logger.info(
                            "Department data  is ------------------->{}".format(parsed_data))
                        if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Department'):
                            if self.import_mapping_department_field and self.import_mapping_department_id and self.env.context.get(
                                    'mapping'):
                                self.import_mapping_department_id.with_context(
                                    {'import': True}).json_data = parsed_data.get('QueryResponse').get('Department')
                                return
                            for emp in parsed_data.get('QueryResponse').get('Department'):
                                # ''' This will avoid duplications'''

                                hr_dept = self.env['hr.department'].search(
                                    [('quickbook_id', '=', emp.get('Id')), ('company_id', '=', company.id)])
                                dict_e = {}

                                if emp.get('Name'):
                                    dict_e['name'] = emp.get('Name')

                                if emp.get('Id'):
                                    dict_e['quickbook_id'] = emp.get('Id')
                                    dict_e['company_id'] = company.id

                                if emp.get('ParentRef'):
                                    if emp.get('ParentRef').get('value'):
                                        parent_id = self.env['hr.department'].search(
                                            [('quickbook_id', '=', emp.get('ParentRef').get('value')),
                                             ('company_id', '=', company.id)])
                                        dict_e['parent_id'] = parent_id.id

                                if not hr_dept:

                                    '''If employee is not present we create it'''

                                    dept_create = hr_dept.create(dict_e)
                                    if dept_create:

                                        # company.quickbooks_last_dept_imported_id = int(
                                        #     emp.get('Id'))
                                        _logger.info(
                                            'Department Created Sucessfully..!!')
                                        if self.import_department_by_date:
                                            date_format = '%Y-%m-%d'
                                            if self.department_import_by == 'crt_dt':
                                                date_string = emp.get('MetaData').get(
                                                    'CreateTime')[:10]
                                            else:
                                                date_string = emp.get('MetaData').get(
                                                    'LastUpdatedTime')[:10]

                                            date_object = datetime.strptime(date_string,
                                                                            date_format).date()
                                            self.import_department_date = date_object
                                    else:
                                        _logger.info(
                                            'Department Not Created Sucessfully..!!')
                                else:
                                    dept_write = hr_dept.write(dict_e)
                                    if dept_write:
                                        # company.quickbooks_last_dept_imported_id = int(
                                        #     emp.get('Id'))
                                        _logger.info(
                                            'Department Updated Sucessfully..!!')
                                        if self.import_department_by_date:
                                            date_format = '%Y-%m-%d'
                                            if self.department_import_by == 'crt_dt':
                                                date_string = emp.get('MetaData').get(
                                                    'CreateTime')[:10]
                                            else:
                                                date_string = emp.get('MetaData').get(
                                                    'LastUpdatedTime')[:10]

                                            date_object = datetime.strptime(date_string,
                                                                            date_format).date()
                                            self.import_department_date = date_object
                                    else:
                                        _logger.info(
                                            'Department Not Updated Sucessfully..!!')
                            company.quickbooks_last_dept_imported_id = parsed_data.get('QueryResponse').get(
                                'maxResults') + int(
                                company.quickbooks_last_dept_imported_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                        else:
                            raise UserError(
                                "It seems that all of the Departments are already imported!")
                            _logger.warning(_('Empty data'))
        except Exception as e:
            raise UserError(e)

    def export_department_mapping(self):
        if self.last_department_mapping_export:
            department_ids = self.env['hr.department'].search([
                ('write_date', '>=', self.last_department_mapping_export),
                ('quickbook_id', '=', False),
            ])
        else:
            department_ids = self.env['hr.department'].search([
                ('quickbook_id', '=', False),
            ])
        if self.export_mapping_department_field and self.export_mapping_department_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for department_id in department_ids:
                outdict = {}
                for fields_line_id in self.export_mapping_department_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(department_id, fields_line_id.col1.name)
                    if not attr:
                        continue
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(department_id, fields_line_id.col1.name)
                        attr = ''
                        if m2o_ref:
                            attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                        values = attr or ''
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                parsed_dict = json.dumps(outdict)
                result = requests.request('POST', url + "/department?minorversion=75", headers=headers,
                                          data=parsed_dict)
                if result.status_code == 200:
                    response = result.json()
                    qbo_id = int(response.get('Department').get('Id'))
                    department_id.quickbook_id = qbo_id
                    self.last_department_mapping_export = datetime.now()
                    _logger.info(
                        _("Department exported sucessfully! Department Id: %s" % (
                            department_id.quickbook_id)))
                    self._cr.commit()
                else:
                    self.error_message_from_quickbook(result, department_id.name, 'Department')

    # ---------------------------------SALE ORDER-----------------------------
    def import_sale_order(self):
        try:
            _logger.info("Sale order")
            if self:
                company = self

                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    company = self.env.company
                _logger.info("Company is22-> {}".format(company))
                if company.access_token:
                    _logger.info(
                        "Access token is ---> {}".format(company.access_token))
                    headers = {}
                    headers['Authorization'] = 'Bearer ' + company.access_token
                    headers['accept'] = 'application/json'
                    headers['Content-Type'] = 'text/plain'
                    if company.import_sale_order_by_date:
                        if self.sale_order_import_by == 'crt_dt':
                            query = f"select * from Estimate WHERE Metadata.CreateTime >= '{company.import_sale_order_date}' order by Id MAXRESULTS {company.limit}"
                        elif self.sale_order_import_by == 'other_dt':
                            query = f"select * from Estimate WHERE TxnDate >= '{company.import_sale_order_date}' order by Id MAXRESULTS {company.limit}"
                        else:
                            query = f"select * from Estimate WHERE Metadata.LastUpdatedTime >= '{company.import_sale_order_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Estimate order by Id STARTPOSITION {company.quickbooks_last_sale_imported_id} MAXRESULTS {company.limit}"
                    _logger.info("Query is -----> {}".format(query))
                    try:
                        data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                                headers=headers)
                    except requests.exceptions.RequestException as re:
                        raise UserError(f"Request error occurred while fetching sale orders: {str(re)}")
                    _logger.info("************data{}".format(data.text))
                    if data.status_code == 200:
                        try:
                            recs = []
                            _logger.info("************data{}".format(data.text))
                            try:
                                parsed_data = json.loads(str(data.text))
                            except json.JSONDecodeError as je:
                                raise UserError(f"JSON decode error while parsing sale order response: {str(je)}")
                            if 'QueryResponse' in parsed_data:
                                Estimate = parsed_data.get(
                                    'QueryResponse').get('Estimate', [])
                            else:
                                Estimate = [parsed_data.get('Estimate')] or []
                            if len(Estimate) == 0:
                                raise UserError(
                                    "It seems that all of the Sale Orders are already imported.")
                            max_result = parsed_data.get('QueryResponse').get('maxResults')

                            if self.import_mapping_vendor_field and self.env.context.get('mapping'):
                                if parsed_data.get('QueryResponse').get('Estimate', []):
                                    self.import_mapping_so_id.with_context({'import': True}).json_data = Estimate
                                else:
                                    raise UserError("Empty data")
                                return
                            if parsed_data:

                                if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Estimate'):
                                    custom_tax_id_id = [[6, False, []]]

                                    for cust in parsed_data.get('QueryResponse').get('Estimate'):
                                        try:
                                            qbo_id = cust.get('Id') or 'Unknown'
                                            if not cust.get('CustomerRef') or not cust.get('CustomerRef').get('value'):
                                                raise ValidationError(f"Missing CustomerRef in sale order. QBO ID: {qbo_id}")
                                            
                                            if "CustomerRef" in cust and cust.get('CustomerRef').get('value'):
                                                # searching sales order
                                                sale_order = self.env['sale.order'].search(
                                                    [('quickbook_id', '=', cust.get('Id')), ('company_id', '=', company.id),
                                                    ('locked', '=', False)])
                                                _logger.info(
                                                    "Sale order exists or not!!!!!---->{}".format(sale_order))
                                                if not sale_order:
                                                    _logger.info("Creating Sales order...")
                                                    _logger.info("Partner value is ---------------> {}".format(
                                                        cust.get('CustomerRef').get('value')))
                                                    res_partner = self.env['res.partner'].search(
                                                        [('qbo_customer_id', '=', cust.get('CustomerRef').get('value')),
                                                        ('type', '=', 'contact'), ('company_id', '=', company.id)], limit=1)
                                                    _logger.info(
                                                        "RES PARTNER IS -> {}".format(res_partner))

                                                    if not res_partner:
                                                        customer_name = cust.get('CustomerRef').get('name')
                                                        customer_id = cust.get('CustomerRef').get('value')
                                                        raise ValidationError(
                                                            f"Customer '{customer_name}' with QuickBooks ID {customer_id} not found in Odoo. Please import the customer before importing sales orders. Sale Order QBO ID: {qbo_id}")

                                                    if res_partner:
                                                        # Check if all products in the sale order exist in Odoo
                                                        all_products_exist = all(
                                                            self.env['product.product'].search(
                                                                [('qbo_product_id', '=',
                                                                line.get('SalesItemLineDetail').get('ItemRef').get('value')),
                                                                ('company_id', '=', company.id)], limit=1)
                                                            for line in cust.get('Line') if 'SalesItemLineDetail' in line
                                                        )

                                                        if all_products_exist:
                                                            dict_s = {}
                                                            # Update tax state
                                                            if 'GlobalTaxCalculation' in cust and cust.get(
                                                                    'GlobalTaxCalculation'):
                                                                if cust.get('GlobalTaxCalculation') == 'TaxExcluded':
                                                                    dict_s[
                                                                        'tax_state'] = 'exclusive'
                                                                elif cust.get('GlobalTaxCalculation') == 'TaxInclusive':
                                                                    dict_s[
                                                                        'tax_state'] = 'inclusive'
                                                                elif cust.get('GlobalTaxCalculation') == 'NotApplicable':
                                                                    dict_s[
                                                                        'tax_state'] = 'notapplicable'

                                                            if 'Id' in cust and cust.get('Id'):
                                                                dict_s[
                                                                    'partner_id'] = res_partner.id
                                                                dict_s['state'] = 'sale'
                                                                dict_s['quickbook_id'] = cust.get(
                                                                    'Id')
                                                                dict_s[
                                                                    'company_id'] = company.id

                                                            if 'DocNumber' in cust and cust.get('DocNumber'):
                                                                dict_s['name'] = cust.get(
                                                                    'DocNumber')

                                                            if 'PaymentRefNum' in cust and cust.get('PaymentRefNum'):
                                                                dict_s['client_order_ref'] = cust.get(
                                                                    'PaymentRefNum')

                                                            if 'TotalAmt' in cust and cust.get('TotalAmt'):
                                                                dict_s['amount_total'] = cust.get(
                                                                    'TotalAmt')

                                                            if 'TxnDate' in cust and cust.get('TxnDate'):
                                                                dict_s['date_order'] = cust.get(
                                                                    'TxnDate')

                                                            ele_in_list = len(cust.get('Line'))
                                                            dict_t = cust.get(
                                                                'Line')[ele_in_list - 1]
                                                            _logger.info(
                                                                "Dictionary before creating is----> {}".format(dict_t))

                                                            now = datetime.now()
                                                            _logger.info(
                                                                "Dictionary is--->{}:".format(dict_s))
                                                            so_obj = self.env[
                                                                'sale.order'].create(dict_s)

                                                            if so_obj:
                                                                self._cr.commit()
                                                                _logger.info(
                                                                    "WRITING QBO ID TO SALE ORDER {}".format(so_obj.id))
                                                                so_obj.write(
                                                                    {'quickbook_id': cust.get('Id')})
                                                                _logger.info(
                                                                    "Object is --->{}".format(so_obj))
                                                                _logger.info(
                                                                    'Sale Order Created...!!! :: %s', cust.get('Id'))
                                                            # ///////////////////////////////////////////////////////////////
                                                            custom_tax_id = None
                                                            discount_per = 0
                                                            for i in cust.get('Line'):
                                                                if i.get(
                                                                        'DetailType') == 'DiscountLineDetail' and 'DiscountLineDetail' in i:
                                                                    discount_per = i.get('DiscountLineDetail').get(
                                                                        'DiscountPercent')
                                                                    break
                                                            for i in cust.get('Line'):
                                                                _logger.info(
                                                                    "Particular instance is ------------> {}".format(i))

                                                                if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):

                                                                    if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                        _logger.info(
                                                                            "Transaction data!!!")
                                                                        if i.get('SalesItemLineDetail').get('TaxCodeRef').get(
                                                                                'value'):

                                                                            qb_tax_id = i.get('SalesItemLineDetail').get(
                                                                                'TaxCodeRef').get(
                                                                                'value')
                                                                            record = self.env[
                                                                                'account.tax']
                                                                            tax = record.search([('qbo_tax_id', '=', qb_tax_id),
                                                                                                ('type_tax_use', '=', 'sale'),

                                                                                                ('company_id', '=',
                                                                                                company.id)])

                                                                            if not tax and cust.get(
                                                                                    'TxnTaxDetail') and cust.get(
                                                                                'TxnTaxDetail').get(
                                                                                'TxnTaxCodeRef') and cust.get(
                                                                                'TxnTaxDetail').get(
                                                                                'TxnTaxCodeRef').get('value'):
                                                                                qb_tax_id = cust.get('TxnTaxDetail').get(
                                                                                    'TxnTaxCodeRef').get('value')
                                                                                tax = record.search(
                                                                                    [('qbo_tax_id', '=', qb_tax_id),
                                                                                    ('type_tax_use', '=', 'sale'),
                                                                                    ('company_id', '=',
                                                                                    company.id)], limit=1)

                                                                            if tax:
                                                                                custom_tax_id = [
                                                                                    (6, 0, [tax.id])]
                                                                            else:
                                                                                custom_tax_id = None

                                                                if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                                                                    _logger.info(
                                                                        "SalesItem Data")
                                                                    res_product = self.env['product.product'].search(
                                                                        [('qbo_product_id', '=',
                                                                        i.get('SalesItemLineDetail').get('ItemRef').get(
                                                                            'value')),
                                                                        ('company_id', '=', company.id),
                                                                        ('active', 'in', [True, False])],
                                                                        limit=1)
                                                                    if res_product:
                                                                        if not res_product.active:
                                                                            res_product.active = True

                                                                    shipping_line = False
                                                                    if not res_product and i.get('SalesItemLineDetail').get(
                                                                            'ItemRef').get('value') == 'SHIPPING_ITEM_ID':
                                                                        if not self.delivery_carrier_id:
                                                                            raise UserError(
                                                                                _(f"Please defined the Shipping Method in company. Sale Order QBO ID: {qbo_id}"))
                                                                        res_product = self.delivery_carrier_id.product_id
                                                                        shipping_line = True
                                                                        dict_l = {}
                                                                        dict_l[
                                                                            'order_id'] = so_obj.id
                                                                        dict_l[
                                                                            'product_id'] = res_product.id
                                                                        dict_l['product_uom_qty'] = 1
                                                                        dict_l['price_unit'] = i.get('Amount')
                                                                        dict_l['name'] = res_product.name
                                                                        if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                            tax_val = i.get('SalesItemLineDetail').get(
                                                                                'TaxCodeRef').get('value')
                                                                            if tax_val:
                                                                                dict_l[
                                                                                    'tax_ids'] = custom_tax_id
                                                                        _logger.info(
                                                                            "Dictionary for sale order line is --------> {}".format(
                                                                                dict_l))
                                                                        create_p = self.env[
                                                                            'sale.order.line'].create(dict_l)
                                                                        self._cr.commit()
                                                                        _logger.info(
                                                                            "Sale order line --------------->{}".format(
                                                                                create_p))
                                                                        # if create_p:
                                                                        #     company.quickbooks_last_sale_imported_id = int(
                                                                        #         cust.get('Id'))
                                                                    if shipping_line:
                                                                        continue

                                                                    if res_product:
                                                                        dict_l = {}

                                                                        if discount_per:
                                                                            dict_l['discount'] = discount_per

                                                                        if i.get('Id'):
                                                                            dict_l['qb_id'] = int(
                                                                                i.get('Id'))

                                                                        if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                            tax_val = i.get('SalesItemLineDetail').get(
                                                                                'TaxCodeRef').get(
                                                                                'value')
                                                                            if tax_val:
                                                                                dict_l[
                                                                                    'tax_ids'] = custom_tax_id
                                                                            # else:
                                                                            # dict_l['tax_id']
                                                                            # =

                                                                        dict_l[
                                                                            'order_id'] = so_obj.id

                                                                        dict_l[
                                                                            'product_id'] = res_product.id

                                                                        if i.get('SalesItemLineDetail').get('Qty'):
                                                                            dict_l['product_uom_qty'] = i.get(
                                                                                'SalesItemLineDetail').get(
                                                                                'Qty')
                                                                        else:
                                                                            dict_l[
                                                                                'product_uom_qty'] = 0.0

                                                                        if i.get('SalesItemLineDetail').get('UnitPrice'):
                                                                            dict_l['price_unit'] = i.get(
                                                                                'SalesItemLineDetail').get(
                                                                                'UnitPrice')
                                                                        else:
                                                                            dict_l[
                                                                                'price_unit'] = 0.0

                                                                        if i.get('Description'):
                                                                            dict_l['name'] = i.get(
                                                                                'Description')
                                                                        else:
                                                                            dict_l[
                                                                                'name'] = 'NA'
                                                                        _logger.info(
                                                                            "Dictionary for sale order line is --------> {}".format(
                                                                                dict_l))
                                                                        create_p = self.env[
                                                                            'sale.order.line'].create(dict_l)
                                                                        self._cr.commit()
                                                                        _logger.info(
                                                                            "Sale order line --------------->{}".format(
                                                                                create_p))
                                                                        # if create_p:
                                                                        #     company.quickbooks_last_sale_imported_id = int(
                                                                        #         cust.get('Id'))
                                                                    else:
                                                                        raise UserError('Product ' + str(
                                                                            i.get('SalesItemLineDetail').get('ItemRef').get(

                                                                                'name')) + ' is not defined in Odoo. Sale Order ' + ' Name : ' + cust.get(
                                                                            'DocNumber'))
                                                            if cust.get("LinkedTxn"):
                                                                # LINK SALE ORDER WITH INVOICE
                                                                for rec in cust.get("LinkedTxn"):
                                                                    if rec.get('TxnType') == 'Invoice':
                                                                        try:
                                                                            link_inv_obj = self.env['account.move'].search(
                                                                                [('qbo_invoice_id', '=', rec.get("TxnId")),('company_id', '=',
                                                                                    company.id)],
                                                                                limit=1)
                                                                            if link_inv_obj:
                                                                                # Ensure invoice_obj is valid
                                                                                if so_obj:
                                                                                    try:
                                                                                        # Directly update the invoice_ids field in sale.order
                                                                                        so_obj.write(
                                                                                            {'invoice_ids': [(4, link_inv_obj.id)]})

                                                                                        # Update the invoice_lines field in sale.order.line
                                                                                        for line in so_obj.order_line:
                                                                                            line.write(
                                                                                                {'invoice_lines': [(4, line_id) for
                                                                                                                line_id in
                                                                                                                link_inv_obj.invoice_line_ids.ids]})

                                                                                        # Log the linking for debugging purposes
                                                                                        _logger.info(
                                                                                            f"Linked Sale Order {so_obj.id} to Invoice {link_inv_obj.id}")
                                                                                        # Commit the transaction
                                                                                    except Exception as e:
                                                                                        _logger.error(
                                                                                            f"Error while linking invoice lines to Sale Order {so_obj.qbo_id if so_obj else 'Unknown'}: {str(e)}")
                                                                                else:
                                                                                    _logger.error("Sale Order object is not valid")
                                                                            else:
                                                                                _logger.error(f"No Invoice found with quickbook_id {rec.get('TxnId')}")
                                                                        except Exception as e:
                                                                            _logger.error(
                                                                                f"Unhandled exception occurred while processing LinkedTxn with TxnId {rec.get('TxnId')} for Sale Order QBO ID {so_obj.qbo_id if so_obj else 'Unknown'}: {str(e)}")
                                                                            raise ValidationError(
                                                                                f"Unhandled exception for Sale Order QBO ID {so_obj.qbo_id if so_obj else 'Unknown'} during invoice linking: {str(e)}")


                                                        else:
                                                            _logger.info(
                                                                "Skipping sale order creation because one or more products are not defined in Odoo.")
                                                            for line in cust.get('Line'):
                                                                if 'SalesItemLineDetail' in line:
                                                                    product_name = line.get('SalesItemLineDetail').get(
                                                                        'ItemRef').get('name')
                                                                    raise UserError(
                                                                        f'Product {product_name} is not defined in Odoo. Sale Order Name: {cust.get("DocNumber")}')
                                        except ValidationError as ve:
                                            _logger.error("Validation error in sale order QBO ID %s: %s", qbo_id, str(ve))
                                            raise ve
                                        except UserError as ue:
                                            raise ue
                                        except Exception as order_exc:
                                            _logger.exception("Error processing sale order QBO ID %s", qbo_id)
                                            raise UserError(f"Unexpected error in sale order QBO ID {qbo_id}: {str(order_exc)}")
                                    company.quickbooks_last_sale_imported_id = max_result + int(
                                        company.quickbooks_last_sale_imported_id)
                                    success_form = self.env.ref(
                                        'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                                else:
                                    raise UserError(
                                        "It seems that all of the Sales Order are already imported!")
                        except (UserError, ValidationError):
                            raise
                        except Exception as parse_exc:
                            _logger.exception("Failed to parse QuickBooks response")
                            raise UserError(f"Failed to parse QuickBooks response: {str(parse_exc)}")
            else:
                companys = self.env.companies
                for company in companys:
                    try:
                        if company.access_token:
                            _logger.info(
                                "Access token is ---> {}".format(company.access_token))
                            headers = {}
                            headers['Authorization'] = 'Bearer ' + company.access_token
                            headers['accept'] = 'application/json'
                            headers['Content-Type'] = 'text/plain'
                            if company.import_sale_order_by_date:
                                if self.sale_order_import_by == 'crt_dt':
                                    query = "select * from estimate WHERE Metadata.CreateTime >= '%s' AND ID >= '%s'" % (
                                        company.import_sale_order_date, company.quickbooks_last_sale_imported_id)
                                elif self.sale_order_import_by == 'other_dt':
                                    query = "select * from estimate WHERE TxnDate >= '%s' AND ID >= '%s'" % (
                                        company.import_sale_order_date, company.quickbooks_last_sale_imported_id)
                                else:
                                    query = "select * from estimate WHERE Metadata.LastUpdatedTime >= '%s' AND ID >= '%s'" % (
                                        company.import_sale_order_date, company.quickbooks_last_sale_imported_id)
                            else:
                                query = "select * from estimate WHERE Id > '%s' order by Id  STARTPOSITION %s MAXRESULTS %s " % (
                                    company.quickbooks_last_sale_imported_id, company.start, company.limit)
                            _logger.info("Query is -----> {}".format(query))

                            try:
                                data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                                        headers=headers)
                            except requests.exceptions.RequestException as e:
                                raise ValidationError("Request error while fetching sales order for QBO company ID {}: {}".format(company.id, str(e)))
                            
                            _logger.info("************data{}".format(data.text))
                            if data.status_code == 200:
                                recs = []
                                _logger.info("************data{}".format(data.text))
                                try:
                                    parsed_data = json.loads(str(data.text))
                                except json.JSONDecodeError as e:
                                    raise ValidationError("JSON decode error for QBO company ID {}: {}".format(company.id, str(e)))
                
                                if 'QueryResponse' in parsed_data:
                                    Estimate = parsed_data.get(
                                        'QueryResponse').get('Estimate', [])
                                else:
                                    Estimate = [parsed_data.get('Estimate')] or []
                                if len(Estimate) == 0:
                                    _logger.info(
                                        "It seems that all of the Sale Orders are already imported.")
                                    continue
                                max_result = parsed_data.get('QueryResponse').get('maxResults')

                                if self.import_mapping_vendor_field and self.env.context.get('mapping'):
                                    if parsed_data.get('QueryResponse').get('Estimate', []):
                                        self.import_mapping_so_id.with_context({'import': True}).json_data = Estimate
                                    else:
                                        _logger.info(
                                            "Empty data")
                                        continue
                                    return
                                if parsed_data:

                                    if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get(
                                            'Estimate'):
                                        custom_tax_id_id = [[6, False, []]]

                                        for cust in parsed_data.get('QueryResponse').get('Estimate'):
                                            try:
                                                if "CustomerRef" in cust and cust.get('CustomerRef').get('value'):
                                                    try:
                                                        # searching sales order
                                                        sale_order = self.env['sale.order'].search(
                                                            [('quickbook_id', '=', cust.get('Id')),
                                                            ('company_id', '=', company.id)])
                                                        _logger.info(
                                                            "Sale order exists or not!!!!!---->{}".format(sale_order))
                                                        if not sale_order:
                                                            try:
                                                                _logger.info("Creating Sales order...")
                                                                _logger.info("Partner value is ---------------> {}".format(
                                                                    cust.get('CustomerRef').get('value')))
                                                                res_partner = self.env['res.partner'].search(
                                                                    [('qbo_customer_id', '=', cust.get('CustomerRef').get('value')),
                                                                    ('type', '=', 'contact'), ('company_id', '=', company.id)],
                                                                    limit=1)
                                                                _logger.info(
                                                                    "RES PARTNER IS -> {}".format(res_partner))
                                                                if res_partner:
                                                                    dict_s = {}

                                                                    # Update tax state
                                                                    if 'GlobalTaxCalculation' in cust and cust.get(
                                                                            'GlobalTaxCalculation'):
                                                                        if cust.get('GlobalTaxCalculation') == 'TaxExcluded':
                                                                            dict_s[
                                                                                'tax_state'] = 'exclusive'
                                                                        elif cust.get('GlobalTaxCalculation') == 'TaxInclusive':
                                                                            dict_s[
                                                                                'tax_state'] = 'inclusive'
                                                                        elif cust.get('GlobalTaxCalculation') == 'NotApplicable':
                                                                            dict_s[
                                                                                'tax_state'] = 'notapplicable'

                                                                    if 'Id' in cust and cust.get('Id'):
                                                                        dict_s[
                                                                            'partner_id'] = res_partner.id
                                                                        dict_s['state'] = 'sale'
                                                                        dict_s['quickbook_id'] = cust.get(
                                                                            'Id')
                                                                        dict_s[
                                                                            'company_id'] = company.id

                                                                    if 'DocNumber' in cust and cust.get('DocNumber'):
                                                                        dict_s['name'] = cust.get(
                                                                            'DocNumber')

                                                                    if 'PaymentRefNum' in cust and cust.get('PaymentRefNum'):
                                                                        dict_s['client_order_ref'] = cust.get(
                                                                            'PaymentRefNum')

                                                                    if 'TotalAmt' in cust and cust.get('TotalAmt'):
                                                                        dict_s['amount_total'] = cust.get(
                                                                            'TotalAmt')

                                                                    if 'TxnDate' in cust and cust.get('TxnDate'):
                                                                        dict_s['date_order'] = cust.get(
                                                                            'TxnDate')

                                                                    ele_in_list = len(cust.get('Line'))
                                                                    dict_t = cust.get(
                                                                        'Line')[ele_in_list - 1]
                                                                    _logger.info(
                                                                        "Dictionary before creating is----> {}".format(dict_t))

                                                                    now = datetime.now()
                                                                    _logger.info(
                                                                        "Dictionary is--->{}:".format(dict_s))
                                                                    so_obj = self.env[
                                                                        'sale.order'].create(dict_s)

                                                                    if so_obj:
                                                                        self._cr.commit()
                                                                        _logger.info(
                                                                            "WRITING QBO ID TO SALE ORDER {}".format(so_obj.id))
                                                                        so_obj.write(
                                                                            {'quickbook_id': cust.get('Id')})
                                                                        _logger.info(
                                                                            "Object is --->{}".format(so_obj))
                                                                        _logger.info(
                                                                            'Sale Order Created...!!! :: %s', cust.get('Id'))
                                                                    # ///////////////////////////////////////////////////////////////
                                                                    custom_tax_id = None
                                                                    discount_per = 0
                                                                    for i in cust.get('Line'):
                                                                        if i.get(
                                                                                'DetailType') == 'DiscountLineDetail' and 'DiscountLineDetail' in i:
                                                                            discount_per = i.get('DiscountLineDetail').get(
                                                                                'DiscountPercent')
                                                                            break
                                                                    for i in cust.get('Line'):
                                                                        _logger.info(
                                                                            "Particular instance is ------------> {}".format(i))

                                                                        if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):

                                                                            if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                                _logger.info(
                                                                                    "Transaction data!!!")
                                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef').get(
                                                                                        'value'):

                                                                                    qb_tax_id = i.get('SalesItemLineDetail').get(
                                                                                        'TaxCodeRef').get(
                                                                                        'value')
                                                                                    record = self.env[
                                                                                        'account.tax']
                                                                                    tax = record.search([('qbo_tax_id', '=', qb_tax_id),
                                                                                                        ('type_tax_use', '=', 'sale'),
                                                                                                        ('company_id', '=',
                                                                                                        company.id)])

                                                                                    if tax:
                                                                                        custom_tax_id = [
                                                                                            (6, 0, [tax.id])]
                                                                                    else:
                                                                                        custom_tax_id = None

                                                                        if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                                                                            _logger.info(
                                                                                "SalesItem Data")
                                                                            res_product = self.env['product.product'].search(
                                                                                [('qbo_product_id', '=',
                                                                                i.get('SalesItemLineDetail').get('ItemRef').get(
                                                                                    'value')),
                                                                                ('company_id', '=', company.id),
                                                                                ('active', 'in', [True, False])],
                                                                                limit=1)
                                                                            if res_product:
                                                                                if not res_product.active:
                                                                                    res_product.active = True
                                                                            shipping_line = False
                                                                            if not res_product and i.get('SalesItemLineDetail').get(
                                                                                    'ItemRef').get('value') == 'SHIPPING_ITEM_ID':
                                                                                if not self.delivery_carrier_id:
                                                                                    _logger.info(
                                                                                        "Please defined the Shipping Method in company!")
                                                                                    continue
                                                                                res_product = self.delivery_carrier_id.product_id
                                                                                shipping_line = True
                                                                                dict_l = {}
                                                                                dict_l[
                                                                                    'order_id'] = so_obj.id
                                                                                dict_l[
                                                                                    'product_id'] = res_product.id
                                                                                dict_l['product_uom_qty'] = 1
                                                                                dict_l['price_unit'] = i.get('Amount')
                                                                                dict_l['name'] = res_product.name
                                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                                    tax_val = i.get('SalesItemLineDetail').get(
                                                                                        'TaxCodeRef').get('value')
                                                                                    if tax_val:
                                                                                        dict_l[
                                                                                            'tax_ids'] = custom_tax_id
                                                                                _logger.info(
                                                                                    "Dictionary for sale order line is --------> {}".format(
                                                                                        dict_l))
                                                                                create_p = self.env[
                                                                                    'sale.order.line'].create(dict_l)
                                                                                self._cr.commit()
                                                                                _logger.info(
                                                                                    "Sale order line --------------->{}".format(
                                                                                        create_p))
                                                                                # if create_p:
                                                                                #     company.quickbooks_last_sale_imported_id = int(
                                                                                #         cust.get('Id'))
                                                                            if shipping_line:
                                                                                continue

                                                                            if res_product:
                                                                                dict_l = {}

                                                                                if discount_per:
                                                                                    dict_l['discount'] = discount_per

                                                                                if i.get('Id'):
                                                                                    dict_l['qb_id'] = int(
                                                                                        i.get('Id'))

                                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                                    tax_val = i.get('SalesItemLineDetail').get(
                                                                                        'TaxCodeRef').get(
                                                                                        'value')
                                                                                    if tax_val:
                                                                                        dict_l[
                                                                                            'tax_ids'] = custom_tax_id
                                                                                    # else:
                                                                                    # dict_l['tax_id']
                                                                                    # =

                                                                                dict_l[
                                                                                    'order_id'] = so_obj.id

                                                                                dict_l[
                                                                                    'product_id'] = res_product.id

                                                                                if i.get('SalesItemLineDetail').get('Qty'):
                                                                                    dict_l['product_uom_qty'] = i.get(
                                                                                        'SalesItemLineDetail').get(
                                                                                        'Qty')
                                                                                else:
                                                                                    dict_l[
                                                                                        'product_uom_qty'] = 0.0

                                                                                if i.get('SalesItemLineDetail').get('UnitPrice'):
                                                                                    dict_l['price_unit'] = i.get(
                                                                                        'SalesItemLineDetail').get(
                                                                                        'UnitPrice')
                                                                                else:
                                                                                    dict_l[
                                                                                        'price_unit'] = 0.0

                                                                                if i.get('Description'):
                                                                                    dict_l['name'] = i.get(
                                                                                        'Description')
                                                                                else:
                                                                                    dict_l[
                                                                                        'name'] = 'NA'
                                                                                _logger.info(
                                                                                    "Dictionary for sale order line is --------> {}".format(
                                                                                        dict_l))
                                                                                create_p = self.env[
                                                                                    'sale.order.line'].create(dict_l)
                                                                                self._cr.commit()
                                                                                _logger.info(
                                                                                    "Sale order line --------------->{}".format(
                                                                                        create_p))
                                                                                # if create_p:
                                                                                #     company.quickbooks_last_sale_imported_id = int(
                                                                                #         cust.get('Id'))
                                                                            else:
                                                                                _logger.info(
                                                                                    'Product ' + str(
                                                                                        i.get('SalesItemLineDetail').get('ItemRef').get(

                                                                                            'name')) + ' is not defined in Odoo. Sale Order ' + ' Name : ' + cust.get(
                                                                                        'DocNumber'))
                                                            except Exception as e:
                                                                raise ValidationError("Error while creating sale order for QBO ID {}: {}".format(cust.get('Id'), str(e)))
                    
                                                        else:
                                                            try:
                                                                _logger.info("Else part------")
                                                                res_partner = self.env['res.partner'].search(
                                                                    [('qbo_customer_id', '=', cust.get('CustomerRef').get('value')),
                                                                    ('company_id', '=', company.id)], limit=1)
                                                                _logger.info(
                                                                    "Directing to else part....->{}".format(res_partner))
                                                                if not res_partner:
                                                                    raise ValidationError(
                                                                        "CustomerRef not found while updating for QBO ID: {}".format(cust.get('Id')))
                                                                if res_partner:
                                                                    dict_s = {}

                                                                    if cust.get('Id'):
                                                                        dict_s[
                                                                            'partner_id'] = res_partner.id
                                                                        dict_s['quickbook_id'] = cust.get(
                                                                            'Id')
                                                                        dict_s['state'] = 'sale'

                                                                    now = datetime.now()
                                                                    #                                         dict_s['date_order'] = now.strftime("%Y-%m-%d %H:%M:%S")

                                                                    # Update tax state
                                                                    if 'GlobalTaxCalculation' in cust and cust.get(
                                                                            'GlobalTaxCalculation'):
                                                                        if cust.get('GlobalTaxCalculation') == 'TaxExcluded':
                                                                            dict_s[
                                                                                'tax_state'] = 'exclusive'
                                                                        elif cust.get('GlobalTaxCalculation') == 'TaxInclusive':
                                                                            dict_s[
                                                                                'tax_state'] = 'inclusive'
                                                                        elif cust.get('GlobalTaxCalculation') == 'NotApplicable':
                                                                            dict_s[
                                                                                'tax_state'] = 'notapplicable'

                                                                    if 'PaymentRefNum' in cust and cust.get('PaymentRefNum'):
                                                                        dict_s['client_order_ref'] = cust.get(
                                                                            'PaymentRefNum')

                                                                    if 'DocNumber' in cust and cust.get('DocNumber'):
                                                                        dict_s['name'] = cust.get(
                                                                            'DocNumber')

                                                                    if 'TotalAmt' in cust and cust.get('TotalAmt'):
                                                                        dict_s['amount_total'] = cust.get(
                                                                            'TotalAmt')

                                                                    if 'TxnDate' in cust and cust.get('TxnDate'):
                                                                        dict_s['date_order'] = cust.get(
                                                                            'TxnDate')

                                                                    ele_in_list = len(cust.get('Line'))

                                                                    dict_t = cust.get(
                                                                        'Line')[ele_in_list - 1]

                                                                    _logger.info(
                                                                        "Dict for update is ----> {}".format(dict_s))
                                                                    update_so = sale_order.write(
                                                                        dict_s)
                                                                    _logger.info(
                                                                        "update obj {}".format(update_so))
                                                                    if update_so:
                                                                        _logger.info(
                                                                            'Sale Order Updated...!!! :: %s', cust.get('Id'))
                                                                    custom_tax_id = None
                                                                    discount_per = 0
                                                                    for i in cust.get('Line'):
                                                                        if i.get(
                                                                                'DetailType') == 'DiscountLineDetail' and 'DiscountLineDetail' in i:
                                                                            discount_per = i.get('DiscountLineDetail').get(
                                                                                'DiscountPercent')
                                                                            break
                                                                    # discount_amt = 0
                                                                    for i in cust.get('Line'):
                                                                        _logger.info("IIIIIIIIIIIIIII---{}".format(i))
                                                                        if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                                                                            if i.get('SalesItemLineDetail').get('TaxCodeRef'):

                                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef').get(
                                                                                        'value'):
                                                                                    qb_tax_id = i.get('SalesItemLineDetail').get(
                                                                                        'TaxCodeRef').get(
                                                                                        'value')
                                                                                    record = self.env[
                                                                                        'account.tax']
                                                                                    tax = record.search([('qbo_tax_id', '=', qb_tax_id),
                                                                                                        ('type_tax_use', '=', 'sale'),
                                                                                                        ('company_id', '=',
                                                                                                        company.id)])
                                                                                    if tax:
                                                                                        custom_tax_id = [
                                                                                            (6, 0, [tax.id])]
                                                                                    else:
                                                                                        custom_tax_id = None

                                                                        if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                                                                            res_product = self.env['product.product'].search(
                                                                                [('qbo_product_id', '=',
                                                                                i.get('SalesItemLineDetail').get('ItemRef').get(
                                                                                    'value')),
                                                                                ('company_id', '=', company.id)])
                                                                            shipping_line = False
                                                                            if not res_product and i.get('SalesItemLineDetail').get(
                                                                                    'ItemRef').get('value') == 'SHIPPING_ITEM_ID':
                                                                                if not self.delivery_carrier_id:
                                                                                    _logger.info("Please defined the Shipping Method in company!")
                                                                                    raise ValidationError(f"Please defined the Shipping Method in company {company.id}!")
                                                                                res_product = self.delivery_carrier_id.product_id
                                                                                shipping_line = True
                                                                                dict_l = {}
                                                                                dict_l[
                                                                                    'order_id'] = sale_order.id
                                                                                dict_l[
                                                                                    'product_id'] = res_product.id
                                                                                dict_l['product_uom_qty'] = 1
                                                                                dict_l['price_unit'] = i.get('Amount')
                                                                                dict_l['name'] = res_product.name
                                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                                    tax_val = i.get('SalesItemLineDetail').get(
                                                                                        'TaxCodeRef').get('value')
                                                                                    if tax_val:
                                                                                        dict_l[
                                                                                            'tax_ids'] = custom_tax_id
                                                                                _logger.info(
                                                                                    "Dictionary for sale order line is --------> {}".format(
                                                                                        dict_l))

                                                                                create_po = self.env['sale.order.line'].search(
                                                                                    ['&', ('product_id', '=', res_product.id),
                                                                                    (('order_id', '=', sale_order.id))], limit=1)
                                                                                if create_po:
                                                                                    res = create_po.update(dict_l)
                                                                                self._cr.commit()
                                                                                _logger.info(
                                                                                    "Sale order line --------------->{}".format(
                                                                                        create_po))
                                                                                # if create_po:
                                                                                #     company.quickbooks_last_sale_imported_id = int(
                                                                                #         cust.get('Id'))
                                                                            if shipping_line:
                                                                                continue
                                                                            if res_product:
                                                                                s_order_line = self.env['sale.order.line'].search(
                                                                                    ['&', ('product_id', '=', res_product.id),
                                                                                    (('order_id', '=', sale_order.id))])

                                                                                if s_order_line:

                                                                                    dict_lp = {}

                                                                                    if i.get('SalesItemLineDetail').get('Qty'):
                                                                                        quantity = i.get('SalesItemLineDetail').get(
                                                                                            'Qty')
                                                                                    else:
                                                                                        quantity = 0

                                                                                    if i.get('SalesItemLineDetail').get('TaxCodeRef'):

                                                                                        tax_val = i.get('SalesItemLineDetail').get(
                                                                                            'TaxCodeRef').get(
                                                                                            'value')
                                                                                        if tax_val:
                                                                                            # custom_tax_id = [(6, 0, [tax.id])]
                                                                                            custom_tax_id_id = custom_tax_id
                                                                                        else:
                                                                                            custom_tax_id_id = None

                                                                                    if i.get('Id'):
                                                                                        ol_qb_id = int(
                                                                                            i.get('Id'))
                                                                                    else:
                                                                                        ol_qb_id = 0

                                                                                    if i.get('SalesItemLineDetail').get('UnitPrice'):
                                                                                        sp = i.get('SalesItemLineDetail').get(
                                                                                            'UnitPrice')
                                                                                    else:
                                                                                        sp = 0

                                                                                    if 'Description' in i and i.get('Description'):
                                                                                        description = i.get(
                                                                                            'Description')
                                                                                    else:
                                                                                        description = 'NA'

                                                                                    create_po = self.env['sale.order.line'].search(
                                                                                        ['&', ('product_id', '=', res_product.id),
                                                                                        (('order_id', '=', sale_order.id))], limit=1)

                                                                                    if create_po:
                                                                                        res = create_po.update({

                                                                                            'product_id': res_product.id,
                                                                                            'name': description,
                                                                                            'product_uom_qty': quantity,
                                                                                            'tax_ids': custom_tax_id_id,
                                                                                            'qb_id': ol_qb_id,
                                                                                            # 'product_uom': 1,
                                                                                            'price_unit': sp,
                                                                                        })
                                                                                    if create_po:
                                                                                        # company.quickbooks_last_sale_imported_id = int(
                                                                                        #     cust.get('Id'))
                                                                                        if company.import_sale_order_by_date:
                                                                                            date_format = '%Y-%m-%d'
                                                                                            if company.sale_order_import_by == 'crt_dt':
                                                                                                date_string = cust.get('MetaData').get(
                                                                                                    'CreateTime')[:10]
                                                                                            elif company.sale_order_import_by == 'updt_dt':
                                                                                                date_string = cust.get('MetaData').get(
                                                                                                    'LastUpdatedTime')[:10]
                                                                                            else:
                                                                                                date_string = cust.get('TxnDate')

                                                                                            date_object = datetime.strptime(date_string,
                                                                                                                            date_format).date()
                                                                                            company.import_sale_order_date = date_object

                                                                                else:
                                                                                    '''CODE FOR NEW LINE IN EXISTING SALE ORDER'''
                                                                                    _logger.info(
                                                                                        "Code for new line in existing sale order")
                                                                                    res_product = self.env['product.product'].search(
                                                                                        [('qbo_product_id', '=',
                                                                                        i.get('SalesItemLineDetail').get(
                                                                                            'ItemRef').get(
                                                                                            'value'))], limit=1)

                                                                                    if res_product:
                                                                                        dict_l = {}
                                                                                        if i.get('Id'):
                                                                                            dict_l['qb_id'] = int(
                                                                                                i.get('Id'))

                                                                                        # if discount_amt > 0:
                                                                                        #     dict_l['discount'] = discount_amt

                                                                                        if i.get('SalesItemLineDetail').get(
                                                                                                'TaxCodeRef'):

                                                                                            tax_val = i.get('SalesItemLineDetail').get(
                                                                                                'TaxCodeRef').get(
                                                                                                'value')
                                                                                            if tax_val == 'TAX':

                                                                                                dict_l[
                                                                                                    'tax_ids'] = custom_tax_id
                                                                                            else:
                                                                                                dict_l[
                                                                                                    'tax_ids'] = None

                                                                                        dict_l[
                                                                                            'order_id'] = sale_order.id
                                                                                        # dict_l['order_id'] = sale_order.id

                                                                                        dict_l[
                                                                                            'product_id'] = res_product.id

                                                                                        if i.get('SalesItemLineDetail').get('Qty'):
                                                                                            dict_l['product_uom_qty'] = i.get(
                                                                                                'SalesItemLineDetail').get('Qty')
                                                                                            # cust.get('Line')[0].get('SalesItemLineDetail').get('Qty')
                                                                                        else:
                                                                                            dict_l[
                                                                                                'product_uom_qty'] = 0

                                                                                        if i.get('SalesItemLineDetail').get(
                                                                                                'UnitPrice'):
                                                                                            dict_l['price_unit'] = i.get(
                                                                                                'SalesItemLineDetail').get('UnitPrice')
                                                                                        else:
                                                                                            dict_l[
                                                                                                'price_unit'] = 0

                                                                                        if i.get('Description'):
                                                                                            dict_l['name'] = i.get(
                                                                                                'Description')
                                                                                        else:
                                                                                            dict_l[
                                                                                                'name'] = 'NA'

                                                                                        # dict_l['product_uom'] = 1
                                                                                        _logger.info(
                                                                                            "Sale order line of update is ----> {}".format(
                                                                                                dict_l))
                                                                                        create_p = self.env[
                                                                                            'sale.order.line'].create(dict_l)
                                                                                        _logger.info(
                                                                                            "Sale order line of creation is {}".format(
                                                                                                create_p))
                                                                                        # if create_p:
                                                                                        #     company.quickbooks_last_sale_imported_id = int(
                                                                                        #         cust.get('Id'))

                                                                            else:
                                                                                _logger.info(
                                                                                    'Product ' + str(
                                                                                        i.get('SalesItemLineDetail').get('ItemRef').get(

                                                                                            'name')) + ' is not defined in Odoo. Sale Order ' + ' Name : ' + cust.get(
                                                                                        'DocNumber'))
                                                            except Exception as e:
                                                                raise ValidationError("Error while updating sale order for QBO ID {}: {}".format(cust.get('Id'), str(e)))
                                                    except Exception as e:
                                                        raise ValidationError("Error processing sale order with QBO ID {}: {}".format(cust.get('Id'), str(e)))
                                            except Exception as e:
                                                _logger.error("Failed to process estimate with QBO ID {}: {}".format(cust.get('Id'), str(e)))
                                                raise ValidationError("Failed to process estimate with QBO ID {}: {}".format(cust.get('Id'), str(e)))
                                        company.quickbooks_last_sale_imported_id = max_result + int(
                                            company.quickbooks_last_sale_imported_id)
                                        success_form = self.env.ref(
                                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                                    else:
                                        _logger.info(
                                            "It seems that all of the Sales Order are already imported!")
                    except ValidationError as ve:
                        _logger.error("ValidationError for company {}: {}".format(company.name, str(ve)))
                        raise ve
                    except Exception as e:
                        _logger.error("Unexpected error for company {}: {}".format(company.name, str(e)))
                        raise ValidationError("Unexpected error occurred for company {}: {}".format(company.name, str(e)))
        except ValidationError as ve:
            raise UserError(f"Validation Error: {str(ve)}")
        except Exception as e:
            raise UserError(f"Unexpected Error: {str(e)}")

    # --------------------------------- INVOICE  -----------------------------
    @api.model
    def check_if_lines_present(self, cust):
        if cust.get('Line'):
            for i in cust.get('Line'):
                if i.get('SalesItemLineDetail'):
                    return True
                else:
                    return False
        else:
            return False

    def import_transfer(self):
        try:
            if self:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user"))
                if not company:
                    company = self.env.company
                if company.import_trns_by_date:
                    query = f"select * from Transfer WHERE TxnDate >= '{company.import_trns_date}' order by Id MAXRESULTS {company.limit}"
                    # company.import_trns_date = fields.Date.today()
                else:
                    query = f"select * from Transfer order by Id STARTPOSITION {company.quickbooks_last_trns_imported_id} MAXRESULTS {company.limit}"
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/query?%squery=%s' % (
                    'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
                data = requests.request('GET', url, headers=url_str.get('headers'))
                _logger.info(
                    "Transfer data is ---------------> {}".format(data.text))
                if data.status_code == 200:
                    _logger.info(
                        "Data for importing transfer payments in odoo is ---> {}".format(data.text))
                    max_result = self.env['account.payment'].create_transfer(data, company=company)
                    if max_result:
                        company.quickbooks_last_trns_imported_id = max_result + int(
                            company.quickbooks_last_trns_imported_id)
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                else:
                    raise UserError("Empty data")
                    _logger.warning(_('Empty data'))
            else:
                companys = self.env.companies
                for company in companys:
                    company = self
                    companys = self.env['res.users'].search(
                        [('id', '=', self._uid)]).company_ids
                    if not company in companys:
                        raise ValidationError(
                            _("Company is not allowed for user"))
                    if not company:
                        company = self.env.company
                    if company.import_trns_by_date:
                        query = "select * from Transfer WHERE TxnDate >= '%s' order by Id " % (
                            company.import_trns_date)
                        company.import_trns_date = fields.Date.today()
                    else:
                        query = "select * From Transfer WHERE Id > '%s' order by Id" % (
                            company.quickbooks_last_trns_imported_id)
                    url_str = company.get_import_query_url()
                    url = url_str.get('url') + '/query?%squery=%s' % (
                        'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '',
                        query)
                    data = requests.request('GET', url, headers=url_str.get('headers'))
                    _logger.info(
                        "Transfer data is ---------------> {}".format(data.text))
                    if data.status_code == 200:
                        _logger.info(
                            "Data for importing transfer payments in odoo is ---> {}".format(data.text))
                        max_result = self.env['account.payment'].create_transfer(data, company=company)
                        if max_result:
                            company.quickbooks_last_trns_imported_id = max_result + int(
                                company.quickbooks_last_trns_imported_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                    else:
                        raise UserError("Empty data")
                        _logger.warning(_('Empty data'))
        except Exception as e:
            raise UserError(e)

    def import_deposit(self):
        try:
            if self:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user"))
                if not company:
                    company = self.env.company
                if company.import_cp_by_date:
                    query = f"select * from Deposit WHERE TxnDate >= '{company.import_dp_date}' order by Id MAXRESULTS {company.limit}"
                    company.import_dp_date = fields.Date.today()
                else:
                    query = f"select * from Deposit order by Id STARTPOSITION {company.quickbooks_last_dp_imported_id} MAXRESULTS {company.limit}"
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/query?%squery=%s' % (
                    'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
                data = requests.request('GET', url, headers=url_str.get('headers'))
                _logger.info(
                    "Deposit data is ---------------> {}".format(data.text))
                if data.status_code == 200:
                    _logger.info(
                        "Data for importing deposit payments in odoo is ---> {}".format(data.text))
                    max_result = self.env['account.payment'].create_deposit(data, company=company)
                    if max_result:
                        company.quickbooks_last_dp_imported_id = max_result + int(
                            company.quickbooks_last_dp_imported_id)
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                else:
                    raise UserError("Empty data")
                    _logger.warning(_('Empty data'))
            else:
                companys = self.env.companies
                for company in companys:
                    if company.import_cp_by_date:
                        query = "select * from Deposit WHERE TxnDate >= '%s' order by Id " % (
                            company.import_dp_date)
                        company.import_dp_date = fields.Date.today()
                    else:
                        query = "select * From Deposit WHERE Id > '%s' order by Id" % (
                            company.quickbooks_last_dp_imported_id)
                    url_str = company.get_import_query_url()
                    url = url_str.get('url') + '/query?%squery=%s' % (
                        'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '',
                        query)
                    data = requests.request('GET', url, headers=url_str.get('headers'))
                    _logger.info(
                        "Deposit data is ---------------> {}".format(data.text))
                    if data.status_code == 200:
                        _logger.info(
                            "Data for importing deposit payments in odoo is ---> {}".format(data.text))
                        max_result = self.env['account.payment'].create_deposit(data, company=company)
                        if max_result:
                            company.quickbooks_last_dp_imported_id = max_result + int(
                                company.quickbooks_last_dp_imported_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                    else:
                        raise UserError("Empty data")
                        _logger.warning(_('Empty data'))
        except Exception as e:
            raise UserError(e)

    def import_expenses(self):
        try:
            if self:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user"))
                if not company:
                    company = self.env.company
                if company.import_cp_by_date:
                    query = f"select * from Purchase WHERE TxnDate >= '{company.import_expns_date}' order by Id MAXRESULTS {company.limit}"
                    company.import_expns_date = fields.Date.today()
                else:
                    query = f"select * from Purchase order by Id STARTPOSITION {company.quickbooks_last_expns_imported_id} MAXRESULTS {company.limit}"
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/query?%squery=%s' % (
                    'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '', query)
                data = requests.request('GET', url, headers=url_str.get('headers'))
                _logger.info(
                    "Deposit data is ---------------> {}".format(data.text))

                if data.status_code == 200:
                    _logger.info(
                        "Data for importing expenses payments in odoo is ---> {}".format(data.text))
                    max_result = self.env['account.payment'].create_expenses(data, company=company)
                    if max_result:
                        company.quickbooks_last_expns_imported_id = max_result + int(
                            company.quickbooks_last_expns_imported_id)
                        success_form = self.env.ref(
                            'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                else:
                    raise UserError("Empty data")
                    _logger.warning(_('Empty data'))
            else:
                companys = self.env.companies
                for company in companys:
                    if company.import_cp_by_date:
                        query = "select * from Purchase WHERE TxnDate >= '%s' order by Id " % (
                            company.import_expns_date)
                        company.import_expns_date = fields.Date.today()
                    else:
                        query = "select * From Purchase WHERE Id > '%s' order by Id" % (
                            company.quickbooks_last_expns_imported_id)
                    url_str = company.get_import_query_url()
                    url = url_str.get('url') + '/query?%squery=%s' % (
                        'minorversion=' + url_str.get('minorversion') + '&' if url_str.get('minorversion') else '',
                        query)
                    data = requests.request('GET', url, headers=url_str.get('headers'))
                    _logger.info(
                        "Deposit data is ---------------> {}".format(data.text))

                    if data.status_code == 200:
                        _logger.info(
                            "Data for importing expenses payments in odoo is ---> {}".format(data.text))
                        max_result = self.env['account.payment'].create_expenses(data, company=company)
                        if max_result:
                            company.quickbooks_last_expns_imported_id = max_result + int(
                                company.quickbooks_last_expns_imported_id)
                            success_form = self.env.ref(
                                'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                    else:
                        raise UserError("Empty data")
                        _logger.warning(_('Empty data'))


        except Exception as e:
            raise UserError(e)

    def import_sales_receipt(self):
        try:
            if self:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user"))
                _logger.info("Sales Receipt")
                if not company:
                    company = self.env['res.users'].search(
                        [('id', '=', self._uid)]).company_id
                if not company:
                    company = self.env.company
                _logger.info("Company is-> {}".format(company))
                if company.access_token:
                    _logger.info(
                        "Access token is ---> {}".format(company.access_token))
                    headers = {}
                    headers['Authorization'] = 'Bearer ' + company.access_token
                    headers['accept'] = 'application/json'
                    headers['Content-Type'] = 'text/plain'
                    if company.import_sr_by_date:
                        query = f"select * from SalesReceipt WHERE TxnDate >= '{company.import_sr_date}' order by Id MAXRESULTS {company.limit}"
                        company.import_sr_date = fields.Date.today()
                    else:
                        query = f"select * from SalesReceipt order by Id STARTPOSITION {company.quickbooks_last_sales_receipt_imported_id} MAXRESULTS {company.limit}"
                    _logger.info("Query is -----> {}".format(query))
                    data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                            headers=headers)
                    _logger.info("************data{}".format(data.text))
                    if data.status_code == 200:
                        recs = []
                        parsed_data = json.loads(str(data.text))
                        if 'QueryResponse' in parsed_data:
                            SalesReceipt = parsed_data.get(
                                'QueryResponse').get('SalesReceipt', [])
                        else:
                            SalesReceipt = [parsed_data.get('SalesReceipt')] or []
                        if len(SalesReceipt) == 0:
                            self._cr.commit()
                            raise UserError(
                                "It seems that all of the Sales Receipt are already imported.")
                        if parsed_data:

                            if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get(
                                    'SalesReceipt'):
                                custom_tax_id_id = [[6, False, []]]

                                for cust in parsed_data.get('QueryResponse').get('SalesReceipt'):
                                    if "CustomerRef" in cust and cust.get('CustomerRef').get('value'):
                                        # searching sales order
                                        sale_receipt = self.env['account.move'].search(
                                            [('qbo_salesreceipt_id', '=', cust.get('Id')),
                                             ('company_id', '=', company.id)])

                                        # Update the last imported ID regardless of whether the receipt exists
                                        if int(cust.get('Id')) > company.quickbooks_last_sales_receipt_imported_id:
                                            # company.quickbooks_last_sales_receipt_imported_id = int(cust.get('Id'))
                                            self._cr.commit()

                                        _logger.info(
                                            "Sale order exists or not!!!!!---->{}".format(sale_receipt))
                                        if not sale_receipt:
                                            _logger.info("Creating Sales order...")
                                            _logger.info("Partner value is ---------------> {}".format(
                                                cust.get('CustomerRef').get('value')))
                                            res_partner = self.env['res.partner'].search(
                                                [('qbo_customer_id', '=', cust.get('CustomerRef').get('value')),
                                                 ('type', '=', 'contact'), ('company_id', '=', company.id)], limit=1)
                                            _logger.info(
                                                "RES PARTNER IS -> {}".format(res_partner))
                                            if not res_partner:
                                                raise ValidationError(
                                                    f"Partner Not Found in QBO ID {cust.get('CustomerRef').get('value')}")
                                            else:
                                                dict_s = {}
                                                dict_s[
                                                    'move_type'] = 'out_receipt'
                                                if cust.get('CurrencyRef').get('value'):
                                                    curr = cust.get(
                                                        'CurrencyRef').get('value')
                                                    currency = self.env['res.currency'].sudo().search(
                                                        [('active', 'in', [True, False]),
                                                         ('name', '=', curr)],
                                                        limit=1)
                                                    if currency and cust.get('ExchangeRate'):
                                                        rate_id = []
                                                        for rate in currency.rate_ids:
                                                            rate_id.append(str(rate.name))
                                                        if cust.get('TxnDate') in rate_id:
                                                            for rate in currency.rate_ids:
                                                                if str(rate.name) == cust.get('TxnDate'):
                                                                    if not rate.inverse_company_rate == cust.get(
                                                                            'ExchangeRate'):
                                                                        rate.inverse_company_rate = cust.get(
                                                                            'ExchangeRate')
                                                        else:
                                                            self.env['res.currency.rate'].create({
                                                                'name': cust.get('TxnDate'),
                                                                'inverse_company_rate': cust.get('ExchangeRate'),
                                                                'currency_id': currency.id,
                                                                'company_id': company.id,
                                                            })
                                                        self._cr.commit()
                                                if not currency.active:
                                                    currency.active = True
                                                dict_s[
                                                    'currency_id'] = currency.id

                                                # Update tax state
                                                if 'GlobalTaxCalculation' in cust and cust.get('GlobalTaxCalculation'):
                                                    if cust.get('GlobalTaxCalculation') == 'TaxExcluded':
                                                        dict_s[
                                                            'tax_state'] = 'exclusive'
                                                    elif cust.get('GlobalTaxCalculation') == 'TaxInclusive':
                                                        dict_s[
                                                            'tax_state'] = 'inclusive'
                                                    elif cust.get('GlobalTaxCalculation') == 'NotApplicable':
                                                        dict_s[
                                                            'tax_state'] = 'notapplicable'

                                                if 'Id' in cust and cust.get('Id'):
                                                    dict_s[
                                                        'partner_id'] = res_partner.id
                                                    # dict_s['state'] = 'sale'
                                                    dict_s['qbo_salesreceipt_id'] = cust.get(
                                                        'Id')

                                                if 'DocNumber' in cust and cust.get('DocNumber'):
                                                    pass
                                                    # dict_s['qbo_invoice_name'] = cust.get(
                                                    #     'DocNumber')

                                                if 'TotalAmt' in cust and cust.get('TotalAmt'):
                                                    dict_s['amount_total'] = cust.get(
                                                        'TotalAmt')

                                                if 'TxnDate' in cust and cust.get('TxnDate'):
                                                    dict_s['invoice_date'] = cust.get(
                                                        'TxnDate')

                                                ele_in_list = len(cust.get('Line'))
                                                dict_t = cust.get(
                                                    'Line')[ele_in_list - 1]
                                                _logger.info(
                                                    "Dictionary before creating is----> {}".format(dict_t))
                                                now = datetime.now()
                                                _logger.info(
                                                    "Dictionary is--->{}:".format(dict_s))
                                                if cust.get("DepositToAccountRef") and cust.get(
                                                        "DepositToAccountRef").get(
                                                    "value"):
                                                    account_1 = self.env['account.account'].search(
                                                        [('qbo_id', '=', cust.get("DepositToAccountRef").get("value")),
                                                         ('company_ids', '=', company.id)],
                                                        limit=1)
                                                    if not account_1:
                                                        raise ValidationError(
                                                            _(f'Account Not Found QBO account ID {cust.get("DepositToAccountRef").get("value")}for sales receipt id is {cust.get("Id")}'))
                                                    else:
                                                        journal_1 = self.env['account.journal'].search(
                                                            [('default_account_id', '=', account_1.id),
                                                             ('company_id', '=', company.id)],
                                                            limit=1)
                                                        if not journal_1:
                                                            # Save the changes immediately after each record
                                                            raise ValidationError(
                                                                _(f'Configure Account QBO ID {cust.get("DepositToAccountRef").get("name")} In Journal For Payment'))
                                                else:
                                                    raise ValidationError(
                                                        _(f'Deposit Account Not found for sales receipt qbo id is {cust.get("Id")}'))
                                                dict_s.update({'company_id': company.id})
                                                so_obj = self.env[
                                                    'account.move'].create(dict_s)

                                                if so_obj:
                                                    self._cr.commit()
                                                    _logger.info(
                                                        "WRITING QBO ID TO SALE Receipt {}".format(so_obj.id))
                                                    so_obj.write(
                                                        {'qbo_salesreceipt_id': cust.get('Id')})
                                                    _logger.info(
                                                        "Object is --->{}".format(so_obj))
                                                    _logger.info(
                                                        'Sale Receipt Created...!!! :: %s', cust.get('Id'))
                                                # ///////////////////////////////////////////////////////////////
                                                custom_tax_id = None
                                                discount_per = 0
                                                for i in cust.get('Line'):
                                                    if i.get('DetailType') == 'SubTotalLineDetail':
                                                        sub_total = i.get('Amount')
                                                    if "DiscountLineDetail" in i:
                                                        if i.get('DiscountLineDetail').get('PercentBased'):
                                                            if i.get("DiscountLineDetail").get('DiscountPercent'):
                                                                discount_per = i.get('DiscountLineDetail').get(
                                                                    'DiscountPercent')
                                                        else:
                                                            if sub_total > 0:
                                                                total_amount = (i.get('Amount') / sub_total) * 100
                                                                discount_per = abs(total_amount)
                                                for i in cust.get('Line'):
                                                    _logger.info(
                                                        "Particular instance is ------------> {}".format(i))

                                                    if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):

                                                        if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                            _logger.info(
                                                                "Transaction data!!!")
                                                            if i.get('SalesItemLineDetail').get('TaxCodeRef').get(
                                                                    'value'):
                                                                qb_tax_id = i.get('SalesItemLineDetail').get(
                                                                    'TaxCodeRef').get(
                                                                    'value')
                                                                record = self.env[
                                                                    'account.tax']
                                                                tax = record.search([('qbo_tax_id', '=', qb_tax_id),
                                                                                     ('type_tax_use', '=', 'sale'),
                                                                                     ('company_id', '=', company.id)])

                                                                if tax:
                                                                    custom_tax_id = [
                                                                        (6, 0, [tax.id])]
                                                                else:
                                                                    custom_tax_id = None

                                                    if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                                                        _logger.info(
                                                            "SalesItem Data")
                                                        res_product = self.env['product.product'].search(
                                                            [('qbo_product_id', '=',
                                                              i.get('SalesItemLineDetail').get('ItemRef').get('value')),
                                                             ('company_id', '=', company.id)],
                                                            limit=1)
                                                        shipping_line = False
                                                        if not res_product and i.get('SalesItemLineDetail').get(
                                                                'ItemRef').get(
                                                            'value') == 'SHIPPING_ITEM_ID':
                                                            if not self.delivery_carrier_id:
                                                                raise UserError(
                                                                    _('Please defined the Shipping Method in company!'))
                                                            res_product = self.delivery_carrier_id.product_id
                                                            shipping_line = True
                                                            dict_l = {}
                                                            dict_l[
                                                                'move_id'] = so_obj.id
                                                            dict_l[
                                                                'product_id'] = res_product.id
                                                            dict_l['quantity'] = 1
                                                            dict_l['price_unit'] = i.get('Amount')
                                                            dict_l['name'] = res_product.name
                                                            if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                tax_val = i.get('SalesItemLineDetail').get(
                                                                    'TaxCodeRef').get(
                                                                    'value')
                                                                if tax_val:
                                                                    dict_l[
                                                                        'tax_ids'] = custom_tax_id
                                                            _logger.info(
                                                                "Dictionary for sale order line is --------> {}".format(
                                                                    dict_l))
                                                            create_p = self.env[
                                                                'account.move.line'].create(dict_l)
                                                            self._cr.commit()
                                                            _logger.info(
                                                                "Sales Receipt line --------------->{}".format(
                                                                    create_p))
                                                            # if create_p:
                                                            #     company.quickbooks_last_sales_receipt_imported_id = int(
                                                            #         cust.get('Id'))

                                                        # if shipping_line:
                                                        #     continue
                                                        if res_product:
                                                            dict_l = {}
                                                            if discount_per:
                                                                dict_l['discount'] = discount_per
                                                            if i.get('Id'):
                                                                dict_l['qb_id'] = int(
                                                                    i.get('Id'))

                                                            if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                tax_val = i.get('SalesItemLineDetail').get(
                                                                    'TaxCodeRef').get(
                                                                    'value')
                                                                if tax_val:
                                                                    dict_l[
                                                                        'tax_ids'] = custom_tax_id
                                                                # else:
                                                                # dict_l['tax_ids']
                                                                # =

                                                            dict_l[
                                                                'move_id'] = so_obj.id

                                                            dict_l[
                                                                'product_id'] = res_product.id

                                                            if i.get('SalesItemLineDetail').get('Qty'):
                                                                dict_l['quantity'] = i.get(
                                                                    'SalesItemLineDetail').get(
                                                                    'Qty')
                                                            else:
                                                                dict_l[
                                                                    'quantity'] = 0.0

                                                            if i.get('SalesItemLineDetail').get('UnitPrice'):
                                                                dict_l['price_unit'] = i.get('SalesItemLineDetail').get(
                                                                    'UnitPrice')
                                                            else:
                                                                dict_l[
                                                                    'price_unit'] = 0.0

                                                            if i.get('Description'):
                                                                dict_l['name'] = i.get(
                                                                    'Description')
                                                            else:
                                                                dict_l[
                                                                    'name'] = 'NA'
                                                            _logger.info(
                                                                "Dictionary for sale order line is --------> {}".format(
                                                                    dict_l))
                                                            create_p = self.env[
                                                                'account.move.line'].create(dict_l)
                                                            self._cr.commit()
                                                            _logger.info(
                                                                "Sales Receipt line --------------->{}".format(
                                                                    create_p))
                                                            # if create_p:
                                                            #     company.quickbooks_last_sales_receipt_imported_id = int(
                                                            #         cust.get('Id'))
                                                        else:
                                                            raise UserError('Product ' + str(
                                                                i.get('SalesItemLineDetail').get('ItemRef').get(

                                                                    'name')) + ' is not defined in Odoo. Sales Receipt ' + ' Name : ' + cust.get(
                                                                'DocNumber'))
                                                so_obj.action_post()
                                                if so_obj.amount_residual:
                                                    # make payment
                                                    payment = self.env['account.payment.register'].with_context(
                                                        active_model='account.move', active_ids=so_obj.ids).create({
                                                        'journal_id': journal_1.id,
                                                    })._create_payments()
                                                    result = payment.qbo_salesreceipt_id = cust.get("Id")

                                                    # Update each payment record
                                                    for pay in payment:
                                                        pay.write({
                                                            'sale_receipt': True
                                                        })

                                                self._cr.commit()

                                        else:
                                            pass

                                company.quickbooks_last_sales_receipt_imported_id = parsed_data.get(
                                    'QueryResponse').get('maxResults') + int(
                                    company.quickbooks_last_sales_receipt_imported_id)

                                success_form = self.env.ref(
                                    'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                            else:
                                self._cr.commit()
                                raise UserError(
                                    "It seems that all of the Sales Order are already imported!")
            else:
                companys = self.env.companies
                for company in companys:
                    if company.access_token:
                        _logger.info(
                            "Access token is ---> {}".format(company.access_token))
                        headers = {}
                        headers['Authorization'] = 'Bearer ' + company.access_token
                        headers['accept'] = 'application/json'
                        headers['Content-Type'] = 'text/plain'
                        if company.import_sr_by_date:
                            query = "select * from SalesReceipt WHERE TxnDate >= '%s'" % (
                                company.import_sr_date)
                            company.import_sr_date = fields.Date.today()
                        else:
                            query = "select * from SalesReceipt WHERE Id > '%s' order by Id  STARTPOSITION %s MAXRESULTS %s " % (
                                company.quickbooks_last_sales_receipt_imported_id, company.start, company.limit)
                        _logger.info("Query is -----> {}".format(query))
                        data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                                headers=headers)
                        _logger.info("************data{}".format(data.text))
                        if data.status_code == 200:
                            recs = []
                            parsed_data = json.loads(str(data.text))
                            if 'QueryResponse' in parsed_data:
                                SalesReceipt = parsed_data.get(
                                    'QueryResponse').get('SalesReceipt', [])
                            else:
                                SalesReceipt = [parsed_data.get('SalesReceipt')] or []
                            if len(SalesReceipt) == 0:
                                self._cr.commit()
                                raise UserError(
                                    "It seems that all of the Sales Receipt are already imported.")
                            if parsed_data:

                                if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get(
                                        'SalesReceipt'):
                                    custom_tax_id_id = [[6, False, []]]

                                    for cust in parsed_data.get('QueryResponse').get('SalesReceipt'):
                                        if "CustomerRef" in cust and cust.get('CustomerRef').get('value'):
                                            # searching sales order
                                            sale_receipt = self.env['account.move'].search(
                                                [('qbo_salesreceipt_id', '=', cust.get('Id')),
                                                 ('company_id', '=', company.id)])
                                            _logger.info(
                                                "Sale order exists or not!!!!!---->{}".format(sale_receipt))
                                            if not sale_receipt:
                                                _logger.info("Creating Sales order...")
                                                _logger.info("Partner value is ---------------> {}".format(
                                                    cust.get('CustomerRef').get('value')))
                                                res_partner = self.env['res.partner'].search(
                                                    [('qbo_customer_id', '=', cust.get('CustomerRef').get('value')),
                                                     ('type', '=', 'contact'), ('company_id', '=', company.id)],
                                                    limit=1)
                                                _logger.info(
                                                    "RES PARTNER IS -> {}".format(res_partner))
                                                if not res_partner:
                                                    raise ValidationError(
                                                        f"Partner Not Found in QBO ID {cust.get('CustomerRef').get('value')}")
                                                else:
                                                    dict_s = {}
                                                    dict_s[
                                                        'move_type'] = 'out_receipt'
                                                    if cust.get('CurrencyRef').get('value'):
                                                        curr = cust.get(
                                                            'CurrencyRef').get('value')
                                                        currency = self.env['res.currency'].sudo().search(
                                                            [('active', 'in', [True, False]),
                                                             ('name', '=', curr)],
                                                            limit=1)
                                                        if currency and cust.get('ExchangeRate'):
                                                            rate_id = []
                                                            for rate in currency.rate_ids:
                                                                rate_id.append(str(rate.name))
                                                            if cust.get('TxnDate') in rate_id:
                                                                for rate in currency.rate_ids:
                                                                    if str(rate.name) == cust.get('TxnDate'):
                                                                        if not rate.inverse_company_rate == cust.get(
                                                                                'ExchangeRate'):
                                                                            rate.inverse_company_rate = cust.get(
                                                                                'ExchangeRate')
                                                            else:
                                                                self.env['res.currency.rate'].create({
                                                                    'name': cust.get('TxnDate'),
                                                                    'inverse_company_rate': cust.get('ExchangeRate'),
                                                                    'currency_id': currency.id,
                                                                    'company_id': company.id,
                                                                })
                                                            self._cr.commit()
                                                    if not currency.active:
                                                        currency.active = True
                                                    dict_s[
                                                        'currency_id'] = currency.id

                                                    # Update tax state
                                                    if 'GlobalTaxCalculation' in cust and cust.get(
                                                            'GlobalTaxCalculation'):
                                                        if cust.get('GlobalTaxCalculation') == 'TaxExcluded':
                                                            dict_s[
                                                                'tax_state'] = 'exclusive'
                                                        elif cust.get('GlobalTaxCalculation') == 'TaxInclusive':
                                                            dict_s[
                                                                'tax_state'] = 'inclusive'
                                                        elif cust.get('GlobalTaxCalculation') == 'NotApplicable':
                                                            dict_s[
                                                                'tax_state'] = 'notapplicable'

                                                    if 'Id' in cust and cust.get('Id'):
                                                        dict_s[
                                                            'partner_id'] = res_partner.id
                                                        # dict_s['state'] = 'sale'
                                                        dict_s['qbo_salesreceipt_id'] = cust.get(
                                                            'Id')

                                                    if 'DocNumber' in cust and cust.get('DocNumber'):
                                                        pass
                                                        # dict_s['qbo_invoice_name'] = cust.get(
                                                        #     'DocNumber')

                                                    if 'TotalAmt' in cust and cust.get('TotalAmt'):
                                                        dict_s['amount_total'] = cust.get(
                                                            'TotalAmt')

                                                    if 'TxnDate' in cust and cust.get('TxnDate'):
                                                        dict_s['invoice_date'] = cust.get(
                                                            'TxnDate')

                                                    ele_in_list = len(cust.get('Line'))
                                                    dict_t = cust.get(
                                                        'Line')[ele_in_list - 1]
                                                    _logger.info(
                                                        "Dictionary before creating is----> {}".format(dict_t))
                                                    now = datetime.now()
                                                    _logger.info(
                                                        "Dictionary is--->{}:".format(dict_s))
                                                    if cust.get("DepositToAccountRef") and cust.get(
                                                            "DepositToAccountRef").get(
                                                        "value"):
                                                        account_1 = self.env['account.account'].search(
                                                            [('qbo_id', '=',
                                                              cust.get("DepositToAccountRef").get("value")),
                                                             ('company_ids', '=', company.id)],
                                                            limit=1)
                                                        if not account_1:
                                                            raise ValidationError(
                                                                _(f'Account Not Found QBO account ID {cust.get("DepositToAccountRef").get("value")}for sales receipt id is {cust.get("Id")}'))
                                                        else:
                                                            journal_1 = self.env['account.journal'].search(
                                                                [('default_account_id', '=', account_1.id),
                                                                 ('company_id', '=', company.id)],
                                                                limit=1)
                                                            if not journal_1:
                                                                raise ValidationError(
                                                                    _(f'Configure Account QBO ID {cust.get("DepositToAccountRef").get("name")} In Journal For Payment'))
                                                    else:
                                                        raise ValidationError(
                                                            _(f'Deposit Account NOt found for sales receipt qbo id is {cust.get("Id")}'))
                                                    dict_s.update({'company_id': company.id})
                                                    so_obj = self.env[
                                                        'account.move'].create(dict_s)

                                                    if so_obj:
                                                        self._cr.commit()
                                                        _logger.info(
                                                            "WRITING QBO ID TO SALE Receipt {}".format(so_obj.id))
                                                        so_obj.write(
                                                            {'qbo_salesreceipt_id': cust.get('Id')})
                                                        _logger.info(
                                                            "Object is --->{}".format(so_obj))
                                                        _logger.info(
                                                            'Sale Receipt Created...!!! :: %s', cust.get('Id'))
                                                    # ///////////////////////////////////////////////////////////////
                                                    custom_tax_id = None
                                                    discount_per = 0
                                                    for i in cust.get('Line'):
                                                        if i.get('DetailType') == 'SubTotalLineDetail':
                                                            sub_total = i.get('Amount')
                                                        if "DiscountLineDetail" in i:
                                                            if i.get('DiscountLineDetail').get('PercentBased'):
                                                                if i.get("DiscountLineDetail").get('DiscountPercent'):
                                                                    discount_per = i.get('DiscountLineDetail').get(
                                                                        'DiscountPercent')
                                                            else:
                                                                if sub_total > 0:
                                                                    total_amount = (i.get('Amount') / sub_total) * 100
                                                                    discount_per = abs(total_amount)
                                                    for i in cust.get('Line'):
                                                        _logger.info(
                                                            "Particular instance is ------------> {}".format(i))

                                                        if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):

                                                            if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                _logger.info(
                                                                    "Transaction data!!!")
                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef').get(
                                                                        'value'):
                                                                    qb_tax_id = i.get('SalesItemLineDetail').get(
                                                                        'TaxCodeRef').get(
                                                                        'value')
                                                                    record = self.env[
                                                                        'account.tax']
                                                                    tax = record.search([('qbo_tax_id', '=', qb_tax_id),
                                                                                         ('type_tax_use', '=', 'sale'),
                                                                                         ('company_id', '=',
                                                                                          company.id)])

                                                                    if tax:
                                                                        custom_tax_id = [
                                                                            (6, 0, [tax.id])]
                                                                    else:
                                                                        custom_tax_id = None

                                                        if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                                                            _logger.info(
                                                                "SalesItem Data")
                                                            res_product = self.env['product.product'].search(
                                                                [('qbo_product_id', '=',
                                                                  i.get('SalesItemLineDetail').get('ItemRef').get(
                                                                      'value')),
                                                                 ('company_id', '=', company.id)],
                                                                limit=1)
                                                            shipping_line = False
                                                            if not res_product and i.get('SalesItemLineDetail').get(
                                                                    'ItemRef').get(
                                                                'value') == 'SHIPPING_ITEM_ID':
                                                                if not self.delivery_carrier_id:
                                                                    raise UserError(
                                                                        _('Please defined the Shipping Method in company!'))
                                                                res_product = self.delivery_carrier_id.product_id
                                                                shipping_line = True
                                                                dict_l = {}
                                                                dict_l[
                                                                    'move_id'] = so_obj.id
                                                                dict_l[
                                                                    'product_id'] = res_product.id
                                                                dict_l['quantity'] = 1
                                                                dict_l['price_unit'] = i.get('Amount')
                                                                dict_l['name'] = res_product.name
                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                    tax_val = i.get('SalesItemLineDetail').get(
                                                                        'TaxCodeRef').get(
                                                                        'value')
                                                                    if tax_val:
                                                                        dict_l[
                                                                            'tax_ids'] = custom_tax_id
                                                                _logger.info(
                                                                    "Dictionary for sale order line is --------> {}".format(
                                                                        dict_l))
                                                                create_p = self.env[
                                                                    'account.move.line'].create(dict_l)
                                                                self._cr.commit()
                                                                _logger.info(
                                                                    "Sales Receipt line --------------->{}".format(
                                                                        create_p))
                                                                # if create_p:
                                                                #     company.quickbooks_last_sales_receipt_imported_id = int(
                                                                #         cust.get('Id'))

                                                            # if shipping_line:
                                                            #     continue
                                                            if res_product:
                                                                dict_l = {}
                                                                if discount_per:
                                                                    dict_l['discount'] = discount_per
                                                                if i.get('Id'):
                                                                    dict_l['qb_id'] = int(
                                                                        i.get('Id'))

                                                                if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                                                                    tax_val = i.get('SalesItemLineDetail').get(
                                                                        'TaxCodeRef').get(
                                                                        'value')
                                                                    if tax_val:
                                                                        dict_l[
                                                                            'tax_ids'] = custom_tax_id
                                                                    # else:
                                                                    # dict_l['tax_ids']
                                                                    # =

                                                                dict_l[
                                                                    'move_id'] = so_obj.id

                                                                dict_l[
                                                                    'product_id'] = res_product.id

                                                                if i.get('SalesItemLineDetail').get('Qty'):
                                                                    dict_l['quantity'] = i.get(
                                                                        'SalesItemLineDetail').get(
                                                                        'Qty')
                                                                else:
                                                                    dict_l[
                                                                        'quantity'] = 0.0

                                                                if i.get('SalesItemLineDetail').get('UnitPrice'):
                                                                    dict_l['price_unit'] = i.get(
                                                                        'SalesItemLineDetail').get(
                                                                        'UnitPrice')
                                                                else:
                                                                    dict_l[
                                                                        'price_unit'] = 0.0

                                                                if i.get('Description'):
                                                                    dict_l['name'] = i.get(
                                                                        'Description')
                                                                else:
                                                                    dict_l[
                                                                        'name'] = 'NA'
                                                                _logger.info(
                                                                    "Dictionary for sale order line is --------> {}".format(
                                                                        dict_l))
                                                                create_p = self.env[
                                                                    'account.move.line'].create(dict_l)
                                                                self._cr.commit()
                                                                _logger.info(
                                                                    "Sales Receipt line --------------->{}".format(
                                                                        create_p))
                                                                # if create_p:
                                                                #     company.quickbooks_last_sales_receipt_imported_id = int(
                                                                #         cust.get('Id'))
                                                            else:
                                                                raise UserError('Product ' + str(
                                                                    i.get('SalesItemLineDetail').get('ItemRef').get(

                                                                        'name')) + ' is not defined in Odoo. Sales Receipt ' + ' Name : ' + cust.get(
                                                                    'DocNumber'))
                                                    so_obj.action_post()
                                                    if so_obj.amount_residual:
                                                        # make payment
                                                        payment = self.env['account.payment.register'].with_context(
                                                            active_model='account.move', active_ids=so_obj.ids).create({
                                                            'journal_id': journal_1.id,
                                                        })._create_payments()
                                                        result = payment.qbo_salesreceipt_id = cust.get("Id")

                                                        # Update each payment record
                                                        for pay in payment:
                                                            pay.write({
                                                                'sale_receipt': True
                                                            })

                                                    self._cr.commit()

                                            else:
                                                pass

                                    success_form = self.env.ref(
                                        'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                                else:
                                    self._cr.commit()
                                    raise UserError(
                                        "It seems that all of the Sales Order are already imported!")
                company.quickbooks_last_sales_receipt_imported_id = parsed_data.get(
                    'QueryResponse').get('maxResults') + int(
                    company.quickbooks_last_sales_receipt_imported_id)

        except Exception as e:
            raise UserError(e)

    # -------------------------------------------- PURCHASE  ORDER  ----------

    # @api.multi

    def import_purchase_order(self):
        try:
            _logger.info("inside purchase order *********************")
            company = self
            companys = self.env['res.users'].search([('id', '=', self._uid)]).company_ids
            if not company in companys:
                company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
            if not company:
                company = self.env.company

            if company.access_token:
                headers = {
                    'Authorization': 'Bearer ' + company.access_token,
                    'accept': 'application/json',
                    'Content-Type': 'text/plain'
                }

                # Build query based on company settings
                if company.import_purchase_order_by_date:
                    if self.sale_order_import_by == 'crt_dt':
                        query = f"select * from PurchaseOrder WHERE Metadata.CreateTime >= '{company.import_purchase_order_date}' order by Id MAXRESULTS {company.limit}"
                    elif self.sale_order_import_by == 'other_dt':
                        query = f"select * from PurchaseOrder WHERE TxnDate >= '{company.import_purchase_order_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from PurchaseOrder WHERE Metadata.LastUpdatedTime >= '{company.import_purchase_order_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from PurchaseOrder order by Id STARTPOSITION {company.quickbooks_last_purchase_imported_id} MAXRESULTS {company.limit}"

                data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                        headers=headers)

                if data.status_code == 200:
                    parsed_data = json.loads(str(data.text))
                    if parsed_data and parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get(
                            'PurchaseOrder'):
                        # Handle mapping context if present
                        if self.import_mapping_po_field and self.import_mapping_po_id and self.env.context.get(
                                'mapping'):
                            if parsed_data.get('QueryResponse', False).get('PurchaseOrder', False):
                                self.import_mapping_po_id.with_context({'import': True}).json_data = parsed_data.get(
                                    'QueryResponse').get('PurchaseOrder')
                            else:
                                raise UserError(f"Empty data from QuickBooks during mapping purchase order {purchase_order_data.get('Id')}.")
                            return

                        for purchase_order_data in parsed_data.get('QueryResponse').get('PurchaseOrder'):
                            try:
                                # Get all lines
                                all_lines = purchase_order_data.get('Line', [])

                                # First identify category lines exclusively
                                category_lines = [line for line in all_lines if
                                                line.get('DetailType') == 'AccountBasedExpenseLineDetail']

                                # Then identify valid item-based lines (making sure to exclude category lines)
                                valid_lines = [line for line in all_lines if
                                            line.get('ItemBasedExpenseLineDetail') and line not in category_lines]

                                # Everything else is invalid
                                invalid_lines = [line for line in all_lines if
                                                line not in valid_lines and line not in category_lines]

                                # Log and skip this purchase order if no valid lines found
                                if not valid_lines and not (self.import_category_detail and category_lines):
                                    # Create detailed message about invalid lines
                                    invalid_details = []
                                    for line in invalid_lines:
                                        line_detail = f"Line Detail Type: {line.get('DetailType', 'Unknown')}"
                                        if line.get('Description'):
                                            line_detail += f", Description: {line.get('Description')}"
                                        invalid_details.append(line_detail)

                                    log_message = f"Skipping PO {purchase_order_data.get('DocNumber', purchase_order_data.get('Id'))}"
                                    log_message += f"Invalid Lines Found ({len(invalid_lines)}):\n"
                                    log_message += "\n".join(f"- {detail}" for detail in invalid_details)

                                    error = self.env['qbo.logger'].sudo().create({
                                        'odoo_name': 'Purchase Order Import',
                                        'odoo_object': 'purchase.order.line',
                                        'message': f"Skipping Purchase order  {purchase_order_data.get('DocNumber', purchase_order_data.get('Id'))}",
                                        'activity': 'Importing Purchase Order from QBO',
                                        'created_date': fields.Datetime.now(),
                                    })
                                    self.env.cr.commit()
                                    continue

                                existing_po = self.env['purchase.order'].search([
                                    ('quickbook_id', '=', purchase_order_data.get('Id')),
                                    ('company_id', '=', company.id)
                                ])

                                if not existing_po:
                                    # Find vendor
                                    vendor = self.env['res.partner'].search([
                                        ('qbo_vendor_id', '=', purchase_order_data.get('VendorRef').get('value')),
                                        ('company_id', '=', company.id)
                                    ], limit=1)

                                    if not vendor:
                                        vendor_name = purchase_order_data.get('VendorRef').get('name')
                                        vendor_id = purchase_order_data.get('VendorRef').get('value')
                                        raise UserError(
                                            f"Vendor '{vendor_name}' with QuickBooks ID {vendor_id} not found in Odoo. Please add the vendor before importing purchase orders.")

                                    # Create PO header
                                    po_vals = {
                                        'partner_id': vendor.id,
                                        'quickbook_id': purchase_order_data.get('Id'),
                                        'company_id': company.id,
                                        'state': 'purchase' if purchase_order_data.get('POStatus') else 'draft',
                                        'name': purchase_order_data.get('DocNumber', False)
                                    }

                                    # Handle creation date
                                    if purchase_order_data.get('MetaData').get('CreateTime'):
                                        date_string = purchase_order_data.get('MetaData').get('CreateTime')
                                        dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
                                        po_vals['date_approve'] = dt.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

                                    new_po = self.env['purchase.order'].create(po_vals)

                                    # Create PO lines only for item-based expenses
                                    for line in valid_lines:
                                        product = self.env['product.product'].search([
                                            ('qbo_product_id', '=',
                                            line.get('ItemBasedExpenseLineDetail').get('ItemRef').get('value')),
                                            ('company_id', '=', company.id)
                                        ], limit=1)

                                        if not product:
                                            product_name = line.get('ItemBasedExpenseLineDetail', {}).get('ItemRef',
                                                                                                        {}).get('name',
                                                                                                                'Unknown Product')
                                                                                                                
                                            _logger.error(
                                                f'Product {product_name} is not defined in Odoo. Purchase order number: {purchase_order_data.get("DocNumber")}')

                                        line_vals = {
                                            'order_id': new_po.id,
                                            'product_id': product.id,
                                            'product_qty': line.get('ItemBasedExpenseLineDetail').get('Qty', 1.0),
                                            'price_unit': line.get('ItemBasedExpenseLineDetail').get('UnitPrice', 0.0),
                                            'name': line.get('Description', 'NA'),
                                            'date_planned': new_po.date_order,
                                            # 'product_uom': 1,
                                            'qb_id': int(line.get('Id')) if line.get('Id') else False
                                        }
                                        self.env['purchase.order.line'].create(line_vals)

                                    # Create purchase order line only for category details
                                    if self.import_category_detail:
                                        for line in category_lines:
                                            account = self.env['account.account'].search([
                                                ('qbo_id', '=',
                                                line.get('AccountBasedExpenseLineDetail').get('AccountRef').get('value')),
                                                # ('company_id', '=', company.id)
                                            ], limit=1)

                                            if not account:
                                                account_name = line.get('AccountBasedExpenseLineDetail', {}).get(
                                                    'AccountRef', {}).get('name', 'Unknown Account')
                                                raise UserError(
                                                    f'Account {account_name} is not defined in Odoo. Purchase order number: {purchase_order_data.get("DocNumber")}')

                                            line_vals = {
                                                'order_id': new_po.id,
                                                'price_subtotal': line.get('Amount', 0.0),
                                                'name': f"{line.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get('name', 'Category Expense')}",
                                                'date_planned': new_po.date_order,
                                                # 'product_uom': 1,
                                                'product_qty': 1,
                                                'price_unit': line.get('Amount', 0.0),
                                                'qb_id': int(line.get('Id')) if line.get('Id') else False
                                            }
                                            self.env['purchase.order.line'].create(line_vals)

                                    if new_po:
                                        if purchase_order_data.get("LinkedTxn"):
                                            for rec in purchase_order_data.get("LinkedTxn"):
                                                if rec.get('TxnType') == 'Purchase':
                                                    invoice_obj = self.env['account.move'].search(
                                                        [('qbo_invoice_id', '=', rec.get("TxnId"))], limit=1)
                                                    prnt_tran_type = 'Bill'
                                                    child_tran_type = 'Purchase Order'
                                                    if new_po:
                                                        # Ensure invoice_obj is valid
                                                        if invoice_obj:
                                                            # Directly update the invoice_ids field in sale.order
                                                            new_po.write({'invoice_ids': [(4, invoice_obj.id)]})

                                                            # Update the invoice_lines field in sale.order.line
                                                            for line in new_po.order_line:
                                                                line.write({'invoice_lines': [(4, line_id) for line_id in
                                                                                            invoice_obj.invoice_line_ids.ids]})

                                                            # Log the linking for debugging purposes
                                                            _logger.info(
                                                                f"Linked {prnt_tran_type} {invoice_obj.id} to {child_tran_type} {new_po.id}")
                                                            # Commit the transaction
                                                        else:
                                                            _logger.error(f"{prnt_tran_type} object is not valid")
                                                    else:
                                                        _logger.error(f"{prnt_tran_type} object is not valid")

                                # Update last imported ID and date
                                # company.quickbooks_last_purchase_imported_id = purchase_order_data.get('Id')
                                if company.import_purchase_order_by_date:
                                    date_format = '%Y-%m-%d'
                                    if company.purchase_order_import_by == 'crt_dt':
                                        date_string = purchase_order_data.get('MetaData').get('CreateTime')[:10]
                                    elif company.purchase_order_import_by == 'updt_dt':
                                        date_string = purchase_order_data.get('MetaData').get('LastUpdatedTime')[:10]
                                    else:
                                        date_string = purchase_order_data.get('TxnDate')
                                    company.import_purchase_order_date = datetime.strptime(date_string, date_format).date()
                            except ValidationError as ve:
                                _logger.error(f"ValidationError in PO import: {str(ve)}")
                                raise ve
                            except Exception as po_ex:
                                _logger.error(f"Unhandled exception in processing PO {purchase_order_data.get('Id')}: {str(po_ex)}")
                                # raise UserError(f"Error in PO ID {purchase_order_data.get('Id')}: {str(po_ex)}")
                        max_result = parsed_data.get('QueryResponse').get('maxResults')
                        company.quickbooks_last_purchase_imported_id = max_result + int(
                            company.quickbooks_last_purchase_imported_id)
                        # Show success message
                        success_form = self.env.ref('pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
                    else:
                        _logger.info("No new purchase orders found to import!")
                        raise UserError(_("It seems that all of the Purchase Order are already imported."))
        except (UserError, ValidationError):
            raise
        except Exception as e:
            raise UserError(f"Unexpected error during PO import: {str(e)}")

    # def import_purchase_order(self):
    #     try:
    #         _logger.info("inside purchase order *********************")
    #         company = self
    #         companys = self.env['res.users'].search(
    #             [('id', '=', self._uid)]).company_ids
    #         if not company in companys:
    #             company = self.env['res.users'].search(
    #                 [('id', '=', self._uid)]).company_id
    #         if not company:
    #             company = self.env.company
    #         if company.access_token:
    #             headers = {}
    #             headers['Authorization'] = 'Bearer ' + company.access_token
    #             headers['accept'] = 'application/json'
    #             headers['Content-Type'] = 'text/plain'
    #             if company.import_purchase_order_by_date:
    #                 if company.purchase_order_import_by == 'crt_dt':
    #                     query = "select * from purchaseorder WHERE MetaData.CreateTime >= '%s' AND ID >= '%s' order by Id" % (
    #                         company.import_purchase_order_date, company.quickbooks_last_purchase_imported_id)
    #                 elif company.purchase_order_import_by == 'other_dt':
    #                     query = "select * from purchaseorder WHERE TxnDate >= '%s' AND ID >= '%s' order by Id" % (
    #                         company.import_purchase_order_date, company.quickbooks_last_purchase_imported_id)
    #                 else:
    #                     query = "select * from purchaseorder WHERE MetaData.LastUpdatedTime >= '%s' AND ID >= '%s' order by Id" % (
    #                         company.import_purchase_order_date, company.quickbooks_last_purchase_imported_id)
    #
    #             else:
    #                 query = "select * from purchaseorder WHERE Id > '%s' order by Id" % (
    #                     company.quickbooks_last_purchase_imported_id)
    #             data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
    #                                     headers=headers)
    #             if data.status_code == 200:
    #                 recs = []
    #                 parsed_data = json.loads(str(data.text))
    #                 if parsed_data:
    #                     if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('PurchaseOrder'):
    #                         if self.import_mapping_po_field and self.import_mapping_po_id and self.env.context.get(
    #                                 'mapping'):
    #                             if parsed_data.get('QueryResponse', False).get('PurchaseOrder', False):
    #                                 self.import_mapping_po_id.with_context({'import': True}).json_data = \
    #                                     parsed_data.get('QueryResponse').get('PurchaseOrder')
    #                             else:
    #                                 raise UserError("Empty data")
    #                             return
    #                         for cust in parsed_data.get('QueryResponse').get('PurchaseOrder'):
    #
    #                             purchase_order = self.env['purchase.order'].search(
    #                                 [('quickbook_id', '=', cust.get('Id')), ('company_id', '=', company.id)])
    #
    #                             if not purchase_order:
    #                                 res_partner = self.env['res.partner'].search(
    #                                     [('qbo_vendor_id', '=', cust.get('VendorRef').get('value')),
    #                                      ('company_id', '=', company.id)], limit=1)
    #
    #                                 if not res_partner:
    #                                     vendor_name = cust.get('VendorRef').get('name')
    #                                     vendor_id = cust.get('VendorRef').get('value')
    #                                     raise UserError(
    #                                         f"Vendor '{vendor_name}' with QuickBooks ID {vendor_id} not found in Odoo. Please add the vendor before importing purchase orders.")
    #
    #                                 if res_partner:
    #                                     dict_s = {}
    #                                     if cust.get('MetaData').get('CreateTime'):
    #                                         date_string = cust.get('MetaData').get('CreateTime')
    #                                         dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
    #                                         # Convert datetime object to Odoo format
    #                                         odoo_date_string = dt.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    #                                         dict_s[
    #                                             'date_approve'] = odoo_date_string
    #
    #                                     if cust.get('Id'):
    #                                         dict_s[
    #                                             'partner_id'] = res_partner.id
    #                                         dict_s['quickbook_id'] = cust.get(
    #                                             'Id')
    #                                     else:
    #                                         dict_s['parent_id'] = cust.get(
    #                                             'VendorRef').get('name')
    #
    #                                     if cust.get('POStatus'):
    #                                         dict_s['state'] = 'purchase'
    #
    #                                     if cust.get('DocNumber'):
    #                                         dict_s['name'] = cust.get(
    #                                             'DocNumber')
    #                                     dict_s.update({'company_id': company.id})
    #                                     so_obj = self.env[
    #                                         'purchase.order'].create(dict_s)
    #                                     if so_obj:
    #                                         _logger.info(
    #                                             'PO Created Successfully :: %s', so_obj)
    #
    #                                     for i in cust.get('Line'):
    #                                         if i.get('ItemBasedExpenseLineDetail'):
    #                                             res_product = self.env['product.product'].search(
    #                                                 [('qbo_product_id', '=',
    #                                                   i.get('ItemBasedExpenseLineDetail').get('ItemRef').get('value')),
    #                                                  ('company_id', '=', company.id)],
    #                                                 limit=1)
    #                                             _logger.info("=======res_product=======%s",res_product)
    #
    #                                             if res_product:
    #                                                 dict_l = {}
    #
    #                                                 dict_l.clear()
    #                                                 dict_l[
    #                                                     'order_id'] = so_obj.id
    #                                                 dict_l[
    #                                                     'product_id'] = res_product.id
    #
    #                                                 if i.get('ItemBasedExpenseLineDetail').get('Qty'):
    #                                                     dict_l['product_qty'] = i.get('ItemBasedExpenseLineDetail').get(
    #                                                         'Qty')
    #
    #                                                 if i.get('Id'):
    #                                                     dict_l['qb_id'] = int(
    #                                                         i.get('Id'))
    #                                                     dict_l[
    #                                                         'date_planned'] = so_obj.date_order
    #
    #                                                 dict_l['product_uom'] = 1
    #
    #                                                 if i.get('ItemBasedExpenseLineDetail').get('UnitPrice'):
    #                                                     dict_l['price_unit'] = i.get('ItemBasedExpenseLineDetail').get(
    #                                                         'UnitPrice')
    #                                                 else:
    #                                                     dict_l[
    #                                                         'price_unit'] = 0.0
    #
    #                                                 if i.get('Description'):
    #                                                     dict_l['name'] = i.get(
    #                                                         'Description')
    #                                                 else:
    #                                                     dict_l['name'] = 'NA'
    #                                                 create_p = self.env[
    #                                                     'purchase.order.line'].create(dict_l)
    #
    #                                                 if create_p:
    #                                                     company.quickbooks_last_purchase_imported_id = cust.get(
    #                                                         'Id')
    #                                                     if company.import_purchase_order_by_date:
    #                                                         date_format = '%Y-%m-%d'
    #                                                         if company.purchase_order_import_by == 'crt_dt':
    #                                                             date_string = cust.get('MetaData').get(
    #                                                                 'CreateTime')[:10]
    #                                                         elif company.purchase_order_import_by == 'updt_dt':
    #                                                             date_string = cust.get('MetaData').get(
    #                                                                 'LastUpdatedTime')[:10]
    #                                                         else:
    #                                                             date_string = cust.get('TxnDate')
    #
    #                                                         date_object = datetime.strptime(date_string,
    #                                                                                         date_format).date()
    #                                                         company.import_purchase_order_date = date_object
    #                                                     self._cr.commit()
    #
    #                                             else:
    #                                                 product_name = i.get('ItemBasedExpenseLineDetail', {}).get(
    #                                                     'ItemRef', {}).get('name', 'Unknown Product')
    #                                                 po_number = cust.get('DocNumber', 'Unknown')
    #
    #
    #                                                 raise UserError(
    #                                                     'Product ' + str(
    #                                                         i.get('ItemBasedExpenseLineDetail').get('ItemRef').get(
    #                                                             'name')) +
    #                                                     ' is not defined in Odoo. Purchase order number1 :' + cust.get(
    #                                                         'DocNumber')
    #                                                 )
    #
    #                             else:
    #
    #                                 company.quickbooks_last_purchase_imported_id = cust.get(
    #                                     'Id')
    #                                 if company.import_purchase_order_by_date:
    #                                     date_format = '%Y-%m-%d'
    #                                     if company.purchase_order_import_by == 'crt_dt':
    #                                         date_string = cust.get('MetaData').get(
    #                                             'CreateTime')[:10]
    #                                     elif company.purchase_order_import_by == 'updt_dt':
    #                                         date_string = cust.get('MetaData').get(
    #                                             'LastUpdatedTime')[:10]
    #                                     else:
    #                                         date_string = cust.get('TxnDate')
    #
    #                                     date_object = datetime.strptime(date_string,
    #                                                                     date_format).date()
    #                                     company.import_purchase_order_date = date_object
    #
    #                                 _logger.info(
    #                                     "All Purchase order seems to be imported!")
    #                         success_form = self.env.ref(
    #                             'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
    #                     else:
    #                         raise UserError(
    #                             "It seems that all of the Purchase Orders are already imported!")
    #     except Exception as e:
    #         raise UserError(e)

    # ---------------------------------VENDOR BILLS---------------------------

    # @api.multi
    def import_vendor_bill_1(self):
        _logger.info("inside vendor bill ****************************")
        company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
        if company.access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + self.access_token
            headers['accept'] = 'application/json'
            headers['Content-Type'] = 'text/plain'
            if company.import_bills_by_date:
                query = "select * from bill WHERE Metadata.CreateTime >= '%s' AND ID >= '%s' order by Id" % (
                    company.import_bills_date, company.quickbooks_last_vendor_bill_imported_id)
            else:
                query = "select * from bill WHERE Id > '%s' order by Id" % (
                    company.quickbooks_last_vendor_bill_imported_id)

            data = requests.request('GET', self.url + str(self.realm_id) + "/query?query=" + query,
                                    headers=headers)
            if data.status_code == 200:
                _logger.info("Vendor bill data is -------------------->{}".format(data.text))
                recs = []
                parsed_data = json.loads(str(data.text))
                if parsed_data:
                    _logger.info("Parsed data for vendor bill is -------------> {}".format(parsed_data))
                    if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('Bill'):

                        for cust in parsed_data.get('QueryResponse').get('Bill'):
                            # searching sales order
                            line_present = self.check_if_lines_present_vendor_bill(cust)
                            _logger.info('ORDER LINES NOT PRESENT IN VENDOR BILL :: %s', line_present)
                            if not line_present:
                                continue

                            bill = self.env['account.move'].search(
                                [('qbo_invoice_id', '=', cust.get('Id'))])
                            _logger.info("Bill search is --------------> {}".format(bill))
                            if not bill:

                                _logger.info("No bill.")
                                _logger.info(
                                    "Vendor value is -----------------> {}".format(cust.get('VendorRef').get('value')))
                                res_partner = self.env['res.partner'].search(
                                    [('qbo_vendor_id', '=', cust.get('VendorRef').get('value'))], limit=1)
                                _logger.info("Res partner is -------------------> {}".format(res_partner))
                                if res_partner:
                                    dict_i = {}
                                    if cust.get('Id'):
                                        dict_i['partner_id'] = res_partner.id

                                        dict_i['qbo_invoice_id'] = cust.get('Id')

                                        dict_i['company_id'] = self.id

                                        dict_i['type'] = 'in_invoice'

                                    if cust.get('CurrencyRef'):
                                        if cust.get('CurrencyRef').get('value'):
                                            currency = self.env['res.currency'].search(
                                                [('name', '=', cust.get('CurrencyRef').get('value'))], limit=1)
                                            dict_i['currency_id'] = currency.id

                                    if res_partner.customer_rank:
                                        sale = self.env['account.journal'].search([('type', 'in', ['sale', 'cash'])],
                                                                                  limit=1)
                                        if sale:
                                            dict_i['journal_id'] = sale.id
                                            _logger.info("Journal was attached..")
                                        else:
                                            _logger.info("No Journal was found..")
                                    if res_partner.supplier_rank:
                                        purchase = self.env['account.journal'].search(
                                            [('type', 'in', ['purchase', 'cash'])],
                                            limit=1)
                                        if purchase:
                                            dict_i['journal_id'] = purchase.id
                                            _logger.info("Journal attached..")
                                        else:
                                            _logger.info("No Journal was found...")

                                        # dict_i['journal_id'] = 1
                                        dict_i['reference_type'] = ''
                                    # if cust.get('DocNumber'):
                                    #     dict_i['number'] = cust.get('DocNumber')
                                    if cust.get('Balance'):
                                        dict_i['state'] = 'draft'
                                        # dict_i['residual'] = cust.get('Balance')
                                        # dict_i['residual_signed'] = cust.get('Balance')
                                        dict_i['amount_residual'] = cust.get('Balance')
                                        dict_i['amount_residual_signed'] = cust.get('Balance')
                                    else:
                                        dict_i['amount_residual'] = 0.0
                                        dict_i['amount_residual_signed'] = 0.0

                                    if cust.get('DueDate'):
                                        dict_i['invoice_date_due'] = cust.get('DueDate')
                                    if cust.get('TxnDate'):
                                        dict_i['invoice_date'] = cust.get('TxnDate')

                                    ele_in_list = len(cust.get('Line'))
                                    dict_t = cust.get('Line')[ele_in_list - 1]

                                    if cust.get('TotalAmt'):
                                        dict_i['amount_total'] = cust.get('TotalAmt')
                                    _logger.info("Dictionary for creation of vendor bill is ---> {}".format(dict_i))
                                    invoice_obj = self.env['account.move'].create(dict_i)
                                    _logger.info("Invoice object is --------> {}".format(invoice_obj))
                                    if invoice_obj:
                                        _logger.info('Vendor Bill Created Successfully :: %s', cust.get('Id'))

                                    custom_tax_id = None

                                    for i in cust.get('Line'):
                                        dict_ol = {}

                                        if i.get('ItemBasedExpenseLineDetail'):
                                            res_product = self.env['product.product'].search([('qbo_product_id', '=',
                                                                                               i.get(
                                                                                                   'ItemBasedExpenseLineDetail').get(
                                                                                                   'ItemRef').get(
                                                                                                   'value'))], limit=1)
                                            if res_product:
                                                dict_ol.clear()
                                                dict_ol['move_id'] = invoice_obj.id
                                                dict_ol['product_id'] = res_product.id

                                                if i.get('Id'):
                                                    dict_ol['qb_id'] = int(i.get('Id'))
                                                    dict_ol['tax_ids'] = None

                                                if i.get('ItemBasedExpenseLineDetail').get('Qty'):
                                                    dict_ol['quantity'] = i.get('ItemBasedExpenseLineDetail').get('Qty')

                                                if i.get('ItemBasedExpenseLineDetail').get('UnitPrice'):
                                                    dict_ol['price_unit'] = float(
                                                        i.get('ItemBasedExpenseLineDetail').get('UnitPrice'))
                                                else:
                                                    if not i.get('ItemBasedExpenseLineDetail').get('Qty'):
                                                        dict_ol['quantity'] = 1
                                                        dict_ol['price_unit'] = float(
                                                            i.get('Amount'))
                                                    else:
                                                        dict_ol['price_unit'] = 0.0

                                                if i.get('Description'):
                                                    dict_ol['name'] = i.get('Description')
                                                else:
                                                    dict_ol['name'] = 'NA'
                                                if res_product.property_account_expense_id:
                                                    dict_ol['account_id'] = res_product.property_account_expense_id.id
                                                else:
                                                    dict_ol[
                                                        'account_id'] = res_product.categ_id.property_account_expense_categ_id.id
                                                _logger.info(
                                                    "Creation for invoice lines ---------------> {}".format(dict_ol))
                                                create_p = self.env['account.move.line'].create(dict_ol)
                                                _logger.info("After creation ---------->{}".format(create_p))
                                                # if create_p:
                                                #     self.quickbooks_last_vendor_bill_imported_id = cust.get('Id')

                                        if i.get('AccountBasedExpenseLineDetail'):
                                            dict_al = {}
                                            dict_al['move_id'] = invoice_obj.id
                                            if i.get('Id'):
                                                dict_al['qb_id'] = int(i.get('Id'))
                                                dict_al['tax_ids'] = None
                                                dict_al['quantity'] = 1

                                            if i.get('Amount'):
                                                dict_al['price_unit'] = float(i.get('Amount'))
                                            else:
                                                dict_al['price_unit'] = 0.0

                                            if i.get('Description'):
                                                dict_al['name'] = i.get('Description')
                                            else:
                                                dict_al['name'] = 'NA'

                                            if i.get('AccountBasedExpenseLineDetail').get('AccountRef'):
                                                account = self.env['account.account'].search([('qbo_id', '=', i.get(
                                                    'AccountBasedExpenseLineDetail').get('AccountRef').get('value'))],
                                                                                             limit=1)
                                                dict_al['account_id'] = account.id

                                            create_p = self.env['account.move.line'].create(dict_al)
                                            if create_p:
                                                # company.quickbooks_last_vendor_bill_imported_id = cust.get('Id')
                                                if company.import_bills_by_date:
                                                    date_format = '%Y-%m-%d'
                                                    if company.vendor_bill_import_by == 'crt_dt':
                                                        date_string = cust.get('MetaData').get(
                                                            'CreateTime')[:10]
                                                    elif company.vendor_bill_import_by == 'updt_dt':
                                                        date_string = cust.get('MetaData').get(
                                                            'LastUpdatedTime')[:10]
                                                    else:
                                                        date_string = cust.get('TxnDate')
                                                    date_object = datetime.strptime(date_string,
                                                                                    date_format).date()
                                                    company.import_bills_date = date_object
                                    if cust.get('Balance') == 0:
                                        if invoice_obj.state == 'draft':
                                            invoice_obj.action_invoice_open()
                                            invoice_obj.write({
                                                'amount_residual': cust.get('Balance'),
                                                'amount_residual_signed': cust.get('Balance')
                                            })
                            else:
                                _logger.info("Bill exists!!!")
                                res_partner = self.env['res.partner'].search(
                                    [('qbo_vendor_id', '=', cust.get('VendorRef').get('value'))], limit=1)
                                _logger.info("Partner is -----------> {}".format(res_partner))
                                if res_partner:
                                    dict_i = {}

                                    if cust.get('Id'):
                                        dict_i['partner_id'] = res_partner.id
                                        dict_i['qbo_invoice_id'] = cust.get('Id')
                                        dict_i['company_id'] = self.id

                                        dict_i['type'] = 'in_invoice'
                                    if cust.get('CurrencyRef'):
                                        if cust.get('CurrencyRef').get('value'):
                                            currency = self.env['res.currency'].search(
                                                [('name', '=', cust.get('CurrencyRef').get('value'))], limit=1)
                                            dict_i['currency_id'] = currency.id

                                    if res_partner.customer_rank:
                                        sale = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                                        if sale:
                                            dict_i['journal_id'] = sale.id
                                    if res_partner.supplier_rank:
                                        purchase = self.env['account.journal'].search([('type', '=', 'purchase')],
                                                                                      limit=1)
                                        if purchase:
                                            dict_i['journal_id'] = purchase.id

                                        dict_i['reference_type'] = ''
                                    if cust.get('TotalAmt'):
                                        dict_i['total'] = cust.get('TotalAmt')

                                    if not cust.get('Balance'):
                                        if bill.state == 'draft':
                                            bill.action_invoice_open()
                                        # dict_i['state'] = 'paid'

                                    if cust.get('Balance'):
                                        dict_i['amount_residual'] = cust.get('Balance')
                                        dict_i['amount_residual_signed'] = cust.get('Balance')
                                    else:
                                        dict_i['amount_residual'] = 0.0
                                        dict_i['amount_residual_signed'] = 0.0

                                    if cust.get('DueDate'):
                                        dict_i['invoice_date_due'] = cust.get('DueDate')
                                    if cust.get('TxnDate'):
                                        dict_i['invoice_date'] = cust.get('TxnDate')

                                    ele_in_list = len(cust.get('Line'))
                                    dict_t = cust.get('Line')[ele_in_list - 1]

                                    if cust.get('Amount'):
                                        dict_i['amount_total'] = cust.get('Amount')
                                    write_inv = bill.write(dict_i)
                                    if write_inv:
                                        _logger.info('Vendor Bill Updated Successfully :: %s', cust.get('Id'))

                                    bill._compute_residual()
                                    for i in cust.get('Line'):

                                        if i.get('ItemBasedExpenseLineDetail'):
                                            res_product = self.env['product.product'].search([('qbo_product_id', '=',
                                                                                               i.get(
                                                                                                   'ItemBasedExpenseLineDetail').get(
                                                                                                   'ItemRef').get(
                                                                                                   'value'))])
                                            if res_product:
                                                p_order_line = self.env['account.move.line'].search(
                                                    ['&', ('product_id', '=', res_product.id),
                                                     (('move_id', '=', bill.id))])

                                                if p_order_line:

                                                    if i.get('Id'):
                                                        ol_qb_id = int(i.get('Id'))

                                                    if i.get('ItemBasedExpenseLineDetail').get('Qty'):
                                                        qty = i.get('ItemBasedExpenseLineDetail').get('Qty')

                                                    if i.get('ItemBasedExpenseLineDetail').get('UnitPrice'):
                                                        sp = float(
                                                            i.get('ItemBasedExpenseLineDetail').get('UnitPrice'))
                                                    else:
                                                        if not i.get('ItemBasedExpenseLineDetail').get('Qty'):
                                                            qty = 1
                                                            sp = float(
                                                                i.get('Amount'))
                                                        else:
                                                            sp = 0.0

                                                    if i.get('Description'):
                                                        description = i.get('Description')
                                                    else:
                                                        description = 'NA'

                                                    # create_p = self.env['account.move.line'].write(dict_ol)

                                                    create_iv = self.env['account.move.line'].search(
                                                        ['&', ('qb_id', '=', int(i.get('Id'))),
                                                         (('move_id', '=', bill.id))])
                                                    if create_iv:
                                                        data_dict = {

                                                            'product_id': res_product.id,
                                                            'name': description,
                                                            'quantity': qty,
                                                            'qb_id': ol_qb_id,
                                                            'price_unit': sp,
                                                            'tax_ids': None,
                                                        }
                                                        if res_product.property_account_expense_id:
                                                            _logger.info("ATTACHING product expense account")
                                                            data_dict.update({
                                                                'account_id': res_product.property_account_expense_id.id})
                                                        else:
                                                            _logger.info("ATTACHING category expense account")
                                                            data_dict.update({
                                                                'account_id': res_product.categ_id.property_account_expense_categ_id.id})
                                                        res = create_iv.write(data_dict)

                                                    if create_iv:
                                                        _logger.info("Invoice created...")
                                                        # company.quickbooks_last_vendor_bill_imported_id = cust.get('Id')
                                                        if company.import_bills_by_date:
                                                            date_format = '%Y-%m-%d'
                                                            if company.vendor_bill_import_by == 'crt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'CreateTime')[:10]
                                                            elif company.vendor_bill_import_by == 'updt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'LastUpdatedTime')[:10]
                                                            else:
                                                                date_string = cust.get('TxnDate')
                                                            date_object = datetime.strptime(date_string,
                                                                                            date_format).date()
                                                            company.import_bills_date = date_object

                                                else:
                                                    dict_ol = {}

                                                    dict_ol.clear()
                                                    dict_ol['move_id'] = bill.id
                                                    dict_ol['product_id'] = res_product.id

                                                    if i.get('Id'):
                                                        dict_ol['qb_id'] = int(i.get('Id'))
                                                        dict_ol['tax_ids'] = None

                                                    if i.get('ItemBasedExpenseLineDetail').get('Qty'):
                                                        dict_ol['quantity'] = i.get('ItemBasedExpenseLineDetail').get(
                                                            'Qty')

                                                    if i.get('ItemBasedExpenseLineDetail').get('UnitPrice'):
                                                        dict_ol['price_unit'] = float(
                                                            i.get('ItemBasedExpenseLineDetail').get('UnitPrice'))
                                                    else:
                                                        if not i.get('ItemBasedExpenseLineDetail').get('Qty'):
                                                            dict_ol['quantity'] = 1
                                                            dict_ol['price_unit'] = float(
                                                                i.get('Amount'))
                                                        else:
                                                            dict_ol['price_unit'] = 0.0

                                                    # dict_ol['date_due'] = cust.get('TxnDate')

                                                    if i.get('Description'):
                                                        dict_ol['name'] = i.get('Description')
                                                    else:
                                                        dict_ol['name'] = 'NA'

                                                    if res_product.property_account_expense_id:
                                                        dict_ol[
                                                            'account_id'] = res_product.property_account_expense_id.id
                                                        _logger.info("Attached from product ")
                                                    else:
                                                        dict_ol[
                                                            'account_id'] = res_product.categ_id.property_account_expense_categ_id.id

                                                    create_p = self.env['account.move.line'].create(dict_ol)
                                                    if create_p:
                                                        # company.quickbooks_last_vendor_bill_imported_id = cust.get('Id')
                                                        if company.import_bills_by_date:
                                                            date_format = '%Y-%m-%d'
                                                            if company.vendor_bill_import_by == 'crt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'CreateTime')[:10]
                                                            elif company.vendor_bill_import_by == 'updt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'LastUpdatedTime')[:10]
                                                            else:
                                                                date_string = cust.get('TxnDate')
                                                            date_object = datetime.strptime(date_string,
                                                                                            date_format).date()
                                                            company.import_bills_date = date_object
                                        if i.get('AccountBasedExpenseLineDetail'):
                                            account_account = self.env['account.account'].search([('qbo_id', '=',
                                                                                                   i.get(
                                                                                                       'AccountBasedExpenseLineDetail').get(
                                                                                                       'AccountRef').get(
                                                                                                       'value'))])
                                            if account_account:
                                                a_order_line = self.env['account.move.line'].search(
                                                    ['&', ('account_id', '=', account_account.id),
                                                     (('move_id', '=', bill.id))])
                                                dict_al = {}
                                                if i.get('Id'):
                                                    dict_al['qb_id'] = int(i.get('Id'))
                                                    dict_al['tax_ids'] = None
                                                    dict_al['quantity'] = 1

                                                if i.get('Amount'):
                                                    dict_al['price_unit'] = float(i.get('Amount'))
                                                else:
                                                    dict_al['price_unit'] = 0.0

                                                if i.get('Description'):
                                                    dict_al['name'] = i.get('Description')
                                                else:
                                                    dict_al['name'] = 'NA'

                                                if i.get('AccountBasedExpenseLineDetail').get('AccountRef'):
                                                    account = self.env['account.account'].search([('qbo_id', '=', i.get(
                                                        'AccountBasedExpenseLineDetail').get('AccountRef').get(
                                                        'value'))])
                                                    if account:
                                                        dict_al['account_id'] = account.id
                                                        _logger.info(
                                                            "Attaching account id from AccountBasedExpenseLineDetail")
                                                    else:
                                                        _logger.error(
                                                            "Unable to fetch Account Based Expense Line Detail")

                                                if not a_order_line:
                                                    dict_al['move_id'] = bill.id
                                                    _logger.info(
                                                        "Account invoice line dict is ---------> {}".format(dict_al))
                                                    create_p = self.env['account.move.line'].create(dict_al)
                                                    if create_p:
                                                        _logger.info(
                                                            "Creation of invoice lines of vendor bills --------------- {}".format(
                                                                create_p))
                                                        # company.quickbooks_last_vendor_bill_imported_id = cust.get('Id')
                                                        if company.import_bills_by_date:
                                                            date_format = '%Y-%m-%d'
                                                            if company.vendor_bill_import_by == 'crt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'CreateTime')[:10]
                                                            elif company.vendor_bill_import_by == 'updt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'LastUpdatedTime')[:10]
                                                            else:
                                                                date_string = cust.get('TxnDate')
                                                            date_object = datetime.strptime(date_string,
                                                                                            date_format).date()
                                                            company.import_bills_date = date_object
                                                else:
                                                    _logger.info("Redirecting else part account.move.line")
                                                    create_p = self.env['account.move.line'].write(dict_al)
                                                    if create_p:
                                                        _logger.info(
                                                            "Updation  of invoice lines of vendor bills --------------- {}".format(
                                                                create_p))

                                                        # company.quickbooks_last_vendor_bill_imported_id = cust.get('Id')
                                                        if company.import_bills_by_date:
                                                            date_format = '%Y-%m-%d'
                                                            if company.vendor_bill_import_by == 'crt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'CreateTime')[:10]
                                                            elif company.vendor_bill_import_by == 'updt_dt':
                                                                date_string = cust.get('MetaData').get(
                                                                    'LastUpdatedTime')[:10]
                                                            else:
                                                                date_string = cust.get('TxnDate')
                                                            date_object = datetime.strptime(date_string,
                                                                                            date_format).date()
                                                            company.import_bills_date = date_object

            else:
                raise UserError("Empty Data")
                _logger.warning(_('Empty data'))

    ###################IMPORT CREDIT MEMO###########################################
    # @api.multi
    # def import_credit_memo_1(self):
    #     company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
    #
    #     if company.access_token:
    #         headers = {}
    #         headers['Authorization'] = 'Bearer ' + company.access_token
    #         headers['accept'] = 'application/json'
    #         headers['Content-Type'] = 'text/plain'
    #         if company.import_credit_memo_by_date:
    #             query = "select * from CreditMemo WHERE Metadata.CreateTime >= '%s' AND ID >= '%s' order by Id" % (
    #                 company.import_credit_memo_date, company.quickbooks_last_credit_note_imported_id)
    #         else:
    #             query = "select * from CreditMemo WHERE Id > '%s' order by Id" % (
    #                 company.quickbooks_last_credit_note_imported_id)
    #
    #         data = requests.request('GET', self.url + str(self.realm_id) + "/query?query=" + query,
    #                                 headers=headers)
    #         if data.status_code == 200:
    #             recs = []
    #             parsed_data = json.loads(str(data.text))
    #             count = 0
    #
    #             if parsed_data:
    #                 if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('CreditMemo'):
    #                     for cust in parsed_data.get('QueryResponse').get('CreditMemo'):
    #                         return_val = self.check_account_id(cust)
    #                         if return_val:
    #                             line_present = self.check_if_lines_present(cust)
    #                             _logger.info('ORDER LINES PRESENT IN INVOICE :: %s', line_present)
    #                             if not line_present:
    #                                 continue
    #
    #                             count = count + 1
    #                             account_invoice = self.env['account.move'].search(
    #                                 [('qbo_invoice_id', '=', cust.get('Id'))])
    #                             _logger.info("ACC invoice is -----> {}".format(account_invoice))
    #                             if not account_invoice:
    #
    #                                 res_partner = self.env['res.partner'].search(
    #                                     [('qbo_customer_id', '=', cust.get('CustomerRef').get('value'))])
    #                                 _logger.info("Partner is ---> {}".format(res_partner))
    #                                 if res_partner:
    #                                     dict_i = {}
    #
    #                                     if cust.get('Id'):
    #                                         dict_i['partner_id'] = res_partner.id
    #                                         dict_i['qbo_invoice_id'] = cust.get('Id')
    #                                         dict_i['type'] = 'out_refund'
    #
    #                                         # dict_i['name'] = "INVOICE"
    #                                         # dict_i['account_id'] = 0
    #                                         dict_i['company_id'] = self.id
    #
    #                                     if cust.get('CurrencyRef'):
    #                                         if cust.get('CurrencyRef').get('value'):
    #                                             currency = self.env['res.currency'].search(
    #                                                 [('name', '=', cust.get('CurrencyRef').get('value'))], limit=1)
    #                                             dict_i['currency_id'] = currency.id
    #
    #                                     if res_partner.customer_rank:
    #                                         sale = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
    #                                         if sale:
    #                                             dict_i['journal_id'] = sale.id
    #                                         else:
    #                                             sale = self.env['account.journal'].search([('type', '=', 'bank')],
    #                                                                                       limit=1)
    #                                             if sale:
    #                                                 dict_i['journal_id'] = sale.id
    #                                     if res_partner.supplier_rank:
    #                                         purchase = self.env['account.journal'].search([('type', '=', 'purchase')],
    #                                                                                       limit=1)
    #                                         if purchase:
    #                                             dict_i['journal_id'] = purchase.id
    #                                         else:
    #                                             purchase = self.env['account.journal'].search([('type', '=', 'bank')],
    #                                                                                           limit=1)
    #                                             if purchase:
    #                                                 dict_i['journal_id'] = purchase.id
    #
    #                                         # dict_i['journal_id'] = 1
    #                                         dict_i['reference_type'] = ''
    #
    #                                     if cust.get('DocNumber'):
    #                                         dict_i['name'] = cust.get('DocNumber')
    #                                         # dict_i['number'] = cust.get('DocNumber')
    #
    #                                     if cust.get('Balance'):
    #                                         dict_i['state'] = 'draft'
    #                                         dict_i['amount_residual'] = cust.get('Balance')
    #                                         dict_i['amount_residual_signed'] = cust.get('Balance')
    #                                         # dict_i['residual'] = cust.get('Balance')
    #                                         # dict_i['residual_signed'] = cust.get('Balance')
    #                                     else:
    #                                         dict_i['amount_residual'] = 0.0
    #                                         dict_i['amount_residual_signed'] = 0.0
    #
    #                                     if cust.get('DueDate'):
    #                                         dict_i['invoice_date_due'] = cust.get('DueDate')
    #                                     if cust.get('TxnDate'):
    #                                         dict_i['invoice_date'] = cust.get('TxnDate')
    #
    #                                     ele_in_list = len(cust.get('Line'))
    #                                     #       ele_in_list)
    #                                     dict_t = cust.get('Line')[ele_in_list - 1]
    #
    #                                     if cust.get('TotalAmt'):
    #                                         dict_i['total'] = cust.get('TotalAmt')
    #
    #                                     _logger.info("Dictionary for creation is ---> {}".format(dict_i))
    #                                     invoice_obj = self.env['account.move'].create(dict_i)
    #                                     _logger.info("Invoice obj is -----> {}".format(invoice_obj))
    #                                     if invoice_obj:
    #                                         #                                             self._cr.commit()
    #                                         _logger.info('Credit Memo  Created Successfully..!! :: %s', invoice_obj)
    #                                     custom_tax_id = None
    #
    #                                     for i in cust.get('Line'):
    #                                         dict_ol = {}
    #                                         if cust.get('TxnTaxDetail').get('TxnTaxCodeRef'):
    #                                             if cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value'):
    #
    #                                                 qb_tax_id = cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get(
    #                                                     'value')
    #
    #                                                 record = self.env['account.tax']
    #                                                 tax = record.search([('qbo_tax_id', '=', qb_tax_id)])
    #                                                 if tax:
    #                                                     custom_tax_id = [(6, 0, [tax.id])]
    #                                                     _logger.info("TAX ATTACHED {}".format(tax.id))
    #                                                 else:
    #                                                     custom_tax_id = None
    #
    #                                         if i.get('SalesItemLineDetail'):
    #                                             res_product = self.env['product.product'].search(
    #                                                 [('qbo_product_id', '=',
    #                                                   i.get('SalesItemLineDetail').get('ItemRef').get('value'))])
    #                                             if res_product:
    #
    #                                                 dict_ol.clear()
    #                                                 dict_ol['move_id'] = invoice_obj.id
    #
    #                                                 dict_ol['product_id'] = res_product.id
    #
    #                                                 if i.get('Id'):
    #                                                     dict_ol['qb_id'] = int(i.get('Id'))
    #
    #                                                 # ---------------------------TAX--------------------------------------
    #                                                 if i.get('SalesItemLineDetail').get('TaxCodeRef'):
    #
    #                                                     tax_val = i.get('SalesItemLineDetail').get(
    #                                                         'TaxCodeRef').get(
    #                                                         'value')
    #                                                     if tax_val == 'TAX':
    #
    #                                                         dict_ol['tax_ids'] = custom_tax_id
    #                                                     else:
    #                                                         dict_ol['tax_ids'] = None
    #
    #                                                 if i.get('SalesItemLineDetail').get('Qty'):
    #                                                     dict_ol['quantity'] = i.get('SalesItemLineDetail').get('Qty')
    #
    #                                                 if i.get('SalesItemLineDetail').get('UnitPrice'):
    #                                                     dict_ol['price_unit'] = float(
    #                                                         i.get('SalesItemLineDetail').get('UnitPrice'))
    #                                                 else:
    #                                                     if not i.get('SalesItemLineDetail').get('Qty'):
    #                                                         dict_ol['quantity'] = 1
    #                                                         dict_ol['price_unit'] = float(
    #                                                             i.get('Amount'))
    #                                                     else:
    #                                                         dict_ol['price_unit'] = 0
    #
    #                                                 if i.get('Description'):
    #                                                     dict_ol['name'] = i.get('Description')
    #                                                 else:
    #                                                     dict_ol['name'] = 'NA'
    #
    #                                                 if res_product.property_account_income_id:
    #                                                     dict_ol[
    #                                                         'account_id'] = res_product.property_account_income_id.id
    #                                                     _logger.info("PRODUCT has income account set")
    #                                                 else:
    #                                                     dict_ol[
    #                                                         'account_id'] = res_product.categ_id.property_account_income_categ_id.id
    #                                                     _logger.info(
    #                                                         "No Income account was set, taking from product category..")
    #                                                 if 'account_id' in dict_ol:
    #                                                     _logger.info("\n\n Invoice Line is  ---> {}".format(dict_ol))
    #                                                     create_p = self.env['account.move.line'].create(dict_ol)
    #                                                     if create_p:
    #                                                         self._cr.commit()
    #                                                         _logger.info("Invoice Line Committed!!!")
    #                                                         create_p.move_id._onchange_invoice_line_ids()
    #                                                         company.quickbooks_last_invoice_imported_id = cust.get('Id')
    #                                                         if self.import_invoice_by_date:
    #                                                             date_format = '%Y-%m-%d'
    #                                                             if self.sale_order_import_by == 'crt_dt':
    #                                                                 date_string = cust.get('MetaData').get(
    #                                                                     'CreateTime')[:10]
    #                                                             elif self.sale_order_import_by == 'updt_dt':
    #                                                                 date_string = cust.get('MetaData').get(
    #                                                                     'LastUpdatedTime')[:10]
    #                                                             else:
    #                                                                 date_string = cust.get('TxnDate')
    #
    #                                                             date_object = datetime.strptime(date_string,
    #                                                                                             date_format).date()
    #                                                             self.import_invoice_date = date_object
    #                                                     else:
    #                                                         _logger.error("Invoice line was not created.")
    #                                                 else:
    #                                                     _logger.error("NO ACCOUNT ID WAS ATTACHED !")
    #                                     if cust.get('Balance') == 0:
    #                                         if invoice_obj.state == 'draft':
    #                                             invoice_obj.action_invoice_open()
    #                                             if cust.get('DocNumber'):
    #                                                 invoice_obj.write({'name': cust.get('DocNumber'),
    #                                                                    'amount_residual': cust.get('Balance'),
    #                                                                    'amount_residual_signed': cust.get('Balance')})
    #
    #                             else:
    #                                 res_partner = self.env['res.partner'].search(
    #                                     [('qbo_customer_id', '=', cust.get('CustomerRef').get('value'))])
    #
    #                                 if res_partner:
    #                                     dict_i = {}
    #
    #                                     if cust.get('Id'):
    #                                         dict_i['partner_id'] = res_partner.id
    #                                         dict_i['qbo_invoice_id'] = cust.get('Id')
    #                                         # dict_i['name'] = "INVOICE"
    #                                         # dict_i['account_id'] = 0
    #                                         dict_i['company_id'] = self.id
    #                                         # dict_i['type'] = 'out_refund'
    #
    #                                     if cust.get('CurrencyRef'):
    #                                         if cust.get('CurrencyRef').get('value'):
    #                                             currency = self.env['res.currency'].search(
    #                                                 [('name', '=', cust.get('CurrencyRef').get('value'))], limit=1)
    #                                             dict_i['currency_id'] = currency.id
    #
    #                                     if res_partner.customer_rank:
    #                                         sale = self.env['account.journal'].search([('type', '=', 'sale')],
    #                                                                                   limit=1)
    #                                         if sale:
    #                                             dict_i['journal_id'] = sale.id
    #                                     if res_partner.supplier_rank:
    #                                         purchase = self.env['account.journal'].search(
    #                                             [('type', '=', 'purchase')],
    #                                             limit=1)
    #                                         if purchase:
    #                                             dict_i['journal_id'] = purchase.id
    #
    #                                         # dict_i['journal_id'] = 1
    #                                         dict_i['reference_type'] = ''
    #
    #                                     if cust.get('TotalAmt'):
    #                                         dict_i['total'] = cust.get('TotalAmt')
    #                                     if cust.get('DocNumber'):
    #                                         dict_i['name'] = cust.get('DocNumber')
    #                                         # dict_i['number'] = cust.get('DocNumber')
    #
    #                                     if cust.get('Balance'):
    #                                         dict_i['amount_residual'] = cust.get('Balance')
    #                                         dict_i['amount_residual_signed'] = cust.get('Balance')
    #                                     else:
    #                                         # dict_i['state'] = 'paid'
    #                                         dict_i['amount_residual'] = 0.0
    #                                         dict_i['amount_residual_signed'] = 0.0
    #                                         # dict_i['residual'] = 0.0
    #                                         # dict_i['residual_signed'] = 0.0
    #                                         if account_invoice.state == 'draft':
    #                                             account_invoice.action_invoice_open()
    #
    #                                     if cust.get('DueDate'):
    #                                         dict_i['invoice_date_due'] = cust.get('DueDate')
    #                                     if cust.get('TxnDate'):
    #                                         dict_i['invoice_date'] = cust.get('TxnDate')
    #
    #                                     ele_in_list = len(cust.get('Line'))
    #                                     dict_t = cust.get('Line')[ele_in_list - 1]
    #
    #                                     write_inv = account_invoice.write(dict_i)
    #                                     if write_inv:
    #                                         _logger.info('Credit Memo Updated Successfully..!! :: %s', cust.get('Id'))
    #
    #                                     account_invoice._onchange_invoice_line_ids()
    #
    #                                     custom_tax_id_id = None
    #                                     custom_tax_id = None
    #
    #                                     for i in cust.get('Line'):
    #                                         if cust.get('TxnTaxDetail'):
    #                                             if cust.get('TxnTaxDetail').get('TxnTaxCodeRef'):
    #                                                 if cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value'):
    #
    #                                                     qb_tax_id = cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get(
    #                                                         'value')
    #                                                     record = self.env['account.tax']
    #                                                     tax = record.search([('qbo_tax_id', '=', qb_tax_id)])
    #                                                     if tax:
    #                                                         custom_tax_id = [(6, 0, [tax.id])]
    #                                                     else:
    #                                                         custom_tax_id = None
    #
    #                                         if i.get('SalesItemLineDetail'):
    #                                             res_product = self.env['product.product'].search(
    #                                                 [('qbo_product_id', '=',
    #                                                   i.get('SalesItemLineDetail').get('ItemRef').get('value'))])
    #
    #                                             if res_product:
    #                                                 p_order_line = self.env['account.move.line'].search(
    #                                                     ['&', ('product_id', '=', res_product.id),
    #                                                      (('move_id', '=', account_invoice.id))])
    #
    #                                                 if p_order_line:
    #
    #                                                     if i.get('Id'):
    #                                                         ol_qb_id = int(i.get('Id'))
    #
    #                                                     if i.get('SalesItemLineDetail').get('Qty'):
    #                                                         qty = i.get('SalesItemLineDetail').get('Qty')
    #                                                     else:
    #                                                         qty = 0
    #
    #                                                     if i.get('SalesItemLineDetail').get('UnitPrice'):
    #                                                         sp = float(
    #                                                             i.get('SalesItemLineDetail').get('UnitPrice'))
    #                                                     else:
    #                                                         if not i.get('SalesItemLineDetail').get('Qty'):
    #                                                             qty = 1
    #                                                             sp = float(
    #                                                                 i.get('Amount'))
    #                                                         else:
    #                                                             sp = 0.0
    #
    #                                                     if i.get('SalesItemLineDetail').get('TaxCodeRef'):
    #
    #                                                         tax_val = i.get('SalesItemLineDetail').get(
    #                                                             'TaxCodeRef').get(
    #                                                             'value')
    #                                                         if tax_val == 'TAX':
    #
    #                                                             custom_tax_id_id = custom_tax_id
    #                                                         else:
    #                                                             custom_tax_id_id = None
    #
    #                                                     if i.get('Description'):
    #                                                         description = i.get('Description')
    #                                                     else:
    #                                                         description = 'NA'
    #
    #                                                     income_id = None
    #
    #                                                     if res_product.property_account_income_id.id:
    #                                                         income_id = res_product.property_account_income_id.id
    #                                                     else:
    #                                                         income_id = res_product.categ_id.property_account_income_categ_id.id
    #
    #                                                     # create_p = self.env['account.move.line'].write(dict_ol)
    #
    #                                                     create_iv = self.env['account.move.line'].search(
    #                                                         ['&', ('qb_id', '=', int(i.get('Id'))),
    #                                                          (('move_id', '=', account_invoice.id))])
    #                                                     # search([['qb_id', '=', i.get('Id')]])
    #                                                     if create_iv:
    #                                                         res = create_iv.write({
    #
    #                                                             'product_id': res_product.id,
    #                                                             'name': description,
    #                                                             'quantity': qty,
    #                                                             'account_id': income_id,
    #                                                             'qb_id': ol_qb_id,
    #                                                             'price_unit': sp,
    #                                                             'tax_ids': custom_tax_id_id,
    #                                                         })
    #
    #                                                     if create_iv:
    #                                                         company.quickbooks_last_credit_note_imported_id = cust.get(
    #                                                             'Id')
    #                                                         if company.import_credit_memo_by_date:
    #                                                             date_format = '%Y-%m-%d'
    #                                                             if company.credit_memo_import_by == 'crt_dt':
    #                                                                 date_string = cust.get('MetaData').get(
    #                                                                     'CreateTime')[:10]
    #                                                             elif company.credit_memo_import_by == 'updt_dt':
    #                                                                 date_string = cust.get('MetaData').get(
    #                                                                     'LastUpdatedTime')[:10]
    #                                                             else:
    #                                                                 date_string = cust.get('TxnDate')
    #
    #                                                             date_object = datetime.strptime(date_string,
    #                                                                                             date_format).date()
    #                                                             company.import_credit_memo_date = date_object
    #
    #                                                 else:
    #
    #                                                     dict_ol = {}
    #                                                     res_product_acc = self.env['product.product'].search([])
    #
    #                                                     dict_ol.clear()
    #                                                     dict_ol['move_id'] = account_invoice.id
    #                                                     dict_ol['product_id'] = res_product.id
    #
    #                                                     if i.get('Id'):
    #                                                         dict_ol['qb_id'] = int(i.get('Id'))
    #
    #                                                     if i.get('SalesItemLineDetail').get('TaxCodeRef'):
    #
    #                                                         tax_val = i.get('SalesItemLineDetail').get(
    #                                                             'TaxCodeRef').get(
    #                                                             'value')
    #                                                         if tax_val == 'TAX':
    #                                                             dict_ol['tax_ids'] = custom_tax_id
    #                                                         else:
    #                                                             dict_ol['tax_ids'] = None
    #
    #                                                     if i.get('SalesItemLineDetail').get('Qty'):
    #                                                         dict_ol['quantity'] = i.get('SalesItemLineDetail').get(
    #                                                             'Qty')
    #
    #                                                     if i.get('SalesItemLineDetail').get('UnitPrice'):
    #                                                         dict_ol['price_unit'] = float(
    #                                                             i.get('SalesItemLineDetail').get('UnitPrice'))
    #                                                     else:
    #                                                         if not i.get('SalesItemLineDetail').get('Qty'):
    #                                                             dict_ol['quantity'] = 1
    #                                                             dict_ol['price_unit'] = float(
    #                                                                 i.get('Amount'))
    #                                                         else:
    #                                                             dict_ol['price_unit'] = 0.0
    #
    #                                                     if i.get('Description'):
    #                                                         dict_ol['name'] = i.get('Description')
    #                                                     else:
    #                                                         dict_ol['name'] = 'NA'
    #                                                     if res_product.property_account_income_id:
    #                                                         dict_ol[
    #                                                             'account_id'] = res_product.property_account_income_id.id
    #                                                     else:
    #                                                         dict_ol[
    #                                                             'account_id'] = res_product.categ_id.property_account_income_categ_id.id
    #
    #                                                         create_p = self.env['account.move.line'].create(dict_ol)
    #                                                         if create_p:
    #                                                             company.quickbooks_last_credit_note_imported_id = cust.get(
    #                                                                 'Id')
    #                                                             if company.import_credit_memo_by_date:
    #                                                                 date_format = '%Y-%m-%d'
    #                                                                 if company.credit_memo_import_by == 'crt_dt':
    #                                                                     date_string = cust.get('MetaData').get(
    #                                                                         'CreateTime')[:10]
    #                                                                 elif company.credit_memo_import_by == 'updt_dt':
    #                                                                     date_string = cust.get('MetaData').get(
    #                                                                         'LastUpdatedTime')[:10]
    #                                                                 else:
    #                                                                     date_string = cust.get('TxnDate')
    #
    #                                                                 date_object = datetime.strptime(date_string,
    #                                                                                                 date_format).date()
    #                                                                 company.import_credit_memo_date = date_object
    #         else:
    #             raise UserError("Empty Data")
    #             _logger.warning(_('Empty data'))

    # @api.multi
    def export_customers_mapping(self):
        try:
            company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
            if company.last_customer_mapping_export:
                res_partner = self.env['res.partner'].search([
                    # ('check_update_flag', '=', True),
                    ('customer_rank', '>', 0),
                    ('type', '=', 'contact'),
                    ('write_date', '>=', company.last_customer_mapping_export)
                ])
            else:
                res_partner = self.env['res.partner'].search([
                    ('customer_rank', '>', 0),
                    ('qbo_vendor_id', '=', False),
                    ('qbo_customer_id', '=', False)])
            if self.export_mapping_customer_field and self.export_mapping_customer_id:
                url_str = self.get_import_query_url_1()
                url = url_str.get('url')
                headers = url_str.get('headers')
                for contact in res_partner:
                    outdict = {}
                    if contact.customer_rank and contact.type == 'contact':
                        for fields_line_id in self.export_mapping_customer_id.fields_lines:
                            split_key = fields_line_id.value.split('.')
                            attr = getattr(contact, fields_line_id.col1.name)
                            if not attr:
                                continue
                            if fields_line_id.ttype in ['datetime', 'date', 'boolean', 'integer', 'float', 'char',
                                                        'text', 'monetary']:
                                values = attr
                            elif fields_line_id.ttype in ['many2one']:
                                values = attr.name or False
                            elif fields_line_id.ttype in ['one2many']:
                                values = str(attr.parent_id.id)
                            if len(split_key) > 1:
                                if split_key[0] not in outdict:
                                    outdict[split_key[0]] = {split_key[1]: values}
                                else:
                                    outdict[split_key[0]].update({split_key[1]: values})
                            else:
                                outdict[split_key[0]] = values
                    if contact.qbo_customer_id:
                        realmId = self.realm_id
                        if self.access_token:
                            sql_query = "select Id,SyncToken from customer Where Id = '{}'".format(
                                str(contact.qbo_customer_id))

                            result = requests.request('GET', url + "/query?query=" + sql_query, headers=headers)
                            if result.status_code == 200:
                                parsed_result = result.json()
                                if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get(
                                        'Customer'):
                                    customer_id_retrieved = parsed_result.get('QueryResponse').get('Customer')[0].get(
                                        'Id')
                                    syncToken = ''
                                    if customer_id_retrieved:
                                        ''' HIT UPDATE REQUEST '''
                                        syncToken = parsed_result.get('QueryResponse').get('Customer')[0].get(
                                            'SyncToken')
                                        outdict.update({
                                            self.export_mapping_customer_id.search_field_qbo: customer_id_retrieved,
                                            'SyncToken': syncToken,
                                            'sparse': "true",
                                        })
                        contact.sendDataToQuickbooksForUpdate(outdict)
                        QBQ_od = contact.sendDataToQuickbook(outdict)
                    else:
                        QBQ_od = contact.sendDataToQuickbook(outdict)
                        contact.write({'qbo_customer_id': QBQ_od})
                        contact._cr.commit()
                company.last_customer_mapping_export = fields.Datetime.now()
        except Exception as e:
            _logger.error('Error : {}'.format(e))
            raise UserError(e)

    # @api.multi

    def export_customers(self, cron=None):
        if cron:
            company = self
        else:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user"))
        res_partner = self.env['res.partner'].search([('company_id', '=', company.id), ('qbo_customer_id', '!=', True)])
        for contact in res_partner:
            try:
                if self.partner_individual_records:
                    if contact.company_type == 'company':
                        if contact.id == 1 or contact.id == 3:
                            _logger.info(_("There is no any record to be exported."))
                        else:
                            if contact.customer_rank and contact.type == 'contact':
                                contact.with_context(from_button=True).exportCustomer()
                else:
                    if contact.id == 1 or contact.id == 3:
                        _logger.info(_("There is no any record to be exported."))
                    elif contact.customer_rank and contact.type == 'contact':
                        contact.with_context(from_button=True).exportCustomer(company=self)
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': contact.name,
                    'odoo_object': 'res.partner',
                    'message': str(e),
                    'activity': 'Exporting customers from button',
                    'created_date': fields.Datetime.now(),
                })
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

    def export_vendors_mapping(self):
        company = self.env['res.users'].search([('id', '=', self._uid)]).company_id
        if company.last_vendor_mapping_export:
            res_partner = self.env['res.partner'].search([
                # ('check_update_flag', '=', True),
                ('supplier_rank', '>', 0),
                ('write_date', '>=', company.last_vendor_mapping_export),
                ('type', '=', 'contact')
            ])
        else:
            res_partner = self.env['res.partner'].search([
                ('supplier_rank', '>', 0),
                ('qbo_vendor_id', '=', False),
                ('qbo_customer_id', '=', False)
            ])
        if self.export_mapping_vendor_field and self.export_mapping_vendor_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for contact in res_partner:
                outdict = {}
                for fields_line_id in self.export_mapping_vendor_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(contact, fields_line_id.col1.name)
                    if not attr:
                        continue
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        values = attr.name or False
                    elif fields_line_id.ttype in ['one2many']:
                        values = str(attr.parent_id.id)
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                if contact.qbo_vendor_id:
                    sql_query = "select Id,SyncToken from vendor Where Id = '{}'".format(
                        str(contact.qbo_vendor_id))
                    result = requests.request('GET', url + "/query?query=" + sql_query, headers=headers)
                    if result.status_code == 200:
                        parsed_result = result.json()
                        if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get('Vendor'):
                            customer_id_retrieved = parsed_result.get('QueryResponse').get('Vendor')[0].get('Id')
                            if customer_id_retrieved:
                                ''' HIT UPDATE REQUEST '''
                                syncToken = parsed_result.get('QueryResponse').get('Vendor')[0].get('SyncToken')
                                outdict.update({
                                    self.export_mapping_vendor_id.search_field_qbo: customer_id_retrieved,
                                    'SyncToken': syncToken,
                                    'sparse': "true",
                                })
                    contact.sendVendorDataToQuickbooksForUpdate(outdict)
                else:
                    QBQ_od = contact.sendVendorDataToQuickbook(outdict)
                    contact.write({'qbo_vendor_id': QBQ_od})
                    contact._cr.commit()
            company.last_vendor_mapping_export = fields.Datetime.now()

    # @api.multi
    def export_vendors(self, cron=None):
        if cron:
            company = self
        else:
            company = self
            companys = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_ids
            if not company in companys:
                raise ValidationError(
                    _("Company is not allowed for user"))
        res_partner = self.env['res.partner'].search([('company_id', '=', self.id)])
        for contact in res_partner:
            if contact.id == 1 or contact.id == 3:
                _logger.info(_("There is no any record to be exported."))
            else:
                if contact.supplier_rank:
                    try:
                        contact.with_context(from_button=True).exportVendor(cron=None, company=company)
                    except Exception as e:
                        _logger.exception("Export failed")
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': contact.name,
                            'odoo_object': 'res.partner',
                            'message': str(e),
                            'activity': 'Exporting vendors from button',
                            'created_date': fields.Datetime.now(),
                        })
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

    # @api.multi
    def export_accounts(self):
        accounts = self.env['account.account'].search([('company_ids', '=', self.id)])
        for account in accounts:
            if not account.qbo_id:
                try:
                    account.with_context(from_button=True).export_to_qbo()
                except Exception as e:
                    _logger.exception("Export failed")
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': account.name,
                        'odoo_object': 'account.account',
                        'message': str(e),
                        'activity': 'Exporting accounts from button',
                        'created_date': fields.Datetime.now(),
                    })
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

    # @api.multi

    def export_tax(self):
        taxes = self.env['account.tax'].search([('amount_type', '!=', 'group'), ('company_id', '=', self.id)])
        for tax in taxes:
            try:
                tax.with_context(from_button=True).export_to_qbo()
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': tax.name,
                    'odoo_object': 'account.tax',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })

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
    def export_product_without_reference_number(self):
        # # Search for products linked to the current company that have no internal reference
        products = self.env['product.product'].search([
            ('company_id', '=', self.id),
            ('default_code', '=', False)  # This finds products with no internal reference
        ])

        for product in products:
            self.env['qbo.logger'].create({
                'odoo_name': product.name,
                'odoo_object': 'product.product',
                'message': f'Product Missing Internal Reference: {product.name}',
                'activity': 'Check Products without Internal Reference',
                'created_date': fields.Datetime.now()
            })
            _logger.info(f"Created log for product: {product.name}")

        # Commit the transaction
        self.env.cr.commit()

        return True

        # Commit the transaction

        # Optionally, return the list of products for further processing if needed
        # return products

        # raise ValidationError(
        #     'Please Set Internal Reference for Product: {}'.format(products.name))

        # Access fields in the product
        # for pro in products:
        #     # Example: Access the 'name' and 'list_price' fields
        #     product_name = pro.name
        #     product_price = pro.default_code

    # @api.multi
    def export_products(self, cron=None):
        self.export_product_without_reference_number()
        products = self.env['product.product'].search([('company_id', '=', self.id)])
        if not products:
            raise UserError('There is no any record to be exported.')
        for product in products:
            try:
                if not product.qbo_product_id:
                    if cron:
                        product.with_context(from_button=True).export_product_to_qbo(company=self, cron=1)
                    else:
                        product.with_context(from_button=True).export_product_to_qbo()
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': product.name,
                    'odoo_object': 'product.product',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })

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

    # @api.multi
    def export_payment_method(self):
        company = self
        payment_method = self.env['account.journal'].search(
            [('type', 'in', ['cash', 'bank']), ('company_id', '=', self.id), ('qbo_method_id', '=', False)])
        if not payment_method:
            raise UserError('There is no any record to be exported.')
        for method in payment_method:
            try:
                if not method.qbo_method_id:
                    method.with_context(from_button=True).export_to_qbo(company)
                else:
                    _logger.info(_("There is no any record to be exported."))
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': method,
                    'odoo_object': 'account.journal',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })
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

    def export_payment_terms_mapping(self):
        if self.last_payment_term_mapping_export:
            apt_ids = self.env['account.payment.term'].search([
                ('write_date', '>=', self.last_payment_term_mapping_export),
            ])
        else:
            apt_ids = self.env['account.payment.term'].search([('x_quickbooks_id', '=', False)])
        if self.export_mapping_payment_term_id and self.export_mapping_payment_term_field:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for apt_id in apt_ids:
                outdict = {}
                for fields_line_id in self.export_mapping_payment_term_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(apt_id, fields_line_id.col1.name)
                    if not attr:
                        attr = ''
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                if apt_id.x_quickbooks_id:
                    sql_query = "select Id,SyncToken from term Where Id = '{}'".format(apt_id.x_quickbooks_id)
                    result1 = requests.request('GET', url + "/query?query=" + sql_query, headers=headers)
                    parsed_result = result1.json()
                    outdict.update({
                        'SyncToken': parsed_result.get('QueryResponse').get('Term')[0].get('SyncToken'),
                        'Id': apt_id.x_quickbooks_id,
                    })
                outdict.update({'DueDays': apt_id.line_ids and apt_id.line_ids[0].nb_days or 0.0})
                parsed_dict = json.dumps(outdict)
                result = requests.request('POST', url + "/term", headers=headers, data=parsed_dict)
                if result.status_code == 200:
                    parsed_result = result.json()
                    apt_id.x_quickbooks_id = parsed_result.get('Term').get('Id')
                    self.last_payment_term_mapping_export = datetime.now()
                    _logger.info(_("Payment Terms Id: %s" % (apt_id.x_quickbooks_id)))
                    self._cr.commit()
                else:
                    self.error_message_from_quickbook(result, apt_id.name, 'Payment Terms')

    # @api.multi
    def export_payment_terms(self):
        payment_term = self.env['account.payment.term'].search([])
        if not payment_term:
            raise UserError('There is no any record to be exported.')
        for term in payment_term:
            try:
                if not term.x_quickbooks_id:
                    term.with_context(from_button=True).export_payment_term_to_quickbooks()
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': term,
                    'odoo_object': 'account.payment.term',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })
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

    def export_sale_order_mapping(self):
        # sales = self.env['sale.order'].search([('quickbook_id', '=', False)])
        if self.last_so_mapping_export:
            sales = self.env['sale.order'].search([
                ('write_date', '>=', self.last_so_mapping_export),
                ('state', '=', 'sale'),
                ('quickbook_id', '=', False)])
        else:
            sales = self.env['sale.order'].search([
                ('state', '=', 'sale'),
                ('quickbook_id', '=', False)])
        if self.export_mapping_so_field and self.export_mapping_so_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for sale_id in sales:
                tax_ids = sale_id.order_line.mapped('tax_ids').filtered(lambda x: x.qbo_tax_id)
                if not tax_ids:
                    tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'sale')], limit=1)
                    qb_tax_id = tax_id.qbo_tax_id
                else:
                    qb_tax_id = tax_ids[0].qbo_tax_id
                outdict = {'TxnTaxDetail': {'TxnTaxCodeRef': {'value': qb_tax_id}}}

                for fields_line_id in self.export_mapping_so_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(sale_id, fields_line_id.col1.name)
                    if not attr:
                        continue
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'selection' and fields_line_id.value == 'GlobalTaxCalculation':
                        if sale_id.tax_state == 'exclusive':
                            values = "TaxExcluded"
                        elif sale_id.tax_state == 'inclusive':
                            values = "TaxInclusive"
                        elif sale_id.tax_state == 'notapplicable':
                            values = "NotApplicable"
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(sale_id, fields_line_id.col1.name)
                        attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                        values = attr or ''
                    elif fields_line_id.ttype in ['one2many']:
                        line_list = []
                        for line in attr:
                            line_val = {'DetailType': 'SalesItemLineDetail'}
                            for sub_field in fields_line_id.sub_field_object_id.sub_field_ids:
                                sub_split_key = sub_field.qb_field.split('.')
                                sub_attr = getattr(line, sub_field.field_id.name)
                                if sub_field.ttype == 'many2one':
                                    sub_attr = getattr(sub_attr, sub_field.relation_field.name)
                                    if sub_field.relation == 'product.product' and not sub_attr:
                                        sub_attr = self.env['product.template'].get_qbo_product_ref(sub_attr)
                                    value = sub_attr or ""
                                else:
                                    value = sub_attr or ""
                                if len(sub_split_key) == 1:
                                    line_val.update({sub_field.qb_field: value})
                                elif len(sub_split_key) == 2:
                                    if sub_field.field_id.name == 'price_unit' and line.discount:
                                        value = value - (value * (line.discount / 100))
                                    if sub_split_key[0] not in line_val:
                                        line_val.update({sub_split_key[0]: {sub_split_key[1]: value}})
                                    else:
                                        line_val[sub_split_key[0]].update({sub_split_key[1]: value})
                                    # line_val[sub_split_key[0]] = {sub_split_key[1]: values}
                                elif len(sub_split_key) == 3:
                                    tax_type = "NON"
                                    if line.tax_ids:
                                        tax_type = "TAX"
                                    if sub_split_key[0] == 'SalesItemLineDetail':
                                        line_val.update({sub_split_key[0]: {
                                            sub_split_key[1]: {
                                                sub_split_key[
                                                    2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id},
                                            "TaxCodeRef": {"value": tax_type}
                                        }})
                                    else:
                                        line_val.update({sub_split_key[0]: {
                                            sub_split_key[1]: {
                                                sub_split_key[
                                                    2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id}}})
                            line_list.append(line_val)
                        values = line_list
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                parsed_dict = json.dumps(outdict)

                result = requests.request('POST', url + "/estimate",
                                          headers=headers, data=parsed_dict)
                if result.status_code == 200:
                    response = result.json()
                    qbo_id = int(response.get('Estimate').get('Id'))
                    sale_id.quickbook_id = qbo_id
                    self.last_so_mapping_export = datetime.now()
                    self._cr.commit()
                    _logger.info(_("%s exported successfully to QBO" % (sale_id.name)))
                else:
                    self.error_message_from_quickbook(result, sale_id.name, 'Sale Order')

    @api.model
    def sale_order_sigle(self):
        sales = self.env['sale.order'].search([
            ('state', 'not in', ['done', 'sale']),
            ('company_id', '=', self.id)
        ], limit=1)

        for sal in sales:
            error_sales = self.env['qbo.logger'].sudo().create({
                'odoo_name': f'{sales.name}',
                'odoo_object': 'sale order',
                'message': f'Only Confirm sale records exported to QBO: {sales.name}',
                'activity': 'Export sale Order from QBO',
                'created_date': fields.Datetime.now(),
                # 'company_id': company.id,
            })

            # Ensure the transaction is committed
            self.env.cr.commit()

    # @api.multi
    def export_sale_order(self, cron=None):
        self.sale_order_sigle()
        if self:
            company = self
        sales = self.env['sale.order'].search([('state', 'in', ['done', 'sale']), ('company_id', '=', self.id)])
        if not sales:
            raise UserError('There is no any record to be exported.')

        if len(sales) == 1:
            if sales.state not in ['done', 'sale']:
                raise ValidationError(
                    _("Only confirmed Sales Order is exported to QBO."))

        for sale in sales:
            try:
                if sale.quickbook_id and sale.state == 'sale':
                    _logger.info(
                        _("Sale Order is already exported to QBO. %s" % sale))
                elif not sale.quickbook_id:
                    sale.with_context(from_button=True).exportSaleOrder(cron, company)
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': sale,
                    'odoo_object': 'sale.order',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })

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

    def single_invoice_export(self):
        # Get the current company
        company = self

        # Search for the first invoice meeting the criteria
        invoice = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('company_id', '=', company.id)
        ], limit=1)

        # If an invoice is found, raise a UserError
        if invoice:
            error_sales = self.env['qbo.logger'].sudo().create({
                'odoo_name': f'{invoice.name}',
                'odoo_object': 'Invoice',
                'message': f'Only posted state exported to QBO: {invoice.name}',
                'activity': 'Export sale Order from QBO',
                'created_date': fields.Datetime.now(),
                # 'company_id': company.id,
            })

            # Ensure the transaction is committed
            self.env.cr.commit()

    # @api.multi
    def export_invoice(self):
        # self.single_invoice_export()
        company = self
        invoices = self.env['account.move'].search(
            [('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('company_id', '=', company.id),('qbo_invoice_id', '=', False)])
        if not invoices:
            raise UserError('There is no any record to be exported.')
        for inv in invoices:
            try:
                inv.with_context(from_button=True).export_to_qbo()
                if inv.partner_id.customer_rank:
                    if inv.state == 'open' and inv.qbo_invoice_id:
                        _logger.info(
                            _("Invoice is already exported to QBO. %s" % inv))
                    else:
                        if not inv.qbo_invoice_id:
                            if inv.move_type != 'out_refund' or inv.move_type != 'in_refund':
                                inv.with_context(from_button=True).export_to_qbo()
                            else:
                                _logger.info(
                                    _("This '%s' can not be exported as this is refund type." % inv.name))
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': inv.name,
                    'odoo_object': 'account.move',
                    'message': str(e),
                    'activity': 'Exporting invoices from button',
                    'created_date': fields.Datetime.now(),
                })
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

    def export_invoice_mapping(self):
        move_type = 'out_invoice'
        last_mapping_export = self.last_inv_mapping_export
        export_name = 'Invoice'
        query_type = "/invoice"
        if self.env.context.get('credit'):
            export_name = 'Credit Notes'
            move_type = 'out_refund'
            last_mapping_export = self.last_credit_mapping_export
            query_type = "/creditmemo"
        if last_mapping_export:
            invoice_ids = self.env['account.move'].search([
                ('write_date', '>=', last_mapping_export),
                ('qbo_invoice_id', '=', False),
                ('state', '=', 'posted'),
                ('move_type', '=', move_type)
            ])
        else:
            invoice_ids = self.env['account.move'].search([
                ('qbo_invoice_id', '=', False),
                ('state', '=', 'posted'),
                ('move_type', '=', move_type)
            ])
        url_str = self.get_import_query_url_1()
        url = url_str.get('url')
        headers = url_str.get('headers')
        for invoice_id in invoice_ids:
            tax_ids = invoice_id.invoice_line_ids.mapped('tax_ids').filtered(lambda x: x.qbo_tax_id)
            if not tax_ids:
                tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('qbo_tax_id', '!=', False)],
                                                        limit=1)
                qb_tax_id = tax_id.qbo_tax_id
            else:
                qb_tax_id = tax_ids[0].qbo_tax_id
            if qb_tax_id:
                outdict = {'TxnTaxDetail': {'TxnTaxCodeRef': {'value': qb_tax_id}}}
            else:
                outdict = {}
            for fields_line_id in self.export_mapping_inv_id.fields_lines:
                split_key = fields_line_id.value.split('.')
                if fields_line_id.col1.name == 'qbo_invoice_name':
                    attr = getattr(invoice_id, 'name')
                elif fields_line_id.col1.name == 'currency_id':
                    continue
                else:
                    attr = getattr(invoice_id, fields_line_id.col1.name)
                if not attr:
                    continue
                if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                    values = attr
                elif fields_line_id.ttype == 'selection' and fields_line_id.value == 'GlobalTaxCalculation':
                    if invoice_id.tax_state == 'exclusive':
                        values = "TaxExcluded"
                    elif invoice_id.tax_state == 'inclusive':
                        values = "TaxInclusive"
                    elif invoice_id.tax_state == 'notapplicable':
                        values = "NotApplicable"
                elif fields_line_id.ttype == 'datetime':
                    values = fields.Datetime.to_string(attr)
                elif fields_line_id.ttype == 'date':
                    values = fields.Date.to_string(attr)
                elif fields_line_id.ttype in ['many2one']:
                    m2o_ref = getattr(invoice_id, fields_line_id.col1.name)
                    attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                    values = attr or ''
                elif fields_line_id.ttype in ['one2many']:
                    line_list = []
                    for line in attr:
                        line_val = {
                            'DetailType': 'SalesItemLineDetail',
                        }
                        for sub_field in fields_line_id.sub_field_object_id.sub_field_ids:
                            sub_split_key = sub_field.qb_field.split('.')
                            sub_attr = getattr(line, sub_field.field_id.name)
                            if sub_field.ttype == 'many2one':
                                if sub_field.relation == 'product.product' and not sub_attr:
                                    sub_attr = self.env['product.template'].get_qbo_product_ref(sub_attr)
                                value = sub_attr or ""
                            else:
                                value = sub_attr or ""
                            if len(sub_split_key) == 1:
                                line_val.update({sub_field.qb_field: value})
                            elif len(sub_split_key) == 2:
                                if sub_field.field_id.name == 'price_unit' and line.discount:
                                    value = value - (value * (line.discount / 100))
                                if sub_split_key[0] not in line_val:
                                    line_val.update({sub_split_key[0]: {sub_split_key[1]: value}})
                                else:
                                    line_val[sub_split_key[0]].update({sub_split_key[1]: value})
                                # line_val[sub_split_key[0]] = {sub_split_key[1]: values}
                            elif len(sub_split_key) == 3:
                                tax_type = "NON"
                                if line.tax_ids:
                                    tax_type = "TAX"
                                if sub_split_key[0] == 'SalesItemLineDetail':
                                    line_val.update({sub_split_key[0]: {
                                        sub_split_key[1]: {
                                            sub_split_key[
                                                2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id},
                                        "TaxCodeRef": {"value": tax_type}
                                    }})
                                else:
                                    line_val.update({sub_split_key[0]: {
                                        sub_split_key[1]: {
                                            sub_split_key[
                                                2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id}}})
                        line_list.append(line_val)
                    values = line_list
                if len(split_key) > 1:
                    if split_key[0] not in outdict:
                        outdict[split_key[0]] = {split_key[1]: values}
                    else:
                        outdict[split_key[0]].update({split_key[1]: values})
                else:
                    outdict[split_key[0]] = values
            result = requests.request('POST', url + query_type,
                                      headers=headers, data=json.dumps(outdict))
            if result.status_code == 200:
                response = result.json()
                if self.env.context.get('credit'):
                    invoice_id.qbo_invoice_id = response.get('CreditMemo').get('Id')
                    invoice_id.qbo_invoice_name = response.get('CreditMemo').get('DocNumber')
                    self.last_credit_mapping_export = datetime.now()
                else:
                    invoice_id.qbo_invoice_id = response.get('Invoice').get('Id')
                    invoice_id.qbo_invoice_name = response.get('Invoice').get('DocNumber')
                    self.last_inv_mapping_export = datetime.now()
                self._cr.commit()
                _logger.info(_("%s exported successfully to QBO" % (invoice_id.name)))
            else:
                self.error_message_from_quickbook(result, invoice_id.name, export_name)

    def export_bills_mapping(self):
        if self.last_bill_mapping_export:
            invoice_ids = self.env['account.move'].search([
                ('write_date', '>=', self.last_bill_mapping_export.date()),
                ('qbo_invoice_id', '=', False),
                ('state', '=', 'posted'),
                ('move_type', '=', 'in_invoice')
            ])
        else:
            invoice_ids = self.env['account.move'].search([
                ('qbo_invoice_id', '=', False),
                ('state', '=', 'posted'),
                ('move_type', '=', 'in_invoice')
            ])
        url_str = self.get_import_query_url_1()
        url = url_str.get('url')
        headers = url_str.get('headers')
        for invoice_id in invoice_ids:
            tax_ids = invoice_id.invoice_line_ids.mapped('tax_ids').filtered(lambda x: x.qbo_tax_id)
            if not tax_ids:
                tax_id = self.env['account.tax'].search(
                    [('type_tax_use', '=', 'purchase'), ('qbo_tax_id', '!=', False)], limit=1)
                qb_tax_id = tax_id.qbo_tax_id or tax_id.qbo_tax_rate_id
            else:
                qb_tax_id = tax_ids[0].qbo_tax_id
            if qb_tax_id:
                outdict = {'TxnTaxDetail': {'TxnTaxCodeRef': {'value': qb_tax_id}}}
            else:
                outdict = {}
            for fields_line_id in self.export_mapping_bill_id.fields_lines:
                split_key = fields_line_id.value.split('.')
                if fields_line_id.col1.name == 'qbo_invoice_name':
                    attr = getattr(invoice_id, 'name')
                elif fields_line_id.col1.name == 'currency_id':
                    continue
                else:
                    attr = getattr(invoice_id, fields_line_id.col1.name)
                if not attr:
                    continue
                if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                    values = attr
                elif fields_line_id.ttype == 'selection' and fields_line_id.value == 'GlobalTaxCalculation':
                    if invoice_id.tax_state == 'exclusive':
                        values = "TaxExcluded"
                    elif invoice_id.tax_state == 'inclusive':
                        values = "TaxInclusive"
                    elif invoice_id.tax_state == 'notapplicable':
                        values = "NotApplicable"
                elif fields_line_id.ttype == 'datetime':
                    values = fields.Datetime.to_string(attr)
                elif fields_line_id.ttype == 'date':
                    values = fields.Date.to_string(attr)
                elif fields_line_id.ttype in ['many2one']:
                    m2o_ref = getattr(invoice_id, fields_line_id.col1.name)
                    attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                    values = attr or ''
                elif fields_line_id.ttype in ['one2many']:
                    line_list = []
                    for line in attr:
                        line_val = {
                            'DetailType': 'ItemBasedExpenseLineDetail',
                        }
                        for sub_field in fields_line_id.sub_field_object_id.sub_field_ids:
                            sub_split_key = sub_field.qb_field.split('.')
                            sub_attr = getattr(line, sub_field.field_id.name)
                            if sub_field.ttype == 'many2one':
                                if sub_field.relation == 'product.product' and not sub_attr:
                                    sub_attr = self.env['product.template'].get_qbo_product_ref(sub_attr)
                                value = sub_attr or ""
                            else:
                                value = sub_attr or ""
                            if len(sub_split_key) == 1:
                                line_val.update({sub_field.qb_field: value})
                            elif len(sub_split_key) == 2:
                                if sub_field.field_id.name == 'price_unit' and line.discount:
                                    value = value - (value * (line.discount / 100))
                                if sub_split_key[0] not in line_val:
                                    line_val.update({sub_split_key[0]: {sub_split_key[1]: value}})
                                else:
                                    line_val[sub_split_key[0]].update({sub_split_key[1]: value})
                                # line_val[sub_split_key[0]] = {sub_split_key[1]: values}
                            elif len(sub_split_key) == 3:
                                tax_type = "NON"
                                if line.tax_ids:
                                    tax_type = "TAX"
                                if sub_split_key[0] == 'ItemBasedExpenseLineDetail':
                                    line_val.update({sub_split_key[0]: {
                                        sub_split_key[1]: {
                                            sub_split_key[
                                                2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id},
                                        "TaxCodeRef": {"value": tax_type}
                                    }})
                                else:
                                    line_val.update({sub_split_key[0]: {
                                        sub_split_key[1]: {
                                            sub_split_key[
                                                2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id}}})
                        line_list.append(line_val)
                    values = line_list
                if len(split_key) > 1:
                    if split_key[0] not in outdict:
                        outdict[split_key[0]] = {split_key[1]: values}
                    else:
                        outdict[split_key[0]].update({split_key[1]: values})
                else:
                    outdict[split_key[0]] = values
            result = requests.request('POST', url + "/bill",
                                      headers=headers, data=json.dumps(outdict))
            if result.status_code == 200:
                response = result.json()
                invoice_id.qbo_invoice_id = response.get('Bill').get('Id')
                invoice_id.qbo_invoice_name = response.get('Bill').get('DocNumber')
                self.last_bill_mapping_export = datetime.now()
                self._cr.commit()
                _logger.info(_("%s exported successfully to QBO" % (invoice_id.name)))
            else:
                self.error_message_from_quickbook(result, invoice_id.name, 'Bill')

    def export_purchase_order_mapping(self):
        if self.last_po_mapping_export:
            purchase = self.env['purchase.order'].search([
                ('write_date', '>=', self.last_po_mapping_export),
                ('state', '=', 'purchase'),
                ('quickbook_id', '=', False)
            ])
        else:
            purchase = self.env['purchase.order'].search([
                ('state', '=', 'purchase'),
                ('quickbook_id', '=', False)])
        if self.export_mapping_po_field and self.export_mapping_po_id:
            url_str = self.get_import_query_url_1()
            url = url_str.get('url')
            headers = url_str.get('headers')
            for purchase_id in purchase:
                # tax_ids = purchase_id.order_line.mapped('taxes_id').filtered(lambda x: x.qbo_tax_id)
                # if not tax_ids:
                #     tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')], limit=1)
                #     qb_tax_id = tax_id.qbo_tax_id
                # else:
                #     qb_tax_id = tax_ids[0].qbo_tax_id
                # outdict = {'TxnTaxDetail': {'TxnTaxCodeRef': {'value': qb_tax_id}}}
                outdict = {}
                for fields_line_id in self.export_mapping_po_id.fields_lines:
                    split_key = fields_line_id.value.split('.')
                    attr = getattr(purchase_id, fields_line_id.col1.name)
                    if not attr:
                        continue
                    if fields_line_id.ttype in ['boolean', 'integer', 'float', 'char', 'text', 'monetary']:
                        values = attr
                    elif fields_line_id.ttype == 'selection' and fields_line_id.value == 'GlobalTaxCalculation':
                        if purchase_id.tax_state == 'exclusive':
                            values = "TaxExcluded"
                        elif purchase_id.tax_state == 'inclusive':
                            values = "TaxInclusive"
                        elif purchase_id.tax_state == 'notapplicable':
                            values = "NotApplicable"
                    elif fields_line_id.ttype == 'datetime':
                        values = fields.Datetime.to_string(attr)
                    elif fields_line_id.ttype == 'date':
                        values = fields.Date.to_string(attr)
                    elif fields_line_id.ttype in ['many2one']:
                        m2o_ref = getattr(purchase_id, fields_line_id.col1.name)
                        attr = getattr(m2o_ref, fields_line_id.relation_field.name)
                        values = attr or ''
                    elif fields_line_id.ttype in ['one2many']:
                        line_list = []
                        for line in attr:
                            line_val = {
                                'DetailType': 'ItemBasedExpenseLineDetail',
                            }
                            for sub_field in fields_line_id.sub_field_object_id.sub_field_ids:
                                sub_split_key = sub_field.qb_field.split('.')
                                sub_attr = getattr(line, sub_field.field_id.name)
                                if sub_field.ttype == 'many2one':
                                    if sub_field.relation == 'product.product' and not sub_attr:
                                        sub_attr = self.env['product.template'].get_qbo_product_ref(sub_attr)
                                    value = sub_attr or ""
                                else:
                                    value = sub_attr or ""
                                if len(sub_split_key) == 1:
                                    line_val.update({sub_field.qb_field: value})
                                elif len(sub_split_key) == 2:
                                    if sub_split_key[0] not in line_val:
                                        line_val.update({sub_split_key[0]: {sub_split_key[1]: value}})
                                    else:
                                        line_val[sub_split_key[0]].update({sub_split_key[1]: value})
                                elif len(sub_split_key) == 3:
                                    line_val.update({sub_split_key[0]: {
                                        sub_split_key[1]: {
                                            sub_split_key[
                                                2]: line.product_id.qbo_product_id or line.product_id.product_tmpl_id.qbo_product_id}}})
                            line_list.append(line_val)
                        values = line_list
                    if len(split_key) > 1:
                        if split_key[0] not in outdict:
                            outdict[split_key[0]] = {split_key[1]: values}
                        else:
                            outdict[split_key[0]].update({split_key[1]: values})
                    else:
                        outdict[split_key[0]] = values
                parsed_dict = json.dumps(outdict)
                result = requests.request('POST', url + "/purchaseorder",
                                          headers=headers, data=parsed_dict)
                if result.status_code == 200:
                    response = result.json()
                    qbo_id = response.get('PurchaseOrder').get('Id')
                    purchase_id.quickbook_id = qbo_id
                    self.last_po_mapping_export = datetime.now()
                    self._cr.commit()
                    _logger.info(_("%s exported successfully to QBO" % (purchase_id.name)))
                else:
                    self.error_message_from_quickbook(result, purchase_id.name, 'Purchase Order')

    @api.model
    def export_single_purchase_order(self):
        if self:
            company = self
        purchase_orde = self.env['purchase.order'].search(
            [('state', 'not in', ['purchase', 'done']), ('company_id', '=', self.id)], limit=1)
        if purchase_orde:
            error = self.env['qbo.logger'].sudo().create({
                'odoo_name': f'{purchase_orde.name}',
                'odoo_object': 'purchase.order.line',
                'message': f'Only Confirmed Purchase Order is exported to QBO. {purchase_orde.name}',
                'activity': 'Exporting Purchase Order from QBO',
                'created_date': fields.Datetime.now(),
                # 'company_id': company.id,
            })

            # Ensure the transaction is committed
            self.env.cr.commit()

    # @api.multi
    def export_purchase_order(self, cron=None):
        self.export_single_purchase_order()
        if self:
            company = self
        purchase = self.env['purchase.order'].search(
            [('state', 'in', ['purchase', 'done']), ('company_id', '=', self.id)])
        if not purchase:
            raise UserError('There is no any record to be exported.')
        for order in purchase:
            try:
                if order.state == 'purchase' and order.quickbook_id:
                    _logger.info(
                        _("Purchase Order is already exported to QBO. %s" % order))
                else:
                    order.with_context(from_button=True).exportPurchaseOrder(cron, company)
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': order,
                    'odoo_object': 'purchase.order',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })

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

    def export_customer_payment(self):
        if self:
            company = self
        customer_payments = self.env['account.payment'].search(
            [('sale_receipt', '=', False), ('payment_type', '=', 'inbound'),
             ('state', '=', 'paid'), ('company_id', '=', self.id)])
        if not customer_payments:
            raise UserError('There is no record to be exported to QBO.')
        for payment in customer_payments:
            try:
                if payment.qbo_payment_id:
                    _logger.info(
                        "Customer Payment is already exported to QBO.%s" % payment)
                else:
                    payment.with_context(from_button=True).export_to_qbo(company=company)
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': payment,
                    'odoo_object': 'account.payment',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })
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

    def export_vendor_payment(self, cron=None):
        vendor_payments = self.env['account.payment'].search(
            [('payment_type', '=', 'outbound'), ('state', '=', 'paid'), ('company_id', '=', self.id)])
        company = self
        if not vendor_payments:
            raise UserError('There is no record to be exported to QBO.')
        for payment in vendor_payments:
            try:
                if payment.qbo_bill_payment_id:
                    _logger.info(
                        "Vendor Payment is already exported to QBO.%s" % payment)
                else:
                    payment.with_context(from_button=True).export_to_qbo(cron, company)
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': payment,
                    'odoo_object': 'account.payment',
                    'message': str(e),
                    'activity': 'Export from button',
                    'created_date': fields.Datetime.now(),
                })
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
    def export_singl_vendor_bill(self):
        if self:
            company = self
        vendor_bill = self.env['account.move'].search([('state', 'in', ['posted']),
                                                       ('company_id', '=', self.id)], limit=1)
        if vendor_bill:
            vendor_b = self.env['qbo.logger'].sudo().create({
                'odoo_name': f'{vendor_bill.name}',
                'odoo_object': 'Vendor Bill',
                'message': f'Only posted state Vendor Bill is exported to QBO:{vendor_bill.name}',
                'activity': 'Export Vendor bill from QBO',
                'created_date': fields.Datetime.now(),
                # 'company_id': company.id,
            })

            # Ensure the transaction is committed
            self.env.cr.commit()

    # @api.multi
    def export_vendor_bill(self, cron=None):
        self.export_singl_vendor_bill()
        if self:
            company = self
        invoices = self.env['account.move'].search([('state', 'in', ['posted']), ('move_type', '=', 'in_invoice'),
                                                    ('company_id', '=', self.id)])
        if not invoices:
            raise UserError('There is no any record to be exported.')
        for inv in invoices:
            try:
                if inv.partner_id.supplier_rank:
                    if inv.state == 'open' and inv.qbo_invoice_id:
                        _logger.info(
                            _("Invoice is already exported to QBO. %s" % inv))
                    else:
                        if not inv.qbo_invoice_id:
                            if inv.move_type != 'out_refund' or inv.move_type != 'in_refund':
                                inv.with_context(from_button=True).export_to_qbo(cron, company)
                            else:
                                _logger.info(
                                    _("This '%s' can not be exported as this is refund type." % inv.name))
                        # inv.export_to_qbo()
            except Exception as e:
                _logger.exception("Export failed")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': inv.name,
                    'odoo_object': 'account.move',
                    'message': str(e),
                    'activity': 'Exporting Vendoe bill from button',
                    'created_date': fields.Datetime.now(),
                })
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

    # @api.multi
    def export_department(self):
        department = self.env['hr.department'].search([('quickbook_id', '!=', True),('company_id', '=', self.id)])

        if not department:
            raise UserError('There is no any record to be exported.')
        for dept in department:
            dept.exportDepartment()
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

    # @api.multi
    def export_employee(self):
        employee = self.env['hr.employee'].search([])
        if not employee:
            raise UserError('There is no any record to be exported.')
        for emp in employee:
            if emp.quickbook_id == 0:
                emp.export_Employees_to_qbo()
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

        #

    ##########################################################################
    def import_journal_entry_cron(self):
        # companys = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_ids
        companys = self.env.companies
        for company in companys:
            _logger.info("Cron company is-> {}".format(company))

            '''
            This function will import journal entry from qbo
            '''
            # For importing journal entry from qbo
            company.import_journal_entry(call_from='cron', company=company)
            _logger.info("--------Journal Entry imported successfully.")
            self._cr.commit()

    def import_journal_entry(self, call_from=None, company=None):
        """IMPORT JournalEntry FROM JournalEntry TO ODOO"""
        try:
            if not company:
                company = self
                companys = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_ids
                if not company in companys:
                    raise ValidationError(
                        _("Company is not allowed for user. Journal Entry QBO ID: %s") % (self.journal_entry or 'N/A')
                    )
            log = None
            _logger.info(
                "\n\n\n<-----------------------------------JournalEntry-------------------------------------->", )

            if not self.journal_entry:
                if call_from == 'cron':
                    log = self.env['qbo.logger'].create({
                        'odoo_name': 'Journal Entry',
                        'odoo_object': 'Journal Entry',
                        'message': "Journal Entry is not defined in the configuration",
                        'created_date': datetime.now(),
                    })
                else:
                    raise UserError(
                        "Journal Entry is not defined in the configuration.")

            if not log:
                try:
                    res = self.journal_main_function()
                except Exception as e:
                    _logger.exception("Failed to execute journal_main_function for QBO ID: %s", self.journal_entry or 'N/A')
                    raise ValidationError(
                        _("Failed to import Journal Entry for QBO ID: %s. Error: %s") % (self.journal_entry or 'N/A', str(e))
                    )

                _logger.info("RESPONSE : %s", res)
                success_form = self.env.ref(
                    'pragmatic_quickbooks_connector_canada.import_successfull_view', False)
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
            else:
                return True
        except UserError as ue:
            if call_from == 'cron':
                _logger.exception("Unexpected error during Journal Entry import (QBO ID: %s)", self.journal_entry or 'N/A')
            else:
                raise ue
        except ValidationError as ve:
            if call_from == 'cron':
                _logger.exception("Unexpected error during Journal Entry import (QBO ID: %s)", self.journal_entry or 'N/A')
            else:
                raise ve
        except Exception as e:
            _logger.exception("Unexpected error during Journal Entry import (QBO ID: %s)", self.journal_entry or 'N/A')
            raise ValidationError(
                _("An unexpected error occurred while importing Journal Entry for QBO ID: %s. Error: %s") %
                (self.journal_entry or 'N/A', str(e))
            )

    def journal_main_function(self):
        _logger.info(
            "Inside journal_main_function ****************************")
        company = self
        if company.access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + self.access_token
            headers['accept'] = 'application/json'
            headers['Content-Type'] = 'text/plain'

            if company.import_je_by_date:
                if self.journal_entry_import_by == 'crt_dt':
                    query = f"select * from JournalEntry WHERE Metadata.CreateTime >= '{company.import_je_date}' order by Id MAXRESULTS {company.limit}"
                elif self.journal_entry_import_by == 'other_dt':
                    query = f"select * from JournalEntry WHERE TxnDate >= '{company.import_je_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from JournalEntry WHERE Metadata.LastUpdatedTime >= '{company.import_je_date}' order by Id MAXRESULTS {company.limit}"
            else:
                query = f"select * from JournalEntry order by Id STARTPOSITION {company.quickbooks_last_journal_entry_imported_id} MAXRESULTS {company.limit}"

            try:
                data = requests.request('GET', self.url + str(self.realm_id) + "/query?query=" + query,
                                        headers=headers)
            except Exception as e:
                _logger.error("Error while requesting JournalEntry data from QBO: %s", str(e))
                raise ValidationError(_("Failed to fetch Journal Entry data from QuickBooks: %s") % str(e))
            
            if data:
                _logger.info(
                    "JournalEntry data is -------------------->{}".format(data.text))
                try:
                    recs = []
                    parsed_data = json.loads(str(data.text))
                except Exception as e:
                    _logger.error("JSON Parsing failed for JournalEntry data: %s", str(e))
                    raise ValidationError(_("Error parsing JournalEntry response from QuickBooks: %s") % str(e))
            
                if parsed_data:
                    _logger.info(
                        "Parsed data for JournalEntry is -------------> {}".format(parsed_data))
                    if parsed_data.get('QueryResponse') and parsed_data.get('QueryResponse').get('JournalEntry'):
                        for JournalEntry in parsed_data.get('QueryResponse').get('JournalEntry'):
                            try:
                                _logger.info(
                                    _('JournalEntry Record : \n\n\n\nJournalEntry From Quickbooks : %s\n\n\n\n' % JournalEntry))

                                self.create_journal_entry(JournalEntry)
                            except Exception as e:
                                journal_id = JournalEntry.get('Id', 'Unknown')
                                _logger.error("Error while creating JournalEntry with QBO ID %s: %s", journal_id, str(e))
                                raise ValidationError(_("Error while importing Journal Entry (QBO ID: %s): %s") % (journal_id, str(e)))
                        company.quickbooks_last_journal_entry_imported_id = parsed_data.get('QueryResponse').get(
                            'maxResults') + int(
                            company.quickbooks_last_journal_entry_imported_id)
                    else:
                        raise UserError(_("It seems that all of the Journal Entries are already imported."))

            else:
                raise UserError("Empty Data")
                _logger.warning(_('Empty data'))

    def create_journal_entry(self, rec):
        try:
            journal_entry = {}
            if rec.get('Id'):
                _logger.info("PROCESSING JournalEntry NUMBER : %s", rec.get('Id'))

            journal_id = self.journal_entry
            if not journal_id:
                raise ValidationError("Missing Journal ID while processing JournalEntry QBO ID: %s" % rec.get('Id'))
            
            journal_entry['journal_id'] = journal_id.id

            journal_object = self.env['account.move'].search([('qbo_invoice_id', '=', rec.get('Id')),
                                                            ('company_id', '=', self.id),
                                                            ('move_type', '=', 'entry')
                                                            ], limit=1)
            _logger.info('Journal Object : %s %s %s' %
                        (journal_object, rec, rec.get('Id')))

            # Update quickbooks_last_journal_entry_imported_id regardless of whether journal exists
            # if rec.get('Id'):
            #     self.quickbooks_last_journal_entry_imported_id = rec.get('Id')

            # Update import_je_date if import_je_by_date is True
            if self.import_je_by_date:
                try:
                    date_format = '%Y-%m-%d'
                    if self.journal_entry_import_by == 'crt_dt':
                        date_string = rec.get('MetaData').get('CreateTime')[:10]
                    elif self.journal_entry_import_by == 'updt_dt':
                        date_string = rec.get('MetaData').get('LastUpdatedTime')[:10]
                    else:
                        date_string = rec.get('TxnDate')

                    date_object = datetime.strptime(date_string, date_format).date()
                    self.import_je_date = date_object
                except Exception as e:
                    raise ValidationError("Invalid or missing date in QBO JournalEntry ID: %s. Error: %s" % (rec.get('Id'), str(e)))

            if not journal_object:
                journal_entry['move_type'] = 'entry'  # For Journal

                if rec.get('PrivateNote'):
                    journal_entry['ref'] = rec.get('PrivateNote')

                if rec.get('Id'):
                    journal_entry['qbo_invoice_id'] = rec.get('Id')

                if rec.get('TxnDate'):
                    journal_date = rec.get('TxnDate')
                    journal_entry['date'] = journal_date

                journal_entry['line_ids'] = []

                if rec.get('Line'):
                    for line in rec.get('Line'):
                        try:
                            line_ids = self.create_journal_line_entries(line, rec,
                                                                        lineAmountType=rec.get('LineAmountTypes'),
                                                                        rec_id=rec.get('Id'))
                            if line_ids:
                                currency_id = self.env['res.currency'].browse(line_ids.get('currency_id'))
                                if currency_id:
                                    balance = line_ids.get('amount_currency')
                                    balance = currency_id._convert(balance,
                                                                self.currency_id,
                                                                self,
                                                                fields.Date.today()
                                                                )
                                    _logger.info('Balance=======================' + str(balance))
                                    line_ids['debit'] = balance > 0 and balance or 0.0
                                    line_ids['credit'] = balance < 0 and -balance or 0.0
                                journal_entry['line_ids'].append((0, 0, line_ids))
                        except Exception as e:
                            raise ValidationError("Error creating journal line for QBO JournalEntry ID: %s. Error: %s" % (rec.get('Id'), str(e)))

                    try:
                        account_journal_id = self.env['account.move'].create(journal_entry)
                        account_journal_id.action_post()
                        self._cr.commit()
                        _logger.info('%s Journal Imported Successfully....' % rec.get('Id'))
                    except Exception as e:
                        raise ValidationError("Error creating or posting journal entry for QBO JournalEntry ID: %s. Error: %s" % (rec.get('Id'), str(e)))
            else:
                _logger.info('%s Journal Already Imported ....' % rec.get('Id'))
        except ValidationError as ve:
            _logger.error("Validation Error in QBO JournalEntry ID: %s. Details: %s", rec.get('Id'), str(ve))
            raise ve
        except Exception as e:
            _logger.error("Unhandled error in QBO JournalEntry ID: %s. Details: %s", rec.get('Id'), str(e))
            raise ValidationError("Unhandled error while processing JournalEntry QBO ID: %s. Error: %s" % (rec.get('Id'), str(e)))

    def create_journal_line_entries(self, line, rec={}, lineAmountType=None, rec_id=None, account_id=None, is_tax=0):

        line_ids = {}
        account_obj = self.env['account.account']

        try:
            if line.get('Description'):
                line_ids['name'] = line.get('Description')
            # else:
            #     line_ids['name'] = 'None'
            #     raise ValidationError('Description missing at line level (QBO Record Id : {})'.format(rec_id))

            if is_tax == 0:
                if lineAmountType == "Inclusive":
                    if line.get('LineAmount') is None or line.get('TaxAmount') is None:
                        raise ValidationError(_('LineAmount or TaxAmount missing for Inclusive Line (QBO Record Id: {})'.format(rec_id)))
                
                    if line.get('LineAmount') > 0:
                        line_ids['debit'] = abs(
                            line.get('LineAmount')) - abs(line.get('TaxAmount'))
                    else:
                        line_ids['credit'] = abs(
                            line.get('LineAmount')) - abs(line.get('TaxAmount'))
                else:
                    if line.get('JournalEntryLineDetail'):
                        if line.get('JournalEntryLineDetail').get('PostingType') == 'Debit':
                            line_ids['debit'] = abs(line.get('Amount'))
                        elif line.get('JournalEntryLineDetail').get('PostingType') == 'Credit':
                            line_ids['credit'] = abs(line.get('Amount'))
                        else:
                            raise ValidationError(_('Invalid PostingType in line (QBO Record Id: {})'.format(rec_id)))
                    else:
                        raise ValidationError(_('Missing JournalEntryLineDetail for non-inclusive line (QBO Record Id: {})'.format(rec_id)))
            else:
                if line.get('JournalEntryLineDetail'):
                    if line.get('JournalEntryLineDetail').get('PostingType') == 'Debit':
                        line_ids['debit'] = line.get('Amount')
                    elif line.get('JournalEntryLineDetail').get('PostingType') == 'Credit':
                        line_ids['credit'] = abs(line.get('Amount'))
                    else:
                        raise ValidationError(_('Invalid PostingType in tax line (QBO Record Id: {})'.format(rec_id)))
                else:
                    raise ValidationError(_('Missing JournalEntryLineDetail for tax line (QBO Record Id: {})'.format(rec_id)))

            if rec.get('CurrencyRef').get('value') != self.currency_id.name:
                if not line.get('JournalEntryLineDetail'):
                    raise ValidationError(_('Missing JournalEntryLineDetail for currency check (QBO Record Id: {})'.format(rec_id)))
                
                if line.get('JournalEntryLineDetail').get('PostingType') == 'Debit':
                    line_ids['amount_currency'] = -1 * abs(line.get('Amount'))
                if line.get('JournalEntryLineDetail').get('PostingType') == 'Credit':
                    line_ids['amount_currency'] = abs(line.get('Amount'))

                if rec.get('CurrencyRef').get('value'):
                    currency = self.env['res.currency'].search(
                        [('name', '=', rec.get('CurrencyRef').get('value'))], limit=1)
                    line_ids['currency_id'] = currency.id
                if line_ids.get('credit'):
                    del line_ids['credit']
                if line_ids.get('debit'):
                    del line_ids['debit']
            if account_id is None:
                if line.get('JournalEntryLineDetail'):
                    account_ref = line.get('JournalEntryLineDetail').get('AccountRef')
                    if line.get('JournalEntryLineDetail').get('AccountRef'):
                        account_id = account_obj.search([('qbo_id', '=', line.get(
                            'JournalEntryLineDetail').get('AccountRef').get('value'))])
                        if not account_id:
                            raise ValidationError(_('Account not found for AccountRef value "{}" (QBO Record Id: {})'.format(account_ref.get('value'), rec_id)))
                else:
                    raise ValidationError(_(f"Missing AccountRef For QBO ID: {rec.get('Id')}"))
            if account_id:
                line_ids['account_id'] = account_id.id

            return line_ids
        except Exception as e:
            raise ValidationError(_('Error creating journal line entry (QBO Record Id: {}): {}'.format(rec_id, str(e))))

    def export_journal_entry_cron(self):
        companys = self.env.companies
        for company in companys:
            invoices = self.env['account.move'].search([('company_id', '=', company.id)])
            # if not invoices:
            #     raise UserError('There is no any record to be exported.')

            for inv in invoices:
                if inv.move_type in ['entry']:
                    inv.export_journal_entry(company=company)
