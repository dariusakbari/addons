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
