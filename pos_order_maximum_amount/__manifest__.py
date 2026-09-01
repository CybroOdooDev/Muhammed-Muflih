{
    'name': 'POS Order Maximum Amount',
    'depends':['base', 'point_of_sale'],
    'category': 'Productivity',
    'author': '',
    'version': '19.0.1.0.0',
    'maintainer': '',
    'company': '',
    'website': '',
    'data':[
        'views/res_config_settings.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_order_maximum_amount/static/src/js/Screens/ProductScreen.js'
        ]
    },
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}
