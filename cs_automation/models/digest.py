from datetime import timedelta

from markupsafe import Markup

from odoo import api, fields, models

BRAND_PRIMARY = "#0fa1af"
BRAND_SECONDARY = "#7daf42"


class CsWeeklyDigest(models.AbstractModel):
    """Builds and sends one consolidated 'outstanding items' email per project
    manager, on a weekly (Monday) cadence. Replaces the per-item reminder
    emails: the in-app activities still exist, but the email channel is a
    single weekly digest."""
    _name = "cs.weekly.digest"
    _description = "Weekly Outstanding-Items Digest"

    # -------------------------------------------------------------- recipients
    @api.model
    def _digest_managers(self):
        """Internal users who manage at least one project."""
        root = self.env.ref("base.user_root", raise_if_not_found=False)
        projects = self.env["project.project"].sudo().search([])
        users = projects.mapped("user_id").filtered(
            lambda u: u and u.active and not u.share
            and (not root or u.id != root.id))
        return users

    # ------------------------------------------------------------ gather items
    @api.model
    def _digest_sections(self, user):
        """Return [(title, [line, ...]), ...] of outstanding items on the
        projects this user manages. Each section is resilient: a missing model
        or field is skipped rather than breaking the digest."""
        today = fields.Date.context_today(self)
        d7 = today + timedelta(days=7)
        d14 = today + timedelta(days=14)
        d30 = today + timedelta(days=30)
        projects = self.env["project.project"].sudo().search(
            [("user_id", "=", user.id)])
        pids = projects.ids
        sections = []

        def gather(title, model, domain, fmt, limit=15):
            try:
                if model not in self.env:
                    return
                recs = self.env[model].sudo().search(
                    domain, limit=limit, order="id desc")
                if recs:
                    sections.append((title, len(recs), [fmt(r) for r in recs]))
            except Exception:
                # never let one section break the whole digest
                return

        proj = [("project_id", "in", pids)] if pids else [("id", "=", 0)]

        gather("RFIs overdue", "cs.rfi",
               proj + [("state", "in", ("draft", "open", "sent")),
                       ("date_required", "<", today)],
               lambda r: "%s — %s (due %s)" % (
                   r.name, r.subject or "", r.date_required or "—"))
        gather("RFIs due within 7 days", "cs.rfi",
               proj + [("state", "in", ("draft", "open", "sent")),
                       ("date_required", ">=", today),
                       ("date_required", "<=", d7)],
               lambda r: "%s — %s (due %s)" % (
                   r.name, r.subject or "", r.date_required or "—"))
        gather("Change orders awaiting decision", "cs.change.order",
               proj + [("state", "=", "submitted")],
               lambda r: "%s — %s" % (r.name, r.title or ""))
        gather("Submittals due within 7 days", "cs.submittal",
               proj + [("state", "in", ("draft", "requested", "received",
                                        "review", "submitted", "revise")),
                       ("date_required_submit", "<=", d7)],
               lambda r: "%s — %s (%s)" % (
                   r.name, r.title or "", r.date_required_submit or "—"))
        gather("Site instructions open", "cs.site.instruction",
               proj + [("state", "in", ("issued", "acknowledged"))],
               lambda r: "%s — %s" % (r.name, r.title or ""))
        gather("Delay events open", "cs.delay.event",
               proj + [("state", "=", "open")],
               lambda r: "%s — %s (%s days)" % (
                   r.name, dict(r._fields["cause"].selection).get(
                       r.cause, r.cause), r.days_impact or 0))
        gather("Punch/deficiency items open", "cs.punch.item",
               proj + [("state", "in", ("open", "in_progress", "verify"))],
               lambda r: "%s — %s" % (r.name, (r.description or "")[:60]))
        gather("Payment applications to action", "cs.payment.application",
               proj + [("state", "in", ("draft", "submitted"))],
               lambda r: "%s — %s" % (r.name, dict(
                   r._fields["state"].selection).get(r.state, r.state)))
        # Company-wide (not project-scoped) expiries
        gather("Work permits expiring within 14 days", "cs.work.permit",
               [("state", "=", "active"), ("valid_to", "<=", d14)],
               lambda r: "%s (valid to %s)" % (r.name, r.valid_to or "—"))
        gather("Certifications expiring within 30 days", "cs.worker.cert",
               [("expiry_date", "!=", False), ("expiry_date", "<=", d30)],
               lambda r: "%s — %s (%s)" % (
                   r.worker_name or "", r.cert_name or "", r.expiry_date or "—"))
        return sections, projects

    # ------------------------------------------------------------------ render
    @api.model
    def _digest_html(self, user, sections, projects):
        today = fields.Date.context_today(self)
        total = sum(n for _t, n, _l in sections)
        parts = []
        parts.append(
            "<div style='font-family:Montserrat,Arial,sans-serif;color:#222;'>")
        parts.append(
            "<div style='background:%s;color:#fff;padding:14px 18px;"
            "border-radius:6px 6px 0 0;'>"
            "<h2 style='margin:0;'>Weekly Outstanding Items</h2>"
            "<div style='opacity:.9;font-size:13px;'>Week of %s · %s</div></div>"
            % (BRAND_PRIMARY, today, user.name or ""))
        parts.append("<div style='padding:16px 18px;'>")
        if not total:
            parts.append(
                "<p style='font-size:15px;'>Nothing outstanding on your "
                "projects this week. \U0001F389</p>")
        else:
            parts.append(
                "<p style='font-size:14px;color:#555;'>%d item(s) across %d "
                "project(s). Full detail is in Odoo — this is your weekly "
                "summary.</p>" % (total, len(projects)))
            for title, n, lines in sections:
                parts.append(
                    "<h3 style='color:%s;margin:16px 0 4px;border-bottom:"
                    "2px solid %s;padding-bottom:3px;'>%s (%d)</h3>"
                    % (BRAND_SECONDARY, BRAND_SECONDARY, title, n))
                parts.append("<ul style='margin:4px 0;padding-left:20px;'>")
                for ln in lines:
                    parts.append("<li style='margin:2px 0;font-size:13px;'>"
                                 "%s</li>" % (ln or ""))
                parts.append("</ul>")
        parts.append(
            "<p style='margin-top:20px;font-size:11px;color:#999;'>"
            "You receive this weekly digest instead of per-item emails. "
            "Real-time alerts still appear in Odoo.</p>")
        parts.append("</div></div>")
        return Markup("".join(parts))

    # ------------------------------------------------------------------ send
    @api.model
    def _send_one(self, user):
        sections, projects = self._digest_sections(user)
        email = (user.partner_id.email or user.email) if user.partner_id else \
            user.email
        if not email:
            return False
        html = self._digest_html(user, sections, projects)
        company = self.env.company
        mail = self.env["mail.mail"].sudo().create({
            "subject": "Weekly outstanding items — %s"
                       % fields.Date.context_today(self),
            "body_html": html,
            "email_to": email,
            "email_from": company.email or company.partner_id.email
            or "notifications@greentechelectric.ca",
            "auto_delete": True,
        })
        mail.send()
        return True

    @api.model
    def _cron_send(self):
        for user in self._digest_managers():
            self._send_one(user)
