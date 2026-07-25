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

    # ------------------------------------------------------------------
    # Per-project metric definitions. Each is a count of records matching
    # a base domain, scoped per project. Open Change Exposure (a monetary
    # sum) is handled separately below. cs.worker.cert is intentionally
    # excluded: it is worker-level, not project-scoped.
    # (key, label, tone, icon, model, base_domain)
    # ------------------------------------------------------------------
    def _project_metric_defs(self):
        return [
            ("rfi_open", "Open RFIs", "primary", "fa-question-circle", "cs.rfi",
             [("state", "in", ("draft", "open", "sent", "answered"))]),
            ("rfi_overdue", "Overdue RFIs", "danger", "fa-clock-o", "cs.rfi",
             [("is_overdue", "=", True)]),
            ("sub_pending", "Pending Submittals", "primary", "fa-file-text-o",
             "cs.submittal",
             [("state", "in", ("draft", "requested", "received", "review",
                               "submitted", "revise"))]),
            ("co_await", "Changes Awaiting Client", "warning", "fa-exchange",
             "cs.change.order", [("state", "=", "submitted")]),
            ("co_unbilled", "Approved, Unbilled", "warning", "fa-usd",
             "cs.change.order", [("state", "=", "approved")]),
            ("punch_open", "Open Deficiencies", "warning",
             "fa-exclamation-triangle", "cs.punch.item",
             [("state", "not in", ("closed", "cancelled"))]),
            ("incident_open", "Open Incidents", "danger", "fa-ambulance",
             "cs.incident", [("state", "not in", ("closed", "cancelled"))]),
            ("fi_pm", "Field Issues to PM", "primary", "fa-flag",
             "cs.field.issue", [("state", "=", "submitted")]),
            ("wp_active", "Active Work Permits", "info", "fa-check-square-o",
             "cs.work.permit", [("state", "=", "active")]),
        ]

    # Models scanned to decide which projects are "construction" projects
    # (i.e. have at least one construction record in any state).
    _CONSTRUCTION_MODELS = [
        "cs.rfi", "cs.change.order", "cs.submittal", "cs.punch.item",
        "cs.incident", "cs.field.issue", "cs.work.permit",
    ]
    _EXPOSURE_DOMAIN = [("state", "not in", ("closed", "cancelled", "rejected"))]

    @api.model
    def _counts_by_project(self, model, domain):
        """Return {project_id: count} for a domain, grouped by project."""
        out = {}
        for grp in self.env[model].read_group(domain, ["project_id"],
                                               ["project_id"]):
            if grp.get("project_id"):
                out[grp["project_id"][0]] = grp["project_id_count"]
        return out

    @api.model
    def get_project_kpis(self):
        """One card block per construction project, each with its own KPIs."""
        defs = self._project_metric_defs()

        # Pre-compute every metric once, grouped by project (few queries).
        counts = {key: self._counts_by_project(model, dom)
                  for (key, _l, _t, _i, model, dom) in defs}

        exposure = {}
        for grp in self.env["cs.change.order"].read_group(
                self._EXPOSURE_DOMAIN, ["project_id", "exposure:sum"],
                ["project_id"]):
            if grp.get("project_id"):
                exposure[grp["project_id"][0]] = grp.get("exposure") or 0.0

        # Which projects to show: any project with a construction record.
        proj_ids = set()
        for model in self._CONSTRUCTION_MODELS:
            for grp in self.env[model].read_group([], ["project_id"],
                                                  ["project_id"]):
                if grp.get("project_id"):
                    proj_ids.add(grp["project_id"][0])

        projects = self.env["project.project"].browse(sorted(proj_ids))
        projects = projects.filtered("active").sorted(
            key=lambda p: (p.cs_code or "", p.name or ""))

        currency = self.env.company.currency_id.symbol or "$"
        result = []
        for p in projects:
            label = p.cs_code or p.name or ""
            cards = []
            for (key, lbl, tone, icon, model, dom) in defs:
                cards.append({
                    "key": key, "label": lbl, "tone": tone, "icon": icon,
                    "value": counts[key].get(p.id, 0),
                    "action": self._win("%s — %s" % (label, lbl), model,
                                        [("project_id", "=", p.id)] + dom),
                })
                # Slot the monetary exposure card right after co_unbilled so
                # the three Change Order figures sit together.
                if key == "co_unbilled":
                    amt = exposure.get(p.id, 0.0)
                    cards.append({
                        "key": "co_exposure", "label": "Open Change Exposure",
                        "tone": "info", "icon": "fa-line-chart",
                        "value": "%s%s" % (currency, "{:,.0f}".format(amt)),
                        "action": self._win(
                            "%s — Open Change Orders" % label,
                            "cs.change.order",
                            [("project_id", "=", p.id)] + self._EXPOSURE_DOMAIN),
                    })
            result.append({
                "project_id": p.id,
                "code": p.cs_code or "",
                "name": p.name or "",
                "cards": cards,
            })
        return result
