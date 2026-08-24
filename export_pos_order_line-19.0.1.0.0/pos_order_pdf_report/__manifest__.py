{
    'name': "Point of Sale Order Report PDF",
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'author': '',
    'maintainer': '',
    'company': '',
    'website': '',
    'depends': ['base', 'point_of_sale', 'sale'],
    'data': [
        'security/pos_order_pdf_report_security.xml',
        'report/pos_order.xml',
        'report/report_template.xml',
        'report/pos_order_report.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False
}
