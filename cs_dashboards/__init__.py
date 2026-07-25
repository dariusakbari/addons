from . import models


def _cs_dashboards_post_init(env):
    """Point the Project app's Overview menu at the Construction Dashboard."""
    action = env.ref("cs_dashboards.action_construction_dashboard",
                     raise_if_not_found=False)
    if not action:
        return
    overview = env["ir.ui.menu"].search([
        ("name", "=", "Overview"),
        ("parent_id.name", "=", "Project"),
    ], limit=1)
    if overview:
        overview.action = "ir.actions.client,%s" % action.id
