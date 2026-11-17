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
import io
import json
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import json_default
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountingReport(models.TransientModel):
    """
    Accounting Report Wizard
    This wizard is used to generate accounting reports.
    """
    _name = "accounting.report.xlsx"
    _inherit = "account.common.report.xlsx"
    _description = "Accounting Report"

    @api.model
    def _get_account_report(self):
        """
        Function to get default account report based on active_id in context.

        :return: Account financial report record or False.
        :rtype: account.financial.report or False
        """
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    enable_filter = fields.Boolean(
        string='Enable Comparison',
        help="Check this box if you want to enable filter for comparison.")
    account_report_id = fields.Many2one(
        'account.financial.report',
        string='Account Reports',
        required=True,
        default=_get_account_report,
        help="Select the account report for which you want to generate data.")
    label_filter = fields.Char(
        string='Column Label',
        help="Enter the label for comparison column. This will be displayed in "
             "the report.")
    filter_cmp = fields.Selection(
        [('filter_no', 'No Filters'), ('filter_date', 'Date')],
        string='Filter by',
        required=True,
        default='filter_no',
        help="Select the filter type for comparison.")
    date_from_cmp = fields.Date(
        string='Start Date',
        help="Enter the start date for comparison.")
    date_to_cmp = fields.Date(
        string='End Date',
        help="Enter the end date for comparison.")
    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        help="Check this box if you want to display Debit and Credit columns "
             "in the report.")

    def _build_comparison_context(self, data):
        """
        Function to build context for comparison based on filter parameters.

        :param data: Data containing filter parameters.
        :type data: dict
        :return: Dictionary containing comparison context.
        :rtype: dict
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        if data['form'].get('filter_cmp') == 'filter_date':
            result['date_from'] = data['form'].get('date_from_cmp')
            result['date_to'] = data['form'].get('date_to_cmp')
            result['strict_range'] = True
        return result

    def check_report(self):
        """
        Function to check and generate report in XLSX format.

        :return: Action for generating the XLSX report.
        :rtype: dict
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'enable_filter', 'debit_credit', 'date_to',
             'journal_ids', 'filter_cmp', 'account_report_id',
             'date_from_cmp', 'date_to_cmp', 'label_filter',
             'target_move', 'company_id'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'].get(field), tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get('lang') or 'en_US')
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'accounting.report.xlsx',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'financial report',
                     },
            'report_type': 'xlsx'
        }

    def check_report_xlsx(self):
        """ Alias for check_report. """
        return self.check_report()

    def get_xlsx_report(self, options, response):
        """
            Function to get report in XLSX format.

            :param options: Options for generating the report.
            :type options: dict
            :param response: HTTP response object.
            :type response: werkzeug.wrappers.Response
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {}
        obj = self.search([('id', '=', options['form']['id'])])
        data['form'] = obj.read([])[0]
        comp_dic = {}
        env_obj = self.env['report.account_reports_xlsx.report_financial']
        data['form']['used_context'] = {}
        data['form']['used_context']['date_to'] = data['form']['date_to']
        data['form']['used_context']['date_from'] = data['form']['date_from']
        data['form']['used_context']['journal_ids'] = data['form'][
            'journal_ids']
        data['form']['used_context']['state'] = 'posted'
        data['form']['used_context']['strict_range'] = True
        comp_dic['state'] = 'posted'
        comp_dic['journal_ids'] = data['form']['journal_ids']
        data['form']['comparison_context'] = comp_dic
        data['account_report_id'] = data['form']['account_report_id']
        accounting_data = env_obj.get_account_lines(data.get('form'))
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3',
             'bold': True})
        format1.set_font_color('#000080')
        format1.set_font_name('Times New Roman')
        format2 = workbook.add_format({'font_size': 10, 'bold': True})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10})
        format8 = workbook.add_format(
            {'font_size': 10, 'bold': True, 'bg_color': '#D3D3D3'})
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        logged_users = self.env.company
        sheet.write('A1', logged_users.name, format4)
        report_date = datetime.now().strftime("%Y-%m-%d")
        sheet.merge_range('A1:B1', _("Report Date"), format6)
        sheet.merge_range('C1:D1', report_date, format7)
        if obj.account_report_id.name:
            sheet.merge_range(3, 0, 4, 9, obj.account_report_id.name, format1)
        else:
            sheet.merge_range(3, 0, 4, 9, _("Financial Report"), format1)
        if obj.target_move == 'all':
            target_moves = _('All Entries')
        else:
            target_moves = _('All Posted Entries')
        sheet.merge_range('A7:B7', _("Target Moves:"), format6)
        sheet.write('C7', target_moves, format7)
        if obj.date_from:
            sheet.write('E7', _("Date from:"), format6)
            sheet.write('F7', str(obj.date_from), format7)
        if obj.date_to:
            sheet.write('H7', _("Date to:"), format6)
            sheet.write('I7', str(obj.date_to), format7)
        row_number = 9
        col_number = 0
        if obj.debit_credit == 1:
            sheet.merge_range('A9:G9', _("Name"), format8)
            sheet.write('H9', _("Debit"), format2)
            sheet.write('I9', _("Credit"), format2)
            sheet.write('J9', _("Balance"), format2)
            for values in accounting_data:
                if values['level'] != 0:
                    if values['level'] == 1:
                        sheet.write(row_number, col_number, values['name'],
                                    format6)
                        sheet.write(row_number, col_number + 7,
                                    values['debit'], format6)
                        sheet.write(row_number, col_number + 8,
                                    values['credit'], format6)
                        sheet.write(row_number, col_number + 9,
                                    values['balance'], format6)
                        row_number += 1
                    elif not values['account_type'] == 'sum':
                        sheet.write(row_number, col_number, values['name'],
                                    format7)
                        sheet.write(row_number, col_number + 7,
                                    values['debit'], format7)
                        sheet.write(row_number, col_number + 8,
                                    values['credit'], format7)
                        sheet.write(row_number, col_number + 9,
                                    values['balance'], format7)
                        row_number += 1

        if not obj.enable_filter and not obj.debit_credit:
            sheet.merge_range('A9:I9', _("Name"), format8)
            sheet.write('J9', _("Balance"), format2)
            for values in accounting_data:
                if values['level'] != 0:
                    if values['level'] == 1:
                        # assets and liabilities
                        sheet.write(row_number, col_number, values['name'],
                                    format6)
                        sheet.write(row_number, col_number + 9,
                                    values['balance'], format6)
                        row_number += 1
                    elif not values['account_type'] == 'sum':
                        sheet.write(row_number, col_number + 1, values['name'],
                                    format7)
                        sheet.write(row_number, col_number + 9,
                                    values['balance'], format7)
                        row_number += 1
        if obj.enable_filter and not obj.debit_credit:
            sheet.merge_range('A9:H9', _("Name"), format8)
            sheet.write('I9', _("Balance"), format2)
            sheet.write('J9', data['form']['label_filter'], format2)
            for values in accounting_data:
                if values['level'] != 0:
                    if values['level'] == 1:
                        sheet.write(row_number, col_number, values['name'],
                                    format6)
                        sheet.write(row_number, col_number + 8,
                                    values['balance'], format6)
                        sheet.write(row_number, col_number + 9,
                                    values['balance_cmp'], format6)
                        row_number += 1
                    elif not values['account_type'] == 'sum':
                        sheet.write(row_number, col_number + 1, values['name'],
                                    format7)
                        sheet.write(row_number, col_number + 8,
                                    values['balance'], format7)
                        sheet.write(row_number, col_number + 9,
                                    values['balance_cmp'], format7)
                        row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
