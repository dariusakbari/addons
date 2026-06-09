from odoo import api, fields, models, _
import requests
import json
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import datetime
import traceback

_logger = logging.getLogger(__name__)


class ResCountry(models.Model):
    _inherit = "res.country"

    @api.model
    def get_country_ref(self, country_name):
        """
        This method take country name as an argument and return county id
        :param country_name: name of the country
        :rtype int: return a recordset id
        """
        try:
            country = None
            if country_name:
                country = self.search([('name', '=', country_name)], limit=1)
                return country.id
            else:
                _logger.info('Country not found in odoo')
                return False
        except Exception:
            return False


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    @api.model
    def get_state_ref(self, state_name, country_name):
        """
        This method take state name as an argument and return state id
        :param state_name: name of state
        :param country_name: name of country
        :rtype int: return a recordset id
        """
        try:
            if state_name:
                _logger.info(_("QBO State : %s" % (state_name)))
                _logger.info(_("QBO Country : %s" % (country_name)))

                country_id = self.env[
                    'res.country'].get_country_ref(country_name)
                if not country_id:
                    context = self._context.get('params').get('id')
                    company = self.env['res.company'].search(
                        [('id', '=', context)])
                    country_id = company.country_id.id
                state = self.search(
                    [('name', '=', state_name), ('country_id', '=', country_id)], limit=1)
                if not state:
                    state_name = state_name.upper()
                    state = self.search(
                        [('code', '=', state_name), ('country_id', '=', country_id)], limit=1)
                    _logger.info(
                        "State not found in Odoo for received company")
                    # state = self.create({'name': state_name, 'country_id': country_id, 'code': state_name})

                if not state:
                    return False
                else:
                    return state.id
            else:
                return False
        except Exception:
            return False


