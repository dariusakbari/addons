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

    # Schedule of Values (AIA G703 continuation sheet)
    line_ids = fields.One2many("cs.payment.application.line", "application_id",
                               string="Schedule of Values", copy=True)
    use_sov = fields.Boolean(string="Uses Schedule of Values",
                             compute="_compute_use_sov", store=True)
    sov_scheduled_total = fields.Monetary(
        string="Scheduled Total", currency_field="currency_id",
        compute="_compute_sov_totals", store=True)

    # Holdback release
    holdback_released = fields.Boolean(copy=False, readonly=True)
    holdback_invoice_id = fields.Many2one("account.move", copy=False,
                                          readonly=True,
                                          string="Holdback Invoice")

    @api.depends("line_ids")
    def _compute_use_sov(self):
        for rec in self:
            rec.use_sov = bool(rec.line_ids)

    @api.depends("line_ids.scheduled_value")
    def _compute_sov_totals(self):
        for rec in self:
            rec.sov_scheduled_total = sum(rec.line_ids.mapped("scheduled_value"))

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
                # Inherit the contract sum / holdback from the project, but
                # only when the caller didn't pass a value. Testing membership
                # (not truthiness) means an explicit 0% holdback is honoured.
                if "original_contract" not in vals:
                    vals["original_contract"] = project.cs_contract_amount
                if "holdback_percent" not in vals:
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

    def action_load_schedule(self):
        """Build the Schedule of Values from the project's approved budget,
        carrying forward previous-completed values from the most recent
        prior application (matched by description)."""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(
                "%s: load the schedule while still in draft." % self.name)
        budget = self.env["cs.project.budget"].search(
            [("project_id", "=", self.project_id.id)], limit=1)
        if not budget or not budget.line_ids:
            raise ValidationError(
                "%s: the project has no budget lines to build a schedule "
                "from. Add a project budget first, or enter the schedule "
                "lines manually." % self.name)
        prior = self.search([
            ("project_id", "=", self.project_id.id),
            ("state", "in", ("approved", "invoiced")),
            ("id", "!=", self.id),
        ], order="date_application desc, id desc", limit=1)
        prior_map = {}
        for pl in prior.line_ids:
            prior_map[(pl.description or "").strip().lower()] = pl.completed_to_date
        self.line_ids.unlink()
        vals = []
        seq = 10
        for bl in budget.line_ids:
            desc = bl.description or dict(budget.line_ids._fields[
                "section"].selection).get(bl.section, bl.section)
            vals.append((0, 0, {
                "sequence": seq,
                "item_no": str(seq // 10),
                "description": desc,
                "budget_line_id": bl.id,
                "scheduled_value": bl.amount,
                "previous_completed": prior_map.get(
                    (desc or "").strip().lower(), 0.0),
            }))
            seq += 10
        self.write({"line_ids": vals})
        return True

    def _sync_completed_from_lines(self):
        """Roll the line completed-to-date totals up into the header so all
        the existing progress math (this-period, holdback, due) reuses it."""
        for rec in self:
            if rec.line_ids:
                total = sum(rec.line_ids.mapped("completed_to_date"))
                if rec.completed_to_date != total:
                    rec.completed_to_date = total

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
        analytic = self._cs_analytic_distribution()
        lines = []
        if self.line_ids:
            # One invoice line per Schedule-of-Values item billed this period,
            # each carrying the project's analytic account for job costing.
            for sl in self.line_ids:
                if not sl.this_period_amount:
                    continue
                lines.append((0, 0, {
                    "product_id": product.id,
                    "name": "%s — %s" % (self.name, sl.description or ""),
                    "quantity": 1.0,
                    "price_unit": sl.this_period_amount,
                    "analytic_distribution": analytic or False,
                }))
        if not lines:
            lines.append((0, 0, {
                "product_id": product.id,
                "name": "%s — progress billing to %s" % (self.name, period),
                "quantity": 1.0,
                "price_unit": self.this_period,
                "analytic_distribution": analytic or False,
            }))
        if self.this_period_holdback:
            lines.append((0, 0, {
                "product_id": product.id,
                "name": "Holdback withheld (%.1f%%)" % (self.holdback_percent or 0.0),
                "quantity": 1.0,
                "price_unit": -self.this_period_holdback,
                "analytic_distribution": analytic or False,
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

    def _cs_analytic_distribution(self):
        """Analytic distribution dict targeting the project's analytic account
        so billed revenue lands on the job for cost/revenue reporting."""
        self.ensure_one()
        account = self.project_id.account_id
        return {str(account.id): 100.0} if account else {}

    def action_release_holdback(self):
        """Invoice the accumulated holdback back to the client (final release).
        Only allowed once the work is essentially complete."""
        self.ensure_one()
        if self.state not in ("approved", "invoiced"):
            raise ValidationError(
                "%s must be approved before releasing holdback." % self.name)
        if self.holdback_released:
            raise ValidationError(
                "%s: holdback has already been released." % self.name)
        if self.percent_complete < 100.0:
            raise ValidationError(
                "%s: holdback is normally released only at 100%% complete "
                "(currently %.1f%%)." % (self.name, self.percent_complete))
        if not self.holdback_to_date:
            raise ValidationError(
                "%s: there is no holdback to release." % self.name)
        if not self.partner_id:
            raise ValidationError("%s has no client to invoice." % self.name)
        product = self._cs_progress_product()
        analytic = self._cs_analytic_distribution()
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_origin": "%s — holdback release" % self.name,
            "invoice_line_ids": [(0, 0, {
                "product_id": product.id,
                "name": "%s — holdback release (%.1f%%)" % (
                    self.name, self.holdback_percent or 0.0),
                "quantity": 1.0,
                "price_unit": self.holdback_to_date,
                "analytic_distribution": analytic or False,
            })],
        })
        self.holdback_invoice_id = move
        self.holdback_released = True
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

    def action_view_holdback_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.holdback_invoice_id.id,
            "view_mode": "form",
        }

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()


class CsPaymentApplicationLine(models.Model):
    """One row of the Schedule of Values (AIA G703 continuation sheet)."""
    _name = "cs.payment.application.line"
    _description = "Payment Application — Schedule of Values Line"
    _order = "application_id, sequence, id"

    application_id = fields.Many2one("cs.payment.application", required=True,
                                     ondelete="cascade", index=True)
    currency_id = fields.Many2one(related="application_id.currency_id")
    sequence = fields.Integer(default=10)
    item_no = fields.Char(string="Item #")
    description = fields.Char(required=True)
    budget_line_id = fields.Many2one("cs.project.budget.line",
                                     string="Budget Line",
                                     help="Links this schedule item to a "
                                          "project budget line for job costing.")
    scheduled_value = fields.Monetary(currency_field="currency_id",
                                      help="Contract value allocated to this "
                                           "item.")
    previous_completed = fields.Monetary(
        string="From Previous", currency_field="currency_id",
        help="Work completed and stored on prior applications.")
    this_period_amount = fields.Monetary(
        string="This Period", currency_field="currency_id",
        help="Value of work completed this application.")
    materials_stored = fields.Monetary(
        string="Materials Stored", currency_field="currency_id",
        help="Presently stored materials not yet incorporated.")
    completed_to_date = fields.Monetary(
        string="Completed & Stored to Date", currency_field="currency_id",
        compute="_compute_amounts", store=True)
    percent = fields.Float(string="%", compute="_compute_amounts", store=True)
    balance_to_finish = fields.Monetary(
        string="Balance to Finish", currency_field="currency_id",
        compute="_compute_amounts", store=True)
    holdback = fields.Monetary(currency_field="currency_id",
                               compute="_compute_amounts", store=True)

    @api.depends("scheduled_value", "previous_completed", "this_period_amount",
                 "materials_stored", "application_id.holdback_percent")
    def _compute_amounts(self):
        for rec in self:
            rec.completed_to_date = (rec.previous_completed
                                     + rec.this_period_amount
                                     + rec.materials_stored)
            rec.percent = ((rec.completed_to_date / rec.scheduled_value * 100.0)
                           if rec.scheduled_value else 0.0)
            rec.balance_to_finish = rec.scheduled_value - rec.completed_to_date
            pct = rec.application_id.holdback_percent or 0.0
            rec.holdback = rec.completed_to_date * pct / 100.0

    def _cs_sync_header(self):
        self.mapped("application_id")._sync_completed_from_lines()

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._cs_sync_header()
        return recs

    def write(self, vals):
        res = super().write(vals)
        self._cs_sync_header()
        return res

    def unlink(self):
        apps = self.mapped("application_id")
        res = super().unlink()
        apps._sync_completed_from_lines()
        return res


class AccountMove(models.Model):
    """Keep a Payment Application in sync with its invoice: if the invoice is
    cancelled or deleted, revert the application so it can be re-billed and
    isn't left stranded in the 'invoiced' state."""
    _inherit = "account.move"

    def _cs_revert_applications(self, move_ids):
        PA = self.env["cs.payment.application"].sudo()
        for pa in PA.search([("invoice_id", "in", move_ids)]):
            vals = {"invoice_id": False}
            if pa.state == "invoiced":
                vals["state"] = "approved"
            pa.write(vals)
        for pa in PA.search([("holdback_invoice_id", "in", move_ids)]):
            pa.write({"holdback_invoice_id": False,
                      "holdback_released": False})

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") == "cancel":
            self._cs_revert_applications(self.ids)
        return res

    def unlink(self):
        move_ids = self.ids
        # Revert links before the rows disappear (state won't auto-revert).
        self._cs_revert_applications(move_ids)
        return super().unlink()
