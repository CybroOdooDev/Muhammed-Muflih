# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Partner Ledger with Partner Filter',
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': """Get Partner Ledger from Res Partner Module""",
    'description': """This app extends the functionality of Odoo by introducing
     a 'Print Partner Ledger' feature to contacts/partners. With this new
     capability, you can easily generate and print partner ledgers directly
     from contacts/partners.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base_accounting_kit'],
    'data': [
        'views/res_partner_views.xml',
        'views/report_partner_ledger_inherit.xml',
        'wizard/account_report_partner_ledger_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'account_partner_ledger_filter/static/src/css/partner_ledger_report.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
}