class ResPartner(models.Model):
    _inherit = "res.partner"

    qbo_vendor_id = fields.Char(
        "QBO Vendor Id", copy=False, help="QuickBooks database recordset id")
    qbo_customer_id = fields.Char(
        "QBO Customer Id", copy=False, help="QuickBooks database recordset id")
    x_quickbooks_exported = fields.Boolean(
        "Exported to Quickbooks ? ", default=False, copy=False)
    x_quickbooks_updated = fields.Boolean(
        "Updated in Quickbook ?", default=False)
    check_update_flag = fields.Boolean('Check Flag')
    mobile = fields.Char(string='Mobile', copy=False)

    ''' For Import Partner'''

    # @api.model
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if not val.get('company_id'):
                val['company_id'] = self.env.user.company_id.id
            val['check_update_flag'] = False
            if self.env.context.get('default_is_company'):
                val['check_update_flag'] = True
            if 'res_partner_search_mode' in self._context and self._context.get(
                    'res_partner_search_mode') == 'customer':
                val['customer_rank'] = 1
            if 'res_partner_search_mode' in self._context and self._context.get(
                    'res_partner_search_mode') == 'supplier':
                val['supplier_rank'] = 1
        res = super(ResPartner, self).create(vals)
        return res

    def write(self, vals):
        vals['check_update_flag'] = False
        if self.env.context.get('default_is_company'):
            vals['check_update_flag'] = True
        res = super(ResPartner, self).write(vals)
        return res

    # @api.model
    # def attachCustomerTitle(self, title):
    #     try:
    #         res_partner_tile = self.env['res.partner.title']
    #         title_id = False
    #         qbo_id = self._context.get('qbo_id') or 'Unknown'
    #
    #         if title:
    #             title_id = res_partner_tile.search([('name', '=', title)], limit=1)
    #             if not title_id:
    #                 try:
    #                     ''' Create New Title in Odoo '''
    #                     create_id = res_partner_tile.create({'name': title})
    #                     # create_id = title_id.id
    #                     if create_id:
    #                         return create_id.id
    #                 except Exception as e:
    #                     raise ValidationError(
    #                         f"Failed to create new title '{title}' for QBO ID: {qbo_id or 'Unknown'}. Error: {str(e)}"
    #                     )
    #             return title_id.id
    #     except Exception as e:
    #         raise ValidationError(
    #             f"Error attaching title '{title}' for QBO ID: {qbo_id or 'Unknown'}. Error: {str(e)}"
    #         )

    @api.model
    def get_parent_customer_ref(self, qbo_parent_id, company=None):
        try:
            if not qbo_parent_id:
                raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Missing required QuickBooks customer ID.")
        
            if not company:
                # try:
                company = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_id
                if not company:
                    raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Company could not be determined from user.")
                # except Exception as e:
                #     raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Error while determining company: {str(e)}")
            # try:
            partner = self.search(
                [('qbo_customer_id', '=', qbo_parent_id), ('company_id', '=', company.id)], limit=1)
            # except Exception as e:
            #     raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Error while searching for partner: {str(e)}")
            
            if not partner:
                # try:
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/customer/' + qbo_parent_id
                data = requests.request('GET', url, headers=url_str.get('headers'))
                if data.status_code == 200:
                    partner = self.create_partner(data, is_customer=True, company=company)
                else:
                    raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Failed to fetch customer from QBO. Status code: {data.status_code}")
                # except Exception as e:
                #     raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Error while fetching or creating partner from QBO: {str(e)}")
            return partner.id
        except ValidationError as ve:
            raise ve
        except UserError as ue:
            raise ue
        except Exception as e:
            raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Unexpected error: {str(e)}")

    @api.model
    def get_parent_vendor_ref(self, qbo_parent_id, company=None):
        try:
            if not qbo_parent_id:
                raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Missing required QuickBooks customer ID.")
            
            if not company:
                # try:
                company = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_id
                if not company:
                    raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Company could not be determined from user.")
                # except Exception as e:
                #     raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Error while determining company: {str(e)}")
            
            # try:
            partner = self.search([('qbo_vendor_id', '=', qbo_parent_id), ('company_id', '=', company.id)], limit=1)
            # except Exception as e:
            #     raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Error while searching for partner: {str(e)}")
            
            if not partner:
                # try:
                url_str = company.get_import_query_url()
                url = url_str.get('url') + '/vendor/' + qbo_parent_id
                data = requests.request('GET', url, headers=url_str.get('headers'))
                if data.status_code == 200:
                    partner = self.create_partner(data, is_vendor=True)
                else:
                    raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Failed to fetch customer from QBO. Status code: {data.status_code}")
                # except Exception as e:
                #     raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Error while fetching or creating partner from QBO: {str(e)}")
            return partner.id
        except ValidationError as ve:
            raise ve
        except UserError as ue:
            raise ue
        except Exception as e:
            raise ValidationError(f"[QBO_ID: {qbo_parent_id}] Unexpected error: {str(e)}")

    @api.model
    def _prepare_partner_dict(self, partner, is_customer=False, is_vendor=False, company=None):
        try:
            vals = {
                'company_type': 'person' if partner.get('Job') else 'company',
                'name': partner.get('DisplayName'),
                'qbo_customer_id': partner.get('Id') if is_customer else '',
                'qbo_vendor_id': partner.get('Id') if is_vendor else '',
                # 'customer': is_customer,
                # 'supplier': is_vendor,
                'email': partner.get('PrimaryEmailAddr').get('Address') if partner.get('PrimaryEmailAddr') else '',
                'phone': partner.get('PrimaryPhone').get('FreeFormNumber') if partner.get('PrimaryPhone') else '',
                'mobile': partner.get('Mobile').get('FreeFormNumber') if partner.get('Mobile') else '',
                'website': partner.get('WebAddr').get('URI') if partner.get('WebAddr') else '',
                'active': partner.get('Active'),
                'comment': partner.get('Notes'),
            }
            if is_customer:
                vals.update({'customer_rank': 1})
            if is_vendor:
                vals.update({'supplier_rank': 1})
            if partner.get('GivenName'):
                vals.update({'name': partner.get('GivenName')})
            if partner.get('MiddleName'):
                vals.update({'name': partner.get('MiddleName')})
            if partner.get('FamilyName'):
                vals.update({'name': partner.get('FamilyName')})
            if partner.get('GivenName') and partner.get('MiddleName'):
                vals.update(
                    {'name': partner.get('GivenName') + ' ' + partner.get('MiddleName')})
            if partner.get('MiddleName') and partner.get('FamilyName'):
                vals.update(
                    {'name': partner.get('MiddleName') + ' ' + partner.get('FamilyName')})
            if partner.get('GivenName') and partner.get('FamilyName'):
                vals.update(
                    {'name': partner.get('GivenName') + ' ' + partner.get('FamilyName')})
            if partner.get('GivenName') and partner.get('MiddleName') and partner.get('FamilyName'):
                vals.update(
                    {'name': partner.get('GivenName') + ' ' + partner.get('MiddleName') + ' ' + partner.get('FamilyName')})

            if 'DisplayName' in partner and partner.get('DisplayName'):
                vals.update({'name': partner.get('DisplayName')})
            if 'Title' in partner and partner.get('Title'):
                ''' If Title is present then first check in odoo if title exists or not
                if exists attach Id of tile else create new and attach its ID'''
                # try:
                #     title = self.attachCustomerTitle(partner.get('Title'))
                #     vals.update({'title': title})
                # except Exception as e:
                #     raise ValidationError(_("Error while attaching title for QBO ID {}: {}".format(partner.get('Id'), str(e))))

            # Checking for Account Receivable and Account Payable
            try:
                if not company:
                    company = self.env['res.users'].search(
                        [('id', '=', self._uid)]).company_id
                if not company:
                    company = self.env.company
                if company.qb_account_recievable and company.qb_account_payable:
                    vals.update({'property_account_receivable_id': company.qb_account_recievable.id,
                                'property_account_payable_id': company.qb_account_payable.id
                                })
                else:
                    _logger.info("Account Payable or Receivable is not set!")
                    raise ValidationError(_(
                        """It seems that Account Payable or Account Receivable is not set for QBO ID {}.
                        Please navigate to Settings ---> Companies ---> QuickBooks Tab.
                        Under QB Account Configuration, please set Account Receivable and Account Payable.
                        """.format(partner.get('Id'))
                    ))
            except Exception as e:
                raise ValidationError(_("Error while setting accounts for QBO ID {}: {}".format(partner.get('Id'), str(e))))

            if 'BillAddr' in partner and partner.get('BillAddr'):
                try:
                    address_vals = {
                        'street': partner.get('BillAddr').get('Line1') or '',
                        'city': partner.get('BillAddr').get('City') or '',
                        'zip': partner.get('BillAddr').get('PostalCode') or '',
                    }

                    if 'line2' in partner.get('BillAddr'):
                        address_vals.update({
                            'street2': partner.get('BillAddr').get('Line2') if 'Line2' in partner.get(
                                'BillAddr') else '',
                        })

                    if 'Country' in partner.get('BillAddr'):
                        address_vals.update({
                            'state_id': self.env['res.country.state'].get_state_ref(
                                partner.get('BillAddr').get('CountrySubDivisionCode'),
                                partner.get('BillAddr').get('Country')) if partner.get('BillAddr').get(
                                'CountrySubDivisionCode') else False,
                            'country_id': self.env['res.country'].get_country_ref(
                                partner.get('BillAddr').get('Country')) if partner.get('BillAddr').get('Country') else False,
                        })

                    vals.update(address_vals)
                except Exception as e:
                    raise ValidationError(_("Error processing address for QBO ID {}: {}".format(partner.get('Id'), str(e))))

            # if 'ParentRef' in partner:
            #     if is_customer:
            #         vals.update({'parent_id': self.get_parent_customer_ref(partner.get('ParentRef').get('value'))})
            #     if is_vendor:
            #         vals.update({'parent_id': self.get_parent_vendor_ref(partner.get('ParentRef').get('value'))})

            return vals
        except Exception as e:
            raise ValidationError(_("An unexpected error occurred while preparing partner dict for QBO ID {}: {}".format(partner.get('Id'), str(e))))

    @api.model
    def create_partner(self, data, is_customer=False, is_vendor=False, company=None):
        """Create partner object in odoo
        :param data: partner object response return by QBO
        :param is_customer: True if partner is a customer
        :param is_vendor: True if partener is a supplier/vendor
        :return int: last import QBO customer or vendor Id
        """
        try:
            res = json.loads(str(data.text))
        except Exception as e:
            raise ValidationError("Failed to parse QBO response: %s" % str(e))
        
        brw_partner = False
        try:
            if is_customer:
                if 'QueryResponse' in res:
                    partners = res.get('QueryResponse').get('Customer', [])
                else:
                    partners = [res.get('Customer')] or []
            elif is_vendor:
                if 'QueryResponse' in res:
                    partners = res.get('QueryResponse').get('Vendor', [])
                else:
                    partners = [res.get('Vendor')] or []
            else:
                partners = []

            # _logger.info(_('\n\nQbo Dict : %s'% partners))

            if len(partners) == 0:
                raise UserError(
                    "It seems that all of the Customers/Vendors are already imported.")
            max_result = res.get('QueryResponse').get('maxResults')
            if not company:
                company = self.env.company
            for partner in partners:
                try:
                    qbo_id = partner.get('Id', 'Unknown ID')
                    vals = self._prepare_partner_dict(
                        partner, is_customer=is_customer, is_vendor=is_vendor, company=company)
                    if company:
                        vals.update({'company_id': company.id})

                    _logger.info(
                        "\n\n\n qbo partner dict : {}\n\n\n\n".format(partner))
                    _logger.info(
                        "VALS For Partner Creation IS !!!!!!!!!!!!---> {}".format(vals))
                    brw_partner = self.search(
                        ['|', ('qbo_customer_id', '=', partner.get('Id')), ('name', '=', partner.get('DisplayName')),
                        ('company_id', '=', company.id)], limit=1)
                    _logger.info("Browsing partner************ {}".format(brw_partner))
                    if not brw_partner:
                        _logger.info(
                            "Customer needs to be created$$$$$$$$$$$$$$$$$$${}".format(vals))
                        brw_partner = self.search(
                            ['|', ('qbo_vendor_id', '=', partner.get('Id')), ('name', '=', partner.get('DisplayName')),
                            ('company_id', '=', company.id)],
                            limit=1)
                        if not brw_partner:
                            try:
                                brw_partner = self.create(vals)
                            except Exception as e:
                                raise ValidationError("Error creating partner with QBO ID {}: {}".format(qbo_id, str(e)))
                            
                            try:
                                if 'BillAddr' in partner and partner.get('BillAddr'):
                                    address_vals = {
                                        'street': partner.get('BillAddr').get('Line1') or '',
                                        'city': partner.get('BillAddr').get('City') or '',
                                        'zip': partner.get('BillAddr').get('PostalCode') or '',
                                        'type': 'invoice',
                                        'parent_id': brw_partner.id
                                    }

                                    if 'line2' in partner.get('BillAddr'):
                                        address_vals.update({
                                            'street2': partner.get('BillAddr').get('Line2') if 'Line2' in partner.get(
                                                'BillAddr') else '',
                                        })

                                    if 'Country' in partner.get('BillAddr'):
                                        address_vals.update({
                                            'state_id': self.env['res.country.state'].get_state_ref(
                                                partner.get('BillAddr').get('CountrySubDivisionCode'),
                                                partner.get('BillAddr').get('Country')) if 'Country' in partner.get(
                                                'BillAddr') and partner.get('BillAddr').get(
                                                'CountrySubDivisionCode') else False,
                                            'country_id': self.env['res.country'].get_country_ref(
                                                partner.get('BillAddr').get('Country')) if 'Country' in partner.get(
                                                'BillAddr') else False,  #
                                        })

                                    # Create partner billing address
                                    # bill_addr = self.create(address_vals)
                                    if brw_partner and address_vals:
                                        brw_partner.write({
                                            'child_ids': [(0, 0, address_vals)]
                                        })

                                    _logger.info(
                                        "BILL ADDRESS VALS IS ---> {} and created id : {}".format(address_vals,brw_partner.child_ids))
                            except Exception as e:
                                raise ValidationError("Error creating billing address for QBO ID {}: {}".format(qbo_id, str(e)))

                            try:
                                if 'ShipAddr' in partner and partner.get('ShipAddr'):
                                    address_vals = None
                                    address_vals = {
                                        'street': partner.get('ShipAddr').get('Line1') or '',
                                        'city': partner.get('ShipAddr').get('City') or '',
                                        'zip': partner.get('ShipAddr').get('PostalCode') or '',
                                        'type': 'delivery',
                                        'parent_id': brw_partner.id
                                    }

                                    if 'line2' in partner.get('ShipAddr'):
                                        address_vals.update({
                                            'street2': partner.get('ShipAddr').get('Line2') or '',
                                        })

                                    if 'Country' in partner.get('ShipAddr'):
                                        address_vals.update({
                                            'state_id': self.env['res.country.state'].get_state_ref(
                                                partner.get('ShipAddr').get(
                                                    'CountrySubDivisionCode'),
                                                partner.get('ShipAddr').get('Country')) if 'Country' in partner.get(
                                                'ShipAddr') and partner.get('ShipAddr').get(
                                                'CountrySubDivisionCode') else False,
                                            'country_id': self.env['res.country'].get_country_ref(
                                                partner.get('ShipAddr').get('Country')) if 'Country' in partner.get(
                                                'ShipAddr') else False,  #
                                        })

                                    # Create partner shipping address
                                    # ship_addr = self.create(address_vals)
                                    if brw_partner and address_vals:
                                        brw_partner.write({
                                            'child_ids': [(0, 0, address_vals)]
                                        })

                                    _logger.info(
                                        "Address Vals is ---> {} and created ids : {}".format(address_vals, brw_partner.child_ids))
                            except Exception as e:
                                raise ValidationError("Error creating shipping address for QBO ID {}: {}".format(qbo_id, str(e)))

                            _logger.info(
                                _("Partner created sucessfully! Partner Id: %s" % (brw_partner.id)))
                            if not company:
                                company = self.env.user.company_id
                            try:
                                if brw_partner.supplier_rank == 1:
                                    if company.import_vendor_by_date:
                                        date_format = '%Y-%m-%d'
                                        if company.vendor_import_by == 'crt_dt':
                                            date_string = partner.get('MetaData').get(
                                                'CreateTime')[:10]
                                        else:
                                            date_string = partner.get('MetaData').get(
                                                'LastUpdatedTime')[:10]

                                        date_object = datetime.strptime(date_string,
                                                                        date_format).date()
                                        company.import_vendor_date = date_object
                                else:
                                    if company.import_customer_by_date:
                                        date_format = '%Y-%m-%d'
                                        if company.cutomer_import_by == 'crt_dt':
                                            date_string = partner.get('MetaData').get(
                                                'CreateTime')[:10]
                                        else:
                                            date_string = partner.get('MetaData').get(
                                                'LastUpdatedTime')[:10]

                                        date_object = datetime.strptime(date_string,
                                                                        date_format).date()
                                        company.import_customer_date = date_object
                            except Exception as e:
                                raise ValidationError("Error setting import date for QBO ID {}: {}".format(qbo_id, str(e)))
                        else:
                            brw_partner.write(vals)
                            try:
                                if 'BillAddr' in partner and partner.get('BillAddr'):
                                    address_vals = {
                                        'street': partner.get('BillAddr').get('Line1') or '',
                                        'city': partner.get('BillAddr').get('City') or '',
                                        'zip': partner.get('BillAddr').get('PostalCode') or '',
                                        'type': 'invoice',
                                        'parent_id': brw_partner.id
                                    }

                                    if 'line2' in partner.get('BillAddr'):
                                        address_vals.update({
                                            'street2': partner.get('BillAddr').get('Line2') if 'Line2' in partner.get(
                                                'BillAddr') else '',
                                        })

                                    if 'Country' in partner.get('BillAddr'):
                                        address_vals.update({
                                            'state_id': self.env['res.country.state'].get_state_ref(
                                                partner.get('BillAddr').get(
                                                    'CountrySubDivisionCode'),
                                                partner.get('BillAddr').get('Country')) if partner.get('BillAddr').get(
                                                'CountrySubDivisionCode') else False,  # and partner.get('BillAddr').get('Country')
                                            'country_id': self.env['res.country'].get_country_ref(
                                                partner.get('BillAddr').get('Country')) if partner.get('BillAddr').get(
                                                'Country') else False,  #
                                        })

                                    # Update partner billing address
                                    _logger.info(
                                        "BILL ADDRESS VALS TO UPDATE ---> {}".format(address_vals))
                                    bill_addr = self.write(address_vals)
                            except Exception as e:
                                raise ValidationError("Error updating billing address for QBO ID {}: {}".format(qbo_id, str(e)))
                            
                            try:
                                if 'ShipAddr' in partner and partner.get('ShipAddr'):
                                    address_vals = {
                                        'street': partner.get('ShipAddr').get('Line1') or '',
                                        'city': partner.get('ShipAddr').get('City') or '',
                                        'zip': partner.get('ShipAddr').get('PostalCode') or '',
                                        'type': 'delivery',
                                        'parent_id': brw_partner.id
                                    }

                                    if 'line2' in partner.get('ShipAddr'):
                                        address_vals.update({
                                            'street2': partner.get('ShipAddr').get('Line2') or '',
                                        })

                                    if 'Country' in partner.get('ShipAddr'):
                                        address_vals.update({
                                            'state_id': self.env['res.country.state'].get_state_ref(
                                                partner.get('ShipAddr').get(
                                                    'CountrySubDivisionCode'),
                                                partner.get('ShipAddr').get('Country')) if 'Country' in partner.get(
                                                'ShipAddr') and partner.get('ShipAddr').get(
                                                'CountrySubDivisionCode') else False,
                                            'country_id': self.env['res.country'].get_country_ref(
                                                partner.get('ShipAddr').get('Country')) if 'Country' in partner.get(
                                                'ShipAddr') else False,  #
                                        })

                                    # Create partner shipping address
                                    ship_addr = self.write(address_vals)
                            except Exception as e:
                                raise ValidationError("Error updating shipping address for QBO ID {}: {}".format(qbo_id, str(e)))

                            _logger.info(
                                _("Partner Updated sucessfully! Partner Id: %s" % (brw_partner.id)))
                            company = self.env.user.company_id

                            try:
                                if brw_partner.supplier_rank == 1:
                                    if company.import_vendor_by_date:
                                        date_format = '%Y-%m-%d'
                                        if company.vendor_import_by == 'crt_dt':
                                            date_string = partner.get('MetaData').get(
                                                'CreateTime')[:10]
                                        else:
                                            date_string = partner.get('MetaData').get(
                                                'LastUpdatedTime')[:10]

                                        date_object = datetime.strptime(date_string,
                                                                        date_format).date()
                                        company.import_vendor_date = date_object
                                else:
                                    date_format = '%Y-%m-%d'
                                    if company.cutomer_import_by == 'crt_dt':
                                        date_string = partner.get('MetaData').get(
                                            'CreateTime')[:10]
                                    else:
                                        date_string = partner.get('MetaData').get(
                                            'LastUpdatedTime')[:10]

                                    date_object = datetime.strptime(date_string,
                                                                    date_format).date()
                                    company.import_customer_date = date_object
                            except Exception as e:
                                raise ValidationError("Error setting import date for QBO ID {}: {}".format(qbo_id, str(e)))
                    else:
                        _logger.info("Customer needs to be updated")
                        # update_customer = self.env['ir.config_parameter'].sudo().get_param(
                        #     'pragmatic_quickbooks_connector_canada.update_customer_import')
                        if not company:
                            company = self.env['res.users'].search(
                                [('id', '=', self._uid)]).company_id
                        update_customer = company.update_customer_import
                        if update_customer:
                            try:
                                brw_partner.write(vals)
                            except Exception as e:
                                raise ValidationError("Error updating partner with QBO ID {}: {}".format(qbo_id, str(e)))
                            
                            try:
                                if 'BillAddr' in partner and partner.get('BillAddr'):
                                    address_vals = {
                                        'street': partner.get('BillAddr').get('Line1') or '',
                                        'city': partner.get('BillAddr').get('City') or '',
                                        'zip': partner.get('BillAddr').get('PostalCode') or '',
                                        'type': 'invoice',
                                        'parent_id': brw_partner.id
                                    }

                                    if 'line2' in partner.get('BillAddr'):
                                        address_vals.update({
                                            'street2': partner.get('BillAddr').get('Line2') if 'Line2' in partner.get(
                                                'BillAddr') else '',
                                        })

                                    if 'Country' in partner.get('BillAddr'):
                                        address_vals.update({
                                            'state_id': self.env['res.country.state'].get_state_ref(
                                                partner.get('BillAddr').get(
                                                    'CountrySubDivisionCode'),
                                                partner.get('BillAddr').get('Country')) if partner.get('BillAddr').get(
                                                'CountrySubDivisionCode') else False,  # and partner.get('BillAddr').get('Country')
                                            'country_id': self.env['res.country'].get_country_ref(
                                                partner.get('BillAddr').get('Country')) if partner.get('BillAddr').get(
                                                'Country') else False,  #
                                        })
                                    # Create partner billing address
                                    for partner_obj in brw_partner.child_ids:
                                        if partner_obj.type == 'invoice':
                                            ship_addr = partner_obj.sudo().write(address_vals)
                            except Exception as e:
                                raise ValidationError("Error updating billing address for QBO ID {}: {}".format(qbo_id, str(e)))

                            try:
                                if 'ShipAddr' in partner and partner.get('ShipAddr'):
                                    # Create partner billing address
                                    address_vals = {
                                        'street': partner.get('ShipAddr').get('Line1') or '',
                                        'city': partner.get('ShipAddr').get('City') or '',
                                        'zip': partner.get('ShipAddr').get('PostalCode') or '',
                                        'type': 'delivery',
                                        'parent_id': brw_partner.id
                                    }

                                    if 'line2' in partner.get('ShipAddr'):
                                        address_vals.update({
                                            'street2': partner.get('ShipAddr').get('Line2') or '',
                                        })

                                    if 'Country' in partner.get('ShipAddr'):
                                        address_vals.update({
                                            'state_id': self.env['res.country.state'].get_state_ref(
                                                partner.get('ShipAddr').get(
                                                    'CountrySubDivisionCode'),
                                                partner.get('ShipAddr').get('Country')) if partner.get('ShipAddr').get(
                                                'CountrySubDivisionCode') else False,  # and partner.get('ShipAddr').get('Country')
                                            'country_id': self.env['res.country'].get_country_ref(
                                                partner.get('ShipAddr').get('Country')) if partner.get('ShipAddr').get(
                                                'Country') else False,
                                        })
                                    for partner_obj in brw_partner.child_ids:
                                        if partner_obj.type == 'delivery':
                                            ship_addr = partner_obj.sudo().write(address_vals)
                                _logger.info(
                                    _("Partner updated sucessfully! Partner Id: %s" % (brw_partner.id)))
                            except Exception as e:
                                raise ValidationError("Error updating shipping address for QBO ID {}: {}".format(qbo_id, str(e)))
                except ValidationError:
                    raise
                except Exception as e:
                    raise ValidationError("Error processing QBO partner with ID {}: {}".format(qbo_id, str(e)))      
            return max_result
        except (UserError, ValidationError):
            raise
        except Exception as e:
            raise ValidationError("Unexpected error while processing partners: {}".format(str(e)))

    ''' Uncategorized '''

    @api.model
    def get_qbo_partner_ref(self, partner):
        from_button = self._context.get('from_button', False)
        # _logger.info('\n\n Inside get_qbo_partner_ref : '.format(partner))
        if partner.customer_rank:
            if partner.qbo_customer_id or (partner.parent_id and partner.parent_id.qbo_customer_id):
                return partner.qbo_customer_id or partner.parent_id.qbo_customer_id
            else:
                self.export_single_Partner(partner)
                if partner.qbo_customer_id or (partner.parent_id and partner.parent_id.qbo_customer_id):
                    return partner.qbo_customer_id or partner.parent_id.qbo_customer_id
                else:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'Error Occured',
                            'odoo_object': 'res.partner',
                            'message': "Partner is not exported to QBO",
                            'activity': 'Export from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(_("Partner is not exported to QBO"))
        else:
            if partner.qbo_vendor_id or (partner.parent_id and partner.parent_id.qbo_vendor_id):
                return partner.qbo_vendor_id or partner.parent_id.qbo_vendor_id
            else:
                self.export_single_Partner(partner)
                if partner.qbo_vendor_id or (partner.parent_id and partner.parent_id.qbo_vendor_id):
                    return partner.qbo_vendor_id or partner.parent_id.qbo_vendor_id
                else:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'Error Occured',
                            'odoo_object': 'res.partner',
                            'message': "Partner is not exported to QBO",
                            'activity': 'Export from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(_("Partner is not exported to QBO"))

    ''' For Export Partner'''

    def sendDataToQuickbooksForUpdate(self, dict):

        company = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id

        ''' GET ACCESS TOKEN '''

        access_token = None
        realmId = None
        parsed_dict = json.dumps(dict)
        if company.access_token:
            access_token = company.access_token
        if company.realm_id:
            realmId = company.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

            result = requests.request(
                'POST', company.url + str(realmId) + "/customer?operation=update", headers=headers, data=parsed_dict)
            if result.status_code == 200:
                parsed_result = result.json()
                if parsed_result.get('Customer').get('Id'):
                    self.x_quickbooks_updated = True
                    return parsed_result.get('Customer').get('Id')
                else:
                    return False
            else:
                self.env['qbo.logger'].create({
                    'odoo_name': dict.get('DisplayName') if dict.get('DisplayName') else self,
                    'odoo_object': 'Customer',
                    'message': result.text,
                    'created_date': datetime.now(),
                })
                return False

    def sendDataToQuickbook(self, dict):
        from_button = self._context.get('from_button', False)
        company = self.company_id
        if not company:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'res.partner',
                    'message': f'"Set Company for Partner {self.name}"',
                    'activity': 'Exporting Partner from Odoo',
                    'created_date': fields.Datetime.now(),
                    # 'company_id': company.id,
                })
            else:
                raise ValidationError(_(f"Set Company for Partner {self.name}"))

        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id

        if not company:
            company = self.env.company

        _logger.info("COMPANY Name is ------------------------------{} :".format(company.id))

        ''' GET ACCESS TOKEN '''

        access_token = None
        realmId = None
        parsed_dict = json.dumps(dict)
        if company.access_token:
            access_token = company.access_token
        if company.realm_id:
            realmId = company.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            _logger.info(f"Parsed Data is ==================================", parsed_dict)

            result = requests.request(
                'POST', company.url + str(realmId) + "/customer", headers=headers, data=parsed_dict)
            if result.status_code == 200:
                parsed_result = result.json()
                if parsed_result.get('Customer').get('Id'):
                    if self.parent_id:
                        self.parent_id.x_quickbooks_exported = True
                        self.qbo_customer_id = parsed_result.get('Customer').get('Id')

                    if not self.parent_id:
                        self.x_quickbooks_exported = True
                        self.qbo_customer_id = parsed_result.get('Customer').get('Id')

                    self._cr.commit()
                    return parsed_result.get('Customer').get('Id')

                else:
                    return False

            elif result.status_code == 400:
                response = result.json()
                error = None
                _logger.info('\n\nError Response : {} '.format(response))
                self.env['qbo.logger'].create({
                    'odoo_name': dict.get('DisplayName') if dict.get('DisplayName') else self,
                    'odoo_object': 'Customer',
                    'message': result.text,
                    'created_date': datetime.now(),
                })
                if response.get('Fault'):
                    if response.get('Fault').get('Error'):
                        for message in response.get('Fault').get('Error'):
                            # updated existing qbo id
                            if message.get('code') == '6240':
                                partner_object = self.env['res.partner'].search(
                                    [('name', '=', dict.get('GivenName'))], limit=1)
                                if not partner_object:
                                    partner_object = self.env['res.partner'].search(
                                        [('name', 'ilike', str(dict.get('DisplayName')))], limit=1)
                                _logger.info('\n\n*******************: {}, {}, {}'.format(partner_object, dict.get('DisplayName'), dict.get('GivenName')))
                                if partner_object and partner_object.customer_rank:
                                    customer_qbo_id = self.checkPartnerInQuickbooks(
                                        partner_object)
                                    exsit_id = self.search([('qbo_customer_id','=',customer_qbo_id),('company_id','=',company.id)],limit=1)
                                    if not exsit_id:
                                        partner_object.write(
                                            {'qbo_customer_id': customer_qbo_id})
                                        partner_object._cr.commit()
                                    else:
                                        if from_button:
                                            self.env['qbo.logger'].create({
                                                'odoo_name': partner_object.name,
                                                'odoo_object': 'Customer',
                                                'message': f"Same Name Exist in Quickbook",
                                                'activity': 'Exporting Partner from Odoo',
                                                'created_date': datetime.now(),
                                            })
                                        else:
                                            raise ValidationError(_("Same Name Exist in Quickbook"))

                            if message.get('Detail') and message.get('Message'):
                                error = message.get('Detail')
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': "Error",
                                        'odoo_object': 'res.partner',
                                        'message': "Error From Qbo for exporting customer : %s" % error,
                                        'activity': 'Exporting Partner from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise UserError(
                                        _("Error From Qbo for exporting customer : %s" % error))
            else:
                self.env['qbo.logger'].create({
                    'odoo_name': dict.get('DisplayName') if dict.get('DisplayName') else self,
                    'odoo_object': 'Customer',
                    'message': result.text,
                    'created_date': datetime.now(),
                })
                return False

    def sendVendorDataToQuickbooksForUpdate(self, dict):
        from_button = self._context.get('from_button', False)
        company = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id

        ''' GET ACCESS TOKEN '''

        access_token = None
        realmId = None
        parsed_dict = json.dumps(dict)
        if company.access_token:
            access_token = company.access_token
        if company.realm_id:
            realmId = company.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

            result = requests.request(
                'POST', company.url + str(realmId) + "/vendor?operation=update", headers=headers, data=parsed_dict)
            if result.status_code == 200:
                parsed_result = result.json()
                if parsed_result.get('Vendor').get('Id'):
                    self.x_quickbooks_updated = True
                    return parsed_result.get('Vendor').get('Id')
                else:
                    return False
            else:
                if from_button:
                    self.env['qbo.logger'].create({
                        'odoo_name': dict.get('DisplayName') if dict.get('DisplayName') else self,
                        'odoo_object': 'Vendor',
                        'message': result.text,
                        'created_date': datetime.now(),
                    })
                else:
                    raise ValidationError(_("Error From Qbo for exporting Vendor : %s" % result.text))

    def sendVendorDataToQuickbook(self, dict):
        from_button = self._context.get('from_button', False)
        company = self.company_id
        if not company:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'res.partner',
                    'message': f'"Set Company for Partner {self.name}"',
                    'activity': 'Exporting Partner from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_(f"Set Company for Partner {self.name}"))
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        if not company:
            company = self.env.company

        ''' GET ACCESS TOKEN '''

        access_token = None
        realmId = None
        parsed_dict = json.dumps(dict)
        if company.access_token:
            access_token = company.access_token
        if company.realm_id:
            realmId = company.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

            result = requests.request(
                'POST', company.url + str(realmId) + "/vendor", headers=headers, data=parsed_dict)
            if result.status_code == 200:
                parsed_result = result.json()
                if parsed_result.get('Vendor').get('Id'):
                    if self.parent_id:
                        self.parent_id.x_quickbooks_exported = True
                    if not self.parent_id:
                        self.x_quickbooks_exported = True
                    self.qbo_vendor_id = parsed_result.get('Vendor').get('Id')
                    self._cr.commit()
                    return parsed_result.get('Vendor').get('Id')
                else:
                    return False
            elif result.status_code == 400:
                response = result.json()
                error = None
                if response.get('Fault'):
                    if response.get('Fault').get('Error'):
                        for message in response.get('Fault').get('Error'):
                            # updated existing qbo id
                            if message.get('code') == '6240':
                                partner_object = self.env['res.partner'].search(
                                    [('supplier_rank', '=', True), ('name', '=', dict.get('GivenName'))])
                                if not partner_object:
                                    partner_object = self.env['res.partner'].search(
                                        [('name', 'ilike', str(dict.get('DisplayName')))], limit=1)
                                if partner_object:
                                    vendor_qbo_id = self.checkPartnerInQuickbooks(
                                        partner_object)
                                    exsit_id = self.search(
                                        [('qbo_vendor_id', '=', vendor_qbo_id), ('company_id', '=', company.id)],
                                        limit=1)
                                    if not exsit_id:
                                        partner_object.write(
                                            {'qbo_vendor_id': vendor_qbo_id})
                                        partner_object._cr.commit()
                                    else:
                                        if from_button:
                                            self.env['qbo.logger'].create({
                                                'odoo_name': partner_object.name,
                                                'odoo_object': 'Vendor',
                                                'message': f"Same Name Exist in Quickbook",
                                                'activity': 'Exporting Partner from Odoo',
                                                'created_date': datetime.now(),
                                            })
                                        else:
                                            raise ValidationError(_("Same Name Exist in Quickbook"))


                            elif message.get('Detail') and message.get('Message'):
                                error = message.get('Detail')
                                if from_button:
                                    self.env['qbo.logger'].create({
                                        'odoo_name': dict.get('DisplayName') if dict.get('DisplayName') else self,
                                        'odoo_object': 'Vendor',
                                        'message': result.text,
                                        'activity': 'Exporting Partner from Odoo',
                                        'created_date': datetime.now(),
                                    })
                                else:
                                    raise ValidationError(_("Error From Qbo for exporting Vendor : %s" % error))
                                # raise UserError(_("Qbo Error : %s" %error))
                                
            else:
                self.env['qbo.logger'].create({
                    'odoo_name': dict.get('DisplayName') if dict.get('DisplayName') else self,
                    'odoo_object': 'Vendor',
                    'message': result.text,
                    'created_date': datetime.now(),
                })
                return False

    def prepareDictStructure(self, obj=False, record_type=None, customer_id_retrieved=False, is_update=False,
                             sync_token=False):
        data_object = None

        if obj:
            data_object = obj
        else:
            data_object = self

        ''' This Function Exports Record to Quickbooks '''
        dict = {}
        dict_phone = {}
        dict_email = {}
        dict_mobile = {}
        dict_billAddr = {}
        dict_shipAddr = {}
        dict_parent_ref = {}
        dict_job = {}

        if data_object.mobile:
            dict['Mobile'] = {'FreeFormNumber': str(data_object.mobile)}

        if data_object.website:
            dict['WebAddr'] = {'URI': str(data_object.website)}

        if data_object.comment:
            dict["Notes"] = data_object.comment


        if data_object.name:
            full_name = str(data_object.name)
            if len(full_name.split()) == 1:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = " "
                dict["FamilyName"] = " "
            if len(full_name.split()) == 2:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = " "
                dict["FamilyName"] = full_name.split()[1]

            if len(full_name.split()) == 3:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = full_name.split()[1]
                dict["FamilyName"] = full_name.split()[2]

            dict['DisplayName'] = str(data_object.name)
            dict['PrintOnCheckName'] = str(data_object.name)

        # if data_object.title:
        #     dict["Title"] = data_object.title.name

        if data_object.email:
            dict_email["PrimaryEmailAddr"] = {
                'Address': str(data_object.email)}

        if data_object.phone:
            dict_phone["PrimaryPhone"] = {
                'FreeFormNumber': str(data_object.phone)}

        if data_object.type == 'invoice' or data_object.type == 'contact':

            bill_addr = {}
            if data_object.street:
                bill_addr.update({'Line1': data_object.street, })
            if data_object.street2:
                bill_addr.update({'Line2': data_object.street2, })
            if data_object.city:
                bill_addr.update({'City': data_object.city, })
            if data_object.country_id:
                if data_object.country_id.name:
                    bill_addr.update(
                        {'Country': data_object.country_id.name, })
            if data_object.state_id:
                if data_object.state_id.name:
                    bill_addr.update(
                        {'CountrySubDivisionCode': data_object.state_id.name, })
            if data_object.zip:
                bill_addr.update({'PostalCode': data_object.zip, })

            dict_billAddr['BillAddr'] = bill_addr


        if self.type == 'delivery':

            ship_addr = {}
            if data_object.street:
                ship_addr.update({'Line1': data_object.street, })
            if data_object.street2:
                ship_addr.update({'Line2': data_object.street2, })
            if data_object.city:
                ship_addr.update({'City': data_object.city, })
            if data_object.country_id:
                if data_object.country_id.name:
                    ship_addr.update(
                        {'Country': data_object.country_id.name, })
            if data_object.state_id:
                if data_object.state_id.name:
                    ship_addr.update(
                        {'CountrySubDivisionCode': data_object.state_id.name, })
            if data_object.zip:
                ship_addr.update({'PostalCode': data_object.zip, })

            dict_shipAddr['ShipAddr'] = ship_addr


        dict.update(dict_email)
        dict.update(dict_phone)
        dict.update(dict_billAddr)
        dict.update(dict_shipAddr)

        if customer_id_retrieved and record_type and record_type == "indv_company":
            dict_parent_ref['ParentRef'] = {
                'value': str(customer_id_retrieved)}
            dict.update(dict_parent_ref)

            dict['Job'] = 'true'
        # _logger.info('\n\nDicttttttttttttt : {} '.format(dict))
        if is_update and customer_id_retrieved:
            dict['Id'] = str(customer_id_retrieved)
            dict['sparse'] = "true"

            ''' Check SyncToken '''
            if sync_token:
                dict['SyncToken'] = str(sync_token)
            result = self.sendDataToQuickbooksForUpdate(dict)
        else:
            if self.customer_rank:
                result = self.sendDataToQuickbook(dict)

            if self.supplier_rank:
                result = self.sendVendorDataToQuickbook(dict)

        if result:
            if is_update:
                _logger.info("UPDATED !!!!!!!!!!!!!!")
            else:
                _logger.info("EXPORTED !!!!!!!!!")
            return result
        else:
            _logger.info("ERROR WHILE UPLOADING !!!!!!!!!")

            return False

    def prepareVendorDictStructure(self, obj=False, record_type=None, vendor_id_retrieved=False, is_update=False,
                                   sync_token=False):
        data_object = None

        if obj:
            data_object = obj
        else:
            data_object = self

        ''' This Function Exports Record to Quickbooks '''
        dict = {}
        dict_phone = {}
        dict_email = {}
        dict_mobile = {}
        dict_billAddr = {}
        dict_shipAddr = {}
        dict_parent_ref = {}
        dict_job = {}

        if data_object.mobile:
            dict['Mobile'] = {'FreeFormNumber': str(data_object.mobile)}

        if data_object.website:
            dict['WebAddr'] = {'URI': str(data_object.website)}

        if data_object.comment:
            dict["Notes"] = data_object.comment

        if data_object.name:
            full_name = str(data_object.name)
            if len(full_name.split()) == 1:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = " "
                dict["FamilyName"] = " "
            if len(full_name.split()) == 2:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = " "
                dict["FamilyName"] = full_name.split()[1]

            if len(full_name.split()) == 3:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = full_name.split()[1]
                dict["FamilyName"] = full_name.split()[2]

            dict['DisplayName'] = str(data_object.name)
            dict['PrintOnCheckName'] = str(data_object.name)
        # if data_object.title:
        #     dict["Title"] = data_object.title.name
        if data_object.email:
            dict_email["PrimaryEmailAddr"] = {
                'Address': str(data_object.email)}

        if data_object.phone:
            dict_phone["PrimaryPhone"] = {
                'FreeFormNumber': str(data_object.phone)}

        if data_object.type == 'invoice' or data_object.type == 'contact':
            bill_addr = {}
            if data_object.street:
                bill_addr.update({'Line1': data_object.street, })
            if data_object.street2:
                bill_addr.update({'Line2': data_object.street2, })
            if data_object.city:
                bill_addr.update({'City': data_object.city, })
            if data_object.country_id:
                if data_object.country_id.name:
                    bill_addr.update(
                        {'Country': data_object.country_id.name, })
            if data_object.state_id:
                if data_object.state_id.name:
                    bill_addr.update(
                        {'CountrySubDivisionCode': data_object.state_id.name, })
            if data_object.zip:
                bill_addr.update({'PostalCode': data_object.zip, })
            dict_billAddr['BillAddr'] = bill_addr


        if self.type == 'delivery':

            ship_addr = {}
            if data_object.street:
                ship_addr.update({'Line1': data_object.street, })
            if data_object.street2:
                ship_addr.update({'Line2': data_object.street2, })
            if data_object.city:
                ship_addr.update({'City': data_object.city, })
            if data_object.country_id:
                if data_object.country_id.name:
                    ship_addr.update(
                        {'Country': data_object.country_id.name, })
            if data_object.state_id:
                if data_object.state_id.name:
                    ship_addr.update(
                        {'CountrySubDivisionCode': data_object.state_id.name, })
            if data_object.zip:
                ship_addr.update({'PostalCode': data_object.zip, })
            dict_shipAddr['ShipAddr'] = ship_addr


        dict.update(dict_email)
        dict.update(dict_phone)
        dict.update(dict_billAddr)
        dict.update(dict_shipAddr)



        if is_update and vendor_id_retrieved:

            dict['Id'] = str(vendor_id_retrieved)
            dict['sparse'] = "true"

            ''' Check SyncToken '''
            if sync_token:
                dict['SyncToken'] = str(sync_token)
            result = self.sendVendorDataToQuickbooksForUpdate(dict)
        else:
            result = self.sendVendorDataToQuickbook(dict)

        if result:
            if is_update:
                _logger.info("UPDATED !!!!!!!!!!!!!!")
            else:
                _logger.info("EXPORTED !!!!!!!!!!!222!!!")
            return result
        else:
            _logger.info("ERROR WHILE UPLOADING !!!!!!!!!!!!!!")

            return False

    def updateExistingCustomer(self, company=None):
        ''' Check first if qbo_customer_id exists in quickbooks or not'''
        if self.x_quickbooks_exported or self.qbo_customer_id:
            from_button = self._context.get('from_button', False)
            ''' Hit request ot quickbooks and check response '''
            if not company:
                company = self.company_id
            if not company:
                company = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_id

            ''' GET ACCESS TOKEN '''

            access_token = None
            realmId = None
            if company.access_token:
                access_token = company.access_token
            if company.id:
                realmId = company.realm_id

            if access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(access_token)
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'

                sql_query = "select Id,SyncToken from customer Where Id = '{}'".format(
                    str(self.qbo_customer_id))

                result = requests.request(
                    'GET', company.url + str(realmId) + "/query?query=" + sql_query, headers=headers)
                if result.status_code == 200:
                    parsed_result = result.json()

                    if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get('Customer'):
                        customer_id_retrieved = parsed_result.get(
                            'QueryResponse').get('Customer')[0].get('Id')
                        if customer_id_retrieved:
                            ''' HIT UPDATE REQUEST '''
                            syncToken = parsed_result.get('QueryResponse').get(
                                'Customer')[0].get('SyncToken')
                            result = self.prepareDictStructure(
                                is_update=True, customer_id_retrieved=customer_id_retrieved, sync_token=syncToken)
                            if result:
                                return result
                            else:
                                return False
                else:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': result.status_code,
                            'odoo_object': 'res.partner',
                            'message': "Failed to query customer in QBO. Status: %s" % result.status_code,
                            'activity': 'Exporting account from Odoo',
                            'created_date': fields.Datetime.now(),
                            # 'company_id': company.id,
                        })
                    else:
                        raise UserError("Failed to query customer in QBO. Status: %s" % result.status_code)

    def updateExistingVendor(self):
        ''' Check first if qbo_customer_id exists in quickbooks or not'''
        if self.x_quickbooks_exported or self.qbo_vendor_id:
            ''' Hit request ot quickbooks and check response '''
            company = self.env['res.users'].search(
                [('id', '=', self._uid)]).company_id
            if not company:
                company = self.env.company

            ''' GET ACCESS TOKEN '''

            access_token = None
            realmId = None
            if company.access_token:
                access_token = company.access_token
            if company.id:
                realmId = company.realm_id

            if access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(access_token)
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'

                sql_query = "select Id,SyncToken from vendor Where Id = '{}'".format(
                    str(self.qbo_vendor_id))

                result = requests.request(
                    'GET', company.url + str(realmId) + "/query?query=" + sql_query, headers=headers)
                if result.status_code == 200:
                    parsed_result = result.json()

                    if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get('Vendor'):
                        vendor_id_retrieved = parsed_result.get(
                            'QueryResponse').get('Vendor')[0].get('Id')
                        if vendor_id_retrieved:
                            ''' HIT UPDATE REQUEST '''
                            syncToken = parsed_result.get('QueryResponse').get(
                                'Vendor')[0].get('SyncToken')
                            result = self.prepareVendorDictStructure(
                                is_update=True, vendor_id_retrieved=vendor_id_retrieved, sync_token=syncToken)
                            if result:
                                return result
                            else:
                                return False
                else:
                    return False

    def createParentInQuickbooks(self, odoo_partner_object, company):
        ''' This Function Creates a new record in quicbooks and returns its Id
        For attaching with the record of customer which will be created in exportPartner Function'''

        if odoo_partner_object and company:

            result = self.prepareDictStructure(
                odoo_partner_object, record_type="company")
            if result:
                return result
        else:
            return False

    '''STEP 1 : Retrieve All Data from odoo_partner_object to form a dictionary which will be passed
            to Quickbooks'''

    def checkPartnerInQuickbooks(self, odoo_partner_object, company=None):
        ''' Check This Name in Quickbooks '''
        customer_id_retrieved = None
        from_button = self._context.get('from_button', False)
        if not company:
            company = self.company_id
        if not company:
            if from_button:
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': f'{self.name}',
                    'odoo_object': 'res.partner',
                    'message': f'"Set Company for Partner {self.name}"',
                    'activity': 'Exporting Partner from Odoo',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_(f"Set Company for Partner {self.name}"))
        # company = self.env['res.users'].search(
        #     [('id', '=', self._uid)]).company_id
        if company:
            access_token = None
            realmId = None
            if company.access_token:
                access_token = company.access_token
            if company.realm_id:
                realmId = company.realm_id

            if access_token and realmId:
                ''' Hit Quickbooks and Check Availability '''
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(access_token)
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'

                if odoo_partner_object.supplier_rank:
                    sql_vendor_query = "select Id from vendor Where DisplayName = '{}'".format(
                        str(odoo_partner_object.name))
                    vendor_result = requests.request('GET',
                                                     company.url +
                                                     str(realmId) + "/query?query=" +
                                                     sql_vendor_query,
                                                     headers=headers)
                    if vendor_result.status_code == 200:
                        parsed_result = vendor_result.json()
                        if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get('Vendor'):
                            vendor_id_retrieved = parsed_result.get(
                                'QueryResponse').get('Vendor')[0].get('Id')
                            if vendor_id_retrieved:
                                return vendor_id_retrieved

                sql_query = "select Id from customer Where DisplayName = '{}'".format(
                    str(odoo_partner_object.name))

                result = requests.request('GET', company.url + str(realmId) + "/query?query=" + sql_query,
                                          headers=headers)

                if result.status_code == 200:
                    parsed_result = result.json()

                    if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get('Customer'):
                        customer_id_retrieved = parsed_result.get(
                            'QueryResponse').get('Customer')[0].get('Id')
                        if customer_id_retrieved:
                            return customer_id_retrieved
                    if not parsed_result.get('QueryResponse').get('Customer'):
                        sql_query = "select Id from vendor Where DisplayName = '{}'".format(
                            str(odoo_partner_object.name))

                        result = requests.request('GET', company.url + str(realmId) + "/query?query=" + sql_query,
                                                  headers=headers)
                        if result.status_code == 200:
                            parsed_result = result.json()
                            if parsed_result.get('QueryResponse').get('Vendor'):
                                if from_button:
                                    self.env['qbo.logger'].sudo().create({
                                        'odoo_name': f'{odoo_partner_object.name}',
                                        'odoo_object': 'res.partner',
                                        'message': f'"Vendor Name Already Exist For Name:  {odoo_partner_object.name}"',
                                        'activity': 'Exporting Partner from Odoo',
                                        'created_date': fields.Datetime.now(),
                                    })
                                else:
                                    raise ValidationError(_(f"Vendor Name Already Exist For Name:  {odoo_partner_object.name}"))
                        new_quickbooks_parent_id = self.createParentInQuickbooks(
                            odoo_partner_object, company)
                        if new_quickbooks_parent_id:
                            if odoo_partner_object.customer_rank:
                                odoo_partner_object.qbo_customer_id = new_quickbooks_parent_id
                            if odoo_partner_object.supplier_rank:
                                odoo_partner_object.qbo_vendor_id = new_quickbooks_parent_id
                            odoo_partner_object.x_quickbooks_exported = True

                            return new_quickbooks_parent_id
                        else:
                            _logger.info(
                                "Inside Else of new_quickbooks_parent_id !!!!!!!!!!!!!!")

                        return False
                else:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': 'Error',
                            'odoo_object': 'res.partner',
                            'message': "Error Occured In Partner Search Request" + result.text,
                            'activity': 'Exporting Partner from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise UserError(
                            "Error Occured In Partner Search Request" + result.text)
                return False
        else:
            _logger.info("Didnt Got QUickbooks Config !!!!!!!!!!!!!!")

    @api.model
    def exportCustomer(self, company=None):
        from_button = self._context.get('from_button', False)
        try:
            if not company:
                company = self.company_id
            if not company:
                if from_button:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': f'{self.name}',
                        'odoo_object': 'res.partner',
                        'message': f'"Please Set Company for Partner":  {self.name}',
                        'activity': 'Exporting Partner from Odoo',
                        'created_date': fields.Datetime.now(),
                    })
                else:
                    raise ValidationError(_(f'Please Set Company for Partner {self.name}'))
            if not company:
                company = self.env['res.users'].search(
                    [('id', '=', self._uid)]).company_id
                if not company:
                    company = self.env.company
            if self.x_quickbooks_exported or self.qbo_customer_id:
                # if self.qbo_customer_id:
                '''  If Customer Already Exported to quickbooks then hit update request '''

                # STEP 1 : GET ID FROM QUICKBOOKS USING GET REQUEST QUERY TO
                # QUICKBOOKS

                update_customer = company.update_customer_export
                # update_customer = self.env['ir.config_parameter'].sudo().get_param('pragmatic_quickbooks_connector_canada.update_customer_export')
                if update_customer:
                    result = self.updateExistingCustomer(company=company)
                    if result:
                        _logger.info("Customer Update was successful !")
                        # raise UserError("Update was successful !")
                    else:
                        _logger.info("Customer Update was not successful !")
                        # raise UserError("Update unsuccessful :(")
                else:
                    _logger.info(
                        "Your not allowed to update any customers while exporting. !")
            else:
                #             raise UserError("Customer Already Exported To Quickbooks")
                #             return False
                ''' Checking if parent_id is assigned or not if not then first read that parent_id and check in
                Quickbooks if present if present then make sub customer else first create that company in Quickbooks and
                attach its reference.
                '''
                if self.parent_id:
                    ''' Check self.parent_id.name in Quickbooks '''
                    customer_id_retrieved = self.checkPartnerInQuickbooks(
                        self.parent_id, company=company)

                    if customer_id_retrieved:
                        result = self.prepareDictStructure(record_type="indv_company",
                                                        customer_id_retrieved=customer_id_retrieved)
                        if result:
                            self.qbo_customer_id = result
                            self.x_quickbooks_exported = True
                            self._cr.commit()
                    else:
                        if from_button:
                            self.env['qbo.logger'].sudo().create({
                                'odoo_name': "Customer ID",
                                'odoo_object': 'res.partner',
                                'message': "Customer ID was not retrieved",
                                'activity': 'Exporting account from Odoo',
                                'created_date': fields.Datetime.now(),
                                # 'company_id': company.id,
                            })
                        else:
                            raise UserError("Customer ID was not retrieved")

                if not self.parent_id:
                    result = self.prepareDictStructure(record_type="individual")
                    # _logger.info('\n\n000000000000 : {}'.format(result))
                    if result:
                        self.qbo_customer_id = result
                        self.x_quickbooks_exported = True
                        self._cr.commit()
        except Exception as e:
            if from_button:
                _logger.warning(str(e))
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Error Occured',
                    'odoo_object': 'res.partner',
                    'message': str(e),
                    'activity': 'Exporting Customer (Exception)',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_('Error : %s' % e))

    @api.model
    def exportVendor(self, cron=None, company=None):
        from_button = self._context.get('from_button', False)
        try:
            if self.x_quickbooks_exported or self.qbo_vendor_id:
                '''  If Customer Already Exported to quickbooks then hit update request '''
                if not company:
                    company = self.company_id
                if not company:
                    if from_button:
                        self.env['qbo.logger'].sudo().create({
                            'odoo_name': f'{self.name}',
                            'odoo_object': 'res.partner',
                            'message': f'"Please Set Company for Partner":  {self.name}',
                            'activity': 'Exporting Partner from Odoo',
                            'created_date': fields.Datetime.now(),
                        })
                    else:
                        raise ValidationError(_(f"Set Company for Partner {self.name}"))
                if not company:
                    company = self.env.company
                update_vendor = company.update_vendor_export

                if update_vendor:
                    result = self.updateExistingVendor()
                    if result:
                        _logger.info("Update was successful !")
                        # raise UserError("Update was successful !")
                    else:
                        _logger.info("Update was not successful !")
                        # raise UserError("Update unsuccessful :(")
                else:
                    _logger.info(
                        "Your not allowed to update any vendors while exporting.")
            else:


                ''' Checking if parent_id is assigned or not if not then first read that parent_id and check in 
                Quickbooks if present if present then make sub customer else first create that company in Quickbooks and 
                attach its reference.
                '''
                if self.parent_id:
                    ''' Check self.parent_id.name in Quickbooks '''
                    customer_id_retrieved = self.checkPartnerInQuickbooks(
                        self.parent_id)
                    if customer_id_retrieved:
                        result = self.prepareVendorDictStructure(record_type="indv_company",
                                                                vendor_id_retrieved=customer_id_retrieved)
                        if result:
                            self.qbo_vendor_id = result
                            self.x_quickbooks_exported = True
                            self._cr.commit()
                    else:
                        _logger.info("Customer ID was not retrieved")

                if not self.parent_id:
                    result = self.prepareVendorDictStructure(
                        record_type="individual")
                    if result:
                        self.qbo_vendor_id = result
                        self.x_quickbooks_exported = True
                        self._cr.commit()
        except Exception as e:
            if from_button:
                _logger.warning(str(e))
                self.env['qbo.logger'].sudo().create({
                    'odoo_name': 'Error Occured',
                    'odoo_object': 'res.partner',
                    'message': str(e),
                    'activity': 'Exporting Vendor (Exception)',
                    'created_date': fields.Datetime.now(),
                })
            else:
                raise ValidationError(_('Error : %s' % e))
            
    # @api.multi
    def export_single_Partner(self, partner):

        if partner.customer_rank:
            partner.exportCustomer()
        elif partner.supplier_rank == 1:
            partner.exportVendor()


    @api.model
    def exportPartner(self):

        from_button = self._context.get('from_button', False)

        if len(self) > 1:
            for customer in self:
                if customer.type == 'contact':
                    if customer.customer_rank:
                        customer.exportCustomer()
                    elif customer.supplier_rank:
                        customer.exportVendor()


        else:
            if self.type == 'contact':
                if self.customer_rank:
                    if self.env.company.partner_individual_records:
                        if self.company_type == 'company':
                            self.exportCustomer()
                        else:
                            if from_button:
                                self.env['qbo.logger'].sudo().create({
                                    'odoo_name': 'Individual Record Error',
                                    'odoo_object': 'res.partner',
                                    'message': f"According To The Settings, You Can't Export Individual Record",
                                    'activity': 'Exporting Partner from Odoo',
                                    'created_date': fields.Datetime.now(),
                                })
                            else:
                                raise ValidationError(f"According To The Settings, You Can't Export Individual Record")

                    else:
                        self.exportCustomer()
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
                elif self.supplier_rank:
                    self.exportVendor()
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
