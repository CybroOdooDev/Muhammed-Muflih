{
    'name': 'Copy Order Serial Number',
    'version': '19.0.1.0.0',
    'depends': ['web', 'point_of_sale', 'stock'],
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'assets': {
        'web.assets_backend': [
            '/copy_order_serial_number/static/src/many2many_tag_copy.js',
            '/copy_order_serial_number/static/src/many2many_tag_copy.xml'
        ]
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}

# This module enables the Copy Lot functionality for Point of Sale orders.
# We updated the many2many_tags widget as part of the enhancement.