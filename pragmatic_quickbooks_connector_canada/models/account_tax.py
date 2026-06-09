# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime

import requests

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = "account.tax"

    qbo_tax_id = fields.Char(
        "QBO Tax Id", copy=False, help="QuickBooks database recordset id")
    qbo_tax_rate_id = fields.Char(
        "QBO Tax Rate Id", copy=False, help="QuickBooks database recordset id")
    tax_agency_id = fields.Many2one(
        'account.tax.agency', string='Agency', help="Tax agency reference")

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Inherited to add help attribute to name field"""
        res = super(AccountTax, self).fields_get(
            allfields, attributes=attributes)
        if 'name' in res:
            if 'help' in res['name']:
                help_str = res['name'].get(
                    'help', '') + ' In case of QBO it will accept tax code max 100 chars and tax rate max 10 chars.'
            else:
                help_str = 'In case of QBO it will accept tax code max 100 chars and tax rate max 10 chars.'
            res['name'].update({'help': help_str})
        return res

    @api.model
    def get_account_tax_ref(self, qbo_tax_id, name, type_tax_use="none", company=None):
        try:
            if not qbo_tax_id or not name or not company:
                raise ValidationError(
                    f"Missing required fields to fetch tax reference. [QBO Tax ID: {qbo_tax_id}]"
                )
            tax = self.search(['&', '|', ('name', '=', name),
                            ('description', '=', name),
                            ('qbo_tax_id', '=', qbo_tax_id),
                            ('type_tax_use', '=', type_tax_use), ('company_id', '=', company.id)], limit=1,
                            order="id Desc")
            if not tax:
                tax = self.search(['&', '|', ('name', '=', name),
                                ('description', '=', name),
                                ('qbo_tax_rate_id', '=', qbo_tax_id),
                                ('type_tax_use', '=', type_tax_use), ('company_id', '=', company.id)], limit=1,
                                order="id Desc")
            if tax:
                return tax.id
            else:
                raise ValidationError(
                    f"No matching tax found for QBO Tax ID: {qbo_tax_id} and name: {name}"
                )
                # Tax Creation code required time being skipped
        except Exception as e:
            raise ValidationError(
                f"Error occurred while fetching tax for QBO Tax ID: {qbo_tax_id}. Details: {str(e)}"
            )

    @api.model
    def get_qbo_tax_code(self, taxes):
        if len(taxes) > 1:
            raise ValidationError(_("Only Single composite tax required"))
        for tax in taxes:
            if tax.amount_type != 'group':
                raise ValidationError(_("Composite tax required"))
            if tax.qbo_tax_id:
                return tax.qbo_tax_id
            else:
                raise ValidationError(_("Tax not exported to QBO."))

    @api.model
    def create_account_tax(self, data, company=None):
        """Create account tax object in odoo
        :param data: account tax object response return by QBO
        :return int: last import QBO account tax Id
        """
        try:
            res = json.loads(str(data.text))
        except Exception as e:
            raise ValidationError(f"Invalid JSON response from QBO. Error: {str(e)}")
    
        tax_obj = False
        try:
            if 'QueryResponse' in res:
                taxes = res.get('QueryResponse').get('TaxCode', [])
            else:
                taxes = [res.get('TaxCode')] or []
            if len(taxes) == 0:
                raise UserError(
                    "It seems that all of the Taxes are already imported.")
            max_result = res.get('QueryResponse').get('maxResults')
            if not company:
                company = self.env.user.company_id

            for tax in taxes:
                try:
                    _logger.info(_("\n\nTax Name : %s" % (tax.get('Name', ''))))
                    _logger.info(_("\n\nTax Id : %s" % (tax.get('Id'))))

                    qbo_tax_id = tax.get('Id', 'Unknown')

                    if not tax.get('Active') and len(taxes) == 1:
                        raise ValidationError(f"Inactive tax found and no other tax to import. QBO Tax ID: {qbo_tax_id}")
                    
                    if 'Active' in tax and tax.get('Active'):
                        if 'Taxable' in tax and tax.get('Taxable'):

                            vals = {
                                'name': tax.get('Name', ''),
                                'description': tax.get('Description', ''),
                                'qbo_tax_id': tax.get('Id'),
                                'amount': 0,
                                'amount_type': 'group',
                                'company_id': company.id,
                                'country_id': company.country_id.id,
                            }

                            if 'TaxGroup' in tax and tax.get('TaxGroup'):
                                purchase_tax_rate_ids = []
                                sale_tax_rate_ids = []

                                # Make two different taxes for purchase and sale tax
                                # scope
                                if tax.get('PurchaseTaxRateList').get('TaxRateDetail', []):
                                    for tax_rate in tax.get('PurchaseTaxRateList').get('TaxRateDetail', []):
                                        purchase_tax_rate_ids.append(
                                            self.create_tax_rate(tax_rate, type_tax_use='purchase', company=company).id)
                                    vals.update({
                                        'type_tax_use': 'purchase',
                                        'children_tax_ids': [(6, 0, purchase_tax_rate_ids)],
                                    })
                                    tax_obj = self.search(
                                        [('qbo_tax_id', '=', tax.get('Id')), ('type_tax_use', '=', 'purchase'),
                                        ('company_id', '=', company.id)],
                                        limit=1) or self.search(
                                        [('name', '=', tax.get('Name')), ('type_tax_use', '=', 'purchase'),
                                        ('company_id', '=', company.id)], limit=1)

                                    if not tax_obj:
                                        tax_obj = self.create(vals)
                                        _logger.info(
                                            _("Account tax created sucessfully! Tax Id: %s" % (tax_obj.id)))

                                        if company.import_tax_by_date:
                                            try:
                                                date_format = '%Y-%m-%d'
                                                if company.tax_import_by == 'crt_dt':
                                                    date_string = tax.get('MetaData').get(
                                                        'CreateTime')[:10]
                                                else:
                                                    date_string = tax.get('MetaData').get(
                                                        'LastUpdatedTime')[:10]

                                                date_object = datetime.strptime(date_string,
                                                                                date_format).date()
                                                company.import_tax_date = date_object
                                            except Exception as e:
                                                _logger.error(f"Failed to parse date for tax ID: {qbo_tax_id}. Error: {e}")
                                                raise ValidationError(f"Failed to parse date for tax ID: {qbo_tax_id}. Error: {e}")
                                    elif tax_obj and not (tax_obj.qbo_tax_id or tax_obj.qbo_tax_rate_id):
                                        tax_obj.write(vals)
                                        _logger.info(
                                            _("Account tax updated sucessfully! Tax Id: %s" % (tax_obj.id)))
                                    self._cr.commit()

                                if tax.get('SalesTaxRateList').get('TaxRateDetail', []):
                                    for tax_rate in tax.get('SalesTaxRateList').get('TaxRateDetail', []):
                                        sale_tax_rate_ids.append(
                                            self.create_tax_rate(tax_rate, type_tax_use='sale', company=company).id)
                                    vals.update({
                                        'type_tax_use': 'sale',
                                        'children_tax_ids': [(6, 0, sale_tax_rate_ids)],
                                    })
                                    tax_obj = self.search([('qbo_tax_id', '=', tax.get('Id')), ('type_tax_use', '=', 'sale'),
                                                        ('company_id', '=', company.id)],
                                                        limit=1) or self.search(
                                        [('name', '=', tax.get('Name')), ('type_tax_use', '=', 'sale'),
                                        ('company_id', '=', company.id)], limit=1)

                                    if not tax_obj:
                                        tax_obj = self.create(vals)

                                        _logger.info(
                                            _("Account tax created sucessfully! Tax Id: %s" % (tax_obj.id)))
                                    elif tax_obj and not (tax_obj.qbo_tax_id or tax_obj.qbo_tax_rate_id):
                                        tax_obj.write(vals)
                                        _logger.info(
                                            _("Account tax updated sucessfully! Tax Id: %s" % (tax_obj.id)))
                                    self._cr.commit()
                        else:
                            _logger.info("Taxable key not found!")
                            raise ValidationError(f"'Taxable' key missing or false for tax. QBO Tax ID: {qbo_tax_id}")
                except Exception as inner_exc:
                    _logger.error(f"Error processing tax with QBO ID: {tax.get('Id')}. Error: {inner_exc}")
                    raise ValidationError(f"Failed to process tax with QBO ID: {tax.get('Id')}. Error: {str(inner_exc)}")
        except (UserError, ValidationError):
            raise
        except Exception as main_exc:
            _logger.error(f"Failed to process QBO tax data. Error: {main_exc}")
            raise ValidationError(f"Error occurred while creating account tax: {str(main_exc)}")
        return max_result

    @api.model
    def create_tax_rate(self, tax_rate, type_tax_use='none', company=None):
        """Create tax rate in Odoo"""
        try:
            if not company:
                company = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_id
            url_str = company.get_import_query_url()

            tax_qbo_id = tax_rate.get('TaxRateRef', {}).get('value')
            if not tax_qbo_id:
                raise ValidationError("Tax QBO ID is missing in the input data.")
        
            #         .browse(self._context.get('qbo_config_id')).get_import_query_url()
            url = url_str.get(
                'url') + '/taxrate/%s' % tax_rate.get('TaxRateRef').get('value')
            
            data = requests.request('GET', url, headers=url_str.get('headers'))

            if data.status_code == 200:
                res = json.loads(str(data.text))
                _logger.info("Tax Rate Result %s" % (res))
                agency = False
                if 'AgencyRef' in res.get('TaxRate'):
                    agency = self.env['account.tax.agency'].search(
                        [('qbo_agency_id', '=', res.get('TaxRate').get('AgencyRef').get('value'))], limit=1)
                    # If tax agency is not created in odoo then import from QBO and
                    # create.
                    if not agency:
                        try:
                            url_str = company.get_import_query_url()
                            url = url_str.get(
                                'url') + '/taxagency/' + res.get('TaxRate').get('AgencyRef').get('value')
                            data = requests.request(
                                'GET', url, headers=url_str.get('headers'))
                            if data.status_code == 200:
                                agency = self.env[
                                    'account.tax.agency'].create_account_tax_agency(data)
                            else:
                                raise ValidationError(_("Failed to fetch or create Tax Agency for Tax ID: %s" % tax_qbo_id))
                        except Exception as e:
                            raise ValidationError(_("Error processing Tax Agency for Tax ID: %s - %s" % (tax_qbo_id, str(e))))

                account = False
                if 'TaxReturnLineRef' in res.get('TaxRate'):
                    try:
                        account = self.env['account.account'].search(
                            [('qbo_id', '=', res.get('TaxRate').get('TaxReturnLineRef').get('value')),
                            ('company_ids', '=', company.id)], limit=1)
                        # If account is not created in odoo then import from QBO and
                        # create.
                        _logger.info("Tax rate account value %s" % (
                            res.get('TaxRate').get('TaxReturnLineRef').get('value')))
                        _logger.info("Account Taxrate %s" % (account))
                        if not account:
                            url_str = company.get_import_query_url()
                            url = url_str.get(
                                'url') + '/account/' + res.get('TaxRate').get('TaxReturnLineRef').get('value')
                            data = requests.request(
                                'GET', url, headers=url_str.get('headers'))
                            if data.status_code == 200:
                                account = self.env[
                                    'account.account'].create_account_account(data)
                            else:
                                raise ValidationError(_("Failed to fetch or create Account for Tax ID: %s" % tax_qbo_id))
                    except Exception as e:
                        raise ValidationError(_("Error processing Account for Tax ID: %s - %s" % (tax_qbo_id, str(e))))

                TaxRateValue = 0
                try:
                    if res.get('TaxRate').get('RateValue'):
                        TaxRateValue = float(res.get('TaxRate').get('RateValue') or 0)
                    elif 'EffectiveTaxRate' in res.get('TaxRate'):
                        for value in res.get('TaxRate').get('EffectiveTaxRate'):
                            if not value.get('EndDate'):
                                TaxRateValue = float(value.get('RateValue') or 0)
                                break
                except Exception:
                    raise ValidationError(_("Invalid RateValue in QBO Tax Rate for Tax ID: %s" % tax_qbo_id))

                # 'name': res.get('TaxRate').get('Name', '') + ' %',
                vals = {
                    'name': res.get('TaxRate').get('Name', '') + ' %',
                    'description': res.get('TaxRate').get('Description', ''),
                    'qbo_tax_rate_id': res.get('TaxRate').get('Id'),
                    'amount_type': 'percent',
                    'amount': TaxRateValue,
                    'type_tax_use': type_tax_use,
                    'tax_agency_id': agency.id if agency else False,
                    'company_id': company.id,
                    'country_id': company.country_id.id,

                }
                tax_obj = self.search(
                    [('qbo_tax_rate_id', '=', res.get('TaxRate').get('Id')), ('company_id', '=', company.id)], limit=1)
                if not tax_obj:
                    tax_group = self.env['account.tax.group'].search([('company_id','=',company.id),('country_id','=',company.country_id.id)],limit=1)
                    if not tax_group:
                        raise ValidationError(_(f"Please create a Tax Group for the country [{company.country_id.name}] in the company [{company.name}]."))
                    vals.update({'tax_group_id':tax_group.id})
                    tax_obj = self.create(vals)

                self.env.cr.commit()
                _logger.info(
                    _("Account tax created sucessfully! Tax Id: %s" % (tax_obj.id)))
                # quickbook_config.last_imported_tax_id = res.get('TaxRate').get('Id')
                return tax_obj
            else:
                _logger.warning(_('Empty data'))
                raise ValidationError(_("Unable to fetch Tax Rate from QBO for Tax ID: %s" % tax_qbo_id))
        except ValidationError as ve:
            _logger.error(str(ve))
            raise ve
        except Exception as e:
            _logger.exception("Unexpected error occurred while creating Tax Rate for Tax ID: %s" % tax_rate.get('TaxRateRef', {}).get('value'))
            raise ValidationError(_("Unexpected error occurred while processing Tax ID: %s - %s" % (
                tax_rate.get('TaxRateRef', {}).get('value'), str(e))))

    # @api.one
    def export_tax_code_to_qbo(self):
        from_button = self._context.get('from_button', False)

        company = self.company_id
        if not company:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'account.tax',
                    'message': f'"Set Company for Tax":  {self.name}',
                    'activity': 'Exporting Tax from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_(f"Set Company for Tax {self.name}"))
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        tax = self
        tax_rate_details = []
        vals = {
            'TaxCode': tax.name,
        }
        try:
            if tax.children_tax_ids:
                for child_tax in tax.children_tax_ids:
                    # If child tax is not exported in QBO then export first and
                    # append return qbo id in tax_rate_ids
                    if child_tax.qbo_tax_rate_id:
                        tax_rate_details.append(
                            {'TaxRateId': child_tax.qbo_tax_rate_id})
                    else:
                        #                     child_tax.get_tax_rate_values(parent_tax = tax)
                        if not child_tax.tax_agency_id:
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': child_tax.name,
                                    'odoo_object': 'account.tax',
                                    'message': "Please select tax agency for child tax %s" % (child_tax.name),
                                    'activity': 'Exporting Tax from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(
                                    _("Please select tax agency for child tax %s" % (child_tax.name)))
                        elif not child_tax.tax_agency_id.qbo_agency_id:
                            child_tax.tax_agency_id.with_context(
                                agency_id=child_tax.tax_agency_id.id).export_to_qbo()

                        rate_vals = {
                            'TaxRateName': child_tax.name,
                            'RateValue': str(child_tax.amount),
                            'TaxAgencyId': child_tax.tax_agency_id.qbo_agency_id,
                            'TaxApplicableOn': 'Sales' if (tax.type_tax_use == 'sale') else 'Purchase',
                        }
                        tax_rate_details.append(rate_vals)
            else:
                if not tax.tax_agency_id:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': f'{tax.name}',
                            'odoo_object': 'account.tax',
                            'message': f'"Please select tax agency for" : {tax.name}',
                            'activity': 'Export Tax from odoo',
                            'created_date': fields.Datetime.now(),

                        })

                        self.env.cr.commit()

                        # Ensure the transaction is committed
                        # raise ValidationError(
                        #     _("Please select tax agency for %s33" % (tax.name)))
                    else:
                        raise ValidationError(
                            _("Please select tax agency for %s" % (tax.name)))
                elif not tax.tax_agency_id.qbo_agency_id:
                    tax.tax_agency_id.with_context(
                        agency_id=tax.tax_agency_id.id).export_to_qbo()

                rate_vals = {
                    'TaxRateName': tax.name,
                    'RateValue': str(tax.amount),
                    'TaxAgencyId': tax.tax_agency_id.qbo_agency_id,
                    'TaxApplicableOn': 'Sales' if (tax.type_tax_use == 'sale') else 'Purchase',
                }
                tax_rate_details.append(rate_vals)

            vals.update({'TaxRateDetails': tax_rate_details})
            parsed_dict = json.dumps(vals)
            access_token = None
            realmId = None

            if company.access_token:
                access_token = company.access_token
            if company.realm_id:
                realmId = company.realm_id

            if access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(access_token)
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'

                result = requests.request('POST', company.url + str(realmId) + "/taxservice/taxcode", headers=headers,
                                        data=parsed_dict)
                if result.status_code == 200:

                    response = result.json()
                    TaxRateDetails = response.get('TaxRateDetails', [])
                    # iterating over response to map tax rate id to qbo tax rate
                    for taxRate in TaxRateDetails:
                        tax_rate = self.search(['&', '|', ('name', '=', taxRate.get('TaxRateName')),
                                                ('description', '=',
                                                taxRate.get('TaxRateName')),
                                                ('qbo_tax_rate_id', '=', False)], limit=1, order="id Desc")
                        if tax_rate:
                            tax_rate.ensure_one()
                            tax_rate.qbo_tax_rate_id = taxRate.get('TaxRateId')

                    tax.qbo_tax_id = response.get('TaxCodeId')
                    self._cr.commit()

                    # if company.last_imported_tax_id < response.get('TaxCodeId'):
                    #     company.last_imported_tax_id = response.get('TaxCodeId')
                    _logger.info(_("%s exported successfully to QBO" % (tax.name)))

                else:
                    _logger.error(
                        _("[%s] %s" % (result.status_code, result.reason)))
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': result.status_code,
                            'odoo_object': 'account.tax',
                            'message': f'"Error Occured" : {result.status_code, result.reason, result.text}',
                            'activity': 'Export Tax from odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(_("[%s] %s %s" % (result.status_code, result.reason, result.text)))
                return result
        except Exception as e:
            _logger.exception("Failed to export tax code")
            self.env['qbo.logger'].sudo().create({
                'odoo_name': tax.name,
                'odoo_object': 'account.tax',
                'message': str(e),
                'activity': 'Export tax code to QBO',
                'created_date': fields.Datetime.now(),
            })
            self.env.cr.commit()
            if not from_button:
                raise UserError(_("Failed to export tax code for tax: %s" % tax.name))

    @api.model
    def export_to_qbo(self):
        """Create account tax and tax rate in QBO"""
        #         company = self.env['res.users'].search([('id','=',self._uid)],limit=1).company_id
        if self._context.get('active_ids'):
            acc_taxes = self.env['account.tax'].browse(
                self._context.get('active_ids'))
        else:
            acc_taxes = self

        for tax in acc_taxes:
            # if tax.amount_type == 'group':
            tax.export_tax_code_to_qbo()
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
    def export_one_tax_at_a_time(self, tax_id):
        """Create account tax and tax rate in QBO"""
        acc_taxes = tax_id
        for tax in acc_taxes:
            # if tax.amount_type == 'group':
            tax.export_tax_code_to_qbo()


class AccountTaxAgency(models.Model):
    _name = "account.tax.agency"
    _description = "Account tax agency used for QBO"

    qbo_agency_id = fields.Char(
        "QBO Agency Id", copy=False, help="QuickBooks database recordset id")
    name = fields.Char("Name", required=True, help="Name of the agency.")
    tax_track_on_sale = fields.Boolean(
        "Tax tracked on sale", default=True, help="Denotes whether this tax agency is used to track tax on sales.")
    tax_track_on_purchase = fields.Boolean(
        "Tax tracked on purchase", help="Denotes whether this tax agency is used to track tax on purchases.")

    @api.model
    def create_account_tax_agency(self, data):
        """Create account tax object in odoo
        :param data: account tax object response return by QBO
        :return account.tax.agency: account tax agency object
        """
        try:
            res = json.loads(str(data.text))
            if 'QueryResponse' in res:
                TaxAgency = res.get('QueryResponse').get('TaxAgency', [])
            else:
                TaxAgency = [res.get('TaxAgency')] or []
            for agency in TaxAgency:
                if not agency:
                    raise ValidationError(_("Tax agency data is empty. Skipping processing."))
                
                qbo_id = agency.get("Id")
                if not qbo_id:
                    raise ValidationError(_("Missing QBO ID in Tax Agency data: %s" % str(agency)))
                
                vals = {
                    'name': agency.get("DisplayName", ''),
                    'qbo_agency_id': agency.get("Id"),
                    'tax_track_on_sale': agency.get('TaxTrackedOnSales'),
                    'tax_track_on_purchase': agency.get('TaxTrackedOnPurchases'),
                }

                try:
                    agency_obj = self.create(vals)
                    _logger.info(
                        _("Tax Agency created sucessfully! Agency Id: %s" % (agency_obj.id)))
                except Exception as e:
                    raise ValidationError(_("Failed to create Tax Agency with QBO ID %s. Error: %s" % (qbo_id, str(e))))
            return agency_obj
        except json.JSONDecodeError:
            raise ValidationError(_("Invalid JSON response received from QBO: %s" % str(data.text)))
        except Exception as e:
            raise ValidationError(_("An unexpected error occurred during Tax Agency creation. Error: %s" % str(e)))

    @api.model
    def export_to_qbo(self):
        """Create account tax agency in QBO"""
        if self._context.get('agency_id'):
            agencies = self
        else:
            agencies = self.env['account.tax.agency'].browse(
                self._context.get('active_ids'))

        from_button = self._context.get('from_button', False)

        for agency in agencies:
            try: 
                vals = {
                    'DisplayName': agency.name,
                    'TaxTrackedOnSales': agency.tax_track_on_sale,
                    'TaxTrackedOnPurchases': agency.tax_track_on_purchase,
                }
                parsed_dict = json.dumps(vals)
                quickbook_config = self.env['res.users'].search(
                    [('id', '=', self._uid)], limit=1).company_id
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

                    result = requests.request(
                        'POST', quickbook_config.url + str(realmId) + "/taxagency", headers=headers, data=parsed_dict)

                    if result.status_code == 200:
                        # response text is either xml string or json string
                        if isinstance(result.text, str):
                            response = quickbook_config.convert_xmltodict(
                                result.text)
                            response = response.get('IntuitResponse')
                        else:
                            response = json.loads(result.text, encoding='utf-8')

                        # update agency id and last sync id
                        agency.qbo_agency_id = response.get('TaxAgency').get('Id')
                        quickbook_config.last_imported_tax_agency_id = response.get(
                            'TaxAgency').get('Id')

                        _logger.info(
                            _("%s exported successfully to QBO" % (agency.name)))
                    else:
                        if from_button:
                            _logger.error(
                                _("[%s] %s" % (result.status_code, result.reason)))
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': result.status_code,
                                'odoo_object': 'account.tax',
                                'message': f'"Error Occured" : {result.status_code, result.reason, result.text}',
                                'activity': 'Export Tax Agency from odoo',
                                'created_date': fields.Datetime.now(),
                            })
                        else:
                            raise ValidationError(
                                _("[%s] %s %s" % (result.status_code, result.reason, result.text)))
            except Exception as e:
                _logger.exception("Error exporting tax agency to QBO")
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': agency.name,
                    'odoo_object': 'account.tax.agency',
                    'message': str(e),
                    'activity': 'Export Tax Agency to QBO',
                    'created_date': fields.Datetime.now(),
                })
                self.env.cr.commit()
                if not from_button:
                    raise UserError(_("Failed to export tax agency to QBO."))
