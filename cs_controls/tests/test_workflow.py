from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, AccessError


@tagged("post_install", "-at_install")
class TestConstructionWorkflow(TransactionCase):
    """Server-side validation gates + role access for the Construction Suite."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "TC Project"})
        cls.partner = cls.env["res.partner"].create(
            {"name": "TC Client", "is_company": True})

        def mkuser(login, group_xmlid):
            return cls.env["res.users"].create({
                "name": login, "login": login,
                "group_ids": [(6, 0, [
                    cls.env.ref("base.group_user").id,
                    cls.env.ref(group_xmlid).id])],
            })
        cls.user_field = mkuser("tc_field", "cs_core.group_cs_field")
        cls.user_pm = mkuser("tc_pm", "cs_core.group_cs_pm")
        cls.user_admin = mkuser("tc_admin", "cs_core.group_cs_admin")

    # ---- workflow gates -------------------------------------------------
    def test_co_submit_requires_pricing(self):
        co = self.env["cs.change.order"].create({
            "project_id": self.project.id, "title": "TC CO",
            "state": "review"})
        with self.assertRaises(ValidationError):
            co.action_submit()

    def test_co_approve_requires_reference(self):
        co = self.env["cs.change.order"].create({
            "project_id": self.project.id, "title": "TC CO",
            "state": "submitted", "amount_submitted": 1000.0,
            "amount_proposed": 1000.0})
        with self.assertRaises(ValidationError):
            co.action_approve()

    def test_submittal_close_requires_outcome(self):
        sub = self.env["cs.submittal"].create({
            "project_id": self.project.id, "title": "TC SUB"})
        with self.assertRaises(ValidationError):
            sub.action_close()

    # ---- change-order approval threshold --------------------------------
    def test_co_threshold_blocks_non_admin(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "cs.co_approval_limit", "10000")
        co = self.env["cs.change.order"].create({
            "project_id": self.project.id, "title": "TC big CO",
            "partner_id": self.partner.id, "state": "submitted",
            "amount_submitted": 20000.0, "amount_proposed": 20000.0,
            "amount_approved": 20000.0, "approval_reference": "PO-1"})
        # A project manager (non-admin) cannot approve above the limit
        with self.assertRaises(ValidationError):
            co.with_user(self.user_pm).action_approve()
        # A construction administrator can
        co.with_user(self.user_admin).action_approve()
        self.assertEqual(co.state, "approved")

    # ---- role access ----------------------------------------------------
    def test_field_cannot_read_change_orders(self):
        co = self.env["cs.change.order"].create({
            "project_id": self.project.id, "title": "TC CO"})
        with self.assertRaises(AccessError):
            co.with_user(self.user_field).check_access("read")

    def test_field_cannot_create_rfi(self):
        with self.assertRaises(AccessError):
            self.env["cs.rfi"].with_user(self.user_field).create({
                "project_id": self.project.id, "subject": "TC RFI"})
