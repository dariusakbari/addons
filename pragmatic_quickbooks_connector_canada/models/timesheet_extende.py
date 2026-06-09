import base64
import json
import logging
from datetime import datetime, time, timedelta

import pytz
import requests
import xmltodict
from xmltodict import ParsingInterrupted

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)





class TimesheetExtended(models.Model):
    _inherit = "account.analytic.line"

    qbo_timeactivity_id = fields.Char("QBO Timesheet Id", copy=False, help="QuickBooks database recordset id")
    billable_status = fields.Selection([
        ('billable', 'Billable'),
        ('non_billable', 'Non-Billable'),
    ], string="Billable Status")

    @api.model
    def create_timesheet(self, data, company):
        """Import Timesheet from QBO, param data: Timesheet object response return by QBO, return Timesheet Timesheet object"""
        _logger.info(_('Inside Create Timesheet<------xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx0---->'))
        res = json.loads(str(data.text))
        if 'QueryResponse' in res:
            Payments = res.get('QueryResponse').get('TimeActivity', [])
        else:
            Payments = [res.get('TimeActivity')] or []
        _logger.info(_('Inside Create Timesheet<------xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx111----> %s' % Payments))
        if len(Payments) == 0:
            raise UserError("It seems that all of the Timesheet are already imported.")
        max_result = res.get('QueryResponse').get('maxResults')
        try:
            if not company:
                company = self.env.company
            for payment in Payments:
                exist_deposit = self.env['account.analytic.line'].search(
                    [('qbo_timeactivity_id', '=', payment.get("Id")), ('company_id', '=', company.id)], limit=1)
                if not exist_deposit:
                    dict_deposit = {}

                    if payment.get('TxnDate'):
                        dict_deposit['date'] = payment.get('TxnDate')
                        dict_deposit['qbo_timeactivity_id'] = payment.get('Id')
                        dict_deposit['company_id'] = company.id
                    if company.default_project_id:
                        dict_deposit['project_id'] = company.default_project_id.id
                    else:
                        raise ValidationError(
                            f"Add Default Project In QB ACCOUNT Configuration")
                    # if payment.get('ProjectRef'):
                    #     project_id = self.env['project.project'].search(
                    #         [('quickbook_id', '=', payment.get('ProjectRef').get('value'))], limit=1)
                    #     if project_id:
                    #         # dict_deposit['employee_id'] = employee.id
                    #         dict_deposit['project_id'] = project_id.id  # for testing
                    #     else:
                    #         raise ValidationError(
                    #             f"Project Not Found On Odoo  QBO ID {payment.get('ProjectRef').get('value')}")
                    # else:
                    #     if company.default_project_id:
                    #         dict_deposit['project_id'] = company.default_project_id.id
                    #     else:
                    #         raise ValidationError(
                    #             f"Add Default Project In QB ACCOUNT Configuration")

                    if payment.get('NameOf'):
                        dict_deposit[
                            'name'] = f"{payment.get('NameOf')} Timesheet [{payment.get('Description') if payment.get('Description') else ''}]"
                    if payment.get('EmployeeRef') and payment.get('EmployeeRef').get('value'):
                        employee = self.env['hr.employee'].search(
                            [('quickbook_id', '=', payment.get('EmployeeRef').get('value'))], limit=1)
                        if employee:
                            dict_deposit['employee_id'] = employee.id
                            # dict_deposit['employee_id'] = 1  # for testing
                        else:
                            raise ValidationError(
                                f"Employee Not Found On Odoo  QBO ID {payment.get('EmployeeRef').get('value')}")

                    if payment.get('CustomerRef') and payment.get('CustomerRef').get('value'):
                        partner = self.env['res.partner'].search(
                            [('qbo_customer_id', '=', payment.get('CustomerRef').get('value'))], limit=1)
                        if partner:
                            dict_deposit['partner_id'] = partner.id
                        else:
                            raise ValidationError(
                                f"Customer Not Found On Odoo  QBO ID {payment.get('CustomerRef').get('value')}")

                    # if payment.get('ItemRef') and payment.get('ItemRef').get('value'):
                    #     product = self.env['product.product'].search(
                    #         [('qbo_product_id', '=', payment.get('ItemRef').get('value'))], limit=1)
                    #     if product:
                    #         dict_deposit['product_id'] = product.id
                    #     else:
                    #         raise ValidationError(
                    #             f"product Not Found On Odoo  QBO ID {payment.get('CustomerRef').get('value')}")
                    if payment.get('BillableStatus'):
                        bill_status = 'non_billable' if payment.get('BillableStatus') == 'NotBillable' else 'billable'
                        dict_deposit['billable_status'] = bill_status
                    hours = payment.get("Hours")
                    minutes = payment.get("Minutes")
                    time = 0.0

                    if hours is not None or minutes is not None:
                        h = float(hours or 0)
                        m = float(minutes or 0)
                        time = h + m / 60
                    elif payment.get("StartTime") and payment.get("EndTime"):
                        start = datetime.fromisoformat(payment["StartTime"])
                        end = datetime.fromisoformat(payment["EndTime"])
                        time = (end - start).total_seconds() / 3600
                    dict_deposit["unit_amount"] = time

                    self.env['account.analytic.line'].create(dict_deposit)
                    self.env.cr.commit()
            return max_result
        except Exception as e:
            raise ValidationError(_('Error : %s' % e))

    @api.model
    def export_timesheet_to_qbo(self, cron=None, company=None):
        from_button = self._context.get('from_button', False)
        if not company:
            company = self.env.company
        access_token = None
        realmId = None
        for timesheet_id in self:
            if not company:
                company = self.company_id
            if not company:
                if from_button:
                    self.env['qbo.logger'].sudo().create({
                        'odoo_name': f'{self.name}',
                        'odoo_object': 'account.analytic.line(Timesheet)',
                        'message': f"Set Company for Timesheet {self.name}",
                        'activity': 'Exporting Timesheet from Odoo',
                        'created_date': fields.Datetime.now(), })
                else:
                    raise ValidationError(_(f"Set Company for Timesheet {self.name}"))
            if not company:
                company = self.env.company
            timesheet_name = timesheet_id.name

            # TxnDate (timesheet date)
            vals = {}
            if timesheet_id.date:
                vals.update({"TxnDate": timesheet_id.date.isoformat()})

            # Description (timesheet name)
            if timesheet_id.name:
                vals.update({"Description": timesheet_id.name})

            # Hours (unit amount)
            if timesheet_id.unit_amount:
                hours = int(timesheet_id.unit_amount)
                minutes = int(round((timesheet_id.unit_amount - hours) * 60))
                vals.update({
                    "Hours": hours,
                    "Minutes": minutes
                })

            # HourlyRate (custom field on employee)
            # if timesheet_id.employee_id and timesheet_id.employee_id.hourly_rate:
            #     vals.update({"HourlyRate": timesheet_id.employee_id.hourly_rate})

            # EmployeeRef (QBO ID and name)
            if timesheet_id.employee_id:
                if timesheet_id.employee_id.quickbook_id:
                    vals.update({
                        "EmployeeRef": {
                            "value": timesheet_id.employee_id.quickbook_id,
                            "name": timesheet_id.employee_id.name
                        }
                    })
                else:
                    raise ValidationError(_(f"Employee is not sync with QBO {timesheet_id.employee_id.name}"))

            # CustomerRef (related partner if project is linked)
            if timesheet_id.partner_id:
                if timesheet_id.partner_id.qbo_customer_id:
                    vals.update({
                        "CustomerRef": {
                            "value": timesheet_id.partner_id.qbo_customer_id,
                            "name": timesheet_id.partner_id.name
                        }
                    })
                else:
                    raise ValidationError(_(f"Customer is not sync with QBO {timesheet_id.partner_id.name}"))
                # if timesheet_id.project_id.partner_id.qbo_customer_id:
                #     vals.update({
                #         "CustomerRef": {
                #             "value": timesheet_id.partner_id.qbo_customer_id,
                #             "name": timesheet_id.partner_id.name
                #         }
                #     })
                # else:
                #     raise ValidationError(_(f"Customer is not sync with QBO {timesheet_id.partner_id.name}"))
            # ProjectRef (custom QBO Project/Job ID)
            # if timesheet_id.project_id and timesheet_id.project_id.quickbook_id:
            #     vals.update({
            #         "ProjectRef": {
            #             "value": timesheet_id.project_id.quickbook_id
            #         }
            #     })

            if timesheet_id.billable_status:
                bill_status = 'NotBillable' if timesheet_id.billable_status == 'non_billable' else 'Billable'
                vals.update({"BillableStatus": bill_status})

            vals.update({"NameOf": "Employee"})
            if company.access_token:
                access_token = company.access_token
            if company.realm_id:
                realmId = company.realm_id
            result = False
            if access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(access_token)
                headers['Content-Type'] = 'application/json'
                headers['accept'] = 'application/json'
                parsed_dict = json.dumps(vals)
                _logger.info('Parsed Dict for create Timesheet : {}'.format(parsed_dict))
                result = requests.request('POST', company.url + str(realmId) + "/timeactivity?minorversion=75",
                                          headers=headers, data=parsed_dict)
                if result.status_code == 200:
                    resp_parsed = json.loads(result.text)
                    if resp_parsed.get('TimeActivity').get('Id'):
                        timesheet_id.qbo_timeactivity_id = resp_parsed.get('TimeActivity').get('Id')
                        _logger.info(_("Timesheet exported sucessfully! product template Id: %s" % (
                            timesheet_id.qbo_timeactivity_id)))
                        self._cr.commit()
                else:
                    raise ValidationError(_(f"Export issue On timesheet{result.status_code}{result.text}"))


