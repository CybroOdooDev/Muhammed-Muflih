from odoo import models, fields


class PurchaseProductHistory(models.Model):
    _name = 'purchase.product.history'
    _description = 'Purchase Product History'
    _order = 'id desc'

    line_ids = fields.One2many('product.history.line', 'history_id',help="purchase product history lines")
    name = fields.Many2one('purchase.order',help="purchase order")


class ProductHistoryLine(models.Model):
    _name = 'product.history.line'
    _description = 'Product History Line'

    product_id = fields.Many2one('product.product',help="product")
    standard_cost = fields.Float('Cost',help="cost")
    qty = fields.Float('Quantity',help="quantity")
    history_id = fields.Many2one('purchase.product.history',help="history")
