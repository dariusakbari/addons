{
    "name": "Construction Portal",
    "summary": "Share RFIs, submittals and transmittals with external "
               "consultants, clients and suppliers; log their responses",
    "version": "19.0.0.1.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "cs_field", "portal"],
    "data": [
        "security/cs_portal_groups.xml",
        "security/ir.model.access.csv",
        "security/cs_portal_rules.xml",
        "views/cs_portal_share_views.xml",
        "views/cs_portal_templates.xml",
    ],
    "installable": True,
}
