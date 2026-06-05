# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
##############################################################################



from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase



@tagged('post_install', '-at_install')
class TestQuickSaleLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Quick Sale Test Product',
            'list_price': 125.0,
        })
        cls.sale_tax = cls.env['account.tax'].create({
            'name': 'Quick Sale Test Tax 10%',
            'amount': 10.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })
        cls.replacement_tax = cls.env['account.tax'].create({
            'name': 'Quick Sale Replacement Tax 5%',
            'amount': 5.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })
        cls.order = cls.env['quick.sale.order'].create({})

    def test_quick_sale_line_creation(self):
        """A quick sale line stores its order, product, quantity, price, and taxes."""
        line = self.env['quick.sale.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 3.0,
            'price_unit': 115.0,
            'tax_ids': [Command.set(self.sale_tax.ids)],
        })

        self.assertEqual(line.order_id, self.order)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.product_uom_qty, 3.0)
        self.assertEqual(line.price_unit, 115.0)
        self.assertEqual(line.tax_ids, self.sale_tax)
        self.assertIn(line, self.order.line_ids)

    def test_quick_sale_line_can_be_updated(self):
        """Editable wizard values and many-to-many taxes can be replaced."""
        line = self.env['quick.sale.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 125.0,
            'tax_ids': [Command.set(self.sale_tax.ids)],
        })

        line.write({
            'product_uom_qty': 4.0,
            'price_unit': 100.0,
            'tax_ids': [Command.set(self.replacement_tax.ids)],
        })

        self.assertEqual(line.product_uom_qty, 4.0)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.tax_ids, self.replacement_tax)

    def test_required_fields(self):
        """Product and unit price remain required in the wizard model."""
        product_field = self.env['quick.sale.line']._fields['product_id']
        price_field = self.env['quick.sale.line']._fields['price_unit']

        self.assertTrue(product_field.required)
        self.assertTrue(price_field.required)
