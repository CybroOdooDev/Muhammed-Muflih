# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import io
import logging
from odoo import api, fields, models
import xlsxwriter

_logger = logging.getLogger(__name__)


class ReceiptPaymentReportWizard(models.TransientModel):
    _name = 'receipt.payment.report.wizard'
    _description = 'Receipt Payment Report Wizard'

    from_date = fields.Date(string='From Date', required=True, default=fields.Date.context_today)
    to_date = fields.Date(string='To Date', required=True, default=fields.Date.context_today)
    partner_type = fields.Selection(
        selection=[('customer', 'Customer'), ('vendor', 'Vendor')],
        string='Partner Type',
    )
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        if self.partner_id:
            self.partner_id = False
        if self.partner_type == 'customer':
            return {'domain': {'partner_id': [('customer_rank', '>', 0)]}}
        elif self.partner_type == 'vendor':
            return {'domain': {'partner_id': [('supplier_rank', '>', 0)]}}
        return {'domain': {'partner_id': []}}

    def _get_report_lines(self):
        """Fetch reconciled receipt/payment items data for XLSX and HTML QWeb reports."""
        domain = [
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('move_id.move_type', 'not in', ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')),
            '|', '|',
            ('reconciled', '=', True),
            ('full_reconcile_id', '!=', False),
            ('matching_number', '!=', False),
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        elif self.partner_type == 'customer':
            domain.append(('partner_id.customer_rank', '>', 0))
        elif self.partner_type == 'vendor':
            domain.append(('partner_id.supplier_rank', '>', 0))

        reconciled_lines = self.env['account.move.line'].search(domain, order='date desc, id desc')

        processed_move_ids = set()
        lines_data = []

        for line in reconciled_lines:
            if line.move_id.id in processed_move_ids:
                continue

            matched = line._all_reconciled_lines().filtered(
                lambda l: l.matched_debit_ids or l.matched_credit_ids or l.reconciled
            )
            if not matched:
                matched = line

            for m in matched:
                if m.move_id:
                    processed_move_ids.add(m.move_id.id)
            processed_move_ids.add(line.move_id.id)

            voucher_names = []
            payment_names = []

            for m in matched:
                if m.move_id.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
                    continue

                payment = m.payment_id or m.move_id.origin_payment_id
                if payment:
                    pay_name = payment.name or m.move_id.name
                    if pay_name and pay_name not in payment_names:
                        payment_names.append(pay_name)
                else:
                    move_name = m.move_id.name
                    if move_name and move_name not in voucher_names:
                        voucher_names.append(move_name)

            voucher_no = ', '.join(voucher_names) if voucher_names else ''
            payment_no = ', '.join(payment_names) if payment_names else ''
            line_amount = max(line.debit, line.credit)

            lines_data.append({
                'date': line.date,
                'voucher_no': voucher_no,
                'payment_no': payment_no,
                'amount': line_amount,
            })

        return lines_data

    def view_report(self):
        """Open the QWeb HTML report in the Odoo report container."""
        return self.env.ref('reciept_and_payment_report.action_report_receipt_payment').report_action(self)

    def action_print_report_xlsx(self):
        """Generate Excel (XLSX) Report for Reconciled Receipt/Payment Items."""
        lines_data = self._get_report_lines()

        # Create in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Report')

        # Formatting styles (NO BACKGROUND COLORS)
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
        })
        label_bold = workbook.add_format({'bold': True, 'font_size': 11})
        label_normal = workbook.add_format({'font_size': 11})
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })
        cell_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'left'})
        date_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'center', 'num_format': 'yyyy-mm-dd'})
        amount_format = workbook.add_format({'font_size': 10, 'border': 1, 'align': 'right', 'num_format': '#,##0.00'})
        total_label_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'right',
            'top': 1,
            'bottom': 6,
        })
        total_amount_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'right',
            'num_format': '#,##0.00',
            'top': 1,
            'bottom': 6,
        })

        # Set Column Widths
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 28)
        sheet.set_column('C:C', 28)
        sheet.set_column('D:D', 20)

        # Dynamic Title (RECEIPT REPORT vs PAYMENT REPORT)
        report_title = "RECEIPT REPORT" if self.partner_type == 'customer' else "PAYMENT REPORT"
        sheet.merge_range('A1:D1', report_title, title_format)
        sheet.set_row(0, 30)

        # Header Metadata
        partner_name = self.partner_id.name if self.partner_id else f"All {self.partner_type.title() if self.partner_type else 'Partner'}s"
        if self.partner_type == 'customer':
            sheet.write('A3', 'Customer:', label_bold)
        else:
            sheet.write('A3', 'Vendor:', label_bold)
        sheet.write('B3', partner_name, label_normal)

        sheet.write('A4', 'From Date:', label_bold)
        sheet.write('B4', str(self.from_date), label_normal)
        sheet.write('C4', 'To Date:', label_bold)
        sheet.write('D4', str(self.to_date), label_normal)

        # Column Headers
        sheet.write('A6', 'Date', header_format)
        sheet.write('B6', 'Voucher No', header_format)
        sheet.write('C6', 'Payment No', header_format)
        sheet.write('D6', 'Amount', header_format)
        sheet.set_row(5, 22)

        row_idx = 6  # 0-indexed row 6 is Excel row 7
        total_sum = 0.0

        for line_data in lines_data:
            line_amount = line_data['amount']
            total_sum += line_amount

            sheet.write(row_idx, 0, str(line_data['date']), date_format)
            sheet.write(row_idx, 1, line_data['voucher_no'], cell_format)
            sheet.write(row_idx, 2, line_data['payment_no'], cell_format)
            sheet.write(row_idx, 3, line_amount, amount_format)
            row_idx += 1

        # Total Row
        first_excel_row = 7                  # 1-indexed Excel row 7 (start of data)
        last_excel_row = row_idx             # 1-indexed Excel row for last written data line

        sheet.write(row_idx, 0, '', total_label_format)
        sheet.write(row_idx, 1, '', total_label_format)
        sheet.write(row_idx, 2, 'Total:', total_label_format)

        if last_excel_row >= first_excel_row:
            formula = f'=SUM(D{first_excel_row}:D{last_excel_row})'
            sheet.write_formula(row_idx, 3, formula, total_amount_format, total_sum)
        else:
            sheet.write(row_idx, 3, 0.00, total_amount_format)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        report_name = "Receipt_Report" if self.partner_type == 'customer' else "Payment_Report"
        filename = f"{report_name}_{self.from_date}_to_{self.to_date}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }