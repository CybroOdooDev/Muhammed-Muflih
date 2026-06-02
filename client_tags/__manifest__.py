# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CLIENT TAGS',
    'version': '1.0',
    'description': "users can set the tags",
    'depends': ['base','base_setup','sale','purchase'],
    'data': [
        'views/res_config_settings.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
    ],

    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}