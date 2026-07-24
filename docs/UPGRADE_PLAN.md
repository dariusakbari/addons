# Construction App — Functional Upgrade Plan (pre-implementation)
Response to the Odoo 19 Functional Upgrade Specification. No code written yet.
Date: 24 July 2026. Author basis: full audit of the gte_* module suite.

## 1. Audit of the existing module structure

Nine installable Odoo 19 modules, version-controlled at
github.com/dariusakbari/addons, deployed via OSM panel. 83 source files,
~2,250 lines of model code. No Studio dependencies in new work; legacy
Studio models (x_hse_*, x_ops_*) remain in DB, menus hidden, 3 records.

| Module | Ver | Models | Notes |
|---|---|---|---|
| gte_core | 0.1 | gte.legacy.mixin | Sequence engine, 8 security groups (privilege "Green Tech Construction") |
| gte_controls | 0.6 | gte.rfi, gte.change.order(+line), gte.submittal(+revision), gte.submittal.spec | State machines, PDFs, Overview queues, project/task smart buttons, role-restricted menus |
| gte_documents | 0.1 | extends documents.document (+revision wizard) | Metadata, supersede workflow, register view |
| gte_field | 0.5 | gte.daily.log(+labour), gte.field.issue, gte.ncr, gte.inspection(+line), gte.site.attendance(+line), gte.visitor.log, gte.transmittal(+line), gte.shop.drawing, gte.gate.pass | Field Issues → PM releases RFI workflow live |
| gte_hse | 0.3 | gte.flha(+hazard+signoff), gte.toolbox.talk(+attendee), gte.incident, gte.equipment.inspection, gte.work.permit, gte.risk | Validation gates, escalations, signatures |
| gte_commercial | 0.2 | gte.project.budget(+line), gte.labour.rate, gte.worker.cert | Budget vs committed vs actual scaffold |
| gte_mail | 0.1 | mail-action mixin | 4 templates + Email buttons; inert (no mail server) |
| gte_hub | 0.2 | extends project.project | SmartBuild-style per-project tabs |
| gte_migration | 0.1 | migration wizard | Idempotent; excluded from this scope per spec |

Infrastructure: netcup VPS, OSM panel (backups nightly + manual, Clone
button available = staging path). All uniqueness via models.Constraint
(Odoo 19 API). Existing tests: gte_controls (4), gte_migration (2) — never
executed as a suite (no test runner used yet; production-tested manually).

## 2. Existing features that can be reused (per priority)

P1 Email: gte_mail templates/buttons + all PDFs → reuse; add reminder/
   resend/distribute sends, bounce surfacing, alias routing, diagnostics.
P2 Validation: every model already has action-gated transitions; RFI/CO/
   SUB gates cover ~60% of the required rules → extend, don't rebuild.
   Chatter tracking already on all key fields. Per-project sequences exist.
P3 Documents: gte_documents metadata + supersede wizard is the foundation;
   register action exists (menu default-view bug to fix).
P4 Missing workflows: Field Issue model ≈ Field Memo (rename/extend);
   Inspection model exists → deficiency creation hook; NCR exists.
   New: punch-list item, meeting minutes, closeout register.
P5 Commercial: budget model + CO cost lines + analytic accounts on all 4
   projects + labour-rate model (needs effective dates/OT) → extend;
   T&M ticket is new; SO/invoice generation from CO is new glue.
P6 Scheduling: native Project/Planning installed; nothing custom yet.
P7 Mobile: responsive views + signature widgets + photo m2m exist;
   camera/captions/QR/weather are additive.
P8 Reporting: 6 QWeb PDFs + 8 Overview queues reusable; dashboards new
   (Odoo spreadsheet dashboards or owl client action — decision D6).
P9 Roles: 8 of 10 groups exist with record rules + rate lockout; add
   Executive Read-Only + 2 portal groups + portal rules + tests.
P10 Automation: 3 crons (RFI overdue, permit expiry, cert expiry) →
   generalize into configurable escalation engine.

## 3. Changes required (models / views / security / integrations)

- gte_core: + res.config.settings (Construction Settings: numbering
  format, thresholds, reminder timings, default coordinators/distribution,
  report branding, required-field toggles); numbering helper rewrite to
  format "{project_code}-RFI-{seq}"; legacy number preserved in
  legacy_source_id (already separate). Override framework (reason wizard +
  audit post) as a core mixin.
- gte_controls: extended gates per P2 (incl. responder/response date,
  approval reference, accounting-link checks, cancel/reopen reason wizard,
  unlink→archive guard, CO approval thresholds); email actions per P1;
  CO→SO/invoice generation (integration: sale, account).
