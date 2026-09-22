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

class PartyCommission(models.TransientModel):
    _name = 'party.commission'
    _description = 'Party Commission'

    customer_ids = fields.Many2many('res.partner', string='Customers')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    sales_excutive_id = fields.Many2one('hr.employee', string='Sales Executive')

    @api.onchange('customer_ids')
    def _onchange_customer_ids(self):
        if self.customer_ids:
            exec_ids = {
                p.x_studio_sales_executive.id
                for p in self.customer_ids
                if getattr(p, 'x_studio_sales_executive', False)
            }
            if len(exec_ids) == 1 and len(self.customer_ids) == len([p for p in self.customer_ids if getattr(p, 'x_studio_sales_executive', False)]):
                self.sales_excutive_id = list(exec_ids)[0]
            else:
                self.sales_excutive_id = False
        else:
            self.sales_excutive_id = False

    def confirm_action(self):
        """Action triggered by the confirm button in the wizard."""
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ('posted', 'paid')),
        ]
        if self.customer_ids:
            domain.append(('partner_id', 'in', self.customer_ids.ids))
        if self.from_date:
            domain.append(('invoice_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('invoice_date', '<=', self.to_date))

        invoices = self.env['account.move'].search(domain, order='invoice_date asc, name asc')
        if not invoices:
            raise UserError(_("No posted invoices found for the selected customer(s) within the specified date range."))

        # Generate a shared reference sequence for all records created in this batch run
        ref_name = self.env['ir.sequence'].next_by_code('booking.provsion') or _('New')

        # Determine partners to process (in order of selection or order of invoices)
        if self.customer_ids:
            partners = self.customer_ids
        else:
            partners = invoices.mapped('partner_id')

        created_provisions = self.env['booking.provsion']

        for partner in partners:
            partner_invoices = invoices.filtered(lambda m: m.partner_id == partner)
            if not partner_invoices:
                continue

            line_vals = []
            for move in partner_invoices:
                product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
                total_invoice_qty = sum(product_lines.mapped('quantity'))

                # Search posted vendor bills linked to this customer invoice
                vendor_bills = self.env['account.move'].search([
                    ('move_type', 'in', ('in_invoice', 'in_refund')),
                    ('state', '=', 'posted'),
                    ('invoice_ids', 'in', move.id)
                ])
                total_vendor_bill_amount = sum(
                    bill.amount_total if bill.move_type == 'in_invoice' else -bill.amount_total
                    for bill in vendor_bills
                )

                for line in product_lines:
                    qty = line.quantity
                    price = line.price_unit
                    total = price * qty
                    discount = line.discount
                    net_sales = line.price_subtotal
                    # Calculate COGS from Sale Order -> Done Delivery Picking -> Stock Valuation Layer
                    cogs = 0.0
                    sale_orders = line.sale_line_ids.order_id or move.invoice_line_ids.sale_line_ids.order_id
                    if sale_orders and line.product_id:
                        done_pickings = sale_orders.picking_ids.filtered(lambda p: p.state == 'done')
                        if done_pickings:
                            product_moves = done_pickings.move_ids.filtered(
                                lambda m: m.state == 'done' and m.product_id == line.product_id
                            )
                            if product_moves:
                                valuation_layers = product_moves.stock_valuation_layer_ids
                                if valuation_layers:
                                    cogs = abs(sum(valuation_layers.mapped('value')))

                    # Fallback to standard_price if valuation layer value is not found or 0.0
                    if not cogs and line.product_id:
                        cogs = 0.0

                    # Printing charges split proportionately by line quantity from linked posted Vendor Bills
                    printing_charges = (total_vendor_bill_amount * (qty / total_invoice_qty)) if total_invoice_qty else 0.0

                    commission_percentage = 0.0
                    commission_value = 0.0
                    net_commission = 0.0
                    profit = net_sales - cogs - printing_charges - net_commission
                    profit_percentage = (profit * 100.0 / net_sales) if net_sales else 0.0

                    line_vals.append((0, 0, {
                        'date': move.invoice_date,
                        'invoice_number': move.name,
                        'customer_id': move.partner_id.id,
                        'item_code': line.product_id.default_code or line.product_id.name if line.product_id else line.name,
                        'qty': qty,
                        'price': price,
                        'total': total,
                        'discount': discount,
                        'net_sales': net_sales,
                        'cogs': cogs,
                        'printing_charges': printing_charges,
                        'commission_percentage': commission_percentage,
                        'commission_value': commission_value,
                        'net_commission': net_commission,
                        'profit': profit,
                        'profit_percentage': profit_percentage,
                    }))

            if line_vals:
                booking_provision = self.env['booking.provsion'].create({
                    'name': ref_name,
                    'customer_ids': [(6, 0, [partner.id])],
                    'from_date': self.from_date,
                    'to_date': self.to_date,
                    'sales_excutive_id': self.sales_excutive_id.id if self.sales_excutive_id else (getattr(partner, 'x_studio_sales_executive', False).id if getattr(partner, 'x_studio_sales_executive', False) else False),
                    'state': 'draft',
                    'line_ids': line_vals,
                })
                created_provisions |= booking_provision

        if not created_provisions:
            raise UserError(_("No posted invoices found for the selected customer(s) within the specified date range."))

        created_provisions.write({
            'party_records': [(6, 0, created_provisions.ids)]
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking Provisions'),
            'res_model': 'booking.provsion',
            'domain': [('id', 'in', created_provisions.ids)],
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'context': {'search_default_group_by_name': 1},
            'target': 'current',
        }
