# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ThemeVeloraCart(http.Controller):
    """Serves the real Odoo cart content for the Velora header cart drawer."""

    @http.route('/theme_velora/cart_drawer', type='json', auth='public', website=True)
    def cart_drawer(self):
        order = request.website.sale_get_order()
        lines = []
        for line in (order.website_order_line if order else []):
            if not line.product_id:
                continue
            lines.append({
                'line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.name_short or line.product_id.name,
                'qty': line._get_displayed_quantity(),
                'price': line._get_cart_display_price(),
                'image_url': f'/web/image/product.product/{line.product_id.id}/image_128',
            })
        cart_total = request.env['ir.ui.view']._render_template(
            'website_sale.total', {'website_sale_order': order}
        )
        return {
            'lines': lines,
            'website_sale.total': cart_total,
            'cart_quantity': order.cart_quantity if order else 0,
            'currency_symbol': order.currency_id.symbol if order else '$',
        }
