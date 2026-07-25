from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cs_mail_ready = fields.Boolean(compute="_compute_cs_mail_diag")
    cs_mail_diag = fields.Html(compute="_compute_cs_mail_diag",
                                string="Construction Mail Readiness")

    @api.depends_context("uid")
    def _compute_cs_mail_diag(self):
        out_n = self.env["ir.mail_server"].sudo().search_count([])
        in_n = self.env["fetchmail.server"].sudo().search_count([]) \
            if "fetchmail.server" in self.env else 0
        alias_dom = self.env["mail.alias.domain"].sudo().search_count([]) \
            if "mail.alias.domain" in self.env else 0
        templates = self.env["mail.template"].sudo().search_count(
            [("name", "in", ["RFI: Send to Consultant",
                              "Change Order: Submit to Client",
                              "Submittal: Request from Supplier",
                              "Daily Site Log: Distribute"])])
        rows = [
            ("Outgoing mail server", out_n, "Required to send RFIs, COs, "
             "submittals and reports."),
            ("Incoming mail server", in_n, "Required for consultant replies "
             "to attach back to the record."),
            ("Alias domain", alias_dom, "Required for per-record reply "
             "routing (e.g. rfi@greentechelectric.ca)."),
            ("Construction templates", templates, "Editable in Settings → "
             "Technical → Email Templates."),
        ]
        ready = out_n > 0
        for rec in self:
            rec.cs_mail_ready = ready
            html = ["<table class='table table-sm'>"]
            for label, n, hint in rows:
                ok = n > 0
                badge = ("<span class='badge text-bg-success'>OK (%s)</span>" % n
                         if ok else
                         "<span class='badge text-bg-danger'>NOT SET</span>")
                html.append(
                    "<tr><td><strong>%s</strong></td><td>%s</td>"
                    "<td class='text-muted'>%s</td></tr>" % (label, badge, hint))
            html.append("</table>")
            if not ready:
                html.append(
                    "<div class='alert alert-warning'>No outgoing mail server "
                    "is configured — all construction email actions are "
                    "inactive. Configure a server in Settings → Technical → "
                    "Outgoing Mail Servers to activate them.</div>")
            rec.cs_mail_diag = "".join(html)
