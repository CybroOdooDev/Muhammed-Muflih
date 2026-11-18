# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'Accounting Reports In Excel',
    'version': '20.0.1.0.0',
    'category': 'Accounting',
    'summary': """Generates Excel report for Partner Ledger, General Ledger,
     Balance Sheet, Profit and Loss, Aged Partner Balance.""",
    'description': """This module generates Excel-based accounting reports, 
 including Partner Ledger, Profit and Loss, Aged Partner Balance, 
 General Ledger, Balance Sheet, and other financial statements, all 
 in .xlsx format.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'live_test_url': 'https://www.youtube.com/watch?v=Sch1VcrunT0&list=PLeJtXzTubzj_wOC0fzgSAyGln4TJWKV4k&index=33',
    'depends': ['account'],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'data': [
        'security/ir.access.csv',
        'data/account_financial_report_data.xml',
        'report/partner_ledger_report.xml',
        'report/report_aged_partner_balance.xml',
        'wizard/partner_ledger_wizard_view.xml',
        'wizard/account_report_aged_partner_balance_view.xml',
        'wizard/account_report_general_ledger_view.xml',
        'wizard/account_financial_report_view.xml',
        'views/account_reports_xlsx_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_reports_xlsx/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'price': 19.99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
