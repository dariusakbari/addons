from odoo import api, fields, models
from odoo.exceptions import ValidationError

SECTIONS = [("labour", "Labour"), ("material", "Material"),
            ("equipment", "Equipment"), ("subcontract", "Subcontract"),
            ("other", "Other")]


class GteProjectBudget(models.Model):
    _name = "cs.project.budget"
    _description = "Project Budget"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(compute="_compute_name", store=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    line_ids = fields.One2many("cs.project.budget.line", "budget_id", copy=True)
    amount_budget = fields.Monetary(aggregator="sum", currency_field="currency_id",
                                    compute="_compute_amounts", store=True)
    amount_committed = fields.Monetary(aggregator="sum",
        currency_field="currency_id", compute="_compute_amounts",
        help="Open purchase commitment: the uninvoiced value of confirmed "
             "purchase orders allocated to this project's analytic account.")
    amount_change_exposure = fields.Monetary(aggregator="sum",
        currency_field="currency_id", compute="_compute_amounts",
        help="Open + approved change-order exposure on this project.")
    amount_actual = fields.Monetary(aggregator="sum",
        currency_field="currency_id", compute="_compute_amounts",
        help="Costs booked to the project's analytic account (negative "
             "analytic amounts).")
    amount_variance = fields.Monetary(aggregator="sum", currency_field="currency_id",
                                      compute="_compute_amounts")
    amount_cost_to_complete = fields.Monetary(
        string="Cost to Complete", currency_field="currency_id",
        help="Estimated remaining cost to finish the work (your input).")
    amount_forecast = fields.Monetary(
        string="Forecast Final Cost", aggregator="sum",
        currency_field="currency_id", compute="_compute_amounts",
        help="Actual cost booked to date plus the cost to complete.")
    amount_forecast_variance = fields.Monetary(
        string="Forecast Variance", aggregator="sum",
        currency_field="currency_id", compute="_compute_amounts",
        help="Budget minus forecast final cost. Negative = projected overrun.")
    state = fields.Selection([("draft", "Draft"), ("approved", "Approved"),
                              ("closed", "Closed")],
                             default="draft", tracking=True, copy=False)

    _budget_project_uniq = models.Constraint(
        "unique(project_id)",
        "This project already has a budget.",
    )

    @api.depends("project_id.name")
    def _compute_name(self):
        for rec in self:
            rec.name = "Budget — %s" % (rec.project_id.name or "")

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id or rec.env.company.currency_id

    @api.depends("line_ids.amount", "project_id", "amount_cost_to_complete")
    def _compute_amounts(self):
        for rec in self:
            rec.amount_budget = sum(rec.line_ids.mapped("amount"))
            cos = self.env["cs.change.order"].search(
                [("project_id", "=", rec.project_id.id),
                 ("state", "not in", ("closed", "cancelled", "rejected"))])
            rec.amount_change_exposure = sum(cos.mapped("exposure"))
            account = rec.project_id.account_id
            rec.amount_committed = rec._open_po_commitment(account)
            actual = 0.0
            if account:
                lines = self.env["account.analytic.line"].search(
                    [("account_id", "=", account.id), ("amount", "<", 0)])
                actual = -sum(lines.mapped("amount"))
            rec.amount_actual = actual
            rec.amount_variance = rec.amount_budget - rec.amount_actual
            rec.amount_forecast = actual + rec.amount_cost_to_complete
            rec.amount_forecast_variance = rec.amount_budget - rec.amount_forecast

    def _open_po_commitment(self, account):
        """Uninvoiced value of confirmed purchase-order lines allocated to the
        project's analytic account. This is the classic 'committed cost' — a
        PO you've issued but not yet been billed for."""
        if not account or "purchase.order.line" not in self.env:
            return 0.0
        pols = self.env["purchase.order.line"].search(
            [("state", "in", ("purchase", "done")),
             ("analytic_distribution", "!=", False)])
        total = 0.0
        for line in pols:
            pct = 0.0
            for key, percentage in (line.analytic_distribution or {}).items():
                ids = [int(a) for a in str(key).split(",") if a.isdigit()]
                if account.id in ids:
                    pct += percentage
            if not pct:
                continue
            qty = line.product_qty or 0.0
            remaining = 1.0
            if qty:
                remaining = max(0.0, (qty - line.qty_invoiced) / qty)
            total += line.price_subtotal * remaining * pct / 100.0
        return total

    def action_approve(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("A budget needs at least one line.")
            rec.state = "approved"

    def action_close(self):
        self.write({"state": "closed"})


class GteProjectBudgetLine(models.Model):
    _name = "cs.project.budget.line"
    _description = "Project Budget Line"

    budget_id = fields.Many2one("cs.project.budget", required=True,
                                ondelete="cascade")
    currency_id = fields.Many2one(related="budget_id.currency_id")
    section = fields.Selection(SECTIONS, required=True, default="labour")
    description = fields.Char()
    amount = fields.Monetary(currency_field="currency_id", required=True)


class GteLabourRate(models.Model):
    """Cost/sell rates by classification, with effective dates so history is
    preserved and OT/DT multipliers. ACL restricted: field employees and
    foremen have NO access to this model at all (audit requirement)."""
    _name = "cs.labour.rate"
    _description = "Labour Rate"
    _order = "classification, effective_from desc"

    classification = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    effective_from = fields.Date(
        required=True, default=fields.Date.context_today,
        help="Date this rate takes effect. Keep old rows for rate history.")
    cost_rate = fields.Monetary(currency_field="currency_id",
                                help="Internal cost per hour — confidential.")
    sell_rate = fields.Monetary(string="Sell Rate (reg.)",
                                currency_field="currency_id")
    ot_multiplier = fields.Float(string="OT ×", default=1.5,
                                 help="Overtime multiplier applied to the sell rate.")
    dt_multiplier = fields.Float(string="DT ×", default=2.0,
                                 help="Double-time multiplier applied to the sell rate.")
    ot_sell_rate = fields.Monetary(string="Sell Rate (OT)", currency_field="currency_id",
                                   compute="_compute_derived_rates")
    dt_sell_rate = fields.Monetary(string="Sell Rate (DT)", currency_field="currency_id",
                                   compute="_compute_derived_rates")
    active = fields.Boolean(default=True)

    _classification_uniq = models.Constraint(
        "unique(classification, company_id, effective_from)",
        "A rate already exists for this classification on that effective date.",
    )

    @api.depends("sell_rate", "ot_multiplier", "dt_multiplier")
    def _compute_derived_rates(self):
        for rec in self:
            rec.ot_sell_rate = rec.sell_rate * (rec.ot_multiplier or 0.0)
            rec.dt_sell_rate = rec.sell_rate * (rec.dt_multiplier or 0.0)

    @api.model
    def get_effective_rate(self, classification, date=None, company_id=None):
        """Return the rate record for a classification effective on `date`
        (the most recent effective_from on or before it), or an empty record.
        """
        date = date or fields.Date.context_today(self)
        company_id = company_id or self.env.company.id
        return self.search([
            ("classification", "=", classification),
            ("company_id", "=", company_id),
            ("effective_from", "<=", date),
        ], order="effective_from desc", limit=1)


class GteWorkerCert(models.Model):
    _name = "cs.worker.cert"
    _description = "Worker Certification"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "expiry_date"

    worker_name = fields.Char(required=True, tracking=True)
    user_id = fields.Many2one("res.users", string="Linked User")
    cert_name = fields.Char(string="Certificate", required=True, tracking=True)
    cert_number = fields.Char(string="Licence / Certificate No.")
    issuer = fields.Char()
    issue_date = fields.Date()
    expiry_date = fields.Date(index=True, tracking=True)
    responsible_id = fields.Many2one(
        "res.users", string="Reminder To",
        default=lambda self: self.env.user,
        help="Gets the renewal activity 30 days before expiry.")
    attachment_ids = fields.Many2many("ir.attachment", string="Certificate Copy")
    state = fields.Selection([("valid", "Valid"), ("expiring", "Expiring Soon"),
                              ("expired", "Expired")],
                             compute="_compute_state", search="_search_state")

    def _compute_state(self):
        today = fields.Date.context_today(self)
        soon = fields.Date.add(today, days=30)
        for rec in self:
            if not rec.expiry_date or rec.expiry_date > soon:
                rec.state = "valid"
            elif rec.expiry_date >= today:
                rec.state = "expiring"
            else:
                rec.state = "expired"

    def _search_state(self, operator, value):
        today = fields.Date.context_today(self)
        soon = fields.Date.add(today, days=30)
        domains = {
            "valid": ["|", ("expiry_date", "=", False), ("expiry_date", ">", soon)],
            "expiring": [("expiry_date", "<=", soon), ("expiry_date", ">=", today)],
            "expired": [("expiry_date", "<", today)],
        }
        if operator == "=" and value in domains:
            return domains[value]
        return []

    @api.model
    def _cron_expiry_reminders(self):
        today = fields.Date.context_today(self)
        soon = fields.Date.add(today, days=30)
        due = self.search([("expiry_date", "!=", False),
                           ("expiry_date", "<=", soon)])
        for rec in due:
            existing = rec.activity_ids.filtered(
                lambda a: a.summary and a.summary.startswith("Certification expiring"))
            if not existing and rec.responsible_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Certification expiring: %s — %s (%s)" % (
                        rec.worker_name, rec.cert_name, rec.expiry_date),
                    user_id=rec.responsible_id.id)


