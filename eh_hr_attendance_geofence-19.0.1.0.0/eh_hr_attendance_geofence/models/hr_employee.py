# -*- encoding: utf-8 -*-
from odoo import fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    eh_mobile_device_ids = fields.One2many(
        'eh.hr.mobile.device',
        'employee_id',
        string='Mobile devices',
    )
    eh_mobile_device_count = fields.Integer(
        string='Active mobiles',
        compute='_compute_eh_mobile_device_count',
    )
    eh_mobile_geofence_required = fields.Boolean(
        string='Require mobile geofence',
        default=True,
        help="When on, this employee's mobile clock-in must be inside at least one of the company's geofence-enabled sites. When off (typical for true off-site / field roles), location is recorded for audit but does not gate the clock-in.",
    )

    def _compute_eh_mobile_device_count(self):
        for employee in self:
            employee.eh_mobile_device_count = len(employee.eh_mobile_device_ids.filtered('active'))

    def action_eh_issue_mobile_pairing_pin(self):
        self.ensure_one()
        pin = self.env['eh.hr.mobile.pairing'].issue(self.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Mobile pairing PIN'),
                'message': _("Pairing PIN for %(name)s: %(pin)s. Valid for 5 minutes, one-shot. The employee opens /eh_hr/mobile on their phone and enters this PIN.") % {
                    'name': self.name,
                    'pin': pin,
                },
                'type': 'success',
                'sticky': True,
            },
        }

    def action_eh_view_mobile_devices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mobile devices for %s') % self.name,
            'res_model': 'eh.hr.mobile.device',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
