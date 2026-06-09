# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models
from odoo.tools import safe_eval


class QuickBook_Object(models.Model):
    _name = "quick.book.collection"
    _description = "QuickBook Collection"

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', 'Model')
    field_domain = fields.Char('Domain')
    record_count = fields.Integer('Count', compute='_compute_count', compute_sudo=True, store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company)
    model_name = fields.Char(related='model_id.model', string='Model Name', readonly=True, store=True)

    @api.onchange('model_id')
    def onchange_model_id(self):
        self.model_name = self.model_id.model

    @api.depends('model_id')
    def _compute_count(self):
        for rec in self.search([]):
            if rec.model_id and rec.field_domain:
                domain = safe_eval.safe_eval(rec.field_domain)
                rec.record_count = self.sudo().env[str(rec.model_id.model)].search_count(domain)

    @api.model
    def get_views(self, views, options=None):
        self._compute_count()
        res = super().get_views(views, options)
        return res



class ResCompany(models.Model):
    _inherit = "res.company"

    sale_order_count = fields.Integer('Sale Order', compute='_compute_count', compute_sudo=True, store=True)
    purchase_order_count = fields.Integer('Purchase Order', compute='_compute_count', compute_sudo=True, store=True)

    def _compute_count(self):
        for rec in self:
            rec.sale_order_count = self.sudo().env['sale.order'].search_count([('quickbook_id', '>', 0)])
            rec.purchase_order_count = self.sudo().env['purchase.order'].search_count([('quickbook_id', '>', 0)])


class QuickBookReport(models.Model):
    _name = "qb.report"
    _description = "Quick Report"
    _auto = False

    qbc_id = fields.Many2one('quick.book.collection', 'QBC')
    record_count = fields.Integer('Count')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT
                company.id,
                qbc.record_count as record_count,
                qbc.id as qbc_id
            FROM res_company company
            join quick_book_collection qbc on qbc.company_id = company.id
        )""" % (self._table))

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        for collection_id in self.env['quick.book.collection'].search([]):
            collection_id._compute_count()
        res = super(QuickBookReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res
