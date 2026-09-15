from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PartyCommission(models.TransientModel):
    _name = 'party.commission'
    _description = 'Party Commission'

    customer_ids = fields.Many2many('res.partner', string='Customers')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    def confirm_action(self):
        """Action triggered by the confirm button in the wizard."""
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ('posted','paid')),
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

        line_vals = []
        for move in invoices:
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

        booking_provision = self.env['booking.provsion'].create({
            'customer_ids': [(6, 0, self.customer_ids.ids)],
            'from_date': self.from_date,
            'to_date': self.to_date,
            'state':'draft',
            'line_ids': line_vals,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Booking Provision',
            'res_model': 'booking.provsion',
            'res_id': booking_provision.id,
            'view_mode': 'form',
            'target': 'current',
        }
