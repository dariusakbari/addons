from odoo import api, fields, models
import datetime
from datetime import datetime, timedelta


class QuickbookLogger(models.Model):
    """
        The QuickbookLogger class is an Odoo model designed for logging interactions between Odoo and Quickbook.
        The class captures detailed information about the integration processes, including the direction of integration,
         module name, execution time, user details, operation specifics, and payloads for requests and responses.
         Additionally, it logs error codes and details, and tracks the resolution status and log type
    """
    _name = "oqb.logger"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quickbook Logger"
    _rec_name = 'integration_direction'
    _order = 'id desc'

    integration_direction = fields.Selection(
        [('otq', 'Odoo to Quickbook'), ('qto', 'Quickbook to Odoo')], string='Integration Direction', tracking=True)
    module_name = fields.Selection(
        [('chart of account', 'Chart of Accounts'), ('customer', 'Customer'),  ('sales orders', 'Sales Orders'), ('invoices', 'Invoices'), ('credit note', 'Credit Note'), ('customer payment', 'Customer Payment'), ('products', 'Products'), ('vendors', 'Vendors'),
        ('purchase order', 'Purchase Orders'), ('purchase bill', 'Vendor Bills'), ('refund', 'Refund'), ('vendor payment', 'Vendor Payment'), ('payment term', 'Payment Term'), ('payment method', 'Payment Method'), ('account tax', 'Account Tax'), ('employee', 'Employee'),
        ('employee', 'Employee'),
        ('department', 'Department')],
        string='Module Name', tracking=True)
    operation_performed_by = fields.Selection(
        [('schedular', 'Schedular'), ('manually', 'Manually')],
        string='Operation Type', tracking=True)
    record_id = fields.Char(string='Record ID')
    quickbook_datetime = fields.Datetime(string="Execution DateTime", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string="User Id", tracking=10)
    operation = fields.Char(string='Operation', tracking=True)
    description = fields.Text(string='Description', tracking=True)
    status_code = fields.Char(string='Status Code', tracking=True)
    instance_name = fields.Char(string='Instance Name', tracking=True)
    error_details = fields.Text(string='Error Details', tracking=True)
    request_payload = fields.Text(string='Request Payload', tracking=True)
    response_payload = fields.Text(string='Response Payload', tracking=True)
    resolution_status = fields.Selection(
        [('pending', 'Pending'), ('resolve', 'Resolve')], string='Resolution Status', tracking=True)
    log_type = fields.Selection(
        [('error', 'Error'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info')], string='Log Type', tracking=True)

    # -------------------------------- Schedular for Delete Logger Records -------------------------------- #
    """
            Description:
                This method is Delete Logger Records using scheduler.
            """

    def _cron_delete_old_log_records(self):
        schedulers = self.env['oqb.instance'].search([('is_connected', '=', True), ('company_name', '!=', False)])
        for scheduler in schedulers:
            try:
                is_connected, notification = self.env['oqb.instance'].test_connection_methods(f'Delete Logger ', '', '',
                                                                          'schedular', scheduler)
                # If the connection failed (is_connected is False), return the notification
                if not is_connected:
                    return notification
                if is_connected:
                    remove_log_scheduler = scheduler.remove_log_scheduler
                    remove_log_month = scheduler.remove_log_month
                    if remove_log_scheduler:
                        months_ago = int(remove_log_month or 1)
                        date_threshold = datetime.now() - timedelta(days=30 * months_ago)
                        old_records = self.env['oqb.logger'].search([('quickbook_datetime', '<', date_threshold)])
                        old_records.unlink()

            except Exception as e:
                error_details = str(e)
                description = f'Error occurred while remove the logs From Logger'
                operation = f'Delete Logger Records'
                self.env['oqb.dry.mixin'].exception_log_error(error_details, '', description, '', '',
                                          operation, 'schedular', scheduler.name, 'Exception Error')
                return None
        return None

    def create_oqb_logger(self, error_details, status_code, integration_direction, module_name, record_id, description, request_payload,
                      response_payload, operation, resolution_status, log_type, operation_performed_by, instance_name):
        """
           Create a new log record for Quickbook integration.
           """
        error_data = {'error_details': error_details,'status_code': status_code,
            'integration_direction': integration_direction,'module_name': module_name,
            'record_id': record_id,'description': description,'request_payload': request_payload,
            'response_payload': response_payload,'operation': operation,'resolution_status': resolution_status,
            'log_type': log_type,'operation_performed_by': operation_performed_by,'instance_name': instance_name}
        logger_record = self.env['oqb.logger'].create(error_data)
        logger_record.env.cr.commit()