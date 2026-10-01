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
    _rec_name = 'invoice_number'
    _order = 'date desc, id desc'

    booking_provision_id = fields.Many2one('booking.provsion', string='Booking Provision', ondelete='cascade')
    sales_excutive_id = fields.Many2one(
        'hr.employee',
        string='Sales Executive',
        related='booking_provision_id.sales_excutive_id',
        store=True,
        readonly=True,
    )
    sales_executive_id = fields.Many2one(
        'hr.employee',
        string='Sales Executive',
        related='sales_excutive_id',
        readonly=True,
    )
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
    paid=fields.Float(string='Paid')
    difference=fields.Float(string='Difference')
    state = fields.Selection(
        related='booking_provision_id.state',
        string='Status',
        store=True,
        readonly=True,
    )
    # analytic_account_id=fields.Many2one('account.analytic.account', string='Analytic Account')
    is_commission_readonly = fields.Boolean(
        compute='_compute_is_commission_readonly'
    )
    is_printing_charges_readonly = fields.Boolean(
        compute='_compute_is_printing_charges_readonly'
    )

    @api.depends('booking_provision_id.state')
    @api.depends_context('uid')
    def _compute_is_commission_readonly(self):
        is_manager = self.env.user.has_group('party_commission.group_party_commission_manager')
        for rec in self:
            state = rec.booking_provision_id.state or 'draft'
            if state == 'draft':
                rec.is_commission_readonly = False
            elif state == 'to_review':
                rec.is_commission_readonly = not is_manager
            else:
                rec.is_commission_readonly = True

    @api.depends('booking_provision_id.state')
    @api.depends_context('uid')
    def _compute_is_printing_charges_readonly(self):
        is_manager = self.env.user.has_group('party_commission.group_party_commission_manager')
        for rec in self:
            state = rec.booking_provision_id.state or 'draft'
            if state == 'to_review':
                rec.is_printing_charges_readonly = not is_manager
            else:
                rec.is_printing_charges_readonly = True

    @api.constrains('commission_percentage', 'commission_value')
    def _check_commission_exclusive(self):
        for rec in self:
            if rec.commission_percentage and rec.commission_value:
                raise ValidationError(_("Only one commission type is allowed at a time (Commission Percentage or Commission Value)."))

    @api.onchange('commission_percentage')
    def _onchange_commission_percentage(self):
        for line in self:
            if line.commission_percentage and line.commission_value:
                line.commission_percentage=0
                return {
                    'warning': {
                        'title': _("Validation Warning"),
                        'message': _("Only one commission type is allowed at a time. Please clear Commission Value before entering Commission Percentage."),
                        'type': 'dialog',
                    }
                }

    @api.onchange('commission_value')
    def _onchange_commission_value(self):
        for line in self:
            if line.commission_value and line.commission_percentage:
                line.commission_value=0
                return {
                    'warning': {
                        'title': _("Validation Warning"),
                        'message': _("Only one commission type is allowed at a time. Please clear Commission Percentage before entering Commission Value."),
                        'type': 'dialog',
                    }
                }

    @api.onchange('paid')
    def _onchange_difference(self):
        if self.paid:
            self.difference=self.net_commission-self.paid
        else:
            self.difference=0


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

    def create_payouts(self):
        if not self:
            raise UserError(_("Please select at least one record to create a payout."))

        partners = self.mapped('customer_id')
        currency = self.env.company.currency_id
        line_vals = []
        for partner in partners:
            partner_lines = self.filtered(lambda l: l.customer_id == partner)
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

        lines_without_partner = self.filtered(lambda l: not l.customer_id)
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

        default_journal = self.env['commission.payout.wizard']._default_journal_id()
        provisions = self.mapped('booking_provision_id')
        wizard = self.env['commission.payout.wizard'].create({
            'payout_line_ids': [(6, 0, self.ids)],
            'booking_provision_ids': [(6, 0, provisions.ids)],
            'journal_id': default_journal.id if default_journal else False,
            'date': fields.Date.context_today(self),
            'allowed_partner_ids': [(6, 0, partners.ids)],
            'line_ids': line_vals,
        })

        return {
            'name': _('Commission Payout'),
            'type': 'ir.actions.act_window',
            'res_model': 'commission.payout.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def write(self, vals):
        if not self.env.su:
            for rec in self:
                if rec.booking_provision_id.state == 'payout':
                    raise UserError(_("You cannot modify commission lines of a Booking Provision that is in 'Payout' state."))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.booking_provision_id.state in ('done', 'payout'):
                raise UserError(_("You cannot delete commission lines of a Booking Provision that is in '%s' state.") % (rec.booking_provision_id.state.capitalize()))
        return super().unlink()
