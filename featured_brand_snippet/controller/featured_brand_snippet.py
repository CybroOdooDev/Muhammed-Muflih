#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################

from odoo import http
from odoo.http import request
from odoo.tools import lazy

from odoo.addons.website_sale.const import SHOP_PATH
from odoo.addons.website_sale.controllers.main import (
    TableCompute,
    WebsiteSale,
    _get_category_routes,
)


class WebsiteSales(WebsiteSale):
    """Display products based on selected brands."""

    @http.route([
        SHOP_PATH,
        f"{SHOP_PATH}/page/<int:page>",
        *_get_category_routes(),
        *_get_category_routes("/page/<int:page>"),
        '/shop/brand/<model("product.brand"):brand>',
        '/shop/brand/<model("product.brand"):brand>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, brand=None, products_prices=None,
             **post):
        """Render the shop page, filtering products by brand when provided."""
        res = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            brand=brand,
            products_prices=products_prices,
            **post,
        )
        if not hasattr(res, 'qcontext'):
            return res

        website = self.env.website

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except (ValueError, TypeError):
                ppg = False

        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        Brand = request.env['product.brand']
        Brand.check_access('read')
        brands = Brand.search([])

        if brand:
            url = "/shop/brand/%s" % request.env['ir.http']._slug(brand)
            products_brand = request.env['product.template'].search([
                ('brand_id', '=', brand.id),
                ('sale_ok', '=', True),
                ('is_published', '=', True),
            ])

            product_brand_count = len(products_brand)

            pager_brand = website.pager(
                url=url,
                total=product_brand_count,
                page=page,
                step=ppg,
                scope=7,
                url_args=post,
            )

            offset = pager_brand['offset']
            page_products = products_brand[offset:offset + ppg]

            products_prices = lazy(
                lambda: page_products._get_sales_prices(
                    request.pricelist.with_context(**self.env.context),
                    request.fiscal_position.with_context(**self.env.context),
                    website.with_context(**self.env.context),
                ),
            )

            # The template looks up each product's variant in this mapping
            Product = request.env['product.product']
            Product.check_access('read')
            product_variant_ids = [
                product._get_first_possible_variant_id()
                for product in page_products
            ]
            variants = Product.browse(
                vid for vid in product_variant_ids if vid
            )
            variants.fetch()
            variant_by_id = {v.id: v for v in variants}
            product_variants = dict(
                zip(
                    page_products,
                    (variant_by_id.get(vid, Product) for vid in product_variant_ids),
                ),
            )

            product_query_params = res.qcontext.get('product_query_params')

            res.qcontext.update({
                'product_variants': product_variants,
                'brand': brand,
                'pager': pager_brand,
                'ppg': ppg,
                'products': page_products,
                'search_count': product_brand_count,
                'bins': TableCompute().process(page_products, ppg, ppr),
                'brands': brands,
                'products_prices': products_prices,
                'get_product_prices': lambda product: lazy(
                    lambda: products_prices[product.id],
                ),
                'previewed_attribute_values': lazy(
                    lambda: page_products._get_previewed_attribute_values(
                        product_query_params,
                    ),
                ),
                'structured_data': page_products.with_context(
                    shop_category_id=category.id if category else False,
                )._render_jsonld(),
            })

        else:
            res.qcontext.update({
                'brand': brand,
                'brands': brands,
            })

        return res


class ProductBrandWebsite(http.Controller):
    """Return featured product brands."""

    @http.route(
        '/product_brand',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
    )
    def featured_brands(self):
        """Fetch featured brands for the website carousel."""
        Brand = request.env['product.brand']
        Brand.check_access('read')
        return Brand.search_read(
            [('is_featured_brand', '=', True)],
            ['name', 'id'],
        )
