# -- coding: utf-8 --
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Party Commission',
    'version': '18.0.1.0.0',
    'category': 'Sale',
    'summary': 'party commission',
    'description': """
        party commission.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale', 'stock', 'account', 'mail', 'hr'],
    'data': [
        'security/party_commission_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/booking_provsion_action.xml',
        'views/booking_provsion_view.xml',
        'views/account_move_views.xml',
        'wizard/party_commission_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,

}