# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import ast
from odoo.exceptions import UserError
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)
from odoo.tools import safe_eval
import requests
import json


class Mapping(models.Model):
    _name = 'mapping.fields'
    _description = 'Mapping'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade',
                               help="Model on which the server action runs.")
    name = fields.Char('Name', required=True)
    model_name = fields.Char(related='model_id.model', string='Model Name', readonly=True, store=True)
    fields_lines = fields.One2many('mapping.fields.object.lines', 'mapping_id', string='Value Mapping', copy=False)
    search_field_odoo_id = fields.Many2one('ir.model.fields', string='Search Field (Odoo)', required=True,
                                           ondelete='cascade')
    search_field_qbo = fields.Char('Search Field (QBO)')
    json_data = fields.Text('JSON Data')
    default_vals = fields.Text('Default Value')

    # mapping_sub_field = fields.One2many('mapping.sub.fields.object.lines', 'mapping_id', string='Sub Field Mapping', copy=False)

    @api.onchange('model_id')
    def onchange_model_id(self):
        if self.model_id:
            self.name = self.model_id.name

    def lookup_dot_separated_key(self, data, key):
        value = data
        for k in key.split('.'):
            value = value.get(k, '')
            if not value:
                return value
        return value

    def write(self, vals):

        res = super(Mapping, self).write(vals)

        if not self.json_data or not self.env.context.get('import'):
            return res
        company_id = self.env.company
        apr_obj = self.env['account.payment.register']
        for data in ast.literal_eval(self.json_data):
            qbo_already_exists = False
            vals = {self.search_field_odoo_id.name: data.get('Id')}

            if self.default_vals:
                vals.update(ast.literal_eval(self.default_vals))
            qbo_id = self.lookup_dot_separated_key(data, self.search_field_qbo)

            map_line1 = []
            for map_line in self.fields_lines.filtered(lambda l: l.ttype not in ['one2many', 'many2many']):
                if map_line.col1.name in vals and vals.get(map_line.col1.name):
                    continue

                map_line1.append(map_line.relation)

                value = self.lookup_dot_separated_key(data, map_line.value)

                if not value:
                    continue
                if map_line.require and not value:
                    raise UserError(_("Require Field (%s) not set properly!") % (map_line.col1.name))

                if map_line.relation:
                    if map_line.col1.ttype == 'many2one':

                        # Check for 'account.account' model and 'user_type_id' field
                        if self.model_name == 'account.account' and map_line.col1.name == 'user_type_id':
                            relation_id = self.env['account.account'].get_account_type(value)
                            vals.update({map_line.col1.name: relation_id.id})

                        # Check for 'account.journal' relation
                        elif map_line.relation == 'account.journal' and value:
                            journal_id = self.env[map_line.relation].get_journal_from_account(value)
                            if journal_id:
                                vals.update({map_line.col1.name: journal_id})

                        # Generic handling for other many2one fields
                        else:
                            relation_id = self.env[map_line.relation].search(
                                [(map_line.relation_field.name, '=', value)], limit=1)
                            if relation_id:
                                vals.update({map_line.col1.name: relation_id.id})

                elif map_line.col1.ttype == 'selection':
                    if self.model_name == 'product.product' and map_line.col1.name == 'type':
                        type_value = 'consu'
                        if value == 'Inventory':
                            type_value = 'product'
                        elif value == 'Service':
                            type_value = 'service'
                        vals.update({map_line.col1.name: type_value})
                    elif self.model_name == 'hr.employee' and map_line.col1.name == 'gender':
                        gender_type = 'female'
                        if value == 'Male':
                            gender_type = 'male'
                        elif value == 'Other':
                            gender_type = 'other'
                        vals.update({map_line.col1.name: gender_type})
                else:
                    vals.update({map_line.col1.name: value})



            object_id = self.env[self.model_name].sudo().search([(self.search_field_odoo_id.name, '=', int(qbo_id))])
            #
            if self.model_name == 'account.payment.term':
                vals.update({'line_ids': [(0, 0, {'value': 'percent', 'nb_days': data.get('DueDays'),
                                                  'days_after': data.get('DayOfMonthDue')})]})
            if object_id:
                _logger.info("Value is ***************1234**** {}".format(vals))
                res = object_id.write(vals)
                if self.model_name not in ['res.partner']:
                    qbo_already_exists = True
            else:
                # vals.update({self.search_field_odoo_id.name: qbo_id})
                _logger.info("Value is ******************* {}".format(vals))
                if self.model_name != 'account.payment':
                    object_id = object_id.create(vals)

            if self.model_name == 'account.payment':
                am_obj = self.env['account.move']
                all_vals = vals.keys()
                ori_val = vals.copy()
                req_vals = ['partner_type', 'payment_type', 'payment_method_id', 'partner_id', 'journal_id', 'amount',
                            'currency_id']
                rem_list = list(all_vals - req_vals)
                [vals.pop(key) for key in rem_list]
                for inv_rec in data.get('Line'):
                    if inv_rec.get('LinkedTxn') and inv_rec.get('LinkedTxn')[0].get('TxnId') and (
                            inv_rec.get('LinkedTxn')[0].get('TxnType') in ['Invoice', 'Bill']):
                        pay_invoice = am_obj.search(
                            [('qbo_invoice_id', '=', inv_rec.get('LinkedTxn')[0].get('TxnId'))], limit=1)
                        if pay_invoice:
                            if pay_invoice.state == 'draft':
                                _logger.info('<---------Invoice is going to open state----------> %s', pay_invoice)
                                pay_invoice.action_post()
                            ori_val.update({'payment_reference': pay_invoice.name})
                            register_payments = apr_obj.with_context(
                                active_model='account.move',
                                active_ids=pay_invoice.id).create(vals)
                            object_id = register_payments._create_payments()
                            object_id.sudo().write(ori_val)
            if self.env.context.get('import'):
                attr = getattr(object_id, self.search_field_odoo_id.name)
                if self.model_name == 'sale.order':
                    company_id.quickbooks_last_sale_imported_id = attr
                if self.model_name == 'account.move':
                    if object_id.move_type == 'out_invoice':
                        company_id.quickbooks_last_invoice_imported_id = attr
                    elif object_id.move_type == 'in_invoice':
                        company_id.quickbooks_last_vendor_bill_imported_id = attr
                    elif object_id.move_type == 'out_refund':
                        company_id.quickbooks_last_credit_note_imported_id = attr
                elif self.model_name == 'purchase.order':
                    company_id.quickbooks_last_purchase_imported_id = attr
                elif self.model_name == 'res.partner':
                    if self.env.context.get('mapping_customer'):
                        company_id.last_imported_customer_id = attr
                    else:
                        company_id.last_imported_vendor_id = attr
                elif self.model_name == 'product.product':
                    company_id.last_imported_product_id = attr
                elif self.model_name == 'product.category':
                    company_id.last_imported_product_category_id = attr
                elif self.model_name == 'account.account':
                    company_id.last_acc_imported_id = attr
                elif self.model_name == 'account.payment.term':
                    company_id.x_quickbooks_last_paymentterm_imported_id = attr
                elif self.model_name == 'account.payment':
                    if object_id.partner_type == 'customer':
                        company_id.last_imported_payment_id = attr
                    else:
                        company_id.last_imported_bill_payment_id = attr

            subvals_list = []
            children_tax_ids = []
            if not qbo_already_exists:
                for map_line in self.fields_lines.filtered(lambda l: l.ttype in ['many2many']):
                    if not self.model_name == 'account.tax':
                        continue
                    check_list = self.lookup_dot_separated_key(data, map_line.value)
                    type_tax_use = 'purchase'
                    if map_line.value == 'SalesTaxRateList.TaxRateDetail':
                        type_tax_use = 'sale'
                    if check_list and isinstance(check_list, list):
                        for d in check_list:
                            url_str = company_id.get_import_query_url()
                            url = url_str.get('url') + '/taxrate/%s' % d.get('TaxRateRef').get('value')
                            data1 = requests.request('GET', url, headers=url_str.get('headers'))
                            if data1.status_code == 200:
                                res = json.loads(str(data1.text))
                                _logger.info("Tax Rate Result %s" % (res))
                                child_id = self.env[self.model_name].create({
                                    'name': res.get('TaxRate').get('Name', '') + ' %',
                                    'description': res.get('TaxRate').get('Description', ''),
                                    'qbo_tax_rate_id': res.get('TaxRate').get('Id'),
                                    'amount_type': 'percent',
                                    'amount': res.get('TaxRate').get('RateValue'),
                                    'type_tax_use': type_tax_use,
                                })
                                children_tax_ids.append((child_id.id))
                for map_line in self.fields_lines.filtered(lambda l: l.ttype in ['one2many']):
                    if not qbo_already_exists and self.model_name in ['res.partner']:
                        domain = [(map_line.col1.relation_field, '=', object_id.id)]
                        if map_line.sub_field_object_id.default_domain:
                            domain += safe_eval.safe_eval(map_line.sub_field_object_id.default_domain)
                        check_record = self.env[map_line.sub_field_object_id.model_name].search(domain)
                        if check_record:
                            check_record.unlink()

                    check_list = self.lookup_dot_separated_key(data, map_line.value)
                    if check_list and isinstance(check_list, list):
                        for d in check_list:
                            if not d.get('Id'):
                                continue
                            subvals = {map_line.col1.relation_field: int(object_id.id)}
                            if self.model_name == 'account.move':
                                item_line = ''
                                if object_id.move_type in ['out_invoice', 'out_refund']:
                                    item_line = 'SalesItemLineDetail'
                                elif object_id.move_type == 'in_invoice':
                                    item_line = 'ItemBasedExpenseLineDetail'
                                if item_line and d.get(item_line, False) and d.get(item_line, False).get(
                                        'TaxCodeRef', False).get('value', False) == 'TAX':
                                    if data.get('TxnTaxDetail', False) and data.get('TxnTaxDetail', False).get(
                                            'TaxLine', False) and data.get('TxnTaxDetail', False).get('TaxLine', False)[
                                        0].get('TaxLineDetail', False).get('TaxRateRef', False).get('value', False):
                                        tax_ref = data.get('TxnTaxDetail', False).get('TaxLine', False)[0].get(
                                            'TaxLineDetail', False).get('TaxRateRef', False).get('value', False)
                                        tax_ids = self.env['account.tax'].search([('qbo_tax_rate_id', '=', tax_ref)])
                                        if tax_ids:
                                            subvals.update({
                                                'tax_ids': [(6, 0, tax_ids.ids)]
                                            })
                                subvals.update({
                                    'account_id': self.env.user.company_id.qb_income_account.id})
                            if self.model_name == 'sale.order':
                                item_line = 'SalesItemLineDetail'
                                if item_line and d.get(item_line, False) and d.get(item_line, False).get(
                                        'TaxCodeRef', False).get('value', False) == 'TAX':
                                    if data.get('TxnTaxDetail', False) and data.get('TxnTaxDetail', False).get(
                                            'TaxLine', False) and data.get('TxnTaxDetail', False).get('TaxLine', False)[
                                        0].get('TaxLineDetail', False).get('TaxRateRef', False).get('value', False):
                                        tax_ref = data.get('TxnTaxDetail', False).get('TaxLine', False)[0].get(
                                            'TaxLineDetail', False).get('TaxRateRef', False).get('value', False)
                                        tax_ids = self.env['account.tax'].search([('qbo_tax_rate_id', '=', tax_ref)])
                                        if tax_ids:
                                            subvals.update({
                                                'tax_id': [(6, 0, tax_ids.ids)]
                                            })
                            if map_line.sub_field_object_id.default_vals:
                                subvals.update(ast.literal_eval(map_line.sub_field_object_id.default_vals))

                            for sub_line in map_line.sub_field_object_id.sub_field_ids:
                                sub_value = self.lookup_dot_separated_key(d, sub_line.qb_field)
                                if sub_line.relation:
                                    if sub_line.ttype == 'many2one':
                                        relation_id = self.env[sub_line.relation].search(
                                            [(sub_line.relation_field.name, '=', sub_value)], limit=1)
                                        if relation_id:
                                            subvals.update({sub_line.field_id.name: relation_id.id})
                                else:
                                    subvals.update({sub_line.field_id.name: sub_value})
                            if subvals.get('analytic_distribution') and self.model_name == 'account.move':
                                analytic_obj = self.env['account.analytic.account'].search(
                                    [('name', '=', subvals.get('analytic_distribution'))], limit=1)
                                if analytic_obj:
                                    subvals.update({'analytic_distribution': {analytic_obj.id: 100}})

                            if self.model_name == 'account.move':
                                subvals_list.append(subvals)
                            else:
                                self.env[map_line.sub_field_object_id.model_name].create(subvals)

                    else:
                        subvals = {map_line.col1.relation_field: int(object_id.id)}
                        if map_line.sub_field_object_id.default_vals:
                            subvals.update(ast.literal_eval(map_line.sub_field_object_id.default_vals))
                        for sub_line in map_line.sub_field_object_id.sub_field_ids:
                            if not data.get(map_line.value, ''):
                                continue
                            sub_value = self.lookup_dot_separated_key(data.get(map_line.value), sub_line.qb_field)
                            if sub_line.relation:
                                if sub_line.ttype == 'many2one':
                                    relation_id = self.env[sub_line.relation].search(
                                        [(sub_line.relation_field.name, '=', sub_value)])
                                    if relation_id:
                                        subvals.update({sub_line.field_id.name: relation_id.id})
                            else:
                                subvals.update({
                                    sub_line.field_id.name: sub_value
                                })
                        self.env[map_line.sub_field_object_id.model_name].create(subvals)
            if self.model_name == 'account.move' and subvals_list:
                invoice_line_ids = []
                for val in subvals_list:
                    invoice_line_ids.append((0, 0, val))
                object_id.invoice_line_ids = invoice_line_ids
                object_id.action_post()
            if self.model_name == 'account.tax' and children_tax_ids:
                object_id.write({'children_tax_ids': [(6, 0, children_tax_ids)]})
        return res


