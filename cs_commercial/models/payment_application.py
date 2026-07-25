from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CsPaymentApplication(models.Model):
    """AIA G702-style progress billing / application for payment."""
    _name = "cs.payment.application"
    _description = "Progress Billing / Payment Application"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "project_id, date_application desc, id desc"

    name = fields.Char(string="Application No.", readonly=True, copy=False,
                       default="New")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    partner_id = fields.Many2one("res.partner", string="Client",
                                 compute="_compute_partner_id", store=True,
                                 readonly=False)
    date_application = fields.Date(default=fields.Date.context_today,
                                   tracking=True)
    period_start = fields.Date(tracking=True)
    period_end = fields.Date(string="Period To", required=True, tracking=True)
    state = fields.Selection([
        ("draft", "Draft"), ("submitted", "Submitted"),
        ("approved", "Approved"), ("invoiced", "Invoiced"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    # Contract sum
    original_contract = fields.Monetary(currency_field="currency_id",
                                        tracking=True)
    approved_co_total = fields.Monetary(string="Approved Changes",
                                        currency_field="currency_id",
                                        compute="_compute_progress", store=True)
    revised_contract = fields.Monetary(string="Revised Contract",
                                       currency_field="currency_id",
                                       compute="_compute_progress", store=True)

    # Work completed
    completed_to_date = fields.Monetary(
        string="Completed to Date", currency_field="currency_id", tracking=True,
        help="Total value of work completed and stored materials to date.")
    percent_complete = fields.Float(string="% Complete",
                                    compute="_compute_progress", store=True)
    previous_completed = fields.Monetary(currency_field="currency_id",
                                         compute="_compute_progress", store=True)
    this_period = fields.Monetary(string="This Period",
                                  currency_field="currency_id",
                                  compute="_compute_progress", store=True)

    # Holdback
    holdback_percent = fields.Float(string="Holdback %", tracking=True)
    holdback_to_date = fields.Monetary(currency_field="currency_id",
                                       compute="_compute_progress", store=True)
    this_period_holdback = fields.Monetary(currency_field="currency_id",
                                           compute="_compute_progress", store=True)

    # Payment
    earned_less_holdback = fields.Monetary(currency_field="currency_id",
                                           compute="_compute_progress", store=True)
    previous_payments = fields.Monetary(currency_field="currency_id",
                                        compute="_compute_progress", store=True)
    current_due = fields.Monetary(string="Current Payment Due",
                                  currency_field="currency_id",
                                  compute="_compute_progress", store=True)

    invoice_id = fields.Many2one("account.move", copy=False, readonly=True)

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = (rec.company_id.currency_id
                               or rec.env.company.currency_id)

    @api.depends("project_id.partner_id")
    def _compute_partner_id(self):
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = rec.project_id.partner_id

    @api.depends("project_id", "original_contract", "completed_to_date",
                 "holdback_percent")
    def _compute_progress(self):
        for rec in self:
            cos = self.env["cs.change.order"].search([
                ("project_id", "=", rec.project_id.id),
                ("state", "in", ("approved", "billed", "paid", "closed")),
            ])
            rec.approved_co_total = sum(cos.mapped("amount_approved"))
            rec.revised_contract = rec.original_contract + rec.approved_co_total
            rec.percent_complete = (
                (rec.completed_to_date / rec.revised_contract * 100.0)
                if rec.revised_contract else 0.0)

            others = self.search([
                ("project_id", "=", rec.project_id.id),
                ("state", "in", ("approved", "invoiced")),
                ("id", "!=", rec.id if isinstance(rec.id, int) else 0),
            ])
            rec.previous_completed = sum(others.mapped("completed_to_date"))
            prev_holdback = sum(others.mapped("holdback_to_date"))
            prev_earned = sum(others.mapped("earned_less_holdback"))

            rec.this_period = rec.completed_to_date - rec.previous_completed
            rec.holdback_to_date = (
                rec.completed_to_date * (rec.holdback_percent or 0.0) / 100.0)
            rec.this_period_holdback = rec.holdback_to_date - prev_holdback
            rec.earned_less_holdback = (
                rec.completed_to_date - rec.holdback_to_date)
            rec.previous_payments = prev_earned
            rec.current_due = rec.earned_less_holdback - prev_earned

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project = None
            if vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                if vals.get("name", "New") == "New":
                    vals["name"] = self._cs_next_number(
                        project, "cs.payment.application", "PA")
                if not vals.get("original_contract"):
                    vals["original_contract"] = project.cs_contract_amount
                if not vals.get("holdback_percent"):
                    vals["holdback_percent"] = project.cs_holdback_percent
        return super().create(vals_list)

    def _set_state(self, allowed_from, new_state):
        for rec in self:
            if rec.state not in allowed_from:
                raise ValidationError(
                    "Invalid transition %s -> %s on %s"
                    % (rec.state, new_state, rec.name))
        self.write({"state": new_state})

    def action_submit(self):
        for rec in self:
            if not rec.period_end:
                raise ValidationError(
                    "%s needs a period-end date." % rec.name)
            if rec.completed_to_date <= rec.previous_completed:
                raise ValidationError(
                    "%s: completed-to-date must exceed the previously billed "
                    "amount (%s)." % (rec.name, rec.previous_completed))
        self._set_state(("draft",), "submitted")

    def action_approve(self):
        self._set_state(("submitted",), "approved")

    def action_reset(self):
        if not self.env.user.has_group("cs_core.group_cs_pm"):
            raise ValidationError(
                "Only project managers can reset a payment application.")
        self._set_state(("submitted", "approved", "cancelled"), "draft")

    def action_cancel(self):
        for rec in self:
            if rec.invoice_id:
                raise ValidationError(
                    "%s already has an invoice; cancel the invoice first."
                    % rec.name)
        self._set_state(("draft", "submitted", "approved"), "cancelled")

    @api.model
    def _cs_progress_product(self):
        product = self.env["product.product"].search(
            [("name", "=", "Construction Progress Billing")], limit=1)
        if not product:
            product = self.env["product.product"].create({
                "name": "Construction Progress Billing",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 0.0,
                "purchase_ok": False,
            })
        return product

    def action_create_invoice(self):
        self.ensure_one()
        if self.state != "approved":
            raise ValidationError(
                "%s must be approved before invoicing." % self.name)
        if self.invoice_id:
            raise ValidationError("%s already has an invoice." % self.name)
        if not self.partner_id:
            raise ValidationError(
                "%s has no client to invoice." % self.name)
        product = self._cs_progress_product()
        period = self.period_end and self.period_end.strftime("%Y-%m-%d") or ""
        lines = [(0, 0, {
            "product_id": product.id,
            "name": "%s — progress billing to %s" % (self.name, period),
            "quantity": 1.0,
            "price_unit": self.this_period,
        })]
        if self.this_period_holdback:
            lines.append((0, 0, {
                "product_id": product.id,
                "name": "Holdback withheld (%.1f%%)" % (self.holdback_percent or 0.0),
                "quantity": 1.0,
                "price_unit": -self.this_period_holdback,
            }))
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_origin": self.name,
            "invoice_line_ids": lines,
        })
        self.invoice_id = move
        self.state = "invoiced"
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
        }

    def action_view_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
        }

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()
