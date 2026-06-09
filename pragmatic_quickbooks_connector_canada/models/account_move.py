# -*- coding: utf-8 -*-
import json
import logging
import traceback
import re
from datetime import datetime
from lxml import etree
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"

    qbo_invoice_id = fields.Char(string=
                                 "QBO Invoice Id", copy=False, help="QBO Invoice Id")
    qbo_credit_memo_id = fields.Char(string=
                                     "QBO Credit Memo Id", copy=False, help="QBO Credit Memo Id")
    qbo_vendor_credit_id = fields.Char(string=
                                       "QBO Vendor Credit Id", copy=False, help="QBO Vendor Credit Id")
    qbo_salesreceipt_id = fields.Char(string=
                                      "QBO Sales receipt Id", copy=False, help="QBO Sales receipt Id")
    qbo_expns_id = fields.Char(string=
                               "QBO Expenses receipt Id", copy=False, help="QBO Expenses Id")
    qbo_deposit_id = fields.Char(string=
                                 "QBO Deposit Id", copy=False, help="QBO Deposit Id")
    qbo_transfer_id = fields.Char(string=
                                  "QBO Transfer Id", copy=False, help="QBO Transfer Id")
    qbo_payment_id = fields.Char(string="QBO Payment Id", copy=False, help="QBO Payment Id")
    qbo_invoice_name = fields.Char(string=
                                   "QBO Invoice Name", copy=False, help="QBO Invoice Name")
    tax_state = fields.Selection(
        [('inclusive', 'Tax Inclusive'), ('exclusive', 'Tax Exclusive'),
         ('notapplicable', 'Not Applicable')],
        string='Tax Status', default="exclusive")
    tax_amount_from_xero = fields.Float('Tax Amount From Quicbooks')

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Set the correct domain for `partner_id`, depending on invoice type """
        result = super(AccountInvoice, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                              submenu=submenu)
        _logger.info("CONTEXT IS ---------------> {}".format(self._context))
        document_type = self._context.get('default_move_type')
        _logger.info("DOCUMENT TYPE IS --> {}".format(document_type))
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            node = doc.xpath("//field[@name='partner_id']")[0]
            if document_type == 'in_invoice':
                _logger.info("DOCUMENT IS OF TYPE VENDOR BILL")
                node.set('domain', "[('supplier_rank', '>=', 1)]")
            if document_type == 'out_invoice':
                _logger.info("DOCUMENT IS OF TYPE CUSTOMER INVOICE")
                node.set('domain', "[('customer_rank', '>=', 1)]")
            if document_type == 'out_refund':
                _logger.info("DOCUMENT IS OF TYPE CUSTOMER CREDIT NOTE")
                node.set('domain', "[('customer_rank', '>=', 1)]")
            if document_type == 'in_refund':
                _logger.info("DOCUMENT IS OF TYPE  VENDOR CREDIT NOTE")
                node.set('domain', "[('supplier_rank', '>=', 1)]")
            result['arch'] = etree.tostring(doc)
        return result

    def check_account_id(self, cust, company=None):
        '''
        This function will check if for a particular product account exists or not
        '''
        try:
            if cust.get('Line'):
                for lines in cust.get('Line'):
                    try:
                        if 'SalesItemLineDetail' in lines and lines.get('SalesItemLineDetail').get('ItemRef').get(
                                'value'):
                            _logger.info("Checking for acc id ......")
                            res_product = self.env['product.product'].search(
                                [('qbo_product_id', '=', lines.get('SalesItemLineDetail').get('ItemRef').get('value')),
                                 ('company_id', '=', company.id)])
                            if res_product:
                                if res_product.property_account_income_id or res_product.categ_id.property_account_income_categ_id:
                                    _logger.info(
                                        "Product/Category has income and expense account set ")
                                    return True
                                else:
                                    raise ValidationError(
                                        "Income account not set for Product or its Category. QBO ID: {}".format(
                                            cust.get('Id') or 'Unknown'))
                    except Exception as line_error:
                        raise ValidationError(
                            "An error occurred while validating product line in QBO ID {}: {}".format(
                                cust.get('Id') or 'Unknown', str(line_error)))
            else:
                raise ValidationError(
                    "No line items found in QBO invoice/vendor bill with ID: {}".format(
                        cust.get('Id') or 'Unknown'))

        except Exception as e:
            raise ValidationError(
                "An error occurred during account check for QBO ID {}: {}".format(
                    cust.get('Id') or 'Unknown', str(e)))

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

    @api.model
    def check_if_lines_present_vendor_bill(self, cust):
        if 'Line' in cust and cust.get('Line'):
            for i in cust.get('Line'):
                if i.get('ItemBasedExpenseLineDetail') or i.get('AccountBasedExpenseLineDetail'):
                    if i.get('ItemBasedExpenseLineDetail'):
                        _logger.info("ItemBasedExpenseLineDetail-----------------> {}".format(
                            i.get('ItemBasedExpenseLineDetail')))
                    elif i.get('AccountBasedExpenseLineDetail'):
                        _logger.info("AccountBasedExpenseLineDetail-----------------> {}".format(
                            i.get('AccountBasedExpenseLineDetail')))
                    return True
                else:
                    _logger.info(
                        "NO ItemBasedExpenseLineDetail or NO AccountBasedExpenseLineDetail ")
                    return False
        else:
            return False

    def create_invoice_dict(self, cust, type, company=None):
        dict_i = {}
        try:
            if type == 'out_invoice' or type == 'out_refund':
                partner_type = 'CustomerRef'
            if type == 'in_invoice':
                partner_type = 'VendorRef'
            if not company:
                company = self.env.company

            try:
                if type == 'in_invoice':
                    res_partner = self.env['res.partner'].search(
                        [('qbo_vendor_id', '=', cust.get(partner_type).get('value')), ('company_id', '=', company.id)],
                        limit=1)
                else:
                    res_partner = self.env['res.partner'].search(
                        [('qbo_customer_id', '=', cust.get(partner_type).get('value')),
                         ('company_id', '=', company.id)],
                        limit=1)
            except Exception as e:
                raise ValidationError("Failed to search partner for QBO ID {}: {}".format(
                    cust.get(partner_type).get('value'), str(e)))

            _logger.info("Partner is ---> {}".format(res_partner))

            if res_partner:
                if cust.get('Id'):
                    dict_i['partner_id'] = res_partner.id
                    dict_i['qbo_invoice_id'] = None if type == 'out_refund' else cust.get('Id')
                    dict_i['company_id'] = company.id
                    dict_i['move_type'] = type
                    dict_i['invoice_date_due'] = cust.get('TxnDate')
                if type == 'out_refund':
                    dict_i['qbo_credit_memo_id'] = cust.get('Id')



                if 'CurrencyRef' in cust and cust.get('CurrencyRef'):
                    if cust.get('CurrencyRef').get('value'):
                        curr = cust.get('CurrencyRef').get('value')
                        _logger.info(
                            "Currency Value for invoice import ------> %s" % (curr))

                        try:
                            currency = self.env['res.currency'].sudo().search(
                                [('active', 'in', [True, False]),
                                 ('name', '=', cust.get('CurrencyRef').get('value'))],
                                limit=1)
                            if not currency.active:
                                currency.active = True
                                # raise UserError(_("Please activate the currency %s") % (cust.get('CurrencyRef').get('value')))
                            dict_i['currency_id'] = int(currency.id)
                            _logger.info(
                                "Currency Object to invoice import ------> %s" % (dict_i))
                        except Exception as e:
                            raise ValidationError("Currency processing failed for QBO ID {}: {}".format(
                                cust.get('Id'), str(e)))

                if res_partner.customer_rank:
                    sale = self.env['account.journal'].search(
                        [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
                    if sale:
                        dict_i['journal_id'] = sale.id
                    else:
                        raise ValidationError("Please Define Sale Journal for QBO ID {}".format(cust.get('Id')))

                if res_partner.supplier_rank:
                    purchase = self.env['account.journal'].search(
                        [('type', '=', 'purchase'), ('company_id', '=', company.id)], limit=1)
                    if purchase:
                        dict_i['journal_id'] = purchase.id
                    else:
                        raise ValidationError("Please Define Purchase Journal for QBO ID {}".format(cust.get('Id')))

                if 'DocNumber' in cust and cust.get('DocNumber'):
                    dict_i['qbo_invoice_name'] = cust.get('DocNumber')
                    # dict_i['number'] = cust.get('DocNumber')

                # to set tax state from qbo
                if 'GlobalTaxCalculation' in cust and cust.get('GlobalTaxCalculation'):
                    if cust.get('GlobalTaxCalculation') == 'TaxExcluded':
                        dict_i['tax_state'] = 'exclusive'
                    elif cust.get('GlobalTaxCalculation') == 'TaxInclusive':
                        dict_i['tax_state'] = 'inclusive'
                    elif cust.get('GlobalTaxCalculation') == 'NotApplicable':
                        dict_i['tax_state'] = 'notapplicable'

                if 'DueDate' in cust and cust.get('DueDate'):
                    dict_i['invoice_date_due'] = cust.get('DueDate')

                if 'TxnDate' in cust and cust.get('TxnDate'):
                    dict_i['invoice_date'] = cust.get('TxnDate')
            else:
                raise ValidationError("No matching partner found for QBO ID {}. Please import {} with QBO ID {}".format(
                    cust.get('Id'), partner_type, str(cust.get(partner_type).get('value'))))

            if not dict_i.get('partner_id'):
                raise UserError("Please Import " + partner_type +
                                " for QBO Id " + str(cust.get(partner_type).get('value')))
            return dict_i

        except Exception as e:
            _logger.error("Invoice processing failed for QBO ID {}: {}".format(cust.get('Id'), str(e)))
            raise

    def import_invoice(self, call_from=None, company=None):
        try:
            if not company:
                try:
                    company = self.env['res.users'].search(
                        [('id', '=', self._uid)]).company_id
                except Exception as e:
                    raise ValidationError("Failed to get user's company info: {}".format(str(e)))
            if not company:
                company = self.env.company
            if company.access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + company.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'

                try:
                    if company.import_invoice_by_date:
                        if company.invoice_import_by == 'crt_dt':
                            query = f"select * from Invoice WHERE Metadata.CreateTime >= '{company.import_invoice_date}' order by Id  MAXRESULTS {company.limit}"
                        elif company.invoice_import_by == 'other_dt':
                            query = f"select * from Invoice WHERE TxnDate >= '{company.import_invoice_date}' order by Id MAXRESULTS {company.limit}"
                        else:
                            query = f"select * from Invoice WHERE Metadata.LastUpdatedTime >= '{company.import_invoice_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Invoice order by Id STARTPOSITION {company.quickbooks_last_invoice_imported_id} MAXRESULTS {company.limit}"
                except Exception as e:
                    raise ValidationError("Error while building invoice query. Last Imported ID: {}. Error: {}".format(
                        company.quickbooks_last_invoice_imported_id, str(e)))

                try:
                    data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                            headers=headers)
                except Exception as e:
                    raise ValidationError("Request to QuickBooks failed. Last Imported ID: {}. Error: {}".format(
                        company.quickbooks_last_invoice_imported_id, str(e)))

                if data.status_code == 200:
                    try:
                        self.create_invoice(data, 'out_invoice', company=company)
                    except (UserError, ValidationError):
                        raise
                    except Exception as e:
                        raise ValidationError(
                            "Invoice creation failed from QBO data. Last Imported ID: {}. Error: {}".format(
                                company.quickbooks_last_invoice_imported_id, str(e)))
                else:
                    raise ValidationError(
                        "Failed to retrieve data from QuickBooks. Status Code: {}. Last Imported ID: {}".format(
                            data.status_code, company.quickbooks_last_invoice_imported_id))
        except UserError as ue:
            if call_from == 'cron':
                _logger.info('Exception : {}'.format(ue))
            else:
                raise ue
        except ValidationError as ve:
            if call_from == 'cron':
                _logger.info('Exception : {}'.format(ve))
            else:
                raise ve
        except Exception as e:
            if call_from == 'cron':
                _logger.info('Exception : {}'.format(e))
            else:
                raise ValidationError("Error during invoice import process: {}".format(str(e)))

    def import_credit_memo(self, company=None):
        try:
            if company.access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + company.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'

                if company.import_credit_memo_date:
                    if company.credit_memo_import_by == 'crt_dt':
                        query = f"select * from CreditMemo WHERE Metadata.CreateTime >= '{company.import_credit_memo_date}' order by Id MAXRESULTS {company.limit}"
                    elif company.credit_memo_import_by == 'other_dt':
                        query = f"select * from CreditMemo WHERE TxnDate >= '{company.import_credit_memo_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from CreditMemo WHERE Metadata.LastUpdatedTime >= '{company.import_credit_memo_date}' order by Id MAXRESULTS {company.limit}"
                else:
                    query = f"select * from CreditMemo order by Id STARTPOSITION {company.quickbooks_last_credit_note_imported_id} MAXRESULTS {company.limit}"

                data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                        headers=headers)
                if data.status_code == 200:
                    self.create_invoice(data, 'out_refund', company=company)
                else:
                    _logger.error('Connection Error...!')
        except Exception as e:
            raise ValidationError(e)

    def import_vendor_bill(self, call_from=None, company=None):
        try:
            _logger.info("inside vendor bill ********11********************")
            if not company:
                try:
                    company = self.env['res.users'].search(
                        [('id', '=', self._uid)]).company_id
                    if not company:
                        company = self.env.company
                except Exception as e:
                    raise ValidationError("Error fetching company information: {}".format(str(e)))

            if company.access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + company.access_token
                headers['accept'] = 'application/json'
                headers['Content-Type'] = 'text/plain'

                try:
                    if company.import_bills_by_date:
                        if company.vendor_bill_import_by == 'crt_dt':
                            query = f"select * from Bill WHERE Metadata.CreateTime >= '{company.import_bills_date}' order by Id MAXRESULTS {company.limit}"
                        elif company.vendor_bill_import_by == 'other_dt':
                            query = f"select * from Bill WHERE TxnDate >= '{company.import_bills_date}' order by Id MAXRESULTS {company.limit}"
                        else:
                            query = f"select * from Bill WHERE Metadata.LastUpdatedTime >= '{company.import_bills_date}' order by Id MAXRESULTS {company.limit}"
                    else:
                        query = f"select * from Bill order by Id STARTPOSITION {company.quickbooks_last_vendor_bill_imported_id} MAXRESULTS {company.limit}"
                except Exception as e:
                    raise ValidationError("Error while constructing QBO query for vendor bills: {}".format(str(e)))

                try:
                    data = requests.request('GET', company.url + str(company.realm_id) + "/query?query=" + query,
                                            headers=headers)
                    if data.status_code == 200:
                        try:
                            self.create_invoice(data, 'in_invoice', company=company)
                        except (UserError, ValidationError):
                            raise
                        except Exception as e:
                            raise ValidationError("Error while creating invoice(s) from vendor bill data. "
                                                  "Last known vendor bill QBO ID: {}. Error: {}".format(
                                company.quickbooks_last_vendor_bill_imported_id, str(e)))
                    else:
                        raise ValidationError("Failed to fetch vendor bills from QBO. "
                                              "Status Code: {} | Response: {} | QBO ID from: {}".format(
                            data.status_code, data.text, company.quickbooks_last_vendor_bill_imported_id))
                except (UserError, ValidationError):
                    raise
                except Exception as e:
                    raise ValidationError("Request to QuickBooks failed while importing vendor bills. "
                                          "QBO ID from: {} | Error: {}".format(
                        company.quickbooks_last_vendor_bill_imported_id, str(e)))
        except UserError as ue:
            if call_from == 'cron':
                _logger.error('Error while importing vendor bill: {}'.format(ue))
            else:
                raise ue
        except ValidationError as ve:
            if call_from == 'cron':
                _logger.error('Error while importing vendor bill: {}'.format(ve))
            else:
                raise ve
        except Exception as e:
            if call_from == 'cron':
                _logger.error('Error while importing vendor bill: {}'.format(e))
            else:
                raise ValidationError("Unhandled exception during vendor bill import: {}".format(e))

    def create_invoice(self, data, type='out_invoice', company=None):
        _logger.info("=============crate invoice===========")
        if not company:
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
        if not company:
            company = self.env.company
        if data:
            recs = []
            parsed_data = json.loads(str(data.text))
            count = 0
            if parsed_data:
                try:
                    if type == 'out_invoice':
                        get_data_for = 'Invoice'
                    elif type == 'out_refund':
                        get_data_for = 'CreditMemo'
                    if type == 'in_invoice':
                        get_data_for = 'Bill'
                    # if type == 'in_refund':
                    #     get_data_for = 'VendorCredit'

                    if 'QueryResponse' in parsed_data and parsed_data.get('QueryResponse') and parsed_data.get(
                            'QueryResponse').get(get_data_for):
                        for cust in parsed_data.get('QueryResponse').get(get_data_for):
                            try:
                                return_val = self.check_account_id(cust, company=company)
                                count = count + 1
                                invoice_field = 'qbo_credit_memo_id' if type == 'out_refund' else 'qbo_invoice_id'
                                account_invoice = self.env['account.move'].search(
                                    [(invoice_field, '=', cust.get('Id')), ('company_id', '=', company.id)])
                                _logger.info(
                                    "ACC invoice is -----> {}".format(account_invoice))
                                try:
                                    if not account_invoice:
                                        if type == 'out_invoice' and cust.get('TotalAmt') < 0:
                                            self.env['qbo.logger'].create({
                                                'odoo_name': 'Qbo Invoice Id : {}'.format(cust.get('DocNumber')),
                                                'odoo_object': 'Invoice',
                                                'activity': 'Import',
                                                'message': 'Cant Create order with negetive total',
                                                'created_date': datetime.now(),
                                            })
                                            continue

                                        currency = None
                                        if 'CurrencyRef' in cust and cust.get('CurrencyRef'):
                                            if cust.get('CurrencyRef').get('value'):
                                                curr = cust.get(
                                                    'CurrencyRef').get('value')
                                                currency = self.env['res.currency'].sudo().search(
                                                    [('active', 'in', [True, False]),
                                                     ('name', '=', curr)],
                                                    limit=1)

                                                if not currency:
                                                    raise ValidationError(
                                                        f"Currency {curr} not found for QBO ID: {cust.get('Id')}")

                                                if not currency.active:
                                                    currency.active = True
                                                if currency and cust.get('ExchangeRate'):
                                                    rate_id = []
                                                    for rate in currency.rate_ids:
                                                        rate_id.append(str(rate.name))
                                                    if cust.get('TxnDate') in rate_id:
                                                        for rate in currency.rate_ids:
                                                            if str(rate.name) == cust.get('TxnDate'):
                                                                if not rate.inverse_company_rate == cust.get(
                                                                        'ExchangeRate'):
                                                                    rate.inverse_company_rate = cust.get('ExchangeRate')
                                                    else:
                                                        self.env['res.currency.rate'].create({
                                                            'name': cust.get('TxnDate'),
                                                            'inverse_company_rate': cust.get('ExchangeRate'),
                                                            'currency_id': currency.id,
                                                            'company_id': company.id,
                                                        })
                                                    self._cr.commit()

                                        _logger.info("Attempting for Invoice Creation")
                                        _logger.info(
                                            "QBO obj is -----> {}".format(cust))
                                        dict_i = self.create_invoice_dict(cust, type, company=company)
                                        dict_i['invoice_line_ids'] = []
                                        partner_obj = self.env['res.partner'].search(
                                            [('id', '=', dict_i.get('partner_id')), ('company_id', '=', company.id)],
                                            limit=1)

                                        if not partner_obj:
                                            raise ValidationError(f"Partner not found for QBO ID: {cust.get('Id')}")

                                        invoice_line = self.odoo_create_invoice_line_dict(cust, partner_obj, type,
                                                                                          dict_i.get('qbo_invoice_id'),
                                                                                          company=company)
                                        _logger.info(
                                            "Invoice Lines are ---> {}".format(invoice_line))

                                        for k in invoice_line:
                                            if currency:
                                                k.update(
                                                    {'currency_id': int(currency.id) if currency else False})
                                            dict_i['invoice_line_ids'].append(
                                                (0, 0, k))
                                        # return True
                                        _logger.info(
                                            "Dictionary for f is ---> {}".format(dict_i))
                                        dict_i.update({'company_id': company.id})
                                        invoice_obj = self.env['account.move'].create(dict_i)
                                        if cust.get("LinkedTxn"):
                                            for rec in cust.get("LinkedTxn"):
                                                link_sale_obj = False
                                                child_tran_type = rec.get('TxnType')
                                                if rec.get('TxnType') == 'Estimate':
                                                    link_sale_obj = self.env['sale.order'].search(
                                                        [('quickbook_id', '=', rec.get("TxnId")),
                                                         ('company_id', '=', company.id)], limit=1)
                                                    prnt_tran_type = 'Invoice'
                                                    child_tran_type = 'Sale Order'
                                                elif rec.get('TxnType') == 'PurchaseOrder':
                                                    link_sale_obj = self.env['purchase.order'].search(
                                                        [('quickbook_id', '=', rec.get("TxnId")),
                                                         ('company_id', '=', company.id)], limit=1)
                                                    prnt_tran_type = 'Bill'
                                                    child_tran_type = 'Purchase Order'
                                                if link_sale_obj:
                                                    # Ensure invoice_obj is valid
                                                    if invoice_obj:
                                                        # Directly update the invoice_ids field in sale.order
                                                        link_sale_obj.write({'invoice_ids': [(4, invoice_obj.id)]})

                                                        # Update the invoice_lines field in sale.order.line
                                                        for line in link_sale_obj.order_line:
                                                            line.write({'invoice_lines': [(4, line_id) for line_id in
                                                                                          invoice_obj.invoice_line_ids.ids]})

                                                        # Log the linking for debugging purposes
                                                        _logger.info(
                                                            f"Linked {prnt_tran_type} {invoice_obj.id} to {child_tran_type} {link_sale_obj.id}")
                                                        # Commit the transaction
                                                    else:
                                                        _logger.error(f"{prnt_tran_type} object is not valid")
                                                        # raise ValidationError(f"{prnt_tran_type} object is not valid")
                                                else:
                                                    _logger.error(
                                                        f"No {child_tran_type} found with quickbook_id {rec.get('TxnId')}")
                                                    # raise ValidationError(
                                                    #     f"No {child_tran_type} found with quickbook_id {rec.get('TxnId')}")

                                        _logger.info(
                                            "Invoice obj is -----> {}".format(invoice_obj))

                                        if invoice_obj and invoice_line:

                                            invoice_obj.action_post()
                                            if cust.get('DepositToAccountRef'):
                                                accunt = self.env['account.account'].search(
                                                    [('qbo_id', '=', cust.get('DepositToAccountRef').get('value')),
                                                     ('company_ids', '=', company.id)], limit=1)
                                                if not accunt:
                                                    raise ValidationError(
                                                        f"Account Not Found[{cust.get('DepositToAccountRef').get('value')}]{cust.get('DepositToAccountRef').get('name')} for QBO ID: {cust.get('Id')}")
                                                else:
                                                    journal = self.env['account.journal'].search(
                                                        [('default_account_id', '=', accunt.id),
                                                         ('company_id', '=', company.id)],
                                                        limit=1)
                                                    if not journal:
                                                        raise ValidationError(
                                                            _(f"Configure Account QBO Name[ID] {accunt.name}[{cust.get('DepositToAccountRef').get('value')}] In Journal For Payment for QBO ID: {cust.get('Id')}"))
                                                    else:
                                                        journal_id = self.env['account.journal'].search(
                                                            [('type', '=', 'bank'),
                                                             ('company_id', '=', company.id)],
                                                            limit=1)
                                                        action_data = invoice_obj.action_register_payment()
                                                        amount = float(cust.get('TotalAmt')) - float(
                                                            cust.get('Balance'))
                                                        self.env['account.payment.register'] \
                                                            .with_context(active_model='account.move',
                                                                          active_ids=invoice_obj.id) \
                                                            .create({
                                                            'payment_date': cust.get('TxnDate'),
                                                            'currency_id': int(currency.id) if currency else False,
                                                            'amount': amount,
                                                            'journal_id': journal_id.id,

                                                        }) \
                                                            ._create_payments()
                                            _logger.info("Invoice Line Committed!!!")

                                            if type == 'out_invoice':
                                                self._cr.commit()
                                                if company.import_invoice_by_date:
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
                                                    company.import_invoice_date = date_object
                                            elif type == 'out_refund':
                                                pass
                                            #     company.quickbooks_last_credit_note_imported_id = cust.get(
                                            #         'Id')

                                            elif type == 'in_invoice':
                                                # company.quickbooks_last_vendor_bill_imported_id = cust.get(
                                                #     'Id')
                                                if company.import_credit_memo_by_date:
                                                    date_format = '%Y-%m-%d'
                                                    if company.credit_memo_import_by == 'crt_dt':
                                                        date_string = cust.get('MetaData').get(
                                                            'CreateTime')[:10]
                                                    elif company.credit_memo_import_by == 'updt_dt':
                                                        date_string = cust.get('MetaData').get(
                                                            'LastUpdatedTime')[:10]
                                                    else:
                                                        date_string = cust.get('TxnDate')

                                                    date_object = datetime.strptime(date_string,
                                                                                    date_format).date()
                                                    company.import_credit_memo_date = date_object
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
                                                _logger.error(
                                                    f"Invoice or invoice lines were not created properly for QBO ID: {cust.get('Id')}")
                                                raise ValidationError(
                                                    f"Invoice or invoice lines were not created properly for QBO ID: {cust.get('Id')}")
                                        else:
                                            _logger.error(
                                                "NO ACCOUNT ID WAS ATTACHED !")

                                    else:

                                        if type == 'out_invoice':
                                            self._cr.commit()
                                            if company.import_invoice_by_date:
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
                                                company.import_invoice_date = date_object
                                        # elif type == 'out_refund':
                                        #     company.quickbooks_last_credit_note_imported_id = cust.get(
                                        #         'Id')
                                        elif type == 'in_invoice':
                                            # company.quickbooks_last_vendor_bill_imported_id = cust.get(
                                            #     'Id')
                                            if company.import_credit_memo_by_date:
                                                date_format = '%Y-%m-%d'
                                                if company.credit_memo_import_by == 'crt_dt':
                                                    date_string = cust.get('MetaData').get(
                                                        'CreateTime')[:10]
                                                elif company.credit_memo_import_by == 'updt_dt':
                                                    date_string = cust.get('MetaData').get(
                                                        'LastUpdatedTime')[:10]
                                                else:
                                                    date_string = cust.get('TxnDate')

                                                date_object = datetime.strptime(date_string,
                                                                                date_format).date()
                                                company.import_credit_memo_date = date_object

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

                                        _logger.info(
                                            "All data seems to be imported successfully!")
                                except Exception as e:
                                    _logger.warning(_('Error for QBO Invoice ID : {}: {} '.format(
                                        cust.get('Id'), traceback.format_exc())))

                                    self.env['qbo.logger'].create({
                                        # 'odoo_name': 'Qbo Invoice Id : {}'.format(cust.get('CustomerRef').get('value')),
                                        'odoo_name': 'Qbo Invoice Id : {}'.format(cust.get('Id')),
                                        'odoo_object': get_data_for,
                                        'activity': 'Import',
                                        'message': e,
                                        'created_date': datetime.now(),
                                    })
                                    raise UserError(
                                        'Error for QBO Invoice ID : {}\n-{} '.format(cust.get('Id'), e))
                                    pass
                            except (UserError, ValidationError):
                                raise
                            except Exception as e:
                                _logger.warning(_('Error for QBO Invoice ID : {}: {} '.format(
                                    cust.get('Id'), traceback.format_exc())))
                                raise UserError('Error for QBO Invoice ID : {}\n-{} '.format(cust.get('Id'), e))
                        max_result = parsed_data.get('QueryResponse').get('maxResults')
                        if type == 'out_invoice':
                            company.quickbooks_last_invoice_imported_id = max_result + int(
                                company.quickbooks_last_invoice_imported_id)
                        elif type == 'in_invoice':
                            company.quickbooks_last_vendor_bill_imported_id = max_result + int(
                                company.quickbooks_last_vendor_bill_imported_id)
                        elif type == 'out_refund':
                            company.quickbooks_last_credit_note_imported_id = max_result + int(
                                company.quickbooks_last_credit_note_imported_id)
                    else:
                        raise UserError(
                            "It seems that all of the data is already imported!")
                except (UserError, ValidationError):
                    raise
                except Exception as main_exception:
                    _logger.exception("Main level exception: {}".format(main_exception))
                    raise UserError(f"Main error occurred during invoice import: {main_exception}")

    def odoo_create_invoice_line_dict(self, cust, partner_data_id, type, qbo_inv_id='', company=None):
        try:
            _logger.info("Attempting to create Invoice Line Dictionary")
            inv_line_data = []
            discount = 0
            invoice_lines = cust.get('Line')
            sub_total = 0
            if invoice_lines:
                for j in invoice_lines:
                    if j.get('DetailType') == 'SubTotalLineDetail':
                        sub_total = j.get('Amount')
                    if "DiscountLineDetail" in j:
                        try:
                            if j.get('DiscountLineDetail').get('PercentBased'):
                                if j.get("DiscountLineDetail").get('DiscountPercent'):
                                    res_account = self.env['account.account'].search(
                                        [('qbo_id', '=',
                                          j.get('DiscountLineDetail').get('DiscountAccountRef').get('value')),
                                         ('company_ids', '=', company.id)])
                                    discount = j.get('DiscountLineDetail').get(
                                        'DiscountPercent')
                            else:
                                if sub_total > 0:
                                    total_amount = (j.get('Amount') / sub_total) * 100
                                    discount = abs(total_amount)
                        except Exception as e:
                            raise ValidationError(
                                f"Error processing DiscountLineDetail for QBO Invoice ID {qbo_inv_id}: {str(e)}")

            for i in cust.get('Line'):
                try:
                    dict_ol = {}
                    dict_col = {}
                    dict_tol = {}
                    shipping_line = False
                    if type == 'out_invoice' or type == 'out_refund':
                        get_data_for = 'SalesItemLineDetail'
                    else:
                        get_data_for = 'ItemBasedExpenseLineDetail'

                    if type == 'out_invoice' or type == 'out_refund':
                        if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                'TxnTaxDetail').get('TxnTaxCodeRef'):
                            # if 'TxnTaxDetail' in cust and
                            # cust.get('TxnTaxDetail').get('TxnTaxCodeRef'):
                            if cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value'):
                                qb_tax_id = cust.get('TxnTaxDetail').get(
                                    'TxnTaxCodeRef').get('value')
                                record = self.env['account.tax']
                                tax = record.search(
                                    [('qbo_tax_id', '=', qb_tax_id), ('type_tax_use', '=', 'sale'),
                                     ('company_id', '=', company.id)])
                                if tax:
                                    custom_tax_id = [[6, False, [tax.id]]]
                                    _logger.info(
                                        _('\n\n\n custom_tax_idcustom_tax_idcustom_tax_idcustom_tax_idcustom_tax_id %s' % custom_tax_id))
                                    # [[6, False, [2]]]
                                    _logger.info("TAX ATTACHED {}".format(tax.id))
                                else:
                                    custom_tax_id = [[6, False, []]]
                        else:
                            custom_tax_id = [[6, False, []]]
                        tax_ids = []
                        if i.get('SalesItemLineDetail') and i.get('SalesItemLineDetail').get('TaxCodeRef') and i.get('SalesItemLineDetail').get('TaxCodeRef').get('value') == 'TAX':
                            if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TaxLine') and cust.get('TxnTaxDetail').get('TotalTax') > 0:
                                for tax_line in cust.get('TxnTaxDetail').get('TaxLine'):
                                    tax_detail = tax_line.get('TaxLineDetail', {})
                                    tax_rate_ref = tax_detail.get('TaxRateRef', {}).get('value')
                                    if tax_rate_ref:
                                        tax = self.env['account.tax'].search([
                                            ('qbo_tax_rate_id', '=', tax_rate_ref),
                                            ('type_tax_use', '=', 'sale'),
                                            ('company_id', '=', company.id)
                                        ], limit=1)
                                        if tax:
                                            tax_ids.append(tax.id)
                                            _logger.info(f"TAX ATTACHED from TaxLine: {tax.id}")

                        # Finally assign all
                        custom_tax_id = [[6, False, tax_ids]] if tax_ids else [[6, False, []]]
                        _logger.info(f"\nFinal custom_tax_id used ---> {custom_tax_id}")


                    else:
                        custom_tax_id = [[6, False, []]]

                    if 'SalesItemLineDetail' in i and i.get('SalesItemLineDetail'):
                        if i.get('SalesItemLineDetail').get('TaxCodeRef'):
                            if i.get('SalesItemLineDetail').get('TaxCodeRef').get(
                                    'value'):  # Not get TAX string so change
                                # if i.get('SalesItemLineDetail').get('TaxCodeRef').get('value') == "TAX":

                                qb_tax_id = i.get('SalesItemLineDetail').get(
                                    'TaxCodeRef').get('value')
                                record = self.env['account.tax']
                                tax = record.search(
                                    [('qbo_tax_id', '=', qb_tax_id), ('type_tax_use', '=', 'sale'),
                                     ('company_id', '=', company.id)])

                                if tax:
                                    custom_tax_id = [[6, False, [tax.id]]]
                                    _logger.info("TAX ATTACHED {}".format(tax.id))
                            else:
                                custom_tax_id = [[6, False, []]]
                        else:
                            custom_tax_id = [[6, False, []]]

                    else:
                        dict_ol['tax_ids'] = [[6, False, []]]
                    if i.get('Id') and not i.get(get_data_for) and not 'AccountBasedExpenseLineDetail' in i:
                        _logger.info(
                            '\n\n AccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetail\n')
                        dict_ol.clear()
                        dict_col.clear()
                        dict_tol.clear()

                        dict_ol['qb_id'] = int(i.get('Id'))

                        # ---------------------------TAX--------------------------------------
                        if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail'):

                            if 'TaxLine' in cust.get('TxnTaxDetail') and cust.get('TxnTaxDetail').get('TaxLine'):
                                if cust.get('TxnTaxDetail').get('TaxLine')[0].get('TaxLineDetail'):
                                    tax_val = cust.get('TxnTaxDetail').get('TaxLine')[0].get('TaxLineDetail').get(
                                        'TaxRateRef').get('value')

                                    if tax_val:
                                        record = self.env['account.tax']
                                        tax = record.search(
                                            [('qbo_tax_rate_id', '=', tax_val), ('company_id', '=', company.id)],
                                            limit=1)

                                        if tax:
                                            dict_ol['tax_ids'] = [[6, False, [tax.id]]]

                                    else:
                                        # dict_ol['invoice_line_tax_ids'] = None
                                        dict_ol['tax_ids'] = [[6, False, []]]

                                    if cust.get('TxnTaxDetail').get('TaxLine')[0].get('TaxLineDetail').get(
                                            'NetAmountTaxable'):
                                        dict_ol['price_unit'] = float(cust.get('TxnTaxDetail').get(
                                            'TaxLine')[0].get('TaxLineDetail').get('NetAmountTaxable'))
                                    else:
                                        dict_ol['price_unit'] = 0

                        dict_ol['quantity'] = 1.0

                        if 'Description' in i and i.get('Description'):
                            dict_ol['name'] = i.get('Description')
                            dict_ol['name'] = i.get('Description')
                        else:
                            dict_ol['name'] = 'NA'

                        if type == 'in_invoice':
                            if not company:
                                company = self.env['res.users'].search(
                                    [('id', '=', self._uid)]).company_id
                            if company:
                                if company.qb_expense_account:
                                    dict_ol[
                                        'account_id'] = company.qb_expense_account.id
                                else:
                                    raise UserError(
                                        f"Please set the Expense Account in QBO Configuration QBO Invoice ID {qbo_inv_id}")

                        if type == 'in_invoice':
                            if not company:
                                company = self.env['res.users'].search(
                                    [('id', '=', self._uid)]).company_id
                            if company:
                                if company.qb_expense_account:
                                    dict_ol[
                                        'account_id'] = company.qb_expense_account.id
                                else:
                                    raise UserError(
                                        f"Please set the Expense Account in QBO Configuration QBO Invoice ID {qbo_inv_id}")
                        if type == 'out_invoice' or type == 'out_refund':
                            if not company:
                                company = self.env['res.users'].search(
                                    [('id', '=', self._uid)]).company_id
                            if company:
                                if company.qb_income_account:
                                    dict_ol[
                                        'account_id'] = company.qb_income_account.id
                                else:
                                    raise UserError(
                                        f"Please set the Income Account in QBO Configuration QBO Invoice ID {qbo_inv_id}")

                        if 'account_id' in dict_ol:
                            _logger.info(
                                "\n\n Invoice Line is  ---> {}".format(dict_ol))
                            inv_line_data.append(dict_ol)
                    if 'AccountBasedExpenseLineDetail' in i and i.get('AccountBasedExpenseLineDetail'):
                        try:
                            res_account = self.env['account.account'].search(
                                [('qbo_id', '=', i.get('AccountBasedExpenseLineDetail').get('AccountRef').get('value')),
                                 ('company_ids', '=', company.id)])
                            _logger.info(
                                _('\n\n=============== AccountBasedExpenseLineDetailAccountBasedExpenseLineDetailAccountBasedExpenseLineDetail %s' % res_account))
                            if not res_account:
                                raise UserError(
                                    f"Account QBO ID {i.get('AccountBasedExpenseLineDetail').get('AccountRef').get('value')} does not exist in Odoo. QBO Invoice ID: {qbo_inv_id}")
                        except Exception as e:
                            raise ValidationError(
                                f"Failed to retrieve Account for QBO Invoice ID {qbo_inv_id}: {str(e)}")

                        if res_account:

                            dict_ol.clear()
                            dict_col.clear()
                            dict_tol.clear()

                            # Parent Id for Product Line & Customer Account Receivable
                            # Line
                            dict_ol['partner_id'] = partner_data_id.id
                            dict_col['partner_id'] = partner_data_id.id
                            dict_tol['partner_id'] = partner_data_id.id

                            # Quickbooks Id for Product Line & Customer Account
                            # Receivable Line
                            if i.get('Id'):
                                dict_ol['qb_id'] = int(i.get('Id'))
                                dict_col['qb_id'] = int(i.get('Id'))
                                dict_tol['qb_id'] = int(i.get('Id'))

                            # ---------------------------TAX--------------------------------------
                            if i.get('AccountBasedExpenseLineDetail').get('TaxCodeRef'):
                                tax_val = i.get('AccountBasedExpenseLineDetail').get(
                                    'TaxCodeRef').get('value')
                                tax = ''
                                if type == 'in_invoice':
                                    record = self.env['account.tax']
                                    tax = record.search(
                                        [('qbo_tax_id', '=', tax_val), ('type_tax_use', '=', 'purchase'),
                                         ('company_id', '=', company.id)],
                                        limit=1)
                                else:
                                    record = self.env['account.tax']
                                    tax = record.search([('qbo_tax_id', '=', tax_val), ('type_tax_use', '=', 'sale'),
                                                         ('company_id', '=', company.id)],
                                                        limit=1)

                                if tax:
                                    dict_ol['tax_ids'] = [[6, False, [tax.id]]]

                                else:
                                    dict_ol['tax_ids'] = [[6, False, []]]
                                    dict_col['tax_ids'] = [[6, False, []]]
                                    dict_tol['tax_ids'] = [[6, False, []]]

                            if i.get('AccountBasedExpenseLineDetail').get('Qty'):
                                dict_ol['quantity'] = i.get(
                                    'AccountBasedExpenseLineDetail').get('Qty')
                                dict_col['quantity'] = i.get(
                                    'AccountBasedExpenseLineDetail').get('Qty')
                                dict_tol['quantity'] = i.get(
                                    'AccountBasedExpenseLineDetail').get('Qty')

                            else:
                                dict_ol['quantity'] = 1.0
                                dict_col['quantity'] = 1.0
                                dict_tol['quantity'] = 1.0

                            if i.get('AccountBasedExpenseLineDetail').get('UnitPrice'):
                                dict_ol['price_unit'] = float(
                                    i.get('AccountBasedExpenseLineDetail').get('UnitPrice'))
                                dict_col[
                                    'price_unit'] = -(float(i.get('AccountBasedExpenseLineDetail').get('UnitPrice')))

                                dict_ol['credit'] = abs(
                                    dict_ol['quantity'] * float(
                                        i.get('AccountBasedExpenseLineDetail').get('UnitPrice')))
                                dict_ol['debit'] = 0

                                dict_col['credit'] = 0
                                dict_col['debit'] = abs(
                                    dict_col['quantity'] * float(
                                        i.get('AccountBasedExpenseLineDetail').get('UnitPrice')))

                            else:
                                if not i.get('AccountBasedExpenseLineDetail').get('Qty'):
                                    dict_ol['price_unit'] = float(i.get('Amount'))
                                    dict_col['price_unit'] = -(float(i.get('Amount')))

                                    dict_ol['credit'] = abs(
                                        dict_ol['quantity'] * float(i.get('Amount')))
                                    dict_ol['debit'] = 0

                                    dict_col['credit'] = 0
                                    dict_col['debit'] = abs(
                                        dict_col['quantity'] * float(i.get('Amount')))
                                else:
                                    dict_ol['price_unit'] = 0
                                    dict_col['price_unit'] = 0

                                    dict_ol['credit'] = 0
                                    dict_ol['debit'] = 0

                                    dict_col['credit'] = 0
                                    dict_col['debit'] = 0

                            company_id = company or self.env.user.company_id
                            import_category_detail = company_id.import_category_detail

                            if import_category_detail and i.get('Description'):
                                dict_ol['name'] = i.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get(
                                    'name', 'Category Expense')
                                dict_col['name'] = i.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get(
                                    'name', 'Category Expense')
                                dict_tol['name'] = i.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get(
                                    'name', 'Category Expense')

                            else:
                                dict_ol['name'] = 'NA'
                                dict_col['name'] = 'NA'
                                dict_tol['name'] = 'NA'

                            if type == 'out_invoice' or type == 'out_refund':
                                if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                        'TxnTaxDetail').get(
                                    'TxnTaxCodeRef'):
                                    if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get(
                                            'value'):
                                        tax_amount = cust.get('TxnTaxDetail').get('TaxLine')[0].get(
                                            'TaxLineDetail').get(
                                            'TaxPercent')
                                        dict_tol['price_unit'] = float(
                                            dict_ol['quantity'] * dict_ol['price_unit'] * float(tax_amount / 100))
                                        dict_tol['credit'] = abs(
                                            dict_tol['price_unit'])
                                        dict_tol['debit'] = 0

                                        dict_col['debit'] += abs(dict_tol['credit'])
                                    else:
                                        dict_tol['price_unit'] = 0
                                        dict_tol['credit'] = 0
                                        dict_tol['debit'] = 0

                                else:
                                    dict_tol['price_unit'] = 0
                                    dict_tol['credit'] = 0
                                    dict_tol['debit'] = 0
                            else:
                                dict_tol['price_unit'] = 0
                                dict_tol['credit'] = 0
                                dict_tol['debit'] = 0

                            if type == 'out_refund' or type == 'in_invoice':
                                dict_ol['credit'], dict_ol['debit'] = dict_ol[
                                    'debit'], dict_ol['credit']
                                dict_col['credit'], dict_col['debit'] = dict_col[
                                    'debit'], dict_col['credit']
                                dict_tol['credit'], dict_tol['debit'] = dict_tol[
                                    'debit'], dict_tol['credit']

                            if res_account:
                                dict_ol['account_id'] = res_account.id
                                _logger.info("PRODUCT has income account set")

                            else:
                                product_red = self.env['product.product']
                                dict_ol['account_id'] = res_account.id

                            if type == "in_invoice":
                                if partner_data_id.property_account_payable_id:
                                    dict_col[
                                        'account_id'] = partner_data_id.property_account_payable_id.id
                                    dict_tol[
                                        'account_id'] = dict_ol.get('account_id',
                                                                    False)  # partner_data_id.property_account_payable_id.id

                            if type == "out_invoice" or type == "out_refund":
                                if partner_data_id.property_account_receivable_id:
                                    dict_col[
                                        'account_id'] = partner_data_id.property_account_receivable_id.id
                                    dict_tol[
                                        'account_id'] = dict_ol.get('account_id',
                                                                    False)  # partner_data_id.property_account_receivable_id.id
                            if import_category_detail:
                                if 'account_id' in dict_ol and 'account_id' in dict_col:
                                    _logger.info(
                                        "\n\n Invoice Line is  ---> {}".format(dict_ol))
                                    inv_line_data.append(dict_ol)

                                # inv_line_data.append(dict_col)
                            if type == 'out_invoice' or type == 'out_refund':
                                if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                        'TxnTaxDetail').get(
                                    'TxnTaxCodeRef'):
                                    dict_ol['tax_repartition_line_id'] = False
                                    dict_col['tax_repartition_line_id'] = False
                                    #
                                    #                                 tax_repartition_line_id = self.env['account.tax.repartition.line'].search([('repartition_type', '=', 'tax')],limit=1)
                                    dict_tol['tax_repartition_line_id'] = False
                                    #                                 dict_tol['tax_repartition_line_id'] = tax_repartition_line_id.id

                                    dict_ol['tax_base_amount'] = 0
                                    dict_col['tax_base_amount'] = 0
                                    dict_tol['tax_base_amount'] = dict_ol[
                                                                      'quantity'] * dict_ol['price_unit']

                                    if cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value'):
                                        inv_line_data.append(dict_tol)

                    if i.get(get_data_for):
                        qbo_id = i.get(get_data_for).get('ItemRef').get('value') if i.get(get_data_for).get('ItemRef') else "No Product"

                        try:
                            if qbo_id != "No Product":
                                res_product = self.env['product.product'].search(
                                    [('qbo_product_id', '=', i.get(get_data_for).get('ItemRef').get('value')),
                                     ('company_id', '=', company.id)])
                            if not res_product and i.get(get_data_for).get('ItemRef').get(
                                    'value') == 'SHIPPING_ITEM_ID':
                                if not company:
                                    if not self.env.user.company_id.delivery_carrier_id:
                                        raise UserError(
                                            _(f'Please defined the Shipping Method in company! QBO Invoice ID: {qbo_inv_id}'))
                                    res_product = self.env.user.company_id.delivery_carrier_id.product_id
                                    shipping_line = True
                                else:
                                    if not company.delivery_carrier_id:
                                        raise UserError(
                                            _(f'Please defined the Shipping Method in company! QBO Invoice ID: {qbo_inv_id}'))
                                    res_product = company.delivery_carrier_id.product_id
                                    shipping_line = True

                            if not res_product:
                                if not isinstance(qbo_id, int):
                                    if cust.get('DocNumber'):
                                        raise UserError('Product ' + str(
                                            i.get(get_data_for).get('ItemRef').get(

                                                'name')) + ' is not defined in Odoo. Transaction ' + ' Name : ' + cust.get(
                                            'DocNumber'))
                                    else:
                                        raise UserError('Product ' + str(
                                            i.get(get_data_for).get('ItemRef').get(
                                                'name')) + ' is not defined in Odoo.')

                                    # res_product = self.env['product.product'].create(vals) #unreachable code

                            if res_product:

                                dict_ol.clear()
                                dict_col.clear()
                                dict_tol.clear()

                                # Product Id for Product Line & Customer Account Receivable
                                # Line
                                dict_ol['product_id'] = res_product.id
                                dict_col['product_id'] = False
                                dict_tol['product_id'] = False

                                # Parent Id for Product Line & Customer Account Receivable
                                # Line
                                dict_ol['partner_id'] = partner_data_id.id
                                dict_col['partner_id'] = partner_data_id.id
                                dict_tol['partner_id'] = partner_data_id.id

                                # Quickbooks Id for Product Line & Customer Account
                                # Receivable Line
                                if i.get('Id'):
                                    dict_ol['qb_id'] = int(i.get('Id'))
                                    dict_col['qb_id'] = int(i.get('Id'))
                                    dict_tol['qb_id'] = int(i.get('Id'))

                                # ---------------------------TAX--------------------------------------
                                if i.get(get_data_for).get('TaxCodeRef'):

                                    tax_val = i.get(get_data_for).get(
                                        'TaxCodeRef').get('value')
                                    if tax_val:
                                        dict_ol['tax_ids'] = custom_tax_id
                                        dict_col['tax_ids'] = custom_tax_id
                                        dict_tol['tax_ids'] = custom_tax_id
                                    else:
                                        dict_ol['tax_ids'] = [[6, False, []]]
                                        dict_col['tax_ids'] = [[6, False, []]]
                                        dict_tol['tax_ids'] = [[6, False, []]]

                                if i.get(get_data_for).get('Qty'):
                                    dict_ol['quantity'] = i.get(get_data_for).get('Qty')
                                    dict_col['quantity'] = i.get(get_data_for).get('Qty')
                                    dict_tol['quantity'] = i.get(get_data_for).get('Qty')
                                elif shipping_line:
                                    dict_ol['quantity'] = 1
                                    dict_col['quantity'] = 1
                                    dict_tol['quantity'] = 1
                                else:
                                    dict_ol['quantity'] = 0
                                    dict_col['quantity'] = 0
                                    dict_tol['quantity'] = 0

                                if i.get(get_data_for).get('UnitPrice'):
                                    dict_ol['price_unit'] = float(
                                        i.get(get_data_for).get('UnitPrice'))
                                    dict_col['price_unit'] = - \
                                        (float(i.get(get_data_for).get('UnitPrice')))

                                    dict_ol['credit'] = abs(
                                        dict_ol['quantity'] * float(i.get(get_data_for).get('UnitPrice')))
                                    dict_ol['debit'] = 0

                                    dict_col['credit'] = 0
                                    dict_col['debit'] = abs(
                                        dict_col['quantity'] * float(i.get(get_data_for).get('UnitPrice')))

                                else:
                                    if not i.get(get_data_for).get('Qty'):
                                        dict_ol['price_unit'] = float(i.get('Amount'))
                                        dict_col['price_unit'] = -(float(i.get('Amount')))

                                        dict_ol['credit'] = abs(
                                            dict_ol['quantity'] * float(i.get('Amount')))
                                        dict_ol['debit'] = 0

                                        dict_col['credit'] = 0
                                        dict_col['debit'] = abs(
                                            dict_col['quantity'] * float(i.get('Amount')))
                                    else:
                                        dict_ol['price_unit'] = 0
                                        dict_col['price_unit'] = 0

                                        dict_ol['credit'] = 0
                                        dict_ol['debit'] = 0

                                        dict_col['credit'] = 0
                                        dict_col['debit'] = 0

                                if i.get('Description'):
                                    dict_ol['name'] = i.get('Description')
                                    dict_col['name'] = i.get('Description')
                                    dict_tol['name'] = i.get('Description')
                                else:
                                    dict_ol['name'] = 'NA'
                                    dict_col['name'] = 'NA'
                                    dict_tol['name'] = 'NA'

                                if type == 'out_invoice' or type == 'out_refund':
                                    if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get(
                                            'TxnTaxDetail') and cust.get(
                                        'TxnTaxDetail').get(
                                        'TxnTaxCodeRef'):
                                        if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get(
                                                'value'):
                                            tax_amount = cust.get('TxnTaxDetail').get('TaxLine')[0].get(
                                                'TaxLineDetail').get(
                                                'TaxPercent')
                                            dict_tol['price_unit'] = float(
                                                dict_ol['quantity'] * dict_ol['price_unit'] * float(tax_amount / 100))
                                            dict_tol['credit'] = abs(
                                                dict_tol['price_unit'])
                                            dict_tol['debit'] = 0

                                            dict_col['debit'] += abs(dict_tol['credit'])
                                        else:
                                            dict_tol['price_unit'] = 0
                                            dict_tol['credit'] = 0
                                            dict_tol['debit'] = 0

                                    else:
                                        dict_tol['price_unit'] = 0
                                        dict_tol['credit'] = 0
                                        dict_tol['debit'] = 0
                                else:
                                    dict_tol['price_unit'] = 0
                                    dict_tol['credit'] = 0
                                    dict_tol['debit'] = 0

                                if type == 'out_refund' or type == 'in_invoice':
                                    dict_ol['credit'], dict_ol['debit'] = dict_ol[
                                        'debit'], dict_ol['credit']
                                    dict_col['credit'], dict_col['debit'] = dict_col[
                                        'debit'], dict_col['credit']
                                    dict_tol['credit'], dict_tol['debit'] = dict_tol[
                                        'debit'], dict_tol['credit']

                                if type == 'out_invoice' or type == "out_refund":
                                    if res_product.property_account_income_id:
                                        dict_ol[
                                            'account_id'] = res_product.property_account_income_id.id
                                        dict_col[
                                            'account_id'] = res_product.property_account_income_id.id
                                        dict_tol[
                                            'account_id'] = res_product.property_account_income_id.id
                                    elif res_product.categ_id.property_account_income_categ_id:
                                        dict_ol[
                                            'account_id'] = res_product.categ_id.property_account_income_categ_id.id
                                        dict_col[
                                            'account_id'] = res_product.categ_id.property_account_income_categ_id.id
                                        dict_tol[
                                            'account_id'] = res_product.categ_id.property_account_income_categ_id.id
                                    else:
                                        raise ValidationError(
                                            _(f"Can't Find Account for Product {res_product.name}"))

                                else:
                                    if res_product.property_account_expense_id:
                                        dict_ol[
                                            'account_id'] = res_product.property_account_expense_id.id
                                        dict_col[
                                            'account_id'] = res_product.property_account_expense_id.id
                                        dict_tol[
                                            'account_id'] = res_product.property_account_expense_id.id
                                    elif res_product.detailed_type == 'product' and res_product.categ_id.property_stock_account_input_categ_id:
                                        dict_ol[
                                            'account_id'] = res_product.categ_id.property_stock_account_input_categ_id.id
                                        dict_col[
                                            'account_id'] = res_product.categ_id.property_stock_account_input_categ_id.id
                                        dict_tol[
                                            'account_id'] = res_product.categ_id.property_stock_account_input_categ_id.id
                                    elif res_product.categ_id.property_account_expense_categ_id.id:
                                        dict_ol[
                                            'account_id'] = res_product.categ_id.property_account_expense_categ_id.id
                                        dict_col[
                                            'account_id'] = res_product.categ_id.property_account_expense_categ_id.id
                                        dict_tol[
                                            'account_id'] = res_product.categ_id.property_account_expense_categ_id.id
                                    else:
                                        raise ValidationError(
                                            _(f"Can't Find Account for Product {res_product.name}"))

                                if type == "in_invoice":
                                    if partner_data_id.property_account_payable_id:
                                        dict_col[
                                            'account_id'] = partner_data_id.property_account_payable_id.id  # find payble14
                                        dict_tol[
                                            'account_id'] = dict_ol.get('account_id',
                                                                        False)  # partner_data_id.property_account_payable_id.id

                                if type == "out_invoice" or type == "out_refund":
                                    if partner_data_id.property_account_receivable_id:
                                        dict_col[
                                            'account_id'] = partner_data_id.property_account_receivable_id.id
                                        dict_tol[
                                            'account_id'] = dict_ol.get('account_id',
                                                                        False)  # partner_data_id.property_account_receivable_id.id

                                _logger.info("DICT COL IS ---> {}".format(dict_col))
                                _logger.info("DICT OL IS ---> {}".format(dict_ol))
                                _logger.info("DICT TOL IS ---> {}".format(dict_tol))
                                if 'account_id' in dict_ol and 'account_id' in dict_col:
                                    _logger.info(
                                        "\n\n Invoice Line is  ---> {}".format(dict_ol))
                                    # dict_ol['discount'] = discount
                                    if not shipping_line:
                                        dict_ol['discount'] = discount
                                    inv_line_data.append(dict_ol)

                                    # dict_col['discount'] = discount
                                    if not shipping_line:
                                        dict_col['discount'] = discount
                                    inv_line_data.append(dict_col)
                                    _logger.info(
                                        "INVOICE LINE DATA FOR NOW IS ---> {}".format(inv_line_data))
                                    if type == 'out_invoice' or type == 'out_refund':
                                        _logger.info("Getting Additional Details!")
                                        if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get(
                                                'TxnTaxDetail') and cust.get(
                                            'TxnTaxDetail').get(
                                            'TxnTaxCodeRef'):
                                            _logger.info("Getting Transaction Details!")
                                            dict_ol['tax_repartition_line_id'] = False
                                            dict_col['tax_repartition_line_id'] = False

                                            #                                 tax_repartition_line_id = self.env['account.tax.repartition.line'].search([('repartition_type', '=', 'tax')],limit=1)
                                            # dict_tol['tax_repartition_line_id'] = tax_repartition_line_id.id
                                            dict_tol['tax_repartition_line_id'] = False
                                            dict_ol['tax_base_amount'] = 0
                                            dict_col['tax_base_amount'] = 0
                                            dict_tol['tax_base_amount'] = dict_ol[
                                                                              'quantity'] * dict_ol['price_unit']
                                            # dict_tol['discount'] = discount
                                            if not shipping_line:
                                                dict_tol['discount'] = discount
                                            if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get(
                                                    'TxnTaxCodeRef').get(
                                                'value'):
                                                pass
                                                # inv_line_data.append(dict_tol) NEED TO CHECK WITH HARESH
                                            else:
                                                _logger.info(
                                                    "TAX Code Reference Value Not Found!")
                                else:
                                    _logger.info("Account ID not found in the dictionary!")
                            else:
                                raise UserError('Product ' + str(
                                    i.get(get_data_for).get('ItemRef').get(
                                        'name')) + ' is not defined in Odoo. Invoice type ' + str(
                                    type) + ' Name :' + cust.get(
                                    'DocNumber'))
                        except Exception as e:
                            raise ValidationError(
                                f"Error retrieving product from QBO ID {qbo_id} in QBO Invoice ID {qbo_inv_id}: {str(e)}")
                except ValidationError as ve:
                    _logger.error(f"Validation error for QBO Invoice ID {qbo_inv_id}: {str(ve)}")
                    raise ve
                except Exception as e:
                    _logger.error(f"Unhandled error for QBO Invoice ID {qbo_inv_id}: {str(e)}")
                    raise ValidationError(
                        f"An unexpected error occurred while processing QBO Invoice ID {qbo_inv_id}: {str(e)}")
            _logger.info(
                "INVOICE LINE DATA SENDING FOR CREATION IS --BEFORE -> {}".format(inv_line_data))
            for j in inv_line_data:
                if j.get('credit') and j.get('debit'):
                    del j['credit']
                    del j['debit']
                if 'product_id' in j:
                    if j.get('quantity') == 0:
                        j['quantity'] = 1
                    if not j.get('product_id'):
                        inv_line_data.remove(j)
            _logger.info(
                "INVOICE LINE DATA SENDING FOR CREATION IS --LATER -> {}".format(inv_line_data))
            return inv_line_data
        except ValidationError as e:
            _logger.error(f"Validation error while processing QBO Invoice ID {qbo_inv_id}: {str(e)}")
            raise e
        except Exception as e:
            _logger.error(f"Unexpected error while processing QBO Invoice ID {qbo_inv_id}: {str(e)}")
            raise ValidationError(f"Unexpected error while processing QBO Invoice ID {qbo_inv_id}: {str(e)}")

    def create_invoice_line_dict(self, cust, invoice_obj, type):
        _logger.info("Attempting to create Invoice Line Dictionary")
        inv_line_data = []

        custom_tax_id = [[6, False, []]]  # Default empty

        if type in ['out_invoice', 'out_refund']:
            txn_tax_detail = cust.get('TxnTaxDetail', {})
            if txn_tax_detail and txn_tax_detail.get('TaxLine'):
                tax_ids = []
                for tax_line in txn_tax_detail['TaxLine']:
                    tax_detail = tax_line.get('TaxLineDetail', {})
                    tax_percent = tax_detail.get('TaxPercent')
                    if tax_percent is not None:
                        # Match Odoo tax based on percent (or qbo_tax_id if available)
                        tax_obj = self.env['account.tax'].search(
                            [('amount', '=', float(tax_percent))], limit=1)
                        if tax_obj:
                            tax_ids.append(tax_obj.id)
                            _logger.info(f"Found Odoo Tax: {tax_obj.name} ({tax_obj.id}) for {tax_percent}%")
                        else:
                            _logger.warning(f"No Odoo tax found for QBO tax percent {tax_percent}%")

                if tax_ids:
                    custom_tax_id = [[6, False, tax_ids]]
                    _logger.info(f"Mapped multiple taxes to custom_tax_id: {custom_tax_id}")
                else:
                    _logger.warning("No valid taxes found. Proceeding with empty tax_ids.")

        for i in cust.get('Line'):
            dict_ol = {}
            dict_col = {}
            dict_tol = {}

            if type == 'out_invoice' or type == 'out_refund':
                get_data_for = 'SalesItemLineDetail'
            else:
                get_data_for = 'ItemBasedExpenseLineDetail'

            if 'AccountBasedExpenseLineDetail' in i and i.get('AccountBasedExpenseLineDetail'):
                res_account = self.env['account.account'].search(
                    [('qbo_id', '=', i.get('AccountBasedExpenseLineDetail').get('AccountRef').get('value'))])
                if not res_account:
                    raise UserError('Account QBO ID ' + i.get('AccountBasedExpenseLineDetail').get('AccountRef').get(
                        'value') + ' doesnot exists in Odoo. ')
                if res_account:

                    dict_ol.clear()
                    dict_col.clear()
                    dict_tol.clear()

                    # Move Id for Product Line & Customer Account Receivable
                    # Line
                    dict_ol['move_id'] = invoice_obj.id
                    dict_col['move_id'] = invoice_obj.id
                    dict_tol['move_id'] = invoice_obj.id

                    # Parent Id for Product Line & Customer Account Receivable
                    # Line
                    dict_ol['partner_id'] = invoice_obj.partner_id.id
                    dict_col['partner_id'] = invoice_obj.partner_id.id
                    dict_tol['partner_id'] = invoice_obj.partner_id.id

                    # Quickbooks Id for Product Line & Customer Account
                    # Receivable Line
                    if i.get('Id'):
                        dict_ol['qb_id'] = int(i.get('Id'))
                        dict_col['qb_id'] = int(i.get('Id'))
                        dict_tol['qb_id'] = int(i.get('Id'))

                    # ---------------------------TAX--------------------------------------
                    if i.get(get_data_for) and i.get(get_data_for).get('TaxCodeRef'):
                        tax_val = i.get(get_data_for).get('TaxCodeRef').get('value')
                        if tax_val:
                            dict_ol['tax_ids'] = custom_tax_id
                            dict_col['tax_ids'] = custom_tax_id
                            dict_tol['tax_ids'] = custom_tax_id
                        else:
                            dict_ol['tax_ids'] = [[6, False, []]]
                            dict_col['tax_ids'] = [[6, False, []]]
                            dict_tol['tax_ids'] = [[6, False, []]]
                    else:
                        dict_ol['tax_ids'] = custom_tax_id
                        dict_col['tax_ids'] = custom_tax_id
                        dict_tol['tax_ids'] = custom_tax_id

                    if i.get('AccountBasedExpenseLineDetail').get('Qty'):
                        dict_ol['quantity'] = i.get(
                            'AccountBasedExpenseLineDetail').get('Qty')
                        dict_col['quantity'] = i.get(
                            'AccountBasedExpenseLineDetail').get('Qty')
                        dict_tol['quantity'] = i.get(
                            'AccountBasedExpenseLineDetail').get('Qty')

                    else:
                        dict_ol['quantity'] = 1.0
                        dict_col['quantity'] = 1.0
                        dict_tol['quantity'] = 1.0

                    if i.get('AccountBasedExpenseLineDetail').get('UnitPrice'):
                        dict_ol['price_unit'] = float(
                            i.get('AccountBasedExpenseLineDetail').get('UnitPrice'))
                        dict_col[
                            'price_unit'] = -(float(i.get('AccountBasedExpenseLineDetail').get('UnitPrice')))

                        dict_ol['credit'] = dict_ol['quantity'] * float(
                            i.get('AccountBasedExpenseLineDetail').get('UnitPrice'))
                        dict_ol['debit'] = 0

                        dict_col['credit'] = 0
                        dict_col['debit'] = dict_col['quantity'] * float(
                            i.get('AccountBasedExpenseLineDetail').get('UnitPrice'))

                    else:
                        if not i.get('AccountBasedExpenseLineDetail').get('Qty'):
                            dict_ol['price_unit'] = float(i.get('Amount'))
                            dict_col['price_unit'] = -(float(i.get('Amount')))

                            dict_ol['credit'] = dict_ol[
                                                    'quantity'] * float(i.get('Amount'))
                            dict_ol['debit'] = 0

                            dict_col['credit'] = 0
                            dict_col['debit'] = dict_col[
                                                    'quantity'] * float(i.get('Amount'))
                        else:
                            dict_ol['price_unit'] = 0
                            dict_col['price_unit'] = 0

                            dict_ol['credit'] = 0
                            dict_ol['debit'] = 0

                            dict_col['credit'] = 0
                            dict_col['debit'] = 0

                    if i.get('Description'):
                        dict_ol['name'] = i.get('Description')
                        dict_col['name'] = i.get('Description')
                        dict_tol['name'] = i.get('Description')
                    else:
                        dict_ol['name'] = 'NA'
                        dict_col['name'] = 'NA'
                        dict_tol['name'] = 'NA'

                    if type == 'out_invoice' or type == 'out_refund':
                        if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                'TxnTaxDetail').get(
                            'TxnTaxCodeRef'):
                            if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value'):
                                tax_amount = cust.get('TxnTaxDetail').get('TaxLine')[0].get('TaxLineDetail').get(
                                    'TaxPercent')
                                dict_tol['price_unit'] = float(
                                    dict_ol['quantity'] * dict_ol['price_unit'] * float(tax_amount / 100))
                                dict_tol['credit'] = dict_tol['price_unit']
                                dict_tol['debit'] = 0

                                dict_col['debit'] += dict_tol['credit']
                            else:
                                dict_tol['price_unit'] = 0
                                dict_tol['credit'] = 0
                                dict_tol['debit'] = 0

                        else:
                            dict_tol['price_unit'] = 0
                            dict_tol['credit'] = 0
                            dict_tol['debit'] = 0
                    else:
                        dict_tol['price_unit'] = 0
                        dict_tol['credit'] = 0
                        dict_tol['debit'] = 0

                    if type == 'out_refund' or type == 'in_invoice':
                        dict_ol['credit'], dict_ol['debit'] = dict_ol[
                            'debit'], dict_ol['credit']
                        dict_col['credit'], dict_col['debit'] = dict_col[
                            'debit'], dict_col['credit']
                        dict_tol['credit'], dict_tol['debit'] = dict_tol[
                            'debit'], dict_tol['credit']

                    if res_account:
                        dict_ol['account_id'] = res_account.id
                        _logger.info("PRODUCT has income account set")

                    if invoice_obj.partner_id.property_account_receivable_id:
                        dict_col[
                            'account_id'] = invoice_obj.partner_id.property_account_receivable_id.id
                        dict_tol[
                            'account_id'] = invoice_obj.partner_id.property_account_receivable_id.id

                    if 'account_id' in dict_ol and 'account_id' in dict_col:
                        _logger.info(
                            "\n\n Invoice Line is  ---> {}".format(dict_ol))
                        inv_line_data.append(dict_ol)
                        inv_line_data.append(dict_col)
                        if type == 'out_invoice' or type == 'out_refund':
                            if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                    'TxnTaxDetail').get(
                                'TxnTaxCodeRef'):
                                dict_ol['tax_repartition_line_id'] = False
                                dict_col['tax_repartition_line_id'] = False
                                #
                                #                                 tax_repartition_line_id = self.env['account.tax.repartition.line'].search([('repartition_type', '=', 'tax')],limit=1)
                                dict_tol['tax_repartition_line_id'] = False
                                #                                 dict_tol['tax_repartition_line_id'] = tax_repartition_line_id.id

                                dict_ol['tax_base_amount'] = 0
                                dict_col['tax_base_amount'] = 0
                                dict_tol['tax_base_amount'] = dict_ol[
                                                                  'quantity'] * dict_ol['price_unit']

                                if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get(
                                        'value'):
                                    inv_line_data.append(dict_tol)

            if i.get(get_data_for):
                res_product = self.env['product.product'].search(
                    [('qbo_product_id', '=', i.get(get_data_for).get('ItemRef').get('value'))])
                if res_product:

                    dict_ol.clear()
                    dict_col.clear()
                    dict_tol.clear()

                    # Move Id for Product Line & Customer Account Receivable
                    # Line
                    dict_ol['move_id'] = invoice_obj.id
                    dict_col['move_id'] = invoice_obj.id
                    dict_tol['move_id'] = invoice_obj.id

                    # Product Id for Product Line & Customer Account Receivable
                    # Line
                    dict_ol['product_id'] = res_product.id
                    dict_col['product_id'] = False
                    dict_tol['product_id'] = False

                    # Parent Id for Product Line & Customer Account Receivable
                    # Line
                    dict_ol['partner_id'] = invoice_obj.partner_id.id
                    dict_col['partner_id'] = invoice_obj.partner_id.id
                    dict_tol['partner_id'] = invoice_obj.partner_id.id

                    # Quickbooks Id for Product Line & Customer Account
                    # Receivable Line
                    if i.get('Id'):
                        dict_ol['qb_id'] = int(i.get('Id'))
                        dict_col['qb_id'] = int(i.get('Id'))
                        dict_tol['qb_id'] = int(i.get('Id'))

                    # ---------------------------TAX--------------------------------------
                    if i.get(get_data_for).get('TaxCodeRef'):
                        tax_val = i.get(get_data_for).get(
                            'TaxCodeRef').get('value')
                        if tax_val == 'TAX':
                            dict_ol['tax_ids'] = custom_tax_id
                            dict_col['tax_ids'] = [[6, False, []]]
                            dict_tol['tax_ids'] = [[6, False, []]]
                        else:
                            # dict_ol['invoice_line_tax_ids'] = None
                            dict_ol['tax_ids'] = [[6, False, []]]
                            dict_col['tax_ids'] = [[6, False, []]]
                            dict_tol['tax_ids'] = [[6, False, []]]

                    if i.get(get_data_for).get('Qty'):
                        dict_ol['quantity'] = i.get(get_data_for).get('Qty')
                        dict_col['quantity'] = i.get(get_data_for).get('Qty')
                        dict_tol['quantity'] = i.get(get_data_for).get('Qty')

                    else:
                        dict_ol['quantity'] = 0
                        dict_col['quantity'] = 0
                        dict_tol['quantity'] = 0

                    if i.get(get_data_for).get('UnitPrice'):
                        dict_ol['price_unit'] = float(
                            i.get(get_data_for).get('UnitPrice'))
                        dict_col['price_unit'] = - \
                            (float(i.get(get_data_for).get('UnitPrice')))

                        dict_ol['credit'] = dict_ol['quantity'] * \
                                            float(i.get(get_data_for).get('UnitPrice'))
                        dict_ol['debit'] = 0

                        dict_col['credit'] = 0
                        dict_col['debit'] = dict_col['quantity'] * \
                                            float(i.get(get_data_for).get('UnitPrice'))

                    else:
                        if not i.get(get_data_for).get('Qty'):
                            dict_ol['price_unit'] = float(i.get('Amount'))
                            dict_col['price_unit'] = -(float(i.get('Amount')))

                            dict_ol['credit'] = dict_ol[
                                                    'quantity'] * float(i.get('Amount'))
                            dict_ol['debit'] = 0

                            dict_col['credit'] = 0
                            dict_col['debit'] = dict_col[
                                                    'quantity'] * float(i.get('Amount'))
                        else:
                            dict_ol['price_unit'] = 0
                            dict_col['price_unit'] = 0

                            dict_ol['credit'] = 0
                            dict_ol['debit'] = 0

                            dict_col['credit'] = 0
                            dict_col['debit'] = 0

                    if i.get('Description'):
                        dict_ol['name'] = i.get('Description')
                        dict_col['name'] = i.get('Description')
                        dict_tol['name'] = i.get('Description')
                    else:
                        dict_ol['name'] = 'NA'
                        dict_col['name'] = 'NA'
                        dict_tol['name'] = 'NA'

                    if type == 'out_invoice' or type == 'out_refund':
                        if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                'TxnTaxDetail').get(
                            'TxnTaxCodeRef'):
                            if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get('value'):
                                tax_amount = cust.get('TxnTaxDetail').get('TaxLine')[0].get('TaxLineDetail').get(
                                    'TaxPercent')
                                dict_tol['price_unit'] = float(
                                    dict_ol['quantity'] * dict_ol['price_unit'] * float(tax_amount / 100))
                                dict_tol['credit'] = dict_tol['price_unit']
                                dict_tol['debit'] = 0

                                dict_col['debit'] += dict_tol['credit']
                            else:
                                dict_tol['price_unit'] = 0
                                dict_tol['credit'] = 0
                                dict_tol['debit'] = 0

                        else:
                            dict_tol['price_unit'] = 0
                            dict_tol['credit'] = 0
                            dict_tol['debit'] = 0
                    else:
                        dict_tol['price_unit'] = 0
                        dict_tol['credit'] = 0
                        dict_tol['debit'] = 0

                    if type == 'out_refund' or type == 'in_invoice':
                        dict_ol['credit'], dict_ol['debit'] = dict_ol[
                            'debit'], dict_ol['credit']
                        dict_col['credit'], dict_col['debit'] = dict_col[
                            'debit'], dict_col['credit']
                        dict_tol['credit'], dict_tol['debit'] = dict_tol[
                            'debit'], dict_tol['credit']

                    if res_product.property_account_income_id:
                        dict_ol[
                            'account_id'] = res_product.property_account_income_id.id
                        _logger.info("PRODUCT has income account set")
                    else:
                        dict_ol[
                            'account_id'] = res_product.categ_id.property_account_income_categ_id.id
                        _logger.info(
                            "No Income account was set, taking from product category..")

                    if invoice_obj.partner_id.property_account_receivable_id:
                        dict_col[
                            'account_id'] = invoice_obj.partner_id.property_account_receivable_id.id
                        dict_tol[
                            'account_id'] = invoice_obj.partner_id.property_account_receivable_id.id
                    else:
                        raise UserError(
                            "Account Receivable not set for Customer ---> {}".format(invoice_obj.partner_id.name))

                    _logger.info("DICT COL IS ---> {}".format(dict_col))
                    _logger.info("DICT OL IS ---> {}".format(dict_ol))
                    _logger.info("DICT TOL IS ---> {}".format(dict_tol))
                    if 'account_id' in dict_ol and 'account_id' in dict_col:
                        _logger.info(
                            "\n\n Invoice Line is  ---> {}".format(dict_ol))
                        inv_line_data.append(dict_ol)
                        inv_line_data.append(dict_col)
                        _logger.info(
                            "INVOICE LINE DATA FOR NOW IS ---> {}".format(inv_line_data))
                        if type == 'out_invoice' or type == 'out_refund':
                            _logger.info("Getting Additional Details!")
                            if 'TxnTaxDetail' in cust and 'TxnTaxCodeRef' in cust.get('TxnTaxDetail') and cust.get(
                                    'TxnTaxDetail').get(
                                'TxnTaxCodeRef'):
                                _logger.info("Getting Transaction Details!")
                                dict_ol['tax_repartition_line_id'] = False
                                dict_col['tax_repartition_line_id'] = False

                                #                                 tax_repartition_line_id = self.env['account.tax.repartition.line'].search([('repartition_type', '=', 'tax')],limit=1)
                                # dict_tol['tax_repartition_line_id'] = tax_repartition_line_id.id
                                dict_tol['tax_repartition_line_id'] = False
                                dict_ol['tax_base_amount'] = 0
                                dict_col['tax_base_amount'] = 0
                                dict_tol['tax_base_amount'] = dict_ol[
                                                                  'quantity'] * dict_ol['price_unit']

                                if 'TxnTaxDetail' in cust and cust.get('TxnTaxDetail').get('TxnTaxCodeRef').get(
                                        'value'):
                                    inv_line_data.append(dict_tol)
                                else:
                                    _logger.info(
                                        "TAX Code Reference Value Not Found!")
                    else:
                        _logger.info("Account ID not found in the dictionary!")
        _logger.info(
            "INVOICE LINE DATA SENDING FOR CREATION IS ---> {}".format(inv_line_data))
        return inv_line_data

    @api.model
    def _prepare_invoice_export_line_dict(self, line):
        #         line = self
        from_button = self._context.get('from_button', False)
        try:
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
            vals = {
                'Description': line.name,
                'Amount': line.price_subtotal,
            }
            # if self.partner_id.supplier_rank:
            #     if line.tax_ids:
            #         raise UserError("Taxable vendor bill cannot be exported.")

            unit_price = line.price_unit
            #  When discount is available in sale order
            if line.discount > 0:
                unit_price = line.price_unit - \
                             (line.price_unit * (line.discount / 100))
                # vals.update({'Amount': unit_price * line.product_uom_qty})
                vals.update({'Amount': unit_price * line.quantity})

            if line.tax_ids:
                # taxCodeRef = 'TAX'
                taxCodeRef = self.env['account.tax'].get_qbo_tax_code(line.tax_ids)
            else:
                taxCodeRef = 'NON'

            if self.partner_id.customer_rank:
                vals.update({
                    'DetailType': 'SalesItemLineDetail',
                    'SalesItemLineDetail': {
                        'ItemRef': {'value': self.env['product.template'].get_qbo_product_ref(line.product_id)},
                        'TaxCodeRef': {'value': taxCodeRef},
                        'UnitPrice': unit_price,  # line.price_unit
                        'Qty': line.quantity,
                    }
                })

            elif self.partner_id.supplier_rank:
                vals.update({
                    'DetailType': 'ItemBasedExpenseLineDetail',
                    'ItemBasedExpenseLineDetail': {
                        'ItemRef': {'value': self.env['product.template'].get_qbo_product_ref(line.product_id)},
                        'TaxCodeRef': {'value': taxCodeRef},
                        'UnitPrice': line.price_unit,
                        'Qty': line.quantity,
                        #                     'BillableStatus' : 'Billable',
                    }
                })

            return vals
        except Exception as e:
            _logger.exception("Failed to prepare invoice export line dictionary for line ID %s: %s", line.id, str(e))
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Unable to export',
                    'odoo_object': 'Sale Order',
                    'message': f"Unable to export invoice line {line.name}. Error: {str(e)}",
                    'activity': 'Exporting Invoice from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_("Unable to export invoice line '%s'. Error: %s") % (line.name, str(e)))

    @api.model
    def get_linked_sales_order_ref(self, quickbook_id, company=None):
        qbo_id = str(quickbook_id)
        if not company:
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
        url_str = company.get_import_query_url()
        url = url_str.get('url') + '/estimate/' + qbo_id + \
              '?minorversion=' + url_str.get('minorversion')
        result = requests.request('GET', url, headers=url_str.get('headers'))
        if result.status_code == 200:
            return True
        else:
            return False

    @api.model
    def _prepare_invoice_export_dict(self, company=None):
        from_button = self._context.get('from_button', False)
        invoice = self
        if invoice.move_type == 'in_refund':
            vals = {
                'TxnDate': str(invoice.invoice_date),
            }
        else:
            vals = {
                'TxnDate': str(invoice.invoice_date),
                'DueDate': str(invoice.invoice_date_due),
            }


        # Added code for linking of Sales Order to an invoice
        if invoice.invoice_origin:
            _logger.info(
                "INVOICE HAS A SALES ORDER ASSOCIATED WITH IT---> {}".format(invoice.invoice_origin))
            if not company:
                company = self.env.company
            if not company.separate_invoice_export:
                # Search for the related sales order
                linked_sales_order = self.env['sale.order'].search(
                    [('name', '=', invoice.invoice_origin)], limit=1)
                _logger.info(
                    "LINKED SALES ORDER IS ---> {}".format(linked_sales_order))
                if linked_sales_order:
                    # CHECK IF ALL THE CRITERIAS ARE MATCHED IN ORDER TO BE LINKED TO QBO
                    # 1 TO CHECK IF QBO ID IS ATTACHED TO SO
                    if linked_sales_order.quickbook_id:
                        _logger.info("QBO ID IS PRESENT TO SO")
                        # 2.TO CHECK IF SO IS PRESENT IN QBO
                        linked_so = self.get_linked_sales_order_ref(
                            linked_sales_order.quickbook_id, company)
                        if linked_so:
                            _logger.info("SALES ORDER IS PRESENT IN QBO")
                            # UPDATE LINKED TRANSACTION DETAILS
                            vals.update({
                                "LinkedTxn": [{
                                    "TxnId": linked_sales_order.quickbook_id,
                                    "TxnType": "Estimate"
                                }
                                ]})
                        else:
                            _logger.info("SALES ORDER NOT PRESENT IN QBO")
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': invoice.invoice_origin,
                                    'odoo_object': 'Sale Order',
                                    'message': "Sales Order : %s  is not present in  Quickbooks." % (
                                        invoice.invoice_origin),
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    _("Sales Order : %s  is not present in  Quickbooks." % (invoice.invoice_origin)))
                    else:
                        _logger.info(
                            "Linked Sales Order is not exported to Quickbooks")
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': invoice.invoice_origin,
                                'odoo_object': 'Sale Order',
                                'message': "Sales Order : %s linked to this Invoice is not exported to Quickbooks.Please export Sales Order first to link the invoice into Quickbooks " % (
                                    invoice.invoice_origin),
                                'activity': 'Exporting Invoice from Odoo',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise ValidationError(
                                _("Sales Order : %s linked to this Invoice is not exported to Quickbooks.Please export Sales Order first to link the invoice into Quickbooks " % (
                                    invoice.invoice_origin)))

        if invoice.partner_id.customer_rank:
            vals.update({'DocNumber': invoice.name,
                         'CustomerRef': {'value': self.env['res.partner'].get_qbo_partner_ref(invoice.partner_id)}})
        elif invoice.partner_id.supplier_rank:
            #             if invoice.invoice_sequence_number_next_prefix and invoice.invoice_sequence_number_next :
            #                 _logger.info("VENDOR BILL NUMBER IS ---> {} {}".format(invoice.invoice_sequence_number_next_prefix,invoice.invoice_sequence_number_next))
            #                 vendor_bill_ref_num = "{}{}".format(invoice.invoice_sequence_number_next_prefix,invoice.invoice_sequence_number_next)
            #                 vals.update({'DocNumber' : vendor_bill_ref_num})
            vals.update({'DocNumber': invoice.name,
                         'VendorRef': {'value': self.env['res.partner'].get_qbo_partner_ref(invoice.partner_id)}})

        arr = []
        tax_id = 0
        lst_line = []
        for line in invoice.invoice_line_ids:
            line_vals = self._prepare_invoice_export_line_dict(line)
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

        # if tax_id:
            # Set Tax type Like Inclusive or Exclusive or Out of scope Tax
        if invoice.tax_state:
            if invoice.tax_state == 'exclusive':
                vals.update({"GlobalTaxCalculation": "TaxExcluded"})
            elif invoice.tax_state == 'inclusive':
                vals.update({"GlobalTaxCalculation": "TaxInclusive"})
            elif invoice.tax_state == 'notapplicable':
                vals.update({"GlobalTaxCalculation": "NotApplicable"})

        vals.update({'Line': lst_line})

        if tax_id:
            j = 0
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
                    # if arr[j] == arr[j + 1]:
                    #     j = j + 1
                    #
                    #     tax_added = self.env['account.tax'].search(
                    #         [('id', '=', tax_id)])
                    #
                    #     vals.update({"TxnTaxDetail": {
                    #         "TxnTaxCodeRef": {
                    #             "value": tax_added.qbo_tax_id
                    #         }}})
                    # else:
                    #     if from_button:
                    #         self.env['qbo.logger'].sudo().create({
                    #             'odoo_name': f'{self.name}',
                    #             'odoo_object': 'Sale Order',
                    #             'message': "You need to add same tax for the required orderlines.",
                    #             'activity': 'Export Invoice from odoo',
                    #             'created_date': fields.Datetime.now(),
                    #         })
                    #     else:
                    #         raise UserError(
                    #             "You need to add same tax for the required orderlines.")

        if invoice.partner_shipping_id and invoice.move_type == 'out_invoice':
            input_string = f"{invoice.partner_shipping_id.contact_address if invoice.partner_shipping_id.contact_address else False}"
            if input_string:
                result_string = re.sub('\n+', '\n', input_string)
            else:
                result_string = False

            vals.update({"ShipAddr": {
                "Line1": f"{invoice.partner_shipping_id.name if invoice.partner_shipping_id.name else ''}" + '\n' + result_string,
            }})
        if invoice.partner_id.contact_address and invoice.move_type == 'out_invoice':
            input_string = f"{invoice.partner_id.contact_address if invoice.partner_id.contact_address else False}"
            if input_string:
                result_string = re.sub('\n+', '\n', input_string)
            else:
                result_string = False
            vals.update({"BillAddr": {
                "Line1": f"{invoice.partner_id.name if invoice.partner_id.name else ''}" + '\n' + result_string,
            }})
        if invoice.invoice_payment_term_id:
            if not invoice.invoice_payment_term_id.x_quickbooks_id:
                if from_button:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': f'{invoice.invoice_payment_term_id.name}',
                        'odoo_object': 'account.move',
                        'message': f'Payment Term[{invoice.invoice_payment_term_id.name}] Not map with quickbook',
                        'activity': 'Export Invoice from odoo',
                        'created_date': fields.Datetime.now(),
                    })
                else:
                    raise ValidationError(
                        _(f'Payment Term[{invoice.invoice_payment_term_id.name}] Not map with quickbook'))
            vals.update({"SalesTermRef": {
                "value": invoice.invoice_payment_term_id.x_quickbooks_id,
            }})
        if self.amount_tax and vals.get("TxnTaxDetail"):
            vals.get("TxnTaxDetail").update({"TotalTax": self.amount_tax})
        return vals

    @api.model
    def export_to_qbo(self, cron=None, company=None):
        """export account invoice to QBO"""
        if len(self) > 1:
            self._context.update({'from_button': True})
        from_button = self._context.get('from_button', False)
        if not company:
            quickbook_config = self.company_id
        else:
            quickbook_config = company
        if not quickbook_config:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'account.move',
                    'message': f'"Set Company for Invoice {self.name}"',
                    'activity': 'Exporting Invoice from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_(f"Set Company for Invoice {self.name}"))

        access_token = None
        realmId = None
        if quickbook_config.access_token:
            access_token = quickbook_config.access_token
        if quickbook_config.realm_id:
            realmId = quickbook_config.realm_id

        # Fetch the selected invoices (could be multiple)
        if self._context.get('active_ids'):
            invoices = self.browse(self._context.get('active_ids'))
        else:
            invoices = self

        failed_invoices = []  # To track failed invoices for reporting later

        for invoice in invoices:
            try:
                if invoice.move_type == 'entry':  # Journal Entry
                    if quickbook_config.export_pos_payment and quickbook_config.export_pos_journal:
                        invoice.export_journal_entry_as_payment(quickbook_config)
                    else:
                        invoice.export_journal_entry()

                if invoice.move_type in ['out_refund', 'in_refund'] and invoice.state == 'posted':
                    vals = invoice._prepare_invoice_export_dict(company=quickbook_config)

                    parsed_dict = json.dumps(vals)
                    if access_token:
                        headers = {'Authorization': 'Bearer ' + str(access_token), 'Content-Type': 'application/json'}
                        if invoice.move_type == 'out_refund':
                            result = requests.request('POST', quickbook_config.url + str(realmId) + "/creditmemo",
                                                      headers=headers, data=parsed_dict)
                        elif invoice.move_type == 'in_refund':
                            result = requests.request('POST', quickbook_config.url + str(realmId) + "/vendorcredit",
                                                      headers=headers, data=parsed_dict)

                        if result.status_code == 200:
                            response = quickbook_config.convert_xmltodict(result.text)
                            cm_or_vc = 'CreditMemo' if invoice.move_type == 'out_refund' else 'VendorCredit'
                            if response.get('IntuitResponse').get(cm_or_vc) and cm_or_vc == 'CreditMemo':
                                invoice.qbo_credit_memo_id = response.get('IntuitResponse').get('CreditMemo').get('Id')
                                invoice.qbo_invoice_name = response.get('IntuitResponse').get('CreditMemo').get(
                                    'DocNumber')
                                self._cr.commit()
                                _logger.info(f"{invoice.name} exported successfully to QBO")
                            elif response.get('IntuitResponse').get(cm_or_vc) and cm_or_vc == 'VendorCredit':
                                invoice.qbo_vendor_credit_id = response.get('IntuitResponse').get('VendorCredit').get('Id')
                                invoice.qbo_invoice_name = response.get('IntuitResponse').get('VendorCredit').get(
                                    'DocNumber')
                                self._cr.commit()
                                _logger.info(f"{invoice.name} exported successfully to QBO")
                            else:
                                failed_invoices.append(invoice)
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': invoice.name,
                                        'odoo_object': 'account.move',
                                        'message': f"Failed to export {invoice.name} to QBO. Response was: {result.text}",
                                        'activity': 'Exporting Invoice from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise ValidationError(
                                        _(f"Failed to export {invoice.name} to QBO. Response was: {result.text}"))
                        else:
                            failed_invoices.append(invoice)
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': invoice.name,
                                    'odoo_object': 'account.move',
                                    'message': f"Failed to export {invoice.name} to QBO. Error: {result.status_code} {result.reason}",
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    _(f"Failed to export {invoice.name} to QBO. Error: {result.status_code} {result.reason}"))

                    # if from_button:
                    #     self.env['qbo.logger'].sudo().create({
                    #         'odoo_name': 'Error',
                    #         'odoo_object': 'account.move',
                    #         'message': "Export function for Credit notes/Refunds and Payments are not available",
                    #         'activity': 'Exporting Invoice from Odoo',
                    #         'created_date': fields.Datetime.now(),
                    #     })
                    # else:
                    #     raise ValidationError(
                    #         _("Export function for Credit notes/Refunds and Payments are not available"))
                if invoice.move_type in ['out_invoice', 'in_invoice']:
                    if invoice.qbo_invoice_id and quickbook_config.update_tax_invoice_export:
                        if invoice.state == 'posted':
                            vals = invoice._prepare_invoice_export_dict(company=quickbook_config)
                            # Handle cases where there are no item references (for bills without products)
                            if invoice.partner_id.supplier_rank and quickbook_config.export_bill_without_product:
                                for line in vals.get('Line', []):
                                    item_detail = line.get('ItemBasedExpenseLineDetail', {})
                                    item_ref = item_detail.get('ItemRef', {})
                                    if item_ref.get('value') is None:
                                        item_ref['value'] = quickbook_config.product_id.qbo_product_id
                            headers = {
                                "Authorization": f"Bearer {access_token}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"
                            }
                            if invoice.move_type == 'out_invoice':
                                query = f"SELECT * FROM Invoice WHERE Id = '{invoice.qbo_invoice_id}'"
                            elif invoice.move_type == 'in_invoice':
                                query = f"SELECT * FROM Bill WHERE Id = '{invoice.qbo_invoice_id}'"

                            response = requests.get(
                                f"{quickbook_config.url}{quickbook_config.realm_id}/query?query={query}",
                                headers=headers
                            )

                            if response.status_code == 200:
                                try:
                                    invoice_data = response.json()

                                    data_1 = invoice_data.get("QueryResponse", {}).get("Invoice", [{}])[0]

                                    sync_token = data_1.get("SyncToken", "1")  # Default to "1" if missing
                                    vals.update({"SyncToken": sync_token, "Id": invoice.qbo_invoice_id})

                                except json.JSONDecodeError:
                                    _logger.info("Error: Failed to parse JSON response.")
                            else:
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': response.status_code,
                                        'odoo_object': 'account.move',
                                        'message': f"HTTP Error {response.status_code}: {response.text}",
                                        'activity': 'Exporting Invoice from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise ValidationError(_(f"HTTP Error {response.status_code}: {response.text}"))

                            parsed_dict = json.dumps(vals)
                            _logger.info(f'Export Dict for Invoice/BILL: \n{parsed_dict}')
                            # Send request to QuickBooks
                            if access_token:
                                headers = {'Authorization': 'Bearer ' + str(access_token),
                                           'Content-Type': 'application/json'}
                                if invoice.partner_id.customer_rank:
                                    result = requests.request('POST', quickbook_config.url + str(realmId) + "/invoice",
                                                              headers=headers, data=parsed_dict)
                                elif invoice.partner_id.supplier_rank:
                                    result = requests.request('POST', quickbook_config.url + str(realmId) + "/bill",
                                                              headers=headers, data=parsed_dict)

                                # Check response status
                                if result.status_code == 200:
                                    response = quickbook_config.convert_xmltodict(result.text)
                                    invoice_or_bill = 'Invoice' if invoice.partner_id.customer_rank else 'Bill'
                                    if response.get('IntuitResponse').get(invoice_or_bill):
                                        invoice.qbo_invoice_id = response.get('IntuitResponse').get(
                                            invoice_or_bill).get(
                                            'Id')
                                        invoice.qbo_invoice_name = response.get('IntuitResponse').get(
                                            invoice_or_bill).get(
                                            'DocNumber')
                                        self._cr.commit()
                                        _logger.info(f"{invoice.name} exported successfully to QBO")
                                    else:
                                        failed_invoices.append(invoice)
                                        if from_button:
                                            self.env['qbo.logger'].sudo().create({
                                                'odoo_name': invoice.name,
                                                'odoo_object': 'account.move',
                                                'message': f"Failed to export {invoice.name} to QBO. Response was: {result.text}",
                                                'activity': 'Exporting Invoice from Odoo',
                                                'created_date': fields.Datetime.now(),
                                            })
                                        else:
                                            raise ValidationError(
                                                _(f"Failed to export {invoice.name} to QBO. Response was: {result.text}"))
                                else:
                                    failed_invoices.append(invoice)
                                    if from_button:
                                        self.env['qbo.logger'].sudo().create({
                                            'odoo_name': invoice.name,
                                            'odoo_object': 'account.move',
                                            'message': f"Failed to export {invoice.name} to QBO. Error: {result.status_code} {result.reason}",
                                            'activity': 'Exporting Invoice from Odoo',
                                            'created_date': fields.Datetime.now(),
                                        })
                                    else:
                                        raise ValidationError(
                                            _(f"Failed to export {invoice.name} to QBO. Error: {result.status_code} {result.reason}"))
                            else:
                                failed_invoices.append(invoice)
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': invoice.name,
                                        'odoo_object': 'account.move',
                                        'message': f"Missing access token for export of {invoice.name}",
                                        'activity': 'Exporting Invoice from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise ValidationError(_(f"Missing access token for export of {invoice.name}"))

                    # Check if invoice has already been exported
                    if invoice.qbo_invoice_id:
                        if invoice.partner_id.customer_rank:
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': invoice.name,
                                    'odoo_object': 'account.move',
                                    'message': f"Invoice {invoice.name} is already exported to QBO",
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(_(f"Invoice {invoice.name} is already exported to QBO"))
                        elif invoice.partner_id.supplier_rank:
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': invoice.name,
                                    'odoo_object': 'account.move',
                                    'message': f"Vendor Bill {invoice.name} is already exported to QBO",
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(_(f"Vendor Bill {invoice.name} is already exported to QBO"))
                        continue  # Skip if already exported

                    # If the invoice is posted, proceed with export
                    if invoice.state == 'posted':
                        vals = invoice._prepare_invoice_export_dict(company=quickbook_config)

                        # Handle cases where there are no item references (for bills without products)
                        if invoice.partner_id.supplier_rank and quickbook_config.export_bill_without_product:
                            for line in vals.get('Line', []):
                                item_detail = line.get('ItemBasedExpenseLineDetail', {})
                                item_ref = item_detail.get('ItemRef', {})
                                if item_ref.get('value') is None:
                                    item_ref['value'] = quickbook_config.product_id.qbo_product_id

                        parsed_dict = json.dumps(vals)
                        _logger.info(f'Export Dict for Invoice/BILL: \n{parsed_dict}')

                        # Send request to QuickBooks
                        if access_token:
                            headers = {'Authorization': 'Bearer ' + str(access_token),
                                       'Content-Type': 'application/json',
                                       'accept':'application/json'}
                            if invoice.partner_id.customer_rank:
                                result = requests.request('POST', quickbook_config.url + str(realmId) + "/invoice",
                                                          headers=headers, data=parsed_dict)
                            elif invoice.partner_id.supplier_rank:
                                result = requests.request('POST', quickbook_config.url + str(realmId) + "/bill",
                                                          headers=headers, data=parsed_dict)
                            # Check response status
                            if result.status_code == 200:
                                response = result.json()
                                # response = quickbook_config.convert_xmltodict(result.text)
                                invoice_or_bill = 'Invoice' if invoice.partner_id.customer_rank else 'Bill'
                                if response.get(invoice_or_bill):
                                    invoice.qbo_invoice_id = response.get(invoice_or_bill).get(
                                        'Id')
                                    invoice.qbo_invoice_name = response.get(invoice_or_bill).get(
                                        'DocNumber')
                                    self._cr.commit()
                                    _logger.info(f"{invoice.name} exported successfully to QBO")
                                else:
                                    failed_invoices.append(invoice)
                                    if from_button:
                                        self.env['qbo.logger'].sudo().create({
                                            'odoo_name': invoice.name,
                                            'odoo_object': 'account.move',
                                            'message': f"Failed to export {invoice.name} to QBO. Response was: {result.text}",
                                            'activity': 'Exporting Invoice from Odoo',
                                            'created_date': fields.Datetime.now(),
                                        })
                                    else:
                                        raise ValidationError(
                                            _(f"Failed to export {invoice.name} to QBO. Response was: {result.text}"))
                            else:
                                failed_invoices.append(invoice)
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': invoice.name,
                                        'odoo_object': 'account.move',
                                        'message': f"Failed to export {invoice.name} to QBO. Error: {result.status_code} {result.reason} {result.text}",
                                        'activity': 'Exporting Invoice from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise ValidationError(
                                        _(f"Failed to export {invoice.name} to QBO. Error: {result.status_code} {result.reason}"))
                        else:
                            failed_invoices.append(invoice)
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': invoice.name,
                                    'odoo_object': 'account.move',
                                    'message': f"Missing access token for export of {invoice.name}",
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(_(f"Missing access token for export of {invoice.name}"))
            except Exception as e:
                failed_invoices.append(invoice)
                if from_button:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': invoice.name,
                        'odoo_object': 'account.move',
                        'message': f"Exception while exporting invoice {invoice.name}: {str(e)}",
                        'activity': 'Exporting Invoice from Odoo',
                        'created_date': fields.Datetime.now(),
                    })
                else:
                    raise ValidationError(_(f"Exception while exporting invoice {invoice.name}: {str(e)}"))
                # _logger.error(f"Exception while exporting invoice {invoice.name}: {str(e)}")

        # After processing all invoices, check if there were any failed exports
        # if failed_invoices:
        #     failed_sales_msg = "\n".join([f"Invoice {fs.name} failed to export" for fs in failed_invoices])
        #     if from_button:
        #         self.env['qbo.logger'].sudo().create({
        #             'odoo_name': 'Invoices Failed to Export',
        #             'odoo_object': 'account.move',
        #             'message': f"The following invoices failed to export to QBO:\n{failed_sales_msg}",
        #             'activity': 'Exporting Invoice from Odoo',
        #             'created_date': fields.Datetime.now(),
        #         })
        #     else:
        #         raise UserError(f"The following invoices failed to export to QBO:\n{failed_sales_msg}")

        # Show a success notification for all invoices if no errors occurred
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
    
    def export_journal_entry_as_payment(self, quickbook_config):
        """
        Export POS Journal Entry (account.move) as Customer Payment to QuickBooks
        """

        access_token = quickbook_config.access_token
        realm_id = quickbook_config.realm_id
        company = self.env.company
        from_button = len(self) > 1

        if not access_token or not realm_id:
            raise ValidationError("QuickBooks is not connected properly.")

        failed_moves = []

        for payment in self:
            try:
                # ------------------------------------------------------------
                # 1️⃣ Basic Validations
                # ------------------------------------------------------------
                if payment.qbo_payment_id:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': payment.name,
                            'odoo_object': 'account.move',
                            'message': f"POS Payment {payment.name} is already exported to QBO.",
                            'activity': 'Exporting POS Payment',
                            'created_date': fields.Datetime.now(),
                        })
                        continue
                    else:
                        raise ValidationError(
                            f"POS Payment {payment.name} is already exported to QBO."
                        )

                if payment.state != 'posted':
                    raise ValidationError(
                        f"POS Payment {payment.name} must be posted before export."
                    )

                # ------------------------------------------------------------
                # 2️⃣ Validate POS Payment Account (Deposit Account)
                # ------------------------------------------------------------
                deposit_account = quickbook_config.export_pos_payment_account

                if not deposit_account:
                    raise ValidationError(
                        "POS Payment Account is not configured. "
                        "Please configure a Clearing / Bank (Asset) account."
                    )

                if deposit_account.account_type == 'receivable':
                    raise ValidationError(
                        "POS Payment Account cannot be a Receivable account. "
                        "Please use a Clearing / Bank (Asset) account."
                    )

                if not deposit_account.qbo_id:
                    raise ValidationError(
                        f"POS Payment Account '{deposit_account.name}' "
                        f"is not exported to QuickBooks."
                    )

                # ------------------------------------------------------------
                # 3️⃣ Find Linked Customer Invoice via Reconciliation
                # ------------------------------------------------------------
                receivable_lines = payment.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable'
                )

                invoices = (
                        receivable_lines.matched_debit_ids.debit_move_id.move_id |
                        receivable_lines.matched_credit_ids.credit_move_id.move_id
                ).filtered(lambda m: m.move_type == 'out_invoice')

                if not invoices:
                    raise ValidationError(
                        f"No reconciled customer invoice found for POS payment {payment.name}."
                    )

                # ------------------------------------------------------------
                # 4️⃣ Prepare QBO Payment Lines
                # ------------------------------------------------------------
                line_vals = []
                total_amount = 0.0

                for invoice in invoices:
                    partner = self.env['res.partner'].get_qbo_partner_ref(invoice.partner_id)
                    if not invoice.qbo_invoice_id:
                        raise ValidationError(
                            f"Linked Invoice {invoice.name} is not exported to QuickBooks."
                        )

                    paid_amount = invoice.amount_total - invoice.amount_residual
                    total_amount += paid_amount

                    line_vals.append({
                        "Amount": paid_amount,
                        "LinkedTxn": [{
                            "TxnId": invoice.qbo_invoice_id,
                            "TxnType": "Invoice"
                        }]
                    })

                if not line_vals:
                    raise ValidationError(
                        f"No valid invoice lines found for POS payment {payment.name}."
                    )

                # ------------------------------------------------------------
                # 5️⃣ Prepare QBO Payment Payload
                # ------------------------------------------------------------
                vals = {
                    "TxnDate": str(payment.date),
                    "PaymentRefNum": payment.name,
                    "TotalAmt": total_amount,
                    "CustomerRef": {
                        "value": partner
                    },
                    "DepositToAccountRef": {
                        "value": deposit_account.qbo_id
                    },
                    "Line": line_vals
                }

                # ------------------------------------------------------------
                # 6️⃣ Send Request to QuickBooks
                # ------------------------------------------------------------
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }

                url = f"{quickbook_config.url}{realm_id}/payment"

                response = requests.post(url, headers=headers, data=json.dumps(vals))

                if response.status_code != 200:
                    raise ValidationError(
                        f"Failed to export POS Payment {payment.name} to QBO. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )

                response_dict = quickbook_config.convert_xmltodict(response.text)
                qbo_payment_id = (
                    response_dict.get('IntuitResponse', {})
                    .get('Payment', {})
                    .get('Id')
                )

                if not qbo_payment_id:
                    raise ValidationError(
                        f"QuickBooks response did not return Payment ID for {payment.name}."
                    )

                payment.qbo_payment_id = qbo_payment_id
                self.env.cr.commit()

            except Exception as e:
                failed_moves.append(payment)
                if from_button:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': payment.name,
                        'odoo_object': 'account.move',
                        'message': f"Error exporting POS Payment {payment.name}: {str(e)}",
                        'activity': 'Exporting POS Payment',
                        'created_date': fields.Datetime.now(),
                    })
                else:
                    raise ValidationError(
                        f"Error exporting POS Payment {payment.name}: {str(e)}"
                    )

        # ------------------------------------------------------------
        # 7️⃣ Final Result / Notification
        # ------------------------------------------------------------
        if failed_moves:
            failed_names = ", ".join(failed_moves.mapped('name'))
            raise ValidationError(
                f"The following POS payments failed to export:\n{failed_names}"
            )

        success_form = self.env.ref(
            'pragmatic_quickbooks_connector_canada.export_successfull_view', False
        )
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'res.company.message',
            'views': [(success_form.id, 'form')],
            'target': 'new',
        }


    @api.model
    def export_journal_entry(self, company=None):
        """export journal enrty to QBO"""
        from_button = self._context.get('from_button', False)
        if not company:
            quickbook_config = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
            if not quickbook_config:
                quickbook_config = self.env.company
            if not quickbook_config:
                quickbook_config = self.env.company
            access_token = None
            realmId = None
        else:
            quickbook_config = company

        if quickbook_config.access_token:
            access_token = quickbook_config.access_token
        if quickbook_config.realm_id:
            realmId = quickbook_config.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'

        invoice = self
        for t in invoice:
            if t.move_type == 'entry':  # Journal Entry
                if not t.qbo_invoice_id:
                    if t.state == 'posted':
                        values = t.prepare_qbo_journal_export_dict()
                        parsed_dict = json.dumps(values)

                        _logger.info(
                            "\n\nPrepared Dictionary :   {} ".format(parsed_dict))

                        data = requests.request('POST', quickbook_config.url + str(realmId) + "/journalentry",
                                                headers=headers, data=parsed_dict)
                        if data.status_code == 200:
                            response_data = quickbook_config.convert_xmltodict(
                                data.text)
                            # update QBO invoice id
                            if response_data.get('IntuitResponse').get('JournalEntry'):
                                t.qbo_invoice_id = response_data.get(
                                    'IntuitResponse').get('JournalEntry').get('Id')
                                self._cr.commit()
                                _logger.info(_("Exported successfully to QBO"))
                        else:
                            _logger.info(
                                _("[%s] %s" % (data.status_code, data.reason)))
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': 'Invoices Failed to Export',
                                    'odoo_object': 'account.move',
                                    'message': f"Journl Entry: {t.name, data.status_code, data.reason, data.text}",
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    _("Journl Entry[%s] [%s] %s %s" % (t.name, data.status_code, data.reason,
                                                                       data.text)))
                    else:
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': 'Invoices Failed to Export',
                                'odoo_object': 'account.move',
                                'message': "Only Posted state Invoice is exported to QBO.",
                                'activity': 'Exporting Invoice from Odoo',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise ValidationError(
                                _("Only Posted state Invoice is exported to QBO."))
                else:
                    _logger.info(
                        _("%s Journal Entry is already exported to QBO. Please, export a different Journal Entry." % t.name))
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'Invoices Failed to Export',
                            'odoo_object': 'account.move',
                            'message': f"{t.name} Journal Entry is already exported to QBO. Please, export a different Journal Entry.",
                            'activity': 'Exporting Invoice from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(
                            _("%s Journal Entry is already exported to QBO. Please, export a different Journal Entry." % t.name))

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

    def prepare_qbo_journal_export_dict(self):
        from_button = self._context.get('from_button', False)
        company = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id
        vals = {}
        narration = None
        if self.ref:
            narration = self.ref

        if self.date:
            date = str(self.date)

        #  Preparing Lines for export Journal
        journal_line_ids = []
        line_amount = None
        currency_name = ''
        if self.line_ids:
            for line in self.line_ids:
                line_dict = {}
                postingtype = ''

                if line.credit > 0:
                    postingtype = 'Credit'
                    line_amount = float(line.credit)
                elif line.debit > 0:
                    postingtype = 'Debit'
                    line_amount = float(line.debit)

                if line.currency_id and line.currency_id.name != company.currency_id.name and line.amount_currency:
                    currency_name = str(line.currency_id.name)
                    if line.amount_currency > 0:
                        postingtype = 'Credit'
                        line_amount = float(line.amount_currency)
                    elif line.amount_currency < 0:
                        postingtype = 'Debit'
                        line_amount = -1 * float(line.amount_currency)
                if line.amount_currency:
                    if line.amount_currency > 0:
                        postingtype = 'Credit'
                        line_amount = float(line.amount_currency)
                    elif line.amount_currency < 0:
                        postingtype = 'Debit'
                        line_amount = -1 * float(line.amount_currency)

                if line.account_id:
                    _logger.info('\n\n Acount ID : %s' % (line.account_id))
                    if line.account_id.qbo_id:
                        account_code = line.account_id.qbo_id
                        account_name = str(line.account_id.name)
                    else:
                        accounts = self.env['account.account'].browse(
                            line.account_id.id)
                        # self.export_to_qbo_main(accounts)
                        accounts.export_single_account()
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': 'Doesnot Exists',
                                'odoo_object': 'account.move',
                                'message': 'Account Code ' + line.account_id.code + ' doesnot exists for QBO in Odoo. ',
                                'activity': 'Exporting Invoice from Odoo',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise UserError(
                                'Account Code ' + line.account_id.code + ' doesnot exists for QBO in Odoo. ')

                if not postingtype:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'Doesnot Exists',
                            'odoo_object': 'account.move',
                            'message': 'Joual Entry ' + self.name + ' doesnot have Credit Debits. ',
                            'activity': 'Exporting Invoice from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise UserError(
                            'Joual Entry ' + self.name + ' doesnot have Credit Debits. ')

                line_dict.update({
                    "JournalEntryLineDetail": {
                        "PostingType": postingtype,
                        "AccountRef": {
                            "name": account_name,
                            "value": account_code
                        }
                    },
                    'DetailType': 'JournalEntryLineDetail',
                    'Amount': line_amount,
                    'Description': line.name,

                })
                if not line.partner_id and line.account_id.account_type == 'asset_receivable':
                    if not company.default_customer_journal_entry:
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': 'UserError',
                                'odoo_object': 'account.move',
                                'message': "Set Default Customer Journal Entry",
                                'activity': 'Exporting Invoice from Odoo',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise ValidationError(_("Set Default Customer Journal Entry"))
                    else:
                        if not company.default_customer_journal_entry.qbo_customer_id:
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': 'Not Sync in Quickbook',
                                    'odoo_object': 'account.move',
                                    'message': f"{company.default_customer_journal_entry.name} is not sync in quickbook",
                                    'activity': 'Exporting Invoice from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    _(f"{company.default_customer_journal_entry.name} is not sync in quickbook"))
                        customer_name = company.default_customer_journal_entry.name
                        customer_value = company.default_customer_journal_entry.qbo_customer_id
                        if line_dict.get('JournalEntryLineDetail'):
                            line_dict.get('JournalEntryLineDetail').update({
                                "Entity": {
                                    "Type": "Customer",
                                    "EntityRef": {
                                        "name": customer_name,
                                        "value": customer_value
                                    }
                                }
                            })

                journal_line_ids.append(line_dict)
        vals.update({"Line": journal_line_ids})
        vals.update({
            "TxnDate": date,
            "PrivateNote": narration,
            "CurrencyRef": {"value": 'USD', "name": 'United States Dollar'}
        })
        if currency_name:
            vals.update({
                "CurrencyRef": {"value": currency_name, "name": currency_name}
            })

        return vals
