# GTE Odoo — Administrator Guide (24 July 2026)

## Architecture
Eight custom add-ons deployed from github.com/dariusakbari/addons via the
OSM panel (darius-osm.myodoo.live): gte_core (mixins, sequences, groups),
gte_controls (RFI/CO/Submittal), gte_documents, gte_field, gte_hse,
gte_commercial, gte_mail, gte_migration. Standard Odoo extension patterns
only; no core patches; no Studio for new work.

## Deploy / update procedure
1. Commit + push to the addons repo (main).
2. OSM panel → instance → Addons → pull (download icon).
3. Python changed? OSM → Restart. XML/data only? restart optional.
4. Odoo → Apps (or RPC) → upgrade the changed module.
5. Verify; record in PRODUCTION_CHANGELOG.md.
Always create an OSM backup before installing/upgrading modules.

## Backup & recovery
- Nightly 2AM OSM backups, 7-day retention + manual "Create Backup".
- RESTORE TEST STILL PENDING: restore a backup into a scratch instance
  (OSM Clone) and open sample records/attachments. Do this before cutover
  sign-off, and after that quarterly.
- Rollback: restore backup via OSM, or uninstall modules in reverse
  dependency order (mail/commercial/documents/migration → field/hse →
  controls → core). Uninstalling removes that module's records.

## Users & roles
- Assign construction roles: Settings → Users → Green Tech Construction.
- Everything-access = Construction Administrator (both current users have it).
- TO DO before adding staff: create users with least privilege (Internal
  User + a construction role, NOT Settings admin); keep ONE break-glass
  admin with documented credentials; enable 2FA after that.
- New employees also need project membership (follower on their projects)
  or they will not see project records.

## Email (pending)
Configure outgoing/incoming servers in Settings → Technical when the
provider is chosen; templates in gte_mail activate automatically. Test
with a mail catcher before external sending; verify reply threading.

## Routine care
- Watch Construction → Overview queues for overdue items.
- Migration exceptions filter on RFIs/COs/Submittals = records awaiting
  SmartBuild-export enrichment. Do not clear flags manually.
- The 189 original tagged tasks stay until reconciliation sign-off, then
  archive (do not delete).
- Old Studio menus/models are hidden, not removed. Reverse: ir.ui.menu
  ids in PRODUCTION_CHANGELOG.md → active=true.
