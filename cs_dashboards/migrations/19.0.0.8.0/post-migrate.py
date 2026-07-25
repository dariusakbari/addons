"""Re-assert the Project > Overview -> Construction Dashboard merge."""
from odoo import SUPERUSER_ID, api
from odoo.addons.cs_dashboards import _cs_apply_overview_merge


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _cs_apply_overview_merge(env)
