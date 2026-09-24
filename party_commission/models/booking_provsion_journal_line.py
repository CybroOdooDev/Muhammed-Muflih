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
    account_id = fields.Many2one('account.account', string='Account', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_provision_id'):
                prov = self.env['booking.provsion'].browse(vals['booking_provision_id'])
                if prov.all_party_confirmed and not self.env.su:
                    raise UserError(_("You cannot add journal lines to a confirmed Booking Provision."))
        return super().create(vals_list)

    def write(self, vals):
        for line in self:
            if line.booking_provision_id.all_party_confirmed and not self.env.su:
                raise UserError(_("You cannot edit journal lines of a confirmed Booking Provision."))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.booking_provision_id.all_party_confirmed and not self.env.su:
                raise UserError(_("You cannot delete journal lines of a confirmed Booking Provision."))
        return super().unlink()