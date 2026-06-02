from docutils.nodes import description

from odoo import api, fields, models, _
import requests
import json
from datetime import date
import pytz
import logging
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OqbDryMixin(models.AbstractModel):
    """
        Abstract model for mixing common functionality related to all modules.
    """
    _name = "oqb.dry.mixin"
    _description = "Oqb Mixin"

    # ---------------------------------- Get Headers ------------------------------ #

    @api.model
    def get_headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    # ---------------------------------- Fetch Odoo And Quickbook Module Fields ------------------------------ #
    @api.model
    def fetch_and_store_oqb_fields(self, table_name, model_name, mapper_model, instance_id, mapper_id_field,
                                   mapper_lines_field, logger_name):
        """
                Description:
                            Fetches fields from a database table and an external API endpoint,
                            then stores them in the specified Odoo model.

                Args:
                    table_name(str): The name of the database table to fetch fields from.
                    endpoint(str): The API endpoint to fetch fields from.
                    mapper_model(odoo.models.Model): The Odoo model to store the fetched fields in.

                Return:
                    count(int): The number of fields stored in the Odoo model.
                """
        try:
            # Fetch the instance name of the quickbook
            instance_name = instance_id.name
            system_odoo = 'Odoo'
            count = 0

            # Fetch odoo fields from the database table
            cr = self.env.cr
            cr.execute(
                f"""
                          SELECT isc.column_name, isc.data_type, imf.field_description
                          FROM information_schema.columns isc
                          JOIN ir_model_fields imf
                          ON isc.column_name = imf.name
                          WHERE isc.table_name = '{table_name}'
                          AND imf.model = '{table_name.replace('_', '.')}'""")
            results = cr.fetchall()

            # Store or update fetched fields in the mapper model
            for column_name, data_type, field_description in results:
                # Extract the actual label name from the field_description dictionary
                label_name = field_description.get('en_US') if isinstance(field_description,
                                                                          dict) else field_description
                partner = mapper_model.search([('label_name', '=', label_name), ('system_name', '=', system_odoo)],
                                              limit=1)
                odoo_field_vals = {'label_name': label_name, 'field_type': data_type, 'internal_name': column_name,
                                   'quickbook_instance_name': instance_name,
                                   'system_name': system_odoo}
                if not partner:
                    count += 1
                    mapper_model.create(odoo_field_vals)

                else:
                    count += 1
                    partner.write(odoo_field_vals)

            # Fetch quickbook fields from the external API
            if logger_name == 'product':
                query = "SELECT * FROM Item WHERE Type IN ('Inventory', 'Service', 'NonInventory') STARTPOSITION 0 MAXRESULTS 1"
            else:
                query = f"SELECT * FROM {model_name} STARTPOSITION 0 MAXRESULTS 1"


            response = self.fetch_quickbooks_data(instance_id, model_name, query)
            operation = f'Get Quickbook Fields'
            response_data = self.env['oqb.instance'].handle_response(response, {}, model_name, '', '', '', 'get',
                                                                     operation, 'manually', instance_id)

            if not response_data:
                description = f'First Create {model_name} in Quickbook. Then Import The Fields'
                operation = f'{logger_name.capitalize()} Record Sync Quickbook to Odoo'
                self.log_operation_warning(logger_name, description, operation, 'odoo', '',
                                           '', 'manually', instance_id.name)
                return 0
            if response_data:
                system_name = 'QuickBooks'  # Set the system name for consistency

                # Process each record in the entity data
                for record in response_data:
                    # Process each field in the record
                    for field_name, field_value in record.items():

                        # If the field is one of the targeted fields, process nested fields
                        if field_name in ['BillAddr', 'Mobile', 'PrimaryEmailAddr', 'PrimaryPhone', 'MetaData',
                                          'ShipAddr', 'Job', 'CurrencyRef', 'PrimaryAddr']:
                            if isinstance(field_value, dict):  # If value is a dictionary, process nested fields
                                nested_fields = self.extract_nested_fields(field_name, field_value, instance_name,
                                                                           system_name)

                                quickbook_field_vals = {
                                    'label_name': field_name,
                                    'field_type': type(field_value).__name__,
                                    'quickbook_instance_name': instance_name,
                                    'system_name': system_name,
                                    'internal_name': field_name,
                                    'field_definition': record
                                }
                                partner = mapper_model.search(
                                    [('label_name', '=', field_name), ('system_name', '=', system_name)], limit=1)

                                if not partner:
                                    count += 1
                                    mapper_model.create(quickbook_field_vals)
                                else:
                                    count += 1
                                    partner.write(quickbook_field_vals)
                                    partner.env.cr.commit()

                                for nested_field_vals in nested_fields:
                                    partner = mapper_model.search(
                                        [('label_name', '=', nested_field_vals['label_name']),
                                         ('system_name', '=', system_name)],
                                        limit=1
                                    )
                                    if not partner:
                                        count += 1
                                        mapper_model.create(nested_field_vals)
                                    else:
                                        count += 1
                                        partner.write(nested_field_vals)
                                        partner.env.cr.commit()
                        else:
                            # Handle top-level fields normally
                            quickbook_field_vals = {
                                'label_name': field_name,
                                'field_type': type(field_value).__name__,
                                'quickbook_instance_name': instance_name,
                                'system_name': system_name,
                                'internal_name': field_name,
                                'field_definition': record
                            }
                            partner = mapper_model.search(
                                [('label_name', '=', field_name), ('system_name', '=', system_name)], limit=1)

                            if not partner:
                                count += 1
                                mapper_model.create(quickbook_field_vals)
                            else:
                                count += 1
                                partner.write(quickbook_field_vals)
                                partner.env.cr.commit()
                self.create_oqb_field_mapping(table_name, model_name, mapper_model, instance_id, mapper_id_field,
                                              mapper_lines_field)

            else:
                return 0

            return count
            # Return the total count of fields created or updated

        except Exception as e:
            # create a record in QuickbookLogger to store the error data
            error_details = str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while fetching {logger_name} module field'
            operation = f'Import Odoo and Quickbook Fields'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo', '',
                                                          operation, 'manually', instance_id.name, error_type)
            return 0

    def create_oqb_field_mapping(self, table_name, model_name, mapper_model, instance_id, mapper_id_field,
                                 mapper_lines_field):
        """
        Automatically map static fields for the Account module in oqb.coa.lines.
        """

        # Define reusable field groups
        base_partner_fields = [
            {'odoo_field_label': 'street', 'quickbook_field_label': 'Line1'},
            {'odoo_field_label': 'street2', 'quickbook_field_label': 'Line2'},
            {'odoo_field_label': 'state_id', 'quickbook_field_label': 'CountrySubDivisionCode'},
            {'odoo_field_label': 'country_id', 'quickbook_field_label': 'Country'},
            {'odoo_field_label': 'city', 'quickbook_field_label': 'City'},
            {'odoo_field_label': 'zip', 'quickbook_field_label': 'PostalCode'},
            {'odoo_field_label': 'email', 'quickbook_field_label': 'PrimaryEmailAddr'},
            {'odoo_field_label': 'phone', 'quickbook_field_label': 'PrimaryPhone'},
            {'odoo_field_label': 'website', 'quickbook_field_label': 'WebAddr'},
            {'odoo_field_label': 'comment', 'quickbook_field_label': 'Notes'}
        ]

        base_name_fields = [
            {'odoo_field_label': 'first_name', 'quickbook_field_label': 'GivenName'},
            {'odoo_field_label': 'last_name', 'quickbook_field_label': 'FamilyName'},
            {'odoo_field_label': 'name', 'quickbook_field_label': 'DisplayName'},
        ]

        base_account_fields = [
            {'odoo_field_label': 'invoice_date', 'quickbook_field_label': 'TxnDate'},
            {'odoo_field_label': 'invoice_date_due', 'quickbook_field_label': 'DueDate'},
            {'odoo_field_label': 'amount_total', 'quickbook_field_label': 'TotalAmt'},
        ]

        base_payment_fields = [
            {'odoo_field_label': 'amount', 'quickbook_field_label': 'TotalAmt'},
        ]

        # Define static mappings for each model
        static_mappings_dict = {
            'Account': [
                {'odoo_field_label': 'name', 'quickbook_field_label': 'Name'},
                {'odoo_field_label': 'account_type', 'quickbook_field_label': 'AccountType'},
                {'odoo_field_label': 'code_store', 'quickbook_field_label': 'AcctNum'},
            ],
            'Customer': base_name_fields + base_partner_fields,
            'Vendor': base_name_fields + base_partner_fields,
            'Item': [
                {'odoo_field_label': 'name', 'quickbook_field_label': 'Name'},
                {'odoo_field_label': 'list_price', 'quickbook_field_label': 'UnitPrice'},
                {'odoo_field_label': 'description', 'quickbook_field_label': 'Description'},
                {'odoo_field_label': 'type', 'quickbook_field_label': 'Type'},
                {'odoo_field_label': 'default_code', 'quickbook_field_label': 'Sku'},
            ],
            'Estimate': [
                {'odoo_field_label': 'date_order', 'quickbook_field_label': 'TxnDate'},
                {'odoo_field_label': 'state', 'quickbook_field_label': 'TxnStatus'},
                # {'odoo_field_label': 'name', 'quickbook_field_label': 'DocNumber'},
            ],
            'Invoice': base_account_fields,
            'Bill': base_account_fields,
            'CreditMemo': [
                {'odoo_field_label': 'invoice_date', 'quickbook_field_label': 'TxnDate'},
            ],
            'VendorCredit': [
                {'odoo_field_label': 'invoice_date', 'quickbook_field_label': 'TxnDate'},
            ],
            'Term': [
                {'odoo_field_label': 'name', 'quickbook_field_label': 'Name'},
                {'odoo_field_label': 'discount_days', 'quickbook_field_label': 'DueDays'},
            ],
            'PaymentMethod': [
                {'odoo_field_label': 'name', 'quickbook_field_label': 'Name'},
            ],
            'TaxCode': [
                {'odoo_field_label': 'name', 'quickbook_field_label': 'Name'},
                {'odoo_field_label': 'description', 'quickbook_field_label': 'Description'},
                {'odoo_field_label': 'amount', 'quickbook_field_label': 'RateValue'},
            ],
            'PurchaseOrder': [
                {'odoo_field_label': 'date_order', 'quickbook_field_label': 'TxnDate'},
                {'odoo_field_label': 'state', 'quickbook_field_label': 'POStatus'},
            ],
            'Payment': base_payment_fields,
            'BillPayment': base_payment_fields,
            'Employee': base_name_fields + [
                {'odoo_field_label': 'private_street', 'quickbook_field_label': 'Line1'},
                {'odoo_field_label': 'private_state_id', 'quickbook_field_label': 'CountrySubDivisionCode'},
                {'odoo_field_label': 'private_country_id', 'quickbook_field_label': 'Country'},
                {'odoo_field_label': 'private_city', 'quickbook_field_label': 'City'},
                {'odoo_field_label': 'private_zip', 'quickbook_field_label': 'PostalCode'},
                {'odoo_field_label': 'work_email', 'quickbook_field_label': 'PrimaryEmailAddr'},
                {'odoo_field_label': 'work_phone', 'quickbook_field_label': 'PrimaryPhone'},
                {'odoo_field_label': 'birthday', 'quickbook_field_label': 'BirthDate'},
                {'odoo_field_label': 'comment', 'quickbook_field_label': 'Notes'},
                {'odoo_field_label': 'gender', 'quickbook_field_label': 'Gender'},
            ],
            'Department': [
                {'odoo_field_label': 'name', 'quickbook_field_label': 'Name'},
            ],
        }

        # Fetch the static mappings for the model
        static_mappings = static_mappings_dict.get(model_name, [])

        # Loop through static mappings and create field mappings
        for mapping in static_mappings:
            # Find Odoo and QuickBooks field labels in the mapper model
            odoo_field = mapper_model.search(
                [('internal_name', '=', mapping['odoo_field_label']), ('system_name', '=', 'Odoo')], limit=1)
            quickbook_field = mapper_model.search(
                [('internal_name', '=', mapping['quickbook_field_label']), ('system_name', '=', 'QuickBooks')],
                limit=1)

            # Check if both fields exist
            if odoo_field and quickbook_field:
                field_mapping_record = self.env[mapper_lines_field].search(
                    [('odoo_fields_label', '=', odoo_field.id), ('quickbook_fields_label', '=', quickbook_field.id),
                     (mapper_id_field, '=', instance_id.id)], limit=1)
                # Create a new field mapping in oqb.coa.lines
                if not field_mapping_record:
                    field_mapping_record = self.env[mapper_lines_field].create({
                        'odoo_fields_label': odoo_field.id,
                        'quickbook_fields_label': quickbook_field.id,
                        mapper_id_field: instance_id.id
                    })
        if model_name in ['Account', 'Estimate', 'PurchaseOrder', 'Item', 'Employee']:
            if model_name == 'Account':
                if not instance_id.odoo_coa_dropdown_mapping:
                    odoo_account_dropdown_mapping = {
                        "account_type": {
                            "asset_receivable": "Accounts Receivable",
                            "liability_payable": "Accounts Payable",
                            "asset_cash": "Bank",
                            "liability_credit_card": "Credit Card",
                            "asset_current": "Other Current Asset",
                            "asset_non_current": "Other Asset",
                            "asset_fixed": "Fixed Asset",
                            "liability_current": "Other Current Liability",
                            "liability_non_current": "Long Term Liability",
                            "equity": "Equity",
                            "income": "Income",
                            "income_other": "Other Income",
                            "expense": "Expense",
                            "expense_depreciation": "Other Expense",
                            "expense_direct_cost": "Cost of Goods Sold"
                        }
                    }
                    instance_id.odoo_coa_dropdown_mapping = json.dumps(odoo_account_dropdown_mapping, indent=4)
                if not instance_id.quickbook_coa_dropdown_mapping:
                    quickbook_account_dropdown_mapping = {
                        "AccountType": {
                            "Accounts Receivable": "asset_receivable",
                            "Accounts Payable": "liability_payable",
                            "Bank": "asset_cash",
                            "Credit Card": "liability_credit_card",
                            "Other Current Asset": "asset_current",
                            "Other Asset": "asset_non_current",
                            "Fixed Asset": "asset_fixed",
                            "Other Current Liability": "liability_current",
                            "Long Term Liability": "liability_non_current",
                            "Equity": "equity",
                            "Income": "income",
                            "Other Income": "income_other",
                            "Expense": "expense",
                            "Other Expense": "expense_depreciation",
                            "Cost of Goods Sold": "expense_direct_cost"
                        }
                    }
                    instance_id.quickbook_coa_dropdown_mapping = json.dumps(quickbook_account_dropdown_mapping,
                                                                            indent=4)
            if model_name == 'Estimate':
                if not instance_id.odoo_sale_order_dropdown_mapping:
                    odoo_sale_order_dropdown_mapping = {
                        "state": {
                            "draft": "Pending",
                            "sent": "Accepted",
                            "sale": "Closed",
                            "cancel": "Rejected"
                        }
                    }
                    instance_id.odoo_sale_order_dropdown_mapping = json.dumps(odoo_sale_order_dropdown_mapping,
                                                                              indent=4)
                if not instance_id.quickbook_sale_order_dropdown_mapping:
                    quickbook_sale_order_dropdown_mapping = {
                        "TxnStatus": {
                            "Pending": "draft",
                            "Accepted": "sent",
                            "Closed": "sale",
                            "Rejected": "cancel"
                        }
                    }
                    instance_id.quickbook_sale_order_dropdown_mapping = json.dumps(
                        quickbook_sale_order_dropdown_mapping, indent=4)
            if model_name == 'Item':
                if not instance_id.odoo_product_dropdown_mapping:
                    odoo_product_dropdown_mapping = {
                        "type": {
                            "service": "Service",
                            "consu": "Inventory",
                        }
                    }
                    instance_id.odoo_product_dropdown_mapping = json.dumps(odoo_product_dropdown_mapping, indent=4)
                if not instance_id.quickbook_product_dropdown_mapping:
                    quickbook_product_dropdown_mapping = {
                        "Type": {
                            "Service": "service",
                            "NonInventory": "service",
                            "Inventory": "consu",
                        }
                    }
                    instance_id.quickbook_product_dropdown_mapping = json.dumps(quickbook_product_dropdown_mapping,
                                                                                indent=4)
            if model_name == 'Employee':
                if not instance_id.odoo_employee_dropdown_mapping:
                    odoo_employee_dropdown_mapping = {
                                "gender": {
                                    "male": "Male",
                                    "female": "Female"
                                }
                            }
                    instance_id.odoo_employee_dropdown_mapping = json.dumps(odoo_employee_dropdown_mapping, indent=4)
                if not instance_id.quickbook_employee_dropdown_mapping:
                    quickbook_employee_dropdown_mapping = {
                            "Gender": {
                                "Male": "male",
                                "Female": "female"
                            }
                        }
                    instance_id.quickbook_employee_dropdown_mapping = json.dumps(quickbook_employee_dropdown_mapping,
                                                                                indent=4)
            if model_name == 'PurchaseOrder':
                if not instance_id.odoo_purchase_order_dropdown_mapping:
                    odoo_purchase_order_dropdown_mapping = {
                        "state": {
                            "draft": "Open",
                            "purchase": "Closed",
                        }
                    }
                    instance_id.odoo_purchase_order_dropdown_mapping = json.dumps(odoo_purchase_order_dropdown_mapping,
                                                                                  indent=4)
                if not instance_id.quickbook_purchase_order_dropdown_mapping:
                    quickbook_purchase_order_dropdown_mapping = {
                        "POStatus": {
                            "Open": "draft",
                            "Closed": "purchase"
                        }
                    }
                    instance_id.quickbook_purchase_order_dropdown_mapping = json.dumps(
                        quickbook_purchase_order_dropdown_mapping,
                        indent=4)

    def fetch_quickbooks_data(self, current_instance, model_name, query):
        """
        Fetch data from a QuickBooks API endpoint for a given model.

        api_token: QuickBooks API token
        company_id: QuickBooks company ID
        base_url: Base API URL for QuickBooks
        model_name: QuickBooks model to query
        start_position: Start position for the query (default: 0)
        max_results: Maximum results to fetch (default: 1)
        minor_version: API minor version (default: 73)
        return: Response data from the QuickBooks API
        """
        try:
            api_token, pagination_size, base_url, minor_version, quickbook_company_id, odoo_company_id = self.get_oqb_instance_data(
                current_instance)

            if not api_token or not quickbook_company_id or not base_url or not model_name:
                raise ValueError("Missing required arguments: api_token, company_id, base_url, or model_name")

            # Build the query and endpoint
            endpoint = f"{base_url}/{quickbook_company_id}/query?query={query}&minorversion={minor_version}"

            # Prepare headers
            headers = self.get_headers(api_token)

            # Make the GET request
            response = requests.get(endpoint, headers=headers, data={})

            return response
        except Exception as e:
            error_msg = _("An error occurred while fetching quickbook data: %s") % str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while fetching quickbook data'
            operation = f'Import Quickbook Data'
            self.env['oqb.dry.mixin'].exception_log_error(error_msg, '', description, '', '',
                                                          operation, 'manually', current_instance.name, error_type)
            return None

    def extract_nested_fields(self, parent_field_name, nested_field_value, instance_name, system_name):
        """
        Extract nested fields from a dictionary and prepare them for processing.

        :param parent_field_name: The name of the parent field
        :param nested_field_value: The dictionary containing nested fields
        :param instance_name: Name of the QuickBooks instance
        :param system_name: System name (e.g., QuickBooks)
        :return: A list of dictionaries representing nested fields
        """
        nested_fields = []
        for field_name, field_value in nested_field_value.items():
            nested_fields.append({
                'label_name': f"{parent_field_name}.{field_name}",
                'field_type': type(field_value).__name__,
                'quickbook_instance_name': instance_name,
                'system_name': system_name,
                'internal_name': field_name,
                'field_definition': nested_field_value
            })
        return nested_fields

    def fetch_company_info(self, instance_id, operation, parameter):
        try:
            # Fetch instance data
            access_token, pagination_size, base_api_url, minor_version, quickbook_company_id, odoo_company_id = \
            self.env[
                'oqb.dry.mixin'].get_oqb_instance_data(instance_id)

            # Construct API URL based on the parameter
            if parameter == 'companyinfo':
                company_info_url = f"{base_api_url}/{quickbook_company_id}/{parameter}/{quickbook_company_id}?minorversion={minor_version}"
            else:
                query = f"select * from {parameter}"
                company_info_url = f"{base_api_url}/{quickbook_company_id}/query?query={query}&minorversion={minor_version}"

            # Get headers
            headers = self.env['oqb.dry.mixin'].get_headers(access_token)

            payload = ""
            # Make a GET request to the API endpoint
            response = requests.get(company_info_url, data=payload, headers=headers)
            # Handle response
            response_data = self.env['oqb.instance'].handle_response(
                response, payload, '', '', '', '', 'get', operation, 'manually', instance_id
            )
            return response_data

        except Exception as e:
            error_msg = _("An error occurred while fetching company info: %s") % str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while fetching company info'
            operation = f'Import Company Info'
            self.env['oqb.dry.mixin'].exception_log_error(error_msg, '', description, '', '',
                                                          operation, 'manually', instance_id.name, error_type)
            return None

    def get_timezone(self, country_code, state_code=None):
        """
        Get timezone for a country and optional state using Odoo data.
        :param country_code: ISO code of the country (e.g., 'US', 'IN')
        :param state_code: Subdivision or state code (e.g., 'CA', 'GJ')
        :return: Timezone name or None if not found.
        """
        # Search for the country using the country code
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        if not country:
            return None, None
        # If a state code is provided, refine the search for the state
        if state_code:
            state = self.env['res.country.state'].search([
                ('code', '=', state_code), ('country_id', '=', country.id)], limit=1)
            if state and country:
                return (state.name if state else None), country.name

        return None, country.name

        # ----------------------------- Fetch Last Sync Date ---------------------------- #

    def last_odoo_sync_date_common(self, last_sync_date_field):
        # Set a temporary variable to store the current UTC time at the start of the function
        current_utc_time = datetime.utcnow()

        user_timezone = self.env.user.tz or 'UTC'

        # Get the current IST time
        now_ist = datetime.now(pytz.timezone(user_timezone))

        # Convert IST time to UTC time
        now_utc = now_ist.astimezone(pytz.utc)
        last_sync_date = last_sync_date_field
        if not last_sync_date:
            last_sync_date = now_utc.replace(tzinfo=None)
        return last_sync_date, current_utc_time

        # ----------------------------- Fetch Last Sync Date ---------------------------- #

    from datetime import datetime
    import pytz

    def last_sync_date_common(self, last_sync_date_field, current_instance):
        """
        Converts and returns the last_sync_date in QuickBooks-compatible time zone format.

        Args:
            last_sync_date_field (datetime): The last synchronization date.

        Returns:
            tuple: (last_sync_date in QuickBooks format, current UTC time in QuickBooks format)
        """
        # Set a temporary variable to store the current UTC time at the start of the function
        last_sync_date, current_utc_time = self.last_odoo_sync_date_common(last_sync_date_field)

        # # Convert the last sync date to the user's timezone
        operation = "Fetch User Time Zone"
        response_data = self.fetch_company_info(current_instance, operation, 'companyinfo')
        timezone = current_instance.quickbook_time_zone
        # Convert to QuickBooks-compatible time zone format (e.g., Pacific Time)
        quickbooks_tz = pytz.timezone(timezone)  # Example: Pacific Time
        last_sync_date_qb = last_sync_date.astimezone(quickbooks_tz)

        # Format the date in QuickBooks-compatible format
        qb_date_format = "%Y-%m-%dT%H:%M:%S%z"
        last_sync_date_qb_formatted = last_sync_date_qb.strftime(qb_date_format)

        # Insert a colon in the timezone offset to match QuickBooks format
        last_sync_date_qb_formatted = (
                last_sync_date_qb_formatted[:-2] + ':' + last_sync_date_qb_formatted[-2:]
        )

        return last_sync_date_qb_formatted, current_utc_time

    # ------------------------ Get Field Lines Data Based On Field Model Name ---------------- #

    def get_fields_lines_data(self, field_model_name, instance_id):
        """
        Get field lines data based on the field model name and current instance ID.

        Args:
            field_model_name (str): The name of the model containing field mappings between Quickbook and Odoo.
            instance_id (recordset): The instance ID of the Quickbook instance.

        Returns:
            recordset: The field lines data.
        """
        FIELD_MODEL_MAPPER = {
            'oqb.customer.lines': 'customer_mapper_id',
            'oqb.coa.lines': 'coa_mapper_id',
            'oqb.product.lines': 'product_mapper_id',
            'oqb.saleorder.lines': 'sale_order_mapper_id',
            'oqb.invoice.lines': 'invoice_mapper_id',
            'oqb.cpt.lines': 'cpt_mapper_id',
            'oqb.vendor.lines': 'vendor_mapper_id',
            'oqb.pco.lines': 'pco_mapper_id',
            'oqb.pcb.lines': 'pcb_mapper_id',
            'oqb.vpt.lines': 'vpt_mapper_id',
            'oqb.employee.lines': 'employee_mapper_id',
            'oqb.dpt.lines': 'dpt_mapper_id',
            'oqb.refund.lines': 'refund_mapper_id',
            'oqb.cdt.lines': 'credit_note_mapper_id',
            'oqb.pyt.lines': 'pyt_mapper_id',
            'oqb.pym.lines': 'pym_mapper_id',
            'oqb.atx.lines': 'atx_mapper_id',
        }

        # Get the appropriate mapper field name based on the field_model_name
        mapper_field_name = FIELD_MODEL_MAPPER.get(field_model_name)
        if not mapper_field_name:
            raise ValueError(f"No mapper field name found for field model name: {field_model_name}")

        # Search for field lines data using the dynamically determined mapper field name
        fields_lines_data = self.env[field_model_name].search([(mapper_field_name, '=', instance_id.id)])
        return fields_lines_data

    # ------------------------------- Get Instance Data ---------------------------- #

    def get_oqb_instance_data(self, current_instance):
        access_token = current_instance.access_token
        pagination_size = current_instance.pagination_size
        api_url = current_instance.base_api_url
        minor_version = current_instance.minor_version
        quickbook_company_id = current_instance.company_id
        odoo_company_id = current_instance.company_name.id
        return access_token, pagination_size, api_url, minor_version, quickbook_company_id, odoo_company_id

    # -------------------------- Integration Direction Based On Logger Name ------------------- #
    def get_module_and_direction(self, logger_name, model_name):
        """
            Determines the module name and record direction based on the logger and model names.

            Args:
                logger_name (str): The name of the logger (e.g., 'contact', 'account').
                model_name (str): The model name in Odoo or Quickbook.

            Returns:
                tuple: A tuple containing (module_name, record_direction).
        """
        module_mapping = {
            'chart of account': 'chart of account',
            'customer': 'customer',
            'sales orders': 'sales orders',
            'invoice': 'invoices',
            'credit note': 'credit note',
            'customer payment': 'customer payment',
            'product': 'products',
            'vendor': 'vendors',
            'purchase order': 'purchase order',
            'purchase bill': 'purchase bill',
            'refund': 'refund',
            'vendor payment': 'vendor payment',
            'payment term': 'payment term',
            'payment method': 'payment method',
            'employee': 'employee',
            'department': 'department',
            'account tax': 'account tax',
        }

        if model_name == 'odoo':
            record_direction = 'qto'  # Quickbook to Odoo
        elif model_name == 'quickbook':
            record_direction = 'otq'  # Odoo to Quickbook
        else:
            record_direction = ''

        module_name = module_mapping.get(logger_name.lower(), '')

        return module_name, record_direction

    # ---------------------------- Method For Log Operation Created And Updated ------------------------- #

    def log_operation(self, logger_name, status_code, record_id, record_data, operation_type, model_name,
                      record_operation, instance_name, parent_name=None, parent_id=None):
        """
        Logs the operation performed on a record in Odoo.

        Args:
            logger_name (str): The name of the logger (e.g., 'contact', 'account').
            record_id (int): The ID of the record in Quickbook.
            record_data (dict): The data of the record being created or updated.
            operation_type (str): The type of operation performed ('create' or 'update').
            model_name (str): The name of the model in Odoo where the record is being created or updated.
            parent_name (str, optional): The name of the parent record, if any. Defaults to None.
            parent_id (int, optional): The ID of the parent record, if any. Defaults to None.

        Returns:
            None
        """

        logger_name_capitalize = logger_name.capitalize()
        if parent_name == None and parent_id == None:
            if operation_type == 'create':
                operation = f'Create {logger_name_capitalize}'
                description = f'{logger_name_capitalize} created successfully in {model_name}.Quickbook {logger_name_capitalize} ID: {record_id}'
                response_payload = f'{logger_name_capitalize} created successfully'
            else:
                operation = f'Update {logger_name_capitalize}'
                description = f'{logger_name_capitalize} updated successfully in {model_name}. Quickbook {logger_name_capitalize} ID: {record_id}'
                response_payload = f'{logger_name_capitalize} updated successfully'
        else:
            if operation_type == 'create':
                operation = f'Create {logger_name_capitalize}'
                description = f'{logger_name_capitalize} created successfully in {model_name}. Quickbook {logger_name_capitalize} ID: {record_id}, Associated {parent_name.capitalize()} ID: {parent_id}'
                response_payload = f'{logger_name_capitalize} created successfully'
            else:
                operation = f'Update {logger_name_capitalize}'
                description = f'{logger_name_capitalize} updated successfully in {model_name}. Quickbook {logger_name_capitalize} ID: {record_id}, Associated {parent_name.capitalize()} ID: {parent_id}'
                response_payload = f'{logger_name_capitalize} updated Successfully'

        module_name, record_direction = self.get_module_and_direction(logger_name, model_name)

        self.env['oqb.logger'].create_oqb_logger(
            '', status_code, record_direction, module_name, record_id, description, record_data,
            response_payload, operation, 'resolve', 'success', record_operation, instance_name
        )

    # ---------------- Method For Odoo to Quickbook Log Operation Created And Updated  ------------ #

    def odoo_to_quickbook_log_operation(self, logger_name, status_code, record_id, record_data, operation_type,
                                        model_name, response_payload, record_operation, instance_name, parent_name=None,
                                        parent_id=None):
        """
        Logs the operation performed on a record in Odoo.

        Args:
            logger_name (str): The name of the logger (e.g., 'contact', 'account').
            record_id (int): The ID of the record in Quickbook.
            record_data (dict): The data of the record being created or updated.
            operation_type (str): The type of operation performed ('create' or 'update').
            model_name (str): The name of the model in Odoo where the record is being created or updated.
            parent_name (str, optional): The name of the parent record, if any. Defaults to None.
            parent_id (int, optional): The ID of the parent record, if any. Defaults to None.

        Returns:
            None
        """
        logger_name_capitalize = logger_name.capitalize()
        description = operation = resolve_status = None
        if parent_name == None and parent_id == None:
            if operation_type == 'insert':
                operation = f"{logger_name_capitalize} Batch Creation"
                description = f"{logger_name_capitalize} created successfully in Quickbook. Odoo {logger_name_capitalize} ID: {record_id}"
                resolve_status = 'success'
            if operation_type == 'update':
                operation = f"{logger_name_capitalize} Batch Updation"
                description = f"{logger_name_capitalize} updated successfully in Quickbook. Odoo {logger_name_capitalize} ID: {record_id}"
                resolve_status = 'success'
            elif operation_type == 'invalid_data':
                operation = f"{logger_name_capitalize} Batch Creation/Updation"
                description = f"{logger_name_capitalize} have not been created/updated successfully. Odoo {logger_name_capitalize} ID: {record_id}"
                resolve_status = 'error'
        else:
            if operation_type == 'record updated':
                operation = f"{parent_name.capitalize()} associated {logger_name} updated successfully in Quickbook"
                description = f'{logger_name_capitalize} updated successfully in {model_name}. Odoo {logger_name_capitalize} ID: {record_id}, Associated {parent_name.capitalize()} ID: {parent_id}'
                resolve_status = 'success'
            elif operation_type == 'record added':
                operation = f"{parent_name.capitalize()} associated {logger_name} created successfully in Quickbook"
                description = f'{logger_name_capitalize} created successfully in {model_name}. Odoo {logger_name_capitalize} ID: {record_id}, Associated {parent_name.capitalize()} ID: {parent_id}'
                resolve_status = 'success'

        module_name, record_direction = self.get_module_and_direction(logger_name, model_name)

        self.env['oqb.logger'].create_oqb_logger(
            '', status_code, record_direction, module_name, record_id, description, record_data,
            response_payload, operation, 'resolve', resolve_status, record_operation, instance_name)

        # ----------------------------------- Method For Log Operation Warning Message ------------------------- #

    def log_operation_warning(self, logger_name, description, operation, model_name, request_payload, record_id,
                              record_operation, instance_name):
        """
        Logs the operation performed on a record in Odoo.

        Args:
            logger_name (str): The name of the logger (e.g., 'contact', 'account').
            record_id (int): The ID of the record in Quickbook.
            record_data (dict): The data of the record being created or updated.
            operation_type (str): The type of operation performed ('create' or 'update').
            model_name (str): The name of the model in Odoo where the record is being created or updated.
            parent_name (str, optional): The name of the parent record, if any. Defaults to None.
            parent_id (int, optional): The ID of the parent record, if any. Defaults to None.

        Returns:
            None
        """

        module_name, record_direction = self.get_module_and_direction(logger_name, model_name)

        self.env['oqb.logger'].create_oqb_logger(
            '', '', record_direction, module_name, record_id, description, request_payload,
            '', operation, 'pending', 'warning', record_operation, instance_name
        )

    # -------------------------------------- Method To Create Exception Error Logger ----------------------- #

    def exception_log_error(self, error_details, logger_name, description, model_name, record_id,
                            operation, operation_type, instance_name, error_type='Exception Error'):
        """
        Logs an error in the QuickbookLogger.

        Args:
            error_details (str): The details of the error.
            logger_name (str): The name of the logger (e.g., 'contact', 'account', 'lead', 'deal').
            error_type (str): The type of the error (default is 'Exception Error').
            module_name (str): The name of the module where the error occurred (default is 'contacts').

        Returns:
            None
        """
        module_name, record_direction = self.get_module_and_direction(logger_name, model_name)
        self.env['oqb.logger'].create_oqb_logger(
            error_details, error_type, record_direction, module_name, record_id, description, '', '', operation,
            'pending', 'error', operation_type, instance_name)

    # ------------------- Logs an HttpLogError in the QuickbookLogger ------------- #

    def http_log_error(self, error_details, logger_name, description, payload, response, model_name, record_id
                       , operation, operation_type, instance_name, error_type='Http Error'):
        """
        Logs an HttpLogError in the QuickbookOdooLogger.

        Args:
            error_details (str): The details of the error.
            logger_name (str): The name of the logger (e.g., 'contact', 'company', 'lead', 'deal').
            description (str): A description of the error.
            payload (dict): The payload data sent during the HTTP request.
            response (str): The response received from the HTTP request.
            error_type (str, optional): The type of the error (default is 'Exception Error').

        Returns:
            None
        """
        module_name, record_direction = self.get_module_and_direction(logger_name, model_name)
        self.env['oqb.logger'].create_oqb_logger(
            error_details, error_type, record_direction, module_name, record_id, description, payload, response,
            operation, 'pending', 'error', operation_type, instance_name)

    # ------------------------- Schedular Logger Function --------------------------------- #
    def scheduler_run_successfully_log(self, logger_name, operation_type, model_name, instance_name):
        module_name, record_direction = self.get_module_and_direction(logger_name, model_name)
        logger_name_capitalize = logger_name.capitalize()
        operation_type_capitalize = operation_type.capitalize()
        schedular_direction = 'Quickbook to Odoo' if model_name == 'odoo' else 'Odoo to Quickbook'
        operation = f"Create/Update {logger_name_capitalize} in {model_name.capitalize()}"
        description = f"{logger_name_capitalize} {operation_type_capitalize} Run Successfully from {schedular_direction}"
        request_payload = f"Run {logger_name_capitalize} {operation_type_capitalize} from {schedular_direction}"
        response_payload = f"{logger_name_capitalize} {operation_type_capitalize} Run Successfully"

        self.env['oqb.logger'].create_oqb_logger(
            '', '', record_direction, module_name, '', description, request_payload,
            response_payload, operation, 'resolve', 'info', operation_type, instance_name)

    # ----------------------------- Get Field Mapping ------------------------ #
    def get_field_mapping(self, current_instance, field_model_name, dropdown_mapping_field):
        """
        Retrieves the field mapping between Quickbook and Odoo based on the provided parameters.

        Args:
            current_instance (object): The current instance object.
            field_model_name (str): The name of the model containing field mappings.
            dropdown_mapping_field (str): The name of the field containing dropdown mapping information.

        Returns:
            dict: A dictionary containing the field mappings.
        """
        field_mapping = {}
        dropdown_mapping = {}

        dropdown_field = getattr(current_instance, dropdown_mapping_field, None)

        if dropdown_field:
            dropdown_mapping = json.loads(dropdown_field)

        fields_lines_data = self.get_fields_lines_data(field_model_name, current_instance)
        for data in fields_lines_data:
            quickbook_field_data = data['quickbook_fields_label']
            odoo_field_data = data['odoo_fields_label']
            quickbook_internal_name = quickbook_field_data.internal_name
            odoo_internal_name = odoo_field_data.internal_name
            field_mapping[quickbook_internal_name] = odoo_internal_name

        return field_mapping, dropdown_mapping

    def quickbook_to_odoo_map_fields(self, record, current_instance, field_model_name, dropdown_mapping_field,
                                     record_id,
                                     logger_name, operation_type):
        """
        Map Quickbook fields to Odoo fields using the provided mappings.

        Args: 'quickbookinstance.accounts.lines'
            record (dict): A dictionary containing Quickbook record data.
            instance_id (str): The Quickbook instance ID.
            field_model_name (str): The name of the model containing field mappings between Quickbook and Odoo.
            dropdown_mapping_field (str): The name of the field in `instance_id` containing dropdown mapping information.
        Returns:
            dict: A dictionary containing mapped data for Odoo fields.
        """
        try:
            record_data = {}
            field_mapping, dropdown_mapping = self.get_field_mapping(current_instance, field_model_name,
                                                                     dropdown_mapping_field)

            if not field_mapping:
                description = f"Field Mapping is required for {logger_name.capitalize()}"
                operation = f'{logger_name.capitalize()} Record Sync Quickbook to Odoo'
                self.log_operation_warning(logger_name, description, operation, 'odoo', '', record_id,
                                           operation_type, current_instance.name)
                return record_data, None, False, False, False, False
            records = record if isinstance(record, list) else [record]
            for record in records:
                is_country_missing, country_name, is_state_missing, state_name = False, None, False, None

                for quickbook_internal_name, odoo_label_name in field_mapping.items():

                    if quickbook_internal_name == 'CountrySubDivisionCode':
                        if 'BillAddr' in record and 'CountrySubDivisionCode' in record['BillAddr']:
                            record_field_data = record['BillAddr']['CountrySubDivisionCode']
                        elif 'PrimaryAddr' in record and 'CountrySubDivisionCode' in record['PrimaryAddr']:
                            record_field_data = record['PrimaryAddr']['CountrySubDivisionCode']
                        else:
                            record_field_data = None  # Default value if the field is not found
                    elif quickbook_internal_name == 'Country':
                        if 'BillAddr' in record and 'Country' in record['BillAddr']:
                            record_field_data = record['BillAddr']['Country']
                        elif 'PrimaryAddr' in record and 'Country' in record['PrimaryAddr']:
                            record_field_data = record['PrimaryAddr']['Country']
                        else:
                            record_field_data = None
                    elif quickbook_internal_name == 'PrimaryEmailAddr':
                        if 'PrimaryEmailAddr' in record and 'Address' in record['PrimaryEmailAddr']:
                            record_field_data = record['PrimaryEmailAddr']['Address']
                        else:
                            record_field_data = None
                    elif quickbook_internal_name == 'PrimaryPhone':
                        if 'PrimaryPhone' in record and 'FreeFormNumber' in record['PrimaryPhone']:
                            record_field_data = record['PrimaryPhone']['FreeFormNumber']
                        else:
                            record_field_data = None
                    elif quickbook_internal_name == 'FreeFormNumber':
                        if 'Mobile' in record and 'FreeFormNumber' in record['Mobile']:
                            record_field_data = record['Mobile']['FreeFormNumber']
                        else:
                            record_field_data = None
                    elif quickbook_internal_name in ['Line1', 'Line2', 'City', 'PostalCode']:
                        if 'BillAddr' in record and quickbook_internal_name in record['BillAddr']:
                            record_field_data = record['BillAddr'][quickbook_internal_name]
                        else:
                            record_field_data = None
                    elif quickbook_internal_name == 'WebAddr':
                        if 'WebAddr' in record and 'URI' in record['WebAddr']:
                            record_field_data = record['WebAddr']['URI']
                        else:
                            record_field_data = None
                    else:
                        record_field_data = record.get(quickbook_internal_name, None)

                    record_data[odoo_label_name] = record_field_data
                    if isinstance(record_field_data, dict) and 'id' in record_field_data:
                        record_data[odoo_label_name] = record_field_data.get('id')
                    if record_field_data is None:
                        record_data[odoo_label_name] = None
                    if quickbook_internal_name == 'CountrySubDivisionCode' and any(
                            addr in record for addr in ['BillAddr', 'PrimaryAddr']) and record_field_data:
                        state_name = record_field_data
                        state = self.env['res.country.state'].search([
                            '|', ('name', '=', state_name), ('code', '=', state_name)
                        ], limit=1)
                        if state:
                            state_id = state.id
                            record_data[odoo_label_name] = state_id
                        else:
                            is_state_missing = True
                            record_data[odoo_label_name] = None
                    elif quickbook_internal_name == 'Country' and any(
                            addr in record for addr in ['BillAddr', 'PrimaryAddr']) and record_field_data:
                        country_name = record_field_data
                        country = self.env['res.country'].search(
                            ['|', ('name', '=', country_name), ('code', '=', country_name)],
                            limit=1)
                        if country:
                            country_id = country.id
                            record_data[odoo_label_name] = country_id
                        else:
                            is_country_missing = True
                            record_data[odoo_label_name] = None
                    elif odoo_label_name in ['email', 'Private Email'] and record_field_data:
                        record_data[odoo_label_name] = record_field_data
                    elif odoo_label_name in ['phone', 'Work Mobile'] and record_field_data:
                        record_data[odoo_label_name] = record_field_data
                    elif quickbook_internal_name in dropdown_mapping:
                        # Extract the 'id' from record_field_data if it is a dictionary
                        if isinstance(record_field_data, dict) and 'id' in record_field_data:
                            mapping_value = str(record_field_data.get('id'))
                        else:
                            mapping_value = str(record_field_data)
                        odoo_value = dropdown_mapping[quickbook_internal_name].get(mapping_value)
                        # record_data[odoo_label_name] = odoo_value
                        if odoo_value:
                            record_data[odoo_label_name] = odoo_value
                        elif not odoo_value and mapping_value and mapping_value != 'None':
                            description = (f'Please review and correct the dropdown configuration '
                                           f'{quickbook_internal_name} mapping as the selected {logger_name} does not '
                                           f'match the configured options. Once corrected the {logger_name} '
                                           f'{quickbook_internal_name}, and please try again. {logger_name} ID: {record_id}')
                            operation = f'{logger_name} sync Quickbook to Odoo'
                            self.log_operation_warning(logger_name, description, operation, 'odoo', record,
                                                       record_id, operation_type, current_instance.name)
                            continue

                mapped_data = self.prepare_mapped_data_quickbook_and_odoo(record_data)
                dynamic_fields_values_hash = self.calculate_hash(mapped_data)
                return record_data, dynamic_fields_values_hash, is_state_missing, is_country_missing, state_name, country_name
            return None, None, False, False, False, False
        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while filed mapping {logger_name} module'
            operation = f'Quickbook to Odoo Map Fields'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo', record_id,
                                                          operation, operation_type, current_instance.name, error_type)
            return None, None, False, False, False, False

    # ---------------------- Prepare the mapped data dictionary ------------------------- #

    @api.model
    def prepare_mapped_data_quickbook_and_odoo(self, mapped_data):
        """
               Prepares the mapped data dictionary by handling float-to-string conversions
               and stripping trailing zeros. Converts float fields to integers if they
               end with ".00" or ".0".

               Args:
                   temp_data (dict): The temporary data dictionary to be processed.

               Returns:
                   dict: The processed mapped data dictionary.
               """
        mapped_data = {key: value for key, value in mapped_data.items()}

        for key, value in mapped_data.items():
            if isinstance(value, float):
                mapped_data[key] = "{:.2f}".format(value).rstrip('0').rstrip('.')

        # Convert float fields to integers if they end with ".00"
        for key, value in mapped_data.items():
            if isinstance(value, str) and value.endswith('.00'):
                try:
                    mapped_data[key] = int(float(value))
                except ValueError:
                    pass  # Ignore conversion errors

            if isinstance(value, str) and value.endswith('.0'):
                try:
                    mapped_data[key] = int(float(value))
                except ValueError:
                    pass  # Ignore conversion errors

        return mapped_data

    # ----------------------------- Create Odoo Hash ----------------------- #
    def calculate_hash(self, mapped_data):
        """
            Calculates the SHA-256 hash of the concatenated values in the mapped data
            dictionary.

            Args:
                mapped_data (dict): The mapped data dictionary whose values will be
                                    concatenated and hashed.

            Returns:
                str: The SHA-256 hash of the concatenated values.
        """
        joined_value = ''.join(str(value) for value in mapped_data.values())
        dynamic_fields_values_hash = hashlib.sha256(str(joined_value).encode()).hexdigest()
        return dynamic_fields_values_hash

    # ----------------------------------- Common method for Odoo Hash and Quickbook ID ------------------------ #

    def get_sync_field_names(self, logger_name):
        """
        Returns the correct field names for odoo_hash and quickbook_id
        based on the logger name (like credit note, refund, etc.).
        """
        if logger_name == 'credit note':
            return 'odoo_credit_note_hash', 'quickbook_credit_note_id'
        elif logger_name == 'refund':
            return 'odoo_refund_hash', 'quickbook_refund_id'
        else:
            return 'odoo_hash', 'quickbook_id'

    # ---------------------------- Quickbook to Odoo Record Updated and Created Common Function -------------------------------- #

    def oqb_create_or_update_odoo_record(self, quickbook_record, odoo_record, record_data, dynamic_fields_values_hash,
                                         quickbook_record_id, quickbook_module_name,
                                         model_name, current_instance, odoo_bill_record, odoo_invoice_record,
                                         logger_name, operation_type, state_name, country_name, check_hash=True,
                                         is_state_missing=False, is_country_missing=False):
        """
        Creates or updates an Odoo record based on Quickbook record data and syncs related records if applicable.

        """
        operation_status = (None, None, None, None)
        try:
            if odoo_record:
                hash_field, quickbook_id_field = self.get_sync_field_names(logger_name)

                # Check if we need to update
                existing_hash = getattr(odoo_record, hash_field)

                if not check_hash or existing_hash != dynamic_fields_values_hash:
                    if logger_name in ['invoice', 'purchase bill', 'credit note', 'refund']:
                        if odoo_record.state == 'posted':
                            return ('no_update', quickbook_record_id, odoo_record.id, odoo_record)
                    if logger_name in ['customer payment', 'vendor payment']:
                        if odoo_record.state == 'paid':
                            return ('no_update', quickbook_record_id, odoo_record.id, odoo_record)
                    odoo_record.write(record_data)

                    if logger_name in ['customer payment', 'vendor payment'] and odoo_record.state != 'paid':
                        quickbook_payment_state = self.map_payment_state(quickbook_record)
                        if quickbook_payment_state == 'paid':
                            odoo_record.action_validate()  # Post the invoice (required to move to 'posted' state)
                            odoo_record.state = 'paid'
                        else:
                            odoo_record.action_draft()

                    odoo_record.env.cr.commit()
                    # Log state and country warnings only if necessary
                    if is_state_missing or is_country_missing:
                        self.log_missing_state_or_country(record_data, quickbook_record_id, logger_name, operation_type,
                        state_name, country_name, current_instance,is_state_missing,is_country_missing)
                    self.log_operation(logger_name, '', quickbook_record_id, record_data, 'update', 'odoo',
                                       operation_type, current_instance.name,
                                       None, None)
                    operation_status = ('update', quickbook_record_id, odoo_record.id, odoo_record)
                else:
                    operation_status = ('no_update', quickbook_record_id, odoo_record.id, odoo_record)
            else:
                if logger_name not in ['vendor payment', 'customer payment']:
                    if logger_name == 'chart of account':
                        acc_code = record_data.get('code_store')

                        if not acc_code:
                            warning_message = 'Code field is not mapped in Chart of Account Field Mapping'
                            self.env['oqb.dry.mixin'].log_operation_warning(
                                logger_name, warning_message,
                                f'{logger_name.capitalize()} Push to QuickBooks',
                                'quickbook', record_data, '',
                                operation_type, current_instance.name
                            )
                            return ('no_create', quickbook_record_id, '', '')

                        #  Search existing account by code
                        existing_account = self.env[model_name].search([('code_store', '=', acc_code)], limit=1)
                        if existing_account:
                            # Optional account type validation
                            qb_type = record_data.get('account_type')
                            if qb_type and existing_account.account_type != qb_type:
                                description = (
                                    f'Account code {acc_code} exists but account type mismatch '
                                    f'(Odoo: {existing_account.account_type}, QB: {qb_type})'
                                )
                                self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description,
                                'Chart of Account Sync', 'odoo',record_data, existing_account.id,
                                operation_type, current_instance.name)
                                return ('no_update', quickbook_record_id, existing_account.id, existing_account)

                            # ✅ Update existing account
                            existing_account.write(record_data)
                            existing_account.env.cr.commit()
                            odoo_record = existing_account
                            operation_status = ('update', quickbook_record_id, odoo_record.id, odoo_record)

                        else:
                            # ✅ Create new account
                            odoo_record = self.env[model_name].create(record_data)
                            odoo_record.env.cr.commit()
                            operation_status = ('create', quickbook_record_id, odoo_record.id, odoo_record)
                    else:
                        # 🔹 Normal create for other models
                        odoo_record = self.env[model_name].create(record_data)
                        odoo_record.env.cr.commit()
                        operation_status = ('create', quickbook_record_id, odoo_record.id, odoo_record)
                else:
                    is_customer = logger_name == 'customer payment'

                    payment_vals = {
                        'amount': record_data['amount'],
                        'payment_date': fields.Date.today(),
                        'journal_id': current_instance.oqb_bank_journal.id,
                        'payment_type': 'inbound' if is_customer else 'outbound',
                        'partner_type': 'customer' if is_customer else 'supplier',
                        'partner_id': record_data['partner_id'],
                        'communication': record_data['memo'],
                        'currency_id': record_data['currency_id'],
                    }

                    active_model = 'account.move'
                    active_ids = odoo_invoice_record.ids if is_customer else odoo_bill_record.ids

                    payment_wizard = self.env['account.payment.register'].with_context(
                        active_model=active_model,
                        active_ids=active_ids
                    ).create(payment_vals)

                    payment_result = payment_wizard.action_create_payments()

                    if payment_result:
                        payment_res_id = payment_result['res_id']
                        domain = [('id', '=', payment_res_id), ('memo', '=', record_data['memo'])]
                        odoo_payment_record = self.env['account.payment'].search(domain, limit=1)

                        odoo_payment_record.quickbook_id = record_data['quickbook_id']
                        odoo_payment_record.odoo_hash = record_data['odoo_hash']
                        odoo_payment_record.instance_name = record_data['instance_name']
                        odoo_payment_record.quickbook_sync_token = record_data['quickbook_sync_token']
                        odoo_payment_record.sync_to_quickbook = record_data['sync_to_quickbook']
                        odoo_payment_record.sync_to_quickbook = record_data['sync_to_quickbook']
                        odoo_payment_record.quickbook_payment_name = record_data['quickbook_payment_name']
                        # Only for vendor payments
                        if not is_customer and 'oqb_payment_type' in record_data:
                            odoo_payment_record.oqb_payment_type = record_data['oqb_payment_type']

                odoo_record.env.cr.commit()

                # Log state and country warnings only if necessary
                if is_state_missing or is_country_missing:
                    self.log_missing_state_or_country(record_data, quickbook_record_id, logger_name, operation_type,
                                                      state_name, country_name, current_instance,
                                                      is_state_missing, is_country_missing)
                self.log_operation(logger_name, '', quickbook_record_id, record_data, 'create', 'odoo', operation_type,
                                   current_instance.name, None,
                                   None)
                operation_status = ('create', quickbook_record_id, odoo_record.id, odoo_record)

            return operation_status

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create/Update Odoo {logger_name.capitalize()} Record'
            description = f'Error occurred while processing {logger_name} record Quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo',
                                                          quickbook_record_id, operation, operation_type,
                                                          current_instance.name, error_type)
            return operation_status

        # -------------------------------- Warning Log For State and Country Present in Odoo ----------------------- #

    def log_missing_state_or_country(self, record_data, quickbook_record_id, logger_name, operation_type, state_name,
            country_name, current_instance, is_state_missing=False, is_country_missing=False):
        """
        Logs warnings for missing or mismatched state and country during Quickbook to Odoo sync.

        Args:
            record_data (dict): The data being synced from Quickbook to Odoo.
            quickbook_record_id (str): The Quickbook record ID.
            logger_name (str): The name of the logger used for logging the warnings.
            is_state_missing (bool): Flag indicating if the state is missing or invalid.
            is_country_missing (bool): Flag indicating if the country is missing or invalid.
        """
        try:
            if is_state_missing:
                description = f"The state '{state_name}' specified in Quickbook does not match any state in Odoo. {logger_name.capitalize()} ID: {quickbook_record_id}"
                self.log_operation_warning(logger_name, description,
                                           f'{logger_name.capitalize()} Record Sync Quickbook to Odoo', 'odoo',
                                           record_data, quickbook_record_id, operation_type, current_instance.name)

            if is_country_missing:
                description = f"The country '{country_name}' specified in Quickbook does not match any country in Odoo. {logger_name.capitalize()} ID: {quickbook_record_id}"
                self.log_operation_warning(logger_name, description,
                                           f'{logger_name.capitalize()} Record Sync Quickbook to Odoo', 'odoo',
                                           record_data, quickbook_record_id, operation_type, current_instance.name)

        except Exception as e:
            error_details = str(e)
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name,
            "Error in State/Country Warning Log", 'odoo',quickbook_record_id,
            "Quickbook to Odoo Log", operation_type,current_instance.name, "Exception Error")

    # ------------------------------- Fetch Quickbook Records -------------------- #

    def fetch_data_from_quickbook(self, current_instance, last_sync_date_field, is_company,
                                  field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                                  operation_type, process_record_method, sync_date_field, last_id_field):
        """
        Generic method to fetch data from QuickBooks and process it in Odoo.
        """
        record_id = None
        try:
            last_sync_date, current_utc_time = self.env['oqb.dry.mixin'].last_sync_date_common(last_sync_date_field,
                                                                                               current_instance)
            access_token, pagination_size, base_api_url, minor_version, quickbook_company_id, odoo_company_id = \
                self.env['oqb.dry.mixin'].get_oqb_instance_data(current_instance)
            record_last_id = current_instance[last_id_field] or 0  # Default to 0 if not set
            # select_fields = self.env['oqb.dry.mixin'].get_quickbook_select_fields(field_model_name, current_instance,
            #                                                                       logger_name, operation_type)
            operation_status = None
            while True:
                # Check if record_last_id exists and adjust the query accordingly
                query = f"SELECT * FROM {module_name} where MetaData.LastUpdatedTime > '{last_sync_date}' and Id > '{record_last_id}' ORDERBY Id MAXRESULTS {pagination_size}"

                response = self.env['oqb.dry.mixin'].fetch_quickbooks_data(current_instance, module_name, query)
                operation = f'Get Quickbook {logger_name.capitalize()} Data'
                response_data = self.env['oqb.instance'].handle_response(response, {}, module_name, '', '', '', 'get',
                                                                         operation, 'manually', current_instance)

                if response_data:
                    batch_records = [record for record in response_data]
                    operation_status, quickbook_id = getattr(self, process_record_method)(batch_records,
                    current_instance,field_model_name,dropdown_field_mapping_name,is_company, module_name,
                    logger_name, operation_type,odoo_company_id,check_hash=True)
                    # Update the last record ID after processing
                    record_last_id = response_data[-1].get('Id') if isinstance(response_data[-1],
                                                                               dict) else response_data[-1].Id
                    _logger.info('record_last_id called....', record_last_id)
                    current_instance.write({last_id_field: record_last_id})
                    current_instance.env.cr.commit()

                    if len(response_data) < pagination_size:
                        break
                else:
                    break

            # Update sync date and reset the last record ID
            if last_sync_date and operation_status != 'no_field':
                current_instance.write({
                    sync_date_field: current_utc_time
                })
            # Always reset last_id_field to 0
            current_instance.write({
                last_id_field: 0
            })
            self.scheduler_run_successfully_log(logger_name, operation_type, 'odoo', current_instance.name)
        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while {operation_type} in odoo.'
            operation = f'Fetch {logger_name.capitalize()} Record From Quickbook'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'quickbook',
            record_id, operation, operation_type, current_instance.name,error_type)

    # ------------------------------- Process Quickbook Records Data -------------------- #

    def process_quickbook_record(self, batch_records, current_instance, field_model_name, dropdown_field_mapping_name,
                                 module_name, logger_name, operation_type, odoo_company_id, model_name, related_logger,
                                 search_domain, additional_fields=None, check_hash=True):
        """
        A reusable function to process QuickBooks records and create/update them in Odoo.
        """
        is_multi_company = self.env.user.is_multi_company
        quickbook_id, operation_status, odoo_journal, odoo_invoice_record, odoo_bill_record = None, None, None, None, None
        try:
            for quickbook_record in batch_records:
                quickbook_id = quickbook_record.get('Id')
                quickbook_sync_token = quickbook_record.get('SyncToken')
                invoice_balance, linked_txn = 0, []

                if logger_name == 'chart of account':
                    quickbook_account_code = quickbook_record.get('AcctNum')
                    if not quickbook_account_code:
                        if not related_logger:
                            description = f"Failed to create {related_logger} related {logger_name} in odoo. Account Number is required for {logger_name} record"
                        else:
                            description = f"Failed to create {related_logger} related  {logger_name} in odoo. Account Number is required for {logger_name} record"

                        operation = f'{logger_name.capitalize()} Record Sync Quickbook to Odoo'
                        self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'odoo',
                                                                        quickbook_record, quickbook_id, operation_type,
                                                                        current_instance.name)
                        continue

                partner_record_data, dynamic_fields_values_hash, is_state_missing, is_country_missing, state_name, country_name = \
                    self.env['oqb.dry.mixin'].quickbook_to_odoo_map_fields(
                        quickbook_record, current_instance, field_model_name, dropdown_field_mapping_name, quickbook_id,
                        logger_name, operation_type)

                if not partner_record_data:
                    operation_status = 'no_field'
                    break

                hash_field, quickbook_id_field = self.get_sync_field_names(logger_name)

                # Add common fields
                partner_record_data[quickbook_id_field] = quickbook_id
                partner_record_data['quickbook_sync_token'] = quickbook_sync_token
                partner_record_data[hash_field] = dynamic_fields_values_hash
                partner_record_data['sync_to_quickbook'] = True
                partner_record_data['instance_name'] = current_instance.id if logger_name in ['payment method', 'customer payment', 'vendor payment'] else current_instance.name

                if logger_name == 'vendor':
                    partner_record_data.update({'is_company': False, 'supplier_rank': 1})
                elif logger_name == 'customer':
                    partner_record_data['is_company'] = False
                # Company handling
                if logger_name not in ['payment method', 'customer payment', 'vendor payment',
                                                            'account tax']:
                    partner_record_data['company_ids' if logger_name == 'chart of account' else 'company_id'] = [
                        (6, 0, [odoo_company_id])] if logger_name == 'chart of account' else odoo_company_id
                if logger_name in ['chart of account', 'sales orders', 'invoice', 'purchase order',
                                   'credit note', 'purchase bill', 'refund', 'product', 'customer payment',
                                   'vendor payment']:
                    currency_ref = quickbook_record.get('CurrencyRef', {}).get('value')
                    if currency_ref:
                        currency_id = self.get_currency_id_from_quickbook(currency_ref, current_instance, logger_name,
                                      quickbook_id, quickbook_record,operation_type)
                        if currency_id:
                            partner_record_data['currency_id'] = currency_id

                # Add additional fields if provided
                if additional_fields:
                    partner_record_data.update(additional_fields)

                if logger_name in ['customer payment', 'vendor payment']:
                    invoice_balance = quickbook_record.get('Balance', 0)
                    linked_txn = quickbook_record.get('LinkedTxn', [])
                    partner_record_data.update({'quickbook_payment_name': quickbook_record.get('DocNumber')})

                if logger_name in ['sales orders', 'purchase order', 'customer payment', 'vendor payment']:
                    partner_record_data, odoo_invoice_record = self.process_quickbook_accounting_data(quickbook_record,
                        partner_record_data,logger_name,operation_type,current_instance,odoo_company_id,
                        check_hash,related_logger)
                    if not partner_record_data:
                        continue
                    if logger_name == 'sales orders':
                        quickbook_estimate_name = quickbook_record.get('DocNumber')
                        partner_record_data.update({'quickbook_sale_order_name': quickbook_estimate_name})
                    if logger_name == 'purchase order':
                        quickbook_purchase_order_name = quickbook_record.get('DocNumber')
                        partner_record_data.update({'quickbook_purchase_order_name': quickbook_purchase_order_name})
                    if logger_name == 'customer payment':
                        partner_record_data.update({'payment_type': 'inbound', 'partner_type': 'customer'})
                    elif logger_name == 'vendor payment':
                        partner_record_data, odoo_bill_record, state = self.process_vendor_payment_data(
                            quickbook_record, quickbook_id,
                            partner_record_data, logger_name, operation_type, current_instance)
                        if state == 'skip':
                            continue
                if logger_name in ['invoice', 'purchase bill', 'credit note', 'refund']:
                    invoice_balance = quickbook_record.get('Balance', 0)
                    linked_txn = quickbook_record.get('LinkedTxn', [])
                    partner_record_data.update({'quickbook_account_name': quickbook_record.get('DocNumber')})
                    partner_record_data, odoo_invoice_record = self.process_quickbook_accounting_data(quickbook_record,
                     partner_record_data,logger_name,operation_type,current_instance,odoo_company_id,check_hash,
                     related_logger)
                    if not partner_record_data:
                        continue
                    journal_mapping = {
                        'invoice': ('out_invoice', current_instance.oqb_sale_journal.id),
                        'purchase bill': ('in_invoice', current_instance.oqb_purchase_journal.id),
                        'credit note': ('out_refund', current_instance.oqb_sale_journal.id),
                        'refund': ('in_refund', current_instance.oqb_purchase_journal.id),
                    }
                    if logger_name in journal_mapping:
                        move_type, journal_id = journal_mapping[logger_name]
                        partner_record_data.update({'move_type': move_type, 'journal_id': int(journal_id)})

                if logger_name == 'payment method':
                    pty_method_name = quickbook_record.get('Name')
                    if pty_method_name:
                        partner_record_data.update({'code': pty_method_name.capitalize()})
                if logger_name == 'account tax' and partner_record_data:
                    partner_record_data = self.create_account_tax_rate(quickbook_record, partner_record_data,
                    current_instance, logger_name,operation_type, check_hash, odoo_company_id)
                    tax_groups = self.env['account.tax.group'].search([])
                    if partner_record_data:
                        # Create or update the Odoo record
                        # Check if partner_record_data is a list (i.e., multiple records)
                        if isinstance(partner_record_data, list):
                            for record_data in partner_record_data:
                                canadian_tax_groups = tax_groups.filtered(lambda g: g.country_id.code == 'CA')

                                if not canadian_tax_groups:
                                    description = f'Tax group with country code CA is not created in Odoo. Please create it first.'
                                    operation = f"Create/Update {model_name}"
                                    self.env['oqb.dry.mixin'].log_operation_warning(
                                        logger_name, description, operation, 'odoo',
                                        quickbook_record, quickbook_id, operation_type, current_instance.name
                                    )
                                    continue
                                else:
                                    tax_group_id = canadian_tax_groups[0].id
                                record_data.update({'quickbook_tax_code': quickbook_id, 'tax_group_id': tax_group_id,
                                                    'company_id': odoo_company_id})
                                search_domain = [
                                    ('quickbook_id', '=', record_data['quickbook_id']),
                                    ('instance_name', '=', current_instance.name),
                                    ('quickbook_tax_code', '=', record_data['quickbook_tax_code']),
                                ]

                                # Check for multi-company and append company condition only if enabled
                                if self.env.user.is_multi_company:
                                    search_domain.append(('company_id', '=', odoo_company_id))
                                odoo_record = self.env[model_name].search(search_domain, limit=1)

                                operation_status = self.env['oqb.dry.mixin'].oqb_create_or_update_odoo_record(
                                    quickbook_record,
                                    odoo_record, record_data, dynamic_fields_values_hash, quickbook_id, module_name,
                                    model_name, current_instance, '', '', logger_name, operation_type, state_name,
                                    country_name, check_hash, is_state_missing, is_country_missing)

                if logger_name == 'customer':
                    quickbook_email = quickbook_record.get('PrimaryEmailAddr', {}).get('Address', None)

                    odoo_record, email_exists_with_quickbook_id = self.search_record('res.partner', 'email',
                                                                                     quickbook_email, quickbook_id,
                                                                                     [('is_company', '=', False)])
                    # Additional check for contacts: avoid email duplication
                    if email_exists_with_quickbook_id:
                        if not related_logger:
                            description = (
                                f'The email ID {quickbook_email} is already associated with another {logger_name} with a '
                                f'quickbook ID. Please use a different email ID.')
                        else:
                            description = (
                                f'{related_logger} related {logger_name} email ID {quickbook_email} is already associated with another {logger_name} with a '
                                f'quickbook ID. Please use a different email ID.')
                        operation = f'{logger_name.capitalize()} sync Quickbook to Odoo'
                        self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'odoo',
                        quickbook_record, quickbook_id, operation_type,current_instance.name)
                        continue
                if logger_name == 'product':
                    partner_record_data, state = self.process_product_data(quickbook_record, quickbook_id,
                    partner_record_data, logger_name,operation_type, current_instance,odoo_company_id, check_hash)
                    if 'PurchaseCost' in quickbook_record:
                        partner_record_data.update({'standard_price': quickbook_record.get('PurchaseCost')})
                    # if quickbook_record['Type'] == 'Inventory':
                    #     partner_record_data['QtyOnHand'] = quickbook_record['QtyOnHand']
                    if state == 'skip':
                        continue

                if logger_name != 'account tax':

                    if logger_name not in ['payment method', 'customer payment', 'vendor payment']:
                        domain = list(search_domain)  # base domain
                        domain += [(quickbook_id_field, '=', quickbook_id), ('instance_name', '=', current_instance.name)]

                        if is_multi_company:
                            if logger_name == 'chart of account':
                                domain.append(('company_ids', '=', current_instance.company_name.id))
                            else:
                                domain.append(('company_id', '=', current_instance.company_name.id))

                        odoo_record = self.env[model_name].search(domain, limit=1)
                    else:
                        odoo_record = self.env[model_name].search(search_domain + [(quickbook_id_field, '=', quickbook_id),
                                      ('instance_name', '=', current_instance.id)], limit=1)

                    if partner_record_data:
                        # Create or update the Odoo record
                        operation_status = self.env['oqb.dry.mixin'].oqb_create_or_update_odoo_record(quickbook_record,
                        odoo_record,partner_record_data,dynamic_fields_values_hash,quickbook_id,module_name,model_name,
                        current_instance,odoo_bill_record,odoo_invoice_record,logger_name,operation_type,state_name,
                        country_name,check_hash,is_state_missing,is_country_missing)

                        status, odoo_quotation_id, odoo_id, odoo_record = operation_status
                        if status in ['create', 'update']:
                            if logger_name == 'sales orders':
                                self.create_odoo_order_line(quickbook_record, odoo_record, current_instance,
                                                            logger_name, 'sale.order.line', operation_type, check_hash,
                                                            odoo_company_id, invoice_balance, linked_txn)
                            if logger_name in ['invoice', 'purchase bill', 'credit note', 'refund']:
                                self.create_odoo_order_line(quickbook_record, odoo_record, current_instance,
                                                            logger_name, 'account.move.line', operation_type,
                                                            check_hash,
                                                            odoo_company_id, invoice_balance, linked_txn)
                            if logger_name == 'purchase order':
                                self.create_odoo_order_line(quickbook_record, odoo_record, current_instance,
                                                            logger_name, 'purchase.order.line', operation_type,
                                                            check_hash, odoo_company_id, invoice_balance, linked_txn)

            return operation_status, quickbook_id
        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create/Update Quickbook {logger_name.capitalize()} Record In Odoo'
            description = f'Error occurred while sending {logger_name} record Quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo', quickbook_id,
                                                          operation, operation_type, current_instance.name, error_type)
            return None, None

    # ------------------------------- Process Quickbook Product Data -------------------- #

    def process_product_data(self, quickbook_record, quickbook_id, partner_record_data, logger_name,
                             operation_type, current_instance, odoo_company_id, check_hash):
        status = None
        quickbook_sku_code = quickbook_record.get('Sku')
        odoo_record, product_code_exists_with_quickbook_id = self.search_record('product.template',
        'default_code', quickbook_sku_code,quickbook_id, [])
        # Additional check for contacts: avoid email duplication
        if product_code_exists_with_quickbook_id:
            description = (f'The product with the code "{quickbook_sku_code}" already exists in the system. Please '
                           f'use a unique product code.')
            operation = 'Product Sync Quickbook to Odoo'
            self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'odoo',
                                                            quickbook_record, quickbook_id, operation_type,
                                                            current_instance.name)
            return partner_record_data, 'skip'

        quickbook_income_account_id = quickbook_record.get('IncomeAccountRef', {}).get('value')

        if quickbook_income_account_id:
            quickbook_income_account, status = self.create_or_link_account_in_journal_entry_line(
                quickbook_income_account_id, current_instance, 'oqb.coa.lines',
                'quickbook_coa_dropdown_mapping', 'chart of account', operation_type,
                check_hash, odoo_company_id, logger_name)

            partner_record_data.update({'property_account_income_id': quickbook_income_account.id})

        quickbook_expense_account_id = quickbook_record.get('ExpenseAccountRef', {}).get('value')
        if quickbook_expense_account_id:
            quickbook_expense_account, status = self.create_or_link_account_in_journal_entry_line(
                quickbook_expense_account_id, current_instance, 'oqb.coa.lines',
                'quickbook_coa_dropdown_mapping', 'chart of account', operation_type,
                check_hash, odoo_company_id, logger_name)

            partner_record_data.update({'property_account_expense_id': quickbook_expense_account.id})

        return partner_record_data, status

    # ------------------------------- Process Quickbook Vendor Payment Data -------------------- #

    def process_vendor_payment_data(self, quickbook_record, quickbook_id, partner_record_data, logger_name,
                                    operation_type, current_instance):
        oqb_txn_id, oqb_txn_type = None, None
        partner_record_data.update({'payment_type': 'outbound', 'partner_type': 'supplier'})

        if 'PayType' in quickbook_record:
            oqb_payment_type = 'check' if quickbook_record.get('PayType') == 'Check' else 'credit card'
            partner_record_data.update({'oqb_payment_type': oqb_payment_type})
        if 'Line' in quickbook_record:
            lines = quickbook_record.get("Line", [])
            for line in lines:
                oqb_linked_txn = line.get("LinkedTxn", [])
                for txn in oqb_linked_txn:
                    oqb_txn_id = txn.get("TxnId")
                    oqb_txn_type = txn.get('TxnType')
                    continue

        quickbook_id_field = 'quickbook_refund_id' if oqb_txn_type == 'VendorCredit' else 'quickbook_id'

        if self.env.user.is_multi_company:
            odoo_invoice_record = self.env['account.move'].search([
                ('move_type', 'in', ['in_invoice', 'in_refund']), (quickbook_id_field, '=', str(oqb_txn_id)),
                ('company_id', '=', current_instance.company_name.id)], limit=1)
        else:
            odoo_invoice_record = self.env['account.move'].search([
                ('move_type', 'in', ['in_invoice', 'in_refund']), (quickbook_id_field, '=', str(oqb_txn_id)),
                ], limit=1)

        if not odoo_invoice_record:
            description = f"First create {logger_name} related bill in odoo and than link it to {logger_name.capitalize()}"
            operation = f'{logger_name.capitalize()} Record Sync Quickbook to Odoo'
            self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'odoo',
                                                            partner_record_data, quickbook_id, operation_type,
                                                            current_instance.name)
            return partner_record_data, odoo_invoice_record, 'skip'
        if odoo_invoice_record.state != 'posted':
            odoo_invoice_record.action_post()
        partner_record_data.update({'memo': odoo_invoice_record.name})
        return partner_record_data, odoo_invoice_record, 'success'


    ########### ---------------- Create Account Tax Rate ---------------- ###########

    def create_account_tax_rate(self, record, partner_data, current_instance,
                                logger_name, operation_type, check_hash, odoo_company_id):
        partner_data_list = []  # List to store individual partner data
        # Define keys to process
        tax_rate_lists = ['SalesTaxRateList', 'PurchaseTaxRateList']

        for rate_list_key in tax_rate_lists:
            if rate_list_key in record:
                odoo_tax_type = 'sale' if rate_list_key == 'SalesTaxRateList' else 'purchase'
                # Process each TaxRateDetail in the current list
                tax_rate_details = record.get(rate_list_key, {}).get('TaxRateDetail', [])
                for tax_detail in tax_rate_details:
                    sales_tax_value = tax_detail.get('TaxRateRef', {}).get('value')
                    if sales_tax_value:
                        # Fetch partner record for each TaxRateRef value
                        partner_record = self.env['oqb.dry.mixin'].fetch_quickbook_manual_record(
                            'TaxRate', sales_tax_value, current_instance, logger_name, operation_type, 'Id')
                        if partner_record and isinstance(partner_record, list):
                            tax_rate = partner_record[0].get('RateValue')
                            tax_rate_id = partner_record[0].get('Id')

                            # Create a new dictionary for each partner_data
                            new_partner_data = dict(partner_data)  # Clone the partner_data dictionary
                            new_partner_data.update({
                                'name': f"{new_partner_data['name']}({tax_rate})",
                                'quickbook_id': tax_rate_id,
                                'amount': tax_rate,
                                'type_tax_use': odoo_tax_type  # Add type (Sales or Purchase)
                            })
                            partner_data_list.append(new_partner_data)

        # Return updated partner_data
        return partner_data_list if partner_data_list else [partner_data]

    # ---------------- Check Existing Partner In Odoo By Email Or Odoo ID ---------------- #

    def search_record(self, model, search_field, search_value, quickbook_id, extra_domain=None):
        """
        Search for an existing record in Odoo by a specific field or Quickbook ID.

        Args:
            model (str): The model to search ('res.partner' or 'product.template').
            search_field (str): The field to search by (e.g., 'email' for customers or 'default_code' for products).
            search_value (str): The value of the search field (e.g., an email or default code).
            quickbook_id (int, optional): The Quickbook ID of the record.
            extra_domain (list, optional): Additional domain filters to apply.

        Returns:
            tuple: The found record and a boolean indicating if a Quickbook ID conflict is detected.
        """
        record, quickbook_id_conflict = False, False

        # Build the base domain
        domain = [('active', '=', True)]
        if extra_domain:
            domain += extra_domain

        # Search by the specific field if provided
        if search_value:
            search_domain = domain + [(search_field, '=', search_value)] + [('quickbook_id', '=', quickbook_id)]
            record = self.env[model].search(search_domain)
            if record:
                return record, quickbook_id_conflict
            else:
                search_domain = domain + [(search_field, '=', search_value)]
                record = self.env[model].search(search_domain, limit=1, order="quickbook_id ASC")

                # Check for Quickbook ID conflict
                if record and hasattr(record, 'quickbook_id') and record.quickbook_id:
                    quickbook_id_conflict = True
        else:
            # Search by Quickbook ID if no specific field value is provided
            search_domain = domain + [('quickbook_id', '=', quickbook_id)]
            record = self.env[model].search(search_domain, limit=1)

        return record, quickbook_id_conflict

    # --------------------- Quickbook Invoice State Mapped ------------------- #

    def map_quickbook_invoice_state(self, balance, linked_txn):
        """
        Map QuickBooks invoice data to Odoo invoice state.

        :param balance: Remaining balance on the invoice (float).
        :param linked_txn: List of linked transactions.
        :return: Odoo state as company_ids string.
        """
        state, payment_state = None, None
        if len(linked_txn) == 0 and balance > 0:
            state, payment_state = 'draft', None  # Invoice is created but not finalized or paid.
        elif any(txn.get('TxnType') == 'BillPaymentCheck' for txn in linked_txn) and balance > 0:
            state, payment_state = 'posted', 'partial'
        # partner_data.update({'state': 'posted', 'payment_state': 'partial'})  # Partial payment made.
        elif len(linked_txn) > 0 and balance == 0:
            state, payment_state = 'posted', 'paid'
            # partner_data.update({'state': 'posted', 'payment_state': 'paid'})  # Fully paid.

        return state, payment_state

    # -------------------------- Quickbook Payment State Mapped -------------------------- #

    def map_payment_state(self, qb_payment):
        # Extract relevant fields from QuickBooks payment
        linked_txn = []
        unapplied_amount = qb_payment.get('UnappliedAmt', 0)
        process_payment = qb_payment.get('ProcessPayment', False)
        if 'Line' in qb_payment and qb_payment['Line']:
            linked_txn = qb_payment.get('Line', [])[0].get('LinkedTxn', [])
        # total_amount = qb_payment.get('TotalAmt', 0)

        # Determine Odoo state
        if unapplied_amount > 0:
            return 'draft'  # Payment not fully applied
        elif linked_txn and unapplied_amount == 0:
            return 'paid'  # Payment fully processed and applied
        else:
            return 'draft'  # Default to draft if conditions are not met

    # ----------------------------- Process Quickbook Company and Contact Record -------------------------- #

    def process_quickbook_partner_record(self, batch_records, current_instance, field_model_name,
                                         dropdown_field_mapping_name,
                                         is_company, module_name, logger_name, operation_type, odoo_company_id,
                                         check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='res.partner', related_logger=None,
            search_domain=[('is_company', '=', is_company), ('active', '=', True)],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

        # ----------------------------- Process Quickbook Vendor Record -------------------------- #

    def process_quickbook_vendor_record(self, batch_records, current_instance, field_model_name,
                                        dropdown_field_mapping_name,
                                        is_company, module_name, logger_name, operation_type, odoo_company_id,
                                        check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='res.partner', related_logger=None,
            search_domain=[('is_company', '=', is_company), ('active', '=', True), ('supplier_rank', '>', 0)],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Chart of Account Record -------------------------- #
    def process_quickbook_account_record(self, batch_records, current_instance, field_model_name,
                                         dropdown_field_mapping_name,
                                         is_company, module_name, logger_name, operation_type, odoo_company_id,
                                         check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.account', related_logger=None, search_domain=[], additional_fields={},
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Product Record -------------------------- #

    def process_quickbook_product_record(self, batch_records, current_instance, field_model_name,
                                         dropdown_field_mapping_name,
                                         is_company, module_name, logger_name, operation_type, odoo_company_id,
                                         check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='product.template', related_logger=None, search_domain=[('active', '=', True)],
            additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Sale Order Record -------------------------- #

    def process_quickbook_sale_order_record(self, batch_records, current_instance, field_model_name,
                                            dropdown_field_mapping_name,
                                            is_company, module_name, logger_name, operation_type, odoo_company_id,
                                            check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='sale.order', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Invoice Record -------------------------- #

    def process_quickbook_invoice_record(self, batch_records, current_instance, field_model_name,
                                         dropdown_field_mapping_name,
                                         is_company, module_name, logger_name, operation_type, odoo_company_id,
                                         check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', related_logger=None, search_domain=[('move_type', '=', 'out_invoice')],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Credit Note Record -------------------------- #

    def process_quickbook_credit_note_record(self, batch_records, current_instance, field_model_name,
                                             dropdown_field_mapping_name,
                                             is_company, module_name, logger_name, operation_type, odoo_company_id,
                                             check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', related_logger=None, search_domain=[('move_type', '=', 'out_refund')],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Customer Payment Record -------------------------- #

    def process_quickbook_cpt_record(self, batch_records, current_instance, field_model_name,
                                     dropdown_field_mapping_name,
                                     is_company, module_name, logger_name, operation_type, odoo_company_id,
                                     check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.payment', related_logger=None, search_domain=[('partner_type', '=', 'customer')],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Purchase Order Record -------------------------- #

    def process_quickbook_purchase_order_record(self, batch_records, current_instance, field_model_name,
                                                dropdown_field_mapping_name,
                                                is_company, module_name, logger_name, operation_type, odoo_company_id,
                                                check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='purchase.order', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Purchase Bill Record -------------------------- #

    def process_quickbook_pcb_record(self, batch_records, current_instance, field_model_name,
                                     dropdown_field_mapping_name,
                                     is_company, module_name, logger_name, operation_type, odoo_company_id,
                                     check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', related_logger=None, search_domain=[('move_type', '=', 'in_invoice')],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Refund Record -------------------------- #

    def process_quickbook_refund_record(self, batch_records, current_instance, field_model_name,
                                        dropdown_field_mapping_name,
                                        is_company, module_name, logger_name, operation_type, odoo_company_id,
                                        check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', related_logger=None, search_domain=[('move_type', '=', 'in_refund')],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Vendor Payment Record -------------------------- #

    def process_quickbook_vpt_record(self, batch_records, current_instance, field_model_name,
                                     dropdown_field_mapping_name,
                                     is_company, module_name, logger_name, operation_type, odoo_company_id,
                                     check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.payment', related_logger=None, search_domain=[('partner_type', '=', 'supplier')],
            additional_fields=None, check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Employee Record -------------------------- #

    def process_quickbook_employee_record(self, batch_records, current_instance, field_model_name,
                                          dropdown_field_mapping_name,
                                          is_company, module_name, logger_name, operation_type, odoo_company_id,
                                          check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='hr.employee', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Department Record -------------------------- #

    def process_quickbook_department_record(self, batch_records, current_instance, field_model_name,
                                            dropdown_field_mapping_name,
                                            is_company, module_name, logger_name, operation_type, odoo_company_id,
                                            check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='hr.department', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Payment Term Record -------------------------- #

    def process_quickbook_pyt_record(self, batch_records, current_instance, field_model_name,
                                     dropdown_field_mapping_name,
                                     is_company, module_name, logger_name, operation_type, odoo_company_id,
                                     check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.payment.term', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Payment Method Record -------------------------- #

    def process_quickbook_pym_record(self, batch_records, current_instance, field_model_name,
                                     dropdown_field_mapping_name,
                                     is_company, module_name, logger_name, operation_type, odoo_company_id,
                                     check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='payment.method', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Account Tax Record -------------------------- #

    def process_quickbook_account_tax_record(self, batch_records, current_instance, field_model_name,
                                             dropdown_field_mapping_name,
                                             is_company, module_name, logger_name, operation_type, odoo_company_id,
                                             check_hash):
        operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.tax', related_logger=None, search_domain=[], additional_fields=None,
            check_hash=check_hash)
        return operation_status, quickbook_id

    # ----------------------------- Process Quickbook Accounting Record -------------------------- #


    def process_quickbook_accounting_data(self, quickbook_record, sale_order_record_data, logger_name, operation_type,
                                          current_instance, odoo_company_id, check_hash, related_logger):
        invoice_move, bill_move = None, None
        if logger_name in ['customer payment', 'vendor payment']:
            if 'Line' in quickbook_record and quickbook_record['Line']:
                credit_note_move, vendor_credit_move = None, None

                is_multi_company = self.env.user.is_multi_company

                for line in quickbook_record['Line']:
                    linked_txns = line.get('LinkedTxn', [])
                    for txn in linked_txns:
                        txn_id = txn.get('TxnId')
                        txn_type = txn.get('TxnType')

                        if txn_type == 'Invoice':
                            domain = [
                                ('quickbook_id', '=', txn_id),
                                ('move_type', '=', 'out_invoice'),
                            ]
                            if is_multi_company:
                                domain.append(('company_id', '=', odoo_company_id))

                            invoice_move = self.env['account.move'].search(domain, limit=1)
                            if invoice_move and invoice_move.state != 'posted':
                                invoice_move.action_post()

                        elif txn_type == 'CreditMemo':
                            domain = [
                                ('quickbook_credit_note_id', '=', txn_id),
                                ('move_type', '=', 'out_refund'),
                            ]
                            if is_multi_company:
                                domain.append(('company_id', '=', odoo_company_id))

                            credit_note_move = self.env['account.move'].search(domain, limit=1)
                            if credit_note_move and credit_note_move.state != 'posted':
                                credit_note_move.action_post()

                        elif txn_type == 'Bill':
                            domain = [
                                ('quickbook_id', '=', txn_id),
                                ('move_type', '=', 'in_invoice'),
                            ]
                            if is_multi_company:
                                domain.append(('company_id', '=', odoo_company_id))

                            bill_move = self.env['account.move'].search(domain, limit=1)
                            if bill_move and bill_move.state != 'posted':
                                bill_move.action_post()

                        elif txn_type == 'VendorCredit':
                            domain = [
                                ('quickbook_refund_id', '=', txn_id),
                                ('move_type', '=', 'in_refund'),
                            ]
                            if is_multi_company:
                                domain.append(('company_id', '=', odoo_company_id))

                            vendor_credit_move = self.env['account.move'].search(domain, limit=1)
                            if vendor_credit_move and vendor_credit_move.state != 'posted':
                                vendor_credit_move.action_post()

                # Reconcile customer side
                if invoice_move and credit_note_move:
                    lines_to_reconcile = (invoice_move.line_ids + credit_note_move.line_ids).filtered(
                        lambda line: line.account_id.account_type == 'asset_receivable' and not line.reconciled
                    )
                    if lines_to_reconcile:
                        lines_to_reconcile.reconcile()
                        _logger.info(f"Reconciled Credit Memo {credit_note_move.name} with Invoice {invoice_move.name}")
                    sale_order_record_data.update({'memo': invoice_move.name})
                    # return None, invoice_move

                    # Reconcile vendor side
                if bill_move and vendor_credit_move:
                    lines_to_reconcile = (bill_move.line_ids + vendor_credit_move.line_ids).filtered(
                        lambda line: line.account_id.account_type == 'liability_payable' and not line.reconciled
                    )
                    if lines_to_reconcile:
                        lines_to_reconcile.reconcile()
                        _logger.info(f"Reconciled Vendor Credit {vendor_credit_move.name} with Bill {bill_move.name}")
                    sale_order_record_data.update({'memo': bill_move.name})
                    # return None, bill_move

                elif invoice_move:
                    sale_order_record_data.update({'memo': invoice_move.name})
                elif bill_move:
                    sale_order_record_data.update({'memo': bill_move.name})
                else:
                    # Log warning
                    self.log_operation_warning(
                        logger_name,
                        f"Create Invoice and/or Credit Memo before syncing Payment",
                        f"{logger_name.capitalize()} Record Sync QuickBooks To Odoo",
                        'odoo', quickbook_record, '', operation_type, current_instance.name)

                    return None, None

        quickbook_customer_id = None
        if logger_name in ['sales orders', 'invoice', 'customer payment', 'credit note']:
            quickbook_customer_id = quickbook_record['CustomerRef']['value']
        elif logger_name in ['purchase order', 'purchase bill', 'vendor payment', 'refund']:
            quickbook_customer_id = quickbook_record['VendorRef']['value']

        if quickbook_customer_id:
            if logger_name in ['sales orders', 'invoice', 'customer payment', 'credit note']:
                company_record, status = self.env['oqb.dry.mixin'].create_or_link_company_with_all_modules(
                    quickbook_customer_id, current_instance, 'oqb.customer.lines',
                    'quickbook_customer_dropdown_mapping',
                    'customer', operation_type, odoo_company_id, False, check_hash, logger_name)

            else:
                company_record, status = self.env['oqb.dry.mixin'].create_or_link_company_with_all_modules(
                    quickbook_customer_id, current_instance, 'oqb.vendor.lines', 'quickbook_vendor_dropdown_mapping',
                    'vendor', operation_type, odoo_company_id, False, check_hash, logger_name)

            # Link the company to the Quotation/SaleOrder
            if company_record:
                sale_order_record_data.update({'partner_id': company_record.id})
                return sale_order_record_data, invoice_move
            else:
                return None, invoice_move

        else:
            if not related_logger:
                description = f"Failed to create {logger_name} in odoo. customer field is required for {logger_name} record"
            else:
                description = f"Failed to create {related_logger} related {logger_name} in odoo. customer field is required for {logger_name} record"

            operation = f'{logger_name.capitalize()} Record Sync Quickbook to Odoo'
            self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'odoo',
                                                            sale_order_record_data, '', operation_type,
                                                            current_instance.name)
            return None, invoice_move

    # ----------------------------- Process Quickbook Order Line Record -------------------------- #

    def create_odoo_order_line(self, quickbook_record, sale_order, current_instance,
                               logger_name, order_line_module, operation_type, check_hash, odoo_company_id,
                               invoice_balance, linked_txn):
        quickbook_quoted_items_id, currency_id, quickbook_tax_code_ref = None, None, None
        try:
            quickbook_quoted_items = quickbook_record['Line']
            if quickbook_quoted_items:
                quickbook_quoted_items_id = None
                for item in quickbook_quoted_items:

                    # Check for different line detail types
                    line_detail_key = None
                    if 'SalesItemLineDetail' in item and 'Id' in item:
                        line_detail_key = 'SalesItemLineDetail'
                    elif 'ItemBasedExpenseLineDetail' in item:
                        line_detail_key = 'ItemBasedExpenseLineDetail'
                    elif 'AccountBasedExpenseLineDetail' in item:
                        line_detail_key = 'AccountBasedExpenseLineDetail'

                    # quickbook_account_type = line_detail['AccountRef']['name']

                    if line_detail_key and line_detail_key != 'AccountBasedExpenseLineDetail':
                        line_detail = item[line_detail_key]
                        quickbook_product_id = line_detail['ItemRef']['value']
                        quickbook_product_unit_price = line_detail.get('UnitPrice', 0)
                        quickbook_quoted_items_id = item.get('Id')
                        quickbook_quote_quantity = line_detail.get('Qty', 0)
                        # Extract tax information if available
                        quickbook_tax_code = line_detail.get('TaxCodeRef', {}).get('value')
                        odoo_product_record, status = self.create_or_link_product_in_sale_order_line(
                            quickbook_product_id, current_instance, 'oqb.product.lines',
                            'quickbook_product_dropdown_mapping', 'product', operation_type, check_hash,
                            odoo_company_id, logger_name
                        )

                        if odoo_product_record:
                            odoo_product = self.env['product.product'].search(
                                [('product_tmpl_id', '=', odoo_product_record.id)], limit=1)

                            if logger_name in ['invoice', 'purchase bill', 'credit note', 'refund']:
                                order_line_record = self.env[order_line_module].search(
                                    [('quickbook_id', '=', quickbook_quoted_items_id), ('move_id', '=', sale_order.id)],
                                    limit=1)
                            else:
                                order_line_record = self.env[order_line_module].search(
                                    [('quickbook_id', '=', quickbook_quoted_items_id),
                                     ('order_id', '=', sale_order.id)], limit=1)

                            order_line_vals = {
                                'product_id': odoo_product.id,
                                'price_unit': quickbook_product_unit_price,
                                'quickbook_id': quickbook_quoted_items_id
                            }

                            if logger_name == 'sales orders':
                                order_line_vals.update({
                                    'order_id': sale_order.id,
                                    'product_uom_qty': quickbook_quote_quantity
                                })
                            elif logger_name == 'purchase order':
                                order_line_vals.update({
                                    'order_id': sale_order.id,
                                    'product_qty': quickbook_quote_quantity
                                })
                            elif logger_name in ['invoice', 'purchase bill', 'credit note', 'refund']:
                                order_line_vals.update({
                                    'move_id': sale_order.id,
                                    'quantity': quickbook_quote_quantity
                                })

                            if logger_name == 'sales orders':
                                line_tax_field = 'tax_id'
                            elif logger_name == 'purchase order':
                                line_tax_field = 'taxes_id'
                            else:
                                line_tax_field = 'tax_ids'

                            is_multi_company = self.env.user.is_multi_company
                            if quickbook_tax_code:
                                domain = [('quickbook_tax_code', '=', quickbook_tax_code)]
                                if is_multi_company:
                                    domain.append(('company_id', '=', odoo_company_id))
                                odoo_tax_record = self.env['account.tax'].search(domain, limit=1)
                                order_line_vals.update({line_tax_field: [(6, 0, odoo_tax_record.ids)]})


                            if order_line_record and sale_order.state != 'posted':
                                order_line_record.write(order_line_vals)
                                order_line_record.env.cr.commit()
                            elif not order_line_record:
                                new_order_line_record = self.env[order_line_module].create(order_line_vals)
                                new_order_line_record.env.cr.commit()

                        else:
                            continue
                    if logger_name in ['purchase bill',
                                       'refund'] and line_detail_key == 'AccountBasedExpenseLineDetail':
                        line_detail = item[line_detail_key]
                        quickbook_account_id = line_detail['AccountRef']['value']
                        quickbook_tax_code = line_detail.get('TaxCodeRef', {}).get('value')
                        quickbook_quoted_items_id = item.get('Id')
                        quickbook_account_unit_price = item.get('Amount', 0)

                        odoo_account_record, status = self.create_or_link_account_in_journal_entry_line(
                            quickbook_account_id, current_instance, 'oqb.account.lines',
                            'quickbook_account_dropdown_mapping', 'chart of account', operation_type, check_hash,
                            odoo_company_id, logger_name
                        )

                        if odoo_account_record:
                            order_line_record = self.env[order_line_module].search(
                                [('quickbook_id', '=', quickbook_quoted_items_id),
                                 ('move_id', '=', sale_order.id)], limit=1)

                            if sale_order.state != 'posted':
                                order_line_vals = {
                                    'account_id': odoo_account_record.id,
                                    'quickbook_id': quickbook_quoted_items_id,
                                    'price_unit': quickbook_account_unit_price,
                                    'quantity': 1
                                }

                                order_line_vals.update({'move_id': sale_order.id})
                                is_multi_company = self.env.user.is_multi_company
                                if quickbook_tax_code:
                                    domain = [('quickbook_tax_code', '=', quickbook_tax_code)]
                                    if is_multi_company:
                                        domain.append(('company_id', '=', odoo_company_id))

                                    odoo_tax_record = self.env['account.tax'].search(domain, limit=1)
                                    order_line_vals.update({'tax_ids': [(6, 0, odoo_tax_record.ids)]})
                                if order_line_record:
                                    order_line_record.write(order_line_vals)
                                    order_line_record.env.cr.commit()
                                else:
                                    new_order_line_record = self.env[order_line_module].create(order_line_vals)
                                    new_order_line_record.env.cr.commit()

                if logger_name in ['invoice', 'purchase bill', 'credit note', 'refund']:
                    state, payment_state = self.map_quickbook_invoice_state(invoice_balance, linked_txn)
                    if state == 'posted' and payment_state == 'paid':
                        if sale_order.state != 'posted':
                            sale_order.action_post()  # Post the invoice (required to move to 'posted' state)
                            sale_order.payment_state = 'paid'
                    elif state == 'posted' and payment_state == 'partial':
                        if sale_order.state != 'posted':
                            sale_order.action_post()  # Post the invoice (required to move to 'posted' state)
                            sale_order.payment_state = 'partial'
                    if logger_name == 'credit note':
                        quickbook_credit_amount = quickbook_record['RemainingCredit']
                        if quickbook_credit_amount == 0:
                            sale_order.action_post()
                    sale_order.env.cr.commit()

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create {logger_name.capitalize()} Line For {logger_name.capitalize()}'
            description = f'Error occurred while processing {logger_name} record Quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo',
                                                          quickbook_quoted_items_id, operation, operation_type,
                                                          current_instance.name, error_type)

    # ----------------------------- Process Quickbook Order Line Product Record -------------------------- #

    def create_or_link_product_in_sale_order_line(self, product_id, current_instance,
        field_model_name,dropdown_field_mapping_name, logger_name, operation_type, check_hash,
        odoo_company_id, related_logger_name):
        status = None
        try:
            # Check if the product exists in Odoo
            domain = [
                ('quickbook_id', '=', product_id),
                ('active', '=', True),
            ]

            if self.env.user.is_multi_company:
                domain.append(('company_id', '=', odoo_company_id))

            product_record = self.env['product.template'].search(domain, limit=1)

            if not product_record:
                new_product_record = self.env['oqb.dry.mixin'].fetch_quickbook_manual_record('Item',
                      product_id,current_instance,logger_name,operation_type, 'Id')
                if new_product_record:
                    # Use the existing process_partner_record method to create the company
                    operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
                        batch_records=new_product_record, current_instance=current_instance,
                        field_model_name=field_model_name, dropdown_field_mapping_name=dropdown_field_mapping_name,
                        module_name='Item', logger_name=logger_name, operation_type=operation_type,
                        odoo_company_id=odoo_company_id, model_name='product.template',
                        related_logger=related_logger_name,
                        search_domain=[('active', '=', True)], additional_fields=None, check_hash=check_hash)

                    # Extract the newly created Product ID
                    if operation_status:
                        status, product_id, odoo_id, product_record = operation_status  # Get the created company ID
                else:
                    return None, None
            else:
                status = 'update'
                return product_record, status

            return product_record, status

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create/Link Odoo {logger_name.capitalize()} Record'
            description = f'Error occurred while processing {logger_name} record Quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo',
            product_id, operation, operation_type, current_instance.name,error_type)
            return None, None

    # ----------------------------- Process Quickbook Related Account Record -------------------------- #

    def create_or_link_account_in_journal_entry_line(self, account_id, current_instance,
        field_model_name,dropdown_field_mapping_name, logger_name, operation_type,
        check_hash, odoo_company_id, related_logger):
        status = None
        try:
            # Check if the product exists in Odoo
            account_record = self.env['account.account'].search(
                [('quickbook_id', '=', account_id), ('company_ids', '=', odoo_company_id)], limit=1)

            if not account_record:
                new_account_record = self.env['oqb.dry.mixin'].fetch_quickbook_manual_record('Account',
                account_id,current_instance,logger_name,operation_type, 'Id')
                if new_account_record:
                    # Use the existing process_partner_record method to create the company
                    operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
                        batch_records=new_account_record, current_instance=current_instance,
                        field_model_name=field_model_name, dropdown_field_mapping_name=dropdown_field_mapping_name,
                        module_name='Account', logger_name=logger_name, operation_type=operation_type,
                        odoo_company_id=odoo_company_id, model_name='account.account', related_logger=related_logger,
                        search_domain=[], additional_fields=None, check_hash=check_hash)

                    # Extract the newly created Product ID
                    if operation_status:
                        status, account_id, odoo_id, account_record = operation_status  # Get the created company ID
                else:
                    return None, None
            else:
                status = 'update'
                return account_record, status

            return account_record, status

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create/Link Odoo {logger_name.capitalize()} Record'
            description = f'Error occurred while processing {logger_name} record Quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo',
            account_id, operation, operation_type, current_instance.name,error_type)
            return None, None

        # ------------------------------ Create or Link Company With All Modules ------------------------------- #

    def create_or_link_company_with_all_modules(self, partner_id, current_instance, field_model_name,
        dropdown_field_mapping_name, logger_name,operation_type, odoo_company_id, is_company, check_hash,
        related_logger_name):
        try:
            status = None
            # Check if the company exists in Odoo
            is_multi_company = self.env.user.is_multi_company
            base_domain = [
                ('quickbook_id', '=', partner_id),
                ('is_company', '=', is_company),
                ('active', '=', True),
            ]

            if is_multi_company:
                base_domain.append(('company_id', '=', odoo_company_id))

            if logger_name in ['customer']:
                domain = list(base_domain)  # Copy the base domain
            else:
                domain = list(base_domain)
                domain.append(('supplier_rank', '>', 0))

            odoo_record = self.env['res.partner'].search(domain, limit=1)

            module_name = 'Customer' if logger_name == 'customer' else 'Vendor'
            if not odoo_record:
                partner_record = self.env['oqb.dry.mixin'].fetch_quickbook_manual_record(module_name,
                partner_id, current_instance,logger_name, operation_type, 'Id')
                search_domain = [('is_company', '=', is_company),
                                 ('active', '=', True)] if logger_name == 'customer' else [
                    ('is_company', '=', is_company), ('active', '=', True), ('supplier_rank', '=', 1)]
                if partner_record:
                    # Use the existing process_partner_record method to create the company
                    operation_status, quickbook_id = self.env['oqb.dry.mixin'].process_quickbook_record(
                        batch_records=partner_record, current_instance=current_instance,
                        field_model_name=field_model_name,
                        dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
                        logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
                        model_name='res.partner', related_logger=related_logger_name, search_domain=search_domain,
                        additional_fields=None,check_hash=check_hash)

                    if operation_status:
                        # Extract the newly created company ID
                        status, partner_id, odoo_id, odoo_record = operation_status  # Get the created company ID
                else:
                    return None, None
            else:
                status = 'update'
                return odoo_record, status

            return odoo_record, status

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create/Link Odoo {logger_name.capitalize()} Record'
            description = f'Error occurred while processing {logger_name} record Quickbook to Odoo'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'odoo', partner_id,
                                                          operation, operation_type, current_instance.name, error_type)
            return None, None

    # -------------------------- Filter Records Based on Quickbook ID ------------------------- #

    def fetch_quickbook_manual_record(self, module_name, record_id, current_instance, logger_name,
                                      operation_type, field_name):
        """
        Fetch data from Quickbook CRM with dynamic query parameters.
        """

        # Step 1: Construct the basic select query
        select_query = f"SELECT * FROM {module_name} WHERE {field_name} = '{record_id}'"

        response = self.env['oqb.dry.mixin'].fetch_quickbooks_data(current_instance, module_name, select_query)
        operation = f'Get Quickbook Fields'
        response_data = self.env['oqb.instance'].handle_response(response, {}, module_name, '', logger_name, '', 'get',
                                                                 operation, operation_type, current_instance)

        return response_data

    # Odoo to Quickbook Sync Records

    # --------------------------------- Odoo to quickbook Field Mappings ------------------------- #

    def odoo_to_quickbook_map_fields(self, record, current_instance, field_model_name, dropdown_mapping_field,
                                     odoo_record_id, logger_name, operation_type):
        """
        Map quickbook fields to Odoo fields using the provided mappings.

        Args: 'oqbinstance.accounts.lines'
            record (dict): A dictionary containing Odoo record data.
            current_instance (str): The quickbook current_instance.
            field_model_name (str): The name of the model containing field mappings between quickbook and Odoo.
            dropdown_mapping_field (str): The name of the field in `current_instance` containing dropdown mapping information.
        Returns:
            dict: A dictionary containing mapped data for Odoo fields.
        """
        try:
            record_data = {}
            field_mapping, dropdown_mapping = self.get_field_mapping(current_instance, field_model_name,
                                                                     dropdown_mapping_field)
            if not field_mapping:
                description = f"Field Mapping is required for {logger_name.capitalize()}"
                operation = f'{logger_name.capitalize()} Record Sync Odoo to Quickbook'
                self.log_operation_warning(logger_name, description, operation, 'quickbook', '', odoo_record_id,
                                           operation_type, current_instance.name)
                return None, None, False
            temp_data = {}
            operation_status = None

            records = record if isinstance(record, list) else [record]

            for record in records:
                for quickbook_internal_name, odoo_internal_name in field_mapping.items():

                    record_field_data = record.get(odoo_internal_name) if isinstance(record, dict) else getattr(record,
                                                                                                                odoo_internal_name,
                                                                                                                record.id)
                    if isinstance(record_field_data, tuple):  # Handle tuple fields
                        record_field_data = record_field_data[0]
                    # Extract the ID from record_field_data if it is a recordset
                    if hasattr(record_field_data, 'id'):
                        record_field_data = record_field_data.id
                    else:
                        record_field_data = record_field_data

                    if not record_field_data:
                        record_data[quickbook_internal_name] = None
                        temp_data[quickbook_internal_name] = None
                    elif quickbook_internal_name in ['Notes', 'Description']:
                        description_str = BeautifulSoup(record_field_data, 'html.parser')
                        # Extract the text content from the HTML using the get_text() method
                        description_text = description_str.get_text()
                        record_data[quickbook_internal_name] = description_text
                        temp_data[quickbook_internal_name] = description_text
                    elif quickbook_internal_name == 'CountrySubDivisionCode' and record_field_data:
                        state_id = record_field_data
                        state = self.env['res.country.state'].search([('id', '=', state_id)],
                                                                     limit=1)
                        state_name = state.code
                        if state:
                            record_data[quickbook_internal_name] = state_name
                            temp_data[quickbook_internal_name] = state_id
                    elif quickbook_internal_name == 'Country' and record_field_data:
                        country_id = record_field_data
                        country = self.env['res.country'].search([('id', '=', country_id)],
                                                                 limit=1)
                        con_name = country.code
                        if country:
                            record_data[quickbook_internal_name] = con_name
                            temp_data[quickbook_internal_name] = country_id
                    elif odoo_internal_name in dropdown_mapping:
                        if record_field_data:
                            organization_value = str(record_field_data)
                            odoo_value = dropdown_mapping[odoo_internal_name].get(organization_value)
                            if odoo_value:
                                record_data[quickbook_internal_name] = odoo_value
                                temp_data[quickbook_internal_name] = organization_value
                            elif not odoo_value and organization_value and organization_value != 'None':
                                description = (f'Please review and correct the dropdown configuration '
                                               f'{odoo_internal_name} mapping as the selected {logger_name} does not '
                                               f'match the configured options. Once corrected the {logger_name} '
                                               f'{odoo_internal_name}, and please try again. {logger_name} ID: {odoo_record_id}')
                                operation = f'{logger_name} sync odoo to quickbook'
                                self.log_operation_warning(logger_name, description, operation, 'quickbook', record,
                                                           odoo_record_id, operation_type, current_instance.name)
                                operation_status = 'skip'
                                continue

                        else:
                            record_data[quickbook_internal_name] = None
                            temp_data[quickbook_internal_name] = None
                    elif isinstance(record_field_data, (date, datetime)):
                        # Check if the data is of type date or datetime
                        # If it's a datetime, convert it to date first
                        if isinstance(record_field_data, datetime):
                            record_field_data = record_field_data.date()
                        # Convert to ISO format (YYYY-MM-DD)
                        iso_format_date = record_field_data.isoformat()
                        # Assign to the record data
                        record_data[quickbook_internal_name] = iso_format_date
                        temp_data[quickbook_internal_name] = iso_format_date
                    elif record_field_data:
                        record_data[quickbook_internal_name] = record_field_data
                        temp_data[quickbook_internal_name] = record_field_data

            # Mapped Data Generation
            mapped_data = self.prepare_mapped_data_quickbook_and_odoo(temp_data)
            # Calculating Hash
            dynamic_fields_values_hash = self.calculate_hash(mapped_data)

            return record_data, dynamic_fields_values_hash, operation_status

        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while field mapping {logger_name} module'
            operation = f'Odoo to quickbook Map Fields'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'quickbook',
                                                          odoo_record_id, operation, operation_type,
                                                          current_instance.name, error_type)
            return None, None, False

    # ----------------------- Fetch Particular Fields From Odoo Record ------------------ #

    def fetch_odoo_records(self, field_model_name, instance_id, odoo_model_name, record_last_id,
                           logger_name, operation_type, last_sync_date=None, offset=0, limit=0):
        """
            Fetch records from the specified model with the defined fields and filters.

        """

        # Step 1: Fetch field mappings from the specified model
        field_mappings = self.get_fields_lines_data(field_model_name, instance_id)

        if not field_mappings:
            description = f"Field Mapping is required for {logger_name.capitalize()}"
            operation = f'{logger_name.capitalize()} Record Sync Odoo To Quickbook'
            self.log_operation_warning(logger_name, description, operation, 'quickbook', '', '',
                                       operation_type, instance_id.name)
            return None, False

        # Step 3: Build domain for search_read
        domain = [
            ('write_date', '>', last_sync_date), ('sync_to_quickbook', '=', True), ('id', '>', record_last_id)
        ]

        active_user_admin = self.env['res.users'].search([('id', '=', 2)], limit=1)
        if active_user_admin.is_multi_company:
            odoo_company_id = instance_id.company_name.id
            if logger_name not in ['payment method', 'customer payment', 'vendor payment']:
                if logger_name == 'chart of account':
                    domain.append(('company_ids', 'in', [odoo_company_id]))
                else:
                    domain.append(('company_id', '=', odoo_company_id))
            else:
                domain.append(('instance_name', '=', instance_id.id))
        # Conditionally add the 'active' field to the domain based on the logger_name
        if logger_name not in ['quotation', 'sales orders', 'purchase order', 'chart of account', 'invoice',
                               'customer payment', 'credit note', 'purchase bill', 'refund', 'vendor payment',
                               'payment method']:
            domain.append(('active', '=', True))
        if logger_name == 'sales orders':
            domain.append(('state', '!=', 'cancel'))
        if logger_name == 'invoice':
            domain.append(('move_type', '=', 'out_invoice'))
        if logger_name == 'purchase bill':
            domain.append(('move_type', '=', 'in_invoice'))
        if logger_name == 'credit note':
            domain.append(('move_type', '=', 'out_refund'))
        if logger_name == 'refund':
            domain.append(('move_type', '=', 'in_refund'))
        if logger_name == 'customer payment':
            domain.append(('partner_type', '=', 'customer'))
        if logger_name == 'vendor payment':
            domain.append(('partner_type', '=', 'supplier'))
        if logger_name == 'customer':
            domain.extend([('is_company', '=', False), ('supplier_rank', '=', 0)])
        if logger_name == 'vendor':
            domain.extend([('is_company', '=', False), ('supplier_rank', '>', 0)])

        # Step 4: Fetch records from the specified model with the defined fields and filters
        odoo_records = self.env[odoo_model_name].search(domain, offset=offset, limit=limit, order='id ASC')

        return odoo_records, True

    # ---------------------------------- Odoo Record Sync to Quickbook ----------------------------- #

    def fetch_data_from_odoo(self, current_instance, last_sync_date_field, odoo_module_name, is_company,
                             field_model_name, dropdown_field_mapping_name, module_name, logger_name,
                             operation_type, process_record_method, sync_date_field, last_id_field):
        try:

            last_sync_date, current_utc_time = self.last_odoo_sync_date_common(last_sync_date_field)
            access_token, pagination_size, base_api_url, minor_version, quickbook_company_id, odoo_company_id = \
                self.env['oqb.dry.mixin'].get_oqb_instance_data(current_instance)
            record_last_id = getattr(current_instance, last_id_field, None)
            while True:

                partner_records, field_mapping = self.fetch_odoo_records(field_model_name, current_instance,
                odoo_module_name,record_last_id, logger_name, operation_type,last_sync_date=last_sync_date, offset=0,
                limit=pagination_size)

                if not partner_records:
                    break
                batch_records = [record for record in partner_records if record.id]
                success_count, operation_status = getattr(self, process_record_method)(batch_records, current_instance,
                               field_model_name,dropdown_field_mapping_name,is_company, module_name,
                               logger_name, operation_type,odoo_company_id,check_hash=True)
                # Update the last record ID after processing
                record_last_id = partner_records[-1].get('id') if isinstance(partner_records[-1],
                                                                             dict) else partner_records[-1].id
                _logger.info('record_last_id called....', record_last_id)
                current_instance.write({last_id_field: record_last_id})
                current_instance.env.cr.commit()

                if len(partner_records) < pagination_size:
                    break

                # Update sync date and reset the last record ID
            if last_sync_date and field_mapping:
                current_instance.write({
                    sync_date_field: current_utc_time, last_id_field: 0
                })
            # Always reset last_id_field to 0
            current_instance.write({
                last_id_field: 0
            })
            self.scheduler_run_successfully_log(logger_name, operation_type, 'quickbook', current_instance.name)

        except Exception as e:
            # create a record in QuickbookLogger to store the error data
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Odoo {logger_name.capitalize()} Record Sync to Quickbook'
            description = f'Error occurred while {logger_name} create/update in Quickbook.'
            self.exception_log_error(error_details, logger_name, description, 'quickbook', '', operation,
                                     operation_type, current_instance.name, error_type)

    # --------------------------------- Create Payload For Quickbook --------------------- #

    def process_odoo_quickbook_record(self, payload, access_token, base_url, quickbook_company_id, module_name,
        partner_odoo_id, logger_name,operation_type, current_instance):
        endpoint = f"{base_url}/{quickbook_company_id}/batch"
        headers = self.get_headers(access_token)
        response = requests.post(endpoint, data=json.dumps(payload), headers=headers)
        response_status = response.status_code
        operation = f'Create quickbook {logger_name} Records'
        response_data = self.env['oqb.instance'].handle_response(response, payload, module_name, 'quickbook',
        logger_name, partner_odoo_id, 'post', operation,operation_type, current_instance)
        return response_data, response_status

    # ------------------------------- Process to Sync Odoo Record to Quickbook ------------------ #

    def sync_odoo_record_to_quickbook(self, odoo_records, module_name, batch_records, dynamic_hashes, logger_name, current_instance,
                                      odoo_company_id, check_hash, operation_type):
        """
        Sync Odoo customer data to QuickBooks and handle nested fields like 'BillAddr' statically.

        Args:
            record_data (dict): Dictionary containing Odoo record data to sync.

        Returns:
            dict: Payload ready for QuickBooks customer creation.
        """

        success_count, operation_status, filtered_batch_records = 0, None, []

        # Define static mappings
        if logger_name == 'employee':
            address_field = "PrimaryAddr"
        else:
            address_field = "BillAddr"

        NESTED_FIELDS = {
            address_field: ["Line1", "Line2", "City", "CountrySubDivisionCode", "PostalCode", "Country"]
        }

        # Ensure odoo_records is a list for uniform processing
        odoo_records = odoo_records if isinstance(odoo_records, list) else [odoo_records]

        # Initialize the QuickBooks batch payload
        quickbook_payload = {"BatchItemRequest": []}
        hash_field, quickbook_id_field = self.get_sync_field_names(logger_name)
        # Iterate through Odoo records and batch records
        for odoo_record, batch_record, dynamic_hash in zip(odoo_records, batch_records, dynamic_hashes):
            # Initialize the record payload
            record_payload = {}

            # Map Odoo record fields dynamically
            for key, value in odoo_record.items():
                if not value:
                    continue
                elif key in NESTED_FIELDS.get(address_field, []):
                    record_payload.setdefault(address_field, {})[key] = value
                elif key == "PrimaryEmailAddr":
                    record_payload.setdefault("PrimaryEmailAddr", {})["Address"] = value
                elif key == "PrimaryPhone":
                    record_payload.setdefault("PrimaryPhone", {})["FreeFormNumber"] = value
                elif key == 'WebAddr':
                    record_payload.setdefault("WebAddr", {})["URI"] = value
                else:
                    record_payload[key] = value
            # Handle product-specific logic
            if logger_name == 'customer':
                success_count, operation_status = self.check_record_conditions(batch_record, module_name, logger_name,
                current_instance, 'email',operation_type, 'res.partner',
                'PrimaryEmailAddr')
                if batch_record.parent_id:
                    record_payload["CompanyName"] = batch_record.parent_id.name
                if operation_status == 'no_action':
                    continue
            if logger_name == 'product':
                success_count, operation_status = self.check_record_conditions(batch_record, module_name, logger_name,
                current_instance, 'default_code',operation_type, 'product.template',
                'Sku')

                if operation_status == 'no_action':
                    continue

                # Get product-level accounts
                odoo_income_account = batch_record.property_account_income_id
                odoo_expense_account = batch_record.property_account_expense_id

                # If not set on product, take from configuration
                if not odoo_income_account:
                    odoo_income_account = current_instance.oqb_product_income_account
                if not odoo_expense_account:
                    odoo_expense_account = current_instance.oqb_product_expense_account

                accounts = [odoo_income_account, odoo_expense_account]
                if odoo_income_account and odoo_expense_account:
                    for account in accounts:
                        if account:
                            if not account.quickbook_id and account.sync_to_quickbook:
                                self.process_odoo_record(
                                    account, current_instance, 'oqb.coa.lines',
                                    'odoo_coa_dropdown_mapping', 'Account',
                                    'chart of account', operation_type, odoo_company_id, 'account.account',
                                    check_hash=True
                                )
                            elif not account.sync_to_quickbook:
                                warning_message = f"'Sync to Quickbook' is required for {logger_name.capitalize()} account: {account.name}."
                                operation = f'Manual {logger_name.capitalize()} Push Odoo To Quickbook'
                                self.env['oqb.dry.mixin'].log_operation_warning(logger_name, warning_message, operation,
                                    'quickbook', account, account.id, 'manually',current_instance.name)

                        record_payload["IncomeAccountRef"] = {"value": odoo_income_account.quickbook_id}
                        record_payload["ExpenseAccountRef"] = {"value": odoo_expense_account.quickbook_id}
                        record_payload["PurchaseCost"] = batch_record.standard_price
                else:
                    description = f"Income & Expense Account field is required for {logger_name.capitalize()}"
                    operation = f'{logger_name.capitalize()} Record Sync Odoo To Quickbook'
                    self.log_operation_warning(logger_name, description, operation, 'quickbook', record_payload, '',
                                               operation_type, current_instance.name)
                    success_count, operation_status = 0, 'no_account'
                    continue

            # ------------------ CHART OF ACCOUNT DUPLICATE NAME HANDLING ------------------ #
            if logger_name == 'chart of account' and not getattr(batch_record, quickbook_id_field):

                skip_create = self.handle_coa_duplicate_name_qb_linking(record_payload=record_payload,
                    batch_record=batch_record,current_instance=current_instance,logger_name=logger_name,
                    operation_type=operation_type,quickbook_id_field=quickbook_id_field, dynamic_hash=dynamic_hash)
                if skip_create:
                    success_count, operation_status = 0, 'sync_process_id'
                    continue

            record_payload = self.process_odoo_to_quickbook_payload(record_payload=record_payload,
                current_instance=current_instance,logger_name=logger_name, odoo_record=odoo_record,
                batch_record=batch_record,odoo_company_id=odoo_company_id,check_hash=check_hash,
                operation_type=operation_type)
            success_count, operation_status = 0, 'action'

            # Remove keys with None values recursively
            record_payload = {k: v for k, v in record_payload.items() if v and v != {}}

            if logger_name == 'credit note':
                invoice_qb_id = None

                # batch_record is account.move (credit note)
                for line in batch_record.line_ids:
                    matched_partials = line.matched_debit_ids + line.matched_credit_ids
                    for partial in matched_partials:
                        debit_move = partial.debit_move_id.move_id
                        credit_move = partial.credit_move_id.move_id

                        # Identify the *other* move: the invoice (not the credit note itself)
                        if debit_move.id != batch_record.id and debit_move.move_type == 'out_invoice' and debit_move.quickbook_id:
                            invoice_qb_id = debit_move.quickbook_id
                        elif credit_move.id != batch_record.id and credit_move.move_type == 'out_invoice' and credit_move.quickbook_id:
                            invoice_qb_id = credit_move.quickbook_id

                # Add InvoiceRef only if invoice(s) are linked
                if invoice_qb_id:
                    record_payload['InvoiceRef'] = {'value': invoice_qb_id}

                record_payload['RemainingCredit'] = 0

            # Determine operation type and prepare the payload
            if getattr(batch_record, quickbook_id_field):
                record_payload.update({'Id': getattr(batch_record, quickbook_id_field), "SyncToken": batch_record.quickbook_sync_token})
                if logger_name == 'employee':
                    record_payload.update({"Active": True})
                operation = "update"
            else:
                operation = "create"

            create_payload = {
                "operation": operation, module_name: record_payload
            }
            # Append to QuickBooks batch payload
            if logger_name == 'product':
                if create_payload['Item']['Type'] == 'Inventory':
                    is_multi_company = self.env.user.is_multi_company

                    product_domain = [('product_tmpl_id', '=', batch_record.id)]
                    if is_multi_company:
                        product_domain.append(('company_id', '=', odoo_company_id))

                    product_record = self.env['product.product'].search(product_domain, limit=1)

                    quant_domain = [('product_id', '=', product_record.id)]
                    if is_multi_company:
                        quant_domain.append(('company_id', '=', odoo_company_id))

                    product_quant = self.env['stock.quant'].search(quant_domain, limit=1)

                    create_payload['Item']["TrackQtyOnHand"] = True
                    create_payload['Item']["QtyOnHand"] = product_quant.quantity
                    if isinstance(product_quant.inventory_date, (date, datetime)):
                        # If it's a datetime, convert it to date first
                        if isinstance(product_quant.inventory_date, datetime):
                            create_payload['Item']["InvStartDate"] = product_quant.inventory_date.date()
                        # Convert to ISO format (YYYY-MM-DD)
                        iso_format_date = product_quant.inventory_date.isoformat()
                        # Assign to the record data
                        create_payload['Item']["InvStartDate"] = iso_format_date
                    odoo_product_asset_account_id = current_instance.oqb_asset_account
                    create_payload['Item']['AssetAccountRef'] = {
                        "value": odoo_product_asset_account_id.quickbook_id
                    }

            if logger_name == 'chart of account' and 'AccountType' in create_payload['Account']:
                if create_payload['Account']['AccountType'] == 'Other Current Asset':
                    create_payload['Account']['AccountSubType'] = 'Inventory'
                if create_payload['Account']['AccountType'] == 'Cost of Goods Sold':
                    create_payload['Account']['AccountSubType'] = 'SuppliesMaterialsCogs'
                if create_payload['Account']['AccountType'] == 'Income':
                    create_payload['Account']['AccountSubType'] = 'SalesOfProductIncome'

            quickbook_payload["BatchItemRequest"].append(create_payload)

            # If we get here, the record passed all checks and should be processed
            filtered_batch_records.append(batch_record)

        # Return the JSON payload
        return quickbook_payload, success_count, operation_status, filtered_batch_records

    # ------------------------------------- Handle Duplicate COA odoo to quickbook ------------------------- #

    def handle_coa_duplicate_name_qb_linking(self, record_payload, batch_record, current_instance,
            logger_name, operation_type, quickbook_id_field, dynamic_hash):
        """
        If Chart of Account with same Name exists in QuickBooks,
        link it to Odoo instead of creating a duplicate.

        Returns:
            True  → record handled & should be skipped from create
            False → continue normal create flow
        """

        if logger_name != 'chart of account':
            return False

        if getattr(batch_record, quickbook_id_field):
            return False

        qb_response = self.fetch_qb_chart_of_account(record_payload=record_payload,current_instance=current_instance,
            logger_name=logger_name,operation_type=operation_type)
        qb_accounts = []

        if isinstance(qb_response, list):
            qb_accounts = qb_response
        elif isinstance(qb_response, dict):
            qb_accounts = qb_response.get('QueryResponse', {}).get('Account', [])

        if not qb_accounts:
            return False

        qb_account = qb_accounts[0]

        # 🔗 Link QuickBooks account to Odoo
        batch_record.write({
            'quickbook_id': qb_account.get('Id'),
            'quickbook_sync_token': qb_account.get('SyncToken'),
            'instance_name': current_instance.name,
            'sync_to_quickbook': True,
            'odoo_hash': dynamic_hash
        })

        batch_record.env.cr.commit()

        warning_message = (
            f"Chart of Account already exists in QuickBooks. "
            f"Linked existing account instead of creating duplicate."
        )

        self.env['oqb.dry.mixin'].log_operation_warning(logger_name,warning_message,'Chart of Account Sync',
            'quickbook',batch_record,batch_record.id,operation_type,current_instance.name)

        return True

    # ------------------------- Fetch Chart of Account Record ------------------- #

    def fetch_qb_chart_of_account(self,record_payload,current_instance,logger_name,operation_type):
        """
        Chart of Account lookup using:
        AcctNum OR Name
        (OR logic handled in Python – QB safe)
        """

        account_name = record_payload.get('Name')
        account_number = record_payload.get('AcctNum')


        qb_accounts = []

        # OR condition (first match wins)
        if account_number:
            qb_accounts = self.fetch_quickbook_manual_record(module_name='Account',record_id=account_number,
                current_instance=current_instance,logger_name=logger_name,operation_type=operation_type,
                field_name='AcctNum')

        if not qb_accounts and account_name:
            qb_accounts = self.fetch_quickbook_manual_record(module_name='Account',record_id=account_name,
                current_instance=current_instance,logger_name=logger_name,operation_type=operation_type,
                field_name='Name')

        return qb_accounts

    # ----------------------------- Duplicate Record Check Condition -------------------------- #

    def check_record_conditions(self, odoo_record, module_name, logger_name, current_instance,
                                unique_field_name, operation_type, odoo_module_name, search_field):
        """
            Checks the conditions for the record (customer, product) based on the unique identifier like email or product code.
        """
        existing_odoo_record = None
        # Fetch Quickbook ID and unique field value (email or product code)
        quickbook_id = odoo_record.quickbook_id
        partner_id = odoo_record.id
        unique_field_value = odoo_record[unique_field_name]

        if quickbook_id and unique_field_value:
            return 1, 'action'

        elif quickbook_id:
            return 1, 'action'

        elif unique_field_value:
            partner_records = self.env['oqb.dry.mixin'].fetch_quickbook_manual_record(module_name,
            unique_field_value,current_instance, logger_name,operation_type, search_field)
            # Check if any of the records' QuickBook IDs exist in Odoo
            if not partner_records:
                return 1, 'action'

            duplication_detected = False
            for partner_record in partner_records:
                quickbook_id = partner_record.get('Id')
                existing_odoo_record = self.env[odoo_module_name].search([('quickbook_id', '=', quickbook_id)], limit=1)

                if existing_odoo_record:
                    duplication_detected = True
                    break

            if duplication_detected:
                # Log a warning and halt processing
                description = (
                    f'The {unique_field_name} {unique_field_value} is already associated with {existing_odoo_record}. '
                    f'Please use a different {unique_field_name}.'
                )
                operation = f'Record Sync {logger_name} Odoo To Quickbook'
                self.log_operation_warning(logger_name, description, operation, 'quickbook',
                                           odoo_record, partner_id, operation_type, current_instance.name)
                return 0, 'no_action'

                # If no duplication is detected and no records exist in Odoo, create a new record in QuickBooks
            if not duplication_detected and not partner_records[0]:
                return 1, 'action'

        return 1, 'action'

    # ------------------------------- Create Payload for Quickbook -------------------------- #

    def process_odoo_to_quickbook_payload(self, record_payload, current_instance, logger_name, odoo_record,
                        batch_record,odoo_company_id, check_hash, operation_type):
        """
        Process and prepare the payload for syncing Odoo records to QuickBooks, handling both customer and vendor scenarios.

        """
        # Determine the line model and corresponding field based on the logger_name
        if logger_name in ['sales orders', 'invoice', 'credit note', 'purchase order', 'purchase bill', 'refund']:
            if logger_name in ['sales orders', 'purchase order']:
                line_model = 'order_line'
            else:
                line_model = 'invoice_line_ids'
            odoo_line_records = batch_record[line_model]

            if not odoo_line_records:
                warning_message = f'Line items are required for creation of {logger_name} in QuickBooks: {batch_record.id}'
                self.env['oqb.dry.mixin'].log_operation_warning(logger_name, warning_message,
                f'{logger_name.capitalize()} Push to QuickBooks','quickbook',
                batch_record, batch_record.id, operation_type,current_instance.name)
                return record_payload  # Skip processing if no line items found

            # Create line items for QuickBooks
            record_payload = self.create_quickbook_order_line(
                record_payload, current_instance, logger_name, odoo_record,
                batch_record, odoo_line_records, odoo_company_id, check_hash, operation_type
            )

        if logger_name in ['vendor payment', 'customer payment']:
            record_payload = self.create_vendor_payment_payload(record_payload, current_instance, logger_name,
                                                                odoo_record, batch_record, odoo_company_id, check_hash,
                                                                operation_type)
        if logger_name not in ['product', 'payment method', 'payment term', 'department', 'employee']:
            odoo_quotation_currency_id = batch_record.currency_id.id
            quickbook_currency = self.get_currency_id_from_odoo(odoo_quotation_currency_id, current_instance,
                                                                logger_name, batch_record.id, odoo_record,
                                                                operation_type)
            if quickbook_currency:
                record_payload.update({"CurrencyRef": {"value": quickbook_currency}})
        # Determine the partner (customer/vendor) and related parameters
        if logger_name in ['sales orders', 'invoice', 'customer payment', 'credit note', 'purchase order',
                           'purchase bill','refund', 'vendor payment']:

            partner_record = batch_record.partner_id

            if partner_record:
                # Define mappings based on whether the partner is a customer or vendor
                if logger_name in ['purchase order', 'purchase bill', 'refund', 'vendor payment']:
                    module_name = 'Vendor'
                    partner_logger_name = 'vendor'
                    field_model_name = 'oqb.vendor.lines'
                    dropdown_mapping_name = 'odoo_vendor_dropdown_mapping'
                    partner_ref_field = 'VendorRef'
                    if not partner_record.supplier_rank > 0:
                        description = f"The selected partner '{partner_record.name}' is not a Vendor."
                        operation = f'{logger_name.capitalize()} Record Sync Odoo To Quickbook'
                        self.log_operation_warning(logger_name, description, operation,
                                                   'quickbook', '', batch_record.id, operation_type,
                                                   current_instance.name)
                        return record_payload
                else:
                    module_name = 'Customer'
                    partner_logger_name = 'customer'
                    field_model_name = 'oqb.customer.lines'
                    dropdown_mapping_name = 'odoo_customer_dropdown_mapping'
                    partner_ref_field = 'CustomerRef'
                    if partner_record.supplier_rank != 0:
                        description = f"The selected partner '{partner_record.name}' is not a Customer."
                        operation = f'{logger_name.capitalize()} Record Sync Odoo To Quickbook'
                        self.log_operation_warning(logger_name, description, operation,
                                                   'quickbook', '', batch_record.id, operation_type,
                                                   current_instance.name)
                        return record_payload

                status, odoo_account = self.odoo_related_record(partner_record, 'res.partner',
                current_instance, field_model_name,dropdown_mapping_name, operation_type, odoo_company_id,
                check_hash, logger_name, partner_logger_name,module_name)

                if status in ['no_process', 'no_record']:
                    return record_payload

                record_payload.update({partner_ref_field: {'value': partner_record.quickbook_id}})
            else:
                description = f"Customer/Vendor field is required for {logger_name.capitalize()} Record"
                operation = f'{logger_name.capitalize()} Record Sync Odoo To Quickbook'
                self.log_operation_warning(logger_name, description, operation,
                'quickbook', '', batch_record.id, operation_type, current_instance.name)
                return record_payload

        return record_payload

    # ----------------------- Process Quickbook Vendor Payment Records --------------------- #

    def create_vendor_payment_payload(self, record_payload, current_instance, logger_name, odoo_record,
                                      batch_record, odoo_company_id, check_hash, operation_type):
        """
        Create a payload for syncing vendor payments to QuickBooks.
        Handles both Check and Credit Card payment types dynamically.

        """
        # Handle Check Payment
        if logger_name == 'vendor payment':
            if batch_record.oqb_payment_type == 'check':
                odoo_vpt_bank_account = batch_record.journal_id.default_account_id
                if not odoo_vpt_bank_account:
                    description = f"No default bank account found for journal {batch_record.journal_id.name}"
                    operation = f'{logger_name.capitalize()} Record Sync QuickBooks To Odoo'
                    self.log_operation_warning(logger_name, description, operation, 'quickbook', '', '',
                                               operation_type, current_instance.name)
                    return record_payload

                odoo_vpt_bank_account_id = odoo_vpt_bank_account.quickbook_id
                if not odoo_vpt_bank_account_id:
                    description = f"First Create Bank Account For {logger_name.capitalize()}"
                    operation = f'{logger_name.capitalize()} Record Sync QuickBooks To Odoo'
                    self.log_operation_warning(logger_name, description, operation, 'quickbook', '', '',
                                               operation_type, current_instance.name)
                    return record_payload

                # Update record_payload for Check Payment
                record_payload["CheckPayment"] = {
                    "BankAccountRef": {
                        "value": str(odoo_vpt_bank_account_id),
                    }
                }
                record_payload["PayType"] = "Check"

            # Handle Credit Card Payment
            elif batch_record.oqb_payment_type == 'credit card':
                # Fetch the credit card account
                odoo_credit_card_account_id = current_instance.oqb_vpt_credit_card_account.id
                if not odoo_credit_card_account_id:
                    description = f"First Create Credit Card Account For {logger_name.capitalize()}"
                    operation = f'{logger_name.capitalize()} Record Sync Odoo to QuickBooks'
                    self.log_operation_warning(logger_name, description, operation, 'quickbook', '', '',
                                               operation_type, current_instance.name)
                    return record_payload

                if self.env.user.is_multi_company:
                    odoo_credit_card_account = self.env['account.account'].search(
                        [('id', '=', odoo_credit_card_account_id), ('company_ids', '=', odoo_company_id)])
                else:
                    odoo_credit_card_account = self.env['account.account'].search(
                        [('id', '=', odoo_credit_card_account_id)])
                # Update record_payload for Credit Card Payment
                record_payload["CreditCardPayment"] = {
                    "CCAccountRef": {
                        "value": str(odoo_credit_card_account.quickbook_id),  # QuickBooks ID of the credit card account
                        "name": str(odoo_credit_card_account.name)  # Name of the credit card account
                    }
                }
                record_payload["PayType"] = "CreditCard"

            # Fetch bill record using reconciliation, instead of relying only on ref

            linked_moves = batch_record.reconciled_bill_ids.filtered(
                lambda m: (
                        m.company_id.id == odoo_company_id and (
                        (m.move_type == 'in_invoice' and m.quickbook_id) or
                        (m.move_type == 'in_refund' and m.quickbook_refund_id)
                ))
            )

            if not linked_moves:
                description = f"First Link Invoice or Credit Note for {logger_name.capitalize()}"
                operation = f'{logger_name.capitalize()} Record Sync Odoo to QuickBooks'
                self.log_operation_warning(
                    logger_name, description, operation, 'quickbook', '', '',
                    operation_type, current_instance.name
                )
                return record_payload

            # Prepare the LinkedTxn payload for either invoice or credit note
            record_payload["Line"] = []

            for move in linked_moves:
                txn_type = "Bill" if move.move_type == "in_invoice" else "VendorCredit"
                quickbook_id = 'quickbook_id' if txn_type == "Bill" else 'quickbook_refund_id'
                record_payload["Line"].append({
                    "Amount": batch_record.amount,  # Or move.amount_total if amount varies
                    "LinkedTxn": [{
                        "TxnId": getattr(move, quickbook_id),
                        "TxnType": txn_type
                    }]
                })
        else:
            # Fetch bill record using reconciliation, instead of relying only on ref
            linked_moves = batch_record.reconciled_invoice_ids.filtered(
                lambda m: (
                        m.company_id.id == odoo_company_id and (
                        (m.move_type == 'out_invoice' and m.quickbook_id) or
                        (m.move_type == 'out_refund' and m.quickbook_credit_note_id)
                ))
            )

            if not linked_moves:
                description = f"First Link Invoice or Credit Note for {logger_name.capitalize()}"
                operation = f'{logger_name.capitalize()} Record Sync Odoo to QuickBooks'
                self.log_operation_warning(
                    logger_name, description, operation, 'quickbook', '', '',
                    operation_type, current_instance.name
                )
                return record_payload

            # Prepare the LinkedTxn payload for either invoice or credit note
            record_payload["Line"] = []

            for move in linked_moves:
                txn_type = "Invoice" if move.move_type == "out_invoice" else "CreditMemo"
                quickbook_id = 'quickbook_id' if txn_type == "Invoice" else 'quickbook_credit_note_id'

                record_payload["Line"].append({
                    "Amount": batch_record.amount,  # Or move.amount_total if amount varies
                    "LinkedTxn": [{
                        "TxnId": getattr(move, quickbook_id),
                        "TxnType": txn_type
                    }]
                })

        return record_payload

    # ---------------------- Create Order Line for Quickbook -------------------- #

    def create_quickbook_order_line(self, record_payload, current_instance, logger_name, odoo_record, batch_record,
                                    odoo_sale_order_line_record, odoo_company_id, check_hash, operation_type):
        # Initialize the list for QuickBooks line items
        quickbooks_lines, item_detail_name, tax_code_ref, line_detail_payload = [], None, None, {}
        subtotal = 0.0  # To calculate the subtotal for all line items
        if logger_name == 'sales orders':
            line_tax_field, line_item_model, line_model_id = 'tax_id', 'sale.order.line', 'order_id'
        elif logger_name == 'purchase order':
            line_tax_field, line_item_model, line_model_id = 'taxes_id', 'purchase.order.line', 'order_id'
        else:
            line_tax_field, line_item_model, line_model_id = 'tax_ids', 'account.move.line', 'move_id'
        # line_tax_field = 'tax_ids' if logger_name == 'invoice' else 'tax_id'
        quickbooks_lines = []
        for line in odoo_sale_order_line_record:
            # Determine the quantity field based on the document type
            if logger_name == 'sales orders':
                quantity_field = 'product_uom_qty'
            elif logger_name == 'purchase order':
                quantity_field = 'product_qty'
            else:
                quantity_field = 'quantity'

            order_line_product = line.product_id
            order_line_id = line.id
            order_unit_price = line.price_unit
            order_quantity = getattr(line, quantity_field)
            order_description = line.name
            order_subtotal = line.price_subtotal

            order_tax_ids = getattr(line, line_tax_field)
            # Take the first tax if multiple are selected
            selected_tax = order_tax_ids[0] if order_tax_ids else None
            # Validate selected tax
            if selected_tax:
                quickbooks_tax_id = selected_tax.quickbook_tax_code
                if quickbooks_tax_id:
                    tax_code_ref = {"value": quickbooks_tax_id}
                else:
                    tax_code_ref = {"value": quickbooks_tax_id}
            else:
                tax_code_ref = {"value": None}

            # Check if the product has a quickbook_id, if not, sync the product to Quickbook
            if order_line_product.product_tmpl_id:
                status, order_line_product = self.odoo_related_record(order_line_product.product_tmpl_id,
                'product.template', current_instance,'oqb.product.lines',
                'odoo_product_dropdown_mapping',operation_type, odoo_company_id, check_hash,
                logger_name, 'product', 'Item')

                if status in ['no_process', 'no_record']:
                    continue

            if logger_name in ['purchase order']:
                odoo_account_id = current_instance.oqb_purchase_account.id
                if self.env.user.is_multi_company:
                    odoo_account = self.env['account.account'].search(
                        [('id', '=', int(odoo_account_id)), ('company_ids', '=', odoo_company_id)], limit=1)
                else:
                    odoo_account = self.env['account.account'].search(
                        [('id', '=', int(odoo_account_id))], limit=1)
                status, odoo_account = self.odoo_related_record(odoo_account, 'account.account', current_instance,
                'oqb.coa.lines', 'odoo_coa_dropdown_mapping',
                 operation_type, odoo_company_id, check_hash,logger_name, 'chart of account',
                                                                'Account')

                if status in ['no_process', 'no_record']:
                    continue
                record_payload.update({'APAccountRef': {"value": odoo_account.quickbook_id}})

            if logger_name in ['sales orders', 'invoice', 'credit note']:
                item_detail_name = 'SalesItemLineDetail'
            elif logger_name in ['purchase bill', 'refund']:
                # Handle both AccountRef and ItemRef conditions for purchase bill
                item_detail_name = None  # Placeholder; set per condition
            else:
                item_detail_name = 'ItemBasedExpenseLineDetail'

            if logger_name in ['purchase bill', 'refund']:
                # Condition for AccountRef
                order_line_account = line.account_id
                if order_line_account:
                    status, order_line_account = self.odoo_related_record(order_line_account,
                   'account.account', current_instance,'oqb.coa.lines',
                   'odoo_coa_dropdown_mapping', operation_type,odoo_company_id, check_hash,
                   logger_name, 'chart of account', 'Account')

                    if status in ['no_process', 'no_record']:
                        continue

                if not order_line_product and order_line_account:
                    account_detail_ref = 'AccountRef'
                    account_detail_ref_id = order_line_account.quickbook_id
                    account_line_detail_payload = {
                        account_detail_ref: {"value": account_detail_ref_id}
                    }
                    account_line_item = {
                        "DetailType": 'AccountBasedExpenseLineDetail',
                        "Amount": order_subtotal,
                        'AccountBasedExpenseLineDetail': account_line_detail_payload,
                        "Description": order_description,
                        "LineNum": order_line_id
                    }
                    quickbooks_lines.append(account_line_item)
                elif order_line_product and order_line_account:
                    # Condition for ItemRef
                    item_detail_ref = 'ItemRef'
                    item_detail_ref_id = order_line_product.quickbook_id
                    item_line_detail_payload = {
                        item_detail_ref: {"value": item_detail_ref_id},
                        "UnitPrice": order_unit_price,
                        "Qty": order_quantity,
                        "TaxCodeRef": tax_code_ref  # Default to 'NON' if no tax
                    }
                    item_line_item = {
                        "DetailType": 'ItemBasedExpenseLineDetail',
                        "Amount": order_subtotal,
                        'ItemBasedExpenseLineDetail': item_line_detail_payload,
                        "Description": order_description,
                        "LineNum": order_line_id
                    }
                    quickbooks_lines.append(item_line_item)

            else:
                if logger_name not in ['refund']:
                    item_detail_ref = 'ItemRef'
                    item_detail_ref_id = order_line_product.quickbook_id
                    line_detail_payload = {
                        item_detail_ref: {"value": item_detail_ref_id},
                        "UnitPrice": order_unit_price,
                        "Qty": order_quantity,
                        "TaxCodeRef": tax_code_ref  # Default to 'NON' if no tax
                    }
                line_item = {
                    "DetailType": item_detail_name,
                    "Amount": order_subtotal,
                    item_detail_name: line_detail_payload,
                    "Description": order_description,
                    "LineNum": order_line_id
                }
                quickbooks_lines.append(line_item)

            subtotal += order_subtotal  # Update the subtotal

        # Update the record payload with line items
        record_payload["Line"] = quickbooks_lines

        return record_payload

    # ----------------------------- Process Odoo Batch Records ------------------------ #

    def process_odoo_record(self, batch_records, current_instance, field_model_name, dropdown_field_mapping_name,
                            module_name, logger_name, operation_type, odoo_company_id, model_name, check_hash=True):
        """
        A reusable function to process QuickBooks records and create/update them in Odoo.
        """
        quickbook_id, operation_status, success_count, odoo_record = None, None, 0, None
        odoo_records, odoo_ids, records_data, dynamic_hashes, update_odoo_records = [], [], [], [], []

        try:
            for odoo_record in batch_records:
                quickbook_record_data, dynamic_fields_values_hash, operation_status = \
                    self.env['oqb.dry.mixin'].odoo_to_quickbook_map_fields(
                        odoo_record, current_instance, field_model_name, dropdown_field_mapping_name, quickbook_id,
                        logger_name, operation_type)
                if not quickbook_record_data:
                    operation_status = 'no_field'
                    break
                # Compare the hashes

                hash_field, quickbook_id_field = self.get_sync_field_names(logger_name)

                # Check if we need to update
                existing_hash = getattr(odoo_record, hash_field)
                if existing_hash != dynamic_fields_values_hash or not check_hash:
                    odoo_records.append(quickbook_record_data)
                    records_data.append(quickbook_record_data)
                    dynamic_hashes.append(dynamic_fields_values_hash)
                    odoo_ids.append(odoo_record.id)
                    update_odoo_records.append(odoo_record)
                else:
                    continue  # Skip this record if hashes are identical
            if odoo_records:
                quickbook_payload, success_count, operation_status, filtered_batch_records = self.sync_odoo_record_to_quickbook(
                    odoo_records, module_name, update_odoo_records, dynamic_hashes, logger_name, current_instance, odoo_company_id,
                    check_hash, operation_type)
                if operation_status in ['no_action', 'no_account', 'sync_process_id'] and not quickbook_payload.get("BatchItemRequest"):
                    return success_count, operation_status
                # if isinstance(quickbook_payload, dict) and isinstance(quickbook_payload.get("BatchItemRequest"), list) and quickbook_payload["BatchItemRequest"]:
                access_token, pagination_size, base_api_url, minor_version, quickbook_company_id, odoo_company_id = \
                    self.env['oqb.dry.mixin'].get_oqb_instance_data(current_instance)
                response_data, response_status = self.process_odoo_quickbook_record(quickbook_payload, access_token,
                base_api_url, quickbook_company_id,module_name, '',logger_name, operation_type,
                current_instance)
                # Update Odoo records with quickbook IDs based on the response
                if response_data:
                    success_count, operation_status = self.update_odoo_records_with_quickbook_id(quickbook_payload,
                    response_data,odoo_ids,dynamic_hashes,records_data,response_status,logger_name,module_name,
                    current_instance,operation_type,filtered_batch_records,check_hash)

                    return success_count, operation_status
                else:
                    return 0, 'no_process'
                # else:
                #     return 0, 'no_process'
            return success_count, operation_status
        except Exception as e:
            error_details = str(e)
            error_type = 'Exception Error'
            operation = f'Create/Update Odoo {logger_name.capitalize()} Record In Quickbook'
            description = f'Error occurred while sending {logger_name} record Odoo to Quickbook'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'quickbook',
            quickbook_id,operation, operation_type, current_instance.name, error_type)
            return success_count, operation_status

    # -------------------------- Update Quickbook Id in Odoo Records --------------------- #

    def update_odoo_records_with_quickbook_id(self, quickbook_payload, response_data, odoo_ids, dynamic_hashes,
            records_data, response_status, logger_name, module_name, current_instance,operation_type, partner_records,
            check_hash):
        """
            Update the Odoo records with the Quickbook ID from the Quickbook API response.
        """
        success_count, operation_status = 0, None

        # Write changes to the record
        hash_field, quickbook_id_field = self.get_sync_field_names(logger_name)

        if response_data:
            if 'BatchItemResponse' in response_data and response_data['BatchItemResponse']:
                for i, (record, odoo_id, record_data, dynamic_fields_values_hash, partner_record,
                        quickbook_record_payload) in enumerate(
                        zip(response_data['BatchItemResponse'], odoo_ids, records_data, dynamic_hashes, partner_records,
                            quickbook_payload['BatchItemRequest'])):

                    # Check if the record contains a fault/error
                    if 'Fault' in record:
                        self.odoo_to_quickbook_log_operation(logger_name, response_status, odoo_id,
                        quickbook_record_payload,'invalid_data', 'quickbook', record, operation_type,
                        current_instance.name, parent_name=None, parent_id=None)
                        continue

                    success_count += 1
                    quickbook_id = record[module_name]['Id']
                    quickbook_sync_token = record[module_name]['SyncToken']

                    if logger_name in ['sales orders', 'purchase order', 'purchase bill', 'refund', 'invoice',
                                       'credit note']:
                        quickbooks_lines = self.get_line_from_record(record)
                        if logger_name in ['sales orders', 'purchase order']:  # Sale & Purchase use 'order_line'
                            line_field = 'order_line'
                        else:  # Invoice uses 'invoice_line_ids'
                            line_field = 'invoice_line_ids'
                        # Loop through the correct lines
                        if line_field:
                            for index, item in enumerate(getattr(partner_record, line_field, [])):
                                quickbook_line = quickbooks_lines[index]

                                # Assign the QuickBooks line Id to the item
                                quickbook_line_id = quickbook_line.get('Id')

                                # Update the Odoo line item with the corresponding QuickBooks ID
                                item.write({'quickbook_id': quickbook_line_id})
                    if getattr(partner_record, quickbook_id_field):
                        existing_hash = getattr(partner_record, hash_field)

                        if existing_hash != dynamic_fields_values_hash or not check_hash:
                            operation_status, record_operation = 'update', 'update'
                        else:
                            operation_status, record_operation = 'update', 'update'
                    else:
                        operation_status, record_operation = 'create', 'insert'
                    if operation_status:
                        partner_record.write({
                            quickbook_id_field: quickbook_id,
                            hash_field: dynamic_fields_values_hash,
                            'quickbook_sync_token': quickbook_sync_token,
                        })

                        if logger_name not in ['payment method', 'customer payment', 'vendor payment']:
                            partner_record['instance_name'] = current_instance.name
                        else:
                            partner_record['instance_name'] = current_instance.id
                        partner_record.env.cr.commit()
                        # Log the operation
                        self.odoo_to_quickbook_log_operation(logger_name, response_status, odoo_id,
                        quickbook_record_payload,record_operation, 'quickbook', record, operation_type,
                        current_instance.name, parent_name=None, parent_id=None)

                return success_count, operation_status
            else:
                return success_count, operation_status
        else:
            return success_count, operation_status

    # ------------------------ Get Order Line Record -------------------- #
    def get_line_from_record(self, record):
        for key, value in record.items():
            if isinstance(value, dict):  # If the value is a dictionary, search recursively
                if 'Line' in value:  # Check if 'Line' key exists
                    return value['Line']
                else:
                    result = self.get_line_from_record(value)  # Recursive call
                    if result is not None:
                        return result
        return None  # Return None if 'Line' not found

    # ------------------------------ Sync Odoo to Quickbook Contact Records ------------------- #

    def process_odoo_partner_record(self, batch_records, current_instance, field_model_name,
                                    dropdown_field_mapping_name, is_company, module_name, logger_name, operation_type,
                                    odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='res.partner', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Chart of Account Records ------------------- #

    def process_odoo_chart_of_account_record(self, batch_records, current_instance, field_model_name,
                                             dropdown_field_mapping_name,
                                             is_company, module_name, logger_name, operation_type, odoo_company_id,
                                             check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.account', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Product Records ------------------- #

    def process_odoo_product_record(self, batch_records, current_instance, field_model_name,
                                    dropdown_field_mapping_name,
                                    is_company, module_name, logger_name, operation_type, odoo_company_id,
                                    check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='product.template', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Sale Order Records ------------------- #

    def process_odoo_sale_order_record(self, batch_records, current_instance, field_model_name,
                                       dropdown_field_mapping_name,
                                       is_company, module_name, logger_name, operation_type, odoo_company_id,
                                       check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='sale.order', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Invoice Records ------------------- #

    def process_odoo_invoice_record(self, batch_records, current_instance, field_model_name,
                                    dropdown_field_mapping_name,
                                    is_company, module_name, logger_name, operation_type, odoo_company_id,
                                    check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Customer Payment Records ------------------- #

    def process_odoo_customer_payment_record(self, batch_records, current_instance, field_model_name,
                                             dropdown_field_mapping_name,
                                             is_company, module_name, logger_name, operation_type, odoo_company_id,
                                             check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.payment', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Credit Note Records ------------------- #

    def process_odoo_credit_note_record(self, batch_records, current_instance, field_model_name,
                                        dropdown_field_mapping_name,
                                        is_company, module_name, logger_name, operation_type, odoo_company_id,
                                        check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Vendor Records ------------------- #

    def process_odoo_vendor_record(self, batch_records, current_instance, field_model_name,
                                   dropdown_field_mapping_name,
                                   is_company, module_name, logger_name, operation_type, odoo_company_id,
                                   check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='res.partner', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Purchase Order Records ------------------- #

    def process_odoo_purchase_order_record(self, batch_records, current_instance, field_model_name,
                                           dropdown_field_mapping_name, is_company, module_name, logger_name,
                                           operation_type, odoo_company_id,
                                           check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='purchase.order', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Purchase Bill Records ------------------- #

    def process_odoo_purchase_bill_record(self, batch_records, current_instance, field_model_name,
                                          dropdown_field_mapping_name, is_company, module_name, logger_name,
                                          operation_type, odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Refund Records ------------------- #

    def process_odoo_refund_record(self, batch_records, current_instance, field_model_name,
                                   dropdown_field_mapping_name, is_company, module_name, logger_name, operation_type,
                                   odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.move', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Vendor Payment Records ------------------- #

    def process_odoo_vendor_payment_record(self, batch_records, current_instance, field_model_name,
                                           dropdown_field_mapping_name, is_company, module_name, logger_name,
                                           operation_type, odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.payment', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Payment Term Records ------------------- #

    def process_odoo_payment_term_record(self, batch_records, current_instance, field_model_name,
                                         dropdown_field_mapping_name, is_company, module_name, logger_name,
                                         operation_type, odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='account.payment.term', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Payment Method Records ------------------- #

    def process_odoo_payment_method_record(self, batch_records, current_instance, field_model_name,
                                           dropdown_field_mapping_name, is_company, module_name, logger_name,
                                           operation_type, odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='payment.method', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Employee Records ------------------- #

    def process_odoo_employee_record(self, batch_records, current_instance, field_model_name,
                                     dropdown_field_mapping_name, is_company, module_name, logger_name, operation_type,
                                     odoo_company_id, check_hash):
        operation_status, success_count = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance,
            field_model_name=field_model_name, dropdown_field_mapping_name=dropdown_field_mapping_name,
            module_name=module_name, logger_name=logger_name, operation_type=operation_type,
            odoo_company_id=odoo_company_id, model_name='hr.employee', check_hash=check_hash)
        return success_count, operation_status

    # ------------------------------ Sync Odoo to Quickbook Department Records ------------------- #

    def process_odoo_department_record(self, batch_records, current_instance, field_model_name,
                                       dropdown_field_mapping_name, is_company, module_name, logger_name,
                                       operation_type, odoo_company_id, check_hash):
        success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
            batch_records=batch_records, current_instance=current_instance, field_model_name=field_model_name,
            dropdown_field_mapping_name=dropdown_field_mapping_name, module_name=module_name,
            logger_name=logger_name, operation_type=operation_type, odoo_company_id=odoo_company_id,
            model_name='hr.department', check_hash=check_hash)
        return success_count, operation_status

    # ----------------------- Get Odoo & Quickbook Currencies ------------------ #


    def get_odoo_quickbook_currencies(self, current_instance, operation_type):
        """
        Synchronizes Odoo active currencies and QuickBooks currencies,
        updating the instance fields for QuickBooks currency list and default currency.
        """
        # Fetch active Odoo currencies
        odoo_active_currency = self.env['res.currency'].search([('active', '=', True)])
        odoo_currency_names = ",".join([currency.name for currency in odoo_active_currency])
        current_instance.odoo_currency_list = odoo_currency_names

        # Fetch QuickBooks company currencies
        currency_response_data = self.fetch_company_info(current_instance, operation_type, 'companycurrency')
        home_currency_response_data = self.fetch_company_info(current_instance, operation_type, 'Preferences')

        # Extract QuickBooks home currency
        quickbook_home_currency = None
        preferences = home_currency_response_data.get("QueryResponse", {}).get("Preferences", [])
        if preferences:
            quickbook_home_currency = preferences[0].get("CurrencyPrefs", {}).get("HomeCurrency", {}).get("value")

        # Extract QuickBooks currency codes
        company_currencies = currency_response_data.get("QueryResponse", {}).get("CompanyCurrency", [])
        quickbook_currency_codes = [currency.get("Code") for currency in company_currencies]

        # Ensure home currency is included in the list
        if quickbook_home_currency and quickbook_home_currency not in quickbook_currency_codes:
            quickbook_currency_codes.append(quickbook_home_currency)

        # Update the instance fields
        current_instance.quickbook_currency_list = ",".join(quickbook_currency_codes)
        current_instance.quickbook_default_currency = quickbook_home_currency

    # ----------------------- Get Odoo Currencies ------------------ #

    def get_currency_id_from_odoo(self, odoo_quote_currency_id, current_instance, logger_name, odoo_quotation_id,
                                  quote_record_data, operation_type):
        """
        Fetch the Currency ID based on the quote currency from quickbook and Odoo's active currencies.
        """

        currency = self.env['res.currency'].search([('id', '=', odoo_quote_currency_id)], limit=1)
        currency_name = currency.name
        if current_instance.quickbook_currency_list:
            quickbook_currency_name = current_instance.quickbook_currency_list
            quickbook_currency_list = quickbook_currency_name.split(',')
            quickbook_default_currency = current_instance.quickbook_default_currency
            if currency and currency_name in quickbook_currency_list:
                return currency_name
            else:
                description = f"Your Selected Currency {currency_name} is not active currency in quickbook so we have taken default currency from quickbook" if currency_name else f"Please Select a Chart of Account Currency"
                operation = f'{logger_name.capitalize()} Record Sync Quickbook to Odoo'
                self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'quickbook',
                                                                quote_record_data, odoo_quotation_id, operation_type,
                                                                current_instance.name)
                return quickbook_default_currency
        else:
            return None

    # ----------------------- Get Quickbook Currencies ------------------ #

    def get_currency_id_from_quickbook(self, quote_currency, current_instance, logger_name, quickbook_id,
                                       response_data, operation_type):
        """
        Fetch the currency ID based on the quote currency from Zoho and Odoo's active currencies.
        """
        if current_instance.odoo_currency_list:
            odoo_currency_list = current_instance.odoo_currency_list.split(',')
            odoo_default_currency = current_instance.odoo_default_currency.name
            currency = self.env['res.currency'].search([('name', '=', quote_currency)], limit=1)
            if currency and currency.name in odoo_currency_list:
                return currency.id
            else:
                # Fallback to default currency in Odoo if the currency from Zoho is not found
                default_currency = self.env['res.currency'].search(
                    [('name', '=', odoo_default_currency), ('active', '=', True)], limit=1)
                description = f"Your Selected Currency {quote_currency} is not active currency in odoo so we have taken default currency from odoo" if quote_currency else f"Please Select a Chart of Account Currency"
                operation = f'{logger_name.capitalize()} Record Sync Zoho To Odoo'
                self.env['oqb.dry.mixin'].log_operation_warning(logger_name, description, operation, 'odoo',
                                                                response_data, quickbook_id, operation_type,
                                                                current_instance.name)
                return default_currency.id
        else:
            return None

        # -------------------- Sync Form and List View Odoo Partner Record to Quickbook ------------------- #

    def odoo_record_send_to_quickbook(self, logger_name, active_ids, odoo_model_name, quickbook_module_name):
        """
                   Sends partner records from Odoo to Quickbook. Handles both account and contact records, and logs the process.

                   This function processes active partner records in the current context and sends them to quickbook. It
                   handles the creation or updating of these records in Quickbook and logs the results.

                   Returns:
                       str: A notification message indicating the result of the synchronization process.
               """
        success_count, operation_status, record_id, current_instance, odoo_company_id, logger_config = 0, None, None, None, None, {}

        if len(active_ids) > 10:
            raise ValidationError(
                "You can only sync up to 10 records at a time to QuickBooks. Please select 10 or fewer records and try again.")
        try:
            quickbook_batch_records = []

            for record_id in active_ids:
                record = self.env[odoo_model_name].search([('id', '=', record_id)])
                if odoo_model_name == 'res.partner':
                    if record.supplier_rank > 0:
                        logger_name, quickbook_module_name = 'vendor', 'Vendor'
                    else:
                        logger_name, quickbook_module_name = 'customer', 'Customer'
                if odoo_model_name == 'account.move':
                    if record.move_type == 'out_invoice':
                        logger_name, quickbook_module_name = 'invoice', 'Invoice'
                    elif record.move_type == 'out_refund':
                        logger_name, quickbook_module_name = 'credit note', 'CreditMemo'
                    elif record.move_type == 'in_invoice':
                        logger_name, quickbook_module_name = 'purchase bill', 'Bill'
                    elif record.move_type == 'in_refund':
                        logger_name, quickbook_module_name = 'refund', 'VendorCredit'
                if odoo_model_name == 'account.payment':
                    if record.partner_type == 'customer':
                        logger_name, quickbook_module_name = 'customer payment', 'Payment'
                    else:
                        logger_name, quickbook_module_name = 'vendor payment', 'BillPayment'
                logger_config = self.env['oqb.wizard'].get_logger_mappings(logger_name, 'odoo')

                if logger_name not in ['payment method', 'customer payment',
                                       'vendor payment'] and self.env.user.is_multi_company:
                    if logger_name == 'chart of account':
                        current_instance = self.env['oqb.instance'].search(
                            [('is_connected', '=', True), ('company_name', '=', record.company_ids.ids)], limit=1)
                    else:
                        current_instance = self.env['oqb.instance'].search(
                            [('is_connected', '=', True), ('company_name', '=', record.company_id.id)], limit=1)
                elif not self.env.user.is_multi_company:
                    current_instance = self.env['oqb.instance'].search([('is_connected', '=', True)], limit=1)
                else:
                    if record.instance_name:
                        current_instance = record.instance_name
                    else:
                        operation_status = 'not_selected'
                        continue
                        # return success_count, active_ids, logger_name, 'not_selected'

                if not current_instance:
                    operation_status = 'no_instance'
                    continue

                access_token, pagination_size, base_api_url, minor_version, quickbook_company_id, odoo_company_id = \
                    self.env['oqb.dry.mixin'].get_oqb_instance_data(current_instance)

                is_connected, notification = current_instance.test_connection_methods(
                    f'Manual {logger_name.capitalize()} Sync Odoo to Quickbook', logger_name, 'quickbook', 'manually',
                    current_instance)

                # If the connection failed (is_connected is False), return the notification
                if not is_connected:
                    operation_status = 'no_connection'
                    continue

                if record.sync_to_quickbook is False:
                    warning_message = f"'Sync to Quickbook' is True required for {logger_name.capitalize()}."
                    operation = f'Manual {logger_name.capitalize()} Push Odoo To Quickbook'
                    self.env['oqb.dry.mixin'].log_operation_warning(logger_name, warning_message, operation,
                                                                    'quickbook', record, record_id, 'manually',
                                                                    current_instance.name)
                    continue

                quickbook_batch_records.append(record)

            # Process company records
            if quickbook_batch_records:
                success_count, operation_status = self.env['oqb.dry.mixin'].process_odoo_record(
                    quickbook_batch_records, current_instance, logger_config['field_model_name'],
                    logger_config['dropdown_field_mapping_name'], quickbook_module_name, logger_name, 'manually',
                    odoo_company_id, 'res.partner', check_hash=False)

            return success_count, active_ids, logger_name, operation_status

        except Exception as e:
            # create a record in QuickbookLogger to store the error data
            error_details = str(e)
            error_type = 'Exception Error'
            description = f'Error occurred while {logger_name} create/update in Quickbook.'
            operation = f'Sync Manual {logger_name.capitalize()} Record Odoo to Quickbook'
            self.env['oqb.dry.mixin'].exception_log_error(error_details, logger_name, description, 'quickbook',
                                                          record_id, operation, 'manually', error_type)
        return success_count, active_ids, logger_name, operation_status

    # ------------------------------ Method For Sync Notification ----------------------- #

    def generate_sync_notification(self, success_count, active_ids, logger_name, operation_status):
        """
            Generate a synchronization notification.

            This method creates a notification message based on the synchronization results. It constructs a message
            detailing the number of records created, updated, and failed during the synchronization process. Depending on
            the success of the synchronization, it returns a notification action with either a success, partial success,
            or failure message.

            Args:
                success_count (int): Number of records that were successfully created or updated.
                operation_status (str): Status of the operation ('create', 'update', 'fail').
                logger_name (str): The name of the entity being synced (e.g., 'account' or 'contact').

            Returns:
                dict: A dictionary containing the notification action. The action includes the type of notification
                      (success or danger), the title, the message, and whether the notification is sticky or not.
            """
        total_records = len(active_ids)  # Total records attempted to sync
        logger_name_capitalize = logger_name.capitalize()

        if int(total_records) == 0:
            # No records were processed
            message = 'No records have been selected for synchronization.'
        elif int(success_count) == int(total_records):
            # All records were successfully processed
            if success_count == 1:
                message = f'{logger_name_capitalize} record have successfully created/updated.'
            else:
                message = f'{success_count} {logger_name_capitalize} records have successfully created/updated.'
        elif int(success_count) > 0:
            # Some records were processed,  but some failed
            message = f'{success_count} {logger_name_capitalize} records have successfully created/updated, but {total_records - success_count} failed.'
        elif operation_status == 'no_action' and logger_name in ['customer']:
            message = f'The Email ID is already associated with another {logger_name}. Please use a different email ID.'
        elif operation_status == 'no_action' and logger_name == 'product':
            message = (f'The product code is already associated with another {logger_name}. Please use a different '
                       f'product code.')
        elif operation_status == 'no_account':
            message = f"Failed to create {logger_name} in Quickbook. Income & Expense Account field is required for {logger_name} record"
        elif operation_status == 'no_process':
            message = f"{logger_name.capitalize()}: Synchronization could not be processed due to an error. Please check the logger"
        elif operation_status == 'no_field_data':
            message = f'{logger_name_capitalize} Field Data Not Mapped'
        elif operation_status == 'no_connection':
            message = f'Failed to complete the operation. Check the API Token or try again.'
        elif operation_status == 'no_instance':
            message = f"'The 'Is Connected' field is set to True, and the 'Company Id' field is required to find the instance."
        elif operation_status == 'not_selected':
            message = f"Please Select Instance Name"
        elif operation_status == "sync_process_id":
             message = (
                    "Chart of Account already exists in QuickBooks with the same name. "
                    "The existing QuickBooks account has been linked to the Odoo record "
                    "by updating the QuickBooks ID. No new account was created."
                )
        else:
            # No records were successfully processed
            message = f'Failed to create/update {logger_name_capitalize} record.'

        if operation_status in ['no_action', 'no_field_data', 'no_connection', 'no_instance', 'not_selected',
                                'no_account', 'sync_process_id']:
            notification_type = 'warning'
        elif operation_status == 'no_process':
            notification_type = 'danger'
        else:
            notification_type = 'success' if int(success_count) == int(total_records) else 'danger'
        notification_title = f'{logger_name_capitalize} Sync Successful' if int(success_count) == int(
            total_records) else f'{logger_name_capitalize} not Synced'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(notification_title),
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }

    # ---------------------- Process Odoo Related Records ---------------------- #

    def odoo_related_record(self, odoo_record, odoo_model_name, current_instance, field_model_name,
                            dropdown_field_mapping_name, operation_type, odoo_company_id, check_hash, logger_name,
                            related_logger_name, module_name):
        if odoo_record:
            if not odoo_record.quickbook_id:
                if odoo_record.sync_to_quickbook == True:
                    # Sync product_record to quickbook and get quickbook_id
                    self.env['oqb.dry.mixin'].process_odoo_record(
                        batch_records=odoo_record, current_instance=current_instance,
                        field_model_name=field_model_name, dropdown_field_mapping_name=dropdown_field_mapping_name,
                        module_name=module_name, logger_name=related_logger_name, operation_type=operation_type,
                        odoo_company_id=odoo_company_id, model_name=odoo_model_name, check_hash=check_hash)
                    return 'record_processed', odoo_record
                else:
                    description = f"'Sync to Quickbook' is True required for {logger_name.capitalize()} related {related_logger_name.capitalize()}"
                    operation = f'{logger_name.capitalize()} Record Sync Odoo To Quickbook'
                    self.log_operation_warning(related_logger_name, description, operation,
                                               'quickbook', '', odoo_record.id, operation_type, current_instance.name)
                    return 'no_process', odoo_record
            else:
                return 'processed', odoo_record
        else:
            return 'no_record', odoo_record




