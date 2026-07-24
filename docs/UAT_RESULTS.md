# UAT / Regression Results — 24 July 2026

Environment: production odoo.greentechelectric.ca (Odoo 19.0+e), executed
via authenticated ORM session. 29 checks, 29 PASS, 0 FAIL.

## Modules & data integrity
- PASS all 8 gte modules installed
- PASS RFIs 66 (64 migrated + 2 test) · COs 85 · Submittals 42 · Specs 98
- PASS 189 migration exceptions flagged; 189 original tagged tasks intact
- PASS every migrated record carries a legacy source ID

## Workflows
- PASS fresh RFI full lifecycle after all upgrades (draft→…→closed)
- PASS closed RFI cannot transition again
- (Earlier same-day production tests: CO pricing/approval/billing cycle;
  submittal revise-and-resubmit with immutable revisions; FLHA/TBT/DSL
  finalize gates + supervisor activities; INC/EQI/WP/RSK gates and
  escalations; NCR/GI/ATT/VIS/TR/SD/GP gates — see PRODUCTION_CHANGELOG.)

## Reports
- PASS all 6 PDF reports render (RFI, CO, Submittal, FLHA, TBT, DSL)

## Automation
- PASS 3 GTE crons active (overdue RFIs, permit expiry, cert expiry)

## Integrity constraints
- PASS duplicate labour rate / budget / attendance sheet all rejected

## Security
- PASS 8 construction groups under Green Tech Construction privilege
- PASS membership record rules present across models
- PASS zero labour-rate ACLs for field/foreman groups
- PASS all active projects on follower-based visibility
- PASS old Studio menus hidden (8), Construction root visible

## Documents
- PASS every superseded document links its superseding revision

## Cross-links
- PASS Bayview smart-button counts = 50 RFIs / 70 COs / 24 submittals

## Known not-yet-tested (owner-gated)
Mail delivery/replies/bounces (no server), portal user isolation (no
portal user), phone-device rendering, backup RESTORE, multi-user role
walkthrough with non-admin accounts, SmartBuild-export reconciliation.
