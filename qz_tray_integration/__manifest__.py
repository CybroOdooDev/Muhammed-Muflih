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
#############################################################################
{
    'name': 'Qz Tray Integration',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'QZ Tray is a desktop application that connects a web browser '
               'to locally available printers and supported hardware. '
               'It provides a JavaScript API that allows web applications'
               ' to send print jobs to printers.',
    'description': 'QZ Tray is a desktop application that connects a web browser'
                   ' to locally available printers and supported hardware.'
                   ' It provides a JavaScript API that allows web applications '
                   'to send print jobs to printers',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'qz_tray_integration/static/lib/qz-tray.js',
            'qz_tray_integration/static/src/js/qz_service.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
