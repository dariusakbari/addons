# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountInherit(models.Model):
    """
       Description:
           This class inherits the 'account.account' model and adds additional functionality for fetching
           account data from quickbook and updating records in Odoo.

       Methods:
           fetch_account_from_quickbook(instance_id, last_sync_date):
               Fetches account data from quickbook and updates records in Odoo.

       """
    _inherit = 'account.account'

    quickbook_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    odoo_hash = fields.Char(string='Odoo hash')
    instance_name = fields.Char(string='Instance Name')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

    def fetch_account_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches account data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_account_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.coa.lines','quickbook_coa_dropdown_mapping',
        'Account','chart of account', operation_type)

        # --------------------------------- Sync Company and Contact Record Quickbook To Odoo ------------------------------- #

    def fetch_account_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,
            field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_quickbook_account_record',
            sync_date_field='quickbook_coa_last_sync_date',last_id_field='quickbook_coa_last_id')

    # Sync Odoo to Quickbook Sync Data...............................

    def fetch_coa_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_chart_of_account_sync_to_quickbook(current_instance, last_sync_date, 'account.account', 'None',
                                                  'oqb.coa.lines', 'odoo_coa_dropdown_mapping',
                                                  'Account', 'chart of account', operation_type)

    def odoo_chart_of_account_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_chart_of_account_record',
            sync_date_field='odoo_coa_last_sync_date',last_id_field='odoo_coa_last_id')

    # -------------------- Sync Form and List View Odoo Chart of Account Record to Quickbook ------------------- #

    def coa_record_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env['oqb.dry.mixin'].odoo_record_send_to_quickbook('chart of account', active_ids, 'account.account', 'Account')
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name, operation_status)


class AccountMoveInherit(models.Model):
    """
       Description:
           This class inherits the 'sale.order' model and adds additional functionality for fetching
           account data from quickbook and updating records in Odoo.

       Methods:
           fetch_quotation_from_quickbook(instance_id, last_sync_date):
               Fetches account data from quickbook and updates records in Odoo.

       """
    _inherit = 'account.move'

    quickbook_id = fields.Char(string='Quickbook ID')
    quickbook_credit_note_id = fields.Char(string='Quickbook ID')
    quickbook_refund_id = fields.Char(string='Quickbook ID')
    sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
    instance_name = fields.Char(string='Instance Name')
    odoo_hash = fields.Char(string='Odoo hash')
    odoo_credit_note_hash = fields.Char(string='Odoo hash')
    odoo_refund_hash = fields.Char(string='Odoo hash')
    quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')
    quickbook_account_name = fields.Char(string='Quickbook Record Name')

    # --------------------------------- Sync Invoice Record Quickbook To Odoo ------------------------------- #

    def fetch_invoice_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_invoice_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.invoice.lines','quickbook_invoice_dropdown_mapping',
        'Invoice','invoice', operation_type)


    def fetch_invoice_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_quickbook_invoice_record',sync_date_field='quickbook_invoice_last_sync_date',
            last_id_field='quickbook_invoice_last_id')

    # -------------------- Sync Form and List View Odoo Chart of Account Record to Quickbook ------------------- #

    def invoice_send_to_quickbook(self):
        # # Ensure active_ids are passed in correctly
        active_ids = self._context.get('active_ids', [])
        logger_name, module_name = None, None
        if not active_ids:
            active_ids = [self.id]
        success_count, active_ids, logger_name, operation_status = self.env[
            'oqb.dry.mixin'].odoo_record_send_to_quickbook(logger_name, active_ids, 'account.move',
                                                           module_name)
        return self.env['oqb.dry.mixin'].generate_sync_notification(success_count, active_ids, logger_name,
                                                                    operation_status)

    # Sync Odoo to Quickbook Partner Data

    def fetch_invoice_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_invoice_sync_to_quickbook(current_instance, last_sync_date, 'account.move',
        'None','oqb.invoice.lines', 'odoo_invoice_dropdown_mapping',
        'Invoice', 'invoice', operation_type)

    def odoo_invoice_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_odoo_invoice_record',
            sync_date_field='odoo_invoice_last_sync_date',last_id_field='odoo_invoice_last_id')

    # --------------------------------- Sync Credit Note Record Quickbook To Odoo ------------------------------- #

    def fetch_credit_note_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches credit note data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_credit_note_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.cdt.lines','quickbook_credit_note_dropdown_mapping',
        'CreditMemo','credit note', operation_type)


    def fetch_credit_note_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_quickbook_credit_note_record',sync_date_field='quickbook_credit_note_last_sync_date',
            last_id_field='quickbook_credit_note_last_id')

    # Sync Odoo to Quickbook Partner Data

    def fetch_credit_note_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_credit_note_sync_to_quickbook(current_instance, last_sync_date, 'account.move',
        'None','oqb.cdt.lines', 'odoo_credit_note_dropdown_mapping',
        'CreditMemo', 'credit note', operation_type)

    def odoo_credit_note_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_credit_note_record',sync_date_field='odoo_credit_note_last_sync_date',
            last_id_field='odoo_credit_note_last_id')

        # --------------------------------- Sync Purchase Bill Record Quickbook To Odoo ------------------------------- #

    def fetch_purchase_bill_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_purchase_bill_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.pcb.lines','quickbook_purchase_bill_dropdown_mapping',
        'Bill','purchase bill', operation_type)


    def fetch_purchase_bill_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                                field_model_name, dropdown_field_mapping_name, module_name,
                                                logger_name,
                                                operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_quickbook_pcb_record',
            sync_date_field='quickbook_purchase_bill_last_sync_date',last_id_field='quickbook_purchase_bill_last_id')


        # Sync Odoo to Quickbook Partner Data

    def fetch_purchase_bill_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_purchase_bill_sync_to_quickbook(current_instance, last_sync_date, 'account.move',
        'None','oqb.pcb.lines', 'odoo_purchase_bill_dropdown_mapping',
        'Bill', 'purchase bill', operation_type)

    def odoo_purchase_bill_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name,logger_name=logger_name,operation_type=operation_type,
            process_record_method='process_odoo_purchase_bill_record',sync_date_field='odoo_purchase_bill_last_sync_date',
            last_id_field='odoo_purchase_bill_last_id')

    # --------------------------------- Sync Refund Record Quickbook To Odoo ------------------------------- #

    def fetch_refund_from_quickbook(self, current_instance, last_sync_date, operation_type):
        #     """
        #        Description:
        #            Fetches product data from quickbook and updates records in Odoo.
        #
        #        Args:
        #            instance_id (str): The quickbook instance ID.
        #            last_sync_date (Datetime): The quickbook account Last Sync Date.
        #        """
        return self.fetch_refund_data_from_quickbook(current_instance, last_sync_date, None,
        'oqb.refund.lines','quickbook_refund_dropdown_mapping',
        'VendorCredit','refund', operation_type)


    def fetch_refund_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                                field_model_name, dropdown_field_mapping_name, module_name,
                                                logger_name,
                                                operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_quickbook_refund_record',
            sync_date_field='quickbook_refund_last_sync_date',last_id_field='quickbook_refund_last_id')


    def fetch_refund_from_odoo(self, current_instance, last_sync_date, operation_type):
        return self.odoo_record_sync_to_quickbook(current_instance, last_sync_date, 'account.move',
        'None','oqb.refund.lines', 'odoo_refund_dropdown_mapping',
        'VendorCredit', 'refund', operation_type)

    def odoo_record_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                      field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                      operation_type):
        self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
            last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
            is_company=is_company,field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
            logger_name=logger_name,operation_type=operation_type,process_record_method='process_odoo_refund_record',
            sync_date_field='odoo_refund_last_sync_date',last_id_field='odoo_refund_last_id')

