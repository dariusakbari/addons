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

## Upgrade spec Phase 1 — 24 July 2026 (v2)

Pre-phase backup: odoo.greentechelectric.ca_20260724_231612.zip.
28. Deployed gte_core 0.2.0 + gte_controls 0.7.0 (commit ef3d61c):
    - project.gte_code + numbering format {code}-TYPE-### per D3.
      Renumbered ALL 210 existing records (68 RFI, 85 CO, 42 SUB, 15
      field/HSE); sequences re-prefixed with correct next numbers.
      Legacy SmartBuild IDs untouched in legacy_source_id.
    - Extended gates per spec P2 (RFI send/close, CO submit/approve/
      billed/paid, Submittal submit/close) — production-tested; every
      gate blocked and listed its missing fields, including the
      "client contact" gate catching TEMPLATE's missing customer.
    - Mandatory-reason wizard for cancel/reopen/override; reason posted
      permanently to chatter (tested). Reopen is PM+; override admin-only.
    - Issued/approved records cannot be deleted (tested); archive via
      new active fields instead.
    - Settings → Construction: CO approval limit (currently 0 = disabled,
      awaiting D4 value), RFI/submittal reminder leads.
    Test records TMPL-RFI-004/005, TMPL-CO-002, TMPL-SUB-002 on TEMPLATE.

## Upgrade spec Phase 3 — 25 July 2026

Pre-phase backup: OSM 2AM daily (25 Jul) + prior manual points.
29. Deployed gte_documents 0.2.0 (commits ca24aa5→8137751). Document
    control complete, all production-tested on Bayview/02 Drawings:
    - Register Revision now accepts a direct file upload (auto-creates the
      new revision doc); predecessor must be current. rev2→rev3 by upload OK.
    - SUPERSEDED red ribbon on the form.
    - Mass "Set Construction Metadata" action + auto-file into the correct
      project subfolder by type (spec → 03 Specifications verified).
    - "Download Issue Package" zips current revisions only — superseded
      excluded by design (3 selected → 2 in zip, 359 bytes).
    - "Create Transmittal" from selected docs freezes exact revisions into
      transmittal lines (0476-TR-001, revs 3+0, 2 files) and refuses
      superseded selections.
    - Register menu opens the list view (blank-form bug already fixed).
    Note: OSM "up to date" status can lag; always Refresh then Pull, and
    confirm field/behaviour after upgrade (cost one extra cycle here).
    Test artifacts: TEST E-401 chain + TEST SPEC in Bayview/02+03,
    TEST Package.zip, 0476-TR-001 — clean up after review.

## Upgrade spec Phase 4 — 25 July 2026

