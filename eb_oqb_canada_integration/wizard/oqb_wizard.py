from odoo import api, fields, models, _
import logging


class ManualQuickbookToOdoo(models.TransientModel):
    """
        The ManualPdToOdoo class is a transient model designed to facilitate the manual transfer of records
        from Quickbook to Odoo. This class allows users to specify which module and record from quickbook they want to send to Odoo
    """
    _name = "oqb.wizard"
    _description = "Manual Record Sync Quickbook To Odoo"

    quickbook_module_name = fields.Selection(
        [('chart of account', 'Chart of Accounts'), ('customer', 'Customer'),  ('sales orders', 'Sales Orders'), ('invoices', 'Invoices'), ('credit note', 'Credit Note'), ('customer payment', 'Customer Payment'), ('products', 'Products'), ('vendors', 'Vendors'),
        ('purchase order', 'Purchase Orders'), ('purchase bill', 'Vendor Bills'), ('refund', 'Refund'), ('vendor payment', 'Vendor Payment'), ('payment term', 'Payment Term'), ('payment method', 'Payment Method'), ('account tax', 'Account Tax'), ('employee', 'Employee'),
        ('employee', 'Employee'),('department', 'Department')],string='Quickbook Module Name', required=True)
    quickbook_record_id = fields.Text(string='Quickbook Record IDs', required=True)
    quickbook_instance = fields.Many2one('oqb.instance', string="Quickbook Instance", required=True)

    # -------------------------- Sync a record from Quickbook to Odoo ----------------------- #

    def action_send_record_quickbook_to_odoo(self):
        """
            Dispatches the action to send a record from Quickbook to Odoo based on the Quickbook module name.

            This function checks the Quickbook module name and record ID to determine which specific function to
            call to handle the synchronization of the record from Quickbook to Odoo. It handles different types
            of records such as organization, person, lead, deal, product, and user.

            return: None
        """
        total_record_ids, record_ids, message = None, None, None

        current_instance = self.quickbook_instance
        logger_name = self.quickbook_module_name
        is_connected, notification = current_instance.test_connection_methods(
            f'Manual {logger_name.capitalize()} Sync Quickbook to Odoo', logger_name, 'odoo', 'manually', current_instance)

        # If the connection failed (is_connected is False), return the notification
        if not is_connected:
            return notification

        if not current_instance.is_connected:
            return {
                'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'type': 'warning', 'sticky': False,
                           'message': f"'The 'Is Connected' field is set to True, and the 'Company Id' field is required to find the instance."},
            }

        quickbook_module = self.quickbook_module_name
        quickbook_config = self.get_module_log_name(quickbook_module)

        if self.quickbook_record_id:

            message, total_record_ids, record_ids = self.sync_quickbook_to_odoo_record(self.quickbook_record_id,
             quickbook_config['module_name'], quickbook_config['logger_name'],current_instance)

        if message:
            return {
                'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {
                    'type': 'success', 'sticky': False,
                    'message': f"{message}. Total {total_record_ids} Ids: {record_ids}",
                },
            }
        else:
            message = "Please Check The Quickbook Logger"
            return {
                'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'type': 'warning', 'sticky': False, 'message': message},
            }

    # --------------------- Get Value From Record Based Not List And Dictionary ------------------- #

    def get_value_from_record(self, record, key):
        if isinstance(record, list) and record and isinstance(record[0], dict):
            return record[0].get(key)
        elif isinstance(record, dict):
            return record.get(key)
        return None

    def get_module_log_name(self, quickbook_module):
        logger_mappings = {
            'customer': {
                'module_name': 'Customer',
                'logger_name': 'customer'
            },
            'chart of account': {
                'module_name': 'Account',
                'logger_name': 'chart of account'
            },
            'sales orders': {
                'module_name': 'Estimate',
                'logger_name': 'sales orders'
            },
            'invoices': {
                'module_name': 'Invoice',
                'logger_name': 'invoice'
            },
            'credit note': {
                'module_name': 'CreditMemo',
                'logger_name': 'credit note'
            },
            'customer payment': {
                'module_name': 'Payment',
                'logger_name': 'customer payment'
            },
            'products': {
                'module_name': 'Item',
                'logger_name': 'product'
            },
            'vendors': {
                'module_name': 'Vendor',
                'logger_name': 'vendor'
            },
            'purchase order': {
                'module_name': 'PurchaseOrder',
                'logger_name': 'purchase order'
            },
            'purchase bill': {
                'module_name': 'Bill',
                'logger_name': 'purchase bill'
            },
            'refund': {
                'module_name': 'VendorCredit',
                'logger_name': 'refund'
            },
            'vendor payment': {
                'module_name': 'BillPayment',
                'logger_name': 'vendor payment'
            },
            'payment term': {
                'module_name': 'Term',
                'logger_name': 'payment term'
            },
            'payment method': {
                'module_name': 'PaymentMethod',
                'logger_name': 'payment method'
            },
            'account tax': {
                'module_name': 'TaxCode',
                'logger_name': 'account tax'
            },
            'employee': {
                'module_name': 'Employee',
                'logger_name': 'employee'
            },
            'department': {
                'module_name': 'Department',
                'logger_name': 'department'
            }
        }

        return logger_mappings[quickbook_module]


    def sync_quickbook_to_odoo_record(self, id_values, module_name, logger_name, current_instance):
        record_id, total_record_ids , partner_record_ids, message, operation_status = None, 0, [], None, None
        try:
            is_connected, notification = current_instance.test_connection_methods(
                f'Manual {logger_name.capitalize()} Sync quickbook to Odoo', logger_name, 'odoo', 'manually', current_instance)

            # If the connection failed (is_connected is False), return the notification
            if not is_connected:
                return notification, None, None

            api_token, pagination_size, base_url, minor_version, quickbook_company_id, odoo_company_id = self.env['oqb.dry.mixin'].get_oqb_instance_data(
                current_instance)
            quickbook_record_ids_list = id_values.split(',')
            if not quickbook_record_ids_list:
                return None, None, None
            for partner_id in quickbook_record_ids_list:
                total_record_ids += 1
                if not partner_id:
                    continue
                partner_id = partner_id.strip()

                partner_record = self.env['oqb.dry.mixin'].fetch_quickbook_manual_record(module_name,
                                partner_id, current_instance,logger_name, 'manually', 'Id')
                if partner_record:
                    # Use the existing process_partner_record method to create the company
                    # Get the dynamic mapping for the logger_name
                    logger_config = self.get_logger_mappings(logger_name, 'quickbook')
                    # Call the common process_quickbook_record method
                    operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
                        batch_records=partner_record,current_instance=current_instance,
                        field_model_name=logger_config['field_model_name'],
                        dropdown_field_mapping_name=logger_config['dropdown_field_mapping_name'],
                        module_name=module_name,logger_name=logger_name,operation_type='manually',
                        odoo_company_id=odoo_company_id,model_name=logger_config['model_name'],related_logger=None,
                        search_domain=logger_config['search_domain'],additional_fields=None,check_hash=False)

                    if operation_status:
                        # Unpack the tuple directly
                        result, record_id, odoo_id, odoo_record = operation_status
                        partner_record_ids.append(record_id)
                        if result == 'no_create' or result is None:
                            message = None
                        elif result == 'no_update':
                            message = f"An update is not required for the posted {logger_name} record."
                        else:
                            message = f"{logger_name.capitalize()} Successfully Created/Updated"
                else:
                    total_record_ids -= 1
                    warning_message = f'No record found for this {logger_name.capitalize()} ID : {partner_id}'
                    operation = f'Manually {logger_name} Push quickbook to Odoo'
                    self.env['oqb.dry.mixin'].log_operation_warning(logger_name, warning_message, operation,
                                                                   'odoo', partner_record, partner_id, 'manually', current_instance.name)

            return message, total_record_ids, partner_record_ids

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Sync quickbook {logger_name.capitalize()} Record to Odoo'
            description = f'Error occurred while sending {logger_name} record quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo', record_id,
                                                         operation, 'manually', current_instance.name, error_type)
            return None, None, None

    def get_logger_mappings(self, logger_name, system_name):
        """Get dynamic mappings for the given logger_name."""
        logger_mappings = {
            'customer': {
                'field_model_name': 'oqb.customer.lines',
                'dropdown_field_mapping_name': f"{system_name}_customer_dropdown_mapping",
                'module_name': 'Customer',
                'model_name': 'res.partner',
                'search_domain': [('is_company', '=', False), ('active', '=', True)]
            },
            'product': {
                'field_model_name': 'oqb.product.lines',
                'dropdown_field_mapping_name': f"{system_name}_product_dropdown_mapping",
                'module_name': 'Item',
                'model_name': 'product.template',
                'search_domain': [('active', '=', True)]
            },
            'chart of account': {
                'field_model_name': 'oqb.coa.lines',
                'dropdown_field_mapping_name': f'{system_name}_coa_dropdown_mapping',
                'module_name': 'Account',
                'model_name': 'account.account',
                'search_domain': []
            },
            'sales orders': {
                'field_model_name': 'oqb.saleorder.lines',
                'dropdown_field_mapping_name': f'{system_name}_sale_order_dropdown_mapping',
                'module_name': 'Estimate',
                'model_name': 'sale.order',
                'search_domain': []
            },
            'invoice': {
                'field_model_name': 'oqb.invoice.lines',
                'dropdown_field_mapping_name': f'{system_name}_invoice_dropdown_mapping',
                'module_name': 'Invoice',
                'model_name': 'account.move',
                'search_domain': [('move_type', '=', 'out_invoice')]
            },
            'customer payment': {
                'field_model_name': 'oqb.cpt.lines',
                'dropdown_field_mapping_name': f'{system_name}_cpt_dropdown_mapping',
                'module_name': 'Payment',
                'model_name': 'account.payment',
                'search_domain': [('partner_type', '=', 'customer')]
            },
            'vendor': {
                'field_model_name': 'oqb.vendor.lines',
                'dropdown_field_mapping_name': f'{system_name}_vendor_dropdown_mapping',
                'module_name': 'Vendor',
                'model_name': 'res.partner',
                'search_domain': [('is_company', '=', False), ('active', '=', True), ('supplier_rank', '>', 0)]
            },
            'purchase order': {
                'field_model_name': 'oqb.pco.lines',
                'dropdown_field_mapping_name': f'{system_name}_purchase_order_dropdown_mapping',
                'module_name': 'PurchaseOrder',
                'model_name': 'purchase.order',
                'search_domain': []
            },
            'purchase bill': {
                'field_model_name': 'oqb.pcb.lines',
                'dropdown_field_mapping_name': f'{system_name}_purchase_bill_dropdown_mapping',
                'module_name': 'Bill',
                'model_name': 'account.move',
                'search_domain': [('move_type', '=', 'in_invoice')]
            },
            'vendor payment': {
                'field_model_name': 'oqb.vpt.lines',
                'dropdown_field_mapping_name': f'{system_name}_vendor_payment_dropdown_mapping',
                'module_name': 'BillPayment',
                'model_name': 'account.payment',
                'search_domain': [('partner_type', '=', 'supplier')]
            },
            'employee': {
                'field_model_name': 'oqb.employee.lines',
                'dropdown_field_mapping_name': f'{system_name}_employee_dropdown_mapping',
                'module_name': 'Employee',
                'model_name': 'hr.employee',
                'search_domain': []
            },
            'department': {
                'field_model_name': 'oqb.dpt.lines',
                'dropdown_field_mapping_name': f'{system_name}_department_dropdown_mapping',
                'module_name': 'Department',
                'model_name': 'hr.department',
                'search_domain': []
            },
            'refund': {
                'field_model_name': 'oqb.refund.lines',
                'dropdown_field_mapping_name': f'{system_name}_refund_dropdown_mapping',
                'module_name': 'VendorCredit',
                'model_name': 'account.move',
                'search_domain': [('move_type', '=', 'in_refund')]
            },
            'credit note': {
                'field_model_name': 'oqb.cdt.lines',
                'dropdown_field_mapping_name': f'{system_name}_credit_note_dropdown_mapping',
                'module_name': 'CreditMemo',
                'model_name': 'account.move',
                'search_domain': [('move_type', '=', 'out_refund')]
            },
            'payment term': {
                'field_model_name': 'oqb.pyt.lines',
                'dropdown_field_mapping_name': f'{system_name}_pyt_dropdown_mapping',
                'module_name': 'Term',
                'model_name': 'account.payment.term',
                'search_domain': []
            },
            'payment method': {
                'field_model_name': 'oqb.pym.lines',
                'dropdown_field_mapping_name': f'{system_name}_pym_dropdown_mapping',
                'module_name': 'PaymentMethod',
                'model_name': 'payment.method',
                'search_domain': []
            },
            'account tax': {
                'field_model_name': 'oqb.atx.lines',
                'dropdown_field_mapping_name': f'{system_name}_account_tax_dropdown_mapping',
                'module_name': 'TaxCode',
                'model_name': 'account.tax',
                'search_domain': []
            }
        }

        # Validate and return the mapping
        if logger_name not in logger_mappings:
            raise ValueError(f"Logger name '{logger_name}' is not supported.")

        return logger_mappings[logger_name]

    # ---------------------- Odoo Res Partner Wizard That Manually Sync Record quickbook to Odoo ------------- #
    class PartnerManualOqbToOdoo(models.TransientModel):
        """
            The ManualPdToOdoo class is a transient model designed to facilitate the manual transfer of records
            from quickbook to Odoo. This class allows users to specify Contacts Module and record from quickbook they want to send to Odoo
        """
        _name = "oqb.partner.wizard"
        _description = "Manual Partner Record Sync quickbook To Odoo"

        quickbook_partner_module = fields.Selection([('customer', 'Customer'), ('vendors', 'vendors')],
            string='quickbook Module Name', required=True)
        quickbook_record_id = fields.Text(string='Quickbook Record IDs', required=True)
        quickbook_instance = fields.Many2one('oqb.instance', string="Quickbook Instance", required=True)

        def action_send_partner_record_quickbook_to_odoo(self):
            # Call test_connection to check if the connection is successful
            total_record_ids, record_ids, message = None, None, None
            current_instance = self.quickbook_instance
            logger_name = self.quickbook_partner_module
            is_connected, notification = current_instance.test_connection_methods(
                f'Manual {logger_name.capitalize()} Sync Quickbook to Odoo', logger_name, 'odoo', 'manually',
                current_instance)

            # If the connection failed (is_connected is False), return the notification
            if not is_connected:
                return notification

            quickbook_module = self.quickbook_partner_module
            quickbook_config = self.env['oqb.wizard'].get_module_log_name(quickbook_module)

            if self.quickbook_partner_module and self.quickbook_record_id:

                message, total_record_ids, record_ids = self.env['oqb.wizard'].sync_quickbook_to_odoo_record(
                    self.quickbook_record_id,quickbook_config['module_name'],quickbook_config['logger_name'],
                    current_instance)

            if message:
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {
                        'type': 'success', 'sticky': False,
                        'message': f"{message}. Total {total_record_ids} Ids: {record_ids}",
                    },
                }
            else:
                message = "Please Check The quickbook Logger"
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'type': 'warning', 'sticky': False, 'message': message},
                }

    # ---------------------- Odoo Res Partner Wizard That Manually Sync Record quickbook to Odoo ------------- #
    class AccountMoveManualOqbToOdoo(models.TransientModel):
        """
            The ManualPdToOdoo class is a transient model designed to facilitate the manual transfer of records
            from quickbook to Odoo. This class allows users to specify Account Move Module and record from quickbook they want to send to Odoo
        """
        _name = "oqb.acc_move.wizard"
        _description = "Manual Invoicing Record Sync Quickbook To Odoo"

        quickbook_partner_module = fields.Selection([('customer', 'Customer'), ('vendors', 'Vendors'), ('products', 'Products'), ('chart of account', 'Chart of Accounts'), ('invoices', 'Invoices'), ('credit note', 'Credit Note'), ('purchase bill', 'Vendor Bills'), ('refund', 'Refund')
        ,('customer payment', 'Customer Payment'), ('vendor payment', 'Vendor Payment'),('account tax', 'Account Tax'), ('payment term', 'Payment Term'), ('payment method', 'Payment Method')],
         string='Quickbook Module Name', required=True)
        quickbook_record_id = fields.Text(string='Quickbook Record IDs', required=True)
        quickbook_instance = fields.Many2one('oqb.instance', string="Quickbook Instance", required=True)

        def action_send_account_move_record_quickbook_to_odoo(self):
            # Call test_connection to check if the connection is successful
            total_record_ids, record_ids, message = None, None, None
            current_instance = self.quickbook_instance
            logger_name = self.quickbook_partner_module
            is_connected, notification = current_instance.test_connection_methods(
                f'Manual {logger_name.capitalize()} Sync Quickbook to Odoo', logger_name, 'odoo', 'manually',
                current_instance)

            # If the connection failed (is_connected is False), return the notification
            if not is_connected:
                return notification

            quickbook_module = self.quickbook_partner_module
            quickbook_config = self.env['oqb.wizard'].get_module_log_name(quickbook_module)

            if self.quickbook_partner_module  and self.quickbook_record_id:

                message, total_record_ids, record_ids = self.env['oqb.wizard'].sync_quickbook_to_odoo_record(
                    self.quickbook_record_id, quickbook_config['module_name'], quickbook_config['logger_name'],
                    current_instance)

            if message:
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {
                        'type': 'success', 'sticky': False,
                        'message': f"{message}. Total {total_record_ids} Ids: {record_ids}",
                    },
                }
            else:
                message = "Please Check The quickbook Logger"
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'type': 'warning', 'sticky': False, 'message': message},
                }

        # ---------------------- Odoo Sale Order Wizard That Manually Sync Record quickbook to Odoo ------------- #
        class SaleOrderManualOqbToOdoo(models.TransientModel):
            """
                The ManualPdToOdoo class is a transient model designed to facilitate the manual transfer of records
                from quickbook to Odoo. This class allows users to specify Account Move Module and record from quickbook they want to send to Odoo
            """
            _name = "oqb.sale_order.wizard"
            _description = "Manual Sale Order Record Sync Quickbook To Odoo"

            quickbook_partner_module = fields.Selection(
                [('products', 'Products'), ('customer', 'Customer'), ('sales orders', 'Sales Orders')],
                string='Quickbook Module Name', required=True)
            quickbook_record_id = fields.Text(string='Quickbook Record IDs', required=True)
            quickbook_instance = fields.Many2one('oqb.instance', string="Quickbook Instance", required=True)

            def action_send_sale_order_record_quickbook_to_odoo(self):
                # Call test_connection to check if the connection is successful
                total_record_ids, record_ids, message = None, None, None
                current_instance = self.quickbook_instance
                logger_name = self.quickbook_partner_module
                is_connected, notification = current_instance.test_connection_methods(
                    f'Manual {logger_name.capitalize()} Sync Quickbook to Odoo', logger_name, 'odoo', 'manually',
                    current_instance)

                # If the connection failed (is_connected is False), return the notification
                if not is_connected:
                    return notification

                quickbook_module = self.quickbook_partner_module
                quickbook_config = self.env['oqb.wizard'].get_module_log_name(quickbook_module)

                if self.quickbook_partner_module and self.quickbook_record_id:

                    message, total_record_ids, record_ids = self.env['oqb.wizard'].sync_quickbook_to_odoo_record(
                        self.quickbook_record_id, quickbook_config['module_name'], quickbook_config['logger_name'],
                        current_instance)

                if message:
                    return {
                        'type': 'ir.actions.client', 'tag': 'display_notification',
                        'params': {
                            'type': 'success', 'sticky': False,
                            'message': f"{message}. Total {total_record_ids} Ids: {record_ids}",
                        },
                    }
                else:
                    message = "Please Check The quickbook Logger"
                    return {
                        'type': 'ir.actions.client', 'tag': 'display_notification',
                        'params': {'type': 'warning', 'sticky': False, 'message': message},
                    }

        # ---------------------- Odoo Purchase Order Wizard That Manually Sync Record quickbook to Odoo ------------- #

        class PurchaseOrderManualOqbToOdoo(models.TransientModel):
            """
                The ManualPdToOdoo class is a transient model designed to facilitate the manual transfer of records
                from quickbook to Odoo. This class allows users to specify Purchase Order Module and record from quickbook they want to send to Odoo
            """
            _name = "oqb.purchase_order.wizard"
            _description = "Manual Purchase Order Record Sync Quickbook To Odoo"

            quickbook_partner_module = fields.Selection(
                [('products', 'Products'), ('vendors', 'vendors'),  ('purchase order', 'Purchase Orders')],
                string='Quickbook Module Name', required=True)
            quickbook_record_id = fields.Text(string='Quickbook Record IDs', required=True)
            quickbook_instance = fields.Many2one('oqb.instance', string="Quickbook Instance", required=True)

            def action_send_purchase_order_record_quickbook_to_odoo(self):
                # Call test_connection to check if the connection is successful
                total_record_ids, record_ids, message = None, None, None
                current_instance = self.quickbook_instance
                logger_name = self.quickbook_partner_module
                is_connected, notification = current_instance.test_connection_methods(
                    f'Manual {logger_name.capitalize()} Sync Quickbook to Odoo', logger_name, 'odoo', 'manually',
                    current_instance)

                # If the connection failed (is_connected is False), return the notification
                if not is_connected:
                    return notification

                quickbook_module = self.quickbook_partner_module
                quickbook_config = self.env['oqb.wizard'].get_module_log_name(quickbook_module)

                if self.quickbook_partner_module and self.quickbook_record_id:

                    message, total_record_ids, record_ids = self.env['oqb.wizard'].sync_quickbook_to_odoo_record(
                        self.quickbook_record_id, quickbook_config['module_name'], quickbook_config['logger_name'],
                        current_instance)

                if message:
                    return {
                        'type': 'ir.actions.client', 'tag': 'display_notification',
                        'params': {
                            'type': 'success', 'sticky': False,
                            'message': f"{message}. Total {total_record_ids} Ids: {record_ids}",
                        },
                    }
                else:
                    message = "Please Check The quickbook Logger"
                    return {
                        'type': 'ir.actions.client', 'tag': 'display_notification',
                        'params': {'type': 'warning', 'sticky': False, 'message': message},
                    }

    # ---------------------- Odoo Employee Department Wizard That Manually Sync Record quickbook to Odoo ------------- #

    class EmployeeDepartmentManualOqbToOdoo(models.TransientModel):
        """
            The ManualPdToOdoo class is a transient model designed to facilitate the manual transfer of records
            from quickbook to Odoo. This class allows users to specify Purchase Order Module and record from quickbook they want to send to Odoo
        """
        _name = "oqb.emp_dept.wizard"
        _description = "Manual Employee, Department Record Sync Quickbook To Odoo"

        quickbook_partner_module = fields.Selection(
            [('employee', 'Employee'), ('department', 'Department')],
            string='Quickbook Module Name', required=True)
        quickbook_record_id = fields.Text(string='Quickbook Record IDs', required=True)
        quickbook_instance = fields.Many2one('oqb.instance', string="Quickbook Instance", required=True)

        def action_send_emp_dept_record_quickbook_to_odoo(self):
            # Call test_connection to check if the connection is successful
            total_record_ids, record_ids, message = None, None, None
            current_instance = self.quickbook_instance
            logger_name = self.quickbook_partner_module
            is_connected, notification = current_instance.test_connection_methods(
                f'Manual {logger_name.capitalize()} Sync Quickbook to Odoo', logger_name, 'odoo', 'manually',
                current_instance)

            # If the connection failed (is_connected is False), return the notification
            if not is_connected:
                return notification

            quickbook_module = self.quickbook_partner_module
            quickbook_config = self.env['oqb.wizard'].get_module_log_name(quickbook_module)

            if self.quickbook_partner_module and self.quickbook_record_id:

                message, total_record_ids, record_ids = self.env['oqb.wizard'].sync_quickbook_to_odoo_record(
                    self.quickbook_record_id, quickbook_config['module_name'], quickbook_config['logger_name'],
                    current_instance)

            if message:
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {
                        'type': 'success', 'sticky': False,
                        'message': f"{message}. Total {total_record_ids} Ids: {record_ids}",
                    },
                }
            else:
                message = "Please Check The quickbook Logger"
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'type': 'warning', 'sticky': False, 'message': message},
                }

