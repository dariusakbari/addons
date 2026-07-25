{
    "name": "GTE Construction Portal",
    "summary": "Share RFIs, submittals and transmittals with external "
               "consultants, clients and suppliers; log their responses",
    "version": "19.0.0.1.0",
    "author": "Green Tech Electric",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["gte_controls", "gte_field", "portal"],
    "data": [
        "security/gte_portal_groups.xml",
        "security/ir.model.access.csv",
        "security/gte_portal_rules.xml",
        "views/gte_portal_share_views.xml",
        "views/gte_portal_templates.xml",
    ],
    "installable": True,
}
