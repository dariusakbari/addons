import base64
import io

from odoo import api, fields, models
from odoo.exceptions import UserError

BRAND_PRIMARY = "#0fa1af"
BRAND_SECONDARY = "#7daf42"


class CsXlsxExport(models.AbstractModel):
    """Spec-driven, brand-styled Excel export engine for the construction
    registers. Each register's list view exposes an "Export to Excel
    (branded)" action that funnels the selected records through here."""
    _name = "cs.xlsx.export"
    _description = "Branded Excel Export Engine"

    # ------------------------------------------------------------------ specs
    def _specs(self):
        return {
            "rfi": {
                "model": "cs.rfi",
                "title": "RFI Register",
                "columns": [
                    ("RFI No.", "name", "text"),
                    ("Subject", "subject", "text"),
                    ("Project", "project_id", "m2o"),
                    ("Status", "state", "sel"),
                    ("Raised", "date_raised", "date"),
                    ("Required", "date_required", "date"),
                    ("Answered", "date_answered", "date"),
                    ("Coordinator", "coordinator_id", "m2o"),
                    ("Cost Impact", "cost_amount", "money"),
                ],
            },
            "change_order": {
                "model": "cs.change.order",
                "title": "Change Order Log",
                "columns": [
                    ("CO No.", "name", "text"),
                    ("Title", "title", "text"),
                    ("Project", "project_id", "m2o"),
                    ("Status", "state", "sel"),
                    ("Proposed", "amount_proposed", "money"),
                    ("Approved", "amount_approved", "money"),
                    ("Exposure", "exposure", "money"),
                    ("Schedule (d)", "schedule_days", "int"),
                    ("Decision", "date_decision", "date"),
                ],
            },
            "submittal": {
                "model": "cs.submittal",
                "title": "Submittal Log",
                "columns": [
                    ("Submittal No.", "name", "text"),
                    ("Title", "title", "text"),
                    ("Project", "project_id", "m2o"),
                    ("Spec Section", "spec_section", "text"),
                    ("Status", "state", "sel"),
                    ("Outcome", "outcome", "sel"),
                    ("Req. Submission", "date_required_submit", "date"),
                    ("Returned", "date_returned", "date"),
                ],
            },
            "drawing": {
                "model": "cs.drawing",
                "title": "Drawing & Document Register",
                "columns": [
                    ("Doc No.", "cs_doc_number", "text"),
                    ("Title", "title", "text"),
                    ("Project", "project_id", "m2o"),
                    ("Type", "doc_type", "sel"),
                    ("Discipline", "discipline", "sel"),
                    ("Rev", "revision", "text"),
                    ("Status", "status", "sel"),
                    ("Issued", "issue_date", "date"),
                ],
            },
            "site_instruction": {
                "model": "cs.site.instruction",
                "title": "Site Instruction Register",
                "columns": [
                    ("SI No.", "name", "text"),
                    ("Title", "title", "text"),
                    ("Project", "project_id", "m2o"),
                    ("Issued To", "issued_to_id", "m2o"),
                    ("Status", "state", "sel"),
                    ("Issued", "date_issued", "date"),
                    ("Required By", "required_by", "date"),
                    ("Cost Impact", "cost_amount", "money"),
                ],
            },
            "payment_application": {
                "model": "cs.payment.application",
                "title": "Payment Applications",
                "columns": [
                    ("Application", "name", "text"),
                    ("Project", "project_id", "m2o"),
                    ("Period To", "period_end", "date"),
                    ("% Complete", "percent_complete", "int"),
                    ("Completed", "completed_to_date", "money"),
                    ("Holdback", "holdback_to_date", "money"),
                    ("Current Due", "current_due", "money"),
                    ("Status", "state", "sel"),
                ],
            },
        }

    # ------------------------------------------------------------------ values
    def _cell(self, rec, field, kind):
        f = rec._fields.get(field)
        if not f:
            return "" if kind not in ("money", "int") else 0
        raw = rec[field]
        if kind == "money":
            return float(raw or 0.0)
        if kind == "int":
            return float(raw or 0)
        if kind == "date":
            return raw or ""
        if kind == "m2o":
            return raw.display_name if raw else ""
        if kind == "sel":
            try:
                return dict(f._description_selection(rec.env)).get(raw, raw or "")
            except Exception:
                return raw or ""
        return raw or ""

    # ------------------------------------------------------------------ build
    @api.model
    def build_xlsx(self, key, records):
        try:
            import xlsxwriter
        except ImportError:
            raise UserError("xlsxwriter is not available on this server.")
        spec = self._specs().get(key)
        if not spec:
            raise UserError("Unknown export '%s'." % key)
        cols = spec["columns"]
        ncol = len(cols)
        company = self.env.company

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {"in_memory": True})
        ws = wb.add_worksheet(spec["title"][:31])

        f_title = wb.add_format({"bold": True, "font_size": 15,
                                 "font_color": "#FFFFFF",
                                 "bg_color": BRAND_PRIMARY, "valign": "vcenter",
                                 "indent": 1})
        f_sub = wb.add_format({"italic": True, "font_color": "#777777"})
        f_hdr = wb.add_format({"bold": True, "font_color": "#FFFFFF",
                               "bg_color": BRAND_SECONDARY, "border": 1,
                               "align": "center", "valign": "vcenter"})
        f_txt = wb.add_format({"border": 1, "valign": "top"})
        f_money = wb.add_format({"border": 1, "num_format": "#,##0.00"})
        f_int = wb.add_format({"border": 1, "num_format": "0"})
        f_date = wb.add_format({"border": 1, "num_format": "yyyy-mm-dd"})
        f_totlbl = wb.add_format({"bold": True, "border": 1,
                                  "bg_color": "#EEEEEE"})
        f_tot = wb.add_format({"bold": True, "border": 1,
                               "num_format": "#,##0.00", "bg_color": "#EEEEEE"})

        ws.merge_range(0, 0, 0, ncol - 1,
                       "%s  —  %s" % (company.name, spec["title"]), f_title)
        ws.set_row(0, 28)
        ws.write(1, 0, "Generated %s by %s  ·  %d record(s)" % (
            fields.Datetime.now().strftime("%Y-%m-%d %H:%M"),
            self.env.user.name, len(records)), f_sub)

        hdr_row = 3
        for c, (label, _f, _k) in enumerate(cols):
            ws.write(hdr_row, c, label, f_hdr)

        money_cols = {c for c, (l, f, k) in enumerate(cols) if k == "money"}
        totals = dict.fromkeys(money_cols, 0.0)
        r = hdr_row + 1
        for rec in records:
            for c, (label, field, kind) in enumerate(cols):
                val = self._cell(rec, field, kind)
                if kind == "money":
                    ws.write_number(r, c, float(val or 0.0), f_money)
                    totals[c] += float(val or 0.0)
                elif kind == "int":
                    ws.write_number(r, c, float(val or 0), f_int)
                elif kind == "date":
                    ws.write(r, c, val.strftime("%Y-%m-%d") if val else "",
                             f_date)
                else:
                    ws.write(r, c, val or "", f_txt)
            r += 1

        if money_cols:
            ws.write(r, 0, "Totals", f_totlbl)
            for c in range(1, ncol):
                if c in money_cols:
                    ws.write_number(r, c, totals[c], f_tot)
                else:
                    ws.write(r, c, "", f_totlbl)

        for c, (label, field, kind) in enumerate(cols):
            ws.set_column(c, c, 24 if kind in ("text", "m2o") else 15)
        ws.freeze_panes(hdr_row + 1, 0)
        wb.close()
        return output.getvalue()

    # ------------------------------------------------------------------ action
    @api.model
    def action_export(self, key, records):
        if not records:
            raise UserError("Select at least one record to export.")
        spec = self._specs()[key]
        data = self.build_xlsx(key, records)
        fname = "%s %s.xlsx" % (spec["title"], fields.Date.context_today(self))
        att = self.env["ir.attachment"].create({
            "name": fname,
            "type": "binary",
            "datas": base64.b64encode(data),
            "mimetype": "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet",
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % att.id,
            "target": "self",
        }
