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

    @api.depends('booking_provision_id.state')
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

    def write(self, vals):
        if any(field in vals for field in ('commission_percentage', 'commission_value', 'printing_charges')):
            is_manager = self.env.user.has_group('party_commission.group_party_commission_manager')
            for rec in self:
                state = rec.booking_provision_id.state or 'draft'
                if state == 'confirmed':
                    raise UserError(_("You cannot edit commission fields in Confirmed state."))
                elif state == 'to_review' and not is_manager:
                    raise UserError(_("Only a Party Commission Manager can edit commission fields in To Review state."))
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

    @api.depends('qty','price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.qty * rec.price
        else:
            rec.total = 0.0

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