- gte_documents: register default-view fix; bulk upload wizard; auto-
  foldering; superseded watermark on download; issue-package zip;
  create-transmittal-from-selection (freeze revision ids on transmittal
  line); search filters; documents.document security for portal.
- gte_field: field.issue → field memo upgrade (recipient, ack, cost/
  schedule impact, distribution); + gte.punch.item (+before/after photos,
  verification); inspection→deficiency hook; + gte.meeting(+agenda/action
  items); + gte.closeout.item; T&M ticket (+lines, signatures, PDF,
  convert-to-CO); daily log weather autofill (integration decision D5),
  saved crews (gte.crew model).
- gte_hse: QR tokens on equipment/forms; no structural change otherwise.
- gte_commercial: rate effective dates/OT/DT/project override; committed/
  actual pulls (purchase.order, account.move, timesheets — integrations);
  holdback + progress billing fields; forecast/cost-to-complete; cost codes
  (analytic plans or gte.cost.code).
- gte_mail: full P1 build (reminder crons, resend, bounce flag on records,
  alias per model via mail.alias, diagnostics settings panel).
- gte_hub: project dashboard tab/graphs; scheduling fields surface.
- NEW gte_portal: portal groups, restricted record rules, portal views/
  controllers for shared RFIs/submittals/transmittals, response logging.
- Security files touched: every module's CSV + rules (add executive
  read-only rows, portal rows, unlink removals) + automated permission
  tests for all 10 roles.
- Tests: new test packages per phase (workflow gates, sequences, calc,
  document links, permissions-per-role, email routing with mail catcher).

## 4. Phased implementation estimate (spec order)

Prereq (P0): none — owner decision 24 Jul 2026: NO staging environment.
Development continues directly in production under the day-one protocol:
mandatory OSM backup before every phase deploy, additive/reversible
changes, per-phase commits, test records confined to the TEMPLATE project
and cleaned after sign-off.
1. Validation/audit/numbering ....... 1.5 sessions  (largest test surface)
2. Email + external comms ........... 1–2 sessions  (blocked by D2 creds)
3. Drawing/document control ......... 1.5 sessions
4. Memos/deficiencies/closeout ...... 1.5 sessions
5. Roles/record rules/portal ........ 1.5 sessions  (portal is the bulk)
6. Commercial/job-cost .............. 2 sessions    (needs D3/D4 inputs)
7. Reporting/dashboards ............. 1.5 sessions
8. Scheduling/manpower .............. 1 session
9. Mobile/field ..................... 1 session     (device tests = owner)
10. Automation/admin settings ....... 1 session
"Session" = one working block like today. Each phase: pre-deploy OSM
backup → deploy → automated tests → role walkthrough (Admin/PM/Field) →
screenshots + report → separate commit → owner sign-off.

## 5. Technical limitations & decisions requiring approval

D1 RESOLVED: owner declined staging. Production-direct development with
   pre-phase OSM backups. NOTE: the spec's restore-proof requirement is
   still unmet — a restore test into a throwaway instance remains
   recommended at any convenient time (it does not create a staging
   obligation).
D2 Mail: provider + credentials path, a test consultant mailbox, and
   subdomain for aliases (e.g. rfi@…). P1 acceptance test impossible
   without it. First delivery tests will target owner-controlled inboxes.
D3 Numbering: adopt {project}-RFI-### (e.g. 0476-RFI-001). Existing ~190
   records were numbered per-project this week and not externally
   circulated → recommend one-time renumber for consistency. Approve.
D4 Commercial inputs: CO approval threshold values; holdback % (Ontario
   10%?); labour rate table with effective dates; billing flow (auto SO
   vs accounting-keyed); cost-code list.
D5 Weather autofill: needs an external weather API (outbound call + key
   in settings, not source). Approve provider or skip.
D6 Dashboards: Odoo 19 Enterprise Dashboards/Spreadsheet-based (fast,
   native) vs custom OWL dashboard (prettier, more code). Recommend
   native first.
D7 Excel outputs: native list XLSX export + PDF logs (no extra deps)
   vs OCA report_xlsx dependency for pixel-perfect workbooks.
   Recommend native first.
LIMITS: no true offline mode (draft-saving + Odoo mobile app only —
   stated, per spec); voice-to-text = device keyboard capability; photo
   annotation limited to caption + basic image tools; superseded-drawing
   watermarking applied on download/print path, previews get badge/label
   only; bounce capture depends on incoming mail (D2); portal users can
   never be fully tested until a real external party is enrolled.

Rules acknowledged: no hard-coded ids/rates, settings-driven values, no
credentials in source, no demo records in production, per-phase commits,
implementation report per phase. Legacy migration explicitly untouched.
