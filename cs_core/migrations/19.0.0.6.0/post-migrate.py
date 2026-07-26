"""Remove the retired Executive (Read-Only) construction role.

Unassign it from any users, then delete the group and its xmlid. Safe if
already absent.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    grp = env.ref("cs_core.group_cs_executive", raise_if_not_found=False)
    if grp:
        grp.unlink()
