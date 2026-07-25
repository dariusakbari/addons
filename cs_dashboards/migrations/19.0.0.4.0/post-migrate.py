"""Re-assert the Project > Overview -> Construction Dashboard merge.

post_init_hook runs only on first install, so this migration re-applies the
menu repoint on every version bump. Uses the (cr, version) signature, which
this Odoo build requires; env is built from the cursor.
"""
from odoo import SUPERUSER_ID, api
from odoo.addons.cs_dashboards import _cs_apply_overview_merge


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _cs_apply_overview_merge(env)
