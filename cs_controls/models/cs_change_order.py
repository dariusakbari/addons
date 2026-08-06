from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteChangeOrder(models.Model):
    _name = "cs.change.order"
    _description = "Change Order"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "project_id, name desc"

    name = fields.Char(string="Change Number", readonly=True, copy=False, default="New")
    title = fields.Char(required=True, tracking=True)
    scope = fields.Html(string="Complete Scope")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    source_type = fields.Selection([
        ("owner", "Owner Initiated"), ("rfi", "From RFI"),
        ("site", "Site Condition"), ("design", "Design Change"),
        ("other", "Other")], default="owner", tracking=True)
    origin_rfi_id = fields.Many2one("cs.rfi", string="Originating RFI", copy=False)
    origin_ref = fields.Char(string="Instruction / Drawing Reference")
    partner_id = fields.Many2one("res.partner", string="Client",
                                 compute="_compute_partner_id", store=True,
                                 readonly=False, tracking=True)
    user_id = fields.Many2one("res.users", string="Project Manager",
                              default=lambda self: self.env.user, tracking=True)
    distribution_ids = fields.Many2many(
        "res.partner", "cs_co_distribution_rel", "co_id", "partner_id",
        string="Distribution List",
        help="Recipients of the change-order email. The client is included "
             "automatically.")
    line_ids = fields.One2many("cs.change.order.line", "order_id", copy=True)
    amount_proposed = fields.Monetary(aggregator="sum", currency_field="currency_id",
                                      compute="_compute_amounts", store=True,
                                      tracking=True)
    amount_submitted = fields.Monetary(currency_field="currency_id", readonly=True,
                                       copy=False, tracking=True,
                                       help="Snapshot taken at submission; never overwritten "
                                            "silently — changes are tracked in the chatter.")
    amount_approved = fields.Monetary(aggregator="sum", currency_field="currency_id", tracking=True)
    exposure = fields.Monetary(aggregator="sum", currency_field="currency_id",
                               compute="_compute_amounts", store=True,
                               help="Approved amount when approved, otherwise proposed "
                                    "amount while the change is unresolved.")
    schedule_days = fields.Integer(string="Schedule Impact (days)", tracking=True)
    date_quote = fields.Date(tracking=True)
    date_submitted = fields.Date(tracking=True)
    date_required = fields.Date(string="Required Decision Date", tracking=True)
    date_decision = fields.Date(string="Approved / Rejected Date", tracking=True)
    billing_status = fields.Selection([
        ("none", "Not Billable"), ("to_bill", "To Bill"),
        ("billed", "Billed")], default="to_bill", tracking=True)
    date_billed = fields.Date(tracking=True)
    payment_status = fields.Selection([
        ("unpaid", "Unpaid"), ("partial", "Partially Paid"), ("paid", "Paid")],
        default="unpaid", tracking=True)
    client_response = fields.Html()
    sale_order_id = fields.Many2one("sale.order", copy=False)
    sale_line_id = fields.Many2one("sale.order.line", copy=False)
    invoice_ids = fields.Many2many("account.move", string="Invoices", copy=False)
    analytic_account_id = fields.Many2one("account.analytic.account", copy=False)
    approval_reference = fields.Char(
        string="Approval Reference", tracking=True,
        help="Client PO / approval letter number, or attach the approval.")
    doc_exception_reason = fields.Char(
        string="Missing-Documents Exception", tracking=True,
        help="Required when submitting without supporting documents.")
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ("draft", "Draft"), ("pricing", "Pricing"), ("review", "Internal Review"),
        ("submitted", "Submitted"), ("changes", "Changes Requested"),
        ("approved", "Approved"), ("rejected", "Rejected"),
        ("billed", "Billed"), ("paid", "Paid"), ("closed", "Closed"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    _co_number_project_uniq = models.Constraint(
        "unique(project_id, name)",
        "Change number must be unique per project.",
    )

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id or rec.env.company.currency_id

    @api.depends("project_id.partner_id")
    def _compute_partner_id(self):
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = rec.project_id.partner_id

    @api.depends("line_ids.price_sell", "amount_approved", "state")
    def _compute_amounts(self):
        for rec in self:
            rec.amount_proposed = sum(rec.line_ids.mapped("price_sell"))
            if rec.state in ("approved", "billed", "paid", "closed"):
                rec.exposure = rec.amount_approved
            elif rec.state in ("rejected", "cancelled"):
                rec.exposure = 0.0
            else:
                rec.exposure = rec.amount_proposed

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(project, "cs.change.order", "CO")
        return super().create(vals_list)

    def _set_state(self, allowed_from, new_state, extra_vals=None):
        for rec in self:
            if rec.state not in allowed_from:
                raise ValidationError(
                    "Invalid transition %s -> %s on %s" % (rec.state, new_state, rec.name))
            rec.write(dict(extra_vals or {}, state=new_state))

    def action_price(self):
        self._set_state(("draft", "changes"), "pricing")

    def action_review(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Cost lines are required before review on %s." % rec.name)
        self._set_state(("pricing",), "review")

    def _attachment_count(self):
        self.ensure_one()
        return self.env["ir.attachment"].search_count(
            [("res_model", "=", self._name), ("res_id", "=", self.id)])

    def action_submit(self):
        for rec in self:
            missing = []
            if not rec.scope: missing.append("description and scope")
            if not rec.source_type: missing.append("source")
            if not rec.line_ids: missing.append("cost breakdown")
            if rec.amount_proposed <= 0: missing.append("proposed amount")
            if not rec.partner_id: missing.append("client contact")
            if not rec._attachment_count() and not rec.doc_exception_reason:
                missing.append("supporting documents or a documented exception")
            if missing:
                raise ValidationError(
                    "%s cannot be submitted. Missing: %s." % (rec.name, ", ".join(missing)))
            rec.amount_submitted = rec.amount_proposed
        self._set_state(("review",), "submitted",
                        {"date_submitted": fields.Date.context_today(self)})

    def action_request_changes(self):
        self._set_state(("submitted",), "changes")

    def action_approve(self):
        limit = float(self.env["ir.config_parameter"].sudo().get_param(
            "cs.co_approval_limit", "0") or 0)
        for rec in self:
            if not rec.amount_approved:
                rec.amount_approved = rec.amount_submitted or rec.amount_proposed
            missing = []
            if not rec.amount_approved: missing.append("approved amount")
            if not rec.approval_reference and not rec._attachment_count():
                missing.append("approval reference or attached approval")
            if missing:
                raise ValidationError(
                    "%s cannot be approved. Missing: %s." % (rec.name, ", ".join(missing)))
            if limit and rec.amount_approved > limit and                     not self.env.user.has_group("cs_core.group_cs_admin"):
                raise ValidationError(
                    "%s exceeds the approval limit (%.2f). A Construction "
                    "Administrator must approve it." % (rec.name, limit))
        self._set_state(("submitted",), "approved",
                        {"date_decision": fields.Date.context_today(self)})

    def action_reject(self):
        self._set_state(("submitted",), "rejected",
                        {"date_decision": fields.Date.context_today(self)})

    def action_billed(self):
        for rec in self:
            if not rec.invoice_ids and not rec.sale_order_id:
                raise ValidationError(
                    "%s cannot be marked billed without a linked sales order "
                    "or invoice." % rec.name)
        self._set_state(("approved",), "billed",
                        {"billing_status": "billed",
                         "date_billed": fields.Date.context_today(self)})

    def action_paid(self):
        for rec in self:
            if not rec.invoice_ids:
                raise ValidationError(
                    "%s cannot be marked paid without linked invoices." % rec.name)
        self._set_state(("billed",), "paid", {"payment_status": "paid"})

    def _cs_project_sale_order(self):
        """Find an open sale order for this project, or create one."""
        self.ensure_one()
        partner = self.partner_id or self.project_id.partner_id
        if not partner:
            raise ValidationError(
                "%s has no client — set a client on the change order or the "
                "project before billing." % self.name)
        so = self.env["sale.order"].search([
            ("cs_project_id", "=", self.project_id.id),
            ("state", "in", ("draft", "sent")),
        ], limit=1)
        if not so:
            so = self.env["sale.order"].create({
                "partner_id": partner.id,
                "cs_project_id": self.project_id.id,
                "origin": self.project_id.name,
            })
        return so

    @api.model
    def _cs_co_product(self):
        """The service product used on change-order sale lines. Resilient:
        return the data record, else an existing one by name, else create it."""
        product = self.env.ref("cs_controls.product_change_order",
                               raise_if_not_found=False)
        if product:
            return product
        product = self.env["product.product"].search(
            [("name", "=", "Change Order Work")], limit=1)
        if not product:
            product = self.env["product.product"].create({
                "name": "Change Order Work",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 0.0,
                "purchase_ok": False,
            })
        return product

    def action_bill_via_sale(self):
        """Add (or update) a sale-order line for the approved change amount."""
        product = self._cs_co_product()
        for rec in self:
            if rec.state not in ("approved", "billed"):
                raise ValidationError(
                    "%s must be approved before it can be billed." % rec.name)
            if not rec.amount_approved:
                raise ValidationError(
                    "%s has no approved amount to bill." % rec.name)
            so = rec._cs_project_sale_order()
            line_vals = {
                "product_id": product.id if product else False,
                "name": "%s — %s" % (rec.name, rec.title or ""),
                "product_uom_qty": 1.0,
                "price_unit": rec.amount_approved,
            }
            if rec.sale_line_id and rec.sale_line_id.order_id == so:
                rec.sale_line_id.write(line_vals)
            else:
                line_vals["order_id"] = so.id
                rec.sale_line_id = self.env["sale.order.line"].create(line_vals)
            # Force the price after the product-driven compute so the approved
            # amount is not overwritten by the product's list price.
            rec.sale_line_id.price_unit = rec.amount_approved
            rec.sale_order_id = so
            rec.billing_status = "to_bill"
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self[:1].sale_order_id.id,
            "view_mode": "form",
        }

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.sale_order_id.id,
            "view_mode": "form",
        }

    def action_reopen(self):
        if not self.env.user.has_group("cs_core.group_cs_pm"):
            raise ValidationError("Only project managers can reopen a change order.")
        self._set_state(("closed", "cancelled", "rejected"), "draft")

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()

    def action_close(self):
        self._set_state(("paid", "rejected", "approved", "billed"), "closed")

    def action_cancel(self):
        self._set_state(("draft", "pricing", "review"), "cancelled")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cs_project_id = fields.Many2one(
        "project.project", string="Construction Project", index=True, copy=False,
        help="Links this order to a construction project so change orders "
             "attach to it.")


