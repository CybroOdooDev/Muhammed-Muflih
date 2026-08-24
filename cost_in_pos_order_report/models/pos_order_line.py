# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields
import logging


_logger = logging.getLogger(__name__)

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    is_fee_calculated = fields.Boolean('Fee Calculation Status')

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    amount_payment_bank_fee = fields.Float('Payment Bank Fee',help="bank fee for payment")
    real_margin = fields.Float('Real Margin',help="real margin for payment")

    def calculate_bank_fee_for_payments(self):
        """calculate bank_fee for payments"""
        order_line_ids = self.env['pos.order.line'].search([('real_margin', '=', False)], limit=10000)
        for rec in order_line_ids:
            rec.real_margin = rec.margin
            rec.amount_payment_bank_fee = 0
        payment_method_with_fee = self.env['pos.payment.method'].search([
            ('bank_fee_account', '!=', False)
        ])
        payment_line_ids = self.env['pos.payment'].search([
            ('payment_method_id', 'in', payment_method_with_fee.ids),
            ('is_fee_calculated', '=', False)
        ])
        for rec in payment_line_ids:
            rec.is_fee_calculated = True
            bank_fee = 0
            if rec.payment_method_id.bank_fee != 0:
                bank_fee = (rec.amount * rec.payment_method_id.bank_fee) / 100
            if rec.payment_method_id.bank_fee_fixed != 0:
                bank_fee += rec.payment_method_id.bank_fee_fixed
            if bank_fee:
                total_price = sum(rec.pos_order_id.lines.mapped('price_subtotal'))
                for line in rec.pos_order_id.lines:
                    if line.price_subtotal and total_price:
                        bank_fee_per_line = (line.price_subtotal / total_price) * bank_fee
                        line.amount_payment_bank_fee = bank_fee_per_line
                        line.real_margin = line.margin - bank_fee_per_line
