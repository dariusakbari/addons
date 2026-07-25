{
    "name": "Construction Reporting & Dashboards",
    "summary": "Graph/pivot analytics, project & portfolio dashboards, "
               "and printable log reports for construction records",
    "version": "19.0.0.7.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "cs_field", "cs_hse", "cs_commercial", "project"],
    "data": [
        "report/cs_log_reports.xml",
        "views/cs_analytics_views.xml",
        "views/cs_dashboard_client.xml",
        "views/cs_dashboard_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cs_dashboards/static/src/dashboard.js",
            "cs_dashboards/static/src/dashboard.xml",
            "cs_dashboards/static/src/dashboard.scss",
        ],
    },
    "post_init_hook": "_cs_dashboards_post_init",
    "installable": True,
    "application": False,
}
