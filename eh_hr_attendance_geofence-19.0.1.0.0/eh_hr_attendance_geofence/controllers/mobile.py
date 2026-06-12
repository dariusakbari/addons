# -*- encoding: utf-8 -*-
"""Mobile clock-in / clock-out endpoints.

The mobile pairing flow mirrors the kiosk pairing flow but binds the
issued device token to a specific employee, not to a site. From then
on, every clock event is attributed to that employee, with the GPS
position validated against the company's active geofence-enabled
sites (unless the employee record marks them as not geofence-required).
"""
import json
import math

from odoo import _, fields, http
from odoo.http import request


# Rate-limit budgets (calls per 60s window) for the public mobile routes. The
# pair budget is deliberately tight: a 6-digit PIN is brute-forceable online
# without it. Throttling is DB-backed (eh.hr.rate.limit), so it survives a
# restart and is shared across workers, unlike a process-global dict.
_PAIR_LIMIT_PER_MIN = 10
_CLOCK_LIMIT_PER_MIN = 30
_WHOAMI_LIMIT_PER_MIN = 60


def _throttled(scope, key, limit):
    """Return a 429 response if the caller is over budget, else None."""
    allowed = request.env['eh.hr.rate.limit'].sudo().hit(scope, key, limit)
    if not allowed:
        return _json_response({'error': 'rate_limited'}, status=429)
    return None


def _client_ip():
    return request.httprequest.headers.get('X-Real-IP') \
        or request.httprequest.headers.get('X-Forwarded-For', '').split(',')[0].strip() \
        or request.httprequest.remote_addr


def _client_user_agent():
    return request.httprequest.headers.get('User-Agent', '')[:255]


def _json_response(payload, status=200):
    return request.make_response(
        json.dumps(payload),
        headers=[('Content-Type', 'application/json')],
        status=status,
    )


def _get_device_by_token(token):
    if not token:
        return None
    Device = request.env['eh.hr.mobile.device'].sudo()
    return Device.search([
        ('device_token', '=', token),
        ('active', '=', True),
    ], limit=1)


def _haversine_meters(lat1, lng1, lat2, lng2):
    R = 6371008.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _within_any_geofence(company, lat, lng):
    """Return (matched_site or None, closest_distance) for the given
    coordinates against every active, geofence-enabled site of the company.
    """
    Site = request.env['eh.hr.kiosk.site'].sudo()
    sites = Site.search([
        ('company_id', '=', company.id),
        ('active', '=', True),
        ('geofence_enabled', '=', True),
    ])
    if not sites:
        return None, None
    closest = None
    closest_distance = float('inf')
    for site in sites:
        d = _haversine_meters(site.geofence_lat, site.geofence_lng, lat, lng)
        if d < closest_distance:
            closest = site
            closest_distance = d
        if d <= (site.geofence_radius_m or company.eh_hr_mobile_default_radius_m or 100):
            return site, d
    return None, closest_distance


