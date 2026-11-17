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
from odoo import fields, models, _
from odoo.tools import json_default
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountReportGeneralLedger(models.TransientModel):
    """
    Transient model for generating the General Ledger report.
    """
    _name = "account.report.general.ledger.xlsx"
    _inherit = "account.common.account.report.xlsx"
    _description = "General Ledger Report"

    initial_balance = fields.Boolean(
        string='Include Initial Balances',
        help='If you selected to filter by date or period, this field allow '
             'you to add a row to refer to the initial balance of the '
             'account', default=True)
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by',
        required=True, default='sort_date')

    def _print_report(self, data):
        """
        Function to print report.

        :param data: Dictionary containing report parameters.
        :type data: dict
        :return: Action to print the report.
        :rtype: dict
        """
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get(
                'date_from'):
            self.initial_balance = False
        return self.env.ref(
            'account.action_report_general_ledger').with_context(
            landscape=True).report_action(self, data=data)

    def check_report(self):
        """
        Function to check and generate report.

        :return: Action to generate the report.
        :rtype: dict
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'date_to', 'journal_ids', 'target_move',
             'display_account', 'initial_balance', 'sortby', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'account.report.general.ledger.xlsx',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'general ledger report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, options, response):
        """
          Function to generate and download XLSX report for General Ledger.

          :param options: Dictionary containing report options and parameters.
          :type options: dict
          :param response: Response object to write the XLSX file content.
          :type response: werkzeug.wrappers.Response
          """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {}
        vals = self.search([('id', '=', options['form']['id'])])
        data['form'] = vals.read([])[0]
        data['model'] = 'ir.ui.menu'
        data['ids'] = []
        data['form']['used_context'] = {
            'date_to': vals.date_to,
            'date_from': vals.date_from,
            'strict_range': True,
            'state': vals.target_move,
            'journal_ids': vals.journal_ids.ids,
        }

        env_obj = self.env['report.account_reports_xlsx.report_generalledger']
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        accounts = self.env['account.account'].browse(options['ids']) or \
                   self.env['account.account'].search([])
        init_balance = vals['initial_balance']
        report_obj = env_obj.with_context(
            data['form'].get('used_context', {}))._get_account_move_entry(
            accounts, init_balance, sortby, display_account)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3',
             'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format5 = workbook.add_format({'font_size': 10, 'align': 'right'})
        format1.set_align('center')
        format2.set_align('center')
        format3.set_align('right')
        format4.set_align('left')
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 15)
        sheet.set_column(13, 13, 15)
        sheet.set_column(14, 14, 15)
        sheet.set_column(15, 15, 15)
        logged_users = self.env.company
        report_date = datetime.now().strftime("%Y-%m-%d")
        sheet.merge_range('M8:N8', _("Report Date"), format3)
        sheet.merge_range('M9:N9', report_date, format4)
        sheet.merge_range(1, 0, 1, 14, logged_users.name, format4)
        sheet.merge_range(3, 0, 4, 14, _("General Ledger Report"), format1)
        sheet.merge_range('A6:B6', _("Journals :"), format6)
        sheet.write('C6', ', '.join([c or '' for c in codes]), format4)
        sheet.write('A7', _("Display Account :"), format6)
        if display_account == 'all':
            display_accounts = _('All')
        elif display_account == 'movement':
            display_accounts = _('With movements')
        else:
            display_accounts = _('With balance not equal to zero')
        sheet.write('C7', display_accounts, format4)
        if vals.target_move == 'all':
            target_moves = _('All Entries')
        else:
            target_moves = _('All Posted Entries')
        sheet.write('A8', _("Target Moves:"), format6)
        sheet.write('C8', target_moves, format4)
        if vals.date_from:
            sheet.write('A9', _("Date from:"), format6)
            sheet.write('C9', str(vals.date_from), format4)
        if vals.date_to:
            sheet.write('A10', _("Date to:"), format6)
            sheet.write('C10', str(vals.date_to), format4)
        if sortby == 'sort_date':
            sortby = _('Date')
        else:
            sortby = _('Journal & Partner')
        sheet.merge_range('C8:D8', _("Sorted By"), format3)
        sheet.merge_range('C9:D9', sortby, format4)
        sheet.merge_range('A8:B8', _("Display Account"), format6)
        sheet.merge_range('A9:B9', display_account, format7)
        sheet.merge_range('E8:F8', _("Target Moves"), format6)
        sheet.merge_range('E9:F9', target_moves, format7)
        sheet.write('A11', _("Date"), format2)
        sheet.write('B11', _("JRNL"), format2)
        sheet.merge_range('C11:D11', _("Partner"), format2)
        sheet.merge_range('E11:F11', _("Ref"), format2)
        sheet.merge_range('G11:H11', _("Move"), format2)
        sheet.merge_range('I11:L11', _("Entry Label"), format2)
        sheet.write('M11', _("Debit"), format2)
        sheet.write('N11', _("Credit"), format2)
        sheet.write('O11', _("Balance"), format2)
        row_number = 11
        col_number = 0
        currency_sym = logged_users.currency_id.symbol or ''
        for values in report_obj:
            sheet.write(row_number, col_number, values.get('code') or '', format3)
            sheet.merge_range(row_number, col_number + 1, row_number,
                              col_number + 11, values.get('name') or '', format6)
            sheet.write(row_number, col_number + 12,
                        f"{currency_sym} " + "{:,}".format(values['debit']), format3)
            sheet.write(row_number, col_number + 13,
                        f"{currency_sym} " + "{:,}".format(values['credit']), format3)
            sheet.write(row_number, col_number + 14,
                        f"{currency_sym} " + "{:,}".format(values['balance']), format3)
            row_number += 1
            for lines in values['move_lines']:
                sheet.write(row_number, col_number, str(lines['ldate'] or ''),
                            format4)
                sheet.write(row_number, col_number + 1, lines['lcode'] or '',
                            format4)
                sheet.merge_range(row_number, col_number + 2,
                                  row_number, col_number + 3,
                                  lines['partner_name'] or '',
                                  format4)
                sheet.merge_range(row_number, col_number + 4,
                                  row_number, col_number + 5,
                                  lines['lref'] or '',
                                  format4)
                sheet.merge_range(row_number, col_number + 6,
                                  row_number, col_number + 7,
                                  lines['move_name'] or '',
                                  format4)
                sheet.merge_range(row_number, col_number + 8,
                                  row_number, col_number + 11,
                                  lines['lname'] or '',
                                  format4)
                sheet.write(row_number, col_number + 12,
                            "{:,}".format(lines['debit']), format5)
                sheet.write(row_number, col_number + 13,
                            "{:,}".format(lines['credit']), format5)
                sheet.write(row_number, col_number + 14,
                            "{:,}".format(lines['balance']), format5)
                row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
