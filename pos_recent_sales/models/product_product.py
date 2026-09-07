# -*- coding: utf-8 -*-
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_info_pos(self, price, quantity, pos_config_id):
        """Fetch POS product information and include the latest 3 POS sale records.
        """
        res = super().get_product_info_pos(price, quantity, pos_config_id)
        config = self.env['pos.config'].browse(pos_config_id)

        domain = [
            ('product_id', '=', self.id),
            ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
        ]
        if config and config.company_id:
            domain.append(('order_id.company_id', '=', config.company_id.id))

        recent_lines = self.env['pos.order.line'].search(
            domain,
            order='create_date desc, id desc',
            limit=3
        )

        recent_sales = []
        for line in recent_lines:
            order = line.order_id
            order_name = order.name or order.pos_reference or ''
            date_str = order.date_order.strftime('%Y-%m-%d %H:%M') if order.date_order else ''
            customer_name = order.partner_id.name if order.partner_id else 'Walk-in Customer'

            recent_sales.append({
                'id': line.id,
                'order_name': order_name,
                'date': date_str,
                'customer': customer_name,
                'price_unit': line.price_unit,
            })

        res['recent_pos_sales'] = recent_sales
        return res
