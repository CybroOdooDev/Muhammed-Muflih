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
from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import json_default
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountAgedTrialBalance(models.TransientModel):
    """
    Transient model for the Aged Partner Balance report in Excel format.
    """
    _name = 'account.aged.trial.balance.xlsx'
    _inherit = 'account.common.report.xlsx'
    _description = 'Account Aged Trial balance'

    period_length = fields.Integer(string=_('Period Length (days)'),
                                   default=30, required=True)
    result_selection = fields.Selection([('customer', _('Receivable Accounts')),
                                         ('supplier', _('Payable Accounts')),
                                         ('customer_supplier',
                                          _('Receivable and Payable Accounts'))
                                         ], string=_("Partner's"),
                                        required=True, default='customer')

    def _aged_buckets(self, date_from, period_length):
        """Calculate the 5 aging period buckets."""
        res = {}
        if not date_from:
            date_from = fields.Date.today()
        start = datetime.strptime(str(date_from), "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            res[str(i)] = {
                'name': (i != 0 and (
                        str((5 - (i + 1)) * period_length + 1) + '-' + str(
                    (5 - i) * period_length)) or (
                                 '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        return res

    def _print_report(self, data):
        """Print the Aged Partner Balance report in PDF format.

            :param data: Dictionary containing report data.
            :type data: dict
            :return: Action dictionary for report printing.
            :rtype: dict
            :raises UserError: If period length is non-positive.
        """
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length', 'result_selection'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))
        res = self._aged_buckets(data['form']['date_from'], period_length)
        data['form'].update(res)
        return self.env.ref(
            'account.action_report_aged_partner_balance').with_context(
            landscape=True).report_action(self, data=data)

    def check_report(self):
        """Prepare and return the report action for generating the Excel report.

            :return: Report action dictionary for generating the Excel report.
            :rtype: dict
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = \
        self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'period_length', 'result_selection', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'account.aged.trial.balance.xlsx',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'aged partner report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, options, response):
        """Generate Aged Partner Balance report in Excel format.

            :param options: Options for generating the report, including the form data.
            :type options: dict
            :param response: Response object to write the generated report.
            :type response: werkzeug.wrappers.Response
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        env_obj = self.env['report.account_reports_xlsx.report_agedpartnerbalance'].with_context(
            options['form'].get('used_context', {}))
        result_selection = options['form'].get('result_selection') or 'customer'
        if result_selection == 'customer':
            account_type = ['asset_receivable']
            account_type_name = _("Receivable Accounts")
        elif result_selection == 'supplier':
            account_type = ['liability_payable']
            account_type_name = _("Payable Accounts")
        else:
            account_type = ['liability_payable', 'asset_receivable']
            account_type_name = _("Receivable and Payable Accounts")
        date_from = options['form'].get('date_from')
        target_move = options['form'].get('target_move')
        if target_move == 'all':
            target_move_name = _("All Entries")
        else:
            target_move_name = _("All Posted Entries")
        period_length = options['form'].get('period_length') or 30
        move_lines, total, dummy = env_obj._get_partner_move_lines(account_type,
                                                                   date_from,
                                                                   target_move,
                                                                   period_length)
        if not dummy or not isinstance(dummy, dict) or '4' not in dummy:
            dummy = self._aged_buckets(date_from, period_length)
        if not total or len(total) < 7:
            total = [0.0] * 7
        sheet = workbook.add_worksheet('Aged Partner Balance')
        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3',
             'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 10, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'align': 'right'})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'align': 'left'})
        format1.set_align('center')
        format2.set_align('center')
        format3.set_align('right')
        format4.set_align('left')
        format6.set_align('right')
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        logged_users = self.env.company
        report_date = datetime.now().strftime("%Y-%m-%d")
        sheet.merge_range('F8:G8', _("Report Date"), format6)
        sheet.write('H8', report_date, format4)
        sheet.merge_range(1, 0, 1, 7, logged_users.name, format4)
        sheet.merge_range(3, 0, 4, 7, _("Aged Partner Balance"), format1)
        sheet.write('A7', _("Partners:"), format6)
        sheet.write('B7', account_type_name, format7)
        sheet.write('A8', _("Start Date:"), format6)
        sheet.write('B8', str(date_from), format7)
        sheet.write('A9', _("Period Length (days)"), format6)
        sheet.write('B9', str(period_length), format7)
        sheet.merge_range('F9:G9', _("Target Moves:"), format6)
        sheet.write('H9', target_move_name, format7)
        sheet.merge_range('A11:B11', _("Partners"), format2)
        sheet.write('C11', _("Not due"), format2)
        sheet.write('D11', dummy['4']['name'], format2)
        sheet.write('E11', dummy['3']['name'], format2)
        sheet.write('F11', dummy['2']['name'], format2)
        sheet.write('G11', dummy['1']['name'], format2)
        sheet.write('H11', dummy['0']['name'], format2)
        sheet.write('I11', _("Total"), format2)
        row_number = 11
        col_number = 0
        symbol = logged_users.currency_id.symbol or ''
        sheet.merge_range(row_number, col_number, row_number, col_number + 1,
                          _("Account Total"), format3)
        sheet.write(row_number, col_number + 2,
                    symbol + ' ' + "{:,}".format(total[6]), format3)
        sheet.write(row_number, col_number + 3,
                    symbol + ' ' + "{:,}".format(total[4]), format3)
        sheet.write(row_number, col_number + 4,
                    symbol + ' ' + "{:,}".format(total[3]), format3)
        sheet.write(row_number, col_number + 5,
                    symbol + ' ' + "{:,}".format(total[2]), format3)
        sheet.write(row_number, col_number + 6,
                    symbol + ' ' + "{:,}".format(total[1]), format3)
        sheet.write(row_number, col_number + 7,
                    symbol + ' ' + "{:,}".format(total[0]), format3)
        sheet.write(row_number, col_number + 8,
                    symbol + ' ' + "{:,}".format(total[5]), format3)
        row_number += 1
        for values in move_lines:
            sheet.merge_range(row_number, col_number, row_number,
                              col_number + 1, values['name'], format4)
            sheet.write(row_number, col_number + 2, "{:,}".format(values['direction']),
                        format5)
            sheet.write(row_number, col_number + 3, "{:,}".format(values['4']),
                        format5)
            sheet.write(row_number, col_number + 4, "{:,}".format(values['3']),
                        format5)
            sheet.write(row_number, col_number + 5, "{:,}".format(values['2']),
                        format5)
            sheet.write(row_number, col_number + 6, "{:,}".format(values['1']),
                        format5)
            sheet.write(row_number, col_number + 7, "{:,}".format(values['0']),
                        format5)
            sheet.write(row_number, col_number + 8, "{:,}".format(values['total']),
                        format5)
            row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
