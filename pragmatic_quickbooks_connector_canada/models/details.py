from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quickbook_id = fields.Integer(string="QuickBooks Id", copy=False)
    total = fields.Float('Total Amount', copy=False)
    check = fields.Boolean(string="Add Global Discount", copy=False)
    discount_type = fields.Selection([('percentage', 'Percentage'), ('value', 'Value')])
    amount = fields.Float('Amount', copy=False)
    percentage_amt = fields.Float('Amt', copy=False)

    tax_state = fields.Selection(
        [('inclusive', 'Tax Inclusive'), ('exclusive', 'Tax Exclusive'), ('notapplicable', 'Not Applicable')],
        string='Tax Status', default="exclusive")

    @api.model_create_multi  # DETAIL WARNING ISSUE
    def create(self, vals):
        discount_per = 0.0
        res = super(SaleOrder, self).create(vals)

        if res.check:
            if res.discount_type and res.amount:
                # Create Account for Discount
                account_id = self.env['account.account'].search([('name', '=', 'Discount')])
                if not account_id:
                    create_account = account_id.create({
                        'code': 171274,
                        'name': 'Discount',
                        'user_type_id': 6,
                    })

                # Create Discount Product
                res_product = self.env['product.product'].search([('is_discount_product', '=', True)], limit=1)
                if not res_product:
                    create_product = res_product.create({
                        'name': 'Discount',
                        'is_discount_product': True,
                        'taxes_id': 0,
                        'type': 'service',
                    })

                # Add Product line
                res_product = self.env['product.product'].search([('is_discount_product', '=', True)], limit=1)
                if not res_product:
                    raise UserError("There is no discount product available, Please add discount product")

                account = self.env['account.account'].search([('name', '=', 'Discount')])
                if res.discount_type == 'percentage':

                    sale_order_line = {
                        'product_id': res_product.id,
                        'account_id': account.id,
                        'order_id': res.id,
                        'name': 'Discount',
                        'price_unit': -res.percentage_amt,
                        'tax_id': 0,
                    }
                    so_line_id = self.env['sale.order.line'].create(sale_order_line)
                else:
                    sale_order_line = {
                        'product_id': res_product.id,
                        'account_id': account.id,
                        'order_id': res.id,
                        'name': 'Discount',
                        'price_unit': -res.amount,
                        'tax_id': 0,
                    }
                    so_line_id = self.env['sale.order.line'].create(sale_order_line)
            else:
                _logger.info(_("Please select discount type and amount"))
        return res

    def write(self, vals):
        discount_per = 0.0
        res = super(SaleOrder, self).write(vals)

        if vals.get('check'):
            if vals.get('discount_type') and vals.get('amount'):

                # Search for Sale orders on which discount is applied
                if vals.get('quickbook_id'):
                    qb_id = vals.get('quickbook_id')
                    sale_order = self.env['sale.order'].search([('quickbook_id', '=', qb_id)])

                # Create Account for Discount
                account_id = self.env['account.account'].search([('name', '=', 'Discount')])
                if not account_id:
                    create_account = account_id.create({
                        'code': 171274,
                        'name': 'Discount',
                        'user_type_id': 6,
                    })

                # Create Discount Product
                res_product = self.env['product.product'].search([('is_discount_product', '=', True)], limit=1)
                if not res_product:
                    create_product = res_product.create({
                        'name': 'Discount',
                        'is_discount_product': True,
                        'taxes_id': 0,
                        'type': 'service',
                    })

                product = self.env['product.product'].search([('is_discount_product', '=', True)], limit=1)
                discount_line = self.env['sale.order.line'].search(
                    [('product_id', '=', product.id), ('order_id', '=', sale_order.id)], limit=1)

                if not discount_line:
                    res_product = self.env['product.product'].search([('is_discount_product', '=', True)], limit=1)
                    if not res_product:
                        raise UserError("There is no discount product available, Please add discount product")
                    account = self.env['account.account'].search([('name', '=', 'Discount')])
                    if vals.get('discount_type') == 'percentage':
                        sale_order_line = {
                            'product_id': res_product.id,
                            'account_id': account.id,
                            'order_id': sale_order.id,
                            'name': 'Discount',
                            'price_unit': -vals.get('percentage_amt'),
                            'tax_id': 0,
                        }
                        so_line_id = self.env['sale.order.line'].create(sale_order_line)
                        if so_line_id:
                            _logger.info("Discount created Successfully...!!!!!!!!!!!!!!!!")
                    else:
                        sale_order_line = {
                            'product_id': res_product.id,
                            'account_id': account.id,
                            'order_id': sale_order.id,
                            'name': 'Discount',
                            'price_unit': -vals.get('amount'),
                            'tax_id': 0,
                        }
                        so_line_id = self.env['sale.order.line'].create(sale_order_line)
                        if so_line_id:
                            _logger.info("Discount created Successfully...!!!!!!!!!!!!!!!!")
                else:
                    res_product = self.env['product.product'].search([('is_discount_product', '=', True)], limit=1)
                    if not res_product:
                        raise UserError("There is no discount product available, Please add discount product")
                    account = self.env['account.account'].search([('name', '=', 'Discount')])

                    if vals.get('discount_type') == 'percentage':
                        sale_order_line = {
                            'product_id': res_product.id,
                            'account_id': account.id,
                            'order_id': sale_order.id,
                            'name': 'Discount',
                            'price_unit': -vals.get('percentage_amt'),
                            'tax_id': 0,
                        }
                        so_line_id = discount_line.write(sale_order_line)
                        if so_line_id:
                            _logger.info("Discount updated Successfully...!!!!!!!!!!!!!!!!")
                    else:
                        sale_order_line = {
                            'product_id': res_product.id,
                            'account_id': account.id,
                            'order_id': sale_order.id,
                            'name': 'Discount',
                            'price_unit': -vals.get('amount'),
                            'tax_id': 0,
                        }
                        so_line_id = discount_line.write(sale_order_line)
                        if so_line_id:
                            _logger.info("Discount updated Successfully...!!!!!!!!!!!!!!!!")
            else:
                _logger.info(_("Please select discount type and amount"))
        return res


