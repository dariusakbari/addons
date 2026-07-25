"""Re-assert the Project > Overview -> Construction Dashboard merge."""
from odoo.addons.cs_dashboards import _cs_apply_overview_merge


def migrate(env, version):
    _cs_apply_overview_merge(env)
