# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockPicking(TransactionCase):
    """Test cases for Stock Picking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer'
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.picking_type = cls.env.ref('stock.picking_type_out')

        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.customer.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'picking_type_id': cls.picking_type.id,
        })

        cls.move = cls.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': cls.product.id,
            'product_uom_qty': 5,
            'product_uom': cls.product.uom_id.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'picking_id': cls.picking.id,
        })

    def test_action_select_all(self):
        """Test selecting all move lines."""
        self.move.product_select = False

        self.picking.action_select_all()

        self.assertTrue(
            self.picking.select_all_toggle,
            "Select All toggle should be enabled."
        )

        self.assertTrue(
            self.move.product_select,
            "Move should be selected."
        )


    def test_action_unselect_all(self):
        """Test unselecting all move lines."""
        self.move.product_select = True
        self.picking.select_all_toggle = True

        self.picking.action_unselect_all()

        self.assertFalse(
            self.picking.select_all_toggle,
            "Select All toggle should be disabled."
        )

        self.assertFalse(
            self.move.product_select,
            "Move should be unselected."
        )


    def test_action_fill_done_qty(self):
        """Test filling done quantity."""

        self.move.product_select = True

        # Force forecast availability
        self.move.forecast_availability = 10

        self.move.quantity = 0

        self.picking.action_fill_done_qty()

        self.assertEqual(
            self.move.quantity,
            self.move.product_uom_qty,
            "Done quantity should match demanded quantity."
        )


    def test_action_unfill_done_qty(self):
        """Test clearing done quantity."""

        self.move.product_select = True
        self.move.quantity = 5

        self.picking.action_unfill_done_qty()

        self.assertEqual(
            self.move.quantity,
            0,
            "Done quantity should be reset to zero."
        )
