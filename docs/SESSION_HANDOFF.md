# Session Handoff — end of 24 July 2026

## Where things stand
All work is committed to github.com/dariusakbari/addons (main) and deployed
to production odoo.greentechelectric.ca via the OSM panel
(darius-osm.myodoo.live). Full history: PRODUCTION_CHANGELOG.md.

Deployed modules: gte_core 0.2.0, gte_controls 0.7.0, gte_documents 0.1.0,
gte_field 0.5.0, gte_hse 0.3.0, gte_commercial 0.2.0, gte_mail 0.1.0,
gte_hub 0.2.0, gte_migration 0.1.0.

Today, in order: discovery report → security hardening → dedicated
RFI/CO/Submittal workflows + PDFs + queues → field & safety suite (14
record classes) → 189 legacy records migrated & reconciled → old
Project-tag menus + HSE app retired → smart buttons + SmartBuild-style
project hub → documents revision control → commercial scaffold →
constraint integrity fix → role-correct field workflow (Field Issues →
PM releases RFI; field crews see only Field & Safety + Drawings) → app
icon → 29/29 regression → upgrade-spec pre-plan (docs/UPGRADE_PLAN.md)
→ **upgrade-spec Phase 1 DONE** (validation gates, reason wizard,
unlink guards, {code}-TYPE-### numbering, 210 records renumbered).

## Next session: upgrade-spec Phase 2 or 3
- Phase 2 (email) — BLOCKED on D2: mail provider, credential path, test
  mailbox. Owner to provide.
- Phase 3 (drawing & document control) — ready to start, no inputs needed.
  (Register default-view fix, bulk upload, auto-foldering, watermarks,
  issue packages, transmittal-from-documents with frozen revisions.)
- Open decisions: D2 mail; D4 CO approval limit value (param
  gte.co_approval_limit currently 0 = disabled), holdback %, rate table,
  billing flow, cost codes; D5 weather API; D6/D7 native dashboards/XLSX.

## Owner to-dos (unchanged)
- Push any pending commit ("git status" in the repo, then Push origin).
- TEST Field Employee user (field.test@…): set password via Change
  Password, then run the phone test script (employee view + mobile forms).
- SmartBuild export (vendor ticket) — critical path for legacy attachments.
- One-time restore test of an OSM backup into a throwaway instance.
- Assign Mujtaba's construction role notes: he has Construction
  Administrator already.
- TEST-prefixed records on TEMPLATE project: archive after review.

## Operational notes
- Deploy loop: commit → owner pushes → OSM Addons pull → (Python changed?
  restart) → upgrade module(s) via Apps → test → changelog entry.
- If backend pages go blank after an upgrade: delete ir.attachment
  records with url like '/web/assets/%', restart, hard-reload
  (recurring Odoo 19 asset-corruption quirk; documented in changelog).
- Pre-phase backup before every deploy (latest: 20260724_231612).
