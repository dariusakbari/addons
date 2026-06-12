# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
{
 'name': "Mobile Geofence Clock-in",
 'summary': "Per-employee mobile clock-in / clock-out with GPS geofence enforcement. Each employee pairs their phone once via PIN, then clocks in from a mobile-friendly web page that the server gates by distance to any of the company's geofence-enabled sites.",
 'description': """
ERP Heritage Mobile Geofence Clock-in
=======================================

Adds a mobile-friendly, geo-fenced clock-in path to the ERP Heritage
attendance suite. Designed for off-site, field, and home-based workers
who do not pass through a kiosk, but whose hours still need verifiable
location anchoring.

How it works
------------

1. **HR pairs a phone.** From the employee record, an admin or
   manager issues a one-time pairing PIN. The employee opens the
   mobile shell on their phone, enters the PIN, and the server
   issues a long-lived opaque token bound to that employee.
2. **The phone uses the mobile shell** for clock-in and clock-out.
   The shell asks for browser geolocation, sends the embedding-free
   request (employee token + lat/lng) to the server.
3. **The server validates the location** against every active
   geofence-enabled site in the employee's company. If the phone is
   inside the radius of at least one site, the clock event is
   posted. If not, the request is rejected and a geofence-violation
   exception is raised.

Privacy posture
---------------

* **Geolocation consent is mandatory.** The first time the mobile
  shell asks for location, an `eh.hr.consent` of type `geolocation`
  is created and granted by the employee's confirmation tap.
* **No background tracking.** The phone reads location only at the
  moment of clock-in and clock-out, never continuously.
* **No raw face image, no biometric on mobile.** This module
  intentionally trusts the device pairing as the identity binding.
  Face on mobile is a Wave 3 / Wave 4 follow-up.

What this module gives you directly
-----------------------------------

* `eh.hr.mobile.device` model with rotating opaque token, last-seen,
  IP, user agent.
* /eh_hr/mobile/<token> mobile shell HTML page.
* /eh_hr/mobile/pair, /eh_hr/mobile/clock pair and clock endpoints.
* Mobile-friendly check-in / check-out shell with geolocation prompt,
  large touch targets, dark mint theme matching the kiosk.
* Per-employee toggle to make geofencing optional (off-site role).

Search keywords
---------------

Mobile clock in, GPS attendance, geofence attendance, field worker
attendance, remote clock in, home-based attendance, Odoo 19 Community
mobile attendance.


    """,
 'author': "ERP Heritage",
 'website': "https://www.erpheritage.com.au/",
 'license': 'LGPL-3',
 'category': 'Human Resources/Attendances',
 'version': '1.0.0',
 'depends': [
 'eh_hr_attendance_base',
 'eh_hr_core',
 'hr_attendance',
 ],
 'data': [
 'security/ir.model.access.csv',
 'security/eh_hr_isolation_rules.xml',
 'data/eh_hr_mobile_crons.xml',
 'views/eh_hr_mobile_device_views.xml',
 'views/hr_employee_views.xml',
 'views/res_config_settings_views.xml',
 'views/mobile_shell_template.xml',
 'views/menus.xml',
 ],
 'images': ['static/description/banner.png'],
 'installable': True,
 'application': False,
 'auto_install': False,
}
