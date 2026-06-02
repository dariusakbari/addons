# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Quickbooks Canada Online Integration | Quickbooks Canada Connector',
    'version': '19.0.0.1',
    'summary': 'Quickbooks Odoo Integration App Quickbooks Online Quickbooks Canada Canada Accounting Quickbooks Canada Online Quickbooks Quickbooks odoo Quickbooks Accounting Odoo Quickbooks connector Odoo Quickbooks integration Quickbooks connector QuickBooks Credit Memo Quickbooks reports Quickbooks Refund Quickbooks Payments Quickbooks credit Memo quickbook connector quickbook integration',
    'sequence': '-101',
    'price': '99.00',
    'currency': 'USD',
    'author': 'echoBitz IT Solutions Pvt. Ltd.',
    'maintainer': 'echoBitz IT Solutions Pvt. Ltd.',
     'description': """
        -Odoo Quickbooks Integration
        -================================
        -<keywords>
        -Quickbooks Odoo Integration App
        -Quickbooks Online
        -Quickbooks Canada
        -Canada Accounting
        -Quickbooks Canada Online
        -Quickbooks
        -Quickbooks odoo
        -Quickbooks Accounting
        -odoo Quickbooks connector
        -odoo Quickbooks integration
        -""",
    'live_test_url': 'https://www.echobitzit.com/contactus',
    'website': 'https://www.echobitzit.com',
    'category': 'Integration',
    'depends': ['base', 'mail', 'web', 'contacts', 'stock', 'account', 'sale_management', 'purchase', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/oqb_security.xml',
        'data/oqb_cron.xml',
        'views/oqb_menu.xml',
        'wizard/oqb_wizard.xml',
        'views/oqb_instance_views.xml',
        'views/oqb_logger_views.xml',
        'views/oqb_field_mapper_views.xml',
        'views/oqb_res_partner_views.xml',
        'views/oqb_account_account_views.xml',
        'views/oqb_product_template_views.xml',
        'views/oqb_sale_order_views.xml',
        'views/oqb_hr_employee_views.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'eb_oqb_canada_integration/static/src/js/oqb_pass_copy.js',
            'eb_oqb_canada_integration/static/src/xml/oqb_pass_copy.xml',
            'eb_oqb_canada_integration/static/src/scss/oqb_pass_copy.scss',
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': True,
    'images': ['static/description/banner.gif'],
    'license': 'OPL-1',
}
