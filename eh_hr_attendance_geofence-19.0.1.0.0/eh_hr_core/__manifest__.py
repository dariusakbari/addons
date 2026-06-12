# -*- coding: utf-8 -*-
{
    'name': 'EH HR Platform Core',
    'summary': 'Foundational platform module for the EH HR Platform: mixins, services, audit log, OWL component kit.',
    'description': """
HR Platform Core (eh_hr_core)
=============================
Thin, dependency-light platform module that every other HR feature module
builds on.

Provides:
    * Abstract mixins (audited, company-aware, platform-base).
    * The audit log (append-only, hash-chained), independent of mail.thread.
    * A service base class and tiny service registry/locator.
    * Settings + feature flag scaffolding (per-company key/value).
    * Timezone helpers and company-scoped query helpers.
    * OWL component kit primitives (HrCard, HrStat, HrSkeleton, ...).

Explicitly NOT here:
    * Workflow logic            → eh_hr_engine_workflow
    * Approval chains           → eh_hr_engine_approval
    * Policy DSL                → eh_hr_engine_policy
    * Notification dispatch     → eh_hr_engine_notification
    * Any feature surface       → eh_hr_attendance_pro, eh_hr_leave_pro, ...
""",
    'version': '1.0.0',
    'author': 'ERP Heritage',
    'website': 'https://erpheritage.com.au',
    'license': 'LGPL-3',
    'category': 'Human Resources/Platform',
    'depends': ['base', 'mail', 'hr', 'eh_hr_compat'],
    'data': [
        'security/eh_hr_core_groups.xml',
        'security/ir.model.access.csv',
        'security/audit_rules.xml',
        'data/eh_hr_core_sequences.xml',
        'data/eh_hr_core_crons.xml',
        'views/eh_hr_audit_log_views.xml',
        'views/eh_hr_settings_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'eh_hr_core/static/src/scss/tokens.scss',
            'eh_hr_core/static/src/components/**/*.js',
            'eh_hr_core/static/src/components/**/*.xml',
            'eh_hr_core/static/src/components/**/*.scss',
            'eh_hr_core/static/src/services/**/*.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'post_init_hook': 'post_init_hook',
    'support': 'info@erpheritage.com.au',
    'installable': True,
    'application': False,
    'auto_install': False,
}
