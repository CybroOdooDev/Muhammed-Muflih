from odoo import models, fields, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cost_history_id = fields.Many2one('purchase.product.history',help="purchase product cost history")
    is_force_cancel_state = fields.Boolean("Is force cancel state", default=False, copy=False,help="is force cancel state")
    is_bill_canceled = fields.Boolean(
        'Is Bill Canceled', default=False, copy=False,help="is bill cancelled")
    is_receipt_canceled = fields.Boolean(
        'Is Receipt Canceled', default=False, copy=False,help="is receipt cancelled")
    force_cancel_bill = fields.Many2one('account.move', copy=False,help="force cancel bill")
    force_cancel_receipt = fields.Many2one('stock.picking', copy=False,help="force cancel receipt")

    def action_force_cancel_order(self):
        """ Force cancel the purchase order, reset and cancel associated payments,
        vendor bills, stock valuation accounting moves, and restore original product
        costs from history.
        """
        if self.is_receipt_canceled and self.force_cancel_receipt.state == 'done':
            payment_ids = self.env['account.payment'].search([
                ('memo', 'in', self.invoice_ids.mapped('name'))
            ])
            for rec in payment_ids:
                rec.action_draft()
                rec.action_cancel()
            self.invoice_ids.button_draft()
            self.invoice_ids.button_cancel()
            account_moves = self.picking_ids.move_ids.account_move_id
            account_moves.button_draft()
            account_moves.button_cancel()
            if self.cost_history_id:
                for line in self.cost_history_id.line_ids:
                    line.product_id.with_company(self.company_id).write({
                        'standard_price': line.standard_cost
                    })
            self.state = 'cancel'
            self.is_force_cancel_state = True
        else:
            raise UserError(
                _('Return the Receipt and Bill to cancel this Purchase Order'))

    def button_confirm(self):
        """ Override button_confirm to record product cost price snapshot
        in purchase product history upon order confirmation.
        """
        super().button_confirm()
        self.cost_history_id = self.env['purchase.product.history'].create([{
            'name': self.id,
            'line_ids': [
                (0, 0, {
                    'product_id': line.product_id.id,
                    'standard_cost': line.product_id.standard_price,
                    'qty': line.product_qty
                })
                for line in self.order_line
            ]
        }])
