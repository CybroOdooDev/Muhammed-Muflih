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
from datetime import datetime, time
from odoo import api, fields, models
import xlsxwriter

_logger = logging.getLogger(__name__)


def _get_sales_executive_name(record):
    """Helper to safely fetch sales executive name from move or partner."""
    if not record or not hasattr(record, 'x_studio_sales_executive'):
        return ''
    sales_exec = record.x_studio_sales_executive
    if not sales_exec:
        return ''
    if hasattr(sales_exec, 'name') and sales_exec.name:
        return sales_exec.name
    elif hasattr(sales_exec, 'display_name') and sales_exec.display_name:
        return sales_exec.display_name
    return str(sales_exec)


def _get_reconciled_cluster(initial_lines):
    """Recursively expand account.move.lines through all partial reconciliation links and non-bank move lines."""
    cluster = set(initial_lines)
    added = True
    while added:
        added = False
        current = list(cluster)
        for line in current:
            rec = line.sudo()._all_reconciled_lines()
            for r in rec:
                if r not in cluster:
                    cluster.add(r)
                    added = True
            if line.move_id and line.move_id.journal_id.type not in ('bank', 'cash'):
                for ml in line.move_id.line_ids:
                    if ml.reconciled or ml.matched_debit_ids or ml.matched_credit_ids:
                        rec_ml = ml.sudo()._all_reconciled_lines()
                        for r in rec_ml:
                            if r not in cluster:
                                cluster.add(r)
                                added = True
    return list(cluster)


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
        """Fetch reconciled receipt/payment items data for XLSX and HTML QWeb reports based on Voucher Reconciliation Date."""
        from_datetime = datetime.combine(self.from_date, time.min)
        to_datetime = datetime.combine(self.to_date, time.max)

        allowed_company_ids = self.env.companies.ids

        # Build SQL search domain with date and partner filters applied directly in DB query
        base_domain = [
            ('company_id', 'in', allowed_company_ids),
            ('move_id.state', '=', 'posted'),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
        ]

        if self.partner_id:
            partner_domain = ['|', ('partner_id', '=', self.partner_id.id), ('move_id.partner_id', '=', self.partner_id.id)]
        elif self.partner_type == 'customer':
            partner_domain = ['|', ('partner_id.customer_rank', '>', 0), ('move_id.partner_id.customer_rank', '>', 0)]
        elif self.partner_type == 'vendor':
            partner_domain = ['|', ('partner_id.supplier_rank', '>', 0), ('move_id.partner_id.supplier_rank', '>', 0)]
        else:
            partner_domain = []

        candidate_domain = base_domain + partner_domain + [
            '|',
            '&', ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', True),
            ('move_id.journal_id.type', 'in', ('bank', 'cash')),
        ]

        candidate_lines = self.env['account.move.line'].sudo().search(candidate_domain)

        # Identify discount account by XML ID or Code '325030004' to exclude write-off/discount entries
        discount_account_ids = set()
        discount_account_ref = self.env.ref('__export__.account_account_3516_948713fc', raise_if_not_found=False)
        if discount_account_ref:
            discount_account_ids.add(discount_account_ref.id)
        code_accounts = self.env['account.account'].sudo().search([('code', '=', '325030004')])
        if code_accounts:
            discount_account_ids.update(code_accounts.ids)

        processed_line_ids = set()
        lines_data = []

        for line in candidate_lines:
            if line.id in processed_line_ids:
                continue

            # Skip unreconciled bank/cash header lines if the move contains reconciled Outstanding Receipts/Payments lines
            if line.move_id and line.move_id.journal_id.type in ('bank', 'cash') and not line.reconciled and not line.matched_debit_ids and not line.matched_credit_ids:
                if any(l.reconciled or l.matched_debit_ids or l.matched_credit_ids for l in line.move_id.line_ids):
                    continue

            matched = _get_reconciled_cluster([line])
            if not matched:
                matched = line.move_id.line_ids.sudo() if line.move_id else line

            # Mark matched move lines and non-bank parent move lines as processed
            for m in matched:
                processed_line_ids.add(m.id)
                if m.move_id:
                    if m.move_id.journal_id.type not in ('bank', 'cash'):
                        for l_sub in m.move_id.line_ids:
                            processed_line_ids.add(l_sub.id)
                    else:
                        if not any(l.reconciled or l.matched_debit_ids or l.matched_credit_ids for l in m.move_id.line_ids):
                            for l_sub in m.move_id.line_ids:
                                processed_line_ids.add(l_sub.id)

            voucher_moves = []
            item_lines = []

            for m in matched:
                if m.move_id.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
                    item_lines.append(m)
                else:
                    payment = m.payment_id or m.move_id.origin_payment_id
                    if payment:
                        item_lines.append(m)
                        # Check if this payment move has linked bank/cash statement entries on its non-receivable lines
                        for l in m.move_id.line_ids:
                            if l.account_id.account_type not in ('asset_receivable', 'liability_payable'):
                                st_lines = l.sudo()._all_reconciled_lines()
                                for st_m in st_lines:
                                    if st_m.move_id != m.move_id and st_m.move_id.journal_id.type in ('bank', 'cash'):
                                        voucher_moves.append(st_m.move_id)
                        if not voucher_moves:
                            voucher_moves.append(m.move_id)
                    else:
                        voucher_moves.append(m.move_id)

            if not voucher_moves:
                continue

            voucher_names = list(set(v.name for v in voucher_moves if v.name))
            voucher_dates = [v.date for v in voucher_moves if v.date]

            if not voucher_names or not voucher_dates:
                continue

            valid_dates = [d for d in voucher_dates if self.from_date <= d <= self.to_date]
            if not valid_dates:
                continue

            reconciliation_date = max(valid_dates)

            # Deduplicate unique voucher moves while preserving order
            unique_voucher_moves = []
            for vm in voucher_moves:
                if vm not in unique_voucher_moves:
                    # Filter out voucher moves using the discount account
                    if discount_account_ids and any(l.account_id.id in discount_account_ids for l in vm.line_ids):
                        continue
                    unique_voucher_moves.append(vm)

            if not unique_voucher_moves:
                continue

            if item_lines:
                partner = line.partner_id or line.move_id.partner_id
                for item in item_lines:
                    if not partner:
                        partner = item.partner_id or item.move_id.partner_id
                customer_name = partner.name if partner else ''

                base_sales_exec_name = ''
                for item in item_lines:
                    base_sales_exec_name = _get_sales_executive_name(item.move_id)
                    if base_sales_exec_name:
                        break
                if not base_sales_exec_name and partner:
                    base_sales_exec_name = _get_sales_executive_name(partner)

                pay_nos = list(set(
                    (item.payment_id.name or item.move_id.name) if (item.payment_id or item.move_id.origin_payment_id) else ''
                    for item in item_lines
                ))
                pay_nos = [p for p in pay_nos if p]
                pay_no_str = ', '.join(pay_nos)

                for vm in unique_voucher_moves:
                    vm_lines = [m for m in matched if m.move_id == vm]
                    rec_lines = [m for m in vm_lines if m.account_id.account_type in ('asset_receivable', 'liability_payable') or m.account_id.reconcile]
                    if rec_lines:
                        vm_amount = sum(max(m.debit, m.credit) for m in rec_lines)
                    elif vm_lines:
                        vm_amount = sum(max(m.debit, m.credit) for m in vm_lines)
                    else:
                        vm_amount = 0.0

                    if vm_amount <= 0 and item_lines:
                        item_sum = sum(max(item.debit, item.credit) for item in item_lines)
                        vm_amount = item_sum / len(unique_voucher_moves) if unique_voucher_moves else item_sum

                    sales_exec_name = _get_sales_executive_name(vm) or base_sales_exec_name
                    vm_date = vm.date if (vm.date and self.from_date <= vm.date <= self.to_date) else reconciliation_date

                    lines_data.append({
                        'date': vm_date,
                        'customer': customer_name,
                        'sales_executive': sales_exec_name,
                        'voucher_no': vm.name or '',
                        'payment_no': pay_no_str,
                        'amount': vm_amount,
                    })
            else:
                # Direct reconciliation between move lines without invoice or account.payment object
                for vm in unique_voucher_moves:
                    vm_lines = [m for m in matched if m.move_id == vm]
                    rec_lines = [m for m in vm_lines if m.account_id.account_type in ('asset_receivable', 'liability_payable') or m.account_id.reconcile]
                    if rec_lines:
                        vm_amount = sum(max(m.debit, m.credit) for m in rec_lines)
                    elif vm_lines:
                        vm_amount = max(max(m.debit, m.credit) for m in vm_lines)
                    else:
                        vm_amount = 0.0

                    if vm_amount <= 0:
                        continue

                    partner = False
                    for m in matched:
                        if m.partner_id:
                            partner = m.partner_id
                            break
                        elif m.move_id.partner_id:
                            partner = m.move_id.partner_id
                            break
                    if not partner:
                        partner = line.partner_id or line.move_id.partner_id

                    customer_name = partner.name if partner else ''

                    sales_exec_name = _get_sales_executive_name(vm)
                    if not sales_exec_name:
                        for m in matched:
                            sales_exec_name = _get_sales_executive_name(m.move_id)
                            if sales_exec_name:
                                break
                    if not sales_exec_name and partner:
                        sales_exec_name = _get_sales_executive_name(partner)

                    vm_date = vm.date if (vm.date and self.from_date <= vm.date <= self.to_date) else reconciliation_date

                    lines_data.append({
                        'date': vm_date,
                        'customer': customer_name,
                        'sales_executive': sales_exec_name,
                        'voucher_no': vm.name or '',
                        'payment_no': '',
                        'amount': vm_amount,
                    })

        return lines_data

    def view_report(self):
        """Open the QWeb HTML report in the Odoo report container."""
        return self.env.ref('reciept_and_payment_report.action_report_receipt_payment').report_action(self)

    def action_print_report_xlsx(self):
        """Generate Excel (XLSX) Report for Reconciled Receipt/Payment Items."""
        lines_data = self._get_report_lines()
        is_receipt = (self.partner_type == 'customer')

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

        if is_receipt:
            # Set Column Widths for Receipt Report (6 columns)
            sheet.set_column('A:A', 15)  # Date
            sheet.set_column('B:B', 28)  # Voucher No
            sheet.set_column('C:C', 28)  # Payment No
            sheet.set_column('D:D', 20)  # Amount
            sheet.set_column('E:E', 25)  # Customer
            sheet.set_column('F:F', 25)  # Sales Executive

            # Dynamic Title
            report_title = "RECEIPT REPORT"
            sheet.merge_range('A1:F1', report_title, title_format)
            sheet.set_row(0, 30)

            # Header Metadata
            partner_name = self.partner_id.name if self.partner_id else "All Customers"
            sheet.write('A3', 'Customer:', label_bold)
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
            sheet.write('E6', 'Customer', header_format)
            sheet.write('F6', 'Sales Executive', header_format)
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
                sheet.write(row_idx, 4, line_data['customer'], cell_format)
                sheet.write(row_idx, 5, line_data['sales_executive'], cell_format)
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

            sheet.write(row_idx, 4, '', total_label_format)
            sheet.write(row_idx, 5, '', total_label_format)
        else:
            # Set Column Widths for Payment Report (4 columns)
            sheet.set_column('A:A', 15)
            sheet.set_column('B:B', 28)
            sheet.set_column('C:C', 28)
            sheet.set_column('D:D', 20)

            # Dynamic Title
            report_title = "PAYMENT REPORT"
            sheet.merge_range('A1:D1', report_title, title_format)
            sheet.set_row(0, 30)

            # Header Metadata
            partner_name = self.partner_id.name if self.partner_id else f"All {self.partner_type.title() if self.partner_type else 'Partner'}s"
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

        report_name = "Receipt_Report" if is_receipt else "Payment_Report"
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