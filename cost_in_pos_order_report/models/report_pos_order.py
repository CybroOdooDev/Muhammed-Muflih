# -*- coding: utf-8 -*-
from odoo import models, fields


class ReportPosOrder(models.Model):
    _inherit = "report.pos.order"

    total_cost = fields.Float(string='Total Cost', readonly=True,help="Total Cost")
    list_price = fields.Float(string='Total List Price', readonly=True,help="Total List Price")
    list_margin = fields.Float(string='List Margin', readonly=True,help="List Margin")
    margin = fields.Float(string='Margin', readonly=True,help="Margin")
    real_margin = fields.Float(string='Real Margin', readonly=True,help="Real Margin")
    amount_payment_bank_fee = fields.Float(string="Bank Fee", readonly=True,help="Bank Fee")

    def _select(self):
        """Extend the SELECT clause of the POS order report SQL query.

        Adds additional reporting fields including total cost, payment bank fees,
        real margin (after bank fee deduction), total list price, and list margin.
        """
        return super()._select() + (
            ', l.total_cost AS total_cost'
            ', l.amount_payment_bank_fee AS amount_payment_bank_fee'
            ', l.real_margin AS real_margin'
            ', pt.list_price * l.qty AS list_price'
            ', (pt.list_price * l.qty) - ROUND('
            '    (l.qty * l.price_unit) * (100 - l.discount) / 100'
            '    / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END,'
            '    cu.decimal_places'
            ') AS list_margin'
        )