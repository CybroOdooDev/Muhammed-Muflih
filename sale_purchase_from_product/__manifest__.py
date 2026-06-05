# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Sale/Purchase Orders from Products',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Create and update Sale/Purchase Orders directly from Product Variant view',
    'description': """This module enhances product management by allowing users to create or update Sale and 
                        Purchase Orders directly from the Product Variant tree view.

                        Users can select multiple product variants and quickly generate new draft orders or 
                        add them to existing orders, eliminating the need to navigate through multiple menus.
                        
                        Key Features:
                        - Create Sale Orders from selected product variants
                        - Create Purchase Orders from selected product variants
                        - Add products to existing draft orders
                        - Bulk selection support for faster operations
                        - Streamlined workflow with reduced navigation
                        
                        This module improves efficiency for sales and purchase teams by simplifying order creation 
                        directly from product listings.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'purchase', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/quick_sale_order_views.xml',
        'wizard/quick_purchase_order_views.xml',
        'views/product_product_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
