# -*- coding: utf-8 -*-
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


class ProfitReportWizard(models.TransientModel):
    _name = 'profit.report.wizard'
    _description = 'Profit Report Wizard'

    customer_ids = fields.Many2many('res.partner', string='Customers')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    sales_executive_id = fields.Many2one('hr.employee', string='Sales Executive')
    line_ids = fields.One2many('report.result', 'wizard_id', string='Report Lines')

    @api.onchange('customer_ids')
    def _onchange_customer_ids(self):
        if self.customer_ids:
            exec_ids = {
                p.x_studio_sales_executive.id
                for p in self.customer_ids
                if getattr(p, 'x_studio_sales_executive', False)
            }
            if len(exec_ids) == 1 and len(self.customer_ids) == len(
                    [p for p in self.customer_ids if getattr(p, 'x_studio_sales_executive', False)]):
                self.sales_executive_id = list(exec_ids)[0]
            else:
                self.sales_executive_id = False
        else:
            self.sales_executive_id = False

    def action_print_report(self):
        """Action to generate and view profit report result list view."""
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
            raise UserError(_('No posted invoices found for the selected customer(s) within the specified date range.'))

        # Clear previous wizard result lines
        self.line_ids.unlink()

        # Create report.result lines
        line_vals = []
        for move in invoices:
            product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            if not product_lines:
                continue

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

            # Determine salesman
            salesman = self.sales_executive_id
            if not salesman and getattr(move.partner_id, 'x_studio_sales_executive', False):
                salesman = move.partner_id.x_studio_sales_executive

            if self.sales_executive_id and salesman != self.sales_executive_id:
                continue

            # Search posted journal entry lines created specifically from Booking Provision (Party Commission)
            booking_moves = self.env['booking.provsion'].search([
                ('move_id', '!=', False),
                ('move_id.state', '=', 'posted')
            ]).mapped('move_id')

            domain_aml = [
                ('move_id', 'in', booking_moves.ids),
                ('partner_id', '=', move.partner_id.id),
                ('credit', '>', 0),
            ]
            if self.from_date:
                domain_aml.append(('date', '>=', self.from_date))
            if self.to_date:
                domain_aml.append(('date', '<=', self.to_date))

            commission_journal_lines = self.env['account.move.line'].search(domain_aml)
            total_party_commission_amount = sum(commission_journal_lines.mapped('credit'))


            partner_invoices = invoices.filtered(lambda m: m.partner_id == move.partner_id)
            total_partner_qty = sum(
                sum(inv.invoice_line_ids.filtered(lambda l: l.display_type == 'product').mapped('quantity'))
                for inv in partner_invoices
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

                # Fallback if valuation layer value is not found or 0.0
                if not cogs and line.product_id:
                    cogs = 0.0

                # Printing charges split proportionately by line quantity from linked posted Vendor Bills
                printing_charges = (total_vendor_bill_amount * (qty / total_invoice_qty)) if total_invoice_qty else 0.0

                # Party commission credit amount from posted journal entries
                party_commission = (total_party_commission_amount * (qty / total_partner_qty)) if total_partner_qty else 0.0
                profit = net_sales - cogs - printing_charges - party_commission
                profit_percentage = (profit * 100.0 / net_sales) if net_sales else 0.0

                line_vals.append({
                    'wizard_id': self.id,
                    'date': move.invoice_date,
                    'voucher': move.name,
                    'customer_id': move.partner_id.id,
                    'product_id': line.product_id.id,
                    'salesman_id': salesman.id if salesman else False,
                    'qty': qty,
                    'rate': price,
                    'net_sales': net_sales,
                    'cogs': cogs,
                    'printing_charges': printing_charges,
                    'party_commission': 0.0,
                    'profit': profit,
                    'profit_percentage': profit_percentage,
                })


        if not line_vals:
            raise UserError(_('No matching invoice lines found for the selected criteria.'))

        self.env['report.result'].create(line_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Report Result'),
            'res_model': 'report.result',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }
