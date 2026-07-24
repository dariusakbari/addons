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

## v0.3 — 24 July 2026 (evening)

8. Installed gte_hse 19.0.0.1.0 (FLHA + Toolbox Talk) and gte_field
   19.0.0.1.0 (Daily Site Log), commit c8774dd. Construction → Field & Safety
   menu. Audit remediations built in: PPE never preselected; finalize blocked
   until hazards+controls, crew signatures, work summary, labour lines and
   foreman signature are present; high-risk FLHAs and submitted logs raise
   supervisor activities; signature widgets record timestamps; per-project
   sequences (FLHA-/TBT-/DSL-); PDF reports on letterhead.
9. Production tests: FLHA-001 (draft→submitted→reviewed, high-risk activity
   raised), TBT-001 (submitted), DSL-001 (reviewed, 8.0 hrs). All PDFs
   HTTP 200. Test records on TEMPLATE project, titled "TEST — …".
   NOT yet verified: phone-sized rendering (verify on a real phone).

## Overlap fix + legacy migration — 24 July 2026 (evening)

10. Hidden superseded Studio menus (ir.ui.menu active=false — reverse by
    setting active=true): Project/RFIs (691), Project/Change Management (692),
    Project/Submittals (693), Project/Safety Sheets (694), HSE FLHA Daily (696),
    HSE New Safety Sheet (695), HSE Toolbox Talks (687). Old HSE registers with
    no replacement yet (Equipment, Incidents, Permits, Risk, Overview) left visible.
11. Installed gte_migration and executed tagged-task migration:
    RFI 64/64 (Bayview 50, Meadowvale 14), Change Orders 84/84 (Airport 1,
    Bayview 70, Meadowvale 13), Submittals 41/41 (Airport 5, Bayview 24,
    Meadowvale 12), Standard Submittal specs 98/98. Re-run test: 0 duplicates
    (idempotency proven in production). All 189 records carry
    migration_incomplete=true pending SmartBuild-export enrichment
    (question/response text, parties, pricing, attachments do not exist in Odoo).
    SmartBuild IDs preserved in legacy_source_id; received dates parsed into
    date fields; every record links back to its original task.
    All 189 original tagged tasks remain active and untouched — archive only
    after reconciliation sign-off per safeguards.

## HSE app retirement — 24 July 2026 (evening)

12. Upgraded gte_hse to 19.0.0.2.0: Incident Reports (INC-), Equipment
    Inspections (EQI-), Work Permits (WP- with expiry cron), Risk Register
    (RSK- with computed 5x5 score). All validation gates and escalation
    activities production-tested; test records on TEMPLATE project.
13. Hidden the old Studio "HSE & Safety" app root menu (id 685,
    active=false — reversible). Its x_hse_* models and 3 legacy records
    remain intact in the database. Project app retained (Construction is
    built on it). Construction → Field & Safety now carries: Daily Site
    Logs, FLHAs, Toolbox Talks, Incidents, Equipment Inspections, Work
    Permits, Risk Register.

## v0.4 + documents — 24 July 2026 (late evening)

14. Upgraded gte_controls 0.3.0 / gte_hse 0.3.0 / gte_field 0.2.0:
    smart buttons on project and task forms with live counts and filtered
    click-through (Bayview verified: 50 RFIs / 70 COs / 24 submittals).
15. Installed gte_documents 0.1.0: construction metadata on every document
    (number, type, discipline, revision, current/superseded, issue date,
    source, links to RFI/CO/Submittal/Task), "Register Revision" supersede
    workflow, Construction → Drawings & Documents register.
    UAT passed in production: rev 1 superseded rev 0 with rev 0 file
    byte-intact, statuses and cross-links correct, double-supersede blocked.
    Test docs "TEST E-401 …" in Bayview / 02 Drawings — remove after review.

## Phase 8 scaffold + integrity fix — 24 July 2026 (night)

16. Created analytic account "250752 - 400 University…" (id 19) and linked
    it to project 24 — all 4 real projects now have analytic accounts.
    (S000xx demo-company analytic accounts noted as demo remnants, untouched.)
