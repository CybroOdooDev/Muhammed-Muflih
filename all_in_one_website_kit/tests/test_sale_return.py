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


from odoo.tests.common import TransactionCase



class TestSaleReturn(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer'
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu'
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

        cls.sale_return = cls.env['sale.return'].create({
            'product_id': cls.product.id,
            'order_id': cls.sale_order.id,
            'quantity': 2,
            'reason': 'Damaged Product'
        })


    def test_sale_return_creation(self):
        """Test Sale Return Record Creation"""

        self.assertTrue(self.sale_return)
        self.assertEqual(
            self.sale_return.product_id.id,
            self.product.id
        )

    def test_return_cancel(self):
        """Test Return Cancel Action"""

        self.sale_return.return_cancel()

        self.assertEqual(
            self.sale_return.state,
            'cancel'
        )

    def test_compute_access_url(self):
        """Test Access URL Computation"""

        self.sale_return._compute_access_url()

        self.assertIn(
            '/my/return_orders/',
            self.sale_return.access_url
        )


    def test_report_filename(self):
        """Test Report Filename"""

        filename = self.sale_return._get_report_base_filename()

        self.assertIn(
            'Sale Return',
            filename
        )


    def test_delivery_picking_count(self):
        """Test Picking Count Computation"""

        self.sale_return._compute_delivery_picking_count()

        self.assertGreaterEqual(
            self.sale_return.delivery_count,
            0
        )

        self.assertGreaterEqual(
            self.sale_return.picking_count,
            0
        )


    def test_onchange_sale_order(self):
        """Test Sale Order Onchange"""

        result = self.sale_return._onchange_sale_order()

        self.assertIsInstance(result, dict)

    def test_onchange_product(self):
        """Test Product Onchange"""

        self.sale_return._onchange_product_id()

        self.assertGreaterEqual(
            self.sale_return.received_qty,
            0
        )

