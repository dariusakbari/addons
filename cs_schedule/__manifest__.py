{
    "name": "Construction Scheduling & Manpower",
    "summary": "Baseline vs forecast dates, delay events with schedule-impact "
               "roll-up, look-ahead schedules and a construction calendar",
    "version": "19.0.0.5.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "cs_field", "project"],
    "data": [
        "security/ir.model.access.csv",
        "security/cs_schedule_rules.xml",
        "views/cs_delay_views.xml",
        "views/cs_project_schedule_views.xml",
        "views/cs_schedule_menus.xml",
        "views/cs_lookahead_views.xml",
        "report/cs_lookahead_report.xml",
    ],
    "installable": True,
    "application": False,
}
