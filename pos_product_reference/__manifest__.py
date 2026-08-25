# -*- coding: utf-8 -*-
{
    'name': 'POS Product Reference',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_reference/static/src/xml/ProductItem.xml',
            'pos_product_reference/static/src/xml/Orderline.xml',
            'pos_product_reference/static/src/scss/product_card.scss',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}