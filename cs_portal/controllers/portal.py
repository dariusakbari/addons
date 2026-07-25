from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class GteConstructionPortal(CustomerPortal):

    def _cs_counts(self, partner):
        return {
            "rfi": request.env["cs.rfi"].search_count(
                [("cs_portal_partner_ids", "in", partner.ids)]),
            "submittal": request.env["cs.submittal"].search_count(
                [("cs_portal_partner_ids", "in", partner.ids)]),
            "transmittal": request.env["cs.transmittal"].search_count(
                [("cs_portal_partner_ids", "in", partner.ids)]),
        }

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        c = self._cs_counts(partner)
        if "cs_rfi_count" in counters:
            values["cs_rfi_count"] = c["rfi"]
        if "cs_submittal_count" in counters:
            values["cs_submittal_count"] = c["submittal"]
        if "cs_transmittal_count" in counters:
            values["cs_transmittal_count"] = c["transmittal"]
        return values

    @http.route(["/my/construction/rfis"], type="http", auth="user",
                website=True)
    def portal_rfis(self, **kw):
        rfis = request.env["cs.rfi"].search(
            [("cs_portal_partner_ids", "in", request.env.user.partner_id.ids)],
            order="name desc")
        return request.render("cs_portal.portal_rfi_list", {
            "rfis": rfis, "page_name": "cs_rfi"})

    @http.route(["/my/construction/rfi/<int:rfi_id>"], type="http",
                auth="user", website=True)
    def portal_rfi_detail(self, rfi_id, **kw):
        rfi = request.env["cs.rfi"].browse(rfi_id)
        if not rfi.exists() or request.env.user.partner_id not in \
                rfi.cs_portal_partner_ids:
            return request.redirect("/my")
        return request.render("cs_portal.portal_rfi_detail", {
            "rfi": rfi, "page_name": "cs_rfi"})

    @http.route(["/my/construction/rfi/<int:rfi_id>/respond"], type="http",
                auth="user", website=True, methods=["POST"], csrf=True)
    def portal_rfi_respond(self, rfi_id, response="", **kw):
        rfi = request.env["cs.rfi"].browse(rfi_id)
        partner = request.env.user.partner_id
        if rfi.exists() and partner in rfi.cs_portal_partner_ids \
                and (response or "").strip():
            rfi._portal_log_response(partner, response)
        return request.redirect("/my/construction/rfi/%s" % rfi_id)

    @http.route(["/my/construction/submittals"], type="http", auth="user",
                website=True)
    def portal_submittals(self, **kw):
        subs = request.env["cs.submittal"].search(
            [("cs_portal_partner_ids", "in", request.env.user.partner_id.ids)],
            order="name desc")
        return request.render("cs_portal.portal_submittal_list", {
            "submittals": subs, "page_name": "cs_submittal"})

    @http.route(["/my/construction/transmittals"], type="http", auth="user",
                website=True)
    def portal_transmittals(self, **kw):
        trs = request.env["cs.transmittal"].search(
            [("cs_portal_partner_ids", "in", request.env.user.partner_id.ids)],
            order="name desc")
        return request.render("cs_portal.portal_transmittal_list", {
            "transmittals": trs, "page_name": "cs_transmittal"})
