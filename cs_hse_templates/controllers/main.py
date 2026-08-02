from odoo import http
from odoo.http import request


class CsSafetyPortal(http.Controller):
    """Scan-to-start deep link used by the printed QR codes.

    A field user scans the QR, authenticates with their normal Odoo login,
    and lands on a fresh draft report for the chosen template. A safety report
    always needs a project, so if the QR did not carry a valid one we show a
    project-selection page instead of failing.
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

        project = request.env["project.project"]
        if project_id:
            try:
                project = project.browse(int(project_id)).exists()
            except (TypeError, ValueError):
                project = request.env["project.project"]

        if not project:
            # No / invalid / inaccessible project — let the user pick one
            # rather than erroring (project_id is required on the report).
            projects = request.env["project.project"].search([], order="name")
            return request.render(
                "cs_hse_templates.safety_pick_project",
                {"template": template, "projects": projects})

        # Create the draft using the user's own rights so access control and
        # multi-company rules apply normally.
        report = request.env["cs.safety.report"].create({
            "template_id": template.id, "project_id": project.id})
        return request.redirect(
            "/odoo/action-cs_hse_templates.action_cs_safety_report/%s"
            % report.id)
