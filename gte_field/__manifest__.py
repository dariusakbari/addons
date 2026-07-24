{
    "name": "GTE Field Operations",
    "summary": "Daily Site Logs with labour, quantities, photos, signature and supervisor review",
    "version": "19.0.0.1.0",
    "author": "Green Tech Electric",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["gte_core", "gte_hse"],
    "data": [
        "security/ir.model.access.csv",
        "security/gte_field_rules.xml",
        "views/gte_field_views.xml",
        "report/gte_field_reports.xml",
    ],
    "installable": True,
    "application": False,
}
