from datetime import timedelta

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def cs_exec_summary(self):
        """Per-project executive KPIs for the summary report."""
        self.ensure_one()
        today = fields.Date.today()

        def cnt(model, dom):
            return self.env[model].search_count(
                [("project_id", "=", self.id)] + dom)

        open_co = self.env["cs.change.order"].search([
            ("project_id", "=", self.id),
            ("state", "not in", ("closed", "cancelled", "rejected"))])
        budget = self.env["cs.project.budget"].sudo().search(
            [("project_id", "=", self.id)], limit=1)
        return {
            "progress": round((self.task_completion_percentage or 0.0) * 100.0),
            "rfi_open": cnt("cs.rfi", [("state", "in",
                            ("draft", "open", "sent", "answered"))]),
            "rfi_overdue": cnt("cs.rfi", [("date_required", "<", today),
                            ("state", "in", ("draft", "open", "sent"))]),
            "sub_pending": cnt("cs.submittal", [("state", "in",
                            ("draft", "requested", "received", "review",
                             "submitted", "revise"))]),
            "co_open": len(open_co),
            "exposure": sum(open_co.mapped("exposure")),
            "deficiencies": cnt("cs.punch.item",
                            [("state", "not in", ("closed", "cancelled"))]),
            "incidents": cnt("cs.incident",
                            [("state", "not in", ("closed", "cancelled"))]),
            "budget": budget.amount_budget if budget else 0.0,
            "forecast": budget.amount_forecast if budget else 0.0,
            "currency": self.env.company.currency_id,
        }


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
    def _activity_counts_by_project(self):
        """Return ({pid: pending}, {pid: overdue}) for scheduled activities on
        the project's construction records — the 'needs a human' signal."""
        today = fields.Date.to_string(fields.Date.context_today(self))
        acts = self.env["mail.activity"].search_read(
            [("res_model", "in", self._CONSTRUCTION_MODELS)],
            ["res_model", "res_id", "date_deadline"])
        by_model = {}
        for a in acts:
            by_model.setdefault(a["res_model"], set()).add(a["res_id"])
        rec_project = {}
        for model, ids in by_model.items():
            for rec in self.env[model].browse(list(ids)).exists():
                rec_project[(model, rec.id)] = (
                    rec.project_id.id if rec.project_id else False)
        pending, overdue, by_pid = {}, {}, {}
        for a in acts:
            pid = rec_project.get((a["res_model"], a["res_id"]))
            if not pid:
                continue
            pending[pid] = pending.get(pid, 0) + 1
            by_pid.setdefault(pid, {}).setdefault(
                a["res_model"], set()).add(a["res_id"])
            if a["date_deadline"] and str(a["date_deadline"]) < today:
                overdue[pid] = overdue.get(pid, 0) + 1
        return pending, overdue, by_pid

    @api.model
    def _new_action(self, name, model, pid):
        """A quick-create action pre-scoped to the project."""
        return {
            "type": "ir.actions.act_window", "name": name, "res_model": model,
            "views": [[False, "form"]], "target": "current",
            "context": {"default_project_id": pid},
        }

    @api.model
    def _activity_action(self, name, model_ids):
        """Open the project's scheduled activities (across its construction
        records) in one list."""
        leaves = []
        for model, ids in model_ids.items():
            if ids:
                leaves.append(["&", ("res_model", "=", model),
                               ("res_id", "in", list(ids))])
        if not leaves:
            domain = [("id", "=", 0)]
        else:
            domain = ["|"] * (len(leaves) - 1)
            for leaf in leaves:
                domain += leaf
        view = self.env.ref("cs_dashboards.view_cs_activity_list")
        return {
            "type": "ir.actions.act_window", "name": name,
            "res_model": "mail.activity", "views": [[view.id, "list"]],
            "domain": domain,
        }

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
            "rfi_total": self._counts_by_project("cs.rfi", []),
            "sub_total": self._counts_by_project("cs.submittal", []),
            "co_total": self._counts_by_project("cs.change.order", []),
        }
        act_pending, act_overdue, act_by_pid = \
            self._activity_counts_by_project()
        doc_ref = self.env.ref("cs_documents.action_cs_doc_register",
                               raise_if_not_found=False)
        doc_action_id = doc_ref.id if doc_ref else False

        proj_ids = set()
        for model in self._CONSTRUCTION_MODELS:
            for grp in self.env[model].read_group([], ["project_id"],
                                                  ["project_id"]):
                if grp.get("project_id"):
                    proj_ids.add(grp["project_id"][0])
        # Also surface real construction jobs that were created from an estimate
        # (their sale line's product carries a project template) even before they
        # have any construction records yet — so a freshly-approved estimate shows
        # up immediately. Generic per-SO "Tasks" projects have no project template
        # and stay out.
        gen_lines = self.env["sale.order.line"].sudo().search([
            ("product_id.project_template_id", "!=", False),
            ("project_id", "!=", False),
        ])
        proj_ids |= set(gen_lines.mapped("project_id").ids)
        projects = self.env["project.project"].browse(sorted(proj_ids))
        projects = projects.filtered(
            lambda p: p.active and not p.is_template).sorted(
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
                {"label": "Total", "value": c["rfi_total"].get(pid, 0),
                 "tone": "muted",
                 "action": win("All RFIs", "cs.rfi", [])},
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
                {"label": "Submittals total", "value": c["sub_total"].get(pid, 0),
                 "tone": "muted",
                 "action": win("All submittals", "cs.submittal", [])},
                {"label": "Changes total", "value": c["co_total"].get(pid, 0),
                 "tone": "muted",
                 "action": win("All change orders", "cs.change.order", [])},
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
                "activity": {
                    "pending": act_pending.get(pid, 0),
                    "overdue": act_overdue.get(pid, 0),
                    "action": self._activity_action(
                        "%s — Activities" % label, act_by_pid.get(pid, {})),
                },
                "quick_actions": [
                    {"label": "New RFI", "icon": "fa-question-circle",
                     "action": self._new_action(
                         "New RFI — %s" % label, "cs.rfi", pid)},
                    {"label": "New CO", "icon": "fa-exchange",
                     "action": self._new_action(
                         "New Change Order — %s" % label,
                         "cs.change.order", pid)},
                    {"label": "Daily Log", "icon": "fa-pencil-square-o",
                     "action": self._new_action(
                         "New Daily Log — %s" % label, "cs.daily.log", pid)},
                    {"label": "Safety Report", "icon": "fa-shield",
                     "action": self._new_action(
                         "New Safety Report — %s" % label,
                         "cs.safety.report", pid)},
                    {"label": "Upload Drawing", "icon": "fa-upload",
                     "action": doc_action_id},
                ],
                "sections": [
                    {"name": "RFIs", "metrics": rfis},
                    {"name": "Submittals & changes", "metrics": changes},
                    {"name": "Field & safety", "metrics": field_safety},
                ],
                "money": money,
            })
        return result
