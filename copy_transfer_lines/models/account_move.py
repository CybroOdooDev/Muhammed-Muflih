# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherited account.move and added a relational field move_type_id
    related to model stock.picking"""
    _inherit = 'account.move'

    transfer_type_id = fields.Many2one('stock.picking',string='Move type', help="This field relates to model stock.picking to create account lines in account.move")

    def action_assign_transfer_line(self):
        """Whenever this field is changed from ui it clear all the existing
                invoice lines and adds current move_type_ids lines to the invoice
                lines of account.move model"""
        move_id = self.transfer_type_id
        order_lines_data = [fields.Command.clear()]
        order_lines_data += [
            fields.Command.create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.product_id.lst_price,
            })
            for line in move_id.move_line_ids
        ]
        if len(order_lines_data) >= 2:
            order_lines_data[1][2]['sequence'] = -99
        self.invoice_line_ids = order_lines_data
