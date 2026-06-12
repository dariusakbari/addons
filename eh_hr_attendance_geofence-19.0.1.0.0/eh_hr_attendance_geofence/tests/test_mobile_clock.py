# -*- encoding: utf-8 -*-
import json

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestMobileClock(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Mobile clock test',
            'company_id': company.id,
            'eh_mobile_geofence_required': True,
        })
        cls.site = cls.env['eh.hr.kiosk.site'].create({
            'name': 'Geofence site',
            'code': 'geo-site',
            'company_id': company.id,
            'geofence_enabled': True,
            'geofence_lat': -37.8136,
            'geofence_lng': 144.9631,
            'geofence_radius_m': 50,
        })
        cls.device = cls.env['eh.hr.mobile.device'].create({
            'name': 'Mobile clock test phone',
            'employee_id': cls.employee.id,
        })

    def _post_clock(self, body):
        return self.url_open(
            '/eh_hr/mobile/clock',
            data=json.dumps(body),
            headers={
                'Content-Type': 'application/json',
                'X-EH-Mobile-Token': self.device.device_token,
            },
        )

    def test_clock_without_token_returns_401(self):
        resp = self.url_open(
            '/eh_hr/mobile/clock',
            data=json.dumps({'lat': 0, 'lng': 0}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(resp.status_code, 401)

    def test_clock_inside_fence_creates_attendance(self):
        resp = self._post_clock({'lat': -37.8136, 'lng': 144.9631})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['action'], 'check_in')
        att = self.env['hr.attendance'].search([('employee_id', '=', self.employee.id)])
        self.assertEqual(len(att), 1)
        self.assertFalse(att.check_out)

    def test_clock_outside_fence_rejected_and_raises_exception(self):
        resp = self._post_clock({'lat': 0.0, 'lng': 0.0})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body['ok'])
        self.assertEqual(body['reason'], 'geofence_violation')
        # Exception raised
        exc = self.env['eh.hr.attendance.exception'].search([
            ('employee_id', '=', self.employee.id),
            ('exception_type', '=', 'geofence_violation'),
        ])
        self.assertTrue(exc)

    def test_clock_without_geo_when_required_rejected(self):
        resp = self._post_clock({})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body['ok'])
        self.assertEqual(body['reason'], 'geofence_required')

    def test_clock_without_geo_when_not_required_passes(self):
        self.employee.write({'eh_mobile_geofence_required': False})
        resp = self._post_clock({})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['action'], 'check_in')

    def test_second_clock_toggles_to_check_out(self):
        # First clock-in.
        first = self._post_clock({'lat': -37.8136, 'lng': 144.9631})
        self.assertEqual(first.json()['action'], 'check_in')
        # Second clock toggles to check-out.
        second = self._post_clock({'lat': -37.8136, 'lng': 144.9631})
        self.assertEqual(second.json()['action'], 'check_out')
