from odoo.tests import TransactionCase, HttpCase, tagged
from odoo.exceptions import AccessError, ValidationError

# A valid 16x16 PNG so ir.attachment image validation accepts it.
PNG_16 = ("iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAGUlEQVR4nGM8"
          "YWPDQApgIkn1qIZRDUNKAwAGWAFg9Wg3vwAAAABJRU5ErkJggg==")


@tagged("post_install", "-at_install")
class TestSafetyTemplates(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "TEST-SAFE"})
        cls.partner = cls.env["res.partner"].create(
            {"name": "Safety Recipient", "email": "safe@example.com"})
        tpl = cls.env["cs.safety.template"].create({
            "name": "Unit Test Template", "code": "UT",
            "template_type": "inspection"})
        sec = cls.env["cs.safety.template.section"].create({
            "template_id": tpl.id, "name": "Checks", "sequence": 10})
        cls.env["cs.safety.template.question"].create([
            {"section_id": sec.id, "sequence": 10, "name": "PPE worn",
             "qtype": "passfailna"},
            {"section_id": sec.id, "sequence": 20, "name": "Guard photo",
             "qtype": "passfailna", "requires_photo": True},
            {"section_id": sec.id, "sequence": 30,
             "name": "Any uncontrolled hazard?", "qtype": "yesno",
             "yesno_pass": "no", "corrective_on_fail": True},
        ])
        tpl.action_publish()
        cls.template = tpl
        cls.safety_user = cls.env["res.users"].create({
            "name": "Safety Lead UT", "login": "safety_lead_ut",
            "groups_id": [(4, cls.env.ref("cs_core.group_cs_safety").id),
                          (4, cls.env.ref("base.group_user").id)]})
        cls.plain_user = cls.env["res.users"].create({
            "name": "Coordinator UT", "login": "coordinator_ut",
            "groups_id": [(4, cls.env.ref("cs_core.group_cs_coordinator").id),
                          (4, cls.env.ref("base.group_user").id)]})

    # -------------------------------------------------------------- helpers
    def _new_report(self):
        return self.env["cs.safety.report"].create({
            "template_id": self.template.id, "project_id": self.project.id})

    def _answer_pass(self, report):
        for a in report.answer_ids:
            if a.qtype == "passfailna":
                a.value_pfn = "pass"
            elif a.qtype == "yesno":
                a.value_yn = a.yesno_pass
        photo_ans = report.answer_ids.filtered("requires_photo")
        att = self.env["ir.attachment"].create(
            {"name": "p.png", "datas": PNG_16, "mimetype": "image/png"})
        photo_ans.photo_ids = [(4, att.id)]

    def _sign(self, report):
        self.env["cs.safety.report.signature"].create([
            {"report_id": report.id, "role": "crew", "signer_name": "Crew A"},
            {"report_id": report.id, "role": "supervisor",
             "signer_name": "Super B"}])

    def _issue(self, report):
        self._answer_pass(report)
        self._sign(report)
        report.action_issue()

    # ---------------------------------------------------------------- tests
    def test_01_open_published_template(self):
        """The template is a mail.thread: chatter reads/writes must work."""
        self.assertEqual(self.template.state, "published")
        # message_ids / message_post exercise mail.thread (the chatter source)
        self.assertIn("message_ids", self.template._fields)
        self.template.message_post(body="opened")
        self.assertTrue(self.template.message_ids)
        # reading the fields the form shows must not error
        self.assertEqual(self.template.question_count, 3)

    def test_02_qr_generation(self):
        url = self.template._qr_target_url(project_id=self.project.id)
        self.assertIn("/safety/new?template_id=%s" % self.template.id, url)
        self.assertIn("project_id=%s" % self.project.id, url)
        wiz = self.env["cs.safety.qr.wizard"].create({
            "template_id": self.template.id, "project_id": self.project.id})
        self.assertTrue(wiz.url.endswith("project_id=%s" % self.project.id))
        self.assertTrue(wiz.qr_image)  # qrcode lib present -> image produced

    def test_03_report_snapshots_template(self):
        r = self._new_report()
        self.assertEqual(len(r.answer_ids), 3)
        self.assertEqual(r.template_version, self.template.version)
        yn = r.answer_ids.filtered(lambda a: a.qtype == "yesno")
        self.assertEqual(yn.yesno_pass, "no")

    def test_04_yesno_scoring_is_configurable(self):
        r = self._new_report()
        yn = r.answer_ids.filtered(lambda a: a.qtype == "yesno")
        # passing answer is No -> answering No must NOT be a fail
        yn.value_yn = "no"
        self.assertFalse(yn.is_fail)
        # answering Yes IS a fail for this question
        yn.value_yn = "yes"
        self.assertTrue(yn.is_fail)
        # pass/fail question still fails on 'fail'
        pf = r.answer_ids.filtered(lambda a: a.qtype == "passfailna")[0]
        pf.value_pfn = "fail"
        self.assertTrue(pf.is_fail)
        pf.value_pfn = "pass"
        self.assertFalse(pf.is_fail)

    def test_05_fail_count_uses_expected_result(self):
        r = self._new_report()
        self._answer_pass(r)                      # all passing (hazard = No)
        self.assertEqual(r.fail_count, 0)
        self.assertEqual(r.overall_result, "pass")
        r.answer_ids.filtered(
            lambda a: a.qtype == "yesno").value_yn = "yes"   # now a fail
        self.assertEqual(r.fail_count, 1)
        self.assertEqual(r.overall_result, "attention")

    def test_06_required_signatures_before_issue(self):
        r = self._new_report()
        self._answer_pass(r)
        with self.assertRaises(ValidationError):
            r.action_issue()                      # no signatures yet
        self._sign(r)
        r.action_issue()
        self.assertEqual(r.state, "issued")

    def test_07_lock_makes_everything_readonly(self):
        r = self._new_report()
        self._issue(r)
        r.action_lock()
        self.assertEqual(r.state, "locked")
        # answers frozen
        with self.assertRaises(ValidationError):
            r.answer_ids[0].value_pfn = "fail"
        # photos frozen (write on answer m2m)
        with self.assertRaises(ValidationError):
            r.answer_ids.filtered("requires_photo").photo_ids = [(5, 0, 0)]
        # signatures frozen (create + write + unlink)
        with self.assertRaises(ValidationError):
            self.env["cs.safety.report.signature"].create(
                {"report_id": r.id, "role": "crew", "signer_name": "X"})
        with self.assertRaises(ValidationError):
            r.signature_ids[0].signer_name = "changed"
        # header fields frozen
        with self.assertRaises(ValidationError):
            r.location = "somewhere"

    def test_08_reopen_unlocks_and_is_logged(self):
        r = self._new_report()
        self._issue(r)
        before = len(r.message_ids)
        r.action_lock()
        r.action_reset_to_draft()
        self.assertEqual(r.state, "draft")
        # lock + reopen both posted to the chatter
        self.assertGreaterEqual(len(r.message_ids), before + 2)
        # editing works again after reopen
        r.answer_ids[0].value_pfn = "fail"
        self.assertEqual(r.answer_ids[0].value_pfn, "fail")

    def test_09_pdf_report_renders(self):
        r = self._new_report()
        self._issue(r)
        html, dummy = self.env["ir.actions.report"]._render_qweb_html(
            "cs_hse_templates.report_cs_safety", r.ids)
        self.assertIn(r.name.encode(), html)

    def test_10_distribution_and_resend(self):
        r = self._new_report()
        self._issue(r)
        r.distribution_ids = [(4, self.partner.id)]
        r.action_distribute()
        self.assertEqual(len(r.distribution_log_ids), 1)
        self.assertEqual(r.distribution_log_ids.note, "initial")
        self.assertTrue(r.last_distributed)
        r.action_resend()
        self.assertEqual(len(r.distribution_log_ids), 2)
        self.assertIn("resend", r.distribution_log_ids.mapped("note"))

    def test_11_seeded_templates_published(self):
        for xmlid in ("tpl_toolbox", "tpl_field_insp", "tpl_site_insp",
                      "tpl_hazard", "tpl_equipment"):
            tpl = self.env.ref("cs_hse_templates.%s" % xmlid)
            self.assertEqual(tpl.state, "published")
            self.assertTrue(tpl.question_count)

    def test_12_reopen_requires_permission(self):
        r = self._new_report()
        self._issue(r)
        r.action_lock()
        # a coordinator (not safety/admin) may not reopen
        with self.assertRaises(AccessError):
            r.with_user(self.plain_user).action_reset_to_draft()
        self.assertEqual(r.state, "locked")
        # a safety lead may, and it stays audited
        n = len(r.message_ids)
        r.with_user(self.safety_user).action_reset_to_draft()
        self.assertEqual(r.state, "draft")
        self.assertGreater(len(r.message_ids), n)

    def test_13_new_hazard_question_scores_correctly(self):
        """The seeded 'Any new hazards identified today?' passes on No, fails
        on Yes and is neutral on N/A, and the roll-up follows suit."""
        tpl = self.env.ref("cs_hse_templates.tpl_daily_inspection")
        r = self.env["cs.safety.report"].create({
            "template_id": tpl.id, "project_id": self.project.id})
        hz = r.answer_ids.filtered(
            lambda a: "new hazards identified" in (a.question_name or ""))
        self.assertEqual(len(hz), 1)
        self.assertEqual(hz.yesno_pass, "no")
        hz.value_yn = "no"
        self.assertFalse(hz.is_fail)
        hz.value_yn = "na"
        self.assertFalse(hz.is_fail)          # neutral
        hz.value_yn = "yes"
        self.assertTrue(hz.is_fail)           # failing
        self.assertGreaterEqual(r.fail_count, 1)
        self.assertEqual(r.overall_result, "attention")


@tagged("post_install", "-at_install")
class TestSafetyRoute(HttpCase):
    """The /safety/new QR deep link: valid project starts a report, a missing
    project falls back to a selection page instead of erroring."""

    def test_route_valid_and_missing_project(self):
        project = self.env["project.project"].create({"name": "RT-SAFE"})
        tpl = self.env.ref("cs_hse_templates.tpl_toolbox")
        user = self.env["res.users"].create({
            "name": "Route Tester", "login": "route_tester",
            "password": "route_tester_pw",
            "groups_id": [(4, self.env.ref("cs_core.group_cs_safety").id),
                          (4, self.env.ref("base.group_user").id)]})
        self.authenticate("route_tester", "route_tester_pw")
        Report = self.env["cs.safety.report"]
        base = Report.search_count([])
        # valid project -> a report is created (then redirected to the backend)
        self.url_open("/safety/new?template_id=%s&project_id=%s"
                      % (tpl.id, project.id))
        self.assertEqual(Report.search_count([]), base + 1)
        # missing project -> selection page, no report created
        resp = self.url_open("/safety/new?template_id=%s" % tpl.id)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Select the project", resp.content)
        self.assertEqual(Report.search_count([]), base + 1)
