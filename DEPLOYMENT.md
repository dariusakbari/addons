# GTE Addons v0.1 — Deployment & Rollback

## Contents
- **gte_core** — legacy/migration mixin, per-project sequences, 8 security groups
  (Field, Foreman, Estimator, Safety, Coordinator, PM, Accounting, Construction Admin).
- **gte_controls** — `gte.rfi`, `gte.change.order` (+ cost lines), `gte.submittal`
  (+ immutable revisions), `gte.submittal.spec`; full state machines, chatter/activity
  tracking, membership record rules, overdue-RFI cron, views, menus, automated tests.
- **gte_migration** — idempotent wizard converting tagged tasks (RFI / Change Order /
  Submittal) + the `x_submittal_spec` library into the dedicated models.
  Dry-run by default. Originals never modified/archived/deleted.

## Install (self-hosted)
1. **Backup first** (DB + filestore). You have yesterday's; take a fresh one —
   production received config changes today (see PRODUCTION_CHANGELOG.md).
2. Copy the three folders into your addons path; ensure the path is in
   `addons_path` in odoo.conf.
3. Restart Odoo, then: `odoo-bin -d <db> -u base --stop-after-init` is NOT needed;
   just install from Apps (update Apps List) or:
   `odoo-bin -d <db> -i gte_core,gte_controls,gte_migration --stop-after-init`
4. Run tests before trusting it:
   `odoo-bin -d <testdb> -i gte_core,gte_controls,gte_migration --test-enable --test-tags gte --stop-after-init`
   (use a copy of production as testdb — this is the closest thing to staging you have chosen to run.)
5. Assign users to the new groups (Settings → Users → Green Tech Construction).
6. Migration: Construction → Configuration → Legacy Migration. Run once with
   **Dry run** checked, review the counts, then run with dry-run off.

## Rollback
- Modules: uninstall `gte_migration`, `gte_controls`, `gte_core` (in that order).
  Uninstalling removes gte.* records/models; original tasks are intact because the
  migration never touches them.
- Full rollback: restore the pre-install backup (DB + filestore).

## Known limitations (v0.1 — next increments)
- No QWeb PDF reports, kanban views, or mail templates yet (Phase 6).
- gte_documents / gte_field / gte_hse / gte_dashboards modules not yet written;
  Studio x_hse_* / x_ops_* models remain in place untouched.
- SmartBuild enrichment importer pending the vendor export (Blocker B3).
- Field-level rate/markup restrictions minimal; tighten with the approved roster (B5).
- 2FA and admin demotion deliberately not changed (B5 + recovery procedure).
