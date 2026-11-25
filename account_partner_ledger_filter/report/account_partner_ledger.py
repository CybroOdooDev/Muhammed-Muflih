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
import time

from odoo import api, models
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    """This class extends the functionality of the base Partner Ledger report
    to provide additional features and customization."""
    _inherit = 'report.base_accounting_kit.report_partnerledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the values needed for the Partner Ledger report.
        data: Additional data for the report
        return: Dictionary containing report data"""
        if not data.get('form'):
            raise UserError(
                self.env._("Form content is missing, this report cannot be printed."))
        data['computed'] = {}
        partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(
            **data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = [
                'liability_payable', 'asset_receivable',
            ]

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.account_type IN %s
              AND a.active""",
                            (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in
                                           self.env.cr.fetchall()]
        account_ids = tuple(data['computed']['account_ids']) or (0,)
        params = [tuple(data['computed']['move_state']),
                  account_ids] + query_get_data[2]
        reconcile_clause = "" if data['form'].get(
            'reconciled') else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND account.active
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        partner_ids = data['form'].get('partner_ids')
        if not partner_ids:
            partner_ids = [res['partner_id'] for res in
                           self.env.cr.dictfetchall()]
        partners = partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))
        if data['form'].get('initial_balance') and partner_ids:
            record = []
            if data['form'].get('date_from'):
                company_id = (
                    data['form'].get('used_context', {}).get('company_id')
                    or self.env.company.id
                )
                add_query = """
                    SELECT a.partner_id, c.name,
                           COALESCE(SUM(a.debit), 0.0) AS initial_debit,
                           COALESCE(SUM(a.credit), 0.0) AS initial_credit
                    FROM account_move_line a
                    JOIN account_move b ON a.move_id = b.id
                    JOIN res_partner c ON a.partner_id = c.id
                    WHERE a.partner_id IN %s
                      AND a.account_id IN %s
                      AND a.company_id = %s
                      AND b.state IN %s
                      AND a.date < %s
                """
                add_params = [
                    tuple(partner_ids),
                    account_ids,
                    company_id,
                    tuple(data['computed']['move_state']),
                    data['form']['date_from'],
                ]
                if not data['form'].get('reconciled'):
                    add_query += " AND a.full_reconcile_id IS NULL"
                journal_ids = data['form'].get('journal_ids') or []
                if journal_ids:
                    add_query += " AND b.journal_id IN %s"
                    add_params.append(tuple(journal_ids))
                add_query += " GROUP BY a.partner_id, c.name ORDER BY c.name"
                self.env.cr.execute(add_query, tuple(add_params))
                record = self.env.cr.dictfetchall()
            return {
                'doc_ids': partner_ids,
                'doc_model': self.env['res.partner'],
                'data': data,
                'docs': partners,
                'time': time,
                'lines': self._lines,
                'sum_partner': self._sum_partner,
                'response': record,
            }
        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }
