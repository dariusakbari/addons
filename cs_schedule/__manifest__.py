{
    "name": "Construction Scheduling & Manpower",
    "summary": "Baseline vs forecast dates, delay events with schedule-impact "
               "roll-up, look-ahead schedules and a construction calendar",
    "version": "19.0.0.3.0",
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
    ],
    "installable": True,
    "application": False,
}
