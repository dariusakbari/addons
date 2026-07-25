from odoo import api, fields, models


class GteMailActionMixin(models.AbstractModel):
    """Send actions + delivery-failure tracking for construction records.
    Inert until an outgoing mail server is configured; activates
    automatically once one exists."""

    _name = "gte.mail.action.mixin"
    _description = "GTE Mail Actions"

    gte_mail_bounced = fields.Boolean(
        string="Delivery Failed", compute="_compute_gte_mail_bounced",
        help="A message on this record failed to deliver (bounce or send "
             "error). Check the chatter and resend.")
    gte_last_sent_date = fields.Datetime(readonly=True, copy=False)

    _gte_mail_template_xmlid = None

    def _compute_gte_mail_bounced(self):
        Notif = self.env["mail.notification"]
        for rec in self:
            msg_ids = self.env["mail.message"].search(
                [("model", "=", rec._name), ("res_id", "=", rec.id)]).ids
            rec.gte_mail_bounced = bool(msg_ids) and bool(Notif.search_count([
                ("mail_message_id", "in", msg_ids),
                ("notification_status", "in", ("bounce", "exception")),
            ]))

    def _gte_open_composer(self, subject_suffix=None):
        self.ensure_one()
        template = self.env.ref(self._gte_mail_template_xmlid,
                                raise_if_not_found=False)
        ctx = {
            "default_model": self._name,
            "default_res_ids": self.ids,
            "default_template_id": template and template.id or False,
            "default_composition_mode": "comment",
        }
        if subject_suffix:
            ctx["gte_subject_suffix"] = subject_suffix
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form", "target": "new", "context": ctx,
        }

    def action_send_email(self):
        self.gte_last_sent_date = fields.Datetime.now()
        return self._gte_open_composer()

    def action_send_reminder(self):
        return self._gte_open_composer(subject_suffix="REMINDER")

    def action_resend_email(self):
        return self._gte_open_composer(subject_suffix="RESEND")


class GteRfi(models.Model):
    _name = "gte.rfi"
    _inherit = ["gte.rfi", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_rfi"

    @api.model
    def _cron_send_reminders(self):
        """Create a reminder activity for RFIs approaching or past their
        required date, within the configured lead window."""
        lead = int(self.env["ir.config_parameter"].sudo().get_param(
            "gte.rfi_reminder_days", "2") or 2)
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
    _name = "gte.change.order"
    _inherit = ["gte.change.order", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_co"


class GteSubmittal(models.Model):
    _name = "gte.submittal"
    _inherit = ["gte.submittal", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_submittal"

    @api.model
    def _cron_send_reminders(self):
        lead = int(self.env["ir.config_parameter"].sudo().get_param(
            "gte.submittal_reminder_days", "7") or 7)
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
    _name = "gte.daily.log"
    _inherit = ["gte.daily.log", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_dsl"


class GteTransmittal(models.Model):
    _name = "gte.transmittal"
    _inherit = ["gte.transmittal", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_transmittal"
