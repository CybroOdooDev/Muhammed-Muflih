# -- coding: utf-8 --
#############################################################################
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class CreateJournalWizard(models.TransientModel):
    _name = 'create.journal.wizard'
    _description = 'Create Journal Entry Wizard'

    booking_provision_ids = fields.Many2many('booking.provsion', string='Booking Provisions')
    date = fields.Date(string='Journal Date', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', '=', 'general')]",
        required=True
    )
    allowed_partner_ids = fields.Many2many('res.partner', string='Allowed Partners')
    line_ids = fields.One2many('create.journal.wizard.line', 'wizard_id', string='Journal Lines')

    def action_create_journal(self):
        self.ensure_one()
        records = self.booking_provision_ids
        if not records:
            raise UserError(_("No Booking Provision records selected."))

        if not self.journal_id:
            raise UserError(_("Please select a Journal."))

        if not self.line_ids:
            raise UserError(_("Please add at least one Journal Line."))

        total_debit = sum(self.line_ids.mapped('debit'))
        total_credit = sum(self.line_ids.mapped('credit'))
        currency = self.env.company.currency_id
        if not float_is_zero(total_debit - total_credit, precision_rounding=currency.rounding or 0.01):
            raise UserError(_("Cannot confirm: Total Debit (%.2f) does not equal Total Credit (%.2f).") % (total_debit, total_credit))

        move_lines = []
        for line in self.line_ids:
            line_vals = {
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id if line.partner_id else False,
                'debit': line.debit or 0.0,
                'credit': line.credit or 0.0,
                'name': records[0].name,
            }
            if line.analytic_account_id:
                line_vals['analytic_distribution'] = {str(line.analytic_account_id.id): 100}
            move_lines.append((0, 0, line_vals))

        move = self.env['account.move'].create({
            'journal_id': self.journal_id.id,
            'date': self.date or fields.Date.context_today(self),
            'ref': records[0].name,
            'move_type': 'entry',
            'line_ids': move_lines,
        })
        move.action_post()

        # Update booking provision records with move_id and sync journal lines
        for rec in records:
            jlines = [(0, 0, {
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id if line.partner_id else False,
                'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False,
                'debit': line.debit or 0.0,
                'credit': line.credit or 0.0,
            }) for line in self.line_ids]
            rec.sudo().write({
                'move_id': move.id,
                'state': 'done',
                'date': self.date,
                'journal_id': self.journal_id.id,
                'journal_line_ids': [(5, 0, 0)] + jlines,
            })
            

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Journal entry created successfully'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'name': _('Journal Entry'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'views': [(False, 'form')],
                    'view_mode': 'form',
                    'res_id': move.id,
                    'target': 'current',
                }
            }
        }


class CreateJournalWizardLine(models.TransientModel):
    _name = 'create.journal.wizard.line'
    _description = 'Create Journal Entry Wizard Line'

    wizard_id = fields.Many2one('create.journal.wizard', ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
