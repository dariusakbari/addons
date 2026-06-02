from odoo import api, fields, models


class ChartOfAccountMapper(models.Model):
    """
        ChartOfAccountMapper Model
        This model represents a mapping between chart of account fields in Odoo and Quickbook.
    """
    _name = "oqb.coa.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Chart of Account Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_chart_of_account_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_account',
            'Account',self.env['oqb.coa.mapper'], instance_id, 'coa_mapper_id', 'oqb.coa.lines', 'chart of account')

class CustomerMapper(models.Model):
    """
        CustomerMapper Model
        This model represents a mapping between customer fields in Odoo and Quickbook.
    """
    _name = "oqb.customer.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Customer Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_customer_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('res_partner',
            'Customer',self.env['oqb.customer.mapper'], instance_id, 'customer_mapper_id', 'oqb.customer.lines', 'customer')


class ProductMapper(models.Model):
    """
        ProductMapper Model
        This model represents a mapping between customer fields in Odoo and Quickbook.
    """
    _name = "oqb.product.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_product_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('product_template',
            'Item',self.env['oqb.product.mapper'], instance_id, 'product_mapper_id', 'oqb.product.lines', 'product')

class SalesReceiptMapper(models.Model):
    """
        SalesReceiptMapper Model
        This model represents a mapping between Sale Order fields in Odoo and Quickbook.
    """
    _name = "oqb.salereceipt.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sale Order Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_sale_receipt_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('sale_order',
            'Estimate',self.env['oqb.salereceipt.mapper'], instance_id, 'sale_order_mapper_id', 'oqb.saleorder.lines', 'sales orders')


class InvoiceMapper(models.Model):
    """
        InvoiceMapper Model
        This model represents a mapping between Invoice fields in Odoo and Quickbook.
    """
    _name = "oqb.invoice.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Invoice Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_invoice_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_move',
            'Invoice',self.env['oqb.invoice.mapper'], instance_id, 'invoice_mapper_id', 'oqb.invoice.lines', 'invoice')

class CreditNoteMapper(models.Model):
    """
        CreditNoteMapper Model
        This model represents a mapping between Credit Note fields in Odoo and Quickbook.
    """
    _name = "oqb.cdt.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Credit Note Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_credit_note_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_move','CreditMemo',
            self.env['oqb.cdt.mapper'], instance_id, 'credit_note_mapper_id', 'oqb.cdt.lines', 'credit note')

class CustomerPaymentMapper(models.Model):
    """
        CustomerPaymentMapper Model
        This model represents a mapping between Customer Payment fields in Odoo and Quickbook.
    """
    _name = "oqb.cpt.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Customer Payment Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_customer_payment_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_payment',
            'Payment',self.env['oqb.cpt.mapper'], instance_id, 'cpt_mapper_id', 'oqb.cpt.lines', 'customer payment')

class VendorMapper(models.Model):
    """
        VendorMapper Model
        This model represents a mapping between Vendor fields in Odoo and Quickbook.
    """
    _name = "oqb.vendor.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vendor Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_vendor_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('res_partner','Vendor',
        self.env['oqb.vendor.mapper'], instance_id, 'vendor_mapper_id', 'oqb.vendor.lines', 'vendor')

class PurchaseOrderMapper(models.Model):
    """
        PurchaseOrderMapper Model
        This model represents a mapping between Purchase Order fields in Odoo and Quickbook.
    """
    _name = "oqb.purchaseorder.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Order Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_purchase_order_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('purchase_order','PurchaseOrder',
        self.env['oqb.purchaseorder.mapper'], instance_id, 'pco_mapper_id', 'oqb.pco.lines', 'purchase order')

class PurchaseBillMapper(models.Model):
    """
        PurchaseBillMapper Model
        This model represents a mapping between Purchase Bill fields in Odoo and Quickbook.
    """
    _name = "oqb.purchasebill.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vendor Bill Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_purchase_bill_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_move',
        'Bill',self.env['oqb.purchasebill.mapper'], instance_id, 'pcb_mapper_id', 'oqb.pcb.lines', 'purchase bill')


class RefundMapper(models.Model):
    """
        RefundMapper Model
        This model represents a mapping between Refund fields in Odoo and Quickbook.
    """
    _name = "oqb.refund.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Refund Mapper"
    _rec_name = 'internal_name'

    
    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_refund_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_move',
            'VendorCredit', self.env['oqb.refund.mapper'], instance_id, 'refund_mapper_id', 'oqb.refund.lines', 'refund')

class VendorPaymentMapper(models.Model):
    """
        VendorPaymentMapper Model
        This model represents a mapping between Vendor Payment fields in Odoo and Quickbook.
    """
    _name = "oqb.vpt.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vendor Payment Mapper"
    _rec_name = 'internal_name'

    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_vendor_payment_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_payment',
            'BillPayment',self.env['oqb.vpt.mapper'], instance_id, 'vpt_mapper_id', 'oqb.vpt.lines', 'vendor payment')

class PaymentTermMapper(models.Model):
    """
        PaymentTermMapper Model
        This model represents a mapping between Payment Term fields in Odoo and Quickbook.
    """
    _name = "oqb.pyt.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payment Term Mapper"
    _rec_name = 'internal_name'

    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_payment_term_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_payment_term',
        'Term',self.env['oqb.pyt.mapper'], instance_id, 'pyt_mapper_id', 'oqb.pyt.lines', 'payment term')

class PaymentMethodMapper(models.Model):
    """
        PaymentMethodMapper Model
        This model represents a mapping between Payment Method fields in Odoo and Quickbook.
    """
    _name = "oqb.pym.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payment Method Mapper"
    _rec_name = 'internal_name'

    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_payment_method_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('payment_method',
            'PaymentMethod',self.env['oqb.pym.mapper'], instance_id, 'pym_mapper_id', 'oqb.pym.lines', 'payment method')

class AccountTaxMapper(models.Model):
    """
        AccountTaxMapper Model
        This model represents a mapping between Account Tax fields in Odoo and Quickbook.
    """
    _name = "oqb.atx.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Account Tax Mapper"
    _rec_name = 'internal_name'

    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_account_tax_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('account_tax',
            'TaxCode',self.env['oqb.atx.mapper'], instance_id, 'atx_mapper_id', 'oqb.atx.lines', 'account tax')

class EmployeeMapper(models.Model):
    """
        EmployeeMapper Model
        This model represents a mapping between Employee fields in Odoo and Quickbook.
    """
    _name = "oqb.employee.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Mapper"
    _rec_name = 'internal_name'

    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_employee_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('hr_employee',
        'Employee',self.env['oqb.employee.mapper'], instance_id, 'employee_mapper_id', 'oqb.employee.lines', 'employee')

class DepartmentMapper(models.Model):
    """
        DepartmentMapper Model
        This model represents a mapping between Department fields in Odoo and Quickbook.
    """
    _name = "oqb.department.mapper"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Department Mapper"
    _rec_name = 'internal_name'

    label_name = fields.Char(string='Label Name', tracking=True)
    field_type = fields.Char(string='Field Type', tracking=True)
    quickbook_instance_name = fields.Char(string='Instance Name', tracking=True)
    system_name = fields.Char(string='System Name', tracking=True)
    internal_name = fields.Char(string='Internal Name')
    field_definition = fields.Text(string='Field Description')

    @api.model
    def fetch_and_store_department_fields(self, instance_id):
        return self.env['oqb.dry.mixin'].fetch_and_store_oqb_fields('hr_department',
        'Department',self.env['oqb.department.mapper'], instance_id, 'dpt_mapper_id', 'oqb.dpt.lines', 'department')