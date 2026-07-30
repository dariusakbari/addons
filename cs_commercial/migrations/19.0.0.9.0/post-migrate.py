from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Revert any Payment Application still marked 'invoiced' whose linked
    invoice has been cancelled (data left inconsistent before the account.move
    sync was in place)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    PA = env["cs.payment.application"].sudo()
    bad = PA.search([("state", "=", "invoiced"),
                     ("invoice_id.state", "=", "cancel")])
    if bad:
        bad.write({"state": "approved", "invoice_id": False})
