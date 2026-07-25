from odoo import api, fields, models


class CsDashboard(models.AbstractModel):
    _name = "cs.dashboard"
    _description = "Construction Dashboard Data"

    # Groups allowed to see monetary figures (budget / cost / change value).
    _MONEY_GROUPS = ("cs_core.group_cs_pm", "cs_core.group_cs_accounting",
                     "cs_core.group_cs_admin")

    @api.model
    def _win(self, name, model, domain, ctx=None):
        return {
            "type": "ir.actions.act_window", "name": name, "res_model": model,
            "views": [[False, "list"], [False, "form"]],
            "domain": domain, "context": ctx or {},
        }

    @api.model
    def _money(self, currency, amount):
        return "%s%s" % (currency, "{:,.0f}".format(amount or 0.0))

    # ------------------------------------------------------------------
    # Per-project count metrics (visible to everyone). Each is a record
    # count matching a base domain, scoped per project. Monetary figures
    # are handled separately and gated by group. cs.worker.cert is excluded
    # (worker-level, not project-scoped).
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
        """One card block per construction project, each with its own KPIs.

        Card order per project: status (progress, open tasks) -> operational
        queues (RFIs, submittals, changes, field & safety) -> commercial
        figures (budget, committed, actual, variance) shown only to users in
        the money groups.
        """
        defs = self._project_metric_defs()
        counts = {key: self._counts_by_project(model, dom)
                  for (key, _l, _t, _i, model, dom) in defs}

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

        show_money = any(self.env.user.has_group(g) for g in self._MONEY_GROUPS)
        currency = self.env.company.currency_id.symbol or "$"

        # Commercial data (only when the viewer may see money).
        exposure, budgets = {}, {}
        if show_money:
            for grp in self.env["cs.change.order"].sudo().read_group(
                    self._EXPOSURE_DOMAIN, ["project_id", "exposure:sum"],
                    ["project_id"]):
                if grp.get("project_id"):
                    exposure[grp["project_id"][0]] = grp.get("exposure") or 0.0
            for bud in self.env["cs.project.budget"].sudo().search([]):
                budgets[bud.project_id.id] = bud

        result = []
        for p in projects:
            label = p.cs_code or p.name or ""

            # --- status cards (everyone) ---
            pct = (p.task_completion_percentage or 0.0) * 100.0
            cards = [
                {"key": "progress", "label": "Task Progress", "tone": "info",
                 "icon": "fa-tasks", "value": "%.0f%%" % pct,
                 "action": self._win("%s — Tasks" % label, "project.task",
                                     [("project_id", "=", p.id)])},
                {"key": "tasks_open", "label": "Open Tasks", "tone": "primary",
                 "icon": "fa-list-ul", "value": p.open_task_count,
                 "action": self._win("%s — Open Tasks" % label, "project.task",
                                     [("project_id", "=", p.id),
                                      ("is_closed", "=", False)])},
            ]

            # --- operational queues (everyone) ---
            for (key, lbl, tone, icon, model, dom) in defs:
                cards.append({
                    "key": key, "label": lbl, "tone": tone, "icon": icon,
                    "value": counts[key].get(p.id, 0),
                    "action": self._win("%s — %s" % (label, lbl), model,
                                        [("project_id", "=", p.id)] + dom),
                })

            # --- commercial figures (money groups only) ---
            if show_money:
                bud = budgets.get(p.id)
                committed = exposure.get(p.id, 0.0)
                actual = 0.0
                if p.account_id:
                    lines = self.env["account.analytic.line"].sudo().search(
                        [("account_id", "=", p.account_id.id),
                         ("amount", "<", 0)])
                    actual = -sum(lines.mapped("amount"))

                cards.append({
                    "key": "budget", "label": "Budget", "tone": "primary",
                    "icon": "fa-calculator",
                    "value": self._money(currency, bud.amount_budget) if bud
                             else "—",
                    "action": self._win("%s — Budget" % label,
                                        "cs.project.budget",
                                        [("project_id", "=", p.id)])})
                cards.append({
                    "key": "committed", "label": "Committed (Changes)",
                    "tone": "warning", "icon": "fa-line-chart",
                    "value": self._money(currency, committed),
                    "action": self._win("%s — Open Change Orders" % label,
                                        "cs.change.order",
                                        [("project_id", "=", p.id)]
                                        + self._EXPOSURE_DOMAIN)})
                cards.append({
                    "key": "actual", "label": "Actual Cost", "tone": "danger",
                    "icon": "fa-dollar", "value": self._money(currency, actual),
                    "action": self._win(
                        "%s — Cost Entries" % label, "account.analytic.line",
                        [("account_id", "=", p.account_id.id)]) if p.account_id
                        else False})
                cards.append({
                    "key": "variance", "label": "Budget Variance",
                    "tone": "info", "icon": "fa-balance-scale",
                    "value": self._money(currency, bud.amount_budget - actual)
                             if bud else "—",
                    "action": self._win("%s — Budget" % label,
                                        "cs.project.budget",
                                        [("project_id", "=", p.id)])})

            result.append({
                "project_id": p.id,
                "code": p.cs_code or "",
                "name": p.name or "",
                "cards": cards,
            })
        return result
