from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GteMailActionMixin(models.AbstractModel):
    """Send actions + delivery-failure tracking for construction records.
    Inert until an outgoing mail server is configured; activates
    automatically once one exists."""

    _name = "cs.mail.action.mixin"
    _description = "Construction Mail Actions"

    cs_mail_bounced = fields.Boolean(
        string="Delivery Failed", compute="_compute_cs_mail_bounced",
        help="A message on this record failed to deliver (bounce or send "
             "error). Check the chatter and resend.")
    cs_last_sent_date = fields.Datetime(readonly=True, copy=False)

    _cs_mail_template_xmlid = None

    def _compute_cs_mail_bounced(self):
        Notif = self.env["mail.notification"]
        for rec in self:
            msg_ids = self.env["mail.message"].search(
                [("model", "=", rec._name), ("res_id", "=", rec.id)]).ids
            rec.cs_mail_bounced = bool(msg_ids) and bool(Notif.search_count([
                ("mail_message_id", "in", msg_ids),
                ("notification_status", "in", ("bounce", "exception")),
            ]))

    # Report to auto-attach as a PDF on the outgoing email (report_name string).
    _cs_mail_report = None

    def _cs_mail_recipients(self):
        """Partners the email should go to. Defaults to the record's
        Distribution list plus its client/partner; models override to add
        their own primary contact (RFI addressed-to, Submittal supplier…)."""
        self.ensure_one()
        partners = self.env["res.partner"]
        if "distribution_ids" in self._fields:
            partners |= self.distribution_ids
        if "partner_id" in self._fields and self.partner_id:
            partners |= self.partner_id
        return partners

    def _cs_mail_attachment(self):
        """Render the record's PDF as an attachment, if a report is set."""
        self.ensure_one()
        if not self._cs_mail_report:
            return self.env["ir.attachment"]
        import base64 as _b64
        pdf, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            self._cs_mail_report, res_ids=self.ids)
        return self.env["ir.attachment"].create({
            "name": "%s.pdf" % (self.display_name or self._description),
            "type": "binary", "datas": _b64.b64encode(pdf),
            "res_model": self._name, "res_id": self.id,
            "mimetype": "application/pdf",
        })

    def _cs_open_composer(self, subject_suffix=None):
        self.ensure_one()
        recipients = self._cs_mail_recipients().filtered("email")
        # Only distribution-based records (RFI, Submittal, Change Order) must
        # have a recipient before sending; other records keep the old
        # template/manual behaviour.
        if "distribution_ids" in self._fields and not recipients:
            raise ValidationError(
                "%s has no email recipients. Add people to the Distribution "
                "list (with email addresses) — the client is included "
                "automatically — before sending." % (self.display_name or ""))
        template = self.env.ref(self._cs_mail_template_xmlid,
                                raise_if_not_found=False)
        ctx = {
            "default_model": self._name,
            "default_res_ids": self.ids,
            "default_template_id": template and template.id or False,
            "default_composition_mode": "comment",
        }
        if recipients:
            ctx["default_partner_ids"] = [(6, 0, recipients.ids)]
        attachment = self._cs_mail_attachment()
        if attachment:
            ctx["default_attachment_ids"] = [(6, 0, attachment.ids)]
        if subject_suffix:
            ctx["cs_subject_suffix"] = subject_suffix
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form", "target": "new", "context": ctx,
        }

    def action_send_email(self):
        self.cs_last_sent_date = fields.Datetime.now()
        return self._cs_open_composer()

    def action_send_reminder(self):
        return self._cs_open_composer(subject_suffix="REMINDER")

    def action_resend_email(self):
        return self._cs_open_composer(subject_suffix="RESEND")


class GteRfi(models.Model):
    _name = "cs.rfi"
    _inherit = ["cs.rfi", "cs.mail.action.mixin"]
    _cs_mail_template_xmlid = "cs_mail.mail_template_cs_rfi"
    _cs_mail_report = "cs_controls.report_cs_rfi"

    def _cs_mail_recipients(self):
        partners = super()._cs_mail_recipients()
        return partners | self.addressed_to_id

    @api.model
    def _cron_send_reminders(self):
        """Create a reminder activity for RFIs approaching or past their
        required date, within the configured lead window."""
        lead = int(self.env["ir.config_parameter"].sudo().get_param(
            "cs.rfi_reminder_days", "2") or 2)
        limit = fields.Date.add(fields.Date.context_today(self), days=lead)
        due = self.search([
            ("state", "in", ("open", "sent")),
            ("date_required", "!=", False),
            ("date_required", "<=", limit),
        ])
        for rec in due:
            existing = rec.activity_ids.filtered(
                lambda a: a.summary and a.summary.startswith("Reminder: RFI"))
            if not existing and rec.coordinator_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Reminder: RFI %s response due %s" % (
                        rec.name, rec.date_required),
                    date_deadline=rec.date_required,
                    user_id=rec.coordinator_id.id)


class GteChangeOrder(models.Model):
    _name = "cs.change.order"
    _inherit = ["cs.change.order", "cs.mail.action.mixin"]
    _cs_mail_template_xmlid = "cs_mail.mail_template_cs_co"
    _cs_mail_report = "cs_controls.report_cs_co"


class GteSubmittal(models.Model):
    _name = "cs.submittal"
    _inherit = ["cs.submittal", "cs.mail.action.mixin"]
    _cs_mail_template_xmlid = "cs_mail.mail_template_cs_submittal"
    _cs_mail_report = "cs_controls.report_cs_submittal"

    def _cs_mail_recipients(self):
        partners = super()._cs_mail_recipients()
        return partners | self.supplier_id | self.contractor_id

    @api.model
    def _cron_send_reminders(self):
        lead = int(self.env["ir.config_parameter"].sudo().get_param(
            "cs.submittal_reminder_days", "7") or 7)
        limit = fields.Date.add(fields.Date.context_today(self), days=lead)
        due = self.search([
            ("state", "in", ("requested", "received", "review")),
            ("date_required_onsite", "!=", False),
            ("date_required_onsite", "<=", limit),
        ])
        for rec in due:
            existing = rec.activity_ids.filtered(
                lambda a: a.summary and a.summary.startswith("Reminder: Submittal"))
            if not existing and rec.coordinator_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="Reminder: Submittal %s required on site %s" % (
                        rec.name, rec.date_required_onsite),
                    date_deadline=rec.date_required_onsite,
                    user_id=rec.coordinator_id.id)


class GteDailyLog(models.Model):
    _name = "cs.daily.log"
    _inherit = ["cs.daily.log", "cs.mail.action.mixin"]
    _cs_mail_template_xmlid = "cs_mail.mail_template_cs_dsl"


class GteTransmittal(models.Model):
    _name = "cs.transmittal"
    _inherit = ["cs.transmittal", "cs.mail.action.mixin"]
    _cs_mail_template_xmlid = "cs_mail.mail_template_cs_transmittal"
