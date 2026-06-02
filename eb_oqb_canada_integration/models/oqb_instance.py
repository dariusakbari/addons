import urllib.parse
from odoo import api, fields, models, _
import requests
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class QuickbookInstance(models.Model):
    """
       Represents a Quickbook Instance in the system, which holds configuration details and synchronization settings
       for various entities like contacts, customers, deals, leads, and products between Odoo and Quickbook.
    """
    _name = 'oqb.instance'
    _description = 'Quickbook Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default='Quickbook Instance', required=True)
    pagination_size = fields.Integer(string='Pagination Size', required=True, default='25')
    is_connected = fields.Boolean(default=False)
    company_id = fields.Char(string='Quickbook Company ID')
    company_name = fields.Many2one('res.company', string='Odoo Company Name', required=True)
    minor_version = fields.Char(string='Quickbook Version', required=True)
    quickbook_time_zone = fields.Char(string='Quickbook Time Zone', required=True, default='America/Toronto')

    # ************************************ Scheduler ********************************** #
    progress_stage = fields.Selection([('not_started', 'Not Started'), ('chart_of_account_otq', 'Chart of Account otq'),
                    ('chart_of_account_qto', 'Chart of Account qto'), ('customer_otq', 'Customer otq'),
                    ('customer_qto', 'Customer qto'), ('product_otq', 'Product otq'),
                    ('product_qto', 'Product qto'), ('sale_order_otq', 'Sale Order otq'),
                    ('sale_order_qto', 'Sale Order qto'), ('invoice_otq', 'Invoice otq'),
                    ('invoice_qto', 'Invoice qto'), ('credit_note_otq', 'Credit Note otq'),
                    ('credit_note_qto', 'Credit Note qto'), ('customer_payment_otq', 'Customer Payment otq'),
                    ('customer_payment_qto', 'Customer Payment qto'),
                    ('vendor_otq', 'Vendor otq'), ('vendor_qto', 'Vendor qto'),
                    ('purchase_order_otq', 'Purchase Order otq'), ('purchase_order_qto', 'Purchase Order qto'),
                    ('vendor_bill_otq', 'Vendor Bill otq'),('vendor_bill_qto', 'Vendor Bill qto'),
                    ('refund_otq', 'Refund otq'), ('refund_qto', 'Refund qto'),
                    ('vendor_payment_otq', 'Vendor Payment otq'), ('vendor_payment_qto', 'Vendor Payment qto'),
                    ('payment_term_otq', 'Payment Term otq'), ('payment_term_qto', 'Payment Term qto'),
                    ('payment_method_otq', 'Payment Method otq'), ('payment_method_qto', 'Payment Method qto'),
                    ('account_tax_otq', 'Account Tax otq'), ('account_tax_qto', 'Account Tax qto'),
                    ('employee_otq', 'Employee otq'), ('employee_qto', 'Employee qto'),
                    ('department_otq', 'Department otq'), ('department_qto', 'Department qto'),
                    ('completed', 'Completed')
                    ], string='Progress Stage', default='not_started')

    # ------------------------- Quickbook Configuration ---------------------- #
    scope_code = fields.Char(string='Scope Code', default='com.intuit.quickbooks.accounting')
    client_id = fields.Char(string='Client ID')
    client_secret = fields.Char(string='Client Secret')
    refresh_grant_type = fields.Char(string='Refresh Token Grant Type', default='authorization_code')
    access_grant_type = fields.Char(string='Access Token Grant Type', default='refresh_token')
    base_api_url = fields.Char(string='Base API URL', default='https://quickbooks.api.intuit.com/v3/company')
    token_api_url = fields.Char(string='Token URL', default='https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer')
    refresh_token = fields.Char(string='Refresh Token')
    access_token = fields.Text(string='Access Token')
    authorize_code = fields.Char(string='Authorization Code')
    redirect_uri = fields.Char(string='Redirect URI', default='https://www.echobitzit.com')
    authorization_url = fields.Text(string='Authorization URL', default='https://appcenter.intuit.com/connect/oauth2?client_id="client_id"&redirect_uri="redirect_uri"&response_type=code&scope=com.intuit.quickbooks.accounting&state=csrf')

    #  ---------------------------- Account Configuration --------------------------------- #

    oqb_sale_journal = fields.Many2one('account.journal', domain="[('type', '=', 'sale')]", string='Sale Journal')
    oqb_purchase_journal = fields.Many2one('account.journal', domain="[('type', '=', 'purchase')]",
                                           string='Purchase Journal')
    oqb_bank_journal = fields.Many2one('account.journal', domain="[('type', '=', 'bank')]", string='Bank Journal')
    oqb_cash_journal = fields.Many2one('account.journal', domain="[('type', '=', 'cash')]", string='Cash Journal')
    oqb_misc_journal = fields.Many2one('account.journal', domain="[('type', '=', 'general')]",
                                       string='Miscellaneous Journal')
    oqb_vpt_credit_card_account = fields.Many2one('account.account',
                                                  domain="[('account_type', '=', 'liability_credit_card')]",
                                                  string='Credit Card Account')
    oqb_purchase_account = fields.Many2one('account.account', domain="[('account_type', '=', 'liability_payable')]",
                                           string='Purchase Order Account')
    oqb_asset_account = fields.Many2one('account.account', domain="[('account_type', '=', 'asset_current')]",
                                        string='Product Asset Account')
    oqb_product_income_account = fields.Many2one('account.account', domain="[('account_type', '=', 'income')]",
                                        string='Product Income Account')
    oqb_product_expense_account = fields.Many2one('account.account', domain="[('account_type', '=', 'expense_direct_cost')]",
                                        string='Product Expense Account')

    # ---------------------------------- Chart of Accounts Fields ------------------------------------- #
    is_coa_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_coa_last_sync_date = fields.Datetime(tracking=True)
    odoo_coa_dropdown_mapping = fields.Text(tracking=True)
    is_coa_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_coa_last_sync_date = fields.Datetime(tracking=True)
    quickbook_coa_dropdown_mapping = fields.Text()
    quickbook_coa_last_id = fields.Text(string='Quickbook Chart of Account Last Id', default=0)
    odoo_coa_last_id = fields.Text(string='Odoo Chart of Account Last Id', default=0)
    coa_line_ids = fields.One2many("oqb.coa.lines", "coa_mapper_id", string="Chart of Account Lines")

    # ---------------------------------- customer Fields ------------------------------------- #
    is_customer_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_customer_last_sync_date = fields.Datetime(tracking=True)
    odoo_customer_dropdown_mapping = fields.Text(tracking=True)
    is_customer_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_customer_last_sync_date = fields.Datetime(tracking=True)
    quickbook_customer_dropdown_mapping = fields.Text()
    quickbook_customer_last_id = fields.Text(string='Quickbook Customer Last Id', default=0)
    odoo_customer_last_id = fields.Text(string='Odoo Customer Last Id', default=0)
    customer_line_ids = fields.One2many("oqb.customer.lines", "customer_mapper_id", string="Customer Lines")


    # ---------------------------------- Vendor Fields ------------------------------------- #
    is_vendor_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_vendor_last_sync_date = fields.Datetime(tracking=True)
    odoo_vendor_dropdown_mapping = fields.Text(tracking=True)
    is_vendor_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_vendor_last_sync_date = fields.Datetime(tracking=True)
    quickbook_vendor_dropdown_mapping = fields.Text()
    quickbook_vendor_last_id = fields.Text(default=0)
    odoo_vendor_last_id = fields.Text(default=0)
    vendor_line_ids = fields.One2many("oqb.vendor.lines", "vendor_mapper_id", string="Vendor Lines")

    # ---------------------------------- Sales Order Fields ------------------------------------- #
    is_sale_order_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_sale_order_last_sync_date = fields.Datetime(tracking=True)
    odoo_sale_order_dropdown_mapping = fields.Text(tracking=True)
    is_sale_order_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_sale_order_last_sync_date = fields.Datetime(tracking=True)
    quickbook_sale_order_dropdown_mapping = fields.Text()
    quickbook_sale_order_last_id = fields.Text(default=0)
    odoo_sale_order_last_id = fields.Text(default=0)
    sale_order_line_ids = fields.One2many("oqb.saleorder.lines", "sale_order_mapper_id", string="Sale Order Lines")


    # ---------------------------------- Invoices Fields ------------------------------------- #
    is_invoice_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_invoice_last_sync_date = fields.Datetime(tracking=True)
    odoo_invoice_dropdown_mapping = fields.Text(tracking=True)
    is_invoice_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_invoice_last_sync_date = fields.Datetime(tracking=True)
    quickbook_invoice_dropdown_mapping = fields.Text()
    quickbook_invoice_last_id = fields.Text(default=0)
    odoo_invoice_last_id = fields.Text(default=0)
    invoice_line_ids = fields.One2many("oqb.invoice.lines", "invoice_mapper_id", string="Invoice Lines")

    # ---------------------------------- Credit Notes Fields ------------------------------------- #
    is_credit_note_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_credit_note_last_sync_date = fields.Datetime(tracking=True)
    odoo_credit_note_dropdown_mapping = fields.Text(tracking=True)
    is_credit_note_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_credit_note_last_sync_date = fields.Datetime(tracking=True)
    quickbook_credit_note_dropdown_mapping = fields.Text()
    quickbook_credit_note_last_id = fields.Text(default=0)
    odoo_credit_note_last_id = fields.Text(default=0)
    credit_note_line_ids = fields.One2many("oqb.cdt.lines", "credit_note_mapper_id", string="Credit Note Lines")

    # ---------------------------------- Purchase Orders Fields ------------------------------------- #
    is_purchase_order_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_purchase_order_last_sync_date = fields.Datetime(tracking=True)
    odoo_purchase_order_dropdown_mapping = fields.Text(tracking=True)
    is_purchase_order_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_purchase_order_last_sync_date = fields.Datetime(tracking=True)
    quickbook_purchase_order_dropdown_mapping = fields.Text()
    quickbook_purchase_order_last_id = fields.Text(default=0)
    odoo_purchase_order_last_id = fields.Text(default=0)
    pco_line_ids = fields.One2many("oqb.pco.lines", "pco_mapper_id", string="Purchase Order Lines")

    # ---------------------------------- Vendor Bill Fields ------------------------------------- #
    is_purchase_bill_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_purchase_bill_last_sync_date = fields.Datetime(tracking=True)
    odoo_purchase_bill_dropdown_mapping = fields.Text(tracking=True)
    is_purchase_bill_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_purchase_bill_last_sync_date = fields.Datetime(tracking=True)
    quickbook_purchase_bill_dropdown_mapping = fields.Text()
    quickbook_purchase_bill_last_id = fields.Text(default=0)
    odoo_purchase_bill_last_id = fields.Text(default=0)
    pcb_line_ids = fields.One2many("oqb.pcb.lines", "pcb_mapper_id", string="Purchase Bill Lines")

    # ---------------------------------- Refund Fields ------------------------------------- #
    is_refund_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_refund_last_sync_date = fields.Datetime(tracking=True)
    odoo_refund_dropdown_mapping = fields.Text(tracking=True)
    is_refund_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_refund_last_sync_date = fields.Datetime(tracking=True)
    quickbook_refund_dropdown_mapping = fields.Text()
    quickbook_refund_last_id = fields.Text(default=0)
    odoo_refund_last_id = fields.Text(default=0)
    refund_line_ids = fields.One2many("oqb.refund.lines", "refund_mapper_id", string="Refund Lines")

    # ---------------------------------- Product Fields ------------------------------------- #
    is_product_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_product_last_sync_date = fields.Datetime(tracking=True)
    odoo_product_dropdown_mapping = fields.Text(tracking=True)
    is_product_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_product_last_sync_date = fields.Datetime(tracking=True)
    quickbook_product_dropdown_mapping = fields.Text()
    product_line_ids = fields.One2many("oqb.product.lines", "product_mapper_id", string="Product Lines")
    quickbook_product_last_id = fields.Char(string='Product Last ID', default=0)
    odoo_product_last_id = fields.Char(string='Product Last ID', default=0)

    # ---------------------------------- Employee Fields ------------------------------------- #
    is_employee_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_employee_last_sync_date = fields.Datetime(tracking=True)
    odoo_employee_dropdown_mapping = fields.Text(tracking=True)
    is_employee_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_employee_last_sync_date = fields.Datetime(tracking=True)
    quickbook_employee_dropdown_mapping = fields.Text()
    employee_line_ids = fields.One2many("oqb.employee.lines", "employee_mapper_id", string="Employee Lines")
    quickbook_employee_last_id = fields.Char(string='Employee Last ID',default=0)
    odoo_employee_last_id = fields.Char(string='Employee Last ID', default=0)

    # ---------------------------------- Department Fields ------------------------------------- #
    is_department_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_department_last_sync_date = fields.Datetime(tracking=True)
    odoo_department_dropdown_mapping = fields.Text(tracking=True)
    is_department_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_department_last_sync_date = fields.Datetime(tracking=True)
    quickbook_department_dropdown_mapping = fields.Text()
    department_line_ids = fields.One2many("oqb.dpt.lines", "dpt_mapper_id", string="Department Lines")
    quickbook_department_last_id = fields.Char(string='Department Last ID', default=0)
    odoo_department_last_id = fields.Char(string='Department Last ID', default=0)

    # ---------------------------------- Customer Payments Fields ------------------------------------- #
    is_customer_payment_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_customer_payment_last_sync_date = fields.Datetime(tracking=True)
    odoo_customer_payment_dropdown_mapping = fields.Text(tracking=True)
    is_customer_payment_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_customer_payment_last_sync_date = fields.Datetime(tracking=True)
    quickbook_customer_payment_dropdown_mapping = fields.Text()
    quickbook_customer_payment_last_id = fields.Text(default=0)
    odoo_customer_payment_last_id = fields.Text(default=0)
    cpt_line_ids = fields.One2many("oqb.cpt.lines", "cpt_mapper_id", string="Customer Payment Lines")

    # ---------------------------------- Vendor Payments Fields ------------------------------------- #
    is_vendor_payment_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_vendor_payment_last_sync_date = fields.Datetime(tracking=True)
    odoo_vendor_payment_dropdown_mapping = fields.Text(tracking=True)
    is_vendor_payment_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_vendor_payment_last_sync_date = fields.Datetime(tracking=True)
    quickbook_vendor_payment_dropdown_mapping = fields.Text()
    quickbook_vendor_payment_last_id = fields.Text(default=0)
    odoo_vendor_payment_last_id = fields.Text(default=0)
    vpt_line_ids = fields.One2many("oqb.vpt.lines", "vpt_mapper_id", string="Vendor Payment Lines")

    # ---------------------------------- Payment Term Fields ------------------------------------- #
    is_pyt_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_pyt_last_sync_date = fields.Datetime(tracking=True)
    odoo_pyt_dropdown_mapping = fields.Text(tracking=True)
    is_pyt_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_pyt_last_sync_date = fields.Datetime(tracking=True)
    quickbook_pyt_dropdown_mapping = fields.Text()
    pyt_line_ids = fields.One2many("oqb.pyt.lines", "pyt_mapper_id", string="Payment Term Lines")
    quickbook_pyt_last_id = fields.Char(string='Payment Term Last ID', default=0)
    odoo_pyt_last_id = fields.Char(string='Payment Term Last ID', default=0)

    # ---------------------------------- Payment Method Fields ------------------------------------- #
    is_pym_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_pym_last_sync_date = fields.Datetime(tracking=True)
    odoo_pym_dropdown_mapping = fields.Text(tracking=True)
    is_pym_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_pym_last_sync_date = fields.Datetime(tracking=True)
    quickbook_pym_dropdown_mapping = fields.Text()
    pym_line_ids = fields.One2many("oqb.pym.lines", "pym_mapper_id", string="Payment Method Lines")
    quickbook_pym_last_id = fields.Char(string='Payment Method Last ID', default=0)
    odoo_pym_last_id = fields.Char(string='Payment Method Last ID', default=0)

    # ---------------------------------- Account Tax Fields ------------------------------------- #
    is_account_tax_sync_odoo_to_quickbook = fields.Boolean(tracking=True)
    odoo_account_tax_last_sync_date = fields.Datetime(tracking=True)
    odoo_account_tax_dropdown_mapping = fields.Text(tracking=True)
    is_account_tax_sync_quickbook_to_odoo = fields.Boolean(tracking=True)
    quickbook_account_tax_last_sync_date = fields.Datetime(tracking=True)
    quickbook_account_tax_dropdown_mapping = fields.Text()
    account_tax_line_ids = fields.One2many("oqb.atx.lines", "atx_mapper_id", string="Payment Method Lines")
    quickbook_account_tax_last_id = fields.Char(string='Account Tax Last ID', default=0)
    odoo_account_tax_last_id = fields.Char(string='Account Tax Last ID', default=0)

    # -------------------------------------- Currency Fields -------------------------------- #

    odoo_default_currency = fields.Many2one('res.currency', string="Odoo Currency", default=lambda self: self.env.company.currency_id.id,)
    odoo_currency_list = fields.Text(string="Odoo Currency List")
    quickbook_default_currency = fields.Char(string="Quickbook Currency")
    quickbook_currency_list = fields.Text(string="Quickbook Currency List")

    # ----------------------------------- Delete Logger Fields --------------------------- #

    remove_log_scheduler = fields.Boolean(tracking=True)
    remove_log_month = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                                         ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12')],
                                        string='Remove Last Month Log', default='1')

    # ---------------------------------------------------------------------------------------------------- #

    # --------------------------- Schedular To Generate Access Token --------------------- #

    def _cron_generate_access_token(self):
        schedulers = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '!=', False)])
        for schedular in schedulers:
            schedular.generate_access_token('schedular')


    # ------------------------------- Fetch All Module Data Odoo and Quickbook Schedular -------------------------- #

    @api.model
    def _cron_fetch_and_store_odoo_quickbook_records_scheduler(self):
        schedulers = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '!=', False)])

        if schedulers:
            for scheduler in schedulers:
                scheduler.search(
                    ['|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|','|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
                     ('is_coa_sync_odoo_to_quickbook', '=', True), ('is_coa_sync_quickbook_to_odoo', '=', True),
                     ('is_customer_sync_odoo_to_quickbook', '=', True), ('is_customer_sync_quickbook_to_odoo', '=', True),
                     ('is_product_sync_odoo_to_quickbook', '=', True), ('is_product_sync_quickbook_to_odoo', '=', True),
                     ('is_sale_order_sync_odoo_to_quickbook', '=', True), ('is_sale_order_sync_quickbook_to_odoo', '=', True),
                     ('is_invoice_sync_odoo_to_quickbook', '=', True), ('is_invoice_sync_quickbook_to_odoo', '=', True),
                     ('is_credit_note_sync_odoo_to_quickbook', '=', True), ('is_credit_note_sync_quickbook_to_odoo', '=', True),
                     ('is_customer_payment_sync_odoo_to_quickbook', '=', True), ('is_customer_payment_sync_quickbook_to_odoo', '=', True),
                     ('is_vendor_sync_odoo_to_quickbook', '=', True), ('is_vendor_sync_quickbook_to_odoo', '=', True),
                     ('is_purchase_order_sync_odoo_to_quickbook', '=', True), ('is_purchase_order_sync_quickbook_to_odoo', '=', True),
                     ('is_purchase_bill_sync_odoo_to_quickbook', '=', True), ('is_purchase_bill_sync_quickbook_to_odoo', '=', True),
                     ('is_refund_sync_odoo_to_quickbook', '=', True), ('is_refund_sync_quickbook_to_odoo', '=', True),
                     ('is_vendor_payment_sync_odoo_to_quickbook', '=', True), ('is_vendor_payment_sync_quickbook_to_odoo', '=', True),
                     ('is_pyt_sync_odoo_to_quickbook', '=', True), ('is_pyt_sync_quickbook_to_odoo', '=', True),
                     ('is_pym_sync_odoo_to_quickbook', '=', True), ('is_pym_sync_quickbook_to_odoo', '=', True),
                     ('is_account_tax_sync_odoo_to_quickbook', '=', True), ('is_account_tax_sync_quickbook_to_odoo', '=', True),
                     ('is_employee_sync_odoo_to_quickbook', '=', True), ('is_employee_sync_quickbook_to_odoo', '=', True),
                     ('is_department_sync_odoo_to_quickbook', '=', True), ('is_department_sync_quickbook_to_odoo', '=', True),
                ])

                scheduler.fetch_schedular_checkboxes(scheduler)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': _('Instance is not connected. Please check the connection settings.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    # --------------------------------- Fetch Scheduler Checkbox ----------------------------------- #
    @api.model
    def fetch_schedular_checkboxes(self, schedular):
        stages = [
                    ('not_started', 'chart_of_account_qto', schedular.is_coa_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_coa),
                    ('chart_of_account_qto', 'customer_otq', schedular.is_coa_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_coa),
                    ('customer_otq', 'customer_qto', schedular.is_customer_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_customer),
                    ('customer_qto', 'product_otq', schedular.is_customer_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_customer),
                    ('product_otq', 'product_qto', schedular.is_product_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_product),
                    ('product_qto', 'sale_order_otq', schedular.is_product_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_product),
                    ('sale_order_otq', 'sale_order_qto', schedular.is_sale_order_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_sale_order),
                    ('sale_order_qto', 'invoice_otq', schedular.is_sale_order_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_sale_order),
                    ('invoice_otq', 'invoice_qto', schedular.is_invoice_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_invoice),
                    ('invoice_qto', 'credit_note_otq', schedular.is_invoice_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_invoice),
                    ('credit_note_otq', 'credit_note_qto', schedular.is_credit_note_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_credit_note),
                    ('credit_note_qto', 'customer_payment_otq', schedular.is_credit_note_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_credit_note),
                    ('customer_payment_otq', 'customer_payment_qto', schedular.is_customer_payment_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_customer_payment),
                    ('customer_payment_qto', 'vendor_otq', schedular.is_customer_payment_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_customer_payment),
                    ('vendor_otq', 'vendor_qto', schedular.is_vendor_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_vendor),
                    ('vendor_qto', 'purchase_order_otq', schedular.is_vendor_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_vendor),
                    ('purchase_order_otq', 'purchase_order_qto', schedular.is_purchase_order_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_purchase_order),
                    ('purchase_order_qto', 'vendor_bill_otq', schedular.is_purchase_order_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_purchase_order),
                    ('vendor_bill_otq', 'vendor_bill_qto', schedular.is_purchase_bill_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_purchase_bill),
                    ('vendor_bill_qto', 'refund_otq', schedular.is_purchase_bill_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_purchase_bill),
                    ('refund_otq', 'refund_qto', schedular.is_refund_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_refund),
                    ('refund_qto', 'vendor_payment_otq', schedular.is_refund_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_refund),
                    ('vendor_payment_otq', 'vendor_payment_qto', schedular.is_vendor_payment_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_vendor_payment),
                    ('vendor_payment_qto', 'payment_term_otq', schedular.is_vendor_payment_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_vendor_payment),
                    ('payment_term_otq', 'payment_term_qto', schedular.is_pyt_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_payment_term),
                    ('payment_term_qto', 'payment_method_otq', schedular.is_pyt_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_payment_term),
                    ('payment_method_otq', 'payment_method_qto', schedular.is_pym_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_payment_method),
                    ('payment_method_qto', 'account_tax_qto', schedular.is_pym_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_payment_method),
                    ('account_tax_qto', 'employee_otq', schedular.is_account_tax_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_account_tax),
                    ('employee_otq', 'employee_qto', schedular.is_employee_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_employee),
                    ('employee_qto', 'department_otq', schedular.is_employee_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_employee),
                    ('department_otq', 'department_qto', schedular.is_department_sync_odoo_to_quickbook, schedular.odoo_to_quickbook_department),
                    ('department_qto', 'completed', schedular.is_department_sync_quickbook_to_odoo, schedular.quickbook_to_odoo_department),
                ]


        try:
            for current_stage, next_stage, sync_flag, sync_method in stages:
                if schedular.progress_stage == current_stage:
                    if sync_flag:
                        sync_method(called_by_scheduler=True)
                    schedular.progress_stage = next_stage
                    schedular.env.cr.commit()  # Commit only after each stage is complete

            if schedular.progress_stage == 'completed':
                schedular.progress_stage = 'not_started'
                schedular.env.cr.commit()

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Sync Odoo and Quickbook Records By Schedular'
            description = 'Error occurred while Running Scheduler For Create/Update Odoo and Quickbook Record'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, '', description, '', '', operation, 'schedular',
                                                             schedular.name, error_type)

    def generate_authorization_url(self):
        """
        Generate QuickBooks OAuth2 authorization URL
        """
        self.ensure_one()

        if not self.client_id or not self.redirect_uri or not self.scope_code:
            raise ValidationError("Ensure 'client_id', 'redirect_uri', and 'scope_code' are set.")

        base_url = "https://appcenter.intuit.com/connect/oauth2"
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': self.scope_code,
            'state': str(self.id),  # record id will come back in callback
        }

        auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"

        self.authorization_url = auth_url
        self.access_token = ''
        self.refresh_token = ''
        self.authorize_code = ''  # reset before new request

        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'new',
        }

    def generate_access_token(self, operation_type='manually'):
        """
        Generate refresh token and access token using the authorization code.
        """
        if not self.is_connected:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("'Is Connected' must be enabled to find the instance."),
                    'type': 'danger',
                    'sticky': False,
                }
            }

        success_count = 0
        failure_count = 0

        if not self.authorize_code:
            raise ValidationError("Authorization Code is missing. Generate it from the authorization URL.")

        # Exchange Authorization Code for Refresh Token
        if not self.refresh_token:
            token_response = requests.post(
                self.token_api_url,
                data={
                    "grant_type": "authorization_code",
                    "code": self.authorize_code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            response_data = self.handle_response(
                token_response, {}, '', '', '', '', 'get', 'odoo', operation_type, self
            )

            if response_data:
                self.refresh_token = response_data.get("refresh_token")

        # Exchange Refresh Token for Access Token
        access_response = requests.post(
            self.token_api_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        response_data = self.handle_response(
            access_response, {}, '', '', '', '', 'get', 'odoo', operation_type, self
        )

        if response_data:
            self.access_token = response_data.get("access_token")
            self.refresh_token = response_data.get("refresh_token")
            success_count += 1
        else:
            failure_count += 1

        # Return final notification after all instances are processed
        if success_count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _(f'Access Token Successfully Generated'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Failed to Generate Access Token for all instances.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    # ---------------------------- Handle HTTP responses ---------------------------- #

    def handle_response(self, response, payload, module_name, model_name, logger_name, record_id, method, operation,
                        operation_type, instance_id):
        """
        Common method to handle HTTP responses.

        Args:
            response (requests.Response): The HTTP response object.

        Returns:
            dict or None: The response data if successful, None otherwise.
        """
        if method == 'get':
            description = f"Failed to fetch Quickbook {module_name} data."
        elif method == 'post':
            description = f"Failed to create Quickbook {module_name} data."
        else:
            description = f"Failed to update Quickbook {module_name} data."
        if response.status_code in [200, 201, 207]:
            response_data = response.json()
            if module_name and method != 'post' and response_data['QueryResponse'] :
                return response_data['QueryResponse'][module_name]
            elif module_name and method != 'post':
                return response_data['QueryResponse']
            else:
                return response_data
        elif response.status_code == 204:
            return None
        elif response.status_code == 304:
            return None
        else:
            error_details = f"{response.status_code} - {response.text}"
            self.env['oqb.dry.mixin'].http_log_error(error_details, logger_name, description, payload, response.text,
            model_name, record_id,operation, operation_type, instance_id.name, f"{response.status_code}")
            return None

    def test_connection(self):
        """
            Test the connection to QuickBooks using the access token.
            Fetches Company Info to verify if the token is valid.
            """
        # Check for missing fields and add to the list
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        if instance_id:
            missing_fields = []
            if not self.access_token:
                missing_fields.append("API Token")
            if not self.company_id:
                missing_fields.append("Company ID")
            if not self.base_api_url:
                missing_fields.append("Base API URL")

            if missing_fields:
                # Construct the dynamic message
                missing_fields_message = ", ".join(missing_fields)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Missing Configuration'),
                        'message': _('The following fields are missing: %s') % missing_fields_message,
                        'type': 'danger',
                        'sticky': False,
                    }
                }
            operation = f'Test Connection'
            response_data = self.env['oqb.dry.mixin'].fetch_company_info(instance_id, operation, 'companyinfo')

            if response_data:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Connection set successfully.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Failed'),
                        'message': _('Failed to establish connection. Check API Token.'),
                        'type': 'danger',
                        'sticky': False,
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("'Is Connected' must be enabled to find the instance."),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_import_currency(self):
        """Receives Currencies from odoo and quickbook"""
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'customer', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        if instance_id:
            self.env['oqb.dry.mixin'].get_odoo_quickbook_currencies(instance_id, 'manually')
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': _('Instance is not connected. Please check the connection settings.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    # --------------------- Test the API connection to Quickbook and Odoo Methods ---------------------- #

    def test_connection_methods(self, operation, logger_name, model_name, operation_type, current_instance):
        """
        Test the API connection to Quickbook.

        This method tests the connection to Quickbook using the provided API token. It attempts to fetch person fields
        from Quickbook and returns a notification indicating whether the connection was successful or failed.

        Returns:
            dict: An action dictionary for displaying a notification to the user indicating the result of the connection test.

        """
        access_token, pagination_size, base_api_url, minor_version, quickbook_company_id, odoo_company_id = self.env[
            'oqb.dry.mixin'].get_oqb_instance_data(current_instance)

        if not current_instance:
            return False, {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('API Token Missing'),
                    'message': _(
                        "Please check the 'is connected' checkbox to activate the instance."),
                    'type': 'danger',
                    'sticky': False,
                }
            }

        if not access_token:
            return False, {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('API Token Missing'),
                    'message': _('API Token is not provided.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

        # Endpoint to fetch Company Info
        company_info_url = f"{base_api_url}/{quickbook_company_id}/companyinfo/{quickbook_company_id}"

        # Prepare headers
        headers = self.env['oqb.dry.mixin'].get_headers(access_token)

        # Make a GET request to the API endpoint
        response = requests.get(company_info_url, data={}, headers=headers)

        response_data = self.handle_response(response, {}, '', '', '',
        '', 'get', operation,'manually', current_instance)

        if response_data:
            return True, {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': _('Connection set successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            description = f'Failed to complete the operation. Check the API Token or try again.'
            error_details = f"{response.status_code} - {response.text}"
            self.env['oqb.dry.mixin'].http_log_error(error_details, logger_name, description, {}, response.text,
            model_name, '',operation, operation_type, current_instance.name, f"{response.status_code}")
            return False, {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Failed'),
                    'message': _('Failed to complete the operation. Check the API Token or try again.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    # -------------------- Fetch and synchronize records for Quickbook and Odoo ---------------- #
    def fetch_records(self, instance_id, last_sync_date, model_name, method_name, scheduler_field_name,
                      operation_type, called_by_scheduler=False):
        """
        Fetch and synchronize records from Quickbook to Odoo.

        This method fetches records from Quickbook based on the provided model name and updates the corresponding
        records in Odoo. It calls the specified method on the model to perform the synchronization.

        Args:
            instance_id (recordset): The Quickbook instance configuration.
            last_sync_date (datetime): The date of the last synchronization.
            model_name (str): The name of the model to fetch records from.
            method_name (str): The name of the method to call for fetching and updating records.

        Returns:
            dict: An action dictionary for displaying a notification to the user if the instance is not connected.

        """
        if instance_id.is_connected:
            if not called_by_scheduler and getattr(instance_id, scheduler_field_name):
                # Scheduler is enabled, show a sticky warning message
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'message': _('Scheduler is currently enabled. Manual sync is disabled.'),
                        'type': 'warning',
                        'sticky': False,
                    }
                }
            else:
                # Proceed with manual synchronization
                getattr(self.env[model_name], method_name)(instance_id, last_sync_date, operation_type)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': _('Instance is not connected. Please check the connection settings.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

    # ----- Apply a rainbow effect when importing fields for entities from Quickbook to Odoo. ------ #
    @api.model
    def action_rainbow_effect(self, arg, name):
        """
            Apply a rainbow effect when importing fields for entities from Quickbook to Odoo.
                Args:
                    arg (int): The number of fields successfully imported.
                    name (str): The name of the entity for which fields are imported.
                create date: 2 April 2024.
                Returns:
                    dict or None: A dictionary containing the effect parameters if `arg` is truthy,
                                  otherwise returns None.
        """
        if arg:
            return {'effect': {'fadeout': 'slow',
                               'message': f"{arg} {name} fields stored in odoo successfully",
                               'type': 'rainbow_man'}}
        return None

    def action_import_customer_fields(self):
        """Import fields for customer from Quickbook and Odoo."""
        # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)], limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'customer', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        customer_fields = self.env['oqb.customer.mapper'].fetch_and_store_customer_fields(instance_id)
        return self.action_rainbow_effect(customer_fields, 'customer')

    def action_import_chart_of_account_fields(self):
        """Import fields for accounts from Quickbook and Odoo."""
        # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
            'chart of account', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        accounts_fields = self.env['oqb.coa.mapper'].fetch_and_store_chart_of_account_fields(instance_id)
        return self.action_rainbow_effect(accounts_fields, 'chart of account')

    def action_import_product_fields(self):
        """Import fields for accounts from Quickbook and Odoo."""
        # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'product', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        product_fields = self.env['oqb.product.mapper'].fetch_and_store_product_fields(instance_id)
        return self.action_rainbow_effect(product_fields, 'product')

    def action_import_sale_order_fields(self):
        """Import fields for accounts from Quickbook and Odoo."""
        # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'sale order', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        sale_order_fields = self.env['oqb.salereceipt.mapper'].fetch_and_store_sale_receipt_fields(instance_id)
        return self.action_rainbow_effect(sale_order_fields, 'sale order')

    def action_import_invoice_fields(self):
        """Import fields for invoice from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'invoice', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        invoice_fields = self.env['oqb.invoice.mapper'].fetch_and_store_invoice_fields(instance_id)
        return self.action_rainbow_effect(invoice_fields, 'invoice')

    def action_import_credit_note_fields(self):
        """Import fields for credit note from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'credit note', '','manually', instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        invoice_fields = self.env['oqb.cdt.mapper'].fetch_and_store_credit_note_fields(instance_id)
        return self.action_rainbow_effect(invoice_fields, 'credit note')

    def action_import_customer_payment_fields(self):
        """Import fields for invoice from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'customer payment', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        customer_payment_fields = self.env['oqb.cpt.mapper'].fetch_and_store_customer_payment_fields(instance_id)
        return self.action_rainbow_effect(customer_payment_fields, 'customer payment')

    def action_import_vendor_fields(self):
        """Import fields for vendor from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'vendor', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        vendor_fields = self.env['oqb.vendor.mapper'].fetch_and_store_vendor_fields(instance_id)
        return self.action_rainbow_effect(vendor_fields, 'vendor')


    def action_import_purchase_order_fields(self):
        """Import fields for vendor from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'purchase order', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        purchase_order_fields = self.env['oqb.purchaseorder.mapper'].fetch_and_store_purchase_order_fields(instance_id)
        return self.action_rainbow_effect(purchase_order_fields, 'purchase order')

    def action_import_purchase_bill_fields(self):
        """Import fields for purchase_bill from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'purchase bill', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        purchase_bill_fields = self.env['oqb.purchasebill.mapper'].fetch_and_store_purchase_bill_fields(instance_id)
        return self.action_rainbow_effect(purchase_bill_fields, 'purchase bill')

    def action_import_refund_fields(self):
        """Import fields for refund from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'refund', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        purchase_bill_fields = self.env['oqb.refund.mapper'].fetch_and_store_refund_fields(instance_id)
        return self.action_rainbow_effect(purchase_bill_fields, 'refund')

    def action_import_vendor_payment_fields(self):
        """Import fields for vendor_payment from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'vendor payment', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        vendor_payment_fields = self.env['oqb.vpt.mapper'].fetch_and_store_vendor_payment_fields(instance_id)
        return self.action_rainbow_effect(vendor_payment_fields, 'vendor payment')

    def action_import_employee_fields(self):
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'employee', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        employee_fields = self.env['oqb.employee.mapper'].fetch_and_store_employee_fields(instance_id)
        return self.action_rainbow_effect(employee_fields, 'employee')

    def action_import_department_fields(self):
        """Import fields for department from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'department', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        department_fields = self.env['oqb.department.mapper'].fetch_and_store_department_fields(instance_id)
        return self.action_rainbow_effect(department_fields, 'department')

    def action_import_payment_term_fields(self):
        """Import fields for Payment Term from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'payment term', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        payment_term_fields = self.env['oqb.pyt.mapper'].fetch_and_store_payment_term_fields(instance_id)
        return self.action_rainbow_effect(payment_term_fields, 'payment term')

    def action_import_payment_method_fields(self):
        """Import fields for Payment Method from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'payment method', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        payment_method_fields = self.env['oqb.pym.mapper'].fetch_and_store_payment_method_fields(instance_id)
        return self.action_rainbow_effect(payment_method_fields, 'payment method')


    def action_import_account_tax_fields(self):
        """Import fields for Account Tax from Quickbook and Odoo."""
        # # Call test_connection_methods to check if the connection is successful
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Fetch Quickbook and Odoo Fields',
        'account tax', '','manually', instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        payment_method_fields = self.env['oqb.atx.mapper'].fetch_and_store_account_tax_fields(instance_id)
        return self.action_rainbow_effect(payment_method_fields, 'account tax')

    def odoo_to_quickbook_coa(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Customer Odoo to Quickbook', 'chart of account',
        'odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_coa_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.account',
                                  'fetch_coa_from_odoo', 'is_coa_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_coa(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Chart of Account Quickbook to Odoo',
        'chart of account','odoo', operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_coa_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.account',
        'fetch_account_from_quickbook', 'is_coa_sync_quickbook_to_odoo', operation_type,
                                  called_by_scheduler)

    def odoo_to_quickbook_customer(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Customer Odoo to Quickbook',
            'customer','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_customer_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'res.partner',
                                  'fetch_customer_from_odoo', 'is_customer_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_customer(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)], limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Customer Quickbook to Odoo', 'customer', 'odoo',
                                                                  operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_customer_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'res.partner',
                                  'fetch_customer_from_quickbook', 'is_customer_sync_quickbook_to_odoo', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_product(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Chart of Product Quickbook to Odoo',
        'product','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_product_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'product.template',
                                  'fetch_product_from_quickbook', 'is_product_sync_quickbook_to_odoo', operation_type,
                                  called_by_scheduler)

    def odoo_to_quickbook_product(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Product Odoo to Quickbook', 'product',
        'quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_product_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'product.template',
                                  'fetch_product_from_odoo', 'is_product_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def odoo_to_quickbook_sale_order(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Sale Order Odoo to Quickbook', 'sale order',
        'quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_sale_order_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'sale.order',
                                  'fetch_sale_order_from_odoo', 'is_sale_order_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_sale_order(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Sales Order Quickbook to Odoo',
              'sale order','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_sale_order_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'sale.order',
                                  'fetch_sale_order_from_quickbook', 'is_sale_order_sync_quickbook_to_odoo', operation_type,
                                  called_by_scheduler)

    def odoo_to_quickbook_invoice(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Invoice Odoo to Quickbook', 'invoice',
       'quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_invoice_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
                                  'fetch_invoice_from_odoo', 'is_invoice_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_invoice(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Invoice Quickbook to Odoo',
        'invoice','odoo', operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_invoice_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
        'fetch_invoice_from_quickbook', 'is_invoice_sync_quickbook_to_odoo',
        operation_type,called_by_scheduler)

    def odoo_to_quickbook_credit_note(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Credit Note Odoo to Quickbook', 'credit note',
        'quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_credit_note_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
                                  'fetch_credit_note_from_odoo', 'is_credit_note_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_credit_note(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Credit Note Quickbook to Odoo',
          'credit note','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_credit_note_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
         'fetch_credit_note_from_quickbook', 'is_credit_note_sync_quickbook_to_odoo',
          operation_type,called_by_scheduler)

    def odoo_to_quickbook_customer_payment(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Customer Payment Odoo to Quickbook',
        'customer payment','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_customer_payment_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.payment',
        'fetch_customer_payment_from_odoo', 'is_customer_payment_sync_odoo_to_quickbook', operation_type,
        called_by_scheduler)

    def quickbook_to_odoo_customer_payment(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Customer Payment Quickbook to Odoo',
         'customer payment','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_customer_payment_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.payment',
           'fetch_cpt_from_quickbook', 'is_customer_payment_sync_quickbook_to_odoo',
           operation_type, called_by_scheduler)

    def odoo_to_quickbook_vendor(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Vendor Odoo to Quickbook',
            'vendor','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_vendor_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'res.partner',
       'fetch_vendor_from_odoo', 'is_vendor_sync_odoo_to_quickbook', operation_type,
         called_by_scheduler)

    def quickbook_to_odoo_vendor(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Vendor Quickbook to Odoo',
          'vendor','odoo',operation_type, instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        last_sync_date = instance_id.quickbook_vendor_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'res.partner',
        'fetch_vendor_from_quickbook', 'is_vendor_sync_quickbook_to_odoo',
        operation_type,called_by_scheduler)

    def odoo_to_quickbook_purchase_order(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Purchase Order Odoo to Quickbook',
        'purchase order','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_purchase_order_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'purchase.order',
        'fetch_purchase_order_from_odoo', 'is_purchase_order_sync_odoo_to_quickbook', operation_type,
        called_by_scheduler)

    def quickbook_to_odoo_purchase_order(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Purchase Order Quickbook to Odoo',
        'purchase order','odoo',operation_type, instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        last_sync_date = instance_id.quickbook_purchase_order_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'purchase.order',
        'fetch_purchase_order_from_quickbook', 'is_purchase_order_sync_quickbook_to_odoo',
        operation_type,called_by_scheduler)

    def odoo_to_quickbook_purchase_bill(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Purchase Bill Odoo to Quickbook',
               'purchase bill','quickbook',operation_type, instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        last_sync_date = instance_id.odoo_purchase_bill_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
               'fetch_purchase_bill_from_odoo', 'is_purchase_bill_sync_odoo_to_quickbook',
               operation_type,called_by_scheduler)

    def quickbook_to_odoo_purchase_bill(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Purchase Bill Quickbook to Odoo',
           'purchase bill','odoo',operation_type, instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        last_sync_date = instance_id.quickbook_purchase_bill_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
        'fetch_purchase_bill_from_quickbook', 'is_purchase_bill_sync_quickbook_to_odoo',
        operation_type,called_by_scheduler)

    def odoo_to_quickbook_refund(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Refund Odoo to Quickbook', 'refund',
             'quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_refund_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
           'fetch_refund_from_odoo', 'is_refund_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_refund(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Refund Quickbook to Odoo',
                   'refund','odoo',operation_type, instance_id)
        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification
        last_sync_date = instance_id.quickbook_refund_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.move',
               'fetch_refund_from_quickbook', 'is_refund_sync_quickbook_to_odoo',
               operation_type,called_by_scheduler)

    def odoo_to_quickbook_vendor_payment(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Vendor Payment Odoo to Quickbook',
              'vendor payment','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_vendor_payment_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.payment',
               'fetch_vendor_payment_from_odoo', 'is_vendor_payment_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_vendor_payment(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Vendor Payment Quickbook to Odoo',
                  'vendor payment','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_vendor_payment_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.payment',
               'fetch_vpt_from_quickbook', 'is_vendor_payment_sync_quickbook_to_odoo',
               operation_type,called_by_scheduler)


    def odoo_to_quickbook_employee(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Employee Odoo to Quickbook',
                'employee','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_employee_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'hr.employee',
               'fetch_employee_from_odoo', 'is_employee_sync_odoo_to_quickbook',
               operation_type,called_by_scheduler)

    def quickbook_to_odoo_employee(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Employee Quickbook to Odoo',
              'employee','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_employee_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'hr.employee',
              'fetch_employee_from_quickbook', 'is_employee_sync_quickbook_to_odoo',
                operation_type,called_by_scheduler)

    def odoo_to_quickbook_department(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Department Odoo to Quickbook',
                'department','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_department_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'hr.department',
                                  'fetch_department_from_odoo', 'is_department_sync_odoo_to_quickbook', operation_type,
                                  called_by_scheduler)

    def quickbook_to_odoo_department(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '=', company_id)],
                                                      limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Department Quickbook to Odoo',
             'department','odoo', operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_department_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'hr.department',
               'fetch_department_from_quickbook','is_department_sync_quickbook_to_odoo',
                operation_type, called_by_scheduler)

    def odoo_to_quickbook_payment_term(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Payment Term Odoo to Quickbook',
          'payment term','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_pyt_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.payment.term',
              'fetch_payment_term_from_odoo', 'is_pyt_sync_odoo_to_quickbook',
              operation_type,called_by_scheduler)

    def quickbook_to_odoo_payment_term(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Payment Term Quickbook to Odoo',
            'payment term','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_pyt_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.payment.term',
             'fetch_payment_term_from_quickbook', 'is_pyt_sync_quickbook_to_odoo',
             operation_type,called_by_scheduler)

    def odoo_to_quickbook_payment_method(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Payment Method Odoo to Quickbook',
                'payment method','quickbook',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.odoo_pym_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'payment.method',
              'fetch_payment_method_from_odoo', 'is_pym_sync_odoo_to_quickbook',
              operation_type, called_by_scheduler)

    def quickbook_to_odoo_payment_method(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Payment Method Quickbook to Odoo',
         'payment method','odoo', operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_pym_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'payment.method',
               'fetch_payment_method_from_quickbook', 'is_pym_sync_quickbook_to_odoo',
               operation_type, called_by_scheduler)

    def quickbook_to_odoo_account_tax(self, called_by_scheduler=False):
        # Call test_connection_methods to check if the connection is successful
        operation_type = 'manually' if called_by_scheduler is False else 'schedular'
        company_id = self.company_name.id
        instance_id = self.env['oqb.instance'].search(
            [('is_connected', '=', True), ('company_name', '=', company_id)],
            limit=1)
        is_connected, notification = self.test_connection_methods(f'Sync Account Tax Quickbook to Odoo',
             'account tax','odoo',operation_type, instance_id)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        last_sync_date = instance_id.quickbook_account_tax_last_sync_date
        return self.fetch_records(instance_id, last_sync_date, 'account.tax',
           'fetch_account_tax_from_quickbook', 'is_account_tax_sync_quickbook_to_odoo',
           operation_type,called_by_scheduler)

        # ------------------------------------ Customer Mapping ------------------------------------ #

    class OqbCustomerLines(models.Model):
        """Represents lines associated with Quickbook instances for customer."""
        _name = "oqb.customer.lines"
        _description = "Quickbook Instances Customer Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.customer.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name', related='quickbook_fields_label.internal_name',
                                               store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type', related='quickbook_fields_label.field_type',
                                       store=True)
        quickbook_fields_label = fields.Many2one('oqb.customer.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                            string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        customer_mapper_id = fields.Many2one("oqb.instance", string="Accounts Mapper Lines")


    # ------------------------------------ Chart of Account Mapping ------------------------------------ #

    class OqbChartOfAccountsLines(models.Model):
        """Represents lines associated with Quickbook instances for Chart of Account."""
        _name = "oqb.coa.lines"
        _description = "Quickbook Instances Chart of Account Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.coa.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name', related='quickbook_fields_label.internal_name',
                                               store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type', related='quickbook_fields_label.field_type',
                                       store=True)
        quickbook_fields_label = fields.Many2one('oqb.coa.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                            string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        coa_mapper_id = fields.Many2one("oqb.instance", string="Chart of Account Mapper Lines")

    # ------------------------------------ Product Mapping ------------------------------------ #

    class OqbProductLines(models.Model):
        """Represents lines associated with Quickbook instances for product."""
        _name = "oqb.product.lines"
        _description = "Quickbook Instances Product Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.product.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type', related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.product.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        product_mapper_id = fields.Many2one("oqb.instance", string="Product Mapper Lines")

        # ------------------------------------ Sale Order Mapping ------------------------------------ #

    class OqbSaleOrdersLines(models.Model):
        """Represents lines associated with Quickbook instances for sale order."""
        _name = "oqb.saleorder.lines"
        _description = "Quickbook Instances Product Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.salereceipt.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type', related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.salereceipt.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        sale_order_mapper_id = fields.Many2one("oqb.instance", string="Product Mapper Lines")


    # ------------------------------------ Invoice Mapping ------------------------------------ #

    class OqbInvoiceLines(models.Model):
        """Represents lines associated with Quickbook instances for invoice."""
        _name = "oqb.invoice.lines"
        _description = "Quickbook Instances Invoice Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.invoice.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
           related='quickbook_fields_label.internal_name',store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type', related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.invoice.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        invoice_mapper_id = fields.Many2one("oqb.instance", string="Invoice Mapper Lines")

    # ------------------------------------ Customer Payment Mapping ------------------------------------ #

    class OqbCustomerPaymentLines(models.Model):
        """Represents lines associated with Quickbook instances for Customer Payment."""
        _name = "oqb.cpt.lines"
        _description = "Quickbook Instances Customer Payment Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.cpt.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.cpt.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        cpt_mapper_id = fields.Many2one("oqb.instance", string="Customer Payment Mapper Lines")

    # ------------------------------------ Vendor Mapping ------------------------------------ #

    class VendorLines(models.Model):
        """Represents lines associated with Quickbook instances for Vendor."""
        _name = "oqb.vendor.lines"
        _description = "Quickbook Instances Vendor Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.vendor.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.vendor.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        vendor_mapper_id = fields.Many2one("oqb.instance", string="Vendor Mapper Lines")

    # ------------------------------------ Purchase Order Mapping ------------------------------------ #

    class PurchaseOrderLines(models.Model):
        """Represents lines associated with Quickbook instances for Purchase Order."""
        _name = "oqb.pco.lines"
        _description = "Quickbook Instances Purchase Order Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.purchaseorder.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.purchaseorder.mapper', domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        pco_mapper_id = fields.Many2one("oqb.instance", string="Purchase Order Mapper Lines")

    # ------------------------------------ Purchase Bill Mapping ------------------------------------ #

    class PurchaseBillLines(models.Model):
        """Represents lines associated with Quickbook instances for Purchase Bill."""
        _name = "oqb.pcb.lines"
        _description = "Quickbook Instances Purchase Bill Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.purchasebill.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.purchasebill.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        pcb_mapper_id = fields.Many2one("oqb.instance", string="Purchase Bill Mapper Lines")

    # ------------------------------------ Vendor Payment Mapping ------------------------------------ #

    class VendorPaymentLines(models.Model):
        """Represents lines associated with Quickbook instances for Vendor Payment."""
        _name = "oqb.vpt.lines"
        _description = "Quickbook Instances Vendor Payment Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.vpt.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.vpt.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        vpt_mapper_id = fields.Many2one("oqb.instance", string="Vendor Payment Mapper Lines")


 # ------------------------------------ Employee Mapping ------------------------------------ #

    class EmployeeLines(models.Model):
        """Represents lines associated with Quickbook instances for Employee."""
        _name = "oqb.employee.lines"
        _description = "Quickbook Instances Employee Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.employee.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.employee.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        employee_mapper_id = fields.Many2one("oqb.instance", string="Employee Mapper Lines")

        # ------------------------------------ Department Mapping ------------------------------------ #

    class DepartmentLines(models.Model):
        """Represents lines associated with Quickbook instances for Department."""
        _name = "oqb.dpt.lines"
        _description = "Quickbook Instances Department Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.department.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.department.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        dpt_mapper_id = fields.Many2one("oqb.instance", string="Department Mapper Lines")

        # ------------------------------------ Credit Note Mapping ------------------------------------ #

    class CreditNoteLines(models.Model):
        """Represents lines associated with Quickbook instances for Credit Note."""
        _name = "oqb.cdt.lines"
        _description = "Quickbook Instances Credit Note Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.cdt.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.cdt.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        credit_note_mapper_id = fields.Many2one("oqb.instance", string="Credit Note Mapper Lines")

        # ------------------------------------ Refund Mapping ------------------------------------ #

    class RefundLines(models.Model):
        """Represents lines associated with Quickbook instances for Refund."""
        _name = "oqb.refund.lines"
        _description = "Quickbook Instances Refund Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.refund.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.refund.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        refund_mapper_id = fields.Many2one("oqb.instance", string="Refund Mapper Lines")

        # ------------------------------------ Payment Term Mapping ------------------------------------ #

    class PaymentTermLines(models.Model):
        """Represents lines associated with Quickbook instances for Payment Term."""
        _name = "oqb.pyt.lines"
        _description = "Quickbook Instances Payment Term Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.pyt.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.pyt.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        pyt_mapper_id = fields.Many2one("oqb.instance", string="Payment Term Mapper Lines")


 # ------------------------------------ Payment Method Mapping ------------------------------------ #

    class PaymentMethodLines(models.Model):
        """Represents lines associated with Quickbook instances for Payment Method."""
        _name = "oqb.pym.lines"
        _description = "Quickbook Instances Payment Term Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.pym.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.pym.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        pym_mapper_id = fields.Many2one("oqb.instance", string="Payment Method Mapper Lines")

# ------------------------------------ Account Tax Mapping ------------------------------------ #

    class AccountTaxLines(models.Model):
        """Represents lines associated with Quickbook instances for Account Tax."""
        _name = "oqb.atx.lines"
        _description = "Quickbook Instances Account Tax Lines"

        odoo_field_internal_name = fields.Char(string='Odoo Field Name', related='odoo_fields_label.internal_name',
                                               store=True)
        odoo_fields_type = fields.Char(string='Odoo Field Type', related='odoo_fields_label.field_type', store=True)
        odoo_fields_label = fields.Many2one('oqb.atx.mapper', domain=[('system_name', '=', 'Odoo')],
                                            string='Odoo Field Label')

        quickbook_field_internal_name = fields.Char(string='Quickbook Field Name',
                                                    related='quickbook_fields_label.internal_name',
                                                    store=True)
        quickbook_fields_type = fields.Char(string='Quickbook Field Type',
                                            related='quickbook_fields_label.field_type',
                                            store=True)
        quickbook_fields_label = fields.Many2one('oqb.atx.mapper',
                                                 domain=[('system_name', '=', 'QuickBooks')],
                                                 string='Quickbook Field Label', required=True)
        description = fields.Char(string='Description')
        atx_mapper_id = fields.Many2one("oqb.instance", string="Account Tax Mapper Lines")

















