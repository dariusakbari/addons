from odoo import fields, models
from odoo.exceptions import ValidationError


class GteReasonWizard(models.TransientModel):
    """Mandatory-reason gate for cancelling, reopening or force-overriding
    a workflow. The reason is posted permanently to the record chatter."""

    _name = "cs.reason.wizard"
    _description = "Workflow Reason"

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    action = fields.Selection([
        ("cancel", "Cancel"), ("reopen", "Reopen"),
        ("override", "Administrator Override")], required=True)
    target_state = fields.Char(help="Only for administrator override.")
    reason = fields.Text(required=True)

    def action_apply(self):
        self.ensure_one()
        if not (self.reason or "").strip():
            raise ValidationError("A reason is required.")
        record = self.env[self.res_model].browse(self.res_id)
        label = dict(self._fields["action"].selection)[self.action]
        if self.action == "cancel":
            record.with_context(cs_reason=self.reason).action_cancel()
        elif self.action == "reopen":
            record.with_context(cs_reason=self.reason).action_reopen()
        elif self.action == "override":
            if not self.env.user.has_group("cs_core.group_cs_admin"):
                raise ValidationError(
                    "Only Construction Administrators may override workflows.")
            if not self.target_state:
                raise ValidationError("Override needs a target state.")
            record.write({"state": self.target_state})
        record.message_post(body="%s by %s — reason: %s" % (
            label, self.env.user.name, self.reason))
        return {"type": "ir.actions.act_window_close"}
