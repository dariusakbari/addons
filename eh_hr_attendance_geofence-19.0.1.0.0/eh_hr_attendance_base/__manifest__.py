# -*- encoding: utf-8 -*-
##############################################################################
#
# ERP Heritage
# Copyright (C) 2026 (https://www.erpheritage.com.au/)
#
##############################################################################
{
 'name': "Attendance Suite Base",
 'summary': "Shared engine for the ERP Heritage people operations suite. Biometric consent lifecycle, kiosk site and device registry, attendance exception log, kiosk audit trail. Auto-installs with any ERP Heritage attendance module.",
 'description': """
ERP Heritage Attendance Suite Base
====================================

The shared engine that powers the ERP Heritage attendance and people
operations modules for Odoo 19 Community. Auto-installs as a dependency
of any ERP Heritage attendance module so you do not need to install it
manually.

What this module gives you directly
-----------------------------------

* **Biometric consent lifecycle.** Every face, fingerprint, geolocation
  or photo capture is gated by an eh.hr.consent record with explicit
  granted, withdrawn and expired states, evidence storage, and a
  configurable retention window. Consent withdrawal cascades to the
  matching biometric template the next time the kiosk runs.

* **Kiosk site and device registry.** A site model for each physical
  clock-in location with optional geofence, and a device registry
  that issues a per-device token, tracks last-seen, and gives a
  manager a single screen to revoke a lost or stolen kiosk.

* **Attendance exception log.** A first-class eh.hr.attendance.exception
  model for late, no-show, missed check-out, location mismatch, low
  match confidence, and geofence violation events. Future modules
  raise to it; managers triage and resolve from one place.

* **Kiosk audit trail.** Every kiosk event (register, heartbeat, match
  attempt, success, failure, consent change, attendance post) lands
  in eh.hr.kiosk.event with timestamp, device, employee, confidence,
  and IP, retained per configurable policy. Defensible record for
  fair work disputes.

* **Retention sweeps.** A daily cron expires consents past their
  validity, deletes withdrawn consents past retention, and trims the
  kiosk audit trail to the configured horizon. Compliance is a
  background process, not a checklist.

What other ERP Heritage modules build on top
---------------------------------------------

* Face Kiosk: in-browser face embedding capture, server-side cosine
  match, attendance posting, manager enrolment wizard.
* Job Costing for Attendance: post-match analytic and project punch.
* Attendance Reports: dashboards, exceptions, audit export PDF.
* Geofence and Mobile (Wave 2): PWA clock-in, GPS fence per worksite.
* Roster and Schedule (Wave 2): rosters, shift templates, scheduled
  versus actual diff for Community Edition.
* Visitor Management (Wave 2): front-desk sign-in, host notification.
* Australian Award Engine (Wave 3): Fair Work and Modern Award OT,
  penalties, allowances on top of clocked time.
* Payroll Export (Wave 3): one-click feeds to common payroll systems.
* Migration (Wave 2): one-time vendor-neutral CSV importer for moving
  off any incumbent biometric attendance system.

Engineering principles
----------------------

* Privacy by design. Raw biometric images never persist on the server.
  Only embeddings live in the database, tied to a granted consent.
* Multi-company aware throughout. Every model is company-scoped and
  guarded by record rules.
* Defensible audit. Every kiosk event is logged with a timestamp the
  customer cannot edit; managers can read, never write.
* No silent fallbacks. Missing consent, missing site, missing device
  token each surface explicit messages.
* Plain Python and OWL components. No third-party cloud dependency.

Search keywords
---------------

Attendance, biometric attendance, face attendance, kiosk attendance,
time clock, time and attendance, T&A, employee clock in, employee
clock out, exception management, geofence attendance, visitor
management, access control, Odoo 19 Community attendance, hr_attendance.


    """,
 'author': "ERP Heritage",
 'website': "https://www.erpheritage.com.au/",
 'license': 'LGPL-3',
 'category': 'Human Resources/Attendances',
 'version': '1.0.0',
 'depends': [
 'base',
 'mail',
 'hr',
 'hr_attendance',
 'eh_hr_compat',
 ],
 'post_init_hook': 'post_init_hook',
 'data': [
 'security/eh_hr_security.xml',
 'security/eh_hr_isolation_rules.xml',
 'security/ir.model.access.csv',
 'data/cron.xml',
 'views/eh_hr_consent_views.xml',
 'views/eh_hr_kiosk_views.xml',
 'views/eh_hr_attendance_exception_views.xml',
 'views/hr_employee_views.xml',
 'views/menus.xml',
 'views/res_config_settings_views.xml',
 ],
 'images': ['static/description/banner.png'],
 'installable': True,
 'application': False,
 'auto_install': False,
}
