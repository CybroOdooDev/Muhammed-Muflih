# -*- coding: utf-8 -*-
{
    'name': 'PDC Payment',
    'version': '1.0',
    'category': 'account',
    'summary': 'PDC Payment',
    'description': '''PDC Payment''',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'account_accountant','sales_extends'],
    'data': [
        'security/ir.model.access.csv',
        'demo/bulk_mail_demo.xml',
        'views/bulk_mail_views.xml',
        # 'views/views.xml',
		'views/account_payment_views.xml',

        'views/account_reconciliated_views.xml',
		'wizard/payment_statement_views.xml',
		'report/payment_statement_report_template.xml',
		'views/account_payment_new_views.xml',
		'views/account_payment_menu_views.xml',
    ],


    'assets': {
        'web.assets_backend': [
            'pdc_payment/static/src/js/action_manager.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}