{
    "name": "GTE Migration",
    "summary": "Idempotent migration of tagged tasks and legacy data into GTE control models",
    "version": "19.0.0.1.0",
    "author": "Green Tech Electric",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["gte_controls"],
    "data": [
        "security/ir.model.access.csv",
        "views/migration_views.xml",
    ],
    "installable": True,
}
