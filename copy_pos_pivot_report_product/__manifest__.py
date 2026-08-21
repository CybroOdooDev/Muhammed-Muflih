{
    'name': 'Copy POS Pivot Report Product',
    'depends': ['web', 'web_enterprise', 'point_of_sale'],
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'assets': {
        'web.assets_backend_lazy': [
            'copy_pos_pivot_report_product/static/src/js/pivot_renderer.js',
            'copy_pos_pivot_report_product/static/src/xml/pivot_renderer.xml'
        ]
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}

# This module facilitates the copying of product information
# from the Point of Sale report pivot view.
