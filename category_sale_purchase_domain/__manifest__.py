# -*- coding: utf-8 -*-
{
    'name': 'Category Sale Purchase Domain',
    'depends': ['base', 'sale_management', 'purchase'],
    'data': [
        'views/res_config_settings.xml',
        'views/sale_order_views.xml',
        # 'views/purchase_order_views.xml',
    ],
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False
}

# This module filters customers and vendors based on their categories.
# All configurations are at the company level and are added under general settings.
