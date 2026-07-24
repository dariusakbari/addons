from odoo import api, fields, models
from odoo.exceptions import ValidationError

SECTIONS = [("labour", "Labour"), ("material", "Material"),
            ("equipment", "Equipment"), ("subcontract", "Subcontract"),
            ("other", "Other")]


class GteProjectBudget(models.Model):
    _name = "gte.project.budget"
    _description = "Project Budget"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(compute="_compute_name", store=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    line_ids = fields.One2many("gte.project.budget.line", "budget_id", copy=True)
    amount_budget = fields.Monetary(currency_field="currency_id",
                                    compute="_compute_amounts", store=True)
    amount_committed = fields.Monetary(
        currency_field="currency_id", compute="_compute_amounts",
        help="Open + approved change-order exposure on this project.")
    amount_actual = fields.Monetary(
        currency_field="currency_id", compute="_compute_amounts",
        help="Costs booked to the project's analytic account (negative "
             "analytic amounts).")
    amount_variance = fields.Monetary(currency_field="currency_id",
                                      compute="_compute_amounts")
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

    @api.depends("line_ids.amount", "project_id")
    def _compute_amounts(self):
        for rec in self:
            rec.amount_budget = sum(rec.line_ids.mapped("amount"))
            cos = self.env["gte.change.order"].search(
                [("project_id", "=", rec.project_id.id),
                 ("state", "not in", ("closed", "cancelled", "rejected"))])
            rec.amount_committed = sum(cos.mapped("exposure"))
            actual = 0.0
            account = rec.project_id.account_id
            if account:
                lines = self.env["account.analytic.line"].search(
                    [("account_id", "=", account.id), ("amount", "<", 0)])
                actual = -sum(lines.mapped("amount"))
            rec.amount_actual = actual
            rec.amount_variance = rec.amount_budget - rec.amount_actual

    def action_approve(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("A budget needs at least one line.")
            rec.state = "approved"

    def action_close(self):
        self.write({"state": "closed"})


class GteProjectBudgetLine(models.Model):
    _name = "gte.project.budget.line"
    _description = "Project Budget Line"

    budget_id = fields.Many2one("gte.project.budget", required=True,
                                ondelete="cascade")
    currency_id = fields.Many2one(related="budget_id.currency_id")
    section = fields.Selection(SECTIONS, required=True, default="labour")
    description = fields.Char()
    amount = fields.Monetary(currency_field="currency_id", required=True)


class GteLabourRate(models.Model):
    """Cost/sell rates by classification. ACL restricted: field employees and
    foremen have NO access to this model at all (audit requirement)."""
    _name = "gte.labour.rate"
    _description = "Labour Rate"
    _order = "classification"

    classification = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    cost_rate = fields.Monetary(currency_field="currency_id",
                                help="Internal cost per hour — confidential.")
    sell_rate = fields.Monetary(currency_field="currency_id")
    active = fields.Boolean(default=True)

    _classification_uniq = models.Constraint(
        "unique(classification, company_id)",
        "A rate already exists for this classification.",
    )


class GteWorkerCert(models.Model):
    _name = "gte.worker.cert"
    _description = "Worker Certification"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
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

    gte_budget_id = fields.Many2one("gte.project.budget",
                                    compute="_compute_gte_budget")
    gte_budget_total = fields.Monetary(compute="_compute_gte_budget",
                                       currency_field="currency_id")

    def _compute_gte_budget(self):
        for rec in self:
            budget = self.env["gte.project.budget"].sudo().search(
                [("project_id", "=", rec.id)], limit=1)
            rec.gte_budget_id = budget
            rec.gte_budget_total = budget.amount_budget if budget else 0.0

    def action_view_gte_budget(self):
        self.ensure_one()
        budget = self.env["gte.project.budget"].search(
            [("project_id", "=", self.id)], limit=1)
        return {
            "type": "ir.actions.act_window",
            "res_model": "gte.project.budget",
            "view_mode": "form",
            "res_id": budget.id or False,
            "context": {"default_project_id": self.id},
        }
