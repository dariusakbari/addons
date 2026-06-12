# -*- encoding: utf-8 -*-
import json

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install', 'eh_hr', 'eh_hr_security')
class TestMobilePairingModel(TransactionCase):
    """Pure-model tests for the persistent, one-shot pairing PIN that
    replaced the old process-global dict."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Pairing model test',
            'company_id': cls.env.company.id,
        })
        cls.Pairing = cls.env['eh.hr.mobile.pairing']

    def test_issue_returns_six_digit_pin(self):
        pin = self.Pairing.issue(self.employee.id)
        self.assertEqual(len(pin), 6)
        self.assertTrue(pin.isdigit())

    def test_pin_is_one_shot(self):
        pin = self.Pairing.issue(self.employee.id)
        self.assertEqual(self.Pairing.redeem(pin), self.employee,
                         'First redeem returns the employee.')
        self.assertFalse(self.Pairing.redeem(pin),
                         'Second redeem of a used PIN returns empty.')

    def test_new_pin_invalidates_prior(self):
        pin1 = self.Pairing.issue(self.employee.id)
        pin2 = self.Pairing.issue(self.employee.id)
        self.assertFalse(self.Pairing.redeem(pin1),
                         'Issuing a new PIN must expire the prior active one.')
        self.assertEqual(self.Pairing.redeem(pin2), self.employee)

    def test_expired_pin_is_rejected(self):
        pin = self.Pairing.issue(self.employee.id, ttl_seconds=-1)
        self.assertFalse(self.Pairing.redeem(pin),
                         'An already-expired PIN cannot be redeemed.')

    def test_unknown_pin_is_rejected(self):
        self.assertFalse(self.Pairing.redeem('000000'))


@tagged('post_install', '-at_install', 'eh_hr')
class TestMobilePairing(HttpCase):
    """End-to-end pairing through the public endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Mobile pair test',
            'company_id': cls.env.company.id,
        })

    def test_pair_with_valid_pin_returns_token(self):
        pin = self.env['eh.hr.mobile.pairing'].issue(self.employee.id)
        resp = self.url_open(
            '/eh_hr/mobile/pair',
            data=json.dumps({'pin': pin, 'device_label': 'Test phone'}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn('device_token', body)
        self.assertEqual(body['employee_id'], self.employee.id)

        Device = self.env['eh.hr.mobile.device'].sudo()
        device = Device.search([('device_token', '=', body['device_token'])], limit=1)
        self.assertTrue(device)
        self.assertEqual(device.employee_id, self.employee)

    def test_pair_with_missing_pin_returns_400(self):
        resp = self.url_open(
            '/eh_hr/mobile/pair',
            data=json.dumps({}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(resp.status_code, 400)

    def test_pair_with_invalid_pin_returns_403(self):
        resp = self.url_open(
            '/eh_hr/mobile/pair',
            data=json.dumps({'pin': '999999'}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(resp.status_code, 403)

    def test_pin_is_one_shot(self):
        pin = self.env['eh.hr.mobile.pairing'].issue(self.employee.id)
        first = self.url_open(
            '/eh_hr/mobile/pair',
            data=json.dumps({'pin': pin}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(first.status_code, 200)
        second = self.url_open(
            '/eh_hr/mobile/pair',
            data=json.dumps({'pin': pin}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(second.status_code, 403)

    def test_whoami_with_valid_token(self):
        device = self.env['eh.hr.mobile.device'].sudo().create({
            'name': 'Whoami test',
            'employee_id': self.employee.id,
        })
        resp = self.url_open(
            '/eh_hr/mobile/whoami',
            headers={'X-EH-Mobile-Token': device.device_token},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['employee_id'], self.employee.id)
        self.assertIn('geofence_required', body)
