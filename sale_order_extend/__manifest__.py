{
    'name': 'Sale order extends',
    'depends': ['sale', 'sale_stock', 'sale_project', 'project'],
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'data': [
        'views/sale_order_view.xml',
        'views/sale_order_document.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'sale_order_extend/static/src/css/report_fonts.css',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False
}
