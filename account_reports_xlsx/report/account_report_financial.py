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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReportFinancial(models.AbstractModel):
    """
    Financial Report Model
    This model is used to generate financial reports such as Balance Sheet,
    Profit and Loss, etc.
    """
    _name = 'report.account_reports_xlsx.report_financial'
    _description = 'Financial Report'

    def _compute_account_balance(self, accounts):
        """
        compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0)
                                   for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = (self.env['account.move.line']._query_get())
            tables = tables.replace(
                '"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause:
                clause_code = where_clause if isinstance(where_clause, str) else (where_clause._sql_tuple[0] if hasattr(where_clause, '_sql_tuple') else str(where_clause))
                if clause_code:
                    wheres.append(clause_code)
            filters = " AND ".join(wheres)
            request = ("SELECT account_id as id, " +
                       ', '.join(mapping.values()) +
                       " FROM " + tables +
                       " WHERE account_id IN %s " +
                       filters +
                       " GROUP BY account_id")
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        """returns a dictionary with key=the ID of a record and
         value=the credit, debit and balance amount
        computed for this record. If the record is of type:
        'accounts': it's the sum of the linked accounts
        'account_type': it's the sum of leaf accounts with
         such an account_type
        'account_report': it's the amount of the related report
        'sum': it's the sum of the children of this record
        (aka a 'view' record)"""
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(
                    report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum of the leaf accounts with such an account type
                if report.account_type_ids:
                    accounts = self.env['account.account'].search(
                        [('account_type', '=', report.account_type_ids)])
                else:
                    accounts = self.env['account.account'].browse([])
                res[report.id]['account'] = self._compute_account_balance(
                    accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        """
        Function to retrieve and calculate lines for financial reports.

        :param data: Data containing filter parameters.
        :type data: dict
        :return: List of dictionaries containing financial report lines.
        :rtype: list
        """
        lines = []
        raw_report_id = data.get('account_report_id')
        report_id = raw_report_id[0] if isinstance(raw_report_id, (list, tuple)) else raw_report_id
        account_report = self.env['account.financial.report'].browse(report_id)
        child_reports = account_report._get_children_by_order()
        res = self.with_context(
            data.get('used_context'))._compute_report_balance(child_reports)
        if data.get('enable_filter'):
            comparison_res = self.with_context(
                data.get('comparison_context'))._compute_report_balance(
                child_reports)
            for report_id_val, value in comparison_res.items():
                res[report_id_val]['comp_bal'] = value['balance']
                report_acc = res[report_id_val].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id_val][
                        'account'].items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * int(report.sign),
                'type': 'report',
                'level': bool(
                    report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False,
                # used to underline the financial report balances
            }
            if data.get('debit_credit'):
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data.get('enable_filter'):
                vals['balance_cmp'] = res[report.id]['comp_bal'] * int(
                    report.sign)

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # print the lines with no details
                continue

            if res[report.id].get('account'):
                sub_lines = []
                currency = self.env.company.currency_id
                for account_id, value in res[report.id]['account'].items():
                    # if there are accounts, they are the leaf of the account.report
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': (account.code or '') + ' ' + (account.name or ''),
                        'balance': value['balance'] * int(report.sign) or 0.0,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.account_type,
                    }
                    if data.get('debit_credit'):
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not currency.is_zero(
                                vals['debit']) or not currency.is_zero(
                            vals['credit']):
                            flag = True
                    if not currency.is_zero(
                            vals['balance']):
                        flag = True
                    if data.get('enable_filter'):
                        vals['balance_cmp'] = value['comp_bal'] * int(
                            report.sign)
                        if not currency.is_zero(
                                vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines,
                                key=lambda sub_line: sub_line['name'])
        return lines

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Function to retrieve report values for the Financial Report.

        :param docids: Document IDs.
        :type docids: list
        :param data: Data for generating the report.
        :type data: dict or None
        :return: Dictionary containing report-related information.
        :rtype: dict
        :raises UserError: If form content is missing, the report cannot be printed.
        """
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        raw_report_id = data['form'].get('account_report_id')
        report_id = raw_report_id[0] if isinstance(raw_report_id, (list, tuple)) else raw_report_id

        return {
            'doc_ids': self.ids,
            'doc_model': self.env['account.financial.report'],
            'data': data['form'],
            'docs': self.env['account.financial.report'].browse(report_id),
            'time': fields.date.today(),
            'get_account_lines': self.get_account_lines,
        }
