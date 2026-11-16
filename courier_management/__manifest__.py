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
{
    'name': 'Courier Management',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Create and manage courier requests and delivery tracking',
    'description': 'This module helps you to create and manage courier '
                   'requests for the courier management.Courier Management '
                   'module is designed to efficiently manage and track the '
                   'movement of goods or packages within your organization.'
                   ' This module streamlines the delivery processes,ensuring'
                   ' that your shipments are handled smoothly and delivered '
                   'to the right recipients in a timely manner.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['contacts', 'mail', 'stock', 'account', 'website'],
    'data': [
        'security/courier_management_groups.xml',
        'security/ir.access.csv',
        'security/courier_request_security.xml',
        'data/portal_entry_data.xml',
        'data/courier_request_data.xml',
        'views/account_move_views.xml',
        'views/courier_request_views.xml',
        'views/courier_detail_views.xml',
        'views/courier_tag_views.xml',
        'views/courier_priority_views.xml',
        'views/courier_dimension_price_views.xml',
        'views/courier_distance_price_views.xml',
        'views/courier_weight_price_views.xml',
        'views/courier_type_views.xml',
        'views/courier_category_views.xml',
        'views/courier_management_menus.xml',
        'views/courier_request_templates.xml',
        'views/courier_request_search_group_by_templates.xml',
        'report/courier_request_reports.xml',
        'report/courier_request_templates.xml',
    ],
    'demo': [
        'data/product_product_demo.xml',
        'data/courier_categories_demo.xml',
        'data/courier_priority_demo.xml',
        'data/courier_weight_price_demo.xml',
        'data/courier_dimension_price_demo.xml',
        'data/courier_distance_price_demo.xml',
        'data/courier_tag_demo.xml',
        'data/courier_type_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'courier_management/static/src/js/courier_request_group_by_search.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'price': 29,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': True,
}
