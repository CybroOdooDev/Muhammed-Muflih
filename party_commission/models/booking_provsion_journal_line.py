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

class BookingProvsionJournalLine(models.Model):
    _name = 'booking.provsion.journal.line'
    _description = 'Booking Provision Journal Line'

    booking_provision_id = fields.Many2one('booking.provsion', string='Booking Provision', ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account')
    partner_id = fields.Many2one('res.partner', string='Partner')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    label=fields.Char(string='Label')

    def _sync_to_related(self):
        if self.env.context.get('skip_party_records_sync'):
            return
        provisions = self.mapped('booking_provision_id')
        for prov in provisions:
            related = prov.party_records - prov
            if related:
                lines_copy = [(0, 0, {
                    'account_id': line.account_id.id if line.account_id else False,
                    'partner_id': line.partner_id.id if line.partner_id else False,
                    'label': line.label,
                    'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False,
                    'debit': line.debit or 0.0,
                    'credit': line.credit or 0.0,
                }) for line in prov.journal_line_ids]
                related.filtered(lambda r: r.state not in ('done', 'payout') and not r.move_id).with_context(skip_party_records_sync=True).sudo().write({
                    'journal_line_ids': [(5, 0, 0)] + lines_copy
                })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_provision_id'):
                prov = self.env['booking.provsion'].browse(vals['booking_provision_id'])
                if prov.move_id and not self.env.su:
                    raise UserError(_("You cannot add journal lines to a confirmed Booking Provision."))
                if not self.env.user.has_group('account.group_account_invoice') and not self.env.su:
                    raise UserError(_("Only users with Accounting: Invoicing rights can add journal lines."))
        res = super().create(vals_list)
        res._sync_to_related()
        return res

    def write(self, vals):
        for line in self:
            if line.booking_provision_id.move_id and not self.env.su:
                raise UserError(_("You cannot edit journal lines of a confirmed Booking Provision."))
            if not self.env.user.has_group('account.group_account_invoice') and not self.env.su:
                raise UserError(_("Only users with Accounting: Invoicing rights can edit journal lines."))
        res = super().write(vals)
        self._sync_to_related()
        return res

    def unlink(self):
        for line in self:
            if line.booking_provision_id.move_id and not self.env.su:
                raise UserError(_("You cannot delete journal lines of a confirmed Booking Provision."))
            if not self.env.user.has_group('account.group_account_invoice') and not self.env.su:
                raise UserError(_("Only users with Accounting: Invoicing rights can delete journal lines."))
        provisions = self.mapped('booking_provision_id')
        res = super().unlink()
        provisions.mapped('journal_line_ids')._sync_to_related()
        return res