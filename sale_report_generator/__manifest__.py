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
    'name': 'Sales All In One Report Generator',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Generates All in One Dynamic Sales Reports',
    'description': """This module facilitates comprehensive Sale Reports,
     offering insights into a company's sales analysis from various
     angles, including orders, order details, sales representatives, and the
     ability to filter data by different date ranges.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.access.csv',
        'report/sale_order_reports.xml',
        'report/sale_order_templates.xml',
        'views/sale_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_report_generator/static/src/js/sale_report.js',
            'sale_report_generator/static/src/css/sale_report.css',
            'sale_report_generator/static/src/xml/sale_report_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
