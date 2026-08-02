from odoo import fields, models


class CsSafetyReopenWizard(models.TransientModel):
    _name = "cs.safety.reopen.wizard"
    _description = "Reopen Safety Report"

    report_id = fields.Many2one(
        "cs.safety.report", string="Report", required=True, ondelete="cascade")
    reason = fields.Text(
        string="Reason for reopening", required=True,
        help="Recorded in the report's chatter with your name and the date.")

    def action_confirm(self):
        self.ensure_one()
        # Permission + audit logging all live in _do_reopen.
        self.report_id._do_reopen(self.reason)
        return {"type": "ir.actions.act_window_close"}
