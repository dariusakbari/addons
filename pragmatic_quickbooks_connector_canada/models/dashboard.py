from odoo import models, api, fields, _
import json
from dateutil.relativedelta import relativedelta
import datetime as DT


class MyClass:

    @classmethod
    def get_pending_order_sale_purchase_counts(cls, element, self):
        """ DASHBOARD FIRST BLOCK TOTAL ORDER For Purchse and sale COUNT LEVEL"""
        purchase_count = 0
        sale_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        if 'purchase.order' == self._name:
            purchase_obj = self.search([('state', '=', 'purchase'), ('quickbook_id', '!=', False), ])
            for po in purchase_obj:
                if element == 'last_month':
                    if po.date_approve.date() <= today and po.date_approve.date() >= month_ago:
                        purchase_count += 1
                elif element == 'last_week':
                    if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                        purchase_count += 1
                elif element == 'today':
                    if po.date_approve.date() == today:
                        purchase_count += 1
                else:
                    if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                        purchase_count += 1
            return purchase_count
        if 'sale.order' == self._name:
            sale_obj = self.search([('state', '=', 'sale'), ('quickbook_id', '!=', False)])
            for so in sale_obj:
                if element == 'last_month':
                    if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                        sale_count += 1
                elif element == 'last_week':
                    if so.date_order.date() <= today and so.date_order.date() >= week_ago:
                        sale_count += 1
                elif element == 'today':
                    if so.date_order.date() == today:
                        sale_count += 1
                else:
                    if so.date_order.date() <= today and so.date_order.date() >= six_month_ago:
                        sale_count += 1
            return sale_count

    @classmethod
    def get_total_order_id(cls, element, self):
        """RETURN ID FOR DASHBOARD FIRST BLOCK SALE AND PURCHASE"""
        purchase_id = []
        sale_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        if 'purchase.order' == self._name:
            purchase_obj = self.search([('state', '=', 'purchase'), ('quickbook_id', '!=', False), ])
            for po in purchase_obj:
                if element == 'last_month':
                    if po.date_approve.date() <= today and po.date_approve.date() >= month_ago:
                        purchase_id.append(po.id)
                elif element == 'last_week':
                    if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                        purchase_id.append(po.id)
                elif element == 'today':
                    if po.date_approve.date() == today:
                        purchase_id.append(po.id)
                else:
                    if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                        purchase_id.append(po.id)
            return purchase_id
        if 'sale.order' == self._name:
            sale_obj = self.search([('state', '=', 'sale'), ('quickbook_id', '!=', False)])
            for so in sale_obj:
                if element == 'last_month':
                    if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                        sale_id.append(so.id)
                elif element == 'last_week':
                    if so.date_order.date() <= today and so.date_order.date() >= week_ago:
                        sale_id.append(so.id)
                elif element == 'today':
                    if so.date_order.date() == today:
                        sale_id.append(so.id)
                else:
                    if so.date_order.date() <= today and so.date_order.date() >= six_month_ago:
                        sale_id.append(so.id)
            return sale_id



    @classmethod
    def waiting_bill_invoice_count(cls, element, self):
        """DASHBOARD second Block count for sale and purchase"""
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        count = 0
        if 'purchase.order' == self._name:
            purchase_obj = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
            if purchase_obj:
                for po in purchase_obj:
                    if po.invoice_count == 0:
                        if element == 'last_month':
                            if po.date_approve.date() <= today and po.date_approve.date() >= month_ago:
                                count += 1
                        elif element == 'last_week':
                            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                                count += 1
                        elif element == 'today':
                            if po.date_approve.date() == today:
                                count += 1
                        else:
                            if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                                count += 1
        if 'sale.order' == self._name:
            sale_obj = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
            if sale_obj:
                for so in sale_obj:
                    if so.invoice_count == 0:
                        if element == 'last_month':
                            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                                count += 1
                        elif element == 'last_week':
                            if so.date_order.date() <= today and so.date_order.date() >= week_ago:
                                count += 1
                        elif element == 'today':
                            if so.date_order.date() == today:
                                count += 1
                        else:
                            if so.date_order.date() <= today and so.date_order.date() >= six_month_ago:
                                count += 1
        return count




    @classmethod
    def get_waiting_bill_invoice_id(cls, element, self):
        """DASHBOARD SEWCOND BLOCK RETURN ID FOR PURCHASE AND SALE"""
        purchase_id = []
        sale_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        if 'purchase.order' == self._name:
            purchase_obj = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
            if purchase_obj:
                for po in purchase_obj:
                    if po.invoice_count == 0:
                        if element == 'last_month':
                            if po.date_approve.date() <= today and po.date_approve.date() >= month_ago:
                                purchase_id.append(po.id)
                        elif element == 'last_week':
                            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                                purchase_id.append(po.id)
                        elif element == 'today':
                            if po.date_approve.date() == today:
                                purchase_id.append(po.id)
                        else:
                            if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                                purchase_id.append(po.id)
                        return purchase_id
        if 'sale.order' == self._name:
            sale_obj = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
            if sale_obj:
                for so in sale_obj:
                    if so.invoice_count == 0:
                        if element == 'last_month':
                            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                                sale_id.append(so.id)
                        elif element == 'last_week':
                            if so.date_order.date() <= today and so.date_order.date() >= week_ago:
                                sale_id.append(so.id)
                        elif element == 'today':
                            if so.date_order.date() == today:
                                sale_id.append(so.id)
                        else:
                            if so.date_order.date() <= today and so.date_order.date() >= six_month_ago:
                                sale_id.append(so.id)
                        return sale_id


