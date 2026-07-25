# Surviving Odoo Core Upgrades — Safety Audit & Checklist

Date: 25 July 2026. Scope: the `cs_*` module suite (Construction Suite) on
Odoo 19 Enterprise, hosted via the OSM panel. This document covers what
happens to our custom modules when **Odoo itself** is upgraded (a patch
within 19.0, or eventually a major jump such as 19 → 20), and the steps that
keep our work intact.

## Summary

The suite is in good shape for upgrades. A full audit of all twelve modules
found no raw SQL, no hard-coded database IDs, no private/internal Odoo API
imports, and clean manifests with explicit dependencies and proper version
strings. The only real exposure is the ordinary one that every serious Odoo
customization carries: we inherit a handful of **core views**, so a major
version that renames those views or their fields would require a small fix.
One data-level customization — pointing the Project app's *Overview* menu at
our dashboard — was previously applied by a one-off write and is now made
**self-healing** through a migration script so upgrades cannot silently
revert it.

## What was audited and found safe

Data access. No module uses `cr.execute`, `self._cr`, or direct SQL. Every
read and write goes through the ORM, so schema changes handled by Odoo's own
migration are picked up automatically.

Record references. No code calls `browse(<number>)` with a literal ID and no
model compares against a hard-coded ID. All cross-record links use XML IDs
(`env.ref(...)`) or stored relations, which Odoo remaps on upgrade.

API surface. The only import from another addon is the standard, public
`from odoo.addons.portal.controllers.portal import CustomerPortal` — the
documented way to extend the portal. No imports reach into private modules,
`models/` internals, or undocumented helpers.

Model inheritance. Every `_inherit` targets a stable public model:
`project.project`, `project.task`, `documents.document`,
`res.config.settings`, `mail.thread`, `mail.activity.mixin`, `portal`,
`sale`, `account`, or our own `cs.*` models. Nothing extends a private or
experimental model.

Manifests. All twelve modules carry a `19.0.x.y.z` version string, an
explicit `depends` list, a license, and `installable: True`. Dependencies
form a clean tree rooted at `cs_core` → `cs_controls`, so Odoo installs and
upgrades them in the correct order.

Constraints. All uniqueness rules use `models.Constraint` (the Odoo 19 API),
not the silently-ignored `_sql_constraints`, so they survive upgrades intact.

## The one real risk: inherited core views

Eight of our view files extend core Project views by XML ID —
`project.edit_project` (project form) and `project.view_task_form2` (task
form) — plus `base.res_config_settings_view_form`. The xpath selectors we use
are structural and robust (`//header`, `//notebook`, `//sheet`,
`//div[@name='button_box']`), which tolerate most layout changes. The failure
mode is narrow but real: if a **major** Odoo upgrade renames one of those
view XML IDs or removes a field we anchor to (for example `tag_ids` on the
project form), the inheriting view will fail to load and that module will
error on upgrade.

This is inherent to extending core views and is the expected, correct way to
build. The mitigation is procedural, not structural: after any major-version
upgrade, load each module and fix any xpath that no longer resolves. Patch
releases within 19.0 do not carry this risk.

## The Overview-menu merge, now self-healing

The Project app's *Overview* menu was repointed to the Construction Dashboard
client action. That native menu has no XML ID (Odoo builds it at runtime), so
it cannot be overridden declaratively. It was originally set by a direct
write, which an upgrade could undo. This is now hardened:

- The repoint logic lives in one idempotent helper,
  `_cs_apply_overview_merge(env)` in `cs_dashboards/__init__.py`. It no-ops
  safely if the action or the menu is missing.
- It runs on install via the `post_init_hook`, **and** on every version bump
  via `cs_dashboards/migrations/19.0.0.4.0/post-migrate.py`. Because
  `post_init_hook` only fires on first install, the migration is what keeps
  the merge alive across upgrades.

Practical consequence: as long as `cs_dashboards` is upgraded after any core
upgrade (see checklist), the Overview merge re-applies itself automatically.

## Pre-upgrade checklist

1. Take a full OSM backup (database + filestore) and confirm it downloaded.
2. Note the current Odoo build/version and the current versions of all
   `cs_*` modules (from Apps, or `docs/` change log).
3. If the upgrade is a **major** version (e.g. 19 → 20), do it against a
   clone first, not production — the OSM panel's Clone button creates one.
   Patch upgrades within 19.0 can proceed on production after the backup.

## Post-upgrade checklist

1. Restart the instance, then open Apps and **Upgrade** the `cs_*` modules
   (upgrading `cs_dashboards` and `cs_controls` pulls the rest via
   dependencies). This re-runs migrations, including the Overview re-merge.
2. Clear the web asset bundles if the client looks stale: delete
   `ir.attachment` records whose URL starts with `/web/assets/`, then hard
   reload. (A stale service worker can also cache old assets — clearing site
   data or a logout/login resolves it.)
3. Smoke-test: open Construction → Overview (dashboard renders 11 KPIs), open
   an RFI, a Change Order, a Submittal, a Daily Log, and the Projects kanban
   (project-type tags visible). Confirm PDFs still print.
4. If a module fails to load after a **major** upgrade, the cause is almost
   always an inherited core view whose anchor moved — open the module's view
   file and repair the xpath. Nothing else in the suite depends on core
   internals.

## Note on the "blank page" symptom

A blank content area with the navbar still present is usually **not** a code
problem. It is most often a stale web-asset bundle or service-worker cache
(fixed by step 2 above), or — when viewing through automation/background
tabs — the browser pausing rendering in a hidden tab. Verified healthy signs:
assets return HTTP 200, `get_kpis` returns data, and the action loads without
console errors. In those cases a clean, focused reload renders normally.
