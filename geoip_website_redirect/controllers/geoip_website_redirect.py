# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging
import requests
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)

PRICELIST_SESSION_KEY = 'website_sale_current_pl'


class Geolocation(Home):
    """ Controller for GeoIP-based language and currency selection. """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_ip_location(self, ip_address):
        """Return {'country': <name>} for an IP address, or {} on failure."""
        if not ip_address:
            return {}
        try:
            resp = requests.get(
                f'http://ip-api.com/json/{ip_address}', timeout=5
            ).json()
            country = resp.get('country')
            return {'country': country} if country else {}
        except Exception as e:
            _logger.warning('GeoIP lookup failed for %s: %s', ip_address, e)
            return {}

    def _apply_lang_and_currency(self, country_name, user=None):
        """
        Given a country name (from countryinfo / ip-api):
        1. Activate the country's primary language and add it to the website.
        2. Activate the country's currency.
        3. Find (or use the first available) pricelist whose currency matches.
        4. Store the pricelist id in the session (shop) and on the partner (portal).

        Returns (language_record, pricelist_record) — either can be empty.
        """
        try:
            from countryinfo import CountryInfo
            country_info = CountryInfo(country_name)
        except Exception as e:
            _logger.warning('CountryInfo lookup failed for %s: %s', country_name, e)
            return None, None

        env = request.env
        language = None
        pricelist = None

        # --- Language ---
        try:
            langs = country_info.languages()
            if langs:
                language = env['res.lang'].sudo().search(
                    [('iso_code', '=', langs[0]),
                     ('active', 'in', [True, False])], limit=1
                )
                if language:
                    language.sudo().write({'active': True})
                    website = (
                        request.website.sudo()
                        if getattr(request, 'website', None)
                        else env['website'].sudo().search([], limit=1)
                    )
                    if website:
                        website.sudo().write({'language_ids': [(4, language.id)]})
                    if user:
                        user.sudo().write({'lang': language.code})
                    # Push lang into session context
                    ctx = dict(request.session.get('context', {}))
                    ctx['lang'] = language.code
                    request.session['context'] = ctx
        except Exception as e:
            _logger.warning('Language resolution failed for %s: %s', country_name, e)

        # --- Currency + Pricelist ---
        try:
            currencies = country_info.currencies()
            if currencies:
                currency = env['res.currency'].sudo().search(
                    [('name', '=', currencies[0]),
                     ('active', 'in', [True, False])], limit=1
                )
                if currency:
                    currency.sudo().write({'active': True})

                    # Find a pricelist that uses this currency (no hardcoding)
                    website_obj = (
                        request.website.sudo()
                        if getattr(request, 'website', None)
                        else env['website'].sudo().search([], limit=1)
                    )
                    available = (
                        website_obj.get_pricelist_available()
                        if website_obj
                        else env['product.pricelist'].sudo().search([])
                    )
                    pricelist = next(
                        (pl for pl in available if pl.currency_id == currency),
                        None
                    )
                    # Fall back: any pricelist with that currency
                    if not pricelist:
                        pricelist = env['product.pricelist'].sudo().search(
                            [('currency_id', '=', currency.id)], limit=1
                        )

                    if pricelist:
                        # Update shop session
                        request.session[PRICELIST_SESSION_KEY] = pricelist.id
                        # Update portal (partner's property pricelist)
                        if user:
                            partner = user.sudo().partner_id
                            if partner:
                                partner.sudo().write(
                                    {'property_product_pricelist': pricelist.id}
                                )
        except Exception as e:
            _logger.warning('Currency/pricelist resolution failed for %s: %s', country_name, e)

        return language, pricelist

    # ------------------------------------------------------------------
    # Login override — apply GeoIP settings right after login
    # ------------------------------------------------------------------

    @http.route()
    def web_login(self, redirect=None, **kw):
        """On login: detect country from IP → set language, currency & pricelist."""
        user_ip = kw.get('user_ip')
        if user_ip and hasattr(request, 'session'):
            request.session['user_ip'] = user_ip

        result = super().web_login(redirect=redirect, **kw)

        if not request.session.uid:
            return result

        user = request.env.user.sudo()

        # Resolve best available IP
        if not user_ip and hasattr(request, 'session'):
            user_ip = request.session.get('user_ip') or user.ip_address
        if not user_ip:
            addr = getattr(request.httprequest, 'remote_addr', None)
            if addr and addr not in ('127.0.0.1', '::1', 'localhost'):
                user_ip = addr

        if user_ip:
            user.write({'ip_address': user_ip})
            if hasattr(request, 'session'):
                request.session['user_ip'] = user_ip

            location = self._get_ip_location(user_ip)
            country_name = location.get('country')
            if country_name:
                language, _pricelist = self._apply_lang_and_currency(
                    country_name, user=user
                )
                if language:
                    return request.redirect(f'/{language.url_code}')

        return result

    # ------------------------------------------------------------------
    # New JSON route — called by JS when user picks a different language
    # ------------------------------------------------------------------

    @http.route(
        '/geoip/set_currency_by_lang',
        type='jsonrpc',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=False,
    )
    def set_currency_by_lang(self, lang_url_code=None, **kw):
        """
        Called from the frontend when the user clicks a language option.

        Looks up the country whose primary language matches `lang_url_code`,
        then applies the matching currency and pricelist — no hardcoding.

        Returns {'success': True, 'pricelist_id': <id>} or {'success': False}.
        """
        if not lang_url_code:
            return {'success': False, 'error': 'No lang_url_code provided'}

        try:
            env = request.env
            # Resolve the res.lang record from the url_code
            lang_rec = env['res.lang'].sudo().search(
                [('url_code', '=', lang_url_code),
                 ('active', 'in', [True, False])], limit=1
            )
            if not lang_rec:
                # Try by code directly
                lang_rec = env['res.lang'].sudo().search(
                    [('code', '=', lang_url_code),
                     ('active', 'in', [True, False])], limit=1
                )

            if not lang_rec:
                return {'success': False, 'error': f'Language not found: {lang_url_code}'}

            # Find the country that uses this language as its primary language
            # We use res.country which has a lang_id or search via countryinfo
            # Strategy: find a res.country whose language code (iso) matches lang iso_code
            iso_code = lang_rec.iso_code  # e.g. 'hi', 'en', 'fr'

            country_rec = env['res.country'].sudo().search([], limit=0)
            target_country = None

            # Use countryinfo to find which country matches this ISO language
            try:
                from countryinfo import CountryInfo
                # CountryInfo doesn't provide reverse lookup, so we iterate
                # on Odoo res.country records and check via their alpha2 code
                all_countries = env['res.country'].sudo().search([('code', '!=', False)])
                for c in all_countries:
                    try:
                        ci = CountryInfo(c.name)
                        langs = ci.languages()
                        if langs and langs[0] == iso_code:
                            target_country = c.name
                            break
                    except Exception:
                        continue
            except Exception as e:
                _logger.warning('CountryInfo reverse lookup failed: %s', e)

            if not target_country:
                # Fallback: use the lang itself to find currency via res.country lang_id field
                country_by_lang = env['res.country'].sudo().search(
                    [('lang_ids.code', '=', lang_rec.code)], limit=1
                )
                if country_by_lang:
                    target_country = country_by_lang.name

            if not target_country:
                return {'success': False, 'error': f'No country found for language: {iso_code}'}

            user = None
            if request.session.uid:
                user = env.user.sudo()

            _language, pricelist = self._apply_lang_and_currency(
                target_country, user=user
            )

            return {
                'success': True,
                'pricelist_id': pricelist.id if pricelist else False,
                'country': target_country,
            }

        except Exception as e:
            _logger.exception('Error in set_currency_by_lang: %s', e)
            return {'success': False, 'error': str(e)}