class PurchaseOrderExtended(models.Model):
    _inherit = "purchase.order"

    @api.model
    def get_waiting_bill_counts(self, element):
        result = MyClass.waiting_bill_invoice_count(element, self)
        return result

    @api.model
    def get_waiting_bill_id(self, element):
        result = MyClass.get_waiting_bill_invoice_id(element, self)
        return result

    @api.model
    def get_pending_order_counts(self, element):
        result = MyClass.get_pending_order_sale_purchase_counts(element, self)
        return result

    @api.model
    def get_purchase_id(self, element):
        result = MyClass.get_total_order_id(element, self)
        return result


    def purchase_piechart_month_detail(self):
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=30)
        purchase_total_count = 0
        purchase_draft_count = 0
        purchase_purchase_count = 0
        purchase_done_count = 0
        purchase_total = self.search([('quickbook_id', '!=', False), ])
        for po in purchase_total:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_total_count += 1
        purchase_draft = self.search([('quickbook_id', '!=', False), ('state', '=', 'draft')])
        for po in purchase_draft:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_draft_count += 1
        purchase_purchase = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
        for po in purchase_purchase:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_purchase_count += 1
        purchase_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for po in purchase_done:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_done_count += 1
        if purchase_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Purchase', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * purchase_draft_count / purchase_total_count],
                          ['Purchase', 100 * purchase_purchase_count / purchase_total_count],
                          ['Done', 100 * purchase_done_count / purchase_total_count]]

        return dataPoints

    def purchase_piechart_week_detail(self):
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        purchase_total_count = 0
        purchase_draft_count = 0
        purchase_purchase_count = 0
        purchase_done_count = 0
        purchase_total = self.search([('quickbook_id', '!=', False), ])
        for po in purchase_total:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_total_count += 1
        purchase_draft = self.search([('quickbook_id', '!=', False), ('state', '=', 'draft')])
        for po in purchase_draft:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_draft_count += 1
        purchase_purchase = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
        for po in purchase_purchase:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_purchase_count += 1
        purchase_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for po in purchase_done:
            if po.date_approve.date() <= today and po.date_approve.date() >= week_ago:
                purchase_done_count += 1
        if purchase_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Purchase', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * purchase_draft_count / purchase_total_count],
                          ['Purchase', 100 * purchase_purchase_count / purchase_total_count],
                          ['Done', 100 * purchase_done_count / purchase_total_count]]

        return dataPoints

    def purchase_piechart_today_detail(self):
        today = DT.date.today()
        purchase_total_count = 0
        purchase_draft_count = 0
        purchase_purchase_count = 0
        purchase_done_count = 0
        purchase_total = self.search([('quickbook_id', '!=', False), ])
        for po in purchase_total:
            if po.date_approve.date() == today:
                purchase_total_count += 1
        purchase_draft = self.search([('quickbook_id', '!=', False), ('state', '=', 'draft')])
        for po in purchase_draft:
            if po.date_approve.date() == today:
                purchase_draft_count += 1
        purchase_purchase = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
        for po in purchase_purchase:
            if po.date_approve.date() == today:
                purchase_purchase_count += 1
        purchase_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for po in purchase_done:
            if po.date_approve.date() == today:
                purchase_done_count += 1
        if purchase_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Purchase', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * purchase_draft_count / purchase_total_count],
                          ['Purchase', 100 * purchase_purchase_count / purchase_total_count],
                          ['Done', 100 * purchase_done_count / purchase_total_count]]

        return dataPoints

    def purchase_piechart_six_month_detail(self):
        today = DT.date.today()
        six_month_ago = today - DT.timedelta(days=180)
        purchase_total_count = 0
        purchase_draft_count = 0
        purchase_purchase_count = 0
        purchase_done_count = 0
        purchase_total = self.search([('quickbook_id', '!=', False), ])
        for po in purchase_total:
            if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                purchase_total_count += 1
        purchase_draft = self.search([('quickbook_id', '!=', False), ('state', '=', 'draft')])
        for po in purchase_draft:
            if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                purchase_draft_count += 1
        purchase_purchase = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
        for po in purchase_purchase:
            if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                purchase_purchase_count += 1
        purchase_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for po in purchase_done:
            if po.date_approve.date() <= today and po.date_approve.date() >= six_month_ago:
                purchase_done_count += 1
        if purchase_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Purchase', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * purchase_draft_count / purchase_total_count],
                          ['Purchase', 100 * purchase_purchase_count / purchase_total_count],
                          ['Done', 100 * purchase_done_count / purchase_total_count]]

        return dataPoints

    @api.model
    def purchase_piechart_detail(self, total_order, paid_order, unpaid_order, waiting_bill):
        if total_order == 0:
            dataPoints = [['State', 'Mhl'],
                          ['WAITING FOR CREATE BILLS', 0],
                          ['PAID', 0],
                          ['UNPAID', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['WAITING FOR CREATE BILLS', 100 * waiting_bill / total_order],
                          ['PAID', 100 * paid_order / total_order],
                          ['UNPAID', 100 * unpaid_order / total_order]]
        return dataPoints

    @api.model
    def get_completed_order_counts(self):
        purchase_obj = self.search_count([('state', '=', 'done'), ('quickbook_id', '!=', False)])
        return purchase_obj

    @api.model
    def get_purchase_order_details(self, element):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        week_ago = today - DT.timedelta(days=7)
        six_month = today - DT.timedelta(days=180)
        summary_dict = {}
        quotation_number = []
        create_date = []
        total = []
        status = []
        purchase_obj = self.search([('quickbook_id', '!=', False), ('state', '=', 'purchase')])
        for result in purchase_obj:
            if element == 'last_month':
                if result.date_approve.date() <= today and result.date_approve.date() >= month_ago:
                    quotation_number.append(result.name)
                    create_date.append(result.date_planned.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
                    status.append(result.state)
            elif element == 'last_week':
                if result.date_approve.date() <= today and result.date_approve.date() >= week_ago:
                    quotation_number.append(result.name)
                    create_date.append(result.date_planned.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
                    status.append(result.state)
            elif element == 'today':
                if result.date_approve.date() == today:
                    quotation_number.append(result.name)
                    create_date.append(result.date_planned.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
                    status.append(result.state)
            else:
                if result.date_approve.date() <= today and result.date_approve.date() >= six_month:
                    quotation_number.append(result.name)
                    create_date.append(result.date_planned.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
                    status.append(result.state)
        summary_dict['quotation_number'] = quotation_number
        summary_dict['create_date'] = create_date
        summary_dict['total'] = total
        summary_dict['status'] = status
        return summary_dict


class SaleOrderExtended(models.Model):
    _inherit = "sale.order"

    def unlink(self):
        company = self.env['res.company'].search([('id', '=', self.company_id.id)])
        company.write({'quickbooks_last_sale_imported_id': None})
        return super(SaleOrderExtended, self).unlink()


    @api.model
    def get_waiting_invoice_counts(self, element):
        result = MyClass.waiting_bill_invoice_count(element, self)
        return result

    @api.model
    def get_waiting_invoice_id(self, element):
        result = MyClass.get_waiting_bill_invoice_id(element, self)
        return result

    def sale_piechart_month_detail(self):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        sale_total_count = 0
        sale_draft_count = 0
        sale_sale_count = 0
        sale_done_count = 0
        sale_total = self.search([('quickbook_id', '!=', False)])
        for so in sale_total:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_total_count += 1
        sale_draft = self.search([('quickbook_id', '!=', False), ('state', 'in', ['draft'])])
        for so in sale_draft:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_draft_count += 1
        sale_sale = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
        for so in sale_sale:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_sale_count += 1
        sale_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for so in sale_done:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_done_count += 1
        if sale_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Sale', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * sale_draft_count / sale_total_count],
                          ['Sale', 100 * sale_sale_count / sale_total_count],
                          ['Done', 100 * sale_done_count / sale_total_count]]
        return dataPoints

    def sale_piechart_week_detail(self):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=7)
        sale_total_count = 0
        sale_draft_count = 0
        sale_sale_count = 0
        sale_done_count = 0
        sale_total = self.search([('quickbook_id', '!=', False)])
        for so in sale_total:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_total_count += 1
        sale_draft = self.search([('quickbook_id', '!=', False), ('state', 'in', ['draft'])])
        for so in sale_draft:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_draft_count += 1
        sale_sale = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
        for so in sale_sale:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_sale_count += 1
        sale_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for so in sale_done:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_done_count += 1
        if sale_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Sale', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * sale_draft_count / sale_total_count],
                          ['Sale', 100 * sale_sale_count / sale_total_count],
                          ['Done', 100 * sale_done_count / sale_total_count]]
        return dataPoints

    def sale_piechart_today_detail(self):
        today = DT.date.today()
        sale_total_count = 0
        sale_draft_count = 0
        sale_sale_count = 0
        sale_done_count = 0
        sale_total = self.search([('quickbook_id', '!=', False)])
        for so in sale_total:
            if so.date_order.date() == today:
                sale_total_count += 1
        sale_draft = self.search([('quickbook_id', '!=', False), ('state', 'in', ['draft'])])
        for so in sale_draft:
            if so.date_order.date() == today:
                sale_draft_count += 1
        sale_sale = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
        for so in sale_sale:
            if so.date_order.date() == today:
                sale_sale_count += 1
        sale_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for so in sale_done:
            if so.date_order.date() == today:
                sale_done_count += 1
        if sale_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Sale', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * sale_draft_count / sale_total_count],
                          ['Sale', 100 * sale_sale_count / sale_total_count],
                          ['Done', 100 * sale_done_count / sale_total_count]]
        return dataPoints

    def sale_piechart_six_month_detail(self):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=180)
        sale_total_count = 0
        sale_draft_count = 0
        sale_sale_count = 0
        sale_done_count = 0
        sale_total = self.search([('quickbook_id', '!=', False)])
        for so in sale_total:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_total_count += 1
        sale_draft = self.search([('quickbook_id', '!=', False), ('state', 'in', ['draft'])])
        for so in sale_draft:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_draft_count += 1
        sale_sale = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
        for so in sale_sale:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_sale_count += 1
        sale_done = self.search([('quickbook_id', '!=', False), ('state', '=', 'done')])
        for so in sale_done:
            if so.date_order.date() <= today and so.date_order.date() >= month_ago:
                sale_done_count += 1
        if sale_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Sale', 0],
                          ['Done', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * sale_draft_count / sale_total_count],
                          ['Sale', 100 * sale_sale_count / sale_total_count],
                          ['Done', 100 * sale_done_count / sale_total_count]]
        return dataPoints

    @api.model
    def sale_piechart_detail(self, paid_sale, unpaid_sale, waiting_sale, sale_order):
        if sale_order == 0:
            dataPoints = [['State', 'Mhl'],
                          ['WAITING FOR CREATE INVOICES', 0],
                          ['PAID', 0],
                          ['UNPAID', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['WAITING FOR CREATE INVOICES', 100 * waiting_sale / sale_order],
                          ['PAID', 100 * paid_sale / sale_order],
                          ['UNPAID', 100 * unpaid_sale / sale_order]]
        return dataPoints

    @api.model
    def get_pending_sale_order_counts(self, element):
        result = MyClass.get_pending_order_sale_purchase_counts(element, self)
        return result

    @api.model
    def get_pending_sale_order_id(self, element):
        result = MyClass.get_total_order_id(element, self)
        return result

    @api.model
    def get_completed_sale_order_counts(self):
        count = 0
        sale_obj = self.search([('state', '=', 'done')])
        for result in sale_obj:
            if result.quickbook_id:
                count += 1
        return count

    @api.model
    def get_sale_order_details(self, element):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        week_ago = today - DT.timedelta(days=7)
        six_month = today - DT.timedelta(days=180)
        summary_dict = {}
        quotation_number = []
        create_date = []
        total = []
        sale_obj = self.search([('quickbook_id', '!=', False), ('state', '=', 'sale')])
        for result in sale_obj:
            if element == 'last_month':
                if result.date_order.date() <= today and result.date_order.date() >= month_ago:
                    quotation_number.append(result.name)
                    create_date.append(result.date_order.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            elif element == 'last_week':
                if result.date_order.date() <= today and result.date_order.date() >= week_ago:
                    quotation_number.append(result.name)
                    create_date.append(result.date_order.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            elif element == 'today':
                if result.date_order.date() == today:
                    quotation_number.append(result.name)
                    create_date.append(result.date_order.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            else:
                if result.date_order.date() <= today and result.date_order.date() >= six_month:
                    quotation_number.append(result.name)
                    create_date.append(result.date_order.date().strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
        summary_dict['quotation_number'] = quotation_number
        summary_dict['create_date'] = create_date
        summary_dict['total'] = total
        return summary_dict


class AccountMoveExtended(models.Model):
    _inherit = "account.move"

    # INVOICE

    def invoice_piechart_month_detail(self):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'out_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        for so in invoice_total:
            if so.invoice_date <= today and so.invoice_date >= month_ago:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date <= today and so.invoice_date >= month_ago:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date <= today and so.invoice_date >= month_ago:
                invoice_posted_count += 1

        if invoice_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    def invoice_piechart_week_detail(self):
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'out_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        for so in invoice_total:
            if so.invoice_date <= today and so.invoice_date >= week_ago:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date <= today and so.invoice_date >= week_ago:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date <= today and so.invoice_date >= week_ago:
                invoice_posted_count += 1

        if invoice_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    def invoice_piechart_today_detail(self):
        today = DT.date.today()
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'out_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        for so in invoice_total:
            if so.invoice_date == today:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date == today:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date == today:
                invoice_posted_count += 1

        if invoice_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    def invoice_piechart_six_month_detail(self):
        today = DT.date.today()
        six_month = today - DT.timedelta(days=180)
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'out_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        for so in invoice_total:
            if so.invoice_date <= today and so.invoice_date >= six_month:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date <= today and so.invoice_date >= six_month:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date <= today and so.invoice_date >= six_month:
                invoice_posted_count += 1

        if invoice_total == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    @api.model
    def invoice_piechart_detail(self, paid_invoice, unpaid_invoice, total_invoice):
        if total_invoice == 0:
            dataPoints = [['State', 'Mhl'],
                          ['PAID', 0],
                          ['UNPAID', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['PAID', 100 * paid_invoice / total_invoice],
                          ['UNPAID', 100 * unpaid_invoice / total_invoice]]
        return dataPoints

    @api.model
    def get_pending_invoice_counts(self, element):
        invoice_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False),
             ('state', '=', 'posted')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_count += 1
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_count += 1
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_count += 1
            else:
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_count += 1
        return invoice_count

    @api.model
    def get_pending_invoice_id(self, element):
        invoice_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False),
             ('state', '=', 'posted')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_id.append(invoice.id)
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_id.append(invoice.id)
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_id.append(invoice.id)
            else:
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_id.append(invoice.id)
        return invoice_id

    @api.model
    def get_xero_unpaid_invoice_counts(self, element):
        invoice_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False), ('payment_state', '=', "not_paid"),
             ('state', '=', 'posted')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_count += 1
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_count += 1
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_count += 1
            else:
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_count += 1
        return invoice_count

    @api.model
    def get_xero_unpaid_invoice_cid(self, element):
        invoice_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False), ('payment_state', '=', "not_paid"),
             ('state', '=', 'posted')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_id.append(invoice.id)
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_id.append(invoice.id)
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_id.append(invoice.id)
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_id.append(invoice.id)
        return invoice_id

    @api.model
    def get_xero_paid_invoice_counts(self, element):
        invoice_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False), ('payment_state', '=', "paid"),
             ('state', '=', 'posted')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_count += 1
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_count += 1
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_count += 1
            else:
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_count += 1
        return invoice_count

    @api.model
    def get_xero_paid_invoice_id(self, element):
        invoice_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False), ('payment_state', '=', "paid"),
             ('state', '=', 'posted')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_id.append(invoice.id)
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_id.append(invoice.id)
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_id.append(invoice.id)
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_id.append(invoice.id)
        return invoice_id

    @api.model
    def get_unpaid_invoice_counts(self, element):
        invoice_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False),
             ('payment_state', '=', "not_paid"), ('state', '!=', 'cancel')])
        for invoice in invoice_obj:
            if invoice.sale_order_count > 0:
                if element == 'last_month':
                    if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                        invoice_count += 1
                elif element == 'last_week':
                    if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                        invoice_count += 1
                elif element == 'today':
                    if invoice.invoice_date == today:
                        invoice_count += 1
                else:
                    if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                        invoice_count += 1
        return invoice_count

    @api.model
    def get_unpaid_invoice_id(self, element):
        invoice_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False),
             ('payment_state', '=', "not_paid"), ('state', '!=', 'cancel')])
        for invoice in invoice_obj:
            if invoice.sale_order_count > 0:
                if element == 'last_month':
                    if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                        invoice_id.append(invoice.id)
                elif element == 'las`t_week':
                    if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                        invoice_id.append(invoice.id)
                elif element == 'today':
                    if invoice.invoice_date == today:
                        invoice_id.append(invoice.id)
                else:
                    if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                        invoice_id.append(invoice.id)
        return invoice_id

    @api.model
    def get_paid_invoice_counts(self, element):
        invoice_paid_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False), ('ref', '!=', False),
             ('payment_state', '=', 'paid')])
        for invoice in invoice_obj:
            if element == 'last_month':
                if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                    invoice_paid_count += 1
            elif element == 'last_week':
                if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                    invoice_paid_count += 1
            elif element == 'today':
                if invoice.invoice_date == today:
                    invoice_paid_count += 1
            else:
                if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                    invoice_paid_count += 1
        return invoice_paid_count

    @api.model
    def get_paid_invoice_id(self, element):
        invoice_paid_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False),
             ('payment_state', '=', 'paid')])
        for invoice in invoice_obj:
            if invoice.sale_order_count > 0:
                if element == 'last_month':
                    if invoice.invoice_date <= today and invoice.invoice_date >= month_ago:
                        invoice_paid_id.append(invoice.id)
                elif element == 'last_week':
                    if invoice.invoice_date <= today and invoice.invoice_date >= week_ago:
                        invoice_paid_id.append(invoice.id)
                elif element == 'today':
                    if invoice.invoice_date == today:
                        invoice_paid_id.append(invoice.id)
                else:
                    if invoice.invoice_date <= today and invoice.invoice_date >= six_month_ago:
                        invoice_paid_id.append(invoice.id)
        return invoice_paid_id

    @api.model
    def get_invoice_details(self, element):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        week_ago = today - DT.timedelta(days=7)
        six_month = today - DT.timedelta(days=180)
        summary_dict = {}
        quotation_number = []
        create_date = []
        total = []
        invoice_obj = self.search(
            [('move_type', '=', 'out_invoice'), ('qbo_invoice_id', '!=', False), ('state', '=', 'posted')])
        for result in invoice_obj:
            if element == 'last_month':
                if result.invoice_date <= today and result.invoice_date >= month_ago:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            elif element == 'last_week':
                if result.invoice_date <= today and result.invoice_date >= week_ago:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            elif element == 'today':
                if result.invoice_date == today:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            else:
                if result.invoice_date <= today and result.invoice_date >= six_month:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
        summary_dict['quotation_number'] = quotation_number
        summary_dict['create_date'] = create_date
        summary_dict['total'] = total
        return summary_dict

    # BILL

    def bill_piechart_month_detail(self):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'in_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'in_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        for so in invoice_total:
            if so.invoice_date <= today and so.invoice_date >= month_ago:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date <= today and so.invoice_date >= month_ago:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date <= today and so.invoice_date >= month_ago:
                invoice_posted_count += 1

        if invoice_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    def bill_piechart_week_detail(self):
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'in_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'in_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        for so in invoice_total:
            if so.invoice_date <= today and so.invoice_date >= week_ago:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date <= today and so.invoice_date >= week_ago:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date <= today and so.invoice_date >= week_ago:
                invoice_posted_count += 1

        if invoice_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    def bill_piechart_today_detail(self):
        today = DT.date.today()
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'in_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'in_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        for so in invoice_total:
            if so.invoice_date == today:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date == today:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date == today:
                invoice_posted_count += 1

        if invoice_total_count == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    def bill_piechart_six_month_detail(self):
        today = DT.date.today()
        six_month = today - DT.timedelta(days=180)
        invoice_total_count = 0
        invoice_draft_count = 0
        invoice_posted_count = 0
        invoice_total = self.search([('qbo_invoice_id', '!=', False), ('move_type', '=', 'in_invoice')])
        invoice_draft = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'draft'), ('move_type', '=', 'in_invoice')])
        invoice_posted = self.search(
            [('qbo_invoice_id', '!=', False), ('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        for so in invoice_total:
            if so.invoice_date <= today and so.invoice_date >= six_month:
                invoice_total_count += 1
        for so in invoice_draft:
            if so.invoice_date <= today and so.invoice_date >= six_month:
                invoice_draft_count += 1
        for so in invoice_posted:
            if so.invoice_date <= today and so.invoice_date >= six_month:
                invoice_posted_count += 1

        if invoice_total == 0:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 0],
                          ['Posted', 0],
                          ]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['Draft', 100 * invoice_draft_count / invoice_total_count],
                          ['Posted', 100 * invoice_posted_count / invoice_total_count],
                          ]
        return dataPoints

    @api.model
    def bill_piechart_detail(self, paid, unpaid, bill_total):
        if bill_total == 0:
            dataPoints = [['State', 'Mhl'],
                          ['PAID', 0],
                          ['UNPAID', 0]]
        else:
            dataPoints = [['State', 'Mhl'],
                          ['PAID', 100 * paid / bill_total],
                          ['UNPAID', 100 * unpaid / bill_total]]
        return dataPoints

    @api.model
    def get_pending_bill_counts(self, element):
        bill_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search([('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False),
                                ('state', '!=', 'cancel'), ('state', '=', 'posted')])
        for bill in bill_obj:
            if element == 'last_month':
                if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                    bill_count += 1
            elif element == 'last_week':
                if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                    bill_count += 1
            elif element == 'today':
                if bill.invoice_date == today:
                    bill_count += 1
            else:
                if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                    bill_count += 1
        return bill_count

    @api.model
    def get_unpaid_xero_bill_counts(self, element):
        bill_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('payment_state', '=', "not_paid"), ('qbo_invoice_id', '!=', False),
             ('state', '!=', 'cancel'), ('state', '=', 'posted')])
        for bill in bill_obj:
            if element == 'last_month':
                if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                    bill_count += 1
            elif element == 'last_week':
                if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                    bill_count += 1
            elif element == 'today':
                if bill.invoice_date == today:
                    bill_count += 1
            else:
                if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                    bill_count += 1
        return bill_count

    @api.model
    def get_unpaid_xero_bill_id(self, element):
        bill_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('payment_state', '=', "not_paid"), ('qbo_invoice_id', '!=', False),
             ('state', '!=', 'cancel'), ('state', '=', 'posted')])
        for bill in bill_obj:
            if element == 'last_month':
                if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                    bill_id.append(bill.id)
            elif element == 'last_week':
                if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                    bill_id.append(bill.id)
            elif element == 'today':
                if bill.invoice_date == today:
                    bill_id.append(bill.id)
            else:
                if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                    bill_id.append(bill.id)
        return bill_id

    @api.model
    def get_paid_xero_bill_counts(self, element):
        bill_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('payment_state', '=', "paid"), ('qbo_invoice_id', '!=', False),
             ('state', '!=', 'cancel'), ('state', '=', 'posted')])
        for bill in bill_obj:
            if element == 'last_month':
                if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                    bill_count += 1
            elif element == 'last_week':
                if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                    bill_count += 1
            elif element == 'today':
                if bill.invoice_date == today:
                    bill_count += 1
            else:
                if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                    bill_count += 1
        return bill_count

    @api.model
    def get_paid_xero_bill_id(self, element):
        bill_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('payment_state', '=', "paid"), ('qbo_invoice_id', '!=', False),
             ('state', '=', 'posted')])
        for bill in bill_obj:
            if element == 'last_month':
                if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                    bill_id.append(bill.id)
            elif element == 'last_week':
                if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                    bill_id.append(bill.id)
            elif element == 'today':
                if bill.invoice_date == today:
                    bill_id.append(bill.id)
            else:
                if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                    bill_id.append(bill.id)
        return bill_id

    @api.model
    def get_pending_bill_id(self, element):
        bill_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search([('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False),
                                ('state', '!=', 'cancel'), ('state', '=', 'posted')])
        for bill in bill_obj:
            if element == 'last_month':
                if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                    bill_id.append(bill.id)
            elif element == 'last_week':
                if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                    bill_id.append(bill.id)
            elif element == 'today':
                if bill.invoice_date == today:
                    bill_id.append(bill.id)
            else:
                if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                    bill_id.append(bill.id)
        return bill_id

    @api.model
    def get_unpaid_bill_counts(self, element):
        bill_unpaid_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False),
             ('payment_state', '=', "not_paid"), ('state', '!=', "cancel")])
        for bill in bill_obj:
            if bill.invoice_line_ids:
                if bill.purchase_order_count > 0:
                    if element == 'last_month':
                        if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                            bill_unpaid_count += 1
                    elif element == 'last_week':
                        if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                            bill_unpaid_count += 1
                    elif element == 'today':
                        if bill.invoice_date == today:
                            bill_unpaid_count += 1
                    else:
                        if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                            bill_unpaid_count += 1

        return bill_unpaid_count

    @api.model
    def get_unpaid_bill_id(self, element):
        bill_unpaid_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False),
             ('payment_state', '=', "not_paid"), ('state', '!=', "cancel")])
        for bill in bill_obj:
            if bill.purchase_order_count > 0:
                if element == 'last_month':
                    if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                        bill_unpaid_id.append(bill.id)
                elif element == 'last_week':
                    if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                        bill_unpaid_id.append(bill.id)
                elif element == 'today':
                    if bill.invoice_date == today:
                        bill_unpaid_id.append(bill.id)
                else:
                    if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                        bill_unpaid_id.append(bill.id)
        return bill_unpaid_id

    @api.model
    def get_paid_bill_counts(self, element):
        paid_bill_count = 0
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search([('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False),
                                ('payment_state', '=', "paid")])
        for bill in bill_obj:
            if bill.purchase_order_count > 0:
                if element == 'last_month':
                    if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                        paid_bill_count += 1
                elif element == 'last_week':
                    if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                        paid_bill_count += 1
                elif element == 'today':
                    if bill.invoice_date == today:
                        paid_bill_count += 1
                else:
                    if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                        paid_bill_count += 1
        return paid_bill_count

    @api.model
    def get_paid_bill_id(self, element):
        paid_bill_id = []
        today = DT.date.today()
        week_ago = today - DT.timedelta(days=7)
        month_ago = today - DT.timedelta(days=30)
        six_month_ago = today - DT.timedelta(days=180)
        bill_obj = self.search([('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False),
                                ('payment_state', '=', "paid")])
        for bill in bill_obj:
            if bill.purchase_order_count > 0:
                if element == 'last_month':
                    if bill.invoice_date <= today and bill.invoice_date >= month_ago:
                        paid_bill_id.append(bill.id)
                elif element == 'last_week':
                    if bill.invoice_date <= today and bill.invoice_date >= week_ago:
                        paid_bill_id.append(bill.id)
                elif element == 'today':
                    if bill.invoice_date == today:
                        paid_bill_id.append(bill.id)
                else:
                    if bill.invoice_date <= today and bill.invoice_date >= six_month_ago:
                        paid_bill_id.append(bill.id)
        return paid_bill_id

    @api.model
    def get_bill_details(self, element):
        today = DT.date.today()
        month_ago = today - DT.timedelta(days=30)
        week_ago = today - DT.timedelta(days=7)
        six_month = today - DT.timedelta(days=180)
        summary_dict = {}
        quotation_number = []
        create_date = []
        total = []
        bill_obj = self.search(
            [('move_type', '=', 'in_invoice'), ('qbo_invoice_id', '!=', False), ('state', '=', 'posted')])
        for result in bill_obj:
            if element == 'last_month':
                if result.invoice_date <= today and result.invoice_date >= month_ago:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            elif element == 'last_week':
                if result.invoice_date <= today and result.invoice_date >= week_ago:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            elif element == 'today':
                if result.invoice_date == today:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")
            else:
                if result.invoice_date <= today and result.invoice_date >= six_month:
                    quotation_number.append(result.name)
                    invoice_date = result.invoice_date
                    create_date.append(invoice_date.strftime("%d/%m/%Y"))
                    total.append(f"{result.currency_id.symbol} {result.amount_total}")

        summary_dict['quotation_number'] = quotation_number
        summary_dict['create_date'] = create_date
        summary_dict['total'] = total
        return summary_dict
