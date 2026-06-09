from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
# from openerp.exceptions import UserError, ValidationError
import requests
import json
import logging
import datetime

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = "hr.employee"

    def getSyncToken(self, qbo_id):
        '''
        :param: Employee ID of quickbooks
        :return: Sync Token if found else False
        '''
        access_token_obj = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id

        access_token = None
        realmId = None

        if access_token_obj.access_token:
            access_token = access_token_obj.access_token

        if access_token_obj.realm_id:
            realmId = access_token_obj.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

            sql_query = "select Id,SyncToken from employee Where Id = '{}'".format(
                str(qbo_id))

            result = requests.request('GET', access_token_obj.url + str(realmId) + "/query?query=" + sql_query,
                                      headers=headers)
            if result.status_code == 200:
                parsed_result = result.json()

                if parsed_result.get('QueryResponse') and parsed_result.get('QueryResponse').get('Employee'):
                    synctoken_id_retrieved = parsed_result.get(
                        'QueryResponse').get('Employee')[0].get('Id')
                    if synctoken_id_retrieved:
                        ''' HIT UPDATE REQUEST '''
                        syncToken = parsed_result.get('QueryResponse').get(
                            'Employee')[0].get('SyncToken')

                        if syncToken:
                            return syncToken
                        else:
                            return False

    def createEmployee(self):
        ''' This Function Exports Record to Quickbooks '''
        ''' STEP 3 '''

        ''' GET ACCESS TOKEN FROM RES COMPANY'''
        access_token_obj = self.env['res.users'].search(
            [('id', '=', self._uid)]).company_id

        access_token = None
        realmId = None

        if access_token_obj.access_token:
            access_token = access_token_obj.access_token

        if access_token_obj.realm_id:
            realmId = access_token_obj.realm_id

        if access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

        dict = {}
        dict_phone = {}
        dict_email = {}
        dict_work_phone = {}
        dict_addr = {}
        dict_birth = {}
        dict_eno = {}
        dict_gender = {}
        dict_id = {}
        dict_hired = {}
        dict_released = {}

        if self.work_phone:
            dict_work_phone['Mobile'] = {
                'FreeFormNumber': str(self.work_phone)}


        if self.quickbook_id:
            dict["Id"] = self.quickbook_id
            dict['sparse'] = "true"

        if self.ssn:
            dict["SSN"] = str(self.ssn)

        if self.billing_rate:
            dict["BillRate"] = str(self.billing_rate)

        if self.sync_id:
            dict["SyncToken"] = str(self.sync_id)

        if self.employee_no:
            dict_id["EmployeeNumber"] = str(self.employee_no)

        if self.name:
            full_name = str(self.name)
            if len(full_name.split()) == 1:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = "NA"
                dict["FamilyName"] = "NA"
            if len(full_name.split()) == 2:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = " "
                dict["FamilyName"] = full_name.split()[1]

            if len(full_name.split()) == 3:
                dict["GivenName"] = full_name.split()[0]
                dict["MiddleName"] = full_name.split()[1]
                dict["FamilyName"] = full_name.split()[2]

            dict['DisplayName'] = str(self.name)
            dict['PrintOnCheckName'] = str(self.name)


        if self.birthday:
            dict_birth["BirthDate"] = self.birthday.strftime('%Y-%m-%d')

        if self.released_date:
            dict_released["ReleasedDate"] = str(self.released_date)

        if self.hired_date:
            dict_hired["HiredDate"] = str(self.hired_date)

        if self.work_email:
            dict_email["PrimaryEmailAddr"] = {'Address': str(self.work_email)}

        if self.mobile_phone:
            dict_phone["PrimaryPhone"] = {
                'FreeFormNumber': str(self.mobile_phone)}

        res_partner = self.env['res.partner'].search(
            [('id', '=', self.address_id.id)], limit=1)


        if self.address_id:
            dict_addr['PrimaryAddr'] = {'Line1': (res_partner.street or ""), 'Line2': (res_partner.street2 or ""),
                                        'City': (res_partner.city or ""),
                                        'Country': (res_partner.country_id.name or ""),
                                        'CountrySubDivisionCode': (res_partner.state_id.name or ""),
                                        'PostalCode': (res_partner.zip or "")}



        dict.update(dict_email)
        dict.update(dict_id)
        dict.update(dict_gender)
        dict.update(dict_work_phone)
        dict.update(dict_phone)
        dict.update(dict_eno)
        dict.update(dict_birth)
        dict.update(dict_hired)
        dict.update(dict_released)
        dict.update(dict_addr)

        if self.quickbook_id:

            dict["SyncToken"] = str(self.sync_id)

            res = self.getSyncToken(self.quickbook_id)
            if res:
                dict["SyncToken"] = str(res)

                parsed_dict = json.dumps(dict)
                result_data = requests.request('POST',
                                               access_token_obj.url +
                                               str(realmId) +
                                               "/employee?operation=update",
                                               headers=headers, data=parsed_dict)
                if result_data.status_code == 200:
                    parsed_result = result_data.json()
                    if parsed_result.get('Employee').get('Id'):
                        return parsed_result.get('Employee').get('Id')
                    else:
                        return False
                else:
                    raise UserError(
                        "Error Occured While Updating" + result_data.text)
        else:
            parsed_dict = json.dumps(dict)
            result_data = requests.request('POST', access_token_obj.url + str(realmId) + "/employee", headers=headers,
                                           data=parsed_dict)
            if result_data.status_code == 200:
                parsed_result = result_data.json()
                if parsed_result.get('Employee').get('Id'):
                    dict_c = {}
                    if parsed_result.get('Employee').get('Id'):
                        dict_c['quickbook_id'] = parsed_result.get(
                            'Employee').get('Id')

                    if parsed_result.get('Employee').get('SyncToken'):
                        dict_c['sync_id'] = parsed_result.get(
                            'Employee').get('SyncToken')
                    return dict_c['quickbook_id']
                    # return parsed_result.get('Employee').get('Id')
                else:
                    return False

            elif result_data.status_code == 400:
                error_message = result_data.text
                try:
                    error_data = json.loads(error_message)
                    error_detail = error_data.get('Fault', {}).get('Error', [{}])[0].get('Detail', '')
                    error_id = error_detail.split('=')[1].split(',')[0]
                except Exception as e:
                    _logger.info(f"An unexpected error occurred:{e}")
                if error_id:
                    data = requests.request('GET', access_token_obj.url + str(
                        access_token_obj.realm_id) + "/query?query=select * from employee where Id = '{}'".format(
                        str(error_id)), headers=headers)
                    if data.status_code == 200:
                        emp_name = False
                        response = data.text
                        try:
                            data = json.loads(response)
                            _logger.info(f"Duplicate Employee LOG -----{data}")
                            if 'QueryResponse' in data and 'Employee' in data['QueryResponse']:
                                emp_name = data['QueryResponse']['Employee'][0]['DisplayName']
                        except json.JSONDecodeError as e:
                            _logger.info(f"Error decoding JSON: {e}")
                        emp_name = emp_name if emp_name else error_id
                        if emp_name:
                            raise ValidationError(
                                f"Duplicate Name - [{emp_name}] is already exist in quickbook "
                            )
                        elif error_id:
                            raise ValidationError(
                                f"[Duplicate Name]  Customer QBO ID - [{error_id}] is already exist with same name in quickbook "
                            )
            else:
                raise UserError(
                    "Error Occured While Exporting" + result_data.text)

    @api.model
    def exportEmployee(self):
        ''' This Function call the function that Exports Record to Quickbooks and updates quickbook_id'''
        ''' STEP 2 '''

        result = self.createEmployee()
        if result:
            self.write({
                'quickbook_id': int(result)
            })
        else:
            raise UserError("Oops Some error occured.")
            # raise UserError("Creation was successful !")

    @api.model
    def export_Employees_to_qbo(self):
        '''First function that is called from Export to QB action button'''
        ''' STEP 1 '''

        if len(self) > 1:
            '''For more then one employees'''
            for i in self:
                i.exportEmployee()
        else:
            '''For only one employee'''
            self.exportEmployee()
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
