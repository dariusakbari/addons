# -*- encoding: utf-8 -*-
import secrets

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EhHrMobileDevice(models.Model):
    _name = 'eh.hr.mobile.device'
    _description = 'Registered Mobile Device'
    _inherit = ['mail.thread']
    _order = 'last_seen desc, id desc'

    name = fields.Char(string='Device label', required=True, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='employee_id.company_id',
        store=True,
        index=True,
    )
    device_token = fields.Char(
        string='Device token',
        required=True,
        index=True,
        copy=False,
        readonly=True,
        default=lambda self: secrets.token_urlsafe(32),
        help="Server-issued opaque token bound to this employee. The mobile shell sends it on every request.",
    )
    registered_on = fields.Datetime(
        string='Registered on',
        default=fields.Datetime.now,
        readonly=True,
    )
    last_seen = fields.Datetime(string='Last seen', readonly=True)
    last_ip = fields.Char(string='Last IP', readonly=True)
    user_agent = fields.Char(string='User agent', readonly=True)
    last_lat = fields.Float(string='Last latitude', digits=(10, 6), readonly=True)
    last_lng = fields.Float(string='Last longitude', digits=(10, 6), readonly=True)
    active = fields.Boolean(default=True, tracking=True)
    notes = fields.Text(string='Notes')

    if hasattr(models, 'Constraint'):
        _unique_mobile_token = models.Constraint('UNIQUE(device_token)', 'Mobile device token collision detected.')
    else:
        _sql_constraints = [('unique_mobile_token', 'UNIQUE(device_token)', 'Mobile device token collision detected.')]

    def action_rotate_token(self):
        for record in self:
            record.device_token = secrets.token_urlsafe(32)

    def action_revoke(self):
        self.write({'active': False})

    def _touch(self, ip_address=None, user_agent=None, lat=None, lng=None):
        vals = {'last_seen': fields.Datetime.now()}
        if ip_address:
            vals['last_ip'] = ip_address
        if user_agent:
            vals['user_agent'] = user_agent[:255]
        if lat is not None:
            vals['last_lat'] = lat
        if lng is not None:
            vals['last_lng'] = lng
        self.sudo().write(vals)
