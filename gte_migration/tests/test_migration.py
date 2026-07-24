from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGteMigration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "M100 Mig Test"})
        cls.tag = cls.env["project.tags"].create({"name": "RFI"}) \
            if not cls.env["project.tags"].search([("name", "=", "RFI")]) \
            else cls.env["project.tags"].search([("name", "=", "RFI")], limit=1)
        cls.task = cls.env["project.task"].create({
            "name": "RFI 48 — Emergency Lighting",
            "project_id": cls.project.id,
            "tag_ids": [(4, cls.tag.id)],
            "description": "<p>SmartBuild RFI #48</p>"
                           "<p>Received: 06/03/2026 Next step: Distribute</p>",
        })

    def _run(self, dry=False):
        wiz = self.env["gte.migration.wizard"].create({"dry_run": dry})
        wiz.action_run()
        return wiz

    def test_idempotent_and_non_destructive(self):
        before_desc = self.task.description
        self._run(dry=False)
        rfis = self.env["gte.rfi"].search([("origin_task_id", "=", self.task.id)])
        self.assertEqual(len(rfis), 1)
        self.assertEqual(rfis.legacy_source_id, "SB-RFI-48")
        self.assertTrue(rfis.migration_incomplete)
        self.assertIn("raised_by_id", rfis.migration_missing_fields)
        # rerun creates no duplicates
        self._run(dry=False)
        rfis = self.env["gte.rfi"].search([("origin_task_id", "=", self.task.id)])
        self.assertEqual(len(rfis), 1)
        # original task untouched
        self.assertEqual(self.task.description, before_desc)
        self.assertTrue(self.task.active)

    def test_dry_run_writes_nothing(self):
        self._run(dry=True)
        self.assertFalse(
            self.env["gte.rfi"].search([("origin_task_id", "=", self.task.id)]))
