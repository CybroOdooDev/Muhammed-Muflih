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
from odoo import api, models, fields
from odoo.tools.misc import get_lang


class AccountCommonReport(models.TransientModel):
    """ Model for common account report wizard. """
    _name = "account.common.report.xlsx"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', 'Company',
                                 required=True,
                                 readonly=True,
                                 default=lambda self: self.env.company,
                                 help='Company for which the report is generated.')
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journals',
        required=True,
        default=lambda self: self.env['account.journal'].search(
            [('company_id', '=', self.company_id.id)]),
        domain="[('company_id', '=', company_id)]",
        help='Select the journals to include in the report.'
    )
    date_from = fields.Date('Start Date', help="Date of first report.")
    date_to = fields.Date('End Date', help="Date of last report.")
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], 'Target Moves', required=True,
                                   default='posted',
                                   help='Select the type of entries to include in the report.')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """
            Onchange method triggered when the company_id field is changed.
            Updates the available journal_ids based on the selected company.
            :return: None
        """
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    def _build_contexts(self, data):
        """
            Function to build and return contexts.

            :param data: Data for generating the report.
            :type data: dict
            :return: Dictionary containing contexts.
            :rtype: dict
        """
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form'][
            'journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form'][
            'target_move'] or ''
        result['date_from'] = data['form'].get('date_from') or False
        result['date_to'] = data['form'].get('date_to') or False
        result['strict_range'] = True if result['date_from'] else False
        company_id = data['form'].get('company_id')
        if isinstance(company_id, (list, tuple)):
            result['company_id'] = company_id[0]
        elif company_id:
            result['company_id'] = company_id
        else:
            result['company_id'] = self.env.company.id
        return result

    def _print_report(self, data):
        """
        Placeholder function for printing report. Actual implementation
        needs to be provided in the specific report module.

           :param data: Data for generating the report.
           :type data: dict
           :raises NotImplementedError: This function should be implemented
           in the specific report module.
        """
        raise NotImplementedError()

    def check_report(self):
        """
            Function to check report.
            :return: Result of the print_report function.
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'date_to', 'journal_ids', 'target_move',
             'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)


class AccountCommonAccountReport(models.TransientModel):
    """ Model for common account report with display_account option. """
    _name = 'account.common.account.report.xlsx'
    _description = 'Account Common Account Report'
    _inherit = 'account.common.report.xlsx'

    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance not equal to zero')],
        string='Display Accounts', required=True, default='movement')

    def pre_print_report(self, data):
        """ Prepare data for preprinting the report. """
        data['form'].update(self.read(['display_account'])[0])
        return data
