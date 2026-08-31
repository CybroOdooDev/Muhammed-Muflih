from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'


    margin = fields.Monetary(
        string="Margin", compute='_compute_margin',
        groups='inventory_stock_report_extends.can_print_inventory_report',help="margin")
    margin_percent = fields.Float(
        string="Margin (%)", compute='_compute_margin',
        digits=(12, 4), groups='inventory_stock_report_extends.can_print_inventory_report',help="margin percentage")


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    margin = fields.Monetary(
        string="Margin", compute='_compute_margin',
        groups='inventory_stock_report_extends.can_print_inventory_report',help=" product margin")
    margin_percent = fields.Float(
        string="Margin (%)", compute='_compute_margin', digits=(12, 4),
        groups='inventory_stock_report_extends.can_print_inventory_report',help="product margin percentage")

    total_cost = fields.Float(
        string='Total cost', digits='Product Price', readonly=True,
        groups='inventory_stock_report_extends.can_print_inventory_report',help="Total cost")

    def _compute_total_cost(self, stock_moves):
        """
        Compute the total cost of the order lines.
        :param stock_moves: recordset of `stock.move`, used for fifo/avco lines
        """
        for line in self.filtered(lambda l: not l.is_total_cost_computed):
            product = line.product_id
            if line._is_product_storable_fifo_avco() and stock_moves:
                product_cost = product._compute_average_price(0, line.qty,
                                                              line._get_stock_moves_to_consider(
                                                                  stock_moves,
                                                                  product))
            else:
                product_cost = product.standard_price
            line.sudo().total_cost = line.qty * product.cost_currency_id._convert(
                from_amount=product_cost,
                to_currency=line.currency_id,
                company=line.company_id or self.env.company,
                date=line.order_id.date_order or fields.Date.today(),
                round=False,
            )
            line.is_total_cost_computed = True