class GteChangeOrderLine(models.Model):
    _name = "cs.change.order.line"
    _description = "Change Order Cost Line"

    order_id = fields.Many2one("cs.change.order", required=True, ondelete="cascade")
    currency_id = fields.Many2one(related="order_id.currency_id")
    section = fields.Selection([
        ("labour", "Labour"), ("material", "Material"), ("equipment", "Equipment"),
        ("subcontract", "Subcontract"), ("other", "Other")],
        required=True, default="labour")
    description = fields.Char(required=True)
    quantity = fields.Float(default=1.0)
    uom = fields.Char(string="Unit")
    unit_cost = fields.Monetary(currency_field="currency_id")
    markup_pct = fields.Float(string="Markup %")
    tax_pct = fields.Float(string="Tax %")
    subtotal_cost = fields.Monetary(currency_field="currency_id",
                                    compute="_compute_amounts", store=True)
    price_sell = fields.Monetary(currency_field="currency_id",
                                 compute="_compute_amounts", store=True)

    @api.depends("quantity", "unit_cost", "markup_pct")
    def _compute_amounts(self):
        for line in self:
            line.subtotal_cost = line.quantity * line.unit_cost
            # Sell price is net of sales tax. tax_pct is retained for reference
            # only and is NOT folded into the change-order value, so contract
            # value and all KPIs stay net of tax.
            line.price_sell = line.subtotal_cost * (1.0 + line.markup_pct / 100.0)
