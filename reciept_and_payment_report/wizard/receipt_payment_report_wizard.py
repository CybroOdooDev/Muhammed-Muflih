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
        """Fetch reconciled receipt/payment items data for XLSX and HTML QWeb reports using fast SQL query."""
        allowed_company_ids = self.env.companies.ids

        # Fetch discount account IDs to exclude moves with write-offs/discounts if applicable
        discount_account_ids = []
        discount_account_ref = self.env.ref('__export__.account_account_3516_948713fc', raise_if_not_found=False)
        if discount_account_ref:
            discount_account_ids.append(discount_account_ref.id)
        code_accounts = self.env['account.account'].sudo().search([('code', '=', '325030004')])
        if code_accounts:
            discount_account_ids.extend(code_accounts.ids)
        discount_account_ids = list(set(discount_account_ids))

        # Check if x_studio_sales_executive field exists on models
        has_move_exec = 'x_studio_sales_executive' in self.env['account.move']._fields
        has_partner_exec = 'x_studio_sales_executive' in self.env['res.partner']._fields

        move_exec_select = "pm.x_studio_sales_executive" if has_move_exec else "NULL"
        bank_exec_select = "bm.x_studio_sales_executive" if has_move_exec else "NULL"
        part_p_exec_select = "part_p.x_studio_sales_executive" if has_partner_exec else "NULL"
        part_b_exec_select = "part_b.x_studio_sales_executive" if has_partner_exec else "NULL"
        part_unrec_exec_select = "part.x_studio_sales_executive" if has_partner_exec else "NULL"

        partner_id_val = self.partner_id.id if self.partner_id else None
        partner_type_val = self.partner_type or 'customer'

        params = [
            allowed_company_ids,
            self.from_date,
            self.to_date,
            partner_type_val,
            partner_type_val,
            partner_type_val,
            partner_type_val,
            partner_id_val,
            partner_id_val,
            discount_account_ids or [0],
        ]

        query = f'''
            WITH bank_statement_recons AS (
                -- 1. Partial reconciliations between Bank/Cash Statement lines and separate Payment/Invoice moves
                SELECT 
                    pr.id AS pr_id,
                    pr.amount AS amount,
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM account_bank_statement_line st2 WHERE st2.move_id = pm.id)
                        THEN GREATEST(bm.date, pm.date)
                        ELSE bm.date
                    END AS date,
                    bm.name AS voucher_no,
                    CASE 
                        WHEN pp.id IS NOT NULL THEN pm.name
                        WHEN pm.move_type IN ('out_invoice', 'in_invoice', 'out_refund', 'in_refund') THEN pm.name
                        ELSE COALESCE(NULLIF(pm.ref, ''), pm.name)
                    END AS payment_no,
                    COALESCE(pl.partner_id, bl.partner_id, pm.partner_id, bm.partner_id) AS partner_id,
                    COALESCE(part_p.name, part_b.name) AS customer_name,
                    COALESCE({move_exec_select}, {bank_exec_select}, {part_p_exec_select}, {part_b_exec_select}) AS sales_exec_id,
                    bm.id AS b_move_id,
                    pm.id AS p_move_id,
                    bm.company_id AS company_id,
                    pp.partner_type AS payment_partner_type,
                    NULL::varchar AS line_account_type,
                    CASE WHEN st.amount > 0 THEN 'inbound' ELSE 'outbound' END AS direction
                FROM account_partial_reconcile pr
                JOIN account_move_line bl ON bl.id IN (pr.debit_move_id, pr.credit_move_id)
                JOIN account_bank_statement_line st ON st.move_id = bl.move_id
                JOIN account_move bm ON bm.id = bl.move_id
                JOIN account_move_line pl ON pl.id = CASE WHEN bl.id = pr.debit_move_id THEN pr.credit_move_id ELSE pr.debit_move_id END
                JOIN account_move pm ON pm.id = pl.move_id AND pm.id != bm.id
                LEFT JOIN account_payment pp ON pp.move_id = pm.id
                LEFT JOIN res_partner part_p ON part_p.id = COALESCE(pl.partner_id, pm.partner_id)
                LEFT JOIN res_partner part_b ON part_b.id = COALESCE(bl.partner_id, bm.partner_id)
                WHERE bm.state = 'posted' AND pm.state = 'posted'
                  AND (
                      -- Normal case: partner move is NOT a bank statement → keep the row
                      NOT EXISTS (SELECT 1 FROM account_bank_statement_line st2 WHERE st2.move_id = pm.id)
                      OR
                      -- Both sides are bank statements → keep only one direction to avoid swap-duplicate
                      bm.id < pm.id
                  )
                  AND NOT (
                      -- Exclude POS cash in/out liquidity transfers by their label pattern
                      st.pos_session_id IS NOT NULL
                      AND (st.payment_ref LIKE '%%-in-%%' OR st.payment_ref LIKE '%%-out-%%')
                  )
            ),
            direct_bank_statement_moves AS (
                -- 2. Bank Statement moves with counterpart receivable/payable lines in SAME move (manual operation / open balance)
                SELECT 
                    0 AS pr_id,
                    GREATEST(l.credit, l.debit) AS amount,
                    bm.date AS date,
                    bm.name AS voucher_no,
                    COALESCE(NULLIF(l.name, ''), NULLIF(bm.ref, ''), '') AS payment_no,
                    COALESCE(l.partner_id, bm.partner_id) AS partner_id,
                    part.name AS customer_name,
                    COALESCE({bank_exec_select}, {part_unrec_exec_select}) AS sales_exec_id,
                    bm.id AS b_move_id,
                    bm.id AS p_move_id,
                    bm.company_id AS company_id,
                    NULL::varchar AS payment_partner_type,
                    acc.account_type::varchar AS line_account_type,
                    CASE WHEN st.amount > 0 THEN 'inbound' ELSE 'outbound' END AS direction
                FROM account_bank_statement_line st
                JOIN account_move bm ON bm.id = st.move_id
                JOIN account_move_line l ON l.move_id = bm.id
                JOIN account_account acc ON acc.id = l.account_id
                LEFT JOIN res_partner part ON part.id = COALESCE(l.partner_id, bm.partner_id)
                WHERE bm.state = 'posted'
                  AND acc.account_type IN ('asset_receivable', 'liability_payable')
                  AND NOT EXISTS (
                      -- Exclude only lines that are already captured via partial reconciliation in CTE 1
                      SELECT 1 FROM account_partial_reconcile apr
                      WHERE l.id IN (apr.debit_move_id, apr.credit_move_id)
                  )
            ),
            combined AS (
                SELECT * FROM bank_statement_recons
                UNION ALL
                SELECT * FROM direct_bank_statement_moves
            )
            SELECT 
                c.date,
                c.voucher_no,
                c.payment_no,
                c.amount,
                c.customer_name AS customer,
                emp.name AS sales_executive
            FROM combined c
            LEFT JOIN res_partner partner ON partner.id = c.partner_id
            LEFT JOIN hr_employee emp ON emp.id = c.sales_exec_id
            WHERE c.company_id = ANY(%s)
              AND c.date >= %s AND c.date <= %s
              AND (
                (%s = 'customer' AND (c.payment_partner_type = 'customer' OR partner.customer_rank > 0 OR c.line_account_type = 'asset_receivable' OR partner.id IS NULL))
                OR
                (%s = 'vendor' AND (c.payment_partner_type = 'supplier' OR partner.supplier_rank > 0 OR c.line_account_type = 'liability_payable' OR partner.id IS NULL))
              )
              AND (
                (%s = 'customer' AND c.direction = 'inbound')
                OR
                (%s = 'vendor' AND c.direction = 'outbound')
              )
              AND (%s::int IS NULL OR c.partner_id = %s)
              AND NOT EXISTS (
                  SELECT 1 FROM account_move_line d_aml 
                  WHERE d_aml.move_id IN (c.b_move_id, c.p_move_id) 
                    AND d_aml.account_id = ANY(%s)
              )
            ORDER BY c.date DESC, c.voucher_no, c.payment_no
        '''
        self.env.cr.execute(query, params)
        rows = self.env.cr.dictfetchall()

        lines_data = []
        for r in rows:
            lines_data.append({
                'date': r['date'],
                'voucher_no': r['voucher_no'] or '',
                'payment_no': r['payment_no'] or '',
                'amount': float(r['amount'] or 0.0),
                'customer': r['customer'] or '',
                'sales_executive': r['sales_executive'] or '',
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