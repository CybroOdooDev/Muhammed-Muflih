# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import http
from odoo.addons.portal.controllers import portal
from odoo.http import request


class CourierRequests(http.Controller):
    """This controller is for portal"""

    def _get_courier_domain(self):
        """It returns the login person domain or all records for administrator"""
        if request.env.user.has_group(
                'courier_management.courier_management_group_administrator'):
            return []
        return [('sender_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/courier/requests'], type='http', auth="user",
                website=True)
    def get_my_courier_requests(self):
        """Take values from courier requests and render to portal list
        template """
        domain = self._get_courier_domain()
        values = {
            'courier_request': request.env['courier.request'].search(domain),
            'page_name': 'courier_requests',
        }
        return request.render(
            "courier_management.portal_my_courier_requests_list", values)

    @http.route(['/my/courier/requests/form/<int:courier_id>'], type='http',
                auth="user", website=True)
    def get_my_courier_request_form(self, courier_id):
        """Take values from courier_request and render to portal form
        template. It also validates that the record belongs to the logged-in user or administrator."""
        domain = [('id', '=', courier_id)]
        if not request.env.user.has_group(
                'courier_management.courier_management_group_administrator'):
            domain.append(('sender_id', '=', request.env.user.partner_id.id))
        courier_request = request.env['courier.request'].search(domain, limit=1)
        if not courier_request:
            return request.redirect('/my/courier/requests')
        values = {
            'record_courier_requests': courier_request,
            'page_name': 'courier_request_form',
        }
        return request.render(
            "courier_management.portal_my_courier_requests_form", values)

    @http.route(['/courier/requests/group/by'], type='json', auth="user",
                website=True)
    def courier_requests_group_by(self, **kwargs):
        """Call from rpc for group by, and it returns the corresponding
        rendered template"""
        group_value = kwargs.get("search_value")
        is_admin = request.env.user.has_group(
            'courier_management.courier_management_group_administrator')
        base_domain = [] if is_admin else [
            ('sender_id', '=', request.env.user.partner_id.id)]

        if group_value == '0':
            records = request.env['courier.request'].search(base_domain)
            return request.env['ir.qweb']._render(
                'courier_management.portal_my_certificates_search',
                {'courier_request': records})

        context = []
        if group_value == '1':
            for types in request.env['courier.type'].search([]):
                domain = [('type_id', '=', types.id)] + base_domain
                records = request.env['courier.request'].search(domain)
                if records:
                    context.append({
                        'name': types.courier_type,
                        'data': records,
                    })
        elif group_value == '2':
            for categories in request.env['courier.category'].search([]):
                domain = [('category_id', '=', categories.id)] + base_domain
                records = request.env['courier.request'].search(domain)
                if records:
                    context.append({
                        'name': categories.courier_category,
                        'data': records,
                    })

        values = {
            'courier_request': context,
        }
        return request.env['ir.qweb']._render(
            'courier_management.courier_requests_group_by_template', values)

    @http.route(['/courier/requests/search'], type='json', auth="user",
                website=True)
    def courier_requests_search(self, **kwargs):
        """It gives the values and return the response to corresponding
        template"""
        search_value = (kwargs.get("search_value") or "").strip()
        is_admin = request.env.user.has_group(
            'courier_management.courier_management_group_administrator')
        domain = [] if is_admin else [
            ('sender_id', '=', request.env.user.partner_id.id)]
        if search_value:
            domain.append(('name', 'ilike', f'%{search_value}%'))
        record = request.env["courier.request"].search(domain)
        return request.env['ir.qweb']._render(
            'courier_management.portal_my_certificates_search',
            {'courier_request': record})


class CourierPortal(portal.CustomerPortal):
    """This will take the count of total courier requests"""

    def _prepare_portal_counter_values(self, counter):
        """Prepare counter values for Odoo 20 portal cards"""
        if counter == 'courier_requests_count':
            domain = [('sender_id', '=', request.env.user.partner_id.id)]
            return 'courier.request', domain, 'read'
        return super()._prepare_portal_counter_values(counter)

    def _prepare_home_portal_values(self, counters):
        """This will return the courier requests count"""
        values = super()._prepare_home_portal_values(counters)
        if 'courier_requests_count' in counters:
            values.update({
                'courier_requests_count': request.env[
                    'courier.request'].search_count(
                    [('sender_id', '=', request.env.user.partner_id.id)]),
            })
        return values