17. Installed gte_commercial 0.1.0 → 0.2.0: Project Budgets (sectioned
    lines; budget vs committed CO-exposure vs analytic actuals vs variance;
    approve/close), Labour Rates (NO access for field/foreman groups;
    cost column accounting/admin only), Worker Certifications (expiry
    states, 30-day reminder cron). Construction → Commercial menu
    (PM/accounting only). Bayview budget approved: $520,000.
18. INTEGRITY FIX: Odoo 19 silently ignores _sql_constraints. Converted all
    7 uniqueness constraints to models.Constraint (gte_controls 0.4.0,
    gte_field 0.3.0, gte_commercial 0.2.0). Production-verified: duplicate
    rate, budget, RFI number and daily log all now rejected.
    Still needed from owner for full Phase 8: employee roster + rates,
    rate-visibility policy, QuickBooks/accounting baseline, billing-flow
    decision.

## Phase 4 complete — 24 July 2026 (night)

19. Upgraded gte_field to 19.0.0.4.0: NCR (assignment activities, close
    requires corrective action), General Inspection (checklist lines,
    overall fail escalation), Site Attendance (unique per project/date,
    float-time in/out), Visitor Log, Transmittal (Document Flow menu),
    Shop Drawing, Gate Pass (authorize gate). Membership record rules on
    all 7. Production-tested: all gates block, NCR-001/GI-001/ATT-001/
    VIS-001/TR-001/SD-001/GP-001 created on TEMPLATE project ("TEST — …").
    All 14 Phase 4 record classes from the mission are now implemented.

## Mail + deliverable docs — 24 July 2026 (night)

20. Installed gte_mail 0.1.0: four mail templates (RFI to consultant,
    CO to client, submittal request to supplier, daily-log distribution)
    with the matching PDF auto-attached; Email buttons on all four forms
    open the composer preloaded (verified in production). Sending remains
    INERT until outgoing/incoming mail servers are configured — external
    delivery, replies, bounces and aliases still untested (Phase 6 gate).
21. Added docs/: DATA_DICTIONARY.md (generated from source, all gte.*
    models), ACCESS_CONTROL_MATRIX.md (generated from ACL files),
    ADMIN_GUIDE.md, FIELD_USER_GUIDE.md.

## Regression test, icon, project hub + incident — 24 July 2026 (late night)

22. Full production regression: 29/29 PASS (docs/UAT_RESULTS.md).
23. Construction app icon (flat Odoo-style hard hat + bolt) via
    gte_controls 0.5.0; web_icon on root menu.
24. Installed gte_hub 0.1.0: SmartBuild-style project-centric navigation.
    Project form now has RFIs / Change Orders / Submittals / Field & Safety
    tabs with embedded per-project registers; records created inside a
    project auto-link. Verified on Bayview (50 RFIs in-form).
25. INCIDENT + FIX: after repeated module upgrades, Odoo's regenerated web
    asset bundles were corrupt — backend actions rendered blank pages with
    no errors (navbar only). Not caused by any gte module (bisect-verified).
    FIX (documented for admins): delete ir.attachment records where url
    like '/web/assets/%', restart via OSM, hard-reload. Applied twice;
    client fully recovered. If it recurs after future upgrades, repeat.

## Role-correct field workflow — 24 July 2026 (v2, late night)

26. Created TEST Field Employee user (id 9, field.test@greentechelectric.ca,
    Internal + Field Employee + Project User groups, member of Bayview only,
    NO password — owner sets it via Change Password for phone testing).
    Structural verification: sees only Bayview records (50 RFIs pre-change),
    no Settings/admin, no labour-rate access.
27. Upgraded gte_controls 0.6.0 / gte_field 0.5.0 / gte_hub 0.2.0 per owner
    workflow direction:
    - New Field Issues register (FI-): field crews raise site issues with
      photos/drawing refs; submit notifies the PM; PM "Release RFI" creates
      the prefilled, linked RFI. Tested: FI-001 → RFI-051 (Bayview), PM
      activity raised, double-release blocked.
    - Menu visibility for pure field employees is now exactly:
      Field & Safety + Drawings & Documents. RFIs/COs/Submittals/Overview/
      Document Flow are coordinator+ (estimator also sees Change Orders).
      Construction app opens on Field & Safety for field crews.
    - Change orders: field-employee ACL removed entirely — no CO records or
      values reachable by field/foreman roles; CO smart buttons and hub tabs
      coordinator/estimator only.