class MappingFieldsObjectLines(models.Model):
    _name = 'mapping.fields.object.lines'
    _description = 'Mapping Fields Object Lines'

    mapping_id = fields.Many2one('mapping.fields', string='Related', ondelete='cascade')
    require = fields.Boolean('Require?')
    col1 = fields.Many2one('ir.model.fields', string='Odoo Field', required=True, ondelete='cascade')
    value = fields.Text(string='QB Field')
    relation = fields.Char(related='col1.relation')
    ttype = fields.Selection(related='col1.ttype')
    relation_field = fields.Many2one('ir.model.fields', 'Relation Search Field')
    om_relation_field_id = fields.Many2one('ir.model.fields', string='O2M/M2M Relation Field', ondelete='cascade')
    sub_field_object_id = fields.Many2one('mapping.sub', 'Sub Field')


class MappingSub(models.Model):
    _name = 'mapping.sub'
    _description = 'Mapping Sub'

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade',
                               help="Model on which the server action runs.")
    model_name = fields.Char(related='model_id.model', string='Model Name', readonly=True, store=True)
    default_vals = fields.Text('Default Value')
    default_domain = fields.Text('Default Domain')
    sub_field_ids = fields.One2many('mapping.sub.fields.object.lines', 'mapping_sub_id')


class MappingSubFieldsObjectLines(models.Model):
    _name = 'mapping.sub.fields.object.lines'
    _description = 'Mapping Fields Object Lines'

    mapping_sub_id = fields.Many2one('mapping.sub', string='Related', ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', string='Fields', required=True, ondelete='cascade')
    relation = fields.Char(related='field_id.relation')
    ttype = fields.Selection(related='field_id.ttype')
    relation_field = fields.Many2one('ir.model.fields', 'Relation Search Field')
    qb_field = fields.Text(string='QB Field', required=True)
