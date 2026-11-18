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
import re
from datetime import datetime
from odoo import fields, models, _
from odoo.tools import json_default
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountReportPartnerLedger(models.TransientModel):
    """
    Transient model for generating the Partner Ledger report in Excel format.
    """
    _name = "account.report.partner.ledger.xlsx"
    _inherit = "account.common.report.xlsx"
    _description = "Account Partner Ledger"

    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'),
         ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')
         ], string="Partners", required=True,
        default='customer')
    amount_currency = fields.Boolean(
        string="With Currency",
        help="It adds the currency column on report if the "
             "currency differs from the company currency.")
    reconciled = fields.Boolean(
        string='Reconciled Entries',
        help="Check this box if you want to include reconciled entries.")
    partner_ids = fields.Many2many(
        'res.partner',
        string='Partners', help="Select partner.")

    def pre_print_report(self, data):
        """Prepares data before printing the report.

            :param data: Dictionary containing report parameters.
            :type data: dict
            :return: Updated dictionary with additional parameters.
            :rtype: dict
            """
        data['form']['result_selection'] = self.result_selection
        data['form']['amount_currency'] = self.amount_currency
        data['form']['reconciled'] = self.reconciled
        data['form']['partner_ids'] = self.partner_ids.ids
        return data

    def _print_report(self, data):
        """Prints the Partner Ledger report in PDF format.

            :param data: Dictionary containing report parameters.
            :type data: dict
            :return: Action to open the PDF report.
            :rtype: dict
            """
        data = self.pre_print_report(data)
        data['form'].update(self.read(['result_selection'])[0])
        return self.check_report()

    def check_report(self):
        """Checks and prepares data for generating the Partner Ledger report in Excel format.

            :return: Action to open the Excel report.
            :rtype: dict
            """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = \
        self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency,
                             'partner_ids': self.partner_ids.ids})
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'account.report.partner.ledger.xlsx',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'partner ledger report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, options, response):
        """Generates an XLSX report for the partner ledger.

            :param options: Options for generating the report.
            :type options: dict
            :param response: Response object for writing the generated report.
            :type response: werkzeug.wrappers.Response
            """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        obj_partner = self.env['res.partner']
        data = options
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        data['computed'] = {}
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable',
                                                'asset_receivable']
        self.env.cr.execute("""
                    SELECT a.id
                    FROM account_account a
                    WHERE a.account_type IN %s
                    """,
                            (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in
                                           self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + list(query_get_data[2])
        reconcile_clause = "" if data['form'].get(
            'reconciled') else ' AND "account_move_line".full_reconcile_id IS NULL '
        where_clause_str = query_get_data[1] if query_get_data[1] else "1=1"
        partner_filter = ""
        if data['form'].get('partner_ids'):
            params.append(tuple(data['form']['partner_ids']))
            partner_filter = ' AND "account_move_line".partner_id IN %s '
        query = """
                    SELECT DISTINCT "account_move_line".partner_id
                    FROM """ + str(query_get_data[0]) + """, account_account AS account, account_move AS am
                    WHERE "account_move_line".partner_id IS NOT NULL
                        AND "account_move_line".account_id = account.id
                        AND am.id = "account_move_line".move_id
                        AND am.state IN %s
                        AND "account_move_line".account_id IN %s
                        AND """ + where_clause_str + reconcile_clause + partner_filter
        self.env.cr.execute(query, tuple(params))
        partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        format1 = workbook.add_format(
            {'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3',
             'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format({'font_size': 12, 'bold': True})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'bold': True})
        format8 = workbook.add_format({'font_size': 10})
        format9 = workbook.add_format({'font_size': 10})
        format10 = workbook.add_format({'font_size': 10, 'bold': True})
        format1.set_align('center')
        format3.set_align('center')
        format4.set_align('center')
        format6.set_align('right')
        currency = self.env.company.currency_id.symbol or ''
        format7.set_num_format('0.00 ' + currency)
        format8.set_num_format('0.00 ' + currency)
        logged_users = self.env.company

        if not partners:
            sheet = workbook.add_worksheet('Partner Ledger')
            sheet.merge_range('A1:B1', logged_users.name, format4)
            sheet.merge_range('A4:R4', _("Partner Ledger - No records found"), format1)

        used_sheet_names = set()
        env_obj = self.env['report.account_reports_xlsx.report_partnerledger']
        report_date = datetime.now().strftime("%Y-%m-%d")

        for items in partners:
            raw_name = items.name or f'Partner_{items.id}'
            clean_name = re.sub(r'[\:\\\/\?\*\[\]]', '_', raw_name)[:28]
            sheet_name = clean_name
            counter = 1
            while sheet_name in used_sheet_names:
                sheet_name = f"{clean_name[:25]}_{counter}"
                counter += 1
            used_sheet_names.add(sheet_name)
            sheet = workbook.add_worksheet(sheet_name)

            sheet.merge_range('A1:B1', logged_users.name, format4)
            if data['form'].get('date_from'):
                sheet.write('E2', _('Date from:'), format6)
                sheet.write('F2', str(data['form']['date_from']), format5)
            if data['form'].get('date_to'):
                sheet.write('E3', _('Date to:'), format6)
                sheet.write('F3', str(data['form']['date_to']), format5)
            sheet.merge_range('I2:J2', _('Target Moves:'), format6)
            if data['form'].get('target_move') == 'all':
                sheet.merge_range('K2:L2', _('All Entries'), format4)
            if data['form'].get('target_move') == 'posted':
                sheet.merge_range('K2:L2', _('All Posted Entries'), format4)
            sheet.merge_range(5, 0, 5, 1, _("Date"), format3)
            sheet.merge_range(5, 2, 5, 3, _("JRNL"), format3)
            sheet.merge_range(5, 4, 5, 5, _("Account"), format3)
            sheet.merge_range(5, 6, 5, 7, _("Ref"), format3)
            sheet.merge_range(5, 8, 5, 11, _("Matching Number"), format3)
            sheet.merge_range(5, 12, 5, 13, _("Debit"), format3)
            sheet.merge_range(5, 14, 5, 15, _("Credit"), format3)
            sheet.merge_range(5, 16, 5, 17, _("Balance"), format3)
            if data['form'].get('amount_currency'):
                sheet.merge_range(5, 18, 5, 19, _("Currency"), format3)
            sheet.merge_range('A2:B2', _("Report Date"), format6)
            sheet.merge_range('C2:D2', report_date, format5)
            sheet.merge_range('A4:R4', _("Partner Ledger"), format1)

            # Partner total header row
            debit_sum = env_obj._sum_partner(data, items, 'debit')
            credit_sum = env_obj._sum_partner(data, items, 'credit')
            sheet.merge_range(6, 0, 6, 11,
                              (items.ref or '') + ' - ' + (
                                      items.name or ''), format2)
            sheet.merge_range(6, 12, 6, 13, debit_sum, format7)
            sheet.merge_range(6, 14, 6, 15, credit_sum, format7)
            sheet.merge_range(6, 16, 6, 17, debit_sum - credit_sum, format7)

            # Move lines starting at row 7
            row_number = 7
            col_number = 0
            partner_balance = env_obj._lines(data, items)
            for lines in partner_balance:
                sheet.merge_range(row_number, col_number, row_number,
                                  col_number + 1, lines['date'], format4)
                sheet.merge_range(row_number, col_number + 2, row_number,
                                  col_number + 3, lines['code'], format4)
                sheet.merge_range(row_number, col_number + 4, row_number,
                                  col_number + 5, lines['a_code'], format4)
                sheet.merge_range(row_number, col_number + 6, row_number,
                                  col_number + 7, lines['displayed_name'],
                                  format4)
                sheet.merge_range(row_number, col_number + 8, row_number,
                                  col_number + 11, lines['matching_number'],
                                  format4)
                sheet.merge_range(row_number, col_number + 12, row_number,
                                  col_number + 13, lines['debit'], format8)
                sheet.merge_range(row_number, col_number + 14, row_number,
                                  col_number + 15, lines['credit'], format8)
                sheet.merge_range(row_number, col_number + 16, row_number,
                                  col_number + 17, lines['progress'], format8)
                if data['form'].get('amount_currency'):
                    sheet.merge_range(row_number, col_number + 18, row_number,
                                      col_number + 19, lines.get('amount_currency', 0.0),
                                      format9)
                row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
