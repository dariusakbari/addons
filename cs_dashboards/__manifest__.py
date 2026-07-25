{
    "name": "Construction Reporting & Dashboards",
    "summary": "Graph/pivot analytics, project & portfolio dashboards, "
               "and printable log reports for construction records",
    "version": "19.0.0.1.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "cs_field", "cs_hse", "cs_commercial", "project"],
    "data": [
        "report/cs_log_reports.xml",
        "views/cs_analytics_views.xml",
        "views/cs_dashboard_menus.xml",
    ],
    "installable": True,
    "application": False,
}