class AccountMoveLineInherit(models.Model):
    """
       Description:
           This class inherits the 'sale.order.line' model and adds additional functionality for fetching
           sale order line data from Quickbook and updating records in Odoo.

       """
    _inherit = 'account.move.line'

    quickbook_id = fields.Char(string='Quickbook ID', readonly=True)


    class AccountTaxInherit(models.Model):
        """
           Description:
               This class inherits the 'account.tax' model and adds additional functionality for fetching
               Account Tax data from quickbook and updating records in Odoo.

           Methods:
               fetch_pyt_from_quickbook(instance_id, last_sync_date):
                   Fetches Account Tax data from quickbook and updates records in Odoo.

           """
        _inherit = 'account.tax'

        quickbook_id = fields.Char(string='Quickbook ID')
        sync_to_quickbook = fields.Boolean(string='Sync To Quickbook', default=False)
        instance_name = fields.Char(string='Instance Name')
        odoo_hash = fields.Char(string='Odoo hash')
        quickbook_tax_code = fields.Char(string='Quickbook Tax Code')
        quickbook_sync_token = fields.Char(string='Quickbook Sync Token', default='0')

        def fetch_account_tax_from_quickbook(self, current_instance, last_sync_date, operation_type):
            #     """
            #        Description:
            #            Fetches Account Tax data from quickbook and updates records in Odoo.
            #
            #        Args:
            #            instance_id (str): The quickbook instance ID.
            #            last_sync_date (Datetime): The quickbook Account Tax Last Sync Date.
            #        """
            return self.fetch_account_tax_data_from_quickbook(current_instance, last_sync_date, None,
                   'oqb.atx.lines','quickbook_account_tax_dropdown_mapping',
                   'TaxCode','account tax', operation_type)

        def fetch_account_tax_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
            self.env['oqb.dry.mixin'].fetch_data_from_quickbook(current_instance=current_instance,
                last_sync_date_field=last_sync_date_field,is_company=is_company,
                field_model_name=field_model_name,dropdown_field_mapping_name=dropdown_field_mapping_name,
                module_name=module_name,logger_name=logger_name,operation_type=operation_type,
                process_record_method='process_quickbook_account_tax_record',
                sync_date_field='quickbook_account_tax_last_sync_date',last_id_field='quickbook_account_tax_last_id')

        def fetch_account_tax_from_odoo(self, current_instance, last_sync_date, operation_type):
            return self.odoo_account_tax_sync_to_quickbook(current_instance, last_sync_date,
            'account.tax', 'None','oqb.atx.lines',
            'odoo_account_tax_dropdown_mapping','TaxService',
            'account tax', operation_type)

        def odoo_account_tax_sync_to_quickbook(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                                          field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                          operation_type):
            self.env['oqb.dry.mixin'].fetch_data_from_odoo(current_instance=current_instance,
                last_sync_date_field=last_sync_date_field,odoo_module_name=odoo_module_name,
                is_company=is_company,field_model_name=field_model_name,
                dropdown_field_mapping_name=dropdown_field_mapping_name,module_name=module_name,
                logger_name=logger_name,operation_type=operation_type,process_record_method='process_odoo_account_tax_record',
                sync_date_field='odoo_account_tax_last_sync_date',last_id_field='odoo_account_tax_last_id')