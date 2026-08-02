from odoo import http
from odoo.http import request


class CsSafetyPortal(http.Controller):
    """Scan-to-start deep links for the printed safety QR codes.

    A posted QR always carries its project, so scanning takes the worker
    straight into a fresh report for that project — they never see a project
    picker. The picker only exists as a fallback for a QR that carried no
    project at all (and even then it lists real, active projects only).
    """

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _published_template(self, template_id):
        tpl = request.env["cs.safety.template"].browse(
            self._to_int(template_id)).exists()
        return tpl if (tpl and tpl.state == "published") else None

    @http.route("/safety/new", type="http", auth="user", website=False)
    def safety_new(self, template_id=None, project_id=None, **kw):
        template = self._published_template(template_id)
        if not template:
            return request.redirect("/odoo")

        # Project carried by the QR -> begin the form immediately.
        if project_id not in (None, "", "0", "false", "False"):
            project = request.env["project.project"].sudo().browse(
                self._to_int(project_id)).exists()
            if not project:
                return request.render(
                    "cs_hse_templates.safety_qr_invalid",
                    {"template": template})
            report = request.env["cs.safety.report"].create({
                "template_id": template.id, "project_id": project.id})
            return request.redirect(
                "/odoo/action-cs_hse_templates.action_cs_safety_report/%s"
                % report.id)

        # Fallback only for a project-less QR: pick from real active projects.
        projects = request.env["project.project"].search(
            [("active", "=", True), ("is_template", "=", False)], order="name")
        return request.render(
            "cs_hse_templates.safety_pick_project",
            {"template": template, "projects": projects})

    @http.route("/safety/qr_poster", type="http", auth="user", website=False)
    def safety_qr_poster(self, template_id=None, project_id=None, **kw):
        """A print-ready, project-specific QR poster to post on site."""
        template = self._published_template(template_id)
        project = request.env["project.project"].sudo().browse(
            self._to_int(project_id)).exists()
        if not template or not project:
            return request.redirect("/odoo")
        from odoo.addons.cs_hse.models.registers import _cs_make_qr
        qr = _cs_make_qr(template._qr_target_url(project_id=project.id))
        qr_uri = "data:image/png;base64,%s" % (qr.decode() if qr else "")
        return request.render("cs_hse_templates.safety_qr_poster", {
            "template": template, "project": project, "qr_uri": qr_uri})
