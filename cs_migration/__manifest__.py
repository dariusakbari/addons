{
    "name": "Construction Migration",
    "summary": "Idempotent migration of tagged tasks and legacy data into Construction control models",
    "version": "19.0.0.1.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls"],
    "data": [
        "security/ir.model.access.csv",
        "views/migration_views.xml",
    ],
    "installable": True,
}
