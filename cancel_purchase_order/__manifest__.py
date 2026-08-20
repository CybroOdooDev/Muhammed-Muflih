{
    'name': 'Force Cancel Purchase Order',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'depends': ['base', 'stock', 'purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'views/account_move_reversal.xml',
        'views/stock_return_picking.xml',
        'views/purchase_product_history.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}
