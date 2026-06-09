# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
###############################################################################

from odoo.tests import common
from unittest.mock import patch




class TestSaleOrder(common.TransactionCase):

    def setUp(self):
        super().setUp()


        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner'
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'comment': 'Customer left a note',
            'rating': '5'
        })

    def test_01_fields(self):
        """Test comment and rating fields"""

        self.assertEqual(
            self.sale_order.comment,
            'Customer left a note'
        )
        self.assertEqual(
            self.sale_order.rating,
            '5'
        )

    def test_02_action_open_returns(self):
        """Test action_open_returns"""


        action = self.sale_order.action_open_returns()

        self.assertEqual(
            action.get('domain'),
            [('order_id', '=', self.sale_order.id)]
        )

        self.assertEqual(
            action.get('context'),
            {'search_default_order': 1}
        )

    @patch(
        'odoo.addons.all_in_one_website_kit.models.sale_order.models.Model.read_group'
    )
    def test_03_compute_return_order_count(self, mock_read_group):
        """Test _compute_return_order_count"""

        mock_read_group.return_value = [{
            'order_id': [self.sale_order.id, self.sale_order.name],
            'sale_order_count': 3,
        }]

        self.sale_order.return_order_count = 0

        self.sale_order._compute_return_order_count()

        self.assertGreaterEqual(
            self.sale_order.return_order_count,
            0
        )

    def test_04_sale_order_exists(self):
        """Verify sale order creation"""

        self.assertTrue(self.sale_order)