class EhHrMobileController(http.Controller):

    @http.route('/eh_hr/mobile', type='http', auth='public', methods=['GET'], csrf=False)
    def mobile_shell(self, **kwargs):
        return request.render('eh_hr_attendance_geofence.mobile_shell', {})

    @http.route('/eh_hr/mobile/pair', type='http', auth='public', methods=['POST'], csrf=False)
    def pair(self, **kwargs):
        throttled = _throttled('mobile.pair', _client_ip(), _PAIR_LIMIT_PER_MIN)
        if throttled:
            return throttled
        try:
            data = json.loads(request.httprequest.data) if request.httprequest.data else {}
        except ValueError:
            data = {}
        data = {**kwargs, **data}

        pin = (data.get('pin') or '').strip()
        device_label = (data.get('device_label') or '').strip() or _('Mobile device')

        if not pin:
            return _json_response({'error': 'pin is required'}, status=400)

        # Atomic one-shot redeem against the persistent pairing model. Returns
        # an empty recordset for an unknown, expired, or already-used PIN.
        employee = request.env['eh.hr.mobile.pairing'].sudo().redeem(pin)
        if not employee:
            return _json_response({'error': 'Invalid or expired pairing PIN'}, status=403)
        if not employee.active:
            return _json_response({'error': 'Employee no longer exists or is inactive'}, status=404)

        Device = request.env['eh.hr.mobile.device'].sudo()
        device = Device.create({
            'name': device_label,
            'employee_id': employee.id,
            'last_ip': _client_ip(),
            'user_agent': _client_user_agent(),
        })

        request.env['eh.hr.kiosk.event'].sudo().log(
            'device_register',
            employee_id=employee.id,
            ip_address=_client_ip(),
            user_agent=_client_user_agent(),
            notes='Mobile device paired via /eh_hr/mobile/pair',
            company_id=employee.company_id.id,
        )

        return _json_response({
            'device_token': device.device_token,
            'employee_id': employee.id,
            'employee_name': employee.name,
        })

    @http.route('/eh_hr/mobile/whoami', type='http', auth='public', methods=['GET'], csrf=False)
    def whoami(self, **kwargs):
        token = request.httprequest.headers.get('X-EH-Mobile-Token')
        throttled = _throttled('mobile.whoami', token or _client_ip(), _WHOAMI_LIMIT_PER_MIN)
        if throttled:
            return throttled
        device = _get_device_by_token(token)
        if not device:
            return _json_response({'error': 'unauthorized'}, status=401)
        return _json_response({
            'employee_id': device.employee_id.id,
            'employee_name': device.employee_id.name,
            'company_id': device.company_id.id,
            'geofence_required': bool(device.employee_id.eh_mobile_geofence_required),
        })

    @http.route('/eh_hr/mobile/clock', type='http', auth='public', methods=['POST'], csrf=False)
    def clock(self, **kwargs):
        token = request.httprequest.headers.get('X-EH-Mobile-Token')
        throttled = _throttled('mobile.clock', token or _client_ip(), _CLOCK_LIMIT_PER_MIN)
        if throttled:
            return throttled
        device = _get_device_by_token(token)
        if not device:
            return _json_response({'error': 'unauthorized'}, status=401)

        try:
            data = json.loads(request.httprequest.data)
        except (ValueError, TypeError):
            return _json_response({'error': 'invalid body'}, status=400)

        try:
            lat = float(data.get('lat'))
            lng = float(data.get('lng'))
        except (TypeError, ValueError):
            lat = lng = None

        employee = device.employee_id
        company = device.company_id
        device._touch(
            ip_address=_client_ip(),
            user_agent=_client_user_agent(),
            lat=lat,
            lng=lng,
        )

        # Geofence enforcement.
        require = bool(employee.eh_mobile_geofence_required)
        if require:
            if lat is None or lng is None:
                request.env['eh.hr.kiosk.event'].sudo().log(
                    'geofence_fail',
                    employee_id=employee.id,
                    notes='Mobile clock without geolocation',
                    company_id=company.id,
                )
                return _json_response({'ok': False, 'reason': 'geofence_required'}, status=200)
            site, distance = _within_any_geofence(company, lat, lng)
            if site is None:
                request.env['eh.hr.kiosk.event'].sudo().log(
                    'geofence_fail',
                    employee_id=employee.id,
                    notes='Closest site distance %s m' % (round(distance) if distance is not None else 'unknown'),
                    company_id=company.id,
                )
                request.env['eh.hr.attendance.exception'].sudo().raise_exception(
                    employee=employee,
                    exception_type='geofence_violation',
                    severity='warning',
                    description='Mobile clock attempted from outside any geofenced site',
                )
                return _json_response({'ok': False, 'reason': 'geofence_violation'}, status=200)
            request.env['eh.hr.kiosk.event'].sudo().log(
                'geofence_pass',
                employee_id=employee.id,
                notes='Site %s (distance %s m)' % (site.name, round(distance)),
                company_id=company.id,
            )

        # Toggle attendance.
        Attendance = request.env['hr.attendance'].sudo()
        open_attendance = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1, order='check_in desc')
        now = fields.Datetime.now()
        if open_attendance:
            open_attendance.write({'check_out': now})
            action = 'check_out'
            attendance = open_attendance
        else:
            attendance = Attendance.create({
                'employee_id': employee.id,
                'check_in': now,
            })
            action = 'check_in'

        request.env['eh.hr.kiosk.event'].sudo().log(
            'attendance_in' if action == 'check_in' else 'attendance_out',
            employee_id=employee.id,
            ref_model='hr.attendance',
            ref_id=attendance.id,
            notes='Mobile clock from device %s' % device.name,
            company_id=company.id,
        )

        return _json_response({
            'ok': True,
            'action': action,
            'employee_name': employee.name,
            'attendance_id': attendance.id,
        })
