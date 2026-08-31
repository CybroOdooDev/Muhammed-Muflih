{
    'name': 'Invntory stock report extends',
    'version': '19.0.1.0.0',
    'summary': 'Invntory stock report extends',
    'category': 'Productivity',
    'depends': ['base', 'web', 'stock'],
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'data':[
        'data/res_groups.xml',
        'views/stock_report.xml',
        'data/report_paperformat.xml',
        'data/stock_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/inventory_stock_report_extends/static/src/stock_report_search_model.js',
        ]
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}
