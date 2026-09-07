{
    'name': 'PSAE - Dot Matrix Printout',
    'summary': 'Creating a custom templates for dot matrix printout',
    'version': '18.0.0.1.1',
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'OEEL-1',
    'depends': ['sale_stock', 'convert_arabic'],
    'data': [
        "data/ir_actions.xml",

        'reports/custom_report_layout.xml',
        "reports/custom_deliveryslip.xml",
        "reports/custom_invoice.xml",
        "data/report_layout.xml",
		'reports/custom_invoice_arabic.xml',
],
    'assets': {
        'web.report_assets_common': [
            'psae_dot_matrix_printout/static/src/scss/report_style.scss'
        ],
    },

    'task_id': [4816408]
}
