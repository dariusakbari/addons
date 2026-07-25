from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGtePortal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "P900 Portal Test"})
        cls.consultant = cls.env["res.partner"].create({"name": "Consultant X"})
        cls.other = cls.env["res.partner"].create({"name": "Outsider Y"})
        portal_group = cls.env.ref("base.group_portal")
        cls.portal_user = cls.env["res.users"].create({
            "name": "Portal Consultant", "login": "portal.consultant.test",
            "partner_id": cls.consultant.id, "groups_id": [(6, 0, [portal_group.id])],
        })
        cls.shared = cls.env["cs.rfi"].create({
            "subject": "Shared RFI", "project_id": cls.project.id,
            "cs_portal_partner_ids": [(4, cls.consultant.id)]})
        cls.private = cls.env["cs.rfi"].create({
            "subject": "Private RFI", "project_id": cls.project.id})

    def test_portal_sees_only_shared(self):
        RfiPortal = self.env["cs.rfi"].with_user(self.portal_user)
        visible = RfiPortal.search([])
        self.assertIn(self.shared, visible)
        self.assertNotIn(self.private, visible)

    def test_portal_cannot_write(self):
        rfi = self.shared.with_user(self.portal_user)
        with self.assertRaises(AccessError):
            rfi.write({"subject": "hacked"})

    def test_response_logging(self):
        self.shared._portal_log_response(self.consultant, "Use detail A-3.")
        self.assertEqual(self.shared.cs_portal_responded_by_id, self.consultant)
        self.assertIn("A-3", self.shared.cs_portal_response)
