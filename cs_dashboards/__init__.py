from . import models


def _cs_apply_overview_merge(env):
    """Point the Project app's Overview menu at the Construction Dashboard.

    Idempotent and defensive: silently no-ops if either the action or the
    native Overview menu is absent (e.g. after a core upgrade that renames or
    rebuilds project menus). Called from both the install hook and the
    version migration so the merge self-heals on every upgrade of this module.
    """
    action = env.ref("cs_dashboards.action_construction_dashboard",
                     raise_if_not_found=False)
    if not action:
        return
    target = "ir.actions.client,%s" % action.id
    overview = env["ir.ui.menu"].search([
        ("name", "=", "Overview"),
        ("parent_id.name", "=", "Project"),
    ], limit=1)
    if overview and overview.action != target:
        overview.action = target


def _cs_dashboards_post_init(env):
    _cs_apply_overview_merge(env)
