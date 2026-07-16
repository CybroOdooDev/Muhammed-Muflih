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


class ThemeVeloraCollections(http.Controller):
    """Handles redirecting collection routes to Odoo eCommerce categories."""

    @http.route('/collections', type='http', auth='public', website=True)
    def collections_all(self, **kwargs):
        """Redirects the general collections link to the main shop page."""
        return request.redirect('/shop')

    @http.route('/collections/<string:collection_name>', type='http', auth='public', website=True)
    def get_collection(self, collection_name, **kwargs):
        """Finds the matching eCommerce category and redirects, else falls back to all categories."""
        mapping = {
            'mens_collection': ['Mens collection', "Men's Collection", 'Mens Collection', 'men'],
            'womens_collection': ['womens collection', "Women's Collection", 'Womens Collection', 'women'],
            'unisex': ['Unisex', 'unisex'],
            'luxury_gift_sets': ['lexury gift sets', 'luxury gift sets', 'Luxury Gift Sets', 'gift sets', 'Gift Sets'],
            'limited_editions': ['Limited Editions', 'limited editions']
        }
        
        search_terms = mapping.get(collection_name, [collection_name])
        category = False
        
        # Try exact case-insensitive matches first
        for term in search_terms:
            category = request.env['product.public.category'].sudo().search([
                ('name', '=ilike', term)
            ], limit=1)
            if category:
                break
                
        # Try substring case-insensitive matches next
        if not category:
            for term in search_terms:
                category = request.env['product.public.category'].sudo().search([
                    ('name', 'ilike', term)
                ], limit=1)
                if category:
                    break
                    
        if category:
            return request.redirect(f'/shop/category/{category.id}')
        return request.redirect('/shop')

    @http.route('/collections/redirect', type='http', auth='public', website=True)
    def redirect_collection(self, name, **kwargs):
        """Finds the matching eCommerce category by name and redirects, else falls back to shop."""
        if not name:
            return request.redirect('/shop')
            
        name_clean = name.strip().lower()
        search_terms = [name, name_clean]
        
        # Expand common search variations for reliability
        if 'men' in name_clean:
            search_terms.extend(['Mens collection', "Men's Collection", 'men'])
        if 'women' in name_clean:
            search_terms.extend(['womens collection', "Women's Collection", 'women'])
        if 'unisex' in name_clean:
            search_terms.extend(['unisex'])
        if 'gift' in name_clean:
            search_terms.extend(['lexury gift sets', 'luxury gift sets', 'Luxury Gift Sets', 'gift sets', 'gift'])
        if 'limited' in name_clean:
            search_terms.extend(['Limited Editions', 'limited editions', 'limited'])
            
        category = False
        
        # Try exact case-insensitive matches first
        for term in search_terms:
            category = request.env['product.public.category'].sudo().search([
                ('name', '=ilike', term)
            ], limit=1)
            if category:
                break
                
        # Try substring case-insensitive matches next
        if not category:
            for term in search_terms:
                category = request.env['product.public.category'].sudo().search([
                    ('name', 'ilike', term)
                ], limit=1)
                if category:
                    break
                    
        if category:
            return request.redirect(f'/shop/category/{category.id}')
        return request.redirect('/shop')


try:
    from odoo.addons.theme_flynova.controllers.theme_flynova import FlynovaThemeController
except ImportError:
    FlynovaThemeController = object


class ThemeVeloraAboutUs(FlynovaThemeController if FlynovaThemeController is not object else http.Controller):

    @http.route(['/about-us', '/about', '/aboutus'], type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        return request.render('website.aboutus', {})




