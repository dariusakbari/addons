"""Re-assert the Project > Overview -> Construction Dashboard merge.

post_init_hook runs only on first install, so upgrades would otherwise lose
the menu repoint if a core `project` upgrade rebuilt its menus. This
post-migration re-applies it on every version bump of cs_dashboards.
"""
from odoo.addons.cs_dashboards import _cs_apply_overview_merge


def migrate(env, version):
    _cs_apply_overview_merge(env)
