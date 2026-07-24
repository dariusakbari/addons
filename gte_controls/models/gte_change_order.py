from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteChangeOrder(models.Model):
    _name = "gte.change.order"
    _description = "Change Order"
    _inherit = ["mail.thread", "mail.activity.mixin", "gte.legacy.mixin"]
    _order = "project_id, name desc"

    name = fields.Char(string="Change Number", readonly=True, copy=False, default="New")
    title = fields.Char(required=True, tracking=True)
    scope = fields.Html(string="Complete Scope")
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    source_type = fields.Selection([
        ("owner", "Owner Initiated"), ("rfi", "From RFI"),
        ("site", "Site Condition"), ("design", "Design Change"),
        ("other", "Other")], default="owner", tracking=True)
    origin_rfi_id = fields.Many2one("gte.rfi", string="Originating RFI", copy=False)
    origin_ref = fields.Char(string="Instruction / Drawing Reference")
    partner_id = fields.Many2one("res.partner", string="Client",
                                 compute="_compute_partner_id", store=True,
                                 readonly=False, tracking=True)
    user_id = fields.Many2one("res.users", string="Project Manager",
                              default=lambda self: self.env.user, tracking=True)
    line_ids = fields.One2many("gte.change.order.line", "order_id", copy=True)
    amount_proposed = fields.Monetary(currency_field="currency_id",
                                      compute="_compute_amounts", store=True,
                                      tracking=True)
    amount_submitted = fields.Monetary(currency_field="currency_id", readonly=True,
                                       copy=False, tracking=True,
                                       help="Snapshot taken at submission; never overwritten "
                                            "silently — changes are tracked in the chatter.")
    amount_approved = fields.Monetary(currency_field="currency_id", tracking=True)
    exposure = fields.Monetary(currency_field="currency_id",
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
    invoice_ids = fields.Many2many("account.move", string="Invoices", copy=False)
    analytic_account_id = fields.Many2one("account.analytic.account", copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("pricing", "Pricing"), ("review", "Internal Review"),
        ("submitted", "Submitted"), ("changes", "Changes Requested"),
        ("approved", "Approved"), ("rejected", "Rejected"),
        ("billed", "Billed"), ("paid", "Paid"), ("closed", "Closed"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    _sql_constraints = [
        ("co_number_project_uniq", "unique(project_id, name)",
         "Change number must be unique per project."),
    ]

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
                vals["name"] = self._gte_next_number(project, "gte.change.order", "CO")
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

    def action_submit(self):
        for rec in self:
            rec.amount_submitted = rec.amount_proposed
        self._set_state(("review",), "submitted",
                        {"date_submitted": fields.Date.context_today(self)})

    def action_request_changes(self):
        self._set_state(("submitted",), "changes")

    def action_approve(self):
        for rec in self:
            if not rec.amount_approved:
                rec.amount_approved = rec.amount_submitted or rec.amount_proposed
        self._set_state(("submitted",), "approved",
                        {"date_decision": fields.Date.context_today(self)})

    def action_reject(self):
        self._set_state(("submitted",), "rejected",
                        {"date_decision": fields.Date.context_today(self)})

    def action_billed(self):
        self._set_state(("approved",), "billed",
                        {"billing_status": "billed",
                         "date_billed": fields.Date.context_today(self)})

    def action_paid(self):
        self._set_state(("billed",), "paid", {"payment_status": "paid"})

    def action_close(self):
        self._set_state(("paid", "rejected", "approved", "billed"), "closed")

    def action_cancel(self):
        self._set_state(("draft", "pricing", "review"), "cancelled")


class GteChangeOrderLine(models.Model):
    _name = "gte.change.order.line"
    _description = "Change Order Cost Line"

    order_id = fields.Many2one("gte.change.order", required=True, ondelete="cascade")
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

    @api.depends("quantity", "unit_cost", "markup_pct", "tax_pct")
    def _compute_amounts(self):
        for line in self:
            line.subtotal_cost = line.quantity * line.unit_cost
            sell = line.subtotal_cost * (1.0 + line.markup_pct / 100.0)
            line.price_sell = sell * (1.0 + line.tax_pct / 100.0)
