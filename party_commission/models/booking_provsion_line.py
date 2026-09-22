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
from odoo.exceptions import ValidationError, UserError


class BookingProvsionLine(models.Model):
    _name = 'booking.provsion.line'
    _description = 'Booking Provision Line'

    booking_provision_id = fields.Many2one('booking.provsion', string='Booking Provision', ondelete='cascade')
    customer_id = fields.Many2one('res.partner', string='Customer')
    date = fields.Date(string='Date')
    invoice_number = fields.Char(string='Invoice Number')
    item_code = fields.Char(string='Item Code')
    qty = fields.Float(string='Qty')
    price = fields.Float(string='Price')
    total = fields.Float(string='Total',compute='_compute_total')
    discount = fields.Float(string='Discount')
    net_sales = fields.Float(string='Net Sales')
    cogs = fields.Float(string='COGS')
    printing_charges = fields.Float(string='Printing Charges')
    commission_percentage = fields.Float(string='Commission %')
    commission_value = fields.Float(string='Commission Value')
    net_commission = fields.Float(string='Net Commission', compute='_compute_net_commission', store=True)
    profit = fields.Float(string='Profit', compute='_compute_profit')
    profit_percentage = fields.Float(string='Profit %', compute='_compute_profit_percentage')
    is_commission_readonly = fields.Boolean(
        compute='_compute_is_commission_readonly'
    )
    is_printing_charges_readonly = fields.Boolean(
        compute='_compute_is_printing_charges_readonly'
    )

    @api.depends('booking_provision_id.state')
    def _compute_is_commission_readonly(self):
        for rec in self:
            state = rec.booking_provision_id.state or 'draft'
            rec.is_commission_readonly = (state != 'draft')

    @api.depends('booking_provision_id.state')
    def _compute_is_printing_charges_readonly(self):
        is_manager = self.env.user.has_group('party_commission.group_party_commission_manager')
        for rec in self:
            state = rec.booking_provision_id.state or 'draft'
            if state == 'to_review':
                rec.is_printing_charges_readonly = not is_manager
            else:
                rec.is_printing_charges_readonly = True

    def write(self, vals):
        is_manager = self.env.user.has_group('party_commission.group_party_commission_manager')
        if any(field in vals for field in ('commission_percentage', 'commission_value')):
            for rec in self:
                state = rec.booking_provision_id.state or 'draft'
                if state != 'draft':
                    raise UserError(_("Commission fields cannot be modified in To Review or Confirmed state."))

        if 'printing_charges' in vals:
            for rec in self:
                state = rec.booking_provision_id.state or 'draft'
                if state != 'to_review' or not is_manager:
                    raise UserError(_("Printing charges can only be modified by a Party Commission Manager when in To Review state."))

        return super().write(vals)

    @api.onchange('commission_percentage', 'commission_value')
    def commission_check(self):
        if self.commission_percentage and self.commission_value:
            raise ValidationError(_("A record can contain only Commission % or Commission Value, not both."))

    @api.constrains('commission_percentage', 'commission_value')
    def _check_commission_fields(self):
        for line in self:
            if line.commission_percentage and line.commission_value:
                raise ValidationError(_("A record can contain only Commission % or Commission Value, not both."))

    @api.depends('qty', 'price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.qty * rec.price

    @api.depends('qty', 'commission_percentage', 'commission_value', 'net_sales')
    def _compute_net_commission(self):
        for rec in self:
            if rec.commission_percentage:
                rec.net_commission = rec.net_sales * (rec.commission_percentage / 100.0)
            elif rec.commission_value:
                rec.net_commission = rec.qty * rec.commission_value
            else:
                rec.net_commission = 0.0

    @api.depends('cogs', 'net_sales', 'printing_charges', 'net_commission')
    def _compute_profit(self):
        for rec in self:
            rec.profit = rec.net_sales - rec.cogs - rec.printing_charges - rec.net_commission

    @api.depends('net_sales', 'profit')
    def _compute_profit_percentage(self):
        for rec in self:
            if rec.net_sales:
                rec.profit_percentage = (rec.profit * 100.0) / rec.net_sales
            else:
                rec.profit_percentage = 0.0
