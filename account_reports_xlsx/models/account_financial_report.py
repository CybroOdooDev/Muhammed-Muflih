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
from odoo import api, models, fields


# Account Financial Report
class AccountFinancialReport(models.Model):
    _name = "account.financial.report"
    _description = "Account Report"

    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        """Returns a dictionary with key=the ID of a record and value = the
        level of this record in the tree structure."""
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

    def _get_children_by_order(self):
        """returns a recordset of all the children computed recursively,
        and sorted by sequence. Ready for the printing"""
        res = self
        children = self.search([('parent_id', 'in', self.ids)],
                               order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order()
        return res

    name = fields.Char('Report Name', required=True,
                       translate=True, help='The name of the report line to be displayed in the ')
    parent_id = fields.Many2one('account.financial.report',
                                'Parent',
                                recursive=True,
                                help='The parent of the current report line in the report hierarchy. If you ')
    children_ids = fields.One2many('account.financial.report', 'parent_id',
                                   'Account Report')
    sequence = fields.Integer('Sequence',
                              help='The sequence field is used to order the report lines.')
    level = fields.Integer(compute='_get_level',
                           string='Level', store=True, recursive=True,
                           help='The level of the report line in the report hierarchy.')
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
    ], 'Type', default='sum',
        help='The type of the report line determines how the balance of this line is computed.')
    account_ids = fields.Many2many('account.account',
                                   'account_account_financial_report',
                                   'report_line_id',
                                   'account_id', 'Accounts',
                                   help='The accounts whose balance will be included in the report line balance.')
    account_report_id = fields.Many2one('account.financial.report',
                                        'Report Value',
                                        help='The report line whose balance will be included in the report line balance.')
    account_type_ids = fields.Selection(
        [
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("expense_other", "Other Expenses"),
            ("off_balance", "Off-Balance Sheet"),
        ],
        string="Account Type",
        help="Account Type",
    )
    sign = fields.Selection([('-1', 'Reverse balance sign'), ('1', 'Preserve balance sign')], 'Sign on Reports',
                            required=True, default='1',
                            help='For reports that projection is reverse ,例: '
                                 'In case of balance sheet, Revenue & Equity has positive balance, but you want to '
                                 'display it as negative. So you have to set sign as -1')
    display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
    ], 'Display details', default='detail_flat')
    style_overwrite = fields.Selection([
        ('0', 'Automatic formatting'),
        ('1', 'Main Title 1 (bold, underlined)'),
        ('2', 'Title 2 (bold)'),
        ('3', 'Title 3 (bold, smaller)'),
        ('4', 'Normal Text'),
        ('5', 'Italic Text (smaller)'),
        ('6', 'Smallest Text'),
    ], 'Financial Report Style', default='0',
        help="You can customize the style of the report.")
