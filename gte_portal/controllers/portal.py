from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class GteConstructionPortal(CustomerPortal):

    def _gte_counts(self, partner):
        return {
            "rfi": request.env["gte.rfi"].search_count(
                [("gte_portal_partner_ids", "in", partner.ids)]),
            "submittal": request.env["gte.submittal"].search_count(
                [("gte_portal_partner_ids", "in", partner.ids)]),
            "transmittal": request.env["gte.transmittal"].search_count(
                [("gte_portal_partner_ids", "in", partner.ids)]),
        }

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        c = self._gte_counts(partner)
        if "gte_rfi_count" in counters:
            values["gte_rfi_count"] = c["rfi"]
        if "gte_submittal_count" in counters:
            values["gte_submittal_count"] = c["submittal"]
        if "gte_transmittal_count" in counters:
            values["gte_transmittal_count"] = c["transmittal"]
        return values

    @http.route(["/my/construction/rfis"], type="http", auth="user",
                website=True)
    def portal_rfis(self, **kw):
        rfis = request.env["gte.rfi"].search(
            [("gte_portal_partner_ids", "in", request.env.user.partner_id.ids)],
            order="name desc")
        return request.render("gte_portal.portal_rfi_list", {
            "rfis": rfis, "page_name": "gte_rfi"})

    @http.route(["/my/construction/rfi/<int:rfi_id>"], type="http",
                auth="user", website=True)
    def portal_rfi_detail(self, rfi_id, **kw):
        rfi = request.env["gte.rfi"].browse(rfi_id)
        if not rfi.exists() or request.env.user.partner_id not in \
                rfi.gte_portal_partner_ids:
            return request.redirect("/my")
        return request.render("gte_portal.portal_rfi_detail", {
            "rfi": rfi, "page_name": "gte_rfi"})

    @http.route(["/my/construction/rfi/<int:rfi_id>/respond"], type="http",
                auth="user", website=True, methods=["POST"], csrf=True)
    def portal_rfi_respond(self, rfi_id, response="", **kw):
        rfi = request.env["gte.rfi"].browse(rfi_id)
        partner = request.env.user.partner_id
        if rfi.exists() and partner in rfi.gte_portal_partner_ids \
                and (response or "").strip():
            rfi._portal_log_response(partner, response)
        return request.redirect("/my/construction/rfi/%s" % rfi_id)

    @http.route(["/my/construction/submittals"], type="http", auth="user",
                website=True)
    def portal_submittals(self, **kw):
        subs = request.env["gte.submittal"].search(
            [("gte_portal_partner_ids", "in", request.env.user.partner_id.ids)],
            order="name desc")
        return request.render("gte_portal.portal_submittal_list", {
            "submittals": subs, "page_name": "gte_submittal"})

    @http.route(["/my/construction/transmittals"], type="http", auth="user",
                website=True)
    def portal_transmittals(self, **kw):
        trs = request.env["gte.transmittal"].search(
            [("gte_portal_partner_ids", "in", request.env.user.partner_id.ids)],
            order="name desc")
        return request.render("gte_portal.portal_transmittal_list", {
            "transmittals": trs, "page_name": "gte_transmittal"})
