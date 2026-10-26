# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'Sales Incentives',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "This module calculates incentives for salespeople based on "
               "gamification target achievements",
    'description': "This module calculates incentives for salespeople based on "
                   "gamification targets, salesman commission, sales achievement, "
                   "and goals.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['crm', 'sales_team', 'gamification', 'account'],
    'data': [
        'security/ir.access.csv',
        'views/sales_incentive_views.xml',
        'views/incentive_approve_views.xml',
        'views/goal_views.xml',
        'views/gamification_challenge_views.xml',
        'report/incentive_report.xml',
        'views/calculate_incentive_views.xml',
        'views/sales_incentive_calculation_menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'price': 79,
    'currency': 'EUR',
}
