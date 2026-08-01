import base64

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .safety_template import QTYPE

# How each answer type is scored for pass/fail roll-up.
FAIL_VALUES = {"fail", "no"}


class CsSafetyReport(models.Model):
    _name = "cs.safety.report"
    _description = "Safety Report"
    _inherit = ["mail.thread", "mail.activity.mixin", "cs.legacy.mixin",
                "cs.qr.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(readonly=True, copy=False, default="New", index=True)
    template_id = fields.Many2one(
        "cs.safety.template", string="Template", required=True,
        domain="[('state','=','published')]", tracking=True,
        ondelete="restrict")
    template_version = fields.Integer(readonly=True, copy=False)
    template_type = fields.Selection(
        related="template_id.template_type", store=True)
    project_id = fields.Many2one(
        "project.project", required=True, index=True, ondelete="restrict",
        tracking=True)
    company_id = fields.Many2one(
        related="project_id.company_id", store=True)
    date = fields.Date(required=True, default=fields.Date.context_today,
                       tracking=True)
    location = fields.Char(string="Work Location")
    title = fields.Char(help="Optional short description of this report.")
    prepared_by_id = fields.Many2one(
        "res.users", string="Prepared By",
        default=lambda self: self.env.user, tracking=True)
    supervisor_id = fields.Many2one("res.users", string="Supervisor")
    intro = fields.Html(related="template_id.intro")

    answer_ids = fields.One2many(
        "cs.safety.report.answer", "report_id", copy=True)
    signature_ids = fields.One2many(
        "cs.safety.report.signature", "report_id", copy=False)

    state = fields.Selection([
        ("draft", "Draft"),
        ("complete", "Complete"),
        ("issued", "Issued"),
        ("locked", "Locked"),
        ("cancelled", "Cancelled")],
        default="draft", tracking=True, index=True, copy=False)

    fail_count = fields.Integer(compute="_compute_results", store=True)
    answered_count = fields.Integer(compute="_compute_results", store=True)
    question_total = fields.Integer(compute="_compute_results", store=True)
    overall_result = fields.Selection([
        ("pass", "Pass"), ("attention", "Needs Attention"),
        ("na", "N/A")], compute="_compute_results", store=True)

    # Distribution (mirrors the Site Instruction pattern)
    distribution_ids = fields.Many2many(
        "res.partner", "cs_safety_report_dist_rel", "report_id", "partner_id",
        string="Distribution")
    distribution_log_ids = fields.One2many(
        "cs.safety.report.distribution", "report_id", copy=False)
    distribution_count = fields.Integer(compute="_compute_distribution_count")
    last_distributed = fields.Datetime(readonly=True, copy=False)

    # ------------------------------------------------------------- computes
    @api.depends("answer_ids.value_pfn", "answer_ids.value_yn",
                 "answer_ids.is_answered", "answer_ids.is_fail")
    def _compute_results(self):
        for rec in self:
            answers = rec.answer_ids
            rec.question_total = len(answers)
            rec.answered_count = len(answers.filtered("is_answered"))
            rec.fail_count = len(answers.filtered("is_fail"))
            if rec.fail_count:
                rec.overall_result = "attention"
            elif rec.answered_count:
                rec.overall_result = "pass"
            else:
                rec.overall_result = "na"

    def _compute_distribution_count(self):
        for rec in self:
            rec.distribution_count = len(rec.distribution_log_ids)

    # ------------------------------------------------------------- creation
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name in (False, "New") and rec.project_id and rec.template_id:
                prefix = (rec.template_id.code or "SAF").upper()
                rec.name = rec._cs_next_number(
                    rec.project_id, "cs.safety.report", prefix)
            if not rec.template_version and rec.template_id:
                rec.template_version = rec.template_id.version
            if not rec.answer_ids and rec.template_id:
                rec._load_from_template()
        return records

    @api.onchange("template_id")
    def _onchange_template_id(self):
        if not self.template_id:
            return
        self.template_version = self.template_id.version
        self.answer_ids = self._build_answer_commands()

    def _build_answer_commands(self):
        self.ensure_one()
        commands = [(5, 0, 0)]
        seq = 0
        for section in self.template_id.section_ids.sorted(
                lambda s: (s.sequence, s.id)):
            for q in section.question_ids.sorted(lambda q: (q.sequence, q.id)):
                seq += 10
                commands.append((0, 0, {
                    "sequence": seq,
                    "section_name": section.name,
                    "question_id": q.id,
                    "question_name": q.name,
                    "help_text": q.help_text,
                    "qtype": q.qtype,
                    "required": q.required,
                    "requires_photo": q.requires_photo,
                    "corrective_on_fail": q.corrective_on_fail,
                }))
        return commands

    def _load_from_template(self):
        for rec in self:
            if not rec.template_id:
                continue
            rec.template_version = rec.template_id.version
            rec.answer_ids = rec._build_answer_commands()

    def action_reload_template(self):
        for rec in self:
            if rec.state != "draft":
                raise ValidationError(
                    "%s is no longer in Draft; reloading would discard "
                    "recorded answers." % rec.name)
        self._load_from_template()

    # ---------------------------------------------------------- edit guard
    def _locked(self):
        return self.filtered(lambda r: r.state in ("issued", "locked",
                                                    "cancelled"))

    def write(self, vals):
        # Once issued, the content is frozen; only distribution/administrative
        # fields may change.
        allowed = {"distribution_ids", "distribution_log_ids",
                   "last_distributed", "state", "message_follower_ids",
                   "message_ids", "activity_ids"}
        if set(vals) - allowed and self._locked():
            raise ValidationError(
                "This report is issued and locked. Reopen it (admins) before "
                "editing, or file a new report.")
        return super().write(vals)

    # ------------------------------------------------------------ workflow
    def _validate_content(self):
        for rec in self:
            if not rec.answer_ids:
                raise ValidationError(
                    "%s has no questions. Pick a template first." % rec.name)
            problems = []
            for a in rec.answer_ids:
                label = "%s / %s" % (a.section_name or "", a.question_name or "")
                if a.required and not a.is_answered:
                    problems.append("%s — answer required" % label)
                    continue
                if a.requires_photo and not a.photo_ids:
                    problems.append("%s — photo required" % label)
                if (a.is_fail and a.corrective_on_fail
                        and not a.corrective_action):
                    problems.append("%s — corrective action required" % label)
            if problems:
                raise ValidationError(
                    "%s cannot be completed yet:\n- %s"
                    % (rec.name, "\n- ".join(problems)))

    def _validate_signatures(self):
        for rec in self:
            crew = rec.signature_ids.filtered(
                lambda s: s.role == "crew" and s.has_mark)
            sup = rec.signature_ids.filtered(
                lambda s: s.role == "supervisor" and s.has_mark)
            missing = []
            if not crew:
                missing.append("at least one crew signature")
            if not sup:
                missing.append("a supervisor signature")
            if missing:
                raise ValidationError(
                    "%s cannot be issued without %s (each signer needs a "
                    "drawn signature or a typed name)."
                    % (rec.name, " and ".join(missing)))

    def action_complete(self):
        self._validate_content()
        self.filtered(lambda r: r.state == "draft").write({"state": "complete"})

    def action_issue(self):
        self._validate_content()
        self._validate_signatures()
        for rec in self:
            if rec.state not in ("draft", "complete"):
                continue
            rec.state = "issued"
            rec.message_post(
                body=Markup("<p><strong>%s</strong> issued — result: %s.</p>")
                % (rec.name, dict(rec._fields["overall_result"].selection).get(
                    rec.overall_result, "")))

    def action_lock(self):
        for rec in self:
            if rec.state != "issued":
                raise ValidationError(
                    "%s must be issued before it can be locked." % rec.name)
            rec.state = "locked"

    def action_reset_to_draft(self):
        # Restricted to admins/safety leads via the button's groups.
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    # --------------------------------------------------------- distribution
    def _render_pdf(self):
        self.ensure_one()
        pdf, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            "cs_hse_templates.report_cs_safety", res_ids=self.ids)
        return self.env["ir.attachment"].create({
            "name": "%s.pdf" % (self.name or "Safety Report"),
            "type": "binary",
            "datas": base64.b64encode(pdf),
            "res_model": "cs.safety.report",
            "res_id": self.id,
            "mimetype": "application/pdf",
        })

    def _distribution_recipients(self):
        self.ensure_one()
        return self.distribution_ids.filtered(lambda p: p.email)

    def _do_distribute(self, resend=False):
        self.ensure_one()
        if self.state not in ("issued", "locked"):
            raise ValidationError(
                "%s must be issued before it can be distributed." % self.name)
        recipients = self._distribution_recipients()
        if not recipients:
            raise ValidationError(
                "%s has no recipient with an email address — add people to "
                "the Distribution list first." % self.name)
        attachment = self._render_pdf()
        body = Markup(
            "<p>Please find attached %ssafety report <strong>%s</strong> "
            "for <strong>%s</strong>%s.</p>") % (
            "re-issued " if resend else "", self.name,
            self.project_id.display_name or "",
            (": %s" % self.title) if self.title else "")
        self.message_post(
            body=body, subject="%s — %s" % (
                self.name, self.template_id.name or ""),
            partner_ids=recipients.ids, attachment_ids=attachment.ids,
            message_type="email", subtype_xmlid="mail.mt_comment")
        now = fields.Datetime.now()
        self.env["cs.safety.report.distribution"].create([{
            "report_id": self.id, "partner_id": p.id, "email": p.email,
            "date_sent": now, "sent_by_id": self.env.user.id,
            "note": "resend" if resend else "initial",
        } for p in recipients])
        self.last_distributed = now
        return recipients

    def action_distribute(self):
        for rec in self:
            recs = rec._do_distribute(resend=False)
        return self._notify("Report sent to %d recipient(s)." % len(recs))

    def action_resend(self):
        for rec in self:
            recs = rec._do_distribute(resend=True)
        return self._notify("Report re-sent to %d recipient(s)." % len(recs))

    def _notify(self, message):
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {"type": "success", "message": message,
                       "next": {"type": "ir.actions.act_window_close"}},
        }

    def unlink(self):
        for rec in self:
            if rec.state in ("issued", "locked"):
                raise ValidationError(
                    "%s is issued and part of the safety record; it cannot be "
                    "deleted. Cancel it instead." % rec.name)
        return super().unlink()


