{
    "name": "Construction Commercial & Resources",
    "summary": "Project budgets, restricted labour rates, worker certifications",
    "version": "19.0.0.5.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "analytic"],
    "data": [
        "security/ir.model.access.csv",
        "views/cs_commercial_views.xml",
        "views/cs_payment_views.xml",
        "report/cs_payment_report.xml",
    ],
    "installable": True,
    "application": False,
}
