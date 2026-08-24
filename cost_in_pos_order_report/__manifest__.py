# -*- coding: utf-8 -*-
{
    'name': 'Cost In POS Order Report',
    'depends': ['point_of_sale', 'purchase'],
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'data': [
        'data/ir_cron.xml',
        'data/purchase_order_line.xml',
        'views/report_pos_order.xml',
        'views/pos_payment_method_views.xml',
        'views/pos_order_views.xml'
    ],
    'maintainer': '',
    'company': '',
    'website': '',
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}

# This module add Total Cost Measure to Point of Sale Report
# Additionally, it displays text in red color if the amount is less than 0.
