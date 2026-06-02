# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class CustomerPaymentInherit(models.Model):
    """
       Description:
           This class inherits the 'account.payment' model and adds additional functionality for fetching
           account data from quickbook and updating records in Odoo.

       Methods:
           fetch_quotation_from_quickbook(instance_id, last_sync_date):
               Fetches account data from quickbook and updates records in Odoo.

       """
    _inherit = 'account.payment'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    instance_name = fields.Many2one('oqb.instance', string='Instance Name')
    odoo_hash = fields.Char(string='Odoo hash')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')
    oqb_payment_type = fields.Selection([
        ('check', 'Check'), ('credit card', 'Credit Card')
    ], default='check')
    quickbook_payment_name = fields.Char(string='Quickbook Record Name')


    # --------------------------------- Sync Customer Payment Record Quickbook To Odoo ------------------------------- #

    def fetch_cpt_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_cpt_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.cpt.lines','quickbook_customer_payment_dropdown_mapping',
        'Payment','customer payment', operation_type)


    def fetch_cpt_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
        field_model_name, dropdown_field_mapping_name, module_name, logger_name,operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_quickbook_cpt_record',
            sync_date_field='quickbook_customer_payment_last_sync_date',last_id_field='quickbook_customer_payment_last_id')

    # Sync Odoo to Quickbook Customer Payment Data

    def fetch_customer_payment_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_customer_payment_sync_to_quickbook(current_instance, last_sync_date, 'account.payment', 'None',
        'oqb.cpt.lines', 'odoo_customer_payment_dropdown_mapping',
        'Payment', 'customer payment', operation_type)

    def odoo_customer_payment_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
       field_model_name, dropdown_field_mapping_name, module_name, logger_name,operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_customer_payment_record',sync_date_field='odoo_customer_payment_last_sync_date',
            last_id_field='odoo_customer_payment_last_id')

    def fetch_vpt_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_vpt_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.vpt.lines','quickbook_vendor_payment_dropdown_mapping',
        'BillPayment','vendor payment', operation_type)

    def fetch_vpt_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,
            field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_quickbook_vpt_record',sync_date_field='quickbook_vendor_payment_last_sync_date',
            last_id_field='quickbook_vendor_payment_last_id')

      # Sync Odoo to Quickbook Partner Data

    def fetch_vendor_payment_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_vendor_payment_sync_to_quickbook(current_instance, last_sync_date, 'account.payment', 'None',
        'oqb.vpt.lines', 'odoo_vendor_payment_dropdown_mapping',
        'BillPayment', 'vendor payment', operation_type)

    def odoo_vendor_payment_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_vendor_payment_record',
            sync_date_field='odoo_vendor_payment_last_sync_date',last_id_field='odoo_vendor_payment_last_id')

        # -------------------- Sync Form and List View Odoo Chart of Account Record to Quickbook ------------------- #

    def payment_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        logger_name, module_name = None, None
        if not active_ids:
            active_ids = [self.id]
        # Determine partner type based on record fields

        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook(logger_name, active_ids, 'account.payment',
                                                           module_name)
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)

    class PaymentTermInherit(models.Model):
        """
           Description:
               This class inherits the 'account.payment' model and adds additional functionality for fetching
               Payment Term data from quickbook and updating records in Odoo.

           Methods:
               fetch_pyt_from_quickbook(instance_id, last_sync_date):
                   Fetches Payment Term data from quickbook and updates records in Odoo.

           """
        _inherit = 'account.payment.term'

        quickbook_id = fields.Char(string='Quickbook ID')
        sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
        instance_name = fields.Char(string='Instance Name')
        odoo_hash = fields.Char(string='Odoo hash')
        quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

        def fetch_payment_term_from_quickbook(self, current_instance, last_sync_date, operation_type):
            #     """
            #        Description:
            #            Fetches Payment Term data from quickbook and updates records in Odoo.
            #
            #        Args:
            #            instance_id (str): The quickbook instance ID.
            #            last_sync_date (Datetime): The quickbook Payment Term Last Sync Date.
            #        """
            return self.fetch_payment_term_data_from_quickbook(current_instance, last_sync_date, None,
                  'oqb.pyt.lines','quickbook_pyt_dropdown_mapping',
                  'Term','payment term', operation_type)

        def fetch_payment_term_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
            self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
                last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
                dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
                logger_name=logger_name,operation_type=operation_type,process_record_method='process_quickbook_pyt_record',
                sync_date_field='quickbook_pyt_last_sync_date',last_id_field='quickbook_pyt_last_id')

     # Sync Odoo to Quickbook Payment Term Data

        def fetch_payment_term_from_odoo(self, current_instance, last_sync_date, operation_type):
            return self.odoo_payment_term_sync_to_quickbook(current_instance, last_sync_date, 'account.payment.term', 'None',
                                                      'oqb.pyt.lines', 'odoo_pyt_dropdown_mapping',
                                                      'Term', 'payment term', operation_type)

        def odoo_payment_term_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
            self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
                last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
                is_company=is_company,field_model_name=field_model_name,
                dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
                logger_name=logger_name,operation_type=operation_type,
                process_record_method='process_odoo_payment_term_record',sync_date_field='odoo_pyt_last_sync_date',
                last_id_field='odoo_pyt_last_id')

        # -------------------- Sync Form and List View Odoo Payment Term Record to Quickbook ------------------- #

        def pyt_send_to_quickbook(self):
            # # Ensure active_ids are passed in correctly
            active_ids = self._context.get('active_ids', [])
            if not active_ids:
                active_ids = [self.id]
            success_count, active_ids, logger_name, operation_status = self.env[
                'oqb.dry.mixin'].odoo_record_send_to_quickbook('payment term', active_ids, 'account.payment.term',
                                                               'Term')
            return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                        operation_status)

class PaymentMethodInherit(models.Model):
    """
       Description:
           This class inherits the 'payment.method' model and adds additional functionality for fetching
           Payment Method data from quickbook and updating records in Odoo.

       Methods:
           fetch_pyt_from_quickbook(instance_id, last_sync_date):
               Fetches Payment Method data from quickbook and updates records in Odoo.

       """
    _inherit = 'payment.method'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    instance_name = fields.Many2one('oqb.instance', string='Instance Name')
    odoo_hash = fields.Char(string='Odoo hash')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

    def fetch_payment_method_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches Payment Method data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook Payment Method Last Sync Date.
        #        """
        return self.fetch_pym_data_from_quickbook(current_instance, last_sync_date, None,
               'oqb.pym.lines','quickbook_pym_dropdown_mapping',
               'PaymentMethod','payment method', operation_type)

    def fetch_pym_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field, is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_quickbook_pym_record',
            sync_date_field='quickbook_pym_last_sync_date',last_id_field='quickbook_pym_last_id')

    def fetch_payment_method_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_payment_method_sync_to_quickbook(current_instance, last_sync_date, 'payment.method', 'None',
        'oqb.pym.lines', 'odoo_pym_dropdown_mapping',
        'PaymentMethod', 'payment method', operation_type)

    def odoo_payment_method_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_payment_method_record',sync_date_field='odoo_pym_last_sync_date',
            last_id_field='odoo_pym_last_id')

    # -------------------- Sync Form and List View Odoo Payment Method Record to Quickbook ------------------- #

    def pym_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook('payment method', active_ids, 'payment.method',
                                                           'PaymentMethod')
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)