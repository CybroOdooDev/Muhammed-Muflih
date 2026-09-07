# -*- coding: utf-8 -*-
{
    'name': 'POS Recent Sales',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Show recent POS sales in product information popup',
    'description': """
        Adds a 'Recent POS Sales' section immediately after 'Replenishment'
        in the Product Information popup in Point of Sale.
    """,
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_recent_sales/static/src/xml/product_info_popup.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
