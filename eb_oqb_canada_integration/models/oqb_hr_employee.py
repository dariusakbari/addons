# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class HrEmployeeInherit(models.Model):
    """
       Description:
           This class inherits the 'res.partner' model and adds additional functionality for fetching
           account data from quickbook and updating records in Odoo.

       Methods:
           fetch_account_from_quickbook(instance_id, last_sync_date):
               Fetches account data from quickbook and updates records in Odoo.

       """
    _inherit = 'hr.employee'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    odoo_hash = fields.Char(string='Odoo hash')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    instance_name = fields.Char(string='Instance Name')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

    @api.onchange('first_name', 'last_name')
    def _onchange_first_last_name(self):
        """
            Updates the 'name' field whenever 'first_name' or 'last_name' fields are changed.

            This method concatenates the 'first_name' and 'last_name' fields, ensuring that
            any None values are filtered out, and sets the result to the 'name' field of the partner.

            Example:
                If 'first_name' is "John" and 'last_name' is "Doe", the 'name' field will be "John Doe".
        """
        for partner in self:
            partner.name = ' '.join(filter(None, [partner.first_name, partner.last_name]))

    def fetch_employee_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches Employee data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_employee_data_from_quickbook(current_instance, last_sync_date, False,
        'oqb.employee.lines','quickbook_employee_dropdown_mapping',
        'Employee','employee', operation_type)

        # --------------------------------- Sync Company and Contact Record Quickbook To Odoo ------------------------------- #

    def fetch_employee_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(
            current_instance=current_instance,last_sync_date_field=last_sync_date_field,
            is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_quickbook_employee_record',
            sync_date_field='quickbook_employee_last_sync_date',last_id_field='quickbook_employee_last_id')

    def fetch_employee_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_employee_sync_to_quickbook(current_instance, last_sync_date, 'hr.employee', 'None',
                                                  'oqb.employee.lines', 'odoo_employee_dropdown_mapping',
                                                  'Employee', 'employee', operation_type)

    def odoo_employee_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_employee_record',sync_date_field='odoo_employee_last_sync_date',
            last_id_field='odoo_employee_last_id')

    # -------------------- Sync Form and List View Odoo Partner Record to Quickbook ------------------- #

    def employee_record_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook('employee', active_ids, 'hr.employee', 'Employee')
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)


class HrDepartmentInherit(models.Model):
    """
       Description:
           This class inherits the 'res.partner' model and adds additional functionality for fetching
           account data from quickbook and updating records in Odoo.

       Methods:
           fetch_account_from_quickbook(instance_id, last_sync_date):
               Fetches account data from quickbook and updates records in Odoo.

       """
    _inherit = 'hr.department'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    odoo_hash = fields.Char(string='Odoo hash')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    instance_name = fields.Char(string='Instance Name')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

    def fetch_department_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches Employee data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_department_data_from_quickbook(current_instance, last_sync_date, False,
        'oqb.dpt.lines','quickbook_department_dropdown_mapping', 'Department',
        'department', operation_type)

    # --------------------------------- Sync Department Record Quickbook To Odoo ------------------------------- #

    def fetch_department_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,logger_name=logger_name,
            operation_type=operation_type,process_record_method='process_quickbook_department_record',
            sync_date_field='quickbook_department_last_sync_date',last_id_field='quickbook_department_last_id')

    def fetch_department_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_department_sync_to_quickbook(current_instance, last_sync_date, 'hr.department', 'None',
                                                  'oqb.dpt.lines', 'odoo_department_dropdown_mapping',
                                                  'Department', 'department', operation_type)

    def odoo_department_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,is_company=is_company,
            field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_department_record',sync_date_field='odoo_department_last_sync_date',
            last_id_field='odoo_department_last_id')

    # -------------------- Sync Form and List View Odoo Partner Record to Quickbook ------------------- #

    def department_record_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook('department', active_ids, 'hr.department', 'Department')
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)

