# -*- coding: utf-8 -*-
"""eh_hr_compat - version compatibility layer for the EH HR Platform.

Exposes a stable surface area so that downstream modules never need to
branch on odoo.release.version_info themselves.
"""
from .api_shim import (
    ODOO_VERSION,
    IS_19_PLUS,
    IS_18_PLUS,
    IS_17_PLUS,
    CONTRACT_MODEL,
    tracking,
    legacy_view_mode,
    owl_import_path,
    safe_field_rename,
    user_groups,
    group_users,
    groups_field,
    setup_access_dropdown,
)
