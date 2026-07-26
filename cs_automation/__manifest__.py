{
    "name": "Construction Automation & Escalations",
    "summary": "Configurable reminder/escalation engine for construction "
               "records (RFIs, submittals, change orders, permits, certs)",
    "version": "19.0.0.2.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "cs_field", "cs_hse", "cs_commercial",
                "cs_schedule"],
    "data": [
        "security/ir.model.access.csv",
        "views/cs_escalation_views.xml",
        "data/cs_escalation_rules.xml",
        "data/cs_digest_cron.xml",
    ],
    "post_init_hook": "_cs_automation_post_init",
    "installable": True,
    "application": False,
}
