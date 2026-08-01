from odoo import http
from odoo.http import request


class CsSafetyPortal(http.Controller):
    """Scan-to-start deep link used by the printed QR codes.

    A field user scans the QR, authenticates with their normal Odoo login,
    and lands on a fresh draft report for the chosen template (pre-scoped to
    a project when the QR carried one). This keeps mobile entry to one tap.
    """

    @http.route("/safety/new", type="http", auth="user", website=False)
    def safety_new(self, template_id=None, project_id=None, **kw):
        try:
            tpl_id = int(template_id)
        except (TypeError, ValueError):
            return request.redirect("/odoo")

        template = request.env["cs.safety.template"].browse(tpl_id).exists()
        if not template or template.state != "published":
            return request.redirect("/odoo")

        vals = {"template_id": template.id}
        if project_id:
            try:
                proj = request.env["project.project"].browse(
                    int(project_id)).exists()
                if proj:
                    vals["project_id"] = proj.id
            except (TypeError, ValueError):
                pass

        # Create the draft using the user's own rights (no sudo), so access
        # control and multi-company rules apply normally.
        report = request.env["cs.safety.report"].create(vals)
        return request.redirect(
            "/odoo/action-cs_hse_templates.action_cs_safety_report/%s"
            % report.id)