class ProjectExtended(models.Model):
    _inherit = "project.project"

    quickbook_id = fields.Char(string="QuickBooks Id", copy=False)

    @api.model
    def create_project(self, data, company=None):
        """Create partner object in odoo, param data: partner object response return by QBO, is_customer: True if partner is a customer, is_vendor: True if partener is a supplier/vendor, return int: last import QBO customer or vendor Id"""
        res = json.loads(str(data.text))
        try:
            if 'QueryResponse' in res:
                partners = res.get('QueryResponse').get('Customer', [])
            else:
                partners = [res.get('Customer')] or []

            if len(partners) == 0:
                raise UserError("It seems that all of the Project are already imported.")
            max_result = res.get('QueryResponse').get('maxResults')
            if not company:
                company = self.env.company
            for partner in partners:
                try:
                    if partner.get('IsProject'):
                        qbo_id = partner.get('Id', 'Unknown ID')

                        brw_partner = self.search(
                            [('quickbook_id', '=', partner.get('Id')),
                             ('company_id', '=', company.id)], limit=1)
                        vals = {}
                        if partner.get('ParentRef'):
                            partner_ref = self.env['res.partner'].search(
                                [('qbo_customer_id', '=', partner.get('ParentRef').get('value')),
                                 ('company_id', '=', company.id)], limit=1)
                            if partner_ref:
                                vals.update({'partner_id': partner_ref.id})
                            else:
                                raise ValidationError(
                                    f"Project Partner not fount in odoo QBO ID{partner.get('ParentRef').get('value')}")
                        vals.update({'name': partner.get('DisplayName'), 'quickbook_id': partner.get('Id')})

                        if company:
                            vals.update({'company_id': company.id})
                        _logger.info(
                            "\n\n--- QBO Project Data ---\nPartner Dict: %s\nVals for Project Creation: %s\n-----------------\n",
                            partner, vals)
                        _logger.info("Browsing Project************ {}".format(brw_partner))
                        if not brw_partner:
                            _logger.info("Project needs to be created----------------{}".format(vals))
                            brw_partner = self.create(vals)
                            _logger.info(_("Project created sucessfully! Partner Id: %s" % (brw_partner.id)))
                except ValidationError:
                    raise
                except Exception as e:
                    raise ValidationError("Error processing QBO Project with ID {}: {}".format(qbo_id, str(e)))
            return max_result
        except (UserError, ValidationError):
            raise
        except Exception as e:
            raise ValidationError("Unexpected error while processing Project: {}".format(str(e)))


