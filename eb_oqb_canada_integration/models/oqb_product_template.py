# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplateInherit(models.Model):
    """
       Description:
           This class inherits the 'product.template' model and adds additional functionality for fetching
           product data from Quickbook and updating records in Odoo.

       """
    _inherit = 'product.template'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook')
    odoo_hash = fields.Char(string='Odoo hash')
    instance_name = fields.Char(string='Instance Name')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

    @api.model
    def fetch_product_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_product_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.product.lines','quickbook_product_dropdown_mapping',
        'Item','product', operation_type)

        # --------------------------------- Sync Company and Contact Record Quickbook To Odoo ------------------------------- #

    def fetch_product_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,logger_name=logger_name,
            operation_type=operation_type,process_record_method='process_quickbook_product_record',
            sync_date_field='quickbook_product_last_sync_date',last_id_field='quickbook_product_last_id')

    # Sync Odoo to Quickbook Product Data

    def fetch_product_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_product_sync_to_quickbook(current_instance, last_sync_date, 'product.template', 'None',
        'oqb.product.lines', 'odoo_product_dropdown_mapping',
        'Item', 'product', operation_type)

    def odoo_product_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,is_company=is_company,
            field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_product_record',sync_date_field='odoo_product_last_sync_date',
            last_id_field='odoo_product_last_id')

    # -------------------- Sync Form and List View Odoo Product Record to Quickbook ------------------- #

    def product_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook('product', active_ids, 'product.template','Item')
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)