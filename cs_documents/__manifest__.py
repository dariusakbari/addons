{
    "name": "Construction Documents & Drawings",
    "summary": "Construction document metadata and revision control (supersede, never overwrite)",
    "version": "19.0.0.4.0",
    "author": "Construction Suite",
    "license": "OPL-1",
    "category": "Construction",
    "depends": ["cs_controls", "documents"],
    "data": [
        "security/ir.model.access.csv",
        "views/cs_document_views.xml",
        "views/cs_drawing_views.xml",
        "report/cs_drawing_report.xml",
    ],
    "installable": True,
    "application": False,
}
