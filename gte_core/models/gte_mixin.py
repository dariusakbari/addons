from odoo import api, fields, models


class GteLegacyMixin(models.AbstractModel):
    """Shared fields for every GTE construction-control record.

    Carries the legacy-source identifier and the migration-completeness
    flag required by the remediation safeguards. Never fabricate values:
    when mandatory data is missing, set migration_incomplete and list the
    missing fields instead.
    """

    _name = "gte.legacy.mixin"
    _description = "GTE Legacy Source Mixin"

    legacy_source_id = fields.Char(
        string="Legacy Source ID", copy=False, index=True,
        help="Identifier of the originating SmartBuild / legacy Odoo record.")
    origin_task_id = fields.Many2one(
        "project.task", string="Original Task", copy=False, ondelete="set null",
        help="Tagged project.task this record was migrated from. The task is "
             "kept (archived after reconciliation), never deleted.")
    migration_incomplete = fields.Boolean(copy=False, default=False, index=True)
    migration_missing_fields = fields.Text(copy=False)

    @api.model
    def _gte_next_number(self, project, code, prefix):
        """Project-scoped sequence, created on first use. Idempotent."""
        seq_code = "%s.p%s" % (code, project.id)
        seq = self.env["ir.sequence"].sudo().search(
            [("code", "=", seq_code)], limit=1)
        if not seq:
            seq = self.env["ir.sequence"].sudo().create({
                "name": "%s %s" % (prefix, project.display_name),
                "code": seq_code,
                "prefix": prefix + "-",
                "padding": 3,
                "company_id": project.company_id.id or False,
            })
        return seq.next_by_id()
