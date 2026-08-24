{
    'name': 'Custom Date Filter',
    'depends':['base', 'web', 'sale', 'point_of_sale', 'stock_enterprise'],
    'version': '19.0.1.0.0',
    'category': '',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'data':[
        'views/pos_order_search_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'custom_date_filter_pos/static/src/**/*',
        ]
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}

# This module enables custom date filters like 'Today',
# 'Yesterday', 'Custom Date Filter'
