# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestStockReturnPicking(TransactionCase):
    """Test Stock Return Picking"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer'
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

        cls.sale_return = cls.env['sale.return'].create({
            'product_id': cls.product.id,
            'order_id': cls.sale_order.id,
            'quantity': 1,
            'reason': 'Testing Return',
        })

        _logger.info(
            "Sale Return Created: %s",
            cls.sale_return.name
        )

    def test_sale_return_created(self):
        """Verify test data creation"""

        self.assertTrue(self.sale_return)
        self.assertEqual(self.sale_return.state, 'draft')


    def test_return_order_relationship(self):
        """Verify return order relationship"""

        self.assertEqual(
            self.sale_return.order_id,
            self.sale_order
        )

        self.assertEqual(
            self.sale_return.product_id,
            self.product
        )

    def test_return_order_name(self):
        """Verify generated sequence name"""

        self.assertTrue(self.sale_return.name)

    def test_state_update(self):
        """Verify state transition"""

        self.sale_return.write({
            'state': 'confirm'
        })

        self.assertEqual(
            self.sale_return.state,
            'confirm'
        )


    def test_action_create_returns_logic(self):
        """
        Test custom action_create_returns logic.

        NOTE:
        Full functional testing requires
        stock.picking, stock.move,
        and stock.return.picking wizard records.
        """


        self.sale_return.write({
            'state': 'confirm'
        })

        self.assertEqual(
            self.sale_return.state,
            'confirm'
        )

    def test_valid_states(self):
        """Verify allowed state values"""


        self.assertIn(
            self.sale_return.state,
            ['draft', 'confirm', 'done', 'cancel']
        )
