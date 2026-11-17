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
from datetime import datetime
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportPartnerLedger(models.AbstractModel):
    """ Abstract model representing the partner ledger report."""
    _name = 'report.account_reports_xlsx.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _lines(self, data, partner):
        """
            Retrieve and format account move lines for a given partner based on specified criteria.

            :param data: Data containing filter parameters.
            :type data: dict
            :param partner: Partner for which account move lines are retrieved.
            :type partner: account.partner
            :return: List of dictionaries containing formatted account move line information.
            :rtype: list
        """
        full_account = []
        currency = self.env['res.currency']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form'].get('reconciled') else ' AND "account_move_line".full_reconcile_id IS NULL '
        where_clause_str = query_get_data[1] if query_get_data[1] else "1=1"
        params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + list(query_get_data[2])
        query = """
            SELECT "account_move_line".id, "account_move_line".date, "account_move_line".account_id, "account_move_line".matching_number, j.code, "account_move_line".ref, m.name as move_name, "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency, "account_move_line".currency_id, c.symbol AS currency_code
            FROM """ + str(query_get_data[0]) + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            WHERE "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + where_clause_str + reconcile_clause + """
                ORDER BY "account_move_line".date"""
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format if lang_id else '%Y-%m-%d'
        account_ids = [r['account_id'] for r in res if r.get('account_id')]
        accounts_map = {acc.id: acc for acc in self.env['account.account'].browse(account_ids)} if account_ids else {}
        for r in res:
            acc = accounts_map.get(r.get('account_id'))
            r['a_code'] = acc.code if acc else ''
            r['a_name'] = acc.name if acc else ''
            r['matching_number'] = r.get('matching_number') or ''
            r['code'] = r.get('code') or ''
            r['date'] = datetime.strptime(str(r['date']), DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if r.get('date') else ''
            r['displayed_name'] = '-'.join(
                str(r[field_name]) for field_name in ('move_name', 'ref', 'name')
                if r.get(field_name) not in (None, '', '/')
            )
            sum += (r.get('debit') or 0.0) - (r.get('credit') or 0.0)
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id')) if r.get('currency_id') else False
            full_account.append(r)
        return full_account

    def _sum_partner(self, data, partner, field):
        """
            Calculate the sum of the specified field for a given partner.

            :param data: Data for generating the report.
            :type data: dict
            :param partner: Partner for which the sum is calculated.
            :type partner: account.partner
            :param field: Field for which the sum is calculated.
            :type field: str
            :return: The calculated sum.
            :rtype: float
        """
        if field not in ['debit', 'credit', 'debit - credit', 'amount_currency']:
            return 0.0
        result = 0.0
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form'].get('reconciled') else ' AND "account_move_line".full_reconcile_id IS NULL '

        where_clause_str = query_get_data[1] if query_get_data[1] else "1=1"
        params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + list(query_get_data[2])
        query = """SELECT sum(""" + field + """)
                FROM """ + str(query_get_data[0]) + """, account_move AS m
                WHERE "account_move_line".partner_id = %s
                    AND m.id = "account_move_line".move_id
                    AND m.state IN %s
                    AND account_id IN %s
                    AND """ + where_clause_str + reconcile_clause
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def get_report_values(self, docids, data=None):
        """
           Function to retrieve report values.

           :param docids: Document IDs.
           :type docids: list
           :param data: Data for generating the report.
           :type data: dict or None
           :return: Dictionary containing report-related information.
           :rtype: dict
           :raises UserError: If form content is missing, the report cannot be printed.
        """
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be "
                              "printed."))

        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable', 'asset_receivable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.account_type IN %s
            """, (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + list(query_get_data[2])
        reconcile_clause = "" if data['form'].get('reconciled') else ' AND "account_move_line".full_reconcile_id IS NULL '
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

        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'type': result_selection,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }
