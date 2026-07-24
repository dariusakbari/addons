# Production change log — 24 July 2026 (applied via authenticated session, logged, reversible)

Rollback point: owner-held backup dated 23 July 2026 (pre-change).

1. Created 6 project roles (project.role ids 1-6): Project Manager, Project
   Coordinator, Site Foreman / Superintendent, Estimator, Safety Lead,
   Accounting / Project Controls. Reverse: delete/archive the records.
2. privacy_visibility changed portal → followers on 12 active projects:
   0999 Airport Tennis, 0476 Bayview Glen, 0436 Meadowvale, Internal,
   250752 400 University, TEMPLATE — Electrical Job, Field Service,
   S00001/S00003/S00005/S00006/S00010 - Tasks.
   Old value was "portal" on all 12. No user impact (all 3 users are admins).
   Reverse: write privacy_visibility='portal'.
3. Created 55 Documents folders: the 11-folder construction template
   (01 Contracts … 11 Closeout and As-Builts) under 0476, 0436, 0999,
   250752 and TEMPLATE project folders. Reverse: delete the empty folders.

Not changed (deliberately): tagged tasks, Studio models/records, users, admin
rights, 2FA, mail settings, demo remnants (e.g. leftover demo-employee Documents
folders — flagged for the demo-data disposition report).

## Deployment — 24 July 2026 (afternoon)

Rollback point: OSM backup odoo.greentechelectric.ca_20260724_145326.zip
(taken via panel immediately before deployment).

4. Installed custom addons gte_core and gte_controls (commit e137fb0 via
   github.com/dariusakbari/addons, pulled through OSM panel).
   gte_migration present in repo but NOT installed (owner decision:
   no legacy-task migration for now; can be installed later).
5. Assigned Construction Administrator group to d.akbari (uid 8) — required
   even for admins by the new ACLs. m.kazimi has NO construction group yet;
   assign roles via Settings → Users → Green Tech Construction.
6. Smoke tests run in production on TEMPLATE — Electrical Job project;
   test records left in terminal states, clearly titled "TEST — …":
   RFI-001 (closed), RFI-002 (cancelled), CO-001 (closed), SUB-001 (closed,
   2 revisions). Safe to archive/delete after review.
Rollback: uninstall gte_controls then gte_core (removes gte.* models/records),
or restore the 14:53 backup via OSM.

## v0.2 — 24 July 2026 (later afternoon)

7. Upgraded gte_controls to 19.0.0.2.0 (commit 2fe7db4): QWeb PDF reports
   for RFI / Change Order / Submittal (Print menu on each record) and a
   Construction → Overview menu with work queues (Overdue RFIs, RFIs
   Awaiting Response / To Distribute, Changes Awaiting Client,
   Approved-Not-Billed, Open Exposure, Pending Submittals, Submittals
   Due For Site). All three PDFs render-tested in production (HTTP 200).
   Fixes along the way: sale dependency declared, t-field-on-td removed,
   currency falls back to company currency when a project has no company.
