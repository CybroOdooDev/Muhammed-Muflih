{
    'name': 'Export Point of Sale Orderline',
    'depends': ['point_of_sale', 'product_reference_in_order', 'pos_order_pdf_report'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_actions_server.xml',
        'data/pos_order_line.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'export_pos_order_line/static/src/js/action_manager.js',
        ],
    },
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': 'Cybrosys',
    'maintainer': '',
    'company': '',
    'website': '',
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}