from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGteControls(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "T100 Test Project"})
        cls.partner = cls.env["res.partner"].create({"name": "Consultant Co"})

    def test_rfi_numbering_and_flow(self):
        rfi1 = self.env["gte.rfi"].create({
            "subject": "Panel schedule conflict", "project_id": self.project.id})
        rfi2 = self.env["gte.rfi"].create({
            "subject": "Second question", "project_id": self.project.id})
        self.assertNotEqual(rfi1.name, rfi2.name)
        self.assertTrue(rfi1.name.startswith("RFI-"))
        rfi1.action_open()
        with self.assertRaises(ValidationError):
            rfi1.action_send()  # question + addressed_to missing
        rfi1.write({"question": "<p>Clarify circuit 12</p>",
                    "addressed_to_id": self.partner.id})
        rfi1.action_send()
        with self.assertRaises(ValidationError):
            rfi1.action_answer()  # response missing
        rfi1.response = "<p>Use drawing E-402 rev 2</p>"
        rfi1.action_answer()
        rfi1.distribution_ids = [(4, self.partner.id)]
        rfi1.action_distribute()
        rfi1.action_close()
        self.assertEqual(rfi1.state, "closed")

    def test_change_order_totals(self):
        co = self.env["gte.change.order"].create({
            "title": "Added receptacles L3", "project_id": self.project.id})
        self.env["gte.change.order.line"].create({
            "order_id": co.id, "section": "labour", "description": "Electrician",
            "quantity": 10, "unit_cost": 100.0, "markup_pct": 10.0, "tax_pct": 0.0})
        self.assertAlmostEqual(co.amount_proposed, 1100.0)
        co.action_price()
        co.action_review()
        co.action_submit()
        self.assertAlmostEqual(co.amount_submitted, 1100.0)
        co.action_approve()
        self.assertAlmostEqual(co.amount_approved, 1100.0)
        self.assertAlmostEqual(co.exposure, 1100.0)

    def test_submittal_revisions_never_overwrite(self):
        sub = self.env["gte.submittal"].create({
            "title": "Lighting fixtures", "project_id": self.project.id,
            "supplier_id": self.partner.id})
        sub.action_request()
        sub.action_receive()
        sub.action_review()
        sub.action_submit()
        self.assertEqual(len(sub.revision_ids), 1)
        sub.comments = "<p>Wrong lumen package</p>"
        sub.action_revise()
        self.assertEqual(sub.state, "revise")
        sub.action_request()
        sub.action_receive()
        sub.action_review()
        sub.action_submit()
        self.assertEqual(len(sub.revision_ids), 2)
        first = sub.revision_ids.sorted("revision")[0]
        self.assertEqual(first.outcome, "revise")  # prior revision retained

    def test_cross_project_uniqueness(self):
        other = self.env["project.project"].create({"name": "T200 Other"})
        r1 = self.env["gte.rfi"].create({"subject": "a", "project_id": self.project.id})
        r2 = self.env["gte.rfi"].create({"subject": "b", "project_id": other.id})
        self.assertTrue(r1.name and r2.name)
