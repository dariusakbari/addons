from datetime import timedelta

from odoo import api, fields, models


class CsDashboard(models.AbstractModel):
    _name = "cs.dashboard"
    _description = "Construction Dashboard Data"

    # Groups allowed to see monetary figures (budget / cost / change value).
    _MONEY_GROUPS = ("cs_core.group_cs_pm", "cs_core.group_cs_accounting",
                     "cs_core.group_cs_admin")
    _CONSTRUCTION_MODELS = [
        "cs.rfi", "cs.change.order", "cs.submittal", "cs.punch.item",
        "cs.incident", "cs.field.issue", "cs.work.permit",
    ]
    _EXPOSURE_DOMAIN = [("state", "not in", ("closed", "cancelled", "rejected"))]
    _RFI_OPEN = ("draft", "open", "sent", "answered")
    _SUB_PENDING = ("draft", "requested", "received", "review", "submitted",
                    "revise")

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
        """One card per construction project: progress + grouped metric
        sections (RFIs, Submittals & changes, Field & safety) with urgency
        tones (amber = due soon, red = overdue) and a commercial footer shown
        only to PM / Accounting / Admin.
        """
        today = fields.Date.context_today(self)
        icp = self.env["ir.config_parameter"].sudo()
        rfi_lead = int(icp.get_param("cs.rfi_reminder_days", 2) or 2)
        sub_lead = int(icp.get_param("cs.submittal_reminder_days", 7) or 7)
        rfi_soon = today + timedelta(days=rfi_lead)
        sub_soon = today + timedelta(days=sub_lead)

        rfi_open_dom = [("state", "in", self._RFI_OPEN)]
        rfi_soon_dom = rfi_open_dom + [("date_required", ">=", today),
                                       ("date_required", "<=", rfi_soon)]
        rfi_over_dom = [("date_required", "<", today),
                        ("state", "in", ("draft", "open", "sent"))]
        sub_dom = [("state", "in", self._SUB_PENDING)]
        sub_soon_dom = sub_dom + [("date_required_submit", ">=", today),
                                  ("date_required_submit", "<=", sub_soon)]
        co_await_dom = [("state", "=", "submitted")]
        co_unb_dom = [("state", "=", "approved")]
        punch_dom = [("state", "not in", ("closed", "cancelled"))]
        inc_dom = [("state", "not in", ("closed", "cancelled"))]
        fi_dom = [("state", "=", "submitted")]
        wp_dom = [("state", "=", "active")]

        c = {
            "rfi_open": self._counts_by_project("cs.rfi", rfi_open_dom),
            "rfi_soon": self._counts_by_project("cs.rfi", rfi_soon_dom),
            "rfi_over": self._counts_by_project("cs.rfi", rfi_over_dom),
            "sub": self._counts_by_project("cs.submittal", sub_dom),
            "sub_soon": self._counts_by_project("cs.submittal", sub_soon_dom),
            "co_await": self._counts_by_project("cs.change.order", co_await_dom),
            "co_unb": self._counts_by_project("cs.change.order", co_unb_dom),
            "punch": self._counts_by_project("cs.punch.item", punch_dom),
            "inc": self._counts_by_project("cs.incident", inc_dom),
            "fi": self._counts_by_project("cs.field.issue", fi_dom),
            "wp": self._counts_by_project("cs.work.permit", wp_dom),
        }

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
        exposure, budgets = {}, {}
        if show_money:
            for grp in self.env["cs.change.order"].sudo().read_group(
                    self._EXPOSURE_DOMAIN, ["project_id", "exposure:sum"],
                    ["project_id"]):
                if grp.get("project_id"):
                    exposure[grp["project_id"][0]] = grp.get("exposure") or 0.0
            for bud in self.env["cs.project.budget"].sudo().search([]):
                budgets[bud.project_id.id] = bud

        def tone(v, base):
            return base if v else "muted"

        result = []
        for p in projects:
            label = p.cs_code or p.name or ""
            pid = p.id

            def win(name, model, dom):
                return self._win("%s — %s" % (label, name), model,
                                 [("project_id", "=", pid)] + dom)

            rfis = [
                {"label": "Open", "value": c["rfi_open"].get(pid, 0),
                 "tone": tone(c["rfi_open"].get(pid, 0), "accent"),
                 "action": win("Open RFIs", "cs.rfi", rfi_open_dom)},
                {"label": "Due soon", "value": c["rfi_soon"].get(pid, 0),
                 "tone": tone(c["rfi_soon"].get(pid, 0), "amber"),
                 "action": win("RFIs due soon", "cs.rfi", rfi_soon_dom)},
                {"label": "Overdue", "value": c["rfi_over"].get(pid, 0),
                 "tone": tone(c["rfi_over"].get(pid, 0), "red"),
                 "action": win("Overdue RFIs", "cs.rfi", rfi_over_dom)},
            ]
            changes = [
                {"label": "Pending submittals", "value": c["sub"].get(pid, 0),
                 "tone": tone(c["sub"].get(pid, 0), "accent"),
                 "action": win("Pending submittals", "cs.submittal", sub_dom)},
                {"label": "Subm. due soon", "value": c["sub_soon"].get(pid, 0),
                 "tone": tone(c["sub_soon"].get(pid, 0), "amber"),
                 "action": win("Submittals due soon", "cs.submittal",
                               sub_soon_dom)},
                {"label": "Awaiting client", "value": c["co_await"].get(pid, 0),
                 "tone": tone(c["co_await"].get(pid, 0), "amber"),
                 "action": win("Awaiting client", "cs.change.order",
                               co_await_dom)},
                {"label": "Approved, unbilled", "value": c["co_unb"].get(pid, 0),
                 "tone": tone(c["co_unb"].get(pid, 0), "amber"),
                 "action": win("Approved, unbilled", "cs.change.order",
                               co_unb_dom)},
            ]
            field_safety = [
                {"label": "Deficiencies", "value": c["punch"].get(pid, 0),
                 "tone": tone(c["punch"].get(pid, 0), "amber"),
                 "action": win("Open deficiencies", "cs.punch.item", punch_dom)},
                {"label": "Incidents", "value": c["inc"].get(pid, 0),
                 "tone": tone(c["inc"].get(pid, 0), "red"),
                 "action": win("Open incidents", "cs.incident", inc_dom)},
                {"label": "Field issues", "value": c["fi"].get(pid, 0),
                 "tone": tone(c["fi"].get(pid, 0), "accent"),
                 "action": win("Field issues to PM", "cs.field.issue", fi_dom)},
                {"label": "Work permits", "value": c["wp"].get(pid, 0),
                 "tone": tone(c["wp"].get(pid, 0), "info"),
                 "action": win("Active work permits", "cs.work.permit", wp_dom)},
            ]

            money = []
            if show_money:
                bud = budgets.get(pid)
                committed = exposure.get(pid, 0.0)
                actual = 0.0
                if p.account_id:
                    lines = self.env["account.analytic.line"].sudo().search(
                        [("account_id", "=", p.account_id.id),
                         ("amount", "<", 0)])
                    actual = -sum(lines.mapped("amount"))
                money = [
                    {"label": "Budget",
                     "value": self._money(currency, bud.amount_budget) if bud
                              else "—",
                     "action": win("Budget", "cs.project.budget", [])},
                    {"label": "Committed",
                     "value": self._money(currency, committed),
                     "action": win("Open change orders", "cs.change.order",
                                   self._EXPOSURE_DOMAIN)},
                    {"label": "Actual cost",
                     "value": self._money(currency, actual),
                     "action": self._win(
                         "%s — Cost entries" % label, "account.analytic.line",
                         [("account_id", "=", p.account_id.id)])
                         if p.account_id else False},
                    {"label": "Variance",
                     "value": self._money(currency, bud.amount_budget - actual)
                              if bud else "—",
                     "action": win("Budget", "cs.project.budget", [])},
                ]

            pct = round((p.task_completion_percentage or 0.0) * 100.0)
            result.append({
                "project_id": pid,
                "code": p.cs_code or "",
                "name": p.name or "",
                "partner": p.partner_id.name or "",
                "tags": p.tag_ids.mapped("name"),
                "progress": pct,
                "tasks_done": p.closed_task_count,
                "tasks_total": p.task_count,
                "tasks_open": p.open_task_count,
                "tasks_action": self._win("%s — Tasks" % label, "project.task",
                                          [("project_id", "=", pid)]),
                "sections": [
                    {"name": "RFIs", "metrics": rfis},
                    {"name": "Submittals & changes", "metrics": changes},
                    {"name": "Field & safety", "metrics": field_safety},
                ],
                "money": money,
            })
        return result
