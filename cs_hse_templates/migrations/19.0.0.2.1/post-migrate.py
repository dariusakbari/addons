from odoo import api, SUPERUSER_ID

from odoo.addons.cs_hse_templates.hooks import _publish_seed_templates


def migrate(cr, version):
    """Publish any seeded starter templates that are still draft after an
    upgrade (the XML publish record is skipped on upgrades because of
    noupdate)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    _publish_seed_templates(env)
