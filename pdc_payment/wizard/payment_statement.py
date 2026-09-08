# -*- coding: utf-8 -*-

import io
import json
from collections import defaultdict
import xlsxwriter
from odoo import api, models, fields
from odoo.tools import json_default


class PaymentStatement(models.TransientModel):
    """ This model represents payment.statement."""
    _name = 'payment.statement'

    statement_type = fields.Selection([('vendor', 'Vendor Statement'), ('customer', 'Customer Statement')],
                                      string="Statement Type", required=True)
    customer_ids = fields.Many2many('res.partner', relation="customer_partner_statement_rel", column1="customer",
                                    column2="payment_statement", string="Customer")
    vendor_ids = fields.Many2many('res.partner', relation="vendor_partner_statement_rel", column1="vendor",
                                  column2="vendor_payment_statement", string="Vendor")
    # date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string="As On Date",default=lambda self: fields.date.today(), required=True, )
    pdc_payment = fields.Boolean(string="Cheque Payment")
    bulk_mail = fields.Boolean(string="Bulk Mail")
    partner_line_ids = fields.One2many(
        'payment.statement.partner.line',
        'statement_id',
        string="Partner Lines"
    )

    @api.onchange('statement_type', 'bulk_mail')
    def _onchange_statement_type(self):
        for rec in self:
            rec.customer_ids = [(5, 0, 0)]
            rec.vendor_ids = [(5, 0, 0)]
            lines = [(5, 0, 0)]
            if rec.bulk_mail and rec.statement_type:
                bulk_mail_rec = self.env['bulk.mail'].search([('type', '=', rec.statement_type)])
                if bulk_mail_rec:
                    partners = bulk_mail_rec.partner_line_ids.mapped('partner_id')
                    for p in partners:
                        lines.append((0, 0, {
                            'partner_id': p.id,
                        }))
                    if rec.statement_type == 'customer':
                        rec.customer_ids = [(6, 0, partners.ids)]
                    elif rec.statement_type == 'vendor':
                        rec.vendor_ids = [(6, 0, partners.ids)]
            rec.partner_line_ids = lines

    @api.onchange('partner_line_ids')
    def _onchange_partner_line_ids(self):
        for rec in self:
            if rec.bulk_mail and rec.statement_type:
                partners = rec.partner_line_ids.mapped('partner_id')
                target_field = 'customer_ids' if rec.statement_type == 'customer' else 'vendor_ids'
                current_partners = getattr(rec, target_field)
                if set(partners.ids) != set(current_partners.ids):
                    setattr(rec, target_field, [(6, 0, partners.ids)])

    @api.onchange('customer_ids', 'vendor_ids')
    def _onchange_customer_vendor_ids(self):
        for rec in self:
            if rec.bulk_mail and rec.statement_type:
                active_partners = rec.customer_ids if rec.statement_type == 'customer' else rec.vendor_ids
                active_ids = set(active_partners.ids)
                current_ids = set(rec.partner_line_ids.mapped('partner_id').ids)
                if active_ids != current_ids:
                    lines = [(5, 0, 0)]
                    for p_id in active_ids:
                        lines.append((0, 0, {'partner_id': p_id}))
                    rec.partner_line_ids = lines






    def domain_statement(self):
        domain = [
            ('state', '=', 'posted'),
            ('invoice_date', '<=', self.date_to),
            ('move_type', '=', 'in_invoice' if self.statement_type == 'vendor' else 'out_invoice'),
            ('company_id', '=', self.env.company.id)
        ]
        if self.vendor_ids:
            domain.append(('partner_id', 'in', self.vendor_ids.ids))
        if self.customer_ids:
            domain.append(('partner_id', 'in', self.customer_ids.ids))
        return domain

    def _is_partial_valid(self, p, date_to):
        """Check if a partial reconciliation was active on or before date_to."""
        return bool(p.max_date and p.max_date <= date_to and p.create_date and p.create_date.date() <= date_to)

    def _is_payment_in_process_as_of_date(self, payment, date_to):
        """Determine if an account.payment was in 'in_process' (uncleared / open) status as of date_to."""
        if not payment or not payment.date or payment.date > date_to:
            return False
        if payment.state == 'in_process':
            return True
        if payment.state == 'paid':
            # Inspect payment lines to see if it was reconciled/cleared only AFTER date_to
            liquidity_lines, counterpart_lines, _writeoff = payment._seek_for_lines()
            reconcilable_liquidity = liquidity_lines.filtered(lambda l: l.account_id.reconcile)

            if reconcilable_liquidity:
                for line in reconcilable_liquidity:
                    partials = line.matched_debit_ids | line.matched_credit_ids
                    valid_partials = [p for p in partials if self._is_partial_valid(p, date_to)]
                    reconciled_as_of_date = sum(p.amount for p in valid_partials)
                    if abs(line.balance) - reconciled_as_of_date > 0.001:
                        # Liquidity line was not yet fully cleared in bank as of date_to
                        return True
                return False

            if counterpart_lines:
                for line in counterpart_lines:
                    partials = line.matched_debit_ids | line.matched_credit_ids
                    valid_partials = [p for p in partials if self._is_partial_valid(p, date_to)]
                    reconciled_as_of_date = sum(p.amount for p in valid_partials)
                    if abs(line.balance) - reconciled_as_of_date > 0.001:
                        return True
                return False

            # Fallback check on all move lines of the payment
            all_partials = payment.move_id.line_ids.matched_debit_ids | payment.move_id.line_ids.matched_credit_ids
            valid_all_partials = [p for p in all_partials if self._is_partial_valid(p, date_to)]
            if not valid_all_partials:
                return True

        return False

    def _get_report_data(self):
        domain = self.domain_statement()

        moves = self.env['account.move'].sudo().search(domain, order='invoice_date asc')

        partners = defaultdict(lambda: {
            'partner_id': None,
            'partner': '',
            'invoices': [],
            'payments': [],
            'payment_ids': set(),
            'invoice_total': 0.0,
            'balance_total': 0.0,
            'pdc_total': 0.0,
            'payment_total': 0.0,
        })

        fully_reversed_inv_ids = set()
        excluded_cn_move_ids = set()

        for move in moves:
            partner_id = move.partner_id
            if not partner_id:
                continue
            pid = partner_id.id
            if pid not in partners and partner_id.commercial_partner_id.id in partners:
                pid = partner_id.commercial_partner_id.id
            pname = partner_id.display_name or partner_id.name

            partner = partners[pid]
            partner['partner_id'] = pid
            if not partner['partner']:
                partner['partner'] = pname

            # Calculate historical residual and reconciliations as of date_to
            rec_pay_lines = move.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
            )

            reconciled_as_of_date_to = 0.0
            reconciled_payments_list = []
            has_refund_as_of_date_to = False

            for line in rec_pay_lines:
                line_partials = [p for p in (line.matched_debit_ids | line.matched_credit_ids) if self._is_partial_valid(p, self.date_to)]
                for p in line_partials:
                    reconciled_as_of_date_to += p.amount
                    counterpart = p.credit_move_id if p.debit_move_id.id == line.id else p.debit_move_id

                    if counterpart.move_id.move_type in ('out_refund', 'in_refund'):
                        excluded_cn_move_ids.add(counterpart.move_id.id)
                        has_refund_as_of_date_to = True

                    pay = counterpart.payment_id or (counterpart.move_id.payment_id if hasattr(counterpart.move_id, 'payment_id') else None)
                    if pay:
                        reconciled_payments_list.append((pay, p.amount, counterpart.date or p.max_date))

            hist_residual = max(0.0, move.amount_total - reconciled_as_of_date_to)

            pdc_amount = 0.0

            for payment, amt, pay_date in reconciled_payments_list:
                if not self._is_payment_in_process_as_of_date(payment, self.date_to):
                    continue
                if self.pdc_payment and not payment.pdc_payment:
                    continue
                if not payment.amount or payment.amount == 0:
                    continue

                partner['payment_total'] += amt
                pdc_amount += amt

                if payment.id not in partner['payment_ids']:
                    partner['payment_ids'].add(payment.id)
                    partner['payments'].append({
                        'payment': payment.name or getattr(payment, 'ref', '') or '',
                        'payment_date': (payment.date or pay_date).strftime('%d/%m/%Y'),
                        'amount': payment.amount,
                        'pdc_payment': payment.pdc_payment,
                        'cheque_no': payment.cheque_no or '',
                        'maturity_date': payment.maturity_date.strftime('%d/%m/%Y') if payment.maturity_date else '',
                    })

            # Skip invoice only if both balance and PDC amount are zero as of date_to
            if hist_residual < 0.01 and pdc_amount < 0.01:
                if has_refund_as_of_date_to:
                    fully_reversed_inv_ids.add(move.id)
                continue

            partner['invoice_total'] += move.amount_total
            partner['balance_total'] += hist_residual
            partner['pdc_total'] += pdc_amount

            partner['invoices'].append({
                'date': move.invoice_date,
                'invoice_date': move.invoice_date.strftime('%d/%m/%Y') if move.invoice_date else '',
                'invoice_no': move.name or '',
                'invoice_amount': move.amount_total,
                'balance': hist_residual,
                'pdc_amount': pdc_amount,
                'ref': move.ref or '',
            })

        # Process account.payment (for in-process entries and new_reference entries)
        pay_domain = [
            ('state', 'in', ['in_process', 'paid']),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.env.company.id),
            ('payment_type', '=', 'outbound' if self.statement_type == 'vendor' else 'inbound'),
        ]
        if self.statement_type == 'vendor' and self.vendor_ids:
            pay_domain.append(('partner_id', 'in', self.vendor_ids.ids))
        elif self.statement_type == 'customer' and self.customer_ids:
            pay_domain.append(('partner_id', 'in', self.customer_ids.ids))

        if self.pdc_payment:
            pay_domain.append(('pdc_payment', '=', True))

        all_payments = self.env['account.payment'].sudo().search(pay_domain, order='date asc')

        for pay in all_payments:
            if not pay.partner_id:
                continue
            if not pay.amount or pay.amount == 0:
                continue

            pid = pay.partner_id.id
            if pid not in partners and pay.partner_id.commercial_partner_id.id in partners:
                pid = pay.partner_id.commercial_partner_id.id
            pname = pay.partner_id.display_name or pay.partner_id.name
            partner = partners[pid]
            partner['partner_id'] = pid
            if not partner['partner']:
                partner['partner'] = pname

            pay_ref = (
                getattr(pay, 'ref', None)
                or getattr(pay, 'memo', None)
                or (pay.move_id.ref if hasattr(pay, 'move_id') and pay.move_id else '')
                or ''
            )

            # Add to second table payments list if payment was in_process as of date_to and not already added
            if self._is_payment_in_process_as_of_date(pay, self.date_to) and pay.id not in partner['payment_ids']:
                partner['payment_ids'].add(pay.id)
                partner['payments'].append({
                    'payment': pay.name or pay_ref or '',
                    'payment_date': pay.date.strftime('%d/%m/%Y') if pay.date else '',
                    'amount': pay.amount,
                    'pdc_payment': pay.pdc_payment,
                    'cheque_no': pay.cheque_no or '',
                    'maturity_date': pay.maturity_date.strftime('%d/%m/%Y') if pay.maturity_date else '',
                })
                partner['payment_total'] += pay.amount

            # If new_reference is non-zero, also include reference adjustment entry in first table
            if pay.new_reference != 0:
                new_ref_val = abs(pay.new_reference)
                inv_amt = -new_ref_val
                bal_amt = -new_ref_val
                pdc_amount = new_ref_val

                partner['invoice_total'] += inv_amt
                partner['balance_total'] += bal_amt
                partner['pdc_total'] += pdc_amount

                partner['invoices'].append({
                    'date': pay.date,
                    'invoice_date': pay.date.strftime('%d/%m/%Y') if pay.date else '',
                    'invoice_no': pay.name or '',
                    'invoice_amount': inv_amt,
                    'balance': bal_amt,
                    'pdc_amount': pdc_amount,
                    'ref': pay_ref,
                })

        # Process Manual Journal Entries, Bank/Cash entries, and Journal Items (unmatched or open balance lines on receivable/payable)
        if not self.pdc_payment:
            acc_type = 'liability_payable' if self.statement_type == 'vendor' else 'asset_receivable'
            line_domain = [
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.env.company.id),
                ('account_id.account_type', '=', acc_type),
                ('move_id.move_type', '=', 'entry'),
            ]
            if self.date_to:
                line_domain.append(('date', '<=', self.date_to))

            if self.statement_type == 'vendor' and self.vendor_ids:
                line_domain.append(('partner_id', 'in', self.vendor_ids.ids))
            elif self.statement_type == 'customer' and self.customer_ids:
                line_domain.append(('partner_id', 'in', self.customer_ids.ids))

            entry_lines = self.env['account.move.line'].sudo().search(line_domain, order='date asc')

            for bl in entry_lines:
                if not bl.partner_id:
                    continue

                pid = bl.partner_id.id
                if pid not in partners and bl.partner_id.commercial_partner_id.id in partners:
                    pid = bl.partner_id.commercial_partner_id.id
                partner = partners[pid]

                # Skip if associated with an account.payment (already processed in payment section)
                if bl.payment_id or (hasattr(bl, 'move_id') and getattr(bl.move_id, 'payment_id', None)):
                    continue

                # Check partial reconciliations on or before date_to
                bl_partials = [p for p in (bl.matched_debit_ids | bl.matched_credit_ids) if self._is_partial_valid(p, self.date_to)]
                reconciled_bl_as_of_date_to = sum(p.amount for p in bl_partials)
                residual_as_of_date_to = abs(bl.balance) - reconciled_bl_as_of_date_to

                # Skip if the journal entry is fully reconciled as of date_to
                if abs(residual_as_of_date_to) < 0.001:
                    continue

                if self.statement_type == 'customer':
                    entry_amt = residual_as_of_date_to if bl.debit > bl.credit else -residual_as_of_date_to
                else:
                    entry_amt = residual_as_of_date_to if bl.credit > bl.debit else -residual_as_of_date_to

                pname = bl.partner_id.display_name or bl.partner_id.name
                partner['partner_id'] = pid
                if not partner['partner']:
                    partner['partner'] = pname

                inv_date = bl.date
                partner['invoice_total'] += entry_amt
                partner['balance_total'] += entry_amt

                ref_val = (
                    bl.name
                    or (bl.move_id.ref if hasattr(bl, 'move_id') and bl.move_id else '')
                    or ''
                )

                partner['invoices'].append({
                    'date': inv_date,
                    'invoice_date': inv_date.strftime('%d/%m/%Y') if inv_date else '',
                    'invoice_no': (bl.move_id.name if hasattr(bl, 'move_id') and bl.move_id else '') or bl.name or '',
                    'invoice_amount': entry_amt,
                    'balance': entry_amt,
                    'pdc_amount': 0.0,
                    'ref': ref_val,
                })

        # Process Credit Notes (both standard and sale return)
        cn_domain = [
            ('state', '=', 'posted'),
            ('move_type', '=', 'in_refund' if self.statement_type == 'vendor' else 'out_refund'),
            ('company_id', '=', self.env.company.id),
        ]
        if self.date_to:
            cn_domain.append(('invoice_date', '<=', self.date_to))

        if self.statement_type == 'vendor' and self.vendor_ids:
            cn_domain.append(('partner_id', 'in', self.vendor_ids.ids))
        elif self.statement_type == 'customer' and self.customer_ids:
            cn_domain.append(('partner_id', 'in', self.customer_ids.ids))

        cn_moves = self.env['account.move'].sudo().search(cn_domain, order='invoice_date asc')

        for move in cn_moves:
            if not move.partner_id:
                continue

            # Calculate residual as of date_to
            cn_lines = move.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
            )
            reconciled_cn_as_of_date_to = 0.0
            for line in cn_lines:
                line_partials = [p for p in (line.matched_debit_ids | line.matched_credit_ids) if self._is_partial_valid(p, self.date_to)]
                reconciled_cn_as_of_date_to += sum(p.amount for p in line_partials)

            cn_balance_as_of_date_to = max(0.0, move.amount_total - reconciled_cn_as_of_date_to)

            # Skip credit notes with 0 residual as of date_to
            if cn_balance_as_of_date_to < 0.01:
                continue

            # Skip credit notes related to fully reversed invoices or already reconciled against invoices as of date_to
            if move.id in excluded_cn_move_ids:
                continue

            orig_inv = getattr(move, 'reversed_entry_id', None)
            if orig_inv and orig_inv.id in fully_reversed_inv_ids:
                continue

            pid = move.partner_id.id
            if pid not in partners and move.partner_id.commercial_partner_id.id in partners:
                pid = move.partner_id.commercial_partner_id.id
            pname = move.partner_id.display_name or move.partner_id.name
            partner = partners[pid]
            partner['partner_id'] = pid
            if not partner['partner']:
                partner['partner'] = pname

            inv_date = move.invoice_date or move.date
            cn_amt = -abs(cn_balance_as_of_date_to)

            partner['invoice_total'] += cn_amt
            partner['balance_total'] += cn_amt

            ref_val = (
                move.ref
                or move.invoice_origin
                or (move.sale_return_id.name if hasattr(move, 'sale_return_id') and move.sale_return_id else '')
                or ''
            )

            partner['invoices'].append({
                'date': inv_date,
                'invoice_date': inv_date.strftime('%d/%m/%Y') if inv_date else '',
                'invoice_no': move.name or '',
                'invoice_amount': cn_amt,
                'balance': cn_amt,
                'pdc_amount': 0.0,
                'ref': ref_val,
            })

        for partner in partners.values():
            partner['invoices'].sort(key=lambda x: x['date'])
            for inv in partner['invoices']:
                inv.pop('date', None)
            partner.pop('payment_ids', None)

            # Precalculate address and cheque data status for PDF & XLS reports
            if partner['partner_id']:
                partner_obj = self.env['res.partner'].sudo().browse(partner['partner_id'])
                partner_address = partner_obj.street or ''
                if partner_obj.street:
                    partner_address += ', '
                if partner_obj.street2:
                    partner_address += partner_obj.street2 + ', '
                if partner_obj.city:
                    partner_address += partner_obj.city + ', '
                if partner_obj.state_id:
                    partner_address += partner_obj.state_id.name + ', '
                if partner_obj.zip:
                    partner_address += partner_obj.zip + ', '
                if partner_obj.country_id:
                    partner_address += partner_obj.country_id.name
                partner['partner_address'] = partner_address.strip(', ')
            else:
                partner['partner_address'] = ''

            payments = partner.get('payments', [])
            partner['payment_total'] = sum(p['amount'] for p in payments)
            partner['has_cheque_data'] = any(
                p.get('cheque_no', '').strip() or p.get('maturity_date', '').strip()
                for p in payments
            )

        data = {
            'model_id': self.id,
            'date_to': self.date_to.strftime('%d/%m/%Y'),
            'statement_type': self.statement_type,
            'partners': list(partners.values()),
        }

        return data

    def print_xls(self):
        data = self._get_report_data()
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'payment.statement',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Statement Report',
            },
            'report_type': 'xlsx',
        }

    def print_pdf(self):
        data = self._get_report_data()
        return self.env.ref('pdc_payment.action_report_payment_statement').report_action(self, data=data)

    def print_html(self):
        data = self._get_report_data()
        return self.env.ref('pdc_payment.action_report_payment_statement_html').report_action(self, data=data)


    def get_xlsx_report(self, data, response):


        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Statement')

        # Formats
        head = workbook.add_format({'bold': True, 'align': 'center'})
        vendor = workbook.add_format({'bold': True})
        table_head = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        date_fmt = workbook.add_format({'align': 'center', 'num_format': 'dd/mm/yyyy'})
        amt = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        amt_bold = workbook.add_format({'bold': True, 'align': 'right', 'num_format': '#,##0.00'})
        ref_label = workbook.add_format({'bold': True, 'italic': True})
        payment_label = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        ref_amt = workbook.add_format({'align': 'right', 'italic': True, 'num_format': '#,##0.00'})
        company_fmt = workbook.add_format({'bold': True, 'align': 'left'})
        heading_bg = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#E6E6FA'})

        # Add company logo if available
        company = self.env.company
        if company.logo:
            try:
                import base64
                # Decode base64 image data
                logo_binary = base64.b64decode(company.logo)
                logo_data = io.BytesIO(logo_binary)
                sheet.insert_image('B2', 'logo', {'image_data': logo_data, 'x_scale': 0.2, 'y_scale': 0.2, 'x_offset': 30, 'object_position': 2})
            except Exception:
                pass

        report_title = 'Vendor Statement' if data.get('statement_type') == 'vendor' else 'Customer Statement'
        sheet.merge_range(
            'A6:H6',
            report_title,
            heading_bg
        )

        # Company Details
        company_details = company.name or ''
        if company.city:
            company_details += ', ' + company.city
        if company.country_id:
            company_details += ', ' + company.country_id.name
        if company.zip:
            company_details += ' - ' + company.zip

        sheet.merge_range('C2:H2', company_details, company_fmt)

        sheet.merge_range('B7:C7', 'As on Date:', head)
        sheet.merge_range('D7:E7', data['date_to'], date_fmt)

        row = 8

        partner_label = 'Vendor' if data.get('statement_type') == 'vendor' else 'Customer'
        for partner in data['partners']:
            sheet.merge_range(row, 0, row, 7, f"{partner_label} : {partner['partner']}", vendor)
            row += 1

            # Vendor/Customer Address
            partner_obj = self.env['res.partner'].sudo().browse(partner['partner_id'])
            partner_address = partner_obj.street or ''
            if partner_obj.street:
                partner_address += ', '
            if partner_obj.street2:
                partner_address += partner_obj.street2 + ', '
            if partner_obj.city:
                partner_address += partner_obj.city + ', '
            if partner_obj.state_id:
                partner_address += partner_obj.state_id.name + ', '
            if partner_obj.zip:
                partner_address += partner_obj.zip + ', '
            if partner_obj.country_id:
                partner_address += partner_obj.country_id.name

            if partner_address:
                sheet.merge_range(row, 1, row, 7, partner_address, company_fmt)
                row += 1

            row += 1

            # Invoice Header - different for vendor vs customer
            if data['statement_type'] == 'vendor':
                headers = ['Sl No', 'Invoice Date', 'Invoice No', 'Bill Reference', 'Invoice Amount', 'PDC Amount', 'Balance', 'Cumulative Balance']
            else:
                headers = ['Sl No', 'Invoice Date', 'Invoice No', 'Customer Ref', 'Invoice Amount', 'PDC Amount', 'Balance', 'Cumulative Balance']

            sheet.write_row(row, 0, headers, table_head)
            row += 1

            # Invoice Lines
            cum_balance = 0.0
            for i, inv in enumerate(partner['invoices'], 1):
                sheet.write(row, 0, i)
                sheet.write(row, 1, inv['invoice_date'], date_fmt)
                sheet.write(row, 2, inv['invoice_no'])

                # Different reference field based on statement type
                sheet.write(row, 3, inv['ref'])
                sheet.write(row, 4, inv['invoice_amount'], amt)
                sheet.write(row, 5, inv['pdc_amount'], amt)
                sheet.write(row, 6, inv['balance'], amt)
                cum_balance += inv['balance']
                sheet.write(row, 7, cum_balance, amt)

                row += 1

            # Invoice Totals
            sheet.write(row, 3, 'Total', table_head)
            sheet.write(row, 4, partner['invoice_total'], amt_bold)
            sheet.write(row, 5, partner['pdc_total'], amt_bold)
            sheet.write(row, 6, partner['balance_total'], amt_bold)
            sheet.write(row, 7, partner['balance_total'], amt_bold)
            row += 2

            payments = partner.get('payments', [])
            payment_total = sum(p['amount'] for p in payments)

            if payments:
                has_cheque_data_partner = any(
                    p.get('cheque_no', '').strip() or p.get('maturity_date', '').strip()
                    for p in payments
                )

                if has_cheque_data_partner:
                    headers = ['Sl No', 'Payment Date', 'Payment No', 'Cheque Number', 'Cheque Date', 'Payment Amount']
                else:
                    headers = ['Sl No', 'Payment Date', 'Payment No', 'Payment Amount']

                sheet.write_row(row, 1, headers, table_head)
                row += 1

                for i, p in enumerate(payments, 1):
                    col = 1
                    sheet.write(row, col, i)
                    col += 1
                    sheet.write(row, col, p['payment_date'], date_fmt)
                    col += 1
                    sheet.write(row, col, p['payment'], payment_label)
                    col += 1

                    if has_cheque_data_partner:
                        sheet.write(row, col, p.get('cheque_no', ''))
                        col += 1
                        sheet.write(row, col, p.get('maturity_date', ''))
                        col += 1

                    sheet.write(row, col, p['amount'], amt)
                    row += 1

                total_col = 6 if has_cheque_data_partner else 4
                sheet.write(row, total_col - 1, 'Total', table_head)
                sheet.write(row, total_col, payment_total, amt_bold)
                row += 2

            row += 2

        sheet.set_column('A:A', 6)
        sheet.set_column('B:C', 22)
        sheet.set_column('D:H', 20)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _generate_partner_xlsx_bytes(self, partner_data):
        import io
        import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Statement')

        # Formats
        head = workbook.add_format({'bold': True, 'align': 'center'})
        vendor = workbook.add_format({'bold': True})
        table_head = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        date_fmt = workbook.add_format({'align': 'center', 'num_format': 'dd/mm/yyyy'})
        amt = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        amt_bold = workbook.add_format({'bold': True, 'align': 'right', 'num_format': '#,##0.00'})
        payment_label = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        company_fmt = workbook.add_format({'bold': True, 'align': 'left'})
        heading_bg = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#E6E6FA'})

        company = self.env.company
        if company.logo:
            try:
                import base64
                logo_binary = base64.b64decode(company.logo)
                logo_data = io.BytesIO(logo_binary)
                sheet.insert_image('B2', 'logo', {'image_data': logo_data, 'x_scale': 0.2, 'y_scale': 0.2, 'x_offset': 30, 'object_position': 2})
            except Exception:
                pass

        report_title = 'Vendor Statement' if self.statement_type == 'vendor' else 'Customer Statement'
        sheet.merge_range('A6:H6', report_title, heading_bg)

        company_details = company.name or ''
        if company.city:
            company_details += ', ' + company.city
        if company.country_id:
            company_details += ', ' + company.country_id.name
        if company.zip:
            company_details += ' - ' + company.zip

        sheet.merge_range('C2:H2', company_details, company_fmt)
        sheet.merge_range('B7:C7', 'As on Date:', head)
        sheet.merge_range('D7:E7', self.date_to.strftime('%d/%m/%Y'), date_fmt)

        row = 8
        partner_label = 'Vendor' if self.statement_type == 'vendor' else 'Customer'
        sheet.merge_range(row, 0, row, 7, f"{partner_label} : {partner_data['partner']}", vendor)
        row += 1

        if partner_data.get('partner_address'):
            sheet.merge_range(row, 1, row, 7, partner_data['partner_address'], company_fmt)
            row += 1

        row += 1

        if self.statement_type == 'vendor':
            headers = ['Sl No', 'Invoice Date', 'Invoice No', 'Bill Reference', 'Invoice Amount', 'PDC Amount', 'Balance', 'Cumulative Balance']
        else:
            headers = ['Sl No', 'Invoice Date', 'Invoice No', 'Customer Ref', 'Invoice Amount', 'PDC Amount', 'Balance', 'Cumulative Balance']

        sheet.write_row(row, 0, headers, table_head)
        row += 1

        cum_balance = 0.0
        for i, inv in enumerate(partner_data.get('invoices', []), 1):
            sheet.write(row, 0, i)
            sheet.write(row, 1, inv['invoice_date'], date_fmt)
            sheet.write(row, 2, inv['invoice_no'])
            sheet.write(row, 3, inv['ref'])
            sheet.write(row, 4, inv['invoice_amount'], amt)
            sheet.write(row, 5, inv['pdc_amount'], amt)
            sheet.write(row, 6, inv['balance'], amt)
            cum_balance += inv['balance']
            sheet.write(row, 7, cum_balance, amt)
            row += 1

        sheet.write(row, 3, 'Total', table_head)
        sheet.write(row, 4, partner_data.get('invoice_total', 0.0), amt_bold)
        sheet.write(row, 5, partner_data.get('pdc_total', 0.0), amt_bold)
        sheet.write(row, 6, partner_data.get('balance_total', 0.0), amt_bold)
        sheet.write(row, 7, partner_data.get('balance_total', 0.0), amt_bold)
        row += 2

        payments = partner_data.get('payments', [])
        payment_total = sum(p['amount'] for p in payments)

        if payments:
            has_cheque_data_partner = partner_data.get('has_cheque_data', False)
            if has_cheque_data_partner:
                headers = ['Sl No', 'Payment Date', 'Payment No', 'Cheque Number', 'Cheque Date', 'Payment Amount']
            else:
                headers = ['Sl No', 'Payment Date', 'Payment No', 'Payment Amount']

            sheet.write_row(row, 1, headers, table_head)
            row += 1

            for i, p in enumerate(payments, 1):
                col = 1
                sheet.write(row, col, i)
                col += 1
                sheet.write(row, col, p['payment_date'], date_fmt)
                col += 1
                sheet.write(row, col, p['payment'], payment_label)
                col += 1

                if has_cheque_data_partner:
                    sheet.write(row, col, p.get('cheque_no', ''))
                    col += 1
                    sheet.write(row, col, p.get('maturity_date', ''))
                    col += 1

                sheet.write(row, col, p['amount'], amt)
                row += 1

            total_col = 6 if has_cheque_data_partner else 4
            sheet.write(row, total_col - 1, 'Total', table_head)
            sheet.write(row, total_col, payment_total, amt_bold)
            row += 2

        sheet.set_column('A:A', 6)
        sheet.set_column('B:C', 22)
        sheet.set_column('D:H', 20)

        workbook.close()
        xlsx_data = output.getvalue()
        output.close()
        return xlsx_data

    def action_send_mail(self):
        """Send separate statement emails with attached XLSX report to each selected partner."""
        import base64

        report_data = self._get_report_data()
        partners_data = report_data.get('partners', [])

        selected_partner_ids = set()
        if self.bulk_mail and self.partner_line_ids:
            selected_partner_ids = set(self.partner_line_ids.mapped('partner_id.id'))
        elif self.statement_type == 'customer' and self.customer_ids:
            selected_partner_ids = set(self.customer_ids.ids)
        elif self.statement_type == 'vendor' and self.vendor_ids:
            selected_partner_ids = set(self.vendor_ids.ids)

        sent_count = 0
        for partner_dict in partners_data:
            pid = partner_dict.get('partner_id')
            if selected_partner_ids and pid not in selected_partner_ids:
                continue

            partner_obj = self.env['res.partner'].browse(pid)
            if not partner_obj.email:
                continue

            xlsx_bytes = self._generate_partner_xlsx_bytes(partner_dict)
            file_name = f"{self.statement_type.capitalize()}_Statement_{(partner_dict['partner'] or '').replace('/', '_')}.xlsx"

            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'datas': base64.b64encode(xlsx_bytes),
                'res_model': 'payment.statement',
                'res_id': self.id,
                'type': 'binary',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            subject = f"{'Vendor' if self.statement_type == 'vendor' else 'Customer'} Statement - {partner_dict['partner']}"
            body_html = f"""
                <p>Dear {partner_dict['partner']},</p>
                <p>Please find attached your statement as of <b>{report_data.get('date_to', '')}</b>.</p>
                <p>Thank you,</p>
                <p><b>{self.env.company.name}</b></p>
            """

            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_to': partner_obj.email,
                'attachment_ids': [(6, 0, [attachment.id])],
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
            sent_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Emails Sent',
                'message': f'Successfully sent {sent_count} individual statement email(s).',
                'type': 'success',
                'sticky': False,
            }
        }








