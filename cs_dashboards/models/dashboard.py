from odoo import api, fields, models


class CsDashboard(models.AbstractModel):
    _name = "cs.dashboard"
    _description = "Construction Dashboard Data"

    @api.model
    def _win(self, name, model, domain, ctx=None):
        return {
            "type": "ir.actions.act_window", "name": name, "res_model": model,
            "views": [[False, "list"], [False, "form"]],
            "domain": domain, "context": ctx or {},
        }

    @api.model
    def get_kpis(self):
        R = self.env["cs.rfi"]
        CO = self.env["cs.change.order"]
        S = self.env["cs.submittal"]
        P = self.env["cs.punch.item"]
        I = self.env["cs.incident"]
        FI = self.env["cs.field.issue"]
        WP = self.env["cs.work.permit"]
        cert = self.env["cs.worker.cert"]

        open_co = CO.search([("state", "not in",
                              ("closed", "cancelled", "rejected"))])
        exposure = sum(open_co.mapped("exposure"))
        currency = self.env.company.currency_id.symbol or "$"

        kpis = [
            {"key": "rfi_open", "label": "Open RFIs", "group": "RFIs",
             "value": R.search_count([("state", "in",
                        ("draft", "open", "sent", "answered"))]),
             "tone": "primary", "icon": "fa-question-circle",
             "action": self._win("Open RFIs", "cs.rfi",
                        [("state", "in", ("draft", "open", "sent", "answered"))])},
            {"key": "rfi_overdue", "label": "Overdue RFIs", "group": "RFIs",
             "value": R.search_count([("is_overdue", "=", True)]),
             "tone": "danger", "icon": "fa-clock-o",
             "action": self._win("Overdue RFIs", "cs.rfi",
                        [("is_overdue", "=", True)])},
            {"key": "sub_pending", "label": "Pending Submittals",
             "group": "Submittals",
             "value": S.search_count([("state", "in",
                        ("draft", "requested", "received", "review",
                         "submitted", "revise"))]),
             "tone": "primary", "icon": "fa-file-text-o",
             "action": self._win("Pending Submittals", "cs.submittal",
                        [("state", "in", ("draft", "requested", "received",
                          "review", "submitted", "revise"))])},
            {"key": "co_await", "label": "Changes Awaiting Client",
             "group": "Change Orders",
             "value": CO.search_count([("state", "=", "submitted")]),
             "tone": "warning", "icon": "fa-exchange",
             "action": self._win("Awaiting Client", "cs.change.order",
                        [("state", "=", "submitted")])},
            {"key": "co_unbilled", "label": "Approved, Unbilled",
             "group": "Change Orders",
             "value": CO.search_count([("state", "=", "approved")]),
             "tone": "warning", "icon": "fa-usd",
             "action": self._win("Approved, Unbilled", "cs.change.order",
                        [("state", "=", "approved")])},
            {"key": "co_exposure", "label": "Open Change Exposure",
             "group": "Change Orders",
             "value": "%s%s" % (currency, "{:,.0f}".format(exposure)),
             "tone": "info", "icon": "fa-line-chart",
             "action": self._win("Open Change Orders", "cs.change.order",
                        [("state", "not in",
                          ("closed", "cancelled", "rejected"))])},
            {"key": "punch_open", "label": "Open Deficiencies",
             "group": "Field & Safety",
             "value": P.search_count([("state", "not in",
                        ("closed", "cancelled"))]),
             "tone": "warning", "icon": "fa-exclamation-triangle",
             "action": self._win("Open Deficiencies", "cs.punch.item",
                        [("state", "not in", ("closed", "cancelled"))])},
            {"key": "incident_open", "label": "Open Incidents",
             "group": "Field & Safety",
             "value": I.search_count([("state", "not in",
                        ("closed", "cancelled"))]),
             "tone": "danger", "icon": "fa-ambulance",
             "action": self._win("Open Incidents", "cs.incident",
                        [("state", "not in", ("closed", "cancelled"))])},
            {"key": "fi_pm", "label": "Field Issues to PM",
             "group": "Field & Safety",
             "value": FI.search_count([("state", "=", "submitted")]),
             "tone": "primary", "icon": "fa-flag",
             "action": self._win("Field Issues", "cs.field.issue",
                        [("state", "=", "submitted")])},
            {"key": "cert_exp", "label": "Certs Expiring/Expired",
             "group": "Field & Safety",
             "value": cert.search_count([("state", "in",
                        ("expiring", "expired"))]),
             "tone": "danger", "icon": "fa-id-card-o",
             "action": self._win("Expiring Certifications", "cs.worker.cert",
                        [("state", "in", ("expiring", "expired"))])},
            {"key": "wp_active", "label": "Active Work Permits",
             "group": "Field & Safety",
             "value": WP.search_count([("state", "=", "active")]),
             "tone": "info", "icon": "fa-check-square-o",
             "action": self._win("Active Permits", "cs.work.permit",
                        [("state", "=", "active")])},
        ]
        return kpis
