from datetime import timedelta

from odoo import api, fields, models

# rule_type -> (model, date_field, open-state domain, activity label)
PRESETS = {
    "rfi_due": ("cs.rfi", "date_required",
                [("state", "in", ("draft", "open", "sent", "answered"))],
                "RFI response due"),
    "sub_due": ("cs.submittal", "date_required_submit",
                [("state", "in", ("draft", "requested", "received", "review",
                                  "submitted", "revise"))],
                "Submittal due"),
    "co_decision": ("cs.change.order", "date_required",
                    [("state", "=", "submitted")],
                    "Change order decision due"),
    "permit_expiry": ("cs.work.permit", "valid_to",
                      [("state", "=", "active")], "Work permit expiring"),
    "cert_expiry": ("cs.worker.cert", "expiry_date", [],
                    "Certification expiring"),
}


class CsEscalationRule(models.Model):
    _name = "cs.escalation.rule"
    _description = "Construction Escalation Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    rule_type = fields.Selection(
        [("rfi_due", "RFI — required response date"),
         ("sub_due", "Submittal — required submission"),
         ("co_decision", "Change order — required decision"),
         ("permit_expiry", "Work permit — valid-to date"),
         ("cert_expiry", "Worker certification — expiry")],
        required=True)
    timing = fields.Selection(
        [("before", "Days before the date (reminder)"),
         ("after", "Days after the date (overdue)")],
        default="before", required=True)
    days = fields.Integer(string="Days", default=2,
                          help="Lead time (before) or overdue threshold (after).")
    notify = fields.Selection(
        [("pm", "Project manager"),
         ("responsible", "Record's responsible person"),
         ("specific", "A specific user")],
        default="pm", required=True)
    user_id = fields.Many2one("res.users", string="Notify user")
    active = fields.Boolean(default=True)

    def _resolve_user(self, rec):
        """Who gets the activity for a given record under this rule."""
        self.ensure_one()
        if self.notify == "specific" and self.user_id:
            return self.user_id
        if (self.notify == "responsible" and "responsible_id" in rec._fields
                and rec.responsible_id):
            return rec.responsible_id
        if "project_id" in rec._fields and rec.project_id.user_id:
            return rec.project_id.user_id
        if "responsible_id" in rec._fields and rec.responsible_id:
            return rec.responsible_id
        return rec.create_uid

    @api.model
    def _cron_run(self):
        today = fields.Date.context_today(self)
        for rule in self.search([("active", "=", True)]):
            preset = PRESETS.get(rule.rule_type)
            if not preset:
                continue
            model, date_field, open_domain, label = preset
            Model = self.env[model]
            if date_field not in Model._fields:
                continue
            if rule.timing == "before":
                hi = today + timedelta(days=rule.days or 0)
                domain = list(open_domain) + [(date_field, ">=", today),
                                              (date_field, "<=", hi)]
            else:
                cutoff = today - timedelta(days=rule.days or 0)
                domain = list(open_domain) + [(date_field, "<", cutoff)]
            marker = "[esc%s]" % rule.id
            for rec in Model.search(domain):
                user = rule._resolve_user(rec)
                if not user:
                    continue
                if self.env["mail.activity"].search_count([
                        ("res_model", "=", model), ("res_id", "=", rec.id),
                        ("summary", "like", marker)]):
                    continue
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary="%s %s" % (label, marker),
                    note=rule.name, user_id=user.id)
