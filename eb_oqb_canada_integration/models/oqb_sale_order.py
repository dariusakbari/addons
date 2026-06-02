# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrderInherit(models.Model):
    """
       Description:
           This class inherits the 'sale.order' model and adds additional functionality for fetching
           account data from quickbook and updating records in Odoo.

       Methods:
           fetch_quotation_from_quickbook(instance_id, last_sync_date):
               Fetches account data from quickbook and updates records in Odoo.

       """
    _inherit = 'sale.order'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    instance_name = fields.Char(string='Instance Name')
    odoo_hash = fields.Char(string='Odoo hash')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')
    quickbook_sale_order_name = fields.Char(string='Quickbook Estimate Name')

    @api.model
    def fetch_sale_order_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_sale_order_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.saleorder.lines','quickbook_sale_order_dropdown_mapping',
        'Estimate','sales orders', operation_type)

        # --------------------------------- Sync Sale Order Record Quickbook To Odoo ------------------------------- #

    def fetch_sale_order_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,logger_name=logger_name,
            operation_type=operation_type,process_record_method='process_quickbook_sale_order_record',
            sync_date_field='quickbook_sale_order_last_sync_date',last_id_field='quickbook_sale_order_last_id')

    # Sync Odoo to Quickbook Product Data

    def fetch_sale_order_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_sale_order_sync_to_quickbook(current_instance, last_sync_date, 'sale.order', 'None',
        'oqb.saleorder.lines', 'odoo_sale_order_dropdown_mapping',
        'Estimate', 'sales orders', operation_type)

    def odoo_sale_order_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,is_company=is_company,
            field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_sale_order_record',sync_date_field='odoo_sale_order_last_sync_date',
            last_id_field='odoo_sale_order_last_id')

    # -------------------- Sync Form and List View Odoo Sales Orders Record to Quickbook ------------------- #

    def sale_order_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook('sales orders', active_ids, 'sale.order',
                                                           'Estimate')
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)


class SaleOrderLineInherit(models.Model):
    """
       Description:
           This class inherits the 'sale.order.line' model and adds additional functionality for fetching
           sales orders line data from Quickbook and updating records in Odoo.

       """
    _inherit = 'sale.order.line'

    quickbook_id = fields.Char(string='Quickbook ID', readonly=True)









