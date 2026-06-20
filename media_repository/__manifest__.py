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
        'security/media_repository_groups.xml',
        'security/ir.model.access.csv',
        'security/media_repository_record_rules.xml',
        'views/media_asset_views.xml',
        'views/media_category_views.xml',
    ],
}