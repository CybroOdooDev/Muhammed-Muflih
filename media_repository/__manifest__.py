# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Media Repository',
    'version': '19.0.0.0',
    'summary': 'Centralized location for storing, organizing, searching, and managing media assets',
    'depends': ['base', 'mail'],
    'application': True,
    'installable': True,
    'data': [
        'security/ir.model.access.csv',
        'views/media_asset_views.xml',
        'views/media_category_views.xml',
    ],
}