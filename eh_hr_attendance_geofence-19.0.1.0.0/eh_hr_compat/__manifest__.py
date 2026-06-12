# -*- coding: utf-8 -*-
{
    'name': 'EH HR Compatibility',
    'summary': 'Version compatibility shims for the EH HR Platform (Odoo 16/17/18/19).',
    'description': """
HR Platform compatibility layer
================================
This module is intentionally tiny. It contains NO business logic and NO state.
Its job is to normalise the parts of the Odoo API that change between minor
versions so the feature modules in eh_hr_platform/* can stay version-agnostic.

Public surface:
    from odoo.addons.eh_hr_compat import CONTRACT_MODEL
    from odoo.addons.eh_hr_compat import tracking
    from odoo.addons.eh_hr_compat import legacy_view_mode
    from odoo.addons.eh_hr_compat import owl_import_path
    from odoo.addons.eh_hr_compat import safe_field_rename

Rules of engagement:
    * No models defined here.
    * No singletons, no caches, no global state.
    * No imports from any other eh_hr_platform module.
    * Anything that depends on the running Odoo version is resolved here once,
      via odoo.release.version_info, and exposed as a constant.
""",
    'version': '1.0.0',
    'author': 'ERP Heritage',
    'maintainer': 'ERP Heritage',
    'website': 'https://erpheritage.com.au',
    'license': 'LGPL-3',
    'category': 'Human Resources/Platform',
    'depends': ['base'],
    'data': [],
    'images': ['static/description/banner.png'],
    'support': 'info@erpheritage.com.au',
    'installable': True,
    'application': False,
    'auto_install': False,
}
