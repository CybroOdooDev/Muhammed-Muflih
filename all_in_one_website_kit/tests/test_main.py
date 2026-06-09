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


from odoo.tests.common import HttpCase


class TestSaleReturnController(HttpCase):

    def setUp(self):
        super().setUp()

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer'
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })


    def test_01_sale_order_creation(self):
        """Verify sale order creation"""


        self.assertTrue(self.sale_order)

        self.assertEqual(
            self.sale_order.partner_id,
            self.partner
        )


    def test_02_product_creation(self):
        """Verify product creation"""

        self.assertTrue(self.product)

        self.assertEqual(
            self.product.name,
            'Test Product'
        )


    def test_03_sale_return_model_exists(self):
        """Verify sale.return model exists"""

        self.assertIn(
            'sale.return',
            self.env
        )

        self.assertEqual(
            self.env['sale.return']._name,
            'sale.return'
        )


    def test_04_create_sale_return_record(self):
        """Verify sale return creation"""

        return_order = self.env['sale.return'].create({
            'partner_id': self.partner.id,
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'quantity': 1,
            'reason': 'Damaged Product',
        })

        self.assertTrue(return_order)

        self.assertEqual(
            return_order.product_id,
            self.product
        )

        self.assertEqual(
            return_order.order_id,
            self.sale_order
        )


    def test_05_sale_return_default_state(self):
        """Verify default state"""

        return_order = self.env['sale.return'].create({
            'partner_id': self.partner.id,
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'quantity': 1,
            'reason': 'Testing',
        })

        self.assertEqual(
            return_order.state,
            'draft'
        )



    def tearDown(self):

        super().tearDown()