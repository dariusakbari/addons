# Mobile Geofence Clock-in

Adds a mobile-friendly, geo-fenced clock-in path to the ERP Heritage
attendance suite. Designed for off-site, field, and home-based workers
who do not pass through a kiosk, but whose hours still need verifiable
location anchoring.

## Install

```
./odoo-bin -d <db> -i eh_hr_attendance_geofence
```

Depends on `eh_hr_attendance_base` and `hr_attendance`.

## Pairing flow

1. On the employee's record, an admin or manager clicks **Issue mobile
   pairing PIN**. A 6-digit PIN is shown for 5 minutes.
2. The employee opens `/eh_hr/mobile` on their phone, enters the PIN,
   and gets a long-lived opaque token bound to their employee record.
3. From then on, the phone clocks in / out against that employee.

## Clock event flow

1. Employee taps **Clock in / out** on the phone.
2. The phone reads its location (browser permission prompt on first use).
3. The phone POSTs `{lat, lng}` plus the device token to
   `/eh_hr/mobile/clock`.
4. The server, if the employee is `eh_mobile_geofence_required = True`,
   validates the position against every active geofence-enabled site
   in the company. First site whose radius contains the position wins;
   the closest site's distance is logged either way.
5. If allowed, an `hr.attendance` row is created or closed (toggle
   based on the employee's last open attendance).
6. Every step writes to the `eh.hr.kiosk.event` audit trail with
   timestamp, IP, and event type (`device_register`,
   `geofence_pass`, `geofence_fail`, `attendance_in`,
   `attendance_out`).

## Privacy posture

* Location is read **only at the moment of clock-in / clock-out**.
  No background tracking.
* The phone gets a permission prompt on first use; without explicit
  consent the OS does not provide coordinates.
* The employee's `eh.hr.consent` of type `geolocation` should be
  granted in advance of pairing. The mobile shell does not (yet)
  capture this consent on the page; the manager creates it from the
  employee record. A future iteration will move consent capture to
  the mobile shell.

## Per-employee opt-out

`hr.employee.eh_mobile_geofence_required` toggles enforcement. For
true off-site / field roles whose location is genuinely unknown, set
this to off. The location is still read and logged when present, but
does not gate the clock event.

## Endpoints

* `GET  /eh_hr/mobile`            mobile shell HTML
* `POST /eh_hr/mobile/pair`       trade pairing PIN for device token
* `GET  /eh_hr/mobile/whoami`     return paired employee for the token
* `POST /eh_hr/mobile/clock`      clock-in / clock-out with optional GPS

## Apps Store readiness checklist

Operator action: `static/description/banner.png`, `icon.png`,
`index.html`. Module display name "Mobile Geofence Clock-in" is 24
chars.

## Honest gaps

* **No service worker, no PWA install.** A future iteration adds
  a `manifest.webmanifest` and a minimal service worker so the mobile
  shell becomes installable to the home screen and works offline. For
  Wave 2 the mobile shell is just a mobile-friendly web page.
* **No camera or face capture on mobile.** The pairing token is the
  identity binding. Adding face on mobile is a Wave 4 follow-up that
  layers on top of the kiosk's face match path.
* **No analytic / project punch from mobile.** Wave 3 adds a job
  picker analogous to the kiosk's.
* **No customer-site geofencing.** Mobile workers visiting customer
  addresses cannot use those addresses as geofences yet. Wave 3 ties
  this to analytic-account geofences for service businesses.
