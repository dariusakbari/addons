from odoo import models


class GteMailActionMixin(models.AbstractModel):
    _name = "gte.mail.action.mixin"
    _description = "Open mail composer preloaded with the record's template"

    _gte_mail_template_xmlid = None

    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref(self._gte_mail_template_xmlid,
                                raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": self._name,
                "default_res_ids": self.ids,
                "default_template_id": template and template.id or False,
                "default_composition_mode": "comment",
            },
        }


class GteRfi(models.Model):
    _name = "gte.rfi"
    _inherit = ["gte.rfi", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_rfi"


class GteChangeOrder(models.Model):
    _name = "gte.change.order"
    _inherit = ["gte.change.order", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_co"


class GteSubmittal(models.Model):
    _name = "gte.submittal"
    _inherit = ["gte.submittal", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_submittal"


class GteDailyLog(models.Model):
    _name = "gte.daily.log"
    _inherit = ["gte.daily.log", "gte.mail.action.mixin"]
    _gte_mail_template_xmlid = "gte_mail.mail_template_gte_dsl"
