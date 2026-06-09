from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
# from openerp.exceptions import UserError, ValidationError
import requests
import json
import logging
import datetime

_logger = logging.getLogger(__name__)


class Dept(models.Model):
    _inherit = "hr.department"

    @api.model
    def _prepare_dept_export_dict(self):
        vals = {}
        if self.name:
            vals.update({
                'Name': self.name,
            })
        if self.parent_id:
            vals.update({
                'ParentRef': {
                    'value': self.env['hr.department'].get_qbo_dept_ref(self.parent_id)
                }
            })
        return vals

    @api.model
    def exportDepartment(self):
        """export departments to QBO"""

        # Get QuickBooks configuration for the current company
        quickbook_config = self.env['res.users'].search([('id', '=', self._uid)]).company_id
        access_token = quickbook_config.access_token
        realmId = quickbook_config.realm_id

        # Check if active departments are passed via context or not
        if self._context.get('active_ids'):
            departments = self.browse(self._context.get('active_ids'))
        else:
            departments = self

        # Initialize a list to track failed exports
        failed_departments = []

        # Process each department for export
        for dept in departments:
            try:
                vals = dept._prepare_dept_export_dict()
                parsed_dict = json.dumps(vals)

                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                }

                # If department already has a QuickBooks ID, perform an update
                if dept.quickbook_id:
                    result = requests.request('POST', f'{quickbook_config.url}{realmId}/department?operation=update',
                                              headers=headers, data=parsed_dict)

                    if result.status_code == 200:
                        response = quickbook_config.convert_xmltodict(result.text)
                        # Update QuickBooks department ID
                        dept.quickbook_id = response.get('IntuitResponse').get('Department').get('Id')
                        self._cr.commit()
                        _logger.info(f"Department '{dept.name}' exported successfully to QBO.")
                    else:
                        # If no changes, log info
                        _logger.info(f"No changes in Department '{dept.name}'.")

                else:
                    # If department does not have a QuickBooks ID, create a new department
                    result = requests.request('POST', f'{quickbook_config.url}{realmId}/department',
                                              headers=headers, data=parsed_dict)

                    if result.status_code == 200:
                        response = quickbook_config.convert_xmltodict(result.text)
                        # Update QuickBooks department ID
                        dept.quickbook_id = response.get('IntuitResponse').get('Department').get('Id')
                        self._cr.commit()
                        _logger.info(f"Department '{dept.name}' exported successfully to QBO.")
                    else:
                        # Log error if failed to export
                        _logger.error(
                            f"Failed to export Department '{dept.name}': {result.status_code} - {result.text}")
                        failed_departments.append(f"{dept.name}: {result.status_code} - {result.text}")

            except Exception as e:
                # Log any unexpected errors and add to failed departments
                _logger.error(f"Error exporting Department '{dept.name}': {str(e)}")
                failed_departments.append(f"{dept.name}: {str(e)}")

        # If any departments failed, raise a validation error with the details
        if failed_departments:
            failed_departments_msg = "\n".join(failed_departments)
            raise ValidationError(f"The following departments failed to export:\n{failed_departments_msg}")

        # If all departments exported successfully, show success notification
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

    # def exportDepartment(self):
    #     """export account invoice to QBO"""
    #     quickbook_config = self.env['res.users'].search(
    #         [('id', '=', self._uid)]).company_id
    #     access_token = None
    #     realmId = None
    #     if quickbook_config.access_token:
    #         access_token = quickbook_config.access_token
    #     if quickbook_config.realm_id:
    #         realmId = quickbook_config.realm_id
    #
    #     if self._context.get('active_ids'):
    #         dept = self.browse(self._context.get('active_ids'))
    #     else:
    #         dept = self
    #
    #     for d in dept:
    #         if d.quickbook_id:
    #             vals = d._prepare_dept_export_dict()
    #             parsed_dict = json.dumps(vals)
    #             if access_token:
    #                 headers = {}
    #                 headers['Authorization'] = 'Bearer ' + str(access_token)
    #                 headers['Content-Type'] = 'application/json'
    #                 result = requests.request('POST', quickbook_config.url + str(realmId) + "/department?operation=update",
    #                                           headers=headers, data=parsed_dict)
    #                 if result.status_code == 200:
    #                     response = quickbook_config.convert_xmltodict(
    #                         result.text)
    #                     # update QBO invoice id
    #                     if d.name:
    #                         d.quickbook_id = response.get(
    #                             'IntuitResponse').get('Department').get('Id')
    #                         self._cr.commit()
    #                     _logger.info(_("exported successfully to QBO"))
    #                 #                         return True
    #                 else:
    #                     _logger.info(_("NO CHANGES IN DEPT"))
    #
    #         else:
    #             vals = d._prepare_dept_export_dict()
    #             parsed_dict = json.dumps(vals)
    #             if access_token:
    #                 headers = {}
    #                 headers['Authorization'] = 'Bearer ' + str(access_token)
    #                 headers['Content-Type'] = 'application/json'
    #
    #                 result = requests.request('POST', quickbook_config.url + str(realmId) + "/department",
    #                                           headers=headers, data=parsed_dict)
    #
    #                 if result.status_code == 200:
    #                     response = quickbook_config.convert_xmltodict(
    #                         result.text)
    #                     # update QBO invoice id
    #                     if d.name:
    #                         d.quickbook_id = response.get(
    #                             'IntuitResponse').get('Department').get('Id')
    #                         self._cr.commit()
    #                     _logger.info(_("exported successfully to QBO"))
    #                     success_form = self.env.ref(
    #                         'pragmatic_quickbooks_connector_canada.export_successfull_view', False)
    #                     return {
    #                         'name': _('Notification'),
    #                         'type': 'ir.actions.act_window',
    #                         'view_type': 'form',
    #                         'view_mode': 'form',
    #                         'res_model': 'res.company.message',
    #                         'views': [(success_form.id, 'form')],
    #                         'view_id': success_form.id,
    #                         'target': 'new',
    #                     }
    #                 #                         return True
    #                 else:
    #                     _logger.error(
    #                         _("[%s] %s" % (result.status_code, result.reason)))
    #                     raise ValidationError(
    #                         _("[%s] %s %s" % (result.status_code, result.reason, result.text)))
