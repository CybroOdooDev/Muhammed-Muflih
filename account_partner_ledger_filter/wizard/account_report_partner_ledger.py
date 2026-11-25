# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import io

import openpyxl
from openpyxl.styles import Alignment

from odoo import fields, models


class AccountPartnerLedger(models.TransientModel):
    """This wizard allows users to generate a Partner Ledger report
        with various options."""
    _inherit = "account.report.partner.ledger"

    partner_ids = fields.Many2many('res.partner', 'partner_ledger_partner_rel',
                                   'id', 'partner_id', string='Partners',
                                   help='Select specific partners for the '
                                        'ledger report.')
    is_include_initial_balance = fields.Boolean(
        string='Include Initial & Closing Balance',
        help='Check this box to include initial and closing balances in the '
             'report.')

    def pre_print_report(self, data):
        """Include partner filter and initial balance flags in report data."""
        data = super().pre_print_report(data)
        data['form'].update({
            'partner_ids': self.partner_ids.ids,
            'initial_balance': self.is_include_initial_balance,
        })
        return data

    def _print_report(self, data):
        """Prepare and print the Partner Ledger PDF report."""
        return super()._print_report(data)

    def action_print_xlsx(self):
        """Export the partner ledger (with optional initial/closing balances) to xlsx."""
        self.ensure_one()
        if not self.is_include_initial_balance:
            return super().action_print_xlsx()

        data = self.pre_print_report(self._xlsx_base_data())
        data['form'].update({
            'reconciled': self.reconciled,
            'amount_currency': self.amount_currency,
        })
        report_model = self.env['report.base_accounting_kit.report_partnerledger']
        values = report_model._get_report_values(None, data)
        lines_fn = values['lines']
        sum_partner_fn = values['sum_partner']
        initial_by_partner = {
            res.get('partner_id') or res.get('name'): res
            for res in (values.get('response') or [])
        }
        columns = [
            {'label': 'Date', 'width': 12},
            {'label': 'JRNL', 'width': 8},
            {'label': 'Account', 'width': 28},
            {'label': 'Ref', 'width': 32},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
            {'label': 'Balance', 'width': 16, 'num': True},
        ]
        rows = []
        for partner in values['docs']:
            init_rec = (
                initial_by_partner.get(partner.id)
                or initial_by_partner.get(partner.name)
                or {}
            )
            initial_debit = init_rec.get('initial_debit') or 0.0
            initial_credit = init_rec.get('initial_credit') or 0.0
            initial_balance = initial_debit - initial_credit
            rows.append({
                'cells': [
                    'Initial Balance', '', '', '',
                    initial_debit, initial_credit, initial_balance,
                ],
                'bold': True,
            })
            partner_debit = sum_partner_fn(data, partner, 'debit')
            partner_credit = sum_partner_fn(data, partner, 'credit')
            partner_balance = sum_partner_fn(data, partner, 'debit - credit')
            rows.append({
                'cells': [
                    partner.name, '', '', '',
                    partner_debit, partner_credit, partner_balance,
                ],
                'bold': True,
            })
            for line in lines_fn(data, partner):
                rows.append({
                    'cells': [
                        line.get('date'), line.get('code'),
                        line.get('a_name') or '',
                        line.get('displayed_name') or '',
                        line.get('debit'), line.get('credit'),
                        (line.get('progress') or 0.0) + initial_balance,
                    ],
                    'indent': 1,
                })
            closing_balance = initial_balance + partner_balance
            rows.append({
                'cells': [
                    'Closing Balance', '', '', '',
                    closing_balance if closing_balance > 0 else 0.0,
                    -closing_balance if closing_balance < 0 else 0.0,
                    closing_balance,
                ],
                'bold': True,
            })
        table = {
            'title': 'Partner Ledger',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Partner Ledger', table)

    def get_xlsx_report(self, data, response):
        """Center and size the Partner Ledger title row so it is not clipped."""
        buf = io.BytesIO()
        res = super().get_xlsx_report(
            data, type('_BufferResponse', (), {'stream': buf})()
        )
        buf.seek(0)
        workbook = openpyxl.load_workbook(buf)
        sheet = workbook.active
        sheet.row_dimensions[1].height = 28
        sheet['A1'].alignment = Alignment(horizontal='center', vertical='center')
        out = io.BytesIO()
        workbook.save(out)
        response.stream.write(out.getvalue())
        return res
