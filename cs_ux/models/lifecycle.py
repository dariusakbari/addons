from markupsafe import Markup


def build_lifecycle_html(steps, today):
    """Render a SmartBuild-style workflow timeline from derived steps.

    steps: list of dicts with keys name, due (date|False), done (bool),
    completed (date|False). The first not-done step is the current one
    ("Next", or "Overdue" if its due date has passed).
    """
    def fmt(d):
        return d.strftime("%d %b %Y") if d else "—"

    rows = []
    current_marked = False
    for s in steps:
        done = s.get("done")
        due = s.get("due")
        completed = s.get("completed")
        if done:
            badge = ('<span style="color:#1d6f4f;font-weight:600;">'
                     '✓ Done</span>')
            bg = "#e9f6ef"
        elif not current_marked:
            current_marked = True
            if due and due < today:
                badge = ('<span style="color:#c02a37;font-weight:600;">'
                         'Overdue</span>')
                bg = "#fdecec"
            else:
                badge = ('<span style="color:#9a6b00;font-weight:600;">'
                         'Next</span>')
                bg = "#fff5e5"
        else:
            badge = '<span style="color:#9aa0a6;">Pending</span>'
            bg = "#ffffff"
        rows.append(
            '<tr style="background:%s;border-bottom:1px solid #eceef0;">'
            '<td style="padding:7px 14px;font-weight:500;">%s</td>'
            '<td style="padding:7px 14px;">%s</td>'
            '<td style="padding:7px 14px;">%s</td>'
            '<td style="padding:7px 14px;">%s</td></tr>'
            % (bg, s["name"], fmt(due), fmt(completed), badge))

    return Markup(
        '<table style="width:100%;border-collapse:collapse;font-size:13px;'
        'border:1px solid #e7e9ec;border-radius:8px;overflow:hidden;">'
        '<tr style="text-align:left;color:#6b7280;background:#f6f7f9;">'
        '<th style="padding:7px 14px;">Step</th>'
        '<th style="padding:7px 14px;">Due</th>'
        '<th style="padding:7px 14px;">Completed</th>'
        '<th style="padding:7px 14px;">Status</th></tr>'
        + "".join(rows) + "</table>")
