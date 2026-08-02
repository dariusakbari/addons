{
    "name": "Construction HSE — Safety Report Templates",
    "summary": "Version-controlled safety report template library: toolbox "
               "talks, inspections, hazard assessments and checklists with "
               "pass/fail/N-A questions, corrective actions, required photos, "
               "crew + supervisor signatures, controlled PDF, QR entry and "
               "recipient history.",
    "version": "19.0.0.2.4",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_hse"],
    "external_dependencies": {"python": ["qrcode"]},
    "data": [
        "security/ir.model.access.csv",
        "security/cs_hse_templates_rules.xml",
        "views/safety_template_views.xml",
        "views/safety_report_views.xml",
        "wizard/safety_qr_wizard_views.xml",
        "report/safety_report_report.xml",
        "views/safety_portal_templates.xml",
        "views/safety_menus.xml",
        "data/safety_template_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
