from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GtePortalShareMixin(models.AbstractModel):
    """Adds portal sharing + response logging to a construction record.
    Only records explicitly shared (portal partner added as follower AND
    listed in cs_portal_partner_ids) are visible to external users."""

    _name = "cs.portal.share.mixin"
    _description = "Construction Portal Share Mixin"

    cs_portal_response = fields.Html(
        string="Portal Response", readonly=True, copy=False,
        help="Latest response captured from the portal.")
    cs_portal_responded_by_id = fields.Many2one(
        "res.partner", string="Portal Responder", readonly=True, copy=False)
    cs_portal_responded_date = fields.Datetime(readonly=True, copy=False)

    def action_share_portal(self):
        """Grant portal access to the selected partners: subscribe them as
        followers and upgrade them to portal users is out of scope here —
        access is via record rules + the share link."""
        for rec in self:
            if rec.cs_portal_partner_ids:
                rec.message_subscribe(
                    partner_ids=rec.cs_portal_partner_ids.ids)
                rec.message_post(
                    body="Shared to portal: %s" % ", ".join(
                        rec.cs_portal_partner_ids.mapped("name")))

    def _portal_log_response(self, partner, body):
        self.ensure_one()
        self.sudo().write({
            "cs_portal_response": body,
            "cs_portal_responded_by_id": partner.id,
            "cs_portal_responded_date": fields.Datetime.now(),
        })
        self.sudo().message_post(
            body="Portal response from %s: %s" % (partner.name, body),
            author_id=partner.id)


class GteRfi(models.Model):
    _name = "cs.rfi"
    _inherit = ["cs.rfi", "cs.portal.share.mixin"]

    cs_portal_partner_ids = fields.Many2many(
        "res.partner", "cs_portal_share_rfi_rel",
        string="Shared With (Portal)")


class GteSubmittal(models.Model):
    _name = "cs.submittal"
    _inherit = ["cs.submittal", "cs.portal.share.mixin"]

    cs_portal_partner_ids = fields.Many2many(
        "res.partner", "cs_portal_share_submittal_rel",
        string="Shared With (Portal)")


class GteTransmittal(models.Model):
    _name = "cs.transmittal"
    _inherit = ["cs.transmittal", "cs.portal.share.mixin"]

    cs_portal_partner_ids = fields.Many2many(
        "res.partner", "cs_portal_share_transmittal_rel",
        string="Shared With (Portal)")