class ProjectProject(models.Model):
    _inherit = "project.project"

    cs_budget_id = fields.Many2one("cs.project.budget",
                                    compute="_compute_cs_budget")
    cs_budget_total = fields.Monetary(compute="_compute_cs_budget",
                                       currency_field="currency_id")
    cs_contract_amount = fields.Monetary(
        string="Original Contract", currency_field="currency_id",
        help="Base contract value, before change orders. Used for progress "
             "billing.")
    cs_holdback_applies = fields.Boolean(
        string="Holdback Applies",
        default=lambda self: bool(self._cs_default_holdback()),
        help="Tick when this project/contract withholds a holdback on progress "
             "billing. The percentage is only used when this is on.")
    cs_holdback_percent = fields.Float(
        string="Holdback %", default=lambda self: self._cs_default_holdback(),
        help="Percentage withheld on progress billing for this project. "
             "Applied only when 'Holdback Applies' is on.")

    @api.onchange("cs_holdback_applies")
    def _onchange_cs_holdback_applies(self):
        if not self.cs_holdback_applies:
            self.cs_holdback_percent = 0.0
        elif not self.cs_holdback_percent:
            self.cs_holdback_percent = self._cs_default_holdback() or 10.0

    @api.model
    def _cs_default_holdback(self):
        """Default holdback for a NEW project. Comes from the optional
        Construction Settings default; if none is configured, 0 (never a
        silent 10%). Each project/contract can then set its own percentage."""
        param = self.env["ir.config_parameter"].sudo().get_param(
            "cs.holdback_percent")
        try:
            return float(param) if param not in (None, False, "") else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _compute_cs_budget(self):
        for rec in self:
            budget = self.env["cs.project.budget"].sudo().search(
                [("project_id", "=", rec.id)], limit=1)
            rec.cs_budget_id = budget
            rec.cs_budget_total = budget.amount_budget if budget else 0.0

    def action_view_cs_budget(self):
        self.ensure_one()
        budget = self.env["cs.project.budget"].search(
            [("project_id", "=", self.id)], limit=1)
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.project.budget",
            "view_mode": "form",
            "res_id": budget.id or False,
            "context": {"default_project_id": self.id},
        }