class SalerOderLine(models.Model):
    _inherit = 'sale.order.line'

    qb_id = fields.Integer(string="QuickBooks Id", copy=False)


class Invoice(models.Model):
    _inherit = 'account.move'

    total = fields.Float('Total Amount', copy=False)
    check = fields.Boolean(string="Add Global Discount", copy=False)
    discount_type = fields.Selection([('percentage', 'Percentage'), ('value', 'Value')])
    amount = fields.Float('Amount', copy=False)
    percentage_amt = fields.Float('Amt', copy=False)




class InvoiceLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals):
        if vals:
            _logger.info(
                "\nACC MOVE LINE INVVals :--------------------------------------------------------------> {} ".format(
                    vals))
            res = super(InvoiceLine, self).create(vals)
        else:
            res = self
        return res

    qb_id = fields.Integer(string="QuickBooks Id", copy=False)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    quickbook_id = fields.Integer(string="QuickBooks Id", copy=False)
    product_id = fields.Many2one('product.product', related='order_line.product_id')


class PurchaseOderLine(models.Model):
    _inherit = 'purchase.order.line'

    qb_id = fields.Char(string="QuickBooks Id", copy=False)


class Employee(models.Model):
    _inherit = "hr.employee"

    sync_id = fields.Integer(string="Sync Token ", copy=False)
    ssn = fields.Char(string="SSN ", copy=False)
    quickbook_id = fields.Integer(string="Quickbook id", copy=False)
    hired_date = fields.Date(string="Hired Date", copy=False)
    released_date = fields.Date(string="Released Date", copy=False)
    billing_rate = fields.Float(string="Billing Rate", copy=False)
    employee_no = fields.Char(string="Employee No", copy=False)


class Department(models.Model):
    _inherit = "hr.department"

    quickbook_id = fields.Integer(string="QuickBooks Id", copy=False)

    @api.model
    def get_qbo_dept_ref(self, dept):
        if dept.quickbook_id:
            return dept.quickbook_id
        else:
            raise ValidationError(_("Department not exported to QBO."))


class ProductTem(models.Model):
    _inherit = 'product.template'

    is_discount_product = fields.Boolean(string="Is Discount Product", copy=False)