class CsSafetyReportAnswer(models.Model):
    _name = "cs.safety.report.answer"
    _description = "Safety Report Answer"
    _order = "sequence, id"

    report_id = fields.Many2one(
        "cs.safety.report", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    section_name = fields.Char(readonly=True)
    question_id = fields.Many2one(
        "cs.safety.template.question", ondelete="set null", readonly=True)
    question_name = fields.Char(string="Question", readonly=True)
    help_text = fields.Char(readonly=True)
    qtype = fields.Selection(QTYPE, readonly=True)
    required = fields.Boolean(readonly=True)
    requires_photo = fields.Boolean(readonly=True)
    corrective_on_fail = fields.Boolean(readonly=True)

    value_pfn = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail"), ("na", "N/A")], string="Result")
    value_yn = fields.Selection(
        [("yes", "Yes"), ("no", "No"), ("na", "N/A")], string="Answer")
    value_rating = fields.Selection(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        string="Rating")
    value_number = fields.Float(string="Value")
    value_text = fields.Text(string="Observation")
    comment = fields.Char()
    corrective_action = fields.Text()
    photo_ids = fields.Many2many(
        "ir.attachment", "cs_safety_answer_attachment_rel", "answer_id",
        "attachment_id", string="Photos")

    is_answered = fields.Boolean(compute="_compute_status", store=True)
    is_fail = fields.Boolean(compute="_compute_status", store=True)

    @api.depends("qtype", "value_pfn", "value_yn", "value_rating",
                 "value_number", "value_text")
    def _compute_status(self):
        for a in self:
            val = a._current_value()
            a.is_answered = bool(val not in (False, None, ""))
            a.is_fail = a.qtype in ("passfailna", "yesno") and (
                (a.value_pfn in FAIL_VALUES) or (a.value_yn in FAIL_VALUES))

    def _current_value(self):
        self.ensure_one()
        return {
            "passfailna": self.value_pfn,
            "yesno": self.value_yn,
            "rating": self.value_rating,
            "number": self.value_number if self.value_number else False,
            "text": self.value_text,
        }.get(self.qtype, False)

    def _guard(self):
        locked = self.mapped("report_id")._locked()
        if locked:
            raise ValidationError(
                "This report is issued and locked; its answers can't change.")

    def write(self, vals):
        # Photos and everything else are frozen once the report is issued.
        if self.mapped("report_id")._locked():
            self._guard()
        return super().write(vals)


class CsSafetyReportSignature(models.Model):
    _name = "cs.safety.report.signature"
    _description = "Safety Report Signature"
    _order = "role desc, id"

    report_id = fields.Many2one(
        "cs.safety.report", required=True, ondelete="cascade", index=True)
    role = fields.Selection(
        [("crew", "Crew"), ("supervisor", "Supervisor")],
        required=True, default="crew")
    signer_name = fields.Char(string="Name", required=True)
    user_id = fields.Many2one("res.users", string="User")
    signature = fields.Binary(string="Signature")
    signed_on = fields.Datetime(default=fields.Datetime.now)
    has_mark = fields.Boolean(compute="_compute_has_mark", store=True)

    @api.depends("signature", "signer_name")
    def _compute_has_mark(self):
        for s in self:
            s.has_mark = bool(s.signature) or bool(s.signer_name)


class CsSafetyReportDistribution(models.Model):
    _name = "cs.safety.report.distribution"
    _description = "Safety Report Distribution Record"
    _order = "date_sent desc, id desc"

    report_id = fields.Many2one(
        "cs.safety.report", required=True, ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", string="Recipient",
                                 required=True)
    email = fields.Char()
    date_sent = fields.Datetime(default=fields.Datetime.now)
    sent_by_id = fields.Many2one("res.users", string="Sent By")
    note = fields.Selection(
        [("initial", "Initial"), ("resend", "Re-sent")], default="initial")
