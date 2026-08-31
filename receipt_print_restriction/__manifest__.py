# -*- coding: utf-8 -*-
{
    'name': 'Receipt Print Restriction',
    'version': '19.0.1.0.0',
    'summary': 'Receipt Print Restriction',
    'category': 'Productivity',
    'depends': ['base', 'point_of_sale'],
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'data': [
        'views/pos.config.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'receipt_print_restriction/static/src/js/OrderReceipt.js',
            'receipt_print_restriction/static/src/js/restrict_print_screen.js',
            'receipt_print_restriction/static/src/js/restrict_printing.js',
            'receipt_print_restriction/static/src/xml/*',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}

# This module restrict multiple receipt printing
# Admin can specify the allowed number of printing for each Point of sale.
