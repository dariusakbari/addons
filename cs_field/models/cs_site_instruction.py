import base64

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CsSiteInstruction(models.Model):
    """Formal Field Memo / Site Instruction — a numbered, issued, acknowledged
    field-direction record (distinct from internal Field Issues)."""
    _name = "cs.site.instruction"
    _description = "Field Memo / Site Instruction"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin"]
    _order = "project_id, name desc"

    name = fields.Char(string="Instruction No.", readonly=True, copy=False,
                       default="New")
    title = fields.Char(required=True, tracking=True)
    project_id = fields.Many2one("project.project", required=True, index=True,
                                 ondelete="restrict", tracking=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    currency_id = fields.Many2one("res.currency",
                                  compute="_compute_currency_id")
    instruction = fields.Html(string="Instruction / Direction")
    issued_by_id = fields.Many2one("res.users", string="Issued By",
                                   default=lambda self: self.env.user,
                                   tracking=True)
    issued_to_id = fields.Many2one("res.partner", string="Issued To",
                                   tracking=True,
                                   help="Contractor / party receiving the direction.")
    date_issued = fields.Date(tracking=True)
    required_by = fields.Date(string="Action Required By", tracking=True)
    acknowledged_by = fields.Char(tracking=True)
    date_acknowledged = fields.Date(tracking=True)
    response = fields.Html(string="Acknowledgement / Response")
    cost_impact = fields.Selection([
        ("none", "None"), ("tbd", "To Be Determined"), ("yes", "Yes")],
        default="none", tracking=True)
    cost_amount = fields.Monetary(currency_field="currency_id")
    schedule_impact_days = fields.Integer(string="Schedule Impact (days)",
                                          tracking=True)
    origin_rfi_id = fields.Many2one("cs.rfi", string="Related RFI", copy=False)
    change_order_id = fields.Many2one("cs.change.order",
                                      string="Resulting Change Order",
                                      copy=False)
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    distribution_ids = fields.Many2many(
        "res.partner", "cs_si_distribution_rel", "si_id", "partner_id",
        string="Distribution List",
        help="Additional recipients (besides Issued To) who get the issued "
             "instruction.")
    last_distributed = fields.Datetime(readonly=True, copy=False)
    distribution_log_ids = fields.One2many(
        "cs.site.instruction.distribution", "instruction_id",
        string="Distribution History", readonly=True, copy=False)
    distribution_count = fields.Integer(compute="_compute_distribution_count")
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ("draft", "Draft"), ("issued", "Issued"),
        ("acknowledged", "Acknowledged"), ("closed", "Closed"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    _si_number_project_uniq = models.Constraint(
        "unique(project_id, name)",
        "Instruction number must be unique per project.",
    )

    @api.depends("company_id.currency_id")
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = (rec.company_id.currency_id
                               or rec.env.company.currency_id)

    def _compute_distribution_count(self):
        for rec in self:
            rec.distribution_count = len(rec.distribution_log_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New" and vals.get("project_id"):
                project = self.env["project.project"].browse(vals["project_id"])
                vals["name"] = self._cs_next_number(
                    project, "cs.site.instruction", "SI")
        return super().create(vals_list)

    def _set_state(self, allowed_from, new_state, extra=None):
        for rec in self:
            if rec.state not in allowed_from:
                raise ValidationError(
                    "Invalid transition %s -> %s on %s"
                    % (rec.state, new_state, rec.name))
            rec.write(dict(extra or {}, state=new_state))

    def action_issue(self):
        for rec in self:
            missing = []
            if not rec.instruction:
                missing.append("instruction text")
            if not rec.issued_to_id:
                missing.append("recipient (Issued To)")
            if missing:
                raise ValidationError(
                    "%s cannot be issued. Missing: %s."
                    % (rec.name, ", ".join(missing)))
        self._set_state(("draft",), "issued",
                        {"date_issued": fields.Date.context_today(self)})

    def action_acknowledge(self):
        for rec in self:
            if not rec.acknowledged_by:
                raise ValidationError(
                    "%s needs who acknowledged it before recording "
                    "acknowledgement." % rec.name)
            if not rec.date_acknowledged:
                rec.date_acknowledged = fields.Date.context_today(self)
        self._set_state(("issued",), "acknowledged")

    def action_close(self):
        self._set_state(("acknowledged", "issued"), "closed")

    def action_cancel(self):
        self._set_state(("draft", "issued"), "cancelled")

    def action_reset(self):
        if not self.env.user.has_group("cs_core.group_cs_pm"):
            raise ValidationError(
                "Only project managers can reopen an instruction.")
        self._set_state(("cancelled", "closed"), "draft")

    # ---------------------------------------------------------- distribution
    def _distribution_recipients(self):
        self.ensure_one()
        partners = self.issued_to_id | self.distribution_ids
        return partners.filtered(lambda p: p.email)

    def _render_si_pdf(self):
        self.ensure_one()
        pdf, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            "cs_field.report_cs_si", res_ids=self.ids)
        return self.env["ir.attachment"].create({
            "name": "%s.pdf" % (self.name or "Site Instruction"),
            "type": "binary",
            "datas": base64.b64encode(pdf),
            "res_model": "cs.site.instruction",
            "res_id": self.id,
            "mimetype": "application/pdf",
        })

    def _do_distribute(self, resend=False):
        self.ensure_one()
        if self.state not in ("issued", "acknowledged"):
            raise ValidationError(
                "%s must be issued before it can be distributed." % self.name)
        recipients = self._distribution_recipients()
        if not recipients:
            raise ValidationError(
                "%s has no recipient with an email address (set 'Issued To' "
                "or add people to the Distribution list)." % self.name)
        attachment = self._render_si_pdf()
        body = Markup(
            "<p>Please find attached %sSite Instruction <strong>%s</strong> "
            "for <strong>%s</strong>: %s.</p>") % (
            "re-issued " if resend else "", self.name,
            self.project_id.display_name or "", self.title or "")
        self.message_post(
            body=body, subject="%s — %s" % (self.name, self.title or ""),
            partner_ids=recipients.ids, attachment_ids=attachment.ids,
            message_type="email", subtype_xmlid="mail.mt_comment")
        now = fields.Datetime.now()
        self.env["cs.site.instruction.distribution"].create([{
            "instruction_id": self.id, "partner_id": p.id, "email": p.email,
            "date_sent": now, "sent_by_id": self.env.user.id,
            "note": "resend" if resend else "initial",
        } for p in recipients])
        self.last_distributed = now
        return recipients

    def action_distribute(self):
        for rec in self:
            recs = rec._do_distribute(resend=False)
        return self._cs_notify("Instruction sent to %d recipient(s)." % len(recs))

    def action_resend(self):
        for rec in self:
            recs = rec._do_distribute(resend=True)
        return self._cs_notify(
            "Instruction re-sent to %d recipient(s)." % len(recs))

    def _cs_notify(self, message):
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {"type": "success", "message": message,
                       "next": {"type": "ir.actions.act_window_close"}},
        }

    def action_make_change_order(self):
        self.ensure_one()
        co = self.env["cs.change.order"].create({
            "project_id": self.project_id.id,
            "title": "From %s: %s" % (self.name, self.title or ""),
            "source_type": "site",
        })
        self.change_order_id = co
        return {
            "type": "ir.actions.act_window",
            "res_model": "cs.change.order",
            "res_id": co.id, "view_mode": "form",
        }

    def unlink(self):
        self._cs_unlink_guard()
        return super().unlink()


class CsSiteInstructionDistribution(models.Model):
    _name = "cs.site.instruction.distribution"
    _description = "Site Instruction Distribution Record"
    _order = "date_sent desc, id desc"

    instruction_id = fields.Many2one("cs.site.instruction", required=True,
                                     ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", string="Recipient",
                                 required=True)
    email = fields.Char()
    date_sent = fields.Datetime(default=fields.Datetime.now)
    sent_by_id = fields.Many2one("res.users", string="Sent By")
    note = fields.Selection([("initial", "Initial"), ("resend", "Re-sent")],
                            default="initial")
