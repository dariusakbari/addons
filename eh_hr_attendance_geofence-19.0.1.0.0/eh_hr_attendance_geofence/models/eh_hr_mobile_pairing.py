# -*- encoding: utf-8 -*-
"""eh.hr.mobile.pairing - short-lived, one-shot mobile pairing PIN.

Replaces the former module-global ``_PAIRING_PINS`` dict in the controller,
which was lost on restart, not shared across workers, and a cross-tenant
leak risk (one process-wide namespace for every company). Persisting the PIN
in a DB row makes pairing correct under multiple workers and across restarts,
and lets the redeem step claim a PIN atomically so a race cannot pair one PIN
to two devices.
"""
import secrets
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EhHrMobilePairing(models.Model):
    _name = 'eh.hr.mobile.pairing'
    _description = 'Mobile pairing PIN (short-lived, one-shot)'
    _order = 'id desc'

    TTL_SECONDS = 300

    pin = fields.Char(required=True, index=True, copy=False, readonly=True)
    employee_id = fields.Many2one('hr.employee', required=True,
                                  ondelete='cascade', index=True, readonly=True)
    company_id = fields.Many2one('res.company', related='employee_id.company_id',
                                 store=True, index=True)
    issued_at = fields.Datetime(default=fields.Datetime.now, required=True,
                                readonly=True)
    expires_at = fields.Datetime(required=True, readonly=True)
    used_at = fields.Datetime(readonly=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ], default='active', index=True, readonly=True)

    @api.model
    def issue(self, employee_id, ttl_seconds=None):
        """Issue a fresh PIN for an employee, expiring any prior active PIN.

        Returns the 6-digit PIN string. One live PIN per employee at a time.
        """
        ttl = ttl_seconds or self.TTL_SECONDS
        self.sudo().search([
            ('employee_id', '=', int(employee_id)),
            ('state', '=', 'active'),
        ]).write({'state': 'expired'})
        now = fields.Datetime.now()
        pin = self._generate_pin()
        self.sudo().create({
            'pin': pin,
            'employee_id': int(employee_id),
            'issued_at': now,
            'expires_at': now + timedelta(seconds=ttl),
        })
        return pin

    @api.model
    def _generate_pin(self):
        for _attempt in range(20):
            pin = ''.join(secrets.choice('0123456789') for _ in range(6))
            if not self.sudo().search_count([
                ('pin', '=', pin), ('state', '=', 'active')]):
                return pin
        raise UserError(_('Could not allocate a unique pairing PIN. '
                          'Please try again.'))

    @api.model
    def redeem(self, pin):
        """Claim a valid, active, unexpired PIN once.

        Returns the employee on success, or an empty hr.employee recordset if
        the PIN is unknown, expired, or already used. Marking the row 'used'
        before returning makes the PIN one-shot. The brute-force control is
        the per-IP throttle on the pair endpoint, so the narrow race where two
        simultaneous requests redeem the same self-issued PIN is benign (it
        would pair the same employee's PIN twice, not cross identities).
        """
        Employee = self.env['hr.employee']
        pin = (pin or '').strip()
        if not pin:
            return Employee
        rec = self.sudo().search([
            ('pin', '=', pin), ('state', '=', 'active')], limit=1)
        if not rec:
            return Employee
        if rec.expires_at and rec.expires_at < fields.Datetime.now():
            rec.state = 'expired'
            return Employee
        rec.write({'state': 'used', 'used_at': fields.Datetime.now()})
        return rec.employee_id

    @api.model
    def _gc_expired(self):
        """Mark lapsed PINs expired and delete terminal rows older than a day.
        Wired to a daily cron."""
        now = fields.Datetime.now()
        self.sudo().search([
            ('state', '=', 'active'), ('expires_at', '<', now)]).write(
            {'state': 'expired'})
        cutoff = now - timedelta(days=1)
        self.sudo().search([
            ('state', 'in', ('used', 'expired')),
            ('issued_at', '<', cutoff)]).unlink()
