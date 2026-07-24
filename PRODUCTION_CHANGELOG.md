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
