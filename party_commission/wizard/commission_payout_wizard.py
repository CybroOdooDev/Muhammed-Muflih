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


class CommissionPayoutWizard(models.TransientModel):
    _name = 'commission.payout.wizard'
    _description = 'Commission Payout Wizard'

    booking_provision_ids = fields.Many2many('booking.provsion', string='Booking Provisions')
    payout_line_ids = fields.Many2many('booking.provsion.line', string='Selected Payout Lines')
    date = fields.Date(string='Journal Date', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', '=', 'general')]",
        default=lambda self: self._default_journal_id(),
        required=True
    )
    allowed_partner_ids = fields.Many2many('res.partner', string='Allowed Partners')
    line_ids = fields.One2many('commission.payout.wizard.line', 'wizard_id', string='Journal Lines')

    @api.model
    def _default_journal_id(self):
        journal = self.env.ref('account.1_general', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
        if not journal:
            journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        return journal

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_ids and active_model == 'booking.provsion.line':
            lines = self.env['booking.provsion.line'].browse(active_ids)
            partners = lines.mapped('customer_id')
            provisions = lines.mapped('booking_provision_id')
            currency = self.env.company.currency_id
            if 'payout_line_ids' in fields_list:
                res['payout_line_ids'] = [(6, 0, lines.ids)]
            if 'booking_provision_ids' in fields_list:
                res['booking_provision_ids'] = [(6, 0, provisions.ids)]
            if 'allowed_partner_ids' in fields_list:
                res['allowed_partner_ids'] = [(6, 0, partners.ids)]
            if 'line_ids' in fields_list and 'line_ids' not in res:
                line_vals = []
                for partner in partners:
                    partner_lines = lines.filtered(lambda l: l.customer_id == partner)
                    diff_sum = sum(partner_lines.mapped('difference'))
                    credit_val = currency.round(diff_sum) if currency else round(diff_sum, 2)
                    account = partner.party_commission_account_id
                    line_vals.append((0, 0, {
                        'account_id': account.id if account else False,
                        'partner_id': partner.id,
                        'label': f"Commission Payout - {partner.name}" if partner.name else '',
                        'analytic_account_id': False,
                        'debit': 0.0,
                        'credit': credit_val,
                    }))
                lines_without_partner = lines.filtered(lambda l: not l.customer_id)
                if lines_without_partner:
                    diff_sum = sum(lines_without_partner.mapped('difference'))
                    credit_val = currency.round(diff_sum) if currency else round(diff_sum, 2)
                    line_vals.append((0, 0, {
                        'account_id': False,
                        'partner_id': False,
                        'label': _("Commission Payout"),
                        'analytic_account_id': False,
                        'debit': 0.0,
                        'credit': credit_val,
                    }))
                res['line_ids'] = line_vals
        return res

    def action_create_journal(self):
        self.ensure_one()
        if not self.journal_id:
            raise UserError(_("Please select a Journal."))

        if not self.line_ids:
            raise UserError(_("Please add at least one Journal Line."))

        total_debit = sum(self.line_ids.mapped('debit'))
        total_credit = sum(self.line_ids.mapped('credit'))
        currency = self.env.company.currency_id
        if not float_is_zero(total_debit - total_credit, precision_rounding=currency.rounding or 0.01):
            raise UserError(_("Cannot confirm: Total Debit (%.2f) does not equal Total Credit (%.2f). Please ensure Total Debit equals Total Credit before confirming.") % (total_debit, total_credit))

        for line in self.line_ids:
            if not line.account_id:
                raise UserError(_("Please select an Account for all journal lines."))

        move_lines = []
        for line in self.line_ids:
            line_vals = {
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id if line.partner_id else False,
                'debit': line.debit or 0.0,
                'credit': line.credit or 0.0,
                'name': line.label or _('Commission Payout'),
            }
            if line.analytic_account_id:
                line_vals['analytic_distribution'] = {str(line.analytic_account_id.id): 100}
            move_lines.append((0, 0, line_vals))

        # Find parent booking provisions
        provisions = self.booking_provision_ids
        if not provisions and self.payout_line_ids:
            provisions = self.payout_line_ids.mapped('booking_provision_id')
        if not provisions and self.env.context.get('active_model') == 'booking.provsion.line':
            payout_lines = self.env['booking.provsion.line'].browse(self.env.context.get('active_ids', []))
            provisions = payout_lines.mapped('booking_provision_id')

        all_provisions = provisions | provisions.mapped('party_records')
        if provisions:
            same_name_provisions = self.env['booking.provsion'].search([('name', 'in', provisions.mapped('name'))])
            all_provisions |= same_name_provisions

        refs = set(all_provisions.mapped('name'))
        ref_str = ", ".join(filter(None, refs)) if refs else _('Commission Payout')

        move = self.env['account.move'].create({
            'journal_id': self.journal_id.id,
            'date': self.date or fields.Date.context_today(self),
            'ref': ref_str,
            'move_type': 'entry',
            'line_ids': move_lines,
        })
        move.action_post()

        # Link the created payout journal entry to parent booking provision records and set state to payout
        for prov in all_provisions:
            vals = {'move_ids': [(4, move.id)], 'state': 'payout'}
            if not prov.move_id:
                vals['move_id'] = move.id
            prov.with_context(skip_party_records_sync=True).sudo().write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Commission Payout Journal entry created successfully'),
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


class CommissionPayoutWizardLine(models.TransientModel):
    _name = 'commission.payout.wizard.line'
    _description = 'Commission Payout Wizard Line'

    wizard_id = fields.Many2one('commission.payout.wizard', ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account')
    partner_id = fields.Many2one('res.partner', string='Partner')
    label = fields.Char(string='Label')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
