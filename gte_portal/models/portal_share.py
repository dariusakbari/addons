from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GtePortalShareMixin(models.AbstractModel):
    """Adds portal sharing + response logging to a construction record.
    Only records explicitly shared (portal partner added as follower AND
    listed in gte_portal_partner_ids) are visible to external users."""

    _name = "gte.portal.share.mixin"
    _description = "GTE Portal Share Mixin"

    gte_portal_response = fields.Html(
        string="Portal Response", readonly=True, copy=False,
        help="Latest response captured from the portal.")
    gte_portal_responded_by_id = fields.Many2one(
        "res.partner", string="Portal Responder", readonly=True, copy=False)
    gte_portal_responded_date = fields.Datetime(readonly=True, copy=False)

    def action_share_portal(self):
        """Grant portal access to the selected partners: subscribe them as
        followers and upgrade them to portal users is out of scope here —
        access is via record rules + the share link."""
        for rec in self:
            if rec.gte_portal_partner_ids:
                rec.message_subscribe(
                    partner_ids=rec.gte_portal_partner_ids.ids)
                rec.message_post(
                    body="Shared to portal: %s" % ", ".join(
                        rec.gte_portal_partner_ids.mapped("name")))

    def _portal_log_response(self, partner, body):
        self.ensure_one()
        self.sudo().write({
            "gte_portal_response": body,
            "gte_portal_responded_by_id": partner.id,
            "gte_portal_responded_date": fields.Datetime.now(),
        })
        self.sudo().message_post(
            body="Portal response from %s: %s" % (partner.name, body),
            author_id=partner.id)


class GteRfi(models.Model):
    _name = "gte.rfi"
    _inherit = ["gte.rfi", "gte.portal.share.mixin"]

    gte_portal_partner_ids = fields.Many2many(
        "res.partner", "gte_portal_share_rfi_rel",
        string="Shared With (Portal)")


class GteSubmittal(models.Model):
    _name = "gte.submittal"
    _inherit = ["gte.submittal", "gte.portal.share.mixin"]

    gte_portal_partner_ids = fields.Many2many(
        "res.partner", "gte_portal_share_submittal_rel",
        string="Shared With (Portal)")


class GteTransmittal(models.Model):
    _name = "gte.transmittal"
    _inherit = ["gte.transmittal", "gte.portal.share.mixin"]

    gte_portal_partner_ids = fields.Many2many(
        "res.partner", "gte_portal_share_transmittal_rel",
        string="Shared With (Portal)")