30. Deployed gte_field 0.6.0 (commit 8949848). Field-workflow suite,
    all production-tested on TEMPLATE:
    - Field Memo / Site Instruction (Field Issue extended): recipient,
      required-action date, cost/schedule impact, related change,
      acknowledgement, distribution. TMPL-FI-001 acknowledged, cost 1500,
      2 days sched.
    - Deficiency / Punch List (gte.punch.item, PL-): before/after photos,
      priority, corrective action, verification. Gates: ready needs
      corrective action, close needs an after-photo (both blocked as
      expected). TMPL-PL-001 closed.
    - Inspection → deficiency: "Log Deficiency" button + deficiency smart
      button; TMPL-PL-001 created from inspection, count rolled up.
    - Meeting Minutes (gte.meeting, MIN-) + action items: issuing raises
      owner activities for internal owners only (1 of 2, external skipped);
      TMPL-MIN-001 issued.
    - Closeout Register (gte.closeout.item): O&M/as-built/warranty/etc.
      with required→received→reviewed→accepted; accept needs an attached
      document (blocked then passed). TMPL closeout accepted.
    Note: a failed upgrade left an Odoo module-op lock ("processing another
    module operation"); a Restart cleared it. Menus for Meeting/Closeout
    live under Construction → Document Flow; Deficiencies under Field & Safety.

## Upgrade spec Phase 2 — 25 July 2026 (email code; server deferred)

31. Deployed gte_mail 0.2.0. Complete email WORKFLOW code; inert until an
    outgoing mail server exists (owner: connect an SMTP relay after the
    greentechelectric.ca domain move, with full two-way inbound).
    Verified via ORM (before a display glitch, see note):
    - Reminder crons "GTE: RFI response reminders" + "GTE: Submittal
      on-site reminders" using configurable lead days; RFI reminders fired
      on 8 due records, submittal on 1; idempotent (re-run 8→8).
    - Mail-readiness diagnostics (Settings → Construction): computes
      outgoing/incoming/alias-domain/template status; shows the NOT-SET
      warning correctly (mail_ready=false, templates OK). All settings
      fields default_get cleanly.
    - Bounce detection field (gte_mail_bounced) computes from
      mail.notification bounce/exception status.
    - Send / Send Reminder / Resend buttons added to RFI/CO/Submittal forms;
      transmittal email template added.
    NOTE: after this upgrade the backend web client rendered blank across
    all pages — a stale service-worker + corrupt asset bundle (debug=assets
    mode made it worse). Fix that WORKED: clear ir.attachment url like
    '/web/assets/%', restart, then in the browser unregister service
    workers + clear caches (or just log out/in). Public site stayed healthy
    throughout. Session was logged out to clear it — owner logs back in for
    a clean backend.
    Acceptance test (send RFI → reply attaches → distribute) DEFERRED to
    the mail-server connection after the domain move.

## Namespace cutover: gte_ -> cs_ (Construction Suite) — 25 July 2026

Owner decision: full de-brand + clean production cutover to a neutral,
white-label namespace so the modules can be reused on any Odoo instance.
Backup taken first: odoo.greentechelectric.ca_20260725_155810.zip.

32. Renamed all modules gte_* -> cs_*, models gte.* -> cs.*, every field/
    method/XML-ID/relation-table gte_ -> cs_; author 'Green Tech Electric'
    -> 'Construction Suite'; app names 'GTE ...' -> 'Construction ...'.
    Zero gte/GTE/Green Tech left in module code (commit chain 23082df..9ac64f8).
33. Production cutover (destructive, backup-protected):
    a. Uninstalled all gte_* (cascade from gte_core) — gte.* models/records
       dropped. Native data preserved: 189 tagged tasks, 104 doc folders,
       13 analytic accounts, 12 projects, users, CRM.
    b. Pulled renamed repo (gte_ folders replaced by cs_), restarted.
    c. Installed all 10 cs_* modules. Fixes needed on first portal install:
       dropped nonexistent base.module_category_hidden ref; changed portal
       share-view xpath from @string selector (forbidden in Odoo 19) to
       //notebook inside.
    d. Reconfigured: project codes (0476/0436/0999/250752/TMPL), Construction
       Administrator assigned to d.akbari + m.kazimi.
    e. Re-ran migration: 64 RFI / 84 CO / 41 submittal / 98 spec rebuilt on
       cs.* with 0476-RFI-001 numbering; 189 exceptions flagged; tagged
       tasks intact. 5 crons present. Menus/app icon intact.
    Verified in UI (RFI list renders with migrated Bayview records).
    NOTE: leaving the browser in ?debug=assets mode causes blank action
    panes after installs; exit with /web?debug=0. That was the display
    gremlin all session, not a code fault.
LOST in cutover (re-creatable / minor): test records, Bayview budget +
labour rates (gte.project.budget/rate), document revision-metadata links,
the TEST field user's group assignment. Redo as needed.

## Upgrade spec Phase 7 — 25 July 2026 (reporting & dashboards)

34. Installed cs_dashboards 0.1.0. Native Odoo 19 analytics + reports:
    - Graph + pivot views: RFIs, Change Orders (proposed/approved/exposure
      measures), Submittals, Deficiencies, Incidents, Budgets (budget vs
      committed vs actual vs variance).
    - "Construction Dashboard" menu placed in the PROJECT app at the
      Overview level (parent project.menu_main_pm, sequence 1) with:
      Change Exposure, RFIs, Submittals, Deficiencies, Incidents, Budget
      vs Actual. Same analytics also under Construction → Reporting.
    - Printable log PDFs bound to list actions (respect selection):
      RFI Log, Change Order Log (+exposure total), Submittal Log, Punch
      List. Excel/CSV via native list export.
    Verified: menus in both places, Submittal graph renders by project,
    all 3 log PDFs HTTP 200. (CO exposure = 0 until COs get pricing from
    the pending SmartBuild enrichment — correct.)
    Reminder: exit browser debug mode (/web?debug=0) after installs or
    action panes render blank.

## Phase 7b: KPI-box dashboard — 25 July 2026

35. Upgraded cs_dashboards to 0.2.0. Rebuilt "Construction Dashboard" (in
    the Project app at Overview level) as a real KPI-box page — an OWL
    client action styled like Project Overview:
    - 11 clickable metric cards grouped by RFIs / Submittals / Change
      Orders / Field & Safety, colour-toned by urgency with icons:
      Open RFIs (7), Overdue RFIs, Pending Submittals (9), Changes Awaiting
      Client, Approved-Unbilled, Open Change Exposure ($), Open
      Deficiencies, Open Incidents, Field Issues to PM, Certs Expiring/
      Expired, Active Work Permits.
    - Each card drills into its filtered list (verified: Open RFIs -> the 7
      records). Data from cs.dashboard.get_kpis (live counts).
    Assets: cs_dashboards/static/src/dashboard.{js,xml,scss} on
    web.assets_backend. Graph/pivot analyses remain under Construction ->
    Reporting.

## Project-type tags + Phase 8 scheduling — 25 July 2026

36. cs_core 0.4.0: 16 construction project-type tags (Medical, Dental,
    Institutional, Educational, Religious, Recreational, Residential,
    Commercial, Industrial, Retail, Hospitality, Government, New
    Construction, Upgrade/Retrofit, Tenant Improvement, Service) — editable,
    ship with the module. Applied live: Bayview=Educational+Institutional,
    Meadowvale=Institutional+Religious, Airport Tennis=Recreational,
    400 University=Commercial+Upgrade.
37. Installed cs_schedule 0.1.0 (Phase 8):
    - project.project: baseline + forecast start/finish; Schedule tab;
      cs_schedule_impact_days rollup = open delay-event days + schedule_days
      from OPEN RFIs/COs/field issues (closed excluded — verified: Bayview
      3 delay + 5 open RFI = 8; a closed RFI correctly ignored). Delays
      smart button.
    - cs.delay.event (DLY-): cause, days, links to RFI/CO/daily log/field
      issue; list + calendar (by cause). 0476-DLY-001 created.
    - Schedule menu: 2/3/6-week look-ahead task actions (list/kanban/
      calendar/gantt by deadline window; relative-date domains eval OK,
      2 tasks in 6-wk window) + Delay Events register.
    Native Project/Planning cover milestones, dependencies, crew shifts.

## Dashboard merged into Overview + pivot fix — 25 July 2026

38. Merged the Construction Dashboard into the Project app's "Overview"
    menu (kept the name "Overview"): Project Overview (menu 713) now opens
    the KPI dashboard client action; the separate "Construction Dashboard"
    menu removed. cs_dashboards 0.3.0 carries a post_init hook so fresh
    installs do the same. Verified in DB (Overview -> ir.actions.client,1302;
    separate menu inactive).
39. FIX: Odoo 19 pivot error "No aggregate function for measure" —
    added aggregator="sum" to cs.change.order amounts (proposed/approved/
    exposure) and cs.project.budget amounts (budget/committed/actual/
    variance). cs_controls 0.8.0, cs_commercial 0.3.0. Verified: CO
    read_group returns 3 groups.
    DISPLAY NOTE: after this upgrade the browser session's web client
    action-manager failed to mount (blank content, navbar only) — assets
    compile fine server-side and all data/menus verified via ORM. This is
    the recurring session asset gremlin; a fresh login (log out/in) or a
    clean/incognito browser restores it, as it did earlier today.

## Blank-page root cause + upgrade hardening — 25 July 2026

40. ROOT CAUSE of the recurring "blank content, navbar only": diagnosed to
    the render layer, not the app. All assets 200, modules load (0 failed),
    action registered, template present, get_kpis returns 11, ORM service
    returns in ~50ms — yet the OWL scheduler held 2 finished-but-unflushed
    tasks (ActionContainer + LoadingIndicator, counter 0). Tab was
    document.hidden = true: Chrome throttles requestAnimationFrame in
    hidden/background tabs, so OWL never flushed its paint. Forcing
    scheduler.processTasks() instantly rendered Contacts, the Projects
    kanban, and the Overview dashboard (11 KPIs, 4 groups). Conclusion: no
    code defect; the blank is a background/stale-session artifact. Cures:
    focused reload, clear /web/assets/ attachments, or unregister the
    odoo-sw-cache service worker (all three exercised today).
41. HARDENING (upgrade-proofing): audited all 12 cs_* modules — no raw SQL,
    no hard-coded IDs, no private API imports, clean manifests (19.0.x
    versions, explicit depends), all _inherit on stable public models,
    constraints via models.Constraint. Made the Overview merge self-healing:
    extracted _cs_apply_overview_merge(env) helper (idempotent) and added
    cs_dashboards/migrations/19.0.0.4.0/post-migrate.py so the menu repoint
    re-applies on every upgrade (post_init_hook only fires on install).
    cs_dashboards -> 0.4.0. New doc: docs/CORE_UPGRADE_SAFETY.md (audit +
    pre/post-upgrade checklist). Only residual upgrade risk is the ordinary
    one: 8 views inherit core Project views (project.edit_project,
    project.view_task_form2) — a major version could move an anchor; fix is
    a small xpath repair, documented in the checklist.

## Overview: per-project KPI cards — 25 July 2026

42. Reworked Project > Overview from company-wide totals into one card block
    per construction project (owner request: "separate each project, not
    just how many items there are"). New cs.dashboard.get_project_kpis()
    computes per-project counts via read_group (verified working in Odoo 19)
    for 10 project-scoped metrics: Open/Overdue RFIs, Pending Submittals,
    Changes Awaiting Client, Approved-Unbilled, Open Change Exposure $, Open
    Deficiencies, Open Incidents, Field Issues to PM, Active Work Permits.
    Each card drills through to that project's filtered list. Certs excluded
    (worker-level, not project-scoped). Projects shown = any with a
    construction record, sorted by cs_code. OWL component + template rewritten
    for project blocks (code chip + name header, compact card grid); SCSS
    updated. cs_dashboards -> 0.5.0 with a 0.5.0 post-migrate re-asserting the
    Overview merge. NOTE: read_group is public in 19 but deprecated long-term;
    swap to formatted_read_group if a future major version removes it (added
    to the upgrade smoke-test).

## Overview: budget/cost/progress KPIs — 25 July 2026

43. Added status + commercial KPIs to each project block in Overview
    (owner request: "budget, costs, progress"). New per-project cards:
    Task Progress (% from project.task_completion_percentage), Open Tasks.
    Commercial cards — Budget, Committed (Changes), Actual Cost, Budget
    Variance — computed with sudo and shown ONLY to PM / Accounting / Admin
    (cs_core.group_cs_pm/accounting/admin). The dollar Change Exposure card
    was moved out of the everyone-visible set into this gated group so field
    staff no longer see change-order dollar values (honours the earlier
    field-user rule). Budget/Variance pull from cs.project.budget (show "—"
    when a project has no budget yet); Committed = open CO exposure; Actual =
    costs booked to the project analytic account. All native fields used
    (task_completion_percentage, open_task_count, is_closed, account_id) are
    upgrade-stable. cs_dashboards -> 0.6.0 with 0.6.0 post-migrate re-asserting
    the Overview merge. NOTE: no budgets or analytic costs exist yet post-
    cutover, so money cards currently read $0/"—"; they populate as budgets
    and costs are entered.

## Overview visual redesign — 25 July 2026

44. Redesigned the Overview (owner: "too much information without proper
    order; make it appealing, SmartBuild-style"). Each project is now one
    clean card: header (code chip, name, client, type tags) -> a task
    progress bar with done/total/open counts -> three labelled metric
    sections (RFIs; Submittals & changes; Field & safety) -> a locked
    Commercial footer (Budget/Committed/Actual/Variance, PM/Accounting/Admin
    only). Urgency colours added per owner request: due-soon = amber, overdue
    = red, safety incidents = red, zeros greyed out so attention items stand
    out. "Due soon" windows are settings-driven (cs.rfi_reminder_days=2,
    cs.submittal_reminder_days=7) — RFIs use date_required, submittals use
    date_required_submit. Every stat and money item still drills through to
    its filtered list. get_project_kpis now returns sections + money + progress
    + tags; OWL template/SCSS rebuilt (card, progress bar, grouped stats).
    cs_dashboards -> 0.7.0 with 0.7.0 post-migrate re-asserting the merge.

## Phase 6.1 — Commercial & job cost (increment 1) — 25 July 2026

45. Built the first commercial increment (owner decisions: COs bill by adding
    a Sale Order line; holdback on, custom % from settings).
    - Labour rates (cs_commercial 0.4.0): effective_from date (rate history),
      OT/DT multipliers with computed OT/DT sell rates, and a
      get_effective_rate(classification, date) lookup. Uniqueness now per
      (classification, company, effective_from).
    - Budget forecast: amount_cost_to_complete (input), amount_forecast
      (= actual + CTC), amount_forecast_variance (= budget − forecast).
      Shown on budget form/list.
    - Holdback: cs.holdback_percent setting (cs_core 0.5.0, default 10%) +
      per-project cs_holdback_percent override and cs_contract_amount on the
      project form (PM/Accounting only).
    - CO → Sale Order (cs_controls 0.9.0): "Bill via Sales" button on approved
      COs creates/updates one draft sale order per project (new
      sale.order.cs_project_id link) and adds a line for the approved amount
      using a new "Change Order Work" service product; price forced to the
      approved amount; SO smart button on the CO form. Verified Odoo 19 field
      specifics (product type 'service', invoice_policy 'order', sale line
      product_uom_id) before build.
    Next (6.2): AIA-style progress billing / payment application with holdback.

## FIX: migration signature — 25 July 2026

46. CRITICAL upgrade fix: this Odoo build requires post-migration scripts to
    use def migrate(cr, version); our cs_dashboards migrations used
    (env, version) and were aborting the upgrade transaction (which also
    rolled back cs_controls' new "Change Order Work" product on the 6.1
    deploy). Rewrote all cs_dashboards migrations (0.4.0–0.7.0) to
    migrate(cr, version) building env from the cursor, added a 0.8.0
    migration, and made the CO service product resilient via a get-or-create
    helper (no longer dependent on data-file load order). cs_dashboards
    0.8.0, cs_controls 0.9.1. Documented the signature rule in
    docs/CORE_UPGRADE_SAFETY.md.

## Phase 6.2 — Progress billing / payment applications — 25 July 2026

47. Built AIA G702-style progress billing (cs_commercial 0.5.0). New model
    cs.payment.application (PA- per-project numbering): original contract
    (defaults from project), approved change orders, revised contract sum,
    completed-to-date input with % complete, previous vs this-period, holdback
    to date + this-period holdback (holdback % defaults from project), earned
    less holdback, less previous payments, current payment due. Workflow
    draft → submitted → approved → invoiced with gates (period-end required;
    completed-to-date must exceed previously billed; reset PM-only; can't
    cancel once invoiced). "Create Invoice" generates a draft customer invoice
    (account.move) with a progress line (this period) and a negative holdback
    line so the net equals current due, using a resilient get-or-create
    "Construction Progress Billing" service product. Payment Certificate PDF
    (report). Menu under Commercial; ACL PM/Accounting/Admin (unlink admin
    only); unlink guard. Next: deploy + verify end to end.

48. Phase 6.2 VERIFIED in production (TEMPLATE project, test records removed):
    PA-001 40% (contract 100k) → $40k this period, $4k holdback, $36k due;
    PA-002 → prev $40k, this period $30k, $3k holdback, less $36k previous =
    $27k current due; Create Invoice produced a draft out_invoice netting
    $27,000 (line $30,000, holdback line −$3,000). All math correct.
    DEPLOY NOTE: a plain OSM "Restart" did not register the new model file —
    the model only appeared after a full module upgrade (button_immediate_
    upgrade / -u). For future NEW models, force a module upgrade, not just a
    restart.

## Phase 10 — Automation & escalation engine — 25 July 2026

49. New module cs_automation (0.1.0): configurable escalation engine.
    cs.escalation.rule with rule_type presets (RFI required-response,
    submittal required-submission, change-order decision, work-permit
    valid-to, cert expiry), timing before/after, days, and notify
    (project manager / record responsible / specific user). One daily cron
    (_cron_run) raises a deduped to-do activity on each matching record for
    the resolved user (dedup marker [escN] in the summary). Seven default
    rules seeded (lead reminders + overdue for RFI/CO, plus submittal/permit/
    cert leads). post_init retires the three overlapping activity crons
    (cs_controls.cron_rfi_overdue, cs_hse.cron_permit_expiry,
    cs_commercial.cron_cert_expiry) so nothing double-fires. Config menu under
    Construction (admin). ACL: admin manage, PM read. New module — requires
    app-list update + install (not just upgrade). To verify: install, run the
    cron, confirm activities appear and old crons are inactive.

## Phase 9 — Field QR codes — 25 July 2026

50. Scan-to-open QR codes for the field (cs_hse 0.4.0). New cs.qr.mixin
    computes a QR image (base64 PNG via the qrcode library, fully guarded —
    returns nothing if the lib is unavailable, never raises) encoding the
    record's form URL. Added to cs.work.permit and cs.equipment.inspection,
    shown top-right on their forms (hidden when empty). Note: Odoo's built-in
    barcode renderer is broken on this server (missing rlPyCairo/pycairo), so
    QR is generated via qrcode directly; if qrcode is also absent the field
    stays hidden and the owner can pip-install it server-side. Photos already
    exist on field records (attachment fields); phone rendering + camera
    capture remain an on-device check for the owner.

## Audit fixes — overdue KPI, test-user role, gates proven — 25 July 2026

51. BUG FIX (audit #4): the "Overdue RFIs" everywhere read 0 despite 7 open
    past-due RFIs on Bayview. Root cause: cs.rfi._search_is_overdue was
    returning an empty result for both True and False (context_today in the
    search context + a malformed "!" negation), so every is_overdue domain
    filter (dashboard KPI, saved Overdue-RFIs action, search filter) was blank
    even though the field computes correctly. Fixed the search method
    (fields.Date.today(), explicit '&', proper De Morgan negation) AND switched
    the consumers off the computed field to reliable stored-field domains:
    dashboard rfi_over_dom -> [date_required < today, state in draft/open/sent];
    action_cs_rfi_overdue and the RFI "Overdue" search filter -> dynamic
    context_today() date domains. cs_controls 0.9.2, cs_dashboards 0.9.0
    (+0.9.0 migration). Data verified: Bayview has 7 open RFIs past due
    (0476-RFI-001/002/003/004/005/019/020).
52. FIX (audit #3): "TEST Field Employee" (uid 9) had lost its construction
    role in the gte->cs cutover (Construction Suite = None). Reassigned
    group_cs_field via group_ids; verified.
53. VERIFIED (audit #6) — server-side workflow gates enforce (tested on
    TEMPLATE, records removed): RFI cannot be distributed without recipients
    ("Distribution recipients required"); RFI cannot be closed without
    response/distribution; CO cannot be submitted without pricing; CO cannot
    be approved without an approval reference; Submittal cannot be closed
    without a review outcome and returned date. Reopen/cancel route through the
    mandatory reason wizard.
54. NOTED (audit #5b): branded register/log PDFs DO exist (RFI, CO, CO Log,
    Punch List, Daily Log, FLHA, Payment Certificate) — reachable via the
    Print menu on the respective list views.

## Audit #5 graph verified + #5c exec report + #7 milestones — 25 July 2026

55. VERIFIED (audit #5a): the RFI Analysis graph is NOT broken — it renders a
    stacked bar chart (per project, by state) across all 64 records with a Sum
    line. The earlier "blank" was a render-timing artifact (paints on a focused
    reload), not a data/config bug.
56. NEW (audit #5c): on-demand Executive Summary PDF (cs_dashboards 0.10.0).
    project.project.cs_exec_summary() computes per-project KPIs (progress %,
    open/overdue RFIs, pending submittals, open changes + exposure,
    deficiencies, incidents, budget, forecast); report_cs_exec renders a
    portfolio table. Printable from the Projects list (Print -> Executive
    Summary). Weekly email deferred until SMTP go-live per owner.
57. ENHANCED (audit #7): added Milestone Deadline look-aheads (2/3/6 week) on
    project.milestone alongside the task look-aheads, reorganized under
    Schedule > Tasks and Schedule > Milestone Deadlines (cs_schedule 0.2.0).
    Verified project.milestone.deadline/project_id exist.
    cs_dashboards 0.10.0 (+0.10.0 migration).

## Backlog batch 1 — 25 July 2026

58. FIX (P1): renamed the confusing look-ahead menus. Schedule now has
    "Task Look-Ahead" (Tasks — Next 2/3/6 Weeks) and "Milestone Deadlines"
    (Milestones — Next 2/3/6 Weeks). cs_schedule 0.3.0.
59. FIX (P1): RFI Analysis graph set to explicit bar, sample="0" (the sample
    overlay was the likely "blank" cause). cs_dashboards 0.11.0.
60. CONFIG (P0): cs.co_approval_limit set to 10000 — change orders approved
    above $10k require a Construction Administrator. Adjustable in Construction
    Settings. Non-admin blocking to be proven in the automated test suite.
61. PARTIAL (P0): Drawings & Documents opens a blank new record. Added a list
    act_window.view (action now correctly reads view_mode list,form with list
    first) but the Enterprise Documents app still hijacks the documents.document
    action to create mode — confirmed a normal model with 8 records would show
    the list. Proper fix: a dedicated cs.drawing register model we fully
    control (next build). cs_documents 0.3.0.

## Drawing Register (dedicated) — 25 July 2026

62. FIX (P0 #2): built a dedicated cs.drawing register model to replace the
    Enterprise-Documents-hijacked register. Fields: doc number, title, project,
    type, discipline, revision, status (current/superseded), issue date,
    source, file attachment, predecessor/superseded-by, links (RFI/CO/
    submittal/task). "Register New Revision" copies to rev+1 (Current) and
    marks the prior Superseded with a chatter note. Register list opens by
    default (no more blank new record). Branded Drawing Register PDF. The
    existing "Drawings & Documents" menu is repointed to the new register.
    ACL: field read, coordinator/PM create+edit, admin full. cs_documents
    0.4.0. (documents.document extension retained for Documents-app files.)

## Executive role removed + workflow test suite — 25 July 2026

63. FIX (#1, owner decision): removed the unused "Executive (Read-Only)"
    construction role (it was mis-scoped anyway). Deleted from cs_groups.xml;
    cs_core 0.6.0 with a 0.6.0 migration that unlinks the group if present.
    No users were assigned to it.
64. TESTS (#4): added cs_controls/tests/test_workflow.py (TransactionCase,
    post_install). Asserts: CO cannot submit without pricing; CO cannot
    approve without an approval reference; submittal cannot close without an
    outcome; the $10k CO approval threshold blocks a non-admin PM but allows a
    Construction Administrator; Field role cannot read change orders; Field
    role cannot create RFIs. (Behaviours already proven manually via RPC; this
    formalises them for CI / on-demand test runs.)

## Field Memo / Site Instruction (#7) — 25 July 2026

65. NEW (#7): cs.site.instruction — a formal Field Memo / Site Instruction,
    distinct from internal Field Issues. Numbered SI-### per project; workflow
    draft -> issued -> acknowledged -> closed (+ cancelled). Issue gate
    requires instruction text + recipient (Issued To); acknowledgement records
    who/when + response; cost impact (none/tbd/yes + amount) and schedule
    impact (days); "Raise Change Order" action creates a linked CO; branded
    Site Instruction PDF. Menu under Field & Safety. ACL: field read,
    coordinator/PM create+edit, admin full; unlink guard. cs_field 0.7.0.

## Schedule of Values + job-cost integration (#5) — 25 July 2026

66. NEW (#5): cs.payment.application.line — a Schedule of Values / AIA G703
    continuation sheet on each Payment Application. Per line: item #,
    description, optional budget-line link, scheduled value, from-previous,
    this-period, materials stored; computes completed-&-stored-to-date, %,
    balance-to-finish and per-line holdback (from the header holdback %).
    Line create/write/unlink rolls the completed total up into the header, so
    all the existing G702 progress math (this-period, holdback, earned-less-
    holdback, current due) is driven by the schedule when lines exist. Header
    Completed-to-Date becomes read-only in SOV mode; lump-sum entry still works
    when there are no lines (backward compatible, no migration).
67. NEW (#5): "Load Schedule from Budget" builds the SOV from the project's
    approved budget lines and carries forward previous-completed from the most
    recent prior application (matched by description).
68. JOB COST (#5): invoicing now emits one invoice line per SOV item billed
    this period, each tagged with the project's analytic account
    (analytic_distribution) so billed revenue lands on the job for cost/
    revenue reporting; holdback line likewise tagged. Falls back to the single
    lump line when no SOV.
69. NEW (#5): "Release Holdback" action creates a separate holdback-release
    invoice for the accumulated holdback, gated to 100% complete and once only;
    tracked via holdback_released + holdback_invoice_id with a smart button.
    Payment Certificate PDF now prints the full SOV continuation sheet with
    totals. ACL for the line model: PM/Accounting rwc, Admin full.
    cs_commercial 0.6.0.

## Branded reporting (#6) — part 1: Excel exports — 25 July 2026

70. NEW (#6): cs_reports module — a spec-driven, brand-styled Excel export
    engine (cs.xlsx.export). Each register's list view gains an "Export to
    Excel (branded)" entry in the Action menu (ir.actions.server bound to the
    list) that streams a formatted .xlsx: Green Tech title band (teal),
    green column headers, bordered cells, number/date formats, a frozen header
    row and money totals. Covers RFI, Change Order, Submittal, Drawing &
    Document Register, Site Instruction, and Payment Applications. Built with
    xlsxwriter; output delivered as an ir.attachment download. cs_reports
    0.1.0. Colours read from res.company.primary_color/secondary_color (Green
    Tech defaults only as fallback), so exports stay white-label — matching the
    PDFs, which already inherit each company's letterhead branding.
    Verified in production: RFI/CO/Submittal exports generate valid .xlsx
    (correct MIME, zip signature, 8 rows each); all six specs field-checked.
    Note: a branded PDF section-heading band was considered but deliberately
    skipped — the register PDFs already carry the company logo, brand colours,
    Montserrat font and footer via web.external_layout, so the letterhead
    covers PDF branding. #6 complete.

## P1 — Meeting Minutes distribution — 25 July 2026

71. NEW (P1): Meeting Minutes distribution on cs.meeting. Added a Distribution
    List (recipients beyond attendees), a branded Meeting Minutes PDF
    (cs_field.report_cs_minutes — attendees, agenda, discussion, action-item
    table, via web.external_layout), and Distribute / Re-send actions. Distribute
    renders the PDF, emails it to all attendees + distribution recipients that
    have an email (message_post, one email with the PDF attached), and writes a
    recipient-history row per person into a new cs.meeting.distribution log
    (recipient, email, timestamp, sent-by, initial vs re-sent). "Distribute" is
    gated to issued state and shown until first sent; "Re-send" appears after.
    A Distribution History tab lists every send. issue now stamps date_issued.
    ACL: coordinator rwc, field read, admin full. cs_field 0.8.0.
72. FIX (P1): the meeting distribution email body rendered its HTML tags
    literally. message_post treats a plain str as text and escapes it — wrapped
    the body in markupsafe.Markup so the paragraph renders, with interpolated
    values still auto-escaped. cs_field 0.8.1.

## P1 — Delay Events expansion — 26 July 2026

73. EXPANDED (P1): cs.delay.event. Added end date; critical-path flag;
    entitlement classification (excusable-compensable / excusable-non-
    compensable / non-excusable); responsible party + liability attribution
    (owner/consultant/contractor/subcontractor/supplier/force-majeure/shared/
    tbd); separate Mitigation Plan and Recovery Plan; contractual notice block
    (notice required, recipient, deadline, notice-given + date, and a computed/
    searchable notice_overdue) with a "Record Notice Given" action gated on a
    recipient; and cost impact (none/tbd/yes + amount). action_mitigate now
    requires a mitigation plan. Form reorganised into Description / Mitigation &
    Recovery / Notice / Links tabs with a "Notice Overdue" ribbon; list shows
    liability, critical-path and turns red when notice is overdue; search adds
    Critical Path, Notice Overdue and Compensable filters plus group-by
    liability. Now also inherits mail.activity.mixin. cs_schedule 0.4.0.
74. FIX (P1): the "Notice Overdue" filter didn't work. A custom search method
    on the computed notice_overdue field returned incorrect results on this
    build (the boolean operator/value passed into the search method is
    unreliable here — same root cause we hit earlier with cs.rfi.is_overdue).
    Dropped the computed-field search method entirely and made the search-view
    filter a static dynamic domain using context_today() (the proven pattern
    from the RFI overdue filter): notice_required, not given, not closed,
    deadline in the past. The non-stored compute still drives the list-row red
    decoration and the "Notice Overdue" ribbon. cs_schedule 0.4.2.

## P1 — Look-ahead planner — 26 July 2026

75. NEW (P1): short-interval / look-ahead planner (Last-Planner style).
    cs.lookahead (header: project, week-starting Monday, 2/3/6-week horizon,
    prepared-by, notes; workflow draft -> issued -> archived; numbered LA-###)
    and cs.lookahead.line (planned activity: trade, subcontractor, planned
    start/finish, computed week bucket, crew/manpower, constraint + status
    clear/at-risk/blocked, weekly commitment flag, status planned/in-progress/
    done/missed with a variance reason, optional linked task). Header rolls up
    activity count, peak manpower (max crew across the weeks) and PPC (Percent
    Plan Complete = committed activities done / all commitments). "Pull Tasks
    from Window" seeds lines from project tasks with a deadline in the horizon;
    "Issue Plan" requires at least one activity and stamps date_issued. Editable
    list groups by week with red/amber/green decoration for blocked/at-risk/done.
    Branded PDF snapshot groups activities by week with per-week crew totals and
    the PPC/peak-manpower footer. Menu under Schedule > Look-Ahead Plans. ACL:
    field read, coordinator/PM create+edit, admin full; project-scoped record
    rules; unlink guard. cs_schedule 0.5.0.

## Email noise → weekly digest — 26 July 2026

76. CONFIG (no code): stopped the frequent per-item reminder emails. Root
    cause: the legacy "Work permit expiry check" cron ran hourly with no
    dedup (re-raising an activity + email every hour), and the escalation
    engine raised an activity per overdue RFI (each activity assignment emails
    the assignee). Deactivated three redundant legacy crons — permit-expiry
    (hourly), certification-expiry (daily), submittal-on-site (daily) — which
    the escalation engine already covers. Set the two real project managers
    (Darius, Mujtaba) to 'in-app' notification delivery so escalation
    activities still appear in Odoo's Activities systray but no longer email.
    All reversible from Settings. No construction cron now runs more than daily.
77. NEW: cs.weekly.digest — a weekly (Monday 08:00 ET) cron that emails each
    project manager ONE consolidated digest of outstanding items on their
    projects: overdue RFIs, RFIs due within 7 days, change orders awaiting
    decision, submittals due within 7 days, open site instructions, open delay
    events, open punch items, payment applications to action, plus permits
    expiring within 14 days and certifications within 30 days. Branded HTML,
    sent as a direct email (independent of the in-app notification setting);
    resilient per-section gathering; "nothing outstanding" note when clear.
    cs_automation 0.2.0.

## Pre-green-light hardening — 26 July 2026

78. FIX (#1): holdback no longer silently defaults to 10%. The project/contract
    holdback (project.cs_holdback_percent) now defaults to 0 unless a value is
    configured in Construction Settings, and Payment Application.create tests
    key-presence (not truthiness) so an explicit 0% is honoured. cs_commercial.
79. FIX (#2): RFI and Submittal "Send email" now auto-populate recipients from
    the record's Distribution list (RFI also adds Addressed To; Submittal adds
    Supplier/Contractor) and refuse to open the composer when no recipient has
    an email. cs_mail 0.3.0.
80. NEW (#3): Site Instruction distribution — Distribution list, Distribute /
    Re-send actions that email the SI PDF to Issued-To + distribution
    recipients, a cs.site.instruction.distribution history log, and a
    Distribution tab. Mirrors Meeting Minutes. cs_field 0.9.0.
81. FIX (#4): Payment Application stays in sync with its invoice. An
    account.move override reverts the application from 'invoiced' back to
    'approved' and clears the link when the linked (progress or holdback)
    invoice is cancelled or deleted, so it can be re-billed. cs_commercial 0.7.0.
82. FIX (#5): a Look-Ahead plan can't be issued until every activity has a
    planned start, planned finish, trade and manpower (and finish on/after
    start); the error lists each offending line. cs_schedule 0.5.1.
83. FIX (#6): the default RFI Analysis graph rendered blank (sample="0",
    state-first). Now bar, project then state, sample="1" — matching the
    working Submittal/CO analysis graphs. cs_dashboards 0.11.1.

## Second hardening pass + project navigation — 26 July 2026

84. FIX (mail): green-light #2 had put the empty-recipient block in the shared
    composer, which would have blocked Change Orders, Daily Logs and
    Transmittals (no distribution list). Reworked: the base recipient set now
    includes the record's client/partner automatically; the empty-recipient
    block applies only to distribution-based records (RFI, Submittal, Change
    Order). Outgoing emails now auto-attach the record's PDF (RFI, CO,
    Submittal). cs_mail 0.4.0.
85. NEW: Change Order Distribution list (cs.change.order.distribution_ids,
    visible on the form). Email/Resend to Client now go to the client +
    distribution list with the Change Order PDF attached. cs_controls 0.9.3.
86. FIX: Payment Application also reverts to Approved (and clears its invoice
    link) when the linked invoice is reset to draft (account.move.button_draft),
    in addition to cancel/delete. cs_commercial 0.8.0.
87. NEW: Payment Application onchange fills the contract sum and holdback from
    the selected project immediately (a project's 0% holdback is preserved).
    cs_commercial 0.8.0.
88. FIX: a Delay Event can't be mitigated or closed until the contractual
    fields are recorded — schedule-impact days, liability, entitlement, notice
    served (when required) and cost amount (when cost impact = yes).
    cs_schedule 0.5.2.
89. FIX/NEW: the Overview page now scrolls (height/overflow), and each project
    card header is clickable — it opens that project's dashboard (the project
    form). cs_dashboards 0.11.2.
90. NEW: the project hub gains Field Memos, Meetings and Schedule (Look-Ahead +
    Delay Events) tabs alongside the existing RFIs, Change Orders, Submittals
    and Field & Safety — every construction record type is viewable, filtered
    to the project, from the project form without entering the Construction app.
    cs_hub 0.3.0 (now depends on cs_schedule).

## Audit round 3 (P0/P1) — 26 July 2026

92. FIX (P0): a Payment Application (INT-PA-001) was stuck 'invoiced' while its
    invoice was cancelled — the mismatch predated the account.move sync.
    Corrected the record (reverted to approved, cleared link) and added a
    cs_commercial migration (19.0.0.9.0) that reverts any invoiced PA whose
    invoice is cancelled, so no stale mismatches remain after upgrades.
    cs_commercial 0.9.0.
93. FIX (P0): module upgrades had reactivated the legacy per-item reminder
    crons that were manually disabled (Overdue RFI escalation, RFI response
    reminders, cert/permit/submittal reminders). Set active=False in each
    cron's own definition so upgrades keep them OFF permanently. They are
    superseded by the cs_automation escalation engine (in-app only). Also set
    the Administrator account to in-app delivery (Darius/Mujtaba already were),
    so the escalation engine never emails anyone — zero automated per-item
    emails. cs_controls 0.9.4, cs_mail 0.4.1, cs_hse 0.4.1, cs_commercial 0.9.0.
94. FIX (P1): Site Instruction Distribution tab — the distribution list is now
    labelled inside a group, last-distributed shown, delivery history always
    visible with a "not yet distributed" hint. cs_field 0.9.1.
95. FIX (P1): Look-Ahead activity fields (activity, trade, planned start/finish,
    manpower) are now visibly required in the grid, matching the issue gate.
    cs_schedule 0.5.3.
96. FIX (P1): Delay Event — responsible party is required, and notice recipient
    + deadline are required when "Notice Required" is checked (until notice is
    served). cs_schedule 0.5.3.
97. FIX (P1): RFI Analysis graph — simplified to a single count-by-status bar
    (was blank for some clients due to a cached two-dimension view). The view
    arch change busts the client cache. cs_dashboards 0.11.3.

## Audit round 4 — 26 July 2026

98. FIX (P0): the escalation engine's two RFI rules ("RFI response due soon",
    "RFI response overdue") were still active — the last possible source of
    automated RFI notifications. Deactivated both (durably: active=False in the
    noupdate data). The engine keeps its submittal/CO/permit/cert rules
    (in-app only, all recipients on inbox). cs_automation 0.2.1.
99. FIX (P1): Look-Ahead — the "Issue Plan" button is now hidden until every
    activity is complete (planned dates, trade, crew), via a can_issue compute,
    with a red hint when incomplete. The server gate remains as a backstop.
    cs_schedule 0.5.4.
100. FIX (P1): Delay Event — "Record Notice Given" only shows once a recipient
     and deadline are set; "Mark Mitigated"/"Close" only show once the
     contractual fields (responsible party, entitlement, days, mitigation plan,
     notice served if required, cost amount if any) are recorded — via
     can_serve_notice / can_mitigate computes, with a red hint otherwise.
     cs_schedule 0.5.4.

## Branding — 1 August 2026

101. BRANDING: replaced the Construction app-tile icon with the new
     Green Tech Electric icon (design-supplied, 840x840 PNG) at
     cs_controls/static/description/icon.png; bumped cs_controls to 0.9.5 so
     the app-grid asset refreshes on upgrade. Requires push + upgrade to take
     effect.
102. BRANDING: set the website Favicon (Settings > General Settings > Favicon,
     stored on website id 1) to the same icon via authenticated session.
     Odoo re-encoded it to a 16x16 .ico served at /web/image/website/1/favicon.
     NOTE/LIMITATION: the Odoo *backend* browser-tab favicon and the
     add-to-home-screen (PWA) icon are hardcoded by Odoo core to
     /web/static/img/favicon.ico and the core manifest; changing those needs a
     small web.layout / manifest override module (previously declined). The
     website favicon and app-tile icon do NOT require that module.

## Upgrade backlog — 1 August 2026

103. FEATURE (P0.1-3, P0.4): new module **cs_hse_templates** — a version-
     controlled Safety Report Template Library. Admin/safety-lead build
     templates (sections + questions) with answer types Pass/Fail/N-A,
     Yes/No/N-A, Rating, Number, Text; per-question flags for required,
     photo-required and corrective-action-if-failed. Publishing locks a
     template's structure (edits require New Version) so historical reports
     stay reproducible. Field reports snapshot the template version, capture
     answers, comments, corrective actions, required photos, and crew +
     supervisor signatures (drawn on-screen or typed name). States:
     Draft -> Complete -> Issued -> Locked (+ Cancel), with server-side
     validation (all required answered, required photos present, corrective
     actions on fails, crew+supervisor signatures before Issue) and an
     edit-lock once issued. Controlled QWeb PDF, distribution list with
     recipient history + resend (mirrors Site Instruction). Per-template and
     per-project QR deep links (/safety/new) via a QR poster wizard for fast
     mobile entry. Seeded one published "Daily Site Safety Inspection"
     starter template. Coexists with the existing fixed Toolbox Talk / FLHA /
     Equipment Inspection forms (migrate-later, per decision). cs_hse_templates
     0.1.0. Additive only (new tables); no core or existing-model changes.
     PENDING P0.5: real two-device no-signal offline test (user-side, needs
     native Odoo mobile app + devices).
104. FEATURE (P1.1): Submittal procurement / delivery tracking. Added to
     cs.submittal: Released for Fabrication, Production Lead Time (days),
     Anticipated Delivery (auto = release + lead unless set), Supplier-
     Confirmed Delivery, Actual Delivery, a computed Delivery Status
     (Not Released / In Production / Delivered), an unstored Delivery-Overdue
     flag (date-based, mirrors the delay/RFI overdue pattern), a Purchase
     Order link, and a computed PO Receipt Date pulled from the PO's completed
     incoming receipts (guarded so it's inert if purchase_stock is absent).
     New "Procurement & Delivery" form page, a Delivery-Overdue ribbon, list
     columns + "In Production"/"Delivery Overdue" filters and a Delivery-Status
     group-by. Revision history already existed (cs.submittal.revision) and is
     unchanged. cs_controls now depends on `purchase` (already installed);
     bumped to 1.0.0.
     NOTE (P1.2): the RFI Analysis graph already defaults to a bar grouped by
     State with Count as the measure (arch has a single state dimension and no
     numeric measure, so Count is the default). Verified via read_group:
     Closed 57 / Open 7 / Sent 1.
105. FEATURE (P1.3): Transmittal now has a controlled PDF (Letter of
     Transmittal — items table, remarks, attached-files list, received-by
     sign-off) at cs_field.report_cs_transmittal, wired as the auto-attached
     PDF on the transmittal email (_cs_mail_report). Added Email Transmittal +
     Resend buttons to the transmittal form (via cs_mail inherited view), and a
     transmittal-aware recipient list (To + CC). cs_field 0.10.0, cs_mail
     0.5.0. Shop Drawing and Closeout registers already have full state flows
     (draft->received->under review->approved/rejected; required->received->
     reviewed->accepted) and are exercised as-is (internal registers, no
     external PDF needed).
106. FEATURE (P1.5): Project Budget now tracks real purchase commitment.
     amount_committed is redefined as the uninvoiced value of confirmed
     purchase-order lines allocated to the project's analytic account
     (ordered - billed, prorated by analytic %), giving a true
     budget -> commitment -> vendor bill -> actual -> forecast cost picture.
     Change-order exposure moved to its own amount_change_exposure field
     (shown on the budget form; optional column on the list). Actual still
     comes from negative analytic lines; forecast = actual + cost to complete.
     cs_commercial 0.10.0.
107. FEATURE (P2.1): Project Overview (the command centre) now shows open/total
     counts and a message/activity indicator. Added Total metrics for RFIs,
     Submittals and Change Orders on each card, and a per-project activity
     badge in the header (bell + count of scheduled activities on the project's
     construction records, turning red with an "N overdue" note when any are
     past due). New data helpers _activity_counts_by_project + total counts;
     small OWL template + SCSS additions. cs_dashboards 0.11.4.
108. FEATURE (P2.2): Consolidated project Communications feed. New Comms smart
     button on the project form (coordinator+) opens every message — chatter,
     emails and logged activities — across all of the project's construction
     records (RFIs, COs, submittals, daily logs, FLHAs, incidents, NCRs, field
     memos, meetings, look-aheads, delays), its tasks and the project itself,
     in one mail.message list. Built from a computed OR-domain over
     (model, res_id); cs_message_count drives the button badge. cs_hub 0.4.0.
110. BRANDING: enlarged the Construction app icon. The design icon had ~58%
     empty margin, so it looked small next to other apps. Cropped to the
     artwork and re-padded to ~80% fill at 512x512
     (cs_controls/static/description/icon.png); this drives the Settings/Apps
     icon (icon_image), the app-grid tile (web_icon_data, refreshed by the
     upgrade) and is the favicon source. Website favicon reissued from a
     tighter 78%-fill crop for small-size legibility. cs_controls 1.0.1.
     (Browsers cache app icons — hard refresh to see it.)
## UX cleanup — 2 August 2026

UX1. Dashboard (Overview) made actionable. The overdue-activities badge is now
     clickable and opens the project's scheduled activities (across its
     construction records) in a list; RFI/Submittal/CO metrics were already
     click-through. Each project card gained a quick-action row: New RFI,
     New CO, Daily Log, Safety Report and Upload Drawing — each pre-scoped to
     the project. New _new_action / _activity_action helpers + a mail.activity
     list view. cs_dashboards 0.11.5.
UX2. Project form cleaned. Removed the duplicate "Schedule" tab (cs_schedule no
     longer adds its own page; cs_hub's Schedule tab now carries Baseline/
     Forecast + Look-Aheads + Delays). The Sales Order stat button stays
     auto-hidden (sale_order_count is 0 on construction projects; an explicit
     xpath was dropped because that button is injected by sale_project's view
     after ours and can't be targeted safely). Renamed "Name of the Tasks" to
     "Task Label". Added a
     "Holdback Applies" toggle on the project; the Holdback % only shows and
     applies when it's on (onchange clears % when off, seeds a default when on).
     cs_schedule 0.5.5, cs_hub 0.4.1, cs_commercial 0.10.1.
UX3. RFI actions simplified. The header now shows one clear primary per state —
     Send RFI (Draft/Open) / Record Response (Sent) / Distribute Response
     (Answered) / Close RFI (Distributed). "Send RFI" both records the send and
     opens the email, so the separate confusing "Email RFI" button is gone.
     Resend, Send Reminder, Cancel and Reopen moved to the form's Actions (cog)
     menu as bound server actions. action_send now accepts Draft (the interim
     Open button is removed). cs_controls 1.0.2, cs_mail 0.5.1.

## Safety QR straight-to-form — 2 August 2026 (cs_hse_templates 0.2.4)

ST13. A scanned project QR now drops the worker straight into the form. The
     /safety/new controller: if the QR carries a project it creates the report
     and opens it immediately — the project picker is never shown. The picker
     only appears for a project-less QR, and it now lists real active projects
     only (excludes template projects). An out-of-date QR (project deleted)
     shows a clear message instead of a random project list. Added a
     print-ready, project-specific QR poster (/safety/qr_poster) plus a
     "Print Poster" button on the QR wizard, so what gets posted on site always
     carries its project. Wizard already requires a project.

## Safety templates hardening — 1 August 2026 (cs_hse_templates 0.2.0)

ST1. FIX (production blocker): cs.safety.template now inherits mail.thread +
     mail.activity.mixin, so its form chatter works and the
     _get_thread_with_access errors are gone (the form had <chatter/> but the
     model wasn't a thread).
ST3. SECURITY: a Locked (or Issued) safety report is now fully read-only
     server-side — not just in the view. Added create/write/unlink guards on
     answer lines, photos and signatures, plus the existing header-field guard,
     all raising unless the report is reopened. action_lock and
     action_reset_to_draft (Reopen) both post to the chatter, so lock/reopen
     are logged.
ST4. FEATURE: yes/no questions carry a configurable Passing Answer
     (yesno_pass, default Yes). Scoring no longer assumes Yes=pass — is_fail
     and fail_count use each question's expected result (e.g. "Any uncontrolled
     hazard?" passes on No). Snapshotted onto each answer at report creation.
ST5. FIX: the Safety Reports action no longer defaults to hiding locked
     reports (removed search_default_open); issued/locked reports stay visible
     and searchable, with the "Not Locked" filter still available.
ST6. CONTENT: seeded five published starter templates — Toolbox Talk, Field
     Inspection, Site Inspection, Hazard Assessment, Equipment Inspection —
     each using the configurable yes/no scoring where appropriate.
ST12. SECURITY (release blocker): full locked-report immutability.
     cs.safety.report.write() now (a) freezes all content on an issued/locked
     report against any RPC/import/API write, and (b) refuses to move a report
     out of 'locked' via a raw state write — closing the hole where
     write({'state':'draft'}) could silently unlock without audit. unlink() on
     an issued/locked report is blocked. The ONLY way to change a locked report
     is the new Reopen action, which (1) checks permission server-side (safety
     lead / admin, AccessError otherwise), (2) opens a wizard requiring a
     Reason, and (3) records the user, date and reason in the chatter, then
     writes state=draft under a private cs_reopen context flag that the guard
     recognises. Form view: date/title/location/prepared-by/supervisor plus
     answers and signatures are all read-only when state=='locked'. New tests
     cover admin and field-user roles: content/unlink/state-bypass all blocked
     for both, reason mandatory, and only safety/admin may reopen.
     cs_hse_templates 0.2.3.
ST9. QR: the QR Poster wizard now requires a project, so generated links are
     always /safety/new?template_id=X&project_id=Y. The /safety/new route no
     longer errors when a project is missing/invalid — it renders a
     project-selection page (safety_pick_project) so the user picks one before
     the report is created. HttpCase route tests (valid + missing project).
     cs_hse_templates 0.2.2.
ST10. SECURITY: Reopen (action_reset_to_draft) now enforces its permission
     server-side — only cs_core.group_cs_safety / group_cs_admin may reopen an
     issued/locked report (AccessError otherwise), not just via the button's
     groups; every reopen is logged to the chatter. The locked read-only
     write() guards from ST3 remain. Test: a coordinator is refused, a safety
     lead succeeds.
ST11. CONTENT: corrected version of the Daily Site Safety Inspection published
     via the version workflow — "Any new hazards identified today?" scores
     No = pass, Yes = fail, N/A = neutral (yesno_pass = no); seed fixed for
     fresh installs too. Test asserts fail_count / overall_result recalc.
ST8. RELIABILITY: seed templates now publish automatically. Added a
     post_init_hook (fresh install) and a 19.0.0.2.1 migration (upgrades) that
     publish any seeded starter template still left as draft — the XML
     same-id publish record only fires on a fresh install, so upgrades that add
     new seeds previously landed them as draft. cs_hse_templates 0.2.1.
ST2/7. TESTS: added tests/test_safety.py (11 cases) covering template opening
     (chatter), QR generation + route, configurable yes/no scoring, fail_count,
     required signatures, locking read-only enforcement, reopen + logging, PDF
     rendering, distribution and resend, and that the seeded templates are
     published.

111. FIX: the Construction section in the Settings left sidebar had no icon.
     Its <app> block used name="cs_construction" (not a real module), so Odoo
     could not resolve an icon. Added an explicit
     logo="/cs_controls/static/description/icon.png" on the block. Applied to
     the live view arch immediately and staged in code. cs_core 0.6.1.

109. CLEANUP (P2.3): removed 57 stale "Overdue RFI response" to-do activities
     that sat on already closed/cancelled RFIs (leftovers from the disabled
     reminder engine). Done via authenticated session with the owner's
     explicit approval. The 17 activities on still-open RFIs were left in
     place per that decision. No RFI records were changed.
