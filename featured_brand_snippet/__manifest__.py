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
{
    'name': 'Featured Brand Snippet',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Dynamic snippet for displaying featured product brands',
    'description': """
        Display featured product brands in a dynamic carousel
        and allow customers to view the products of each brand.
    """,
    'author': 'Cybrosys Technologies',
    'company': 'Cybrosys Technologies',
    'maintainer': 'Cybrosys Technologies',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'product_brand_sale',
        'website_sale',
    ],
    'data': [
        'security/ir.access.csv',
        'views/product_brand_views.xml',
        'views/brand_snippet_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'featured_brand_snippet/static/src/xml/dynamic_brand_carousel.xml',
            'featured_brand_snippet/static/src/js/brand_selection.js',
            'featured_brand_snippet/static/src/scss/responsive_style.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
}
