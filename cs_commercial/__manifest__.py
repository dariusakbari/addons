{
    "name": "Construction Commercial & Resources",
    "summary": "Project budgets, restricted labour rates, worker certifications",
    "version": "19.0.0.11.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "analytic", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/cs_commercial_views.xml",
        "views/cs_payment_views.xml",
        "views/cs_purchase_views.xml",
        "report/cs_payment_report.xml",
    ],
    "installable": True,
    "application": False,
}
