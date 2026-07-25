# Construction Suite — Test & Debug Report
Date: 25 July 2026. Scope: full platform, all user roles. Method: security
config verified from ACLs + record rules + group hierarchy (accurate for every
role without needing each user's password); functional behaviour exercised via
the ORM on the TEMPLATE project, with all test records removed afterward.

## Result summary

Platform is healthy. One real finding (the Executive Read-Only role is
mis-scoped); everything else passed. No crashes, no missing-ACL models, no
broken PDFs, and the confidential-data boundaries hold.

## Security — access by role (verified)

Role hierarchy (who inherits whom): Admin ⊃ Accounting + Project Manager +
Safety; Project Manager ⊃ Coordinator ⊃ Field; Foreman/Estimator/Safety/
Executive ⊃ Field; Accounting is standalone.

Confirmed correct:

- Change Orders, Project Budgets, Labour Rates and Payment Applications are
  **invisible to Field, Foreman, Estimator, Safety and Coordinator** (no ACL
  = no access). This matches the rule that field staff must not see
  change-order or cost values.
- RFIs: Field = read-only; Foreman and Coordinator can create/edit; Admin
  full; Portal read. Submittals: Field read, Coordinator create, Admin full.
- Labour Rates: Accounting/Admin write, Project Manager read-only, Field none
  (rates stay confidential).
- Worker Certifications: Safety and Project Manager manage, Field read.
- Payment Applications and Budgets: Project Manager / Accounting / Admin only.
- Escalation Rules: Admin manage, Project Manager read.
- Every construction business model has ACL rows — no model is accidentally
  inaccessible (which would otherwise throw access errors).

Record rules (row-level) verified on RFIs (representative of the pattern):

1. Internal users see RFIs on projects they belong to (project membership /
   visibility rule).
2. Managers (PM/Admin) see all.
3. Portal users see **only** RFIs explicitly shared with them
   (`cs_portal_partner_ids` contains their partner) — correct client
   isolation. Same three-rule pattern applies to Submittals and Transmittals.

## Finding — Executive Read-Only role is mis-scoped (latent)

`group_cs_executive` currently **implies Field Employee**, so a user in it
would (a) inherit Field's create/edit rights on daily logs, punch items,
incidents, FLHAs, etc. — i.e. it is *not* read-only — and (b) still have no
access to Change Orders, Budgets or Submittals, so it can't act as an
all-seeing executive view either. It is presently latent (no user is assigned
to it). To make it a true read-only overview it should not imply Field, and
should instead carry read-only ACLs plus permissive read record rules across
the construction models. Recommended fix if the role will be used; left as-is
otherwise to avoid an unneeded security change.

## Functional checks (as Admin, on TEMPLATE, cleaned up)

- Model instantiation: gate pass, site attendance, shop drawing, field issue
  and delay event created without error. Risk, Toolbox Talk, Punch Item and
  Visitor Log correctly **rejected** input missing their required fields —
  confirming the validation gates fire. No bad-field or compute crashes on any
  model.
- CO → Sale Order billing: verified end-to-end (approved CO produced a sale
  order line at the approved amount).
- Progress billing: two payment applications computed correct AIA math and
  generated a draft invoice net of holdback ($27,000 = $30,000 − $3,000).
- Payment Certificate PDF: renders (HTTP 200, application/pdf).
- Escalation engine: daily cron created 7 deduplicated activities on overdue
  RFIs; the three legacy crons are deactivated.
- QR codes: generate on permits and equipment (server has the `qrcode`
  library); shown on the forms.
- Per-project Overview dashboard: returns per-project KPIs and renders.

## Environment notes (not code issues)

- Odoo's built-in barcode renderer is unavailable on this server (missing
  `rlPyCairo`/pycairo); QR is generated via the `qrcode` library instead, so
  this does not affect the platform. `wkhtmltopdf` PDF rendering works.
- Email crons remain inert until the SMTP go-live after the domain move.
