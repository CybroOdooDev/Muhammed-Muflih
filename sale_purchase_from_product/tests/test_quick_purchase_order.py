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

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase



@tagged('post_install', '-at_install')
class TestQuickPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Quick Purchase Test Vendor',
            'supplier_rank': 1,
        })
        cls.purchase_tax = cls.env['account.tax'].create({
            'name': 'Quick Purchase Order Tax 10%',
            'amount': 10.0,
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Quick Purchase Order Product',
            'list_price': 125.0,
            'supplier_taxes_id': [Command.set(cls.purchase_tax.ids)],
        })

    def _create_wizard(self, **values):
        wizard_values = {
            'partner_id': self.vendor.id,
            'line_ids': [Command.create({
                'product_id': self.product.id,
                'product_qty': 3.0,
                'price_unit': 115.0,
                'tax_ids': [Command.set(self.purchase_tax.ids)],
            })],
        }
        wizard_values.update(values)
        return self.env['quick.purchase.order'].create(wizard_values)

    def test_purchase_order_domain(self):
        """Only draft and sent purchase orders are selectable."""
        wizard_model = self.env['quick.purchase.order']

        self.assertEqual(
            wizard_model._purchase_ids_domain(),
            [('state', 'in', ['draft', 'sent'])],
        )

    def test_default_get_creates_lines_from_active_products(self):
        """Selected products become wizard lines with default quantity and price."""
        wizard = self.env['quick.purchase.order'].with_context(
            active_ids=self.product.ids,
        ).create({})

        self.assertEqual(wizard.type, 'new_order')
        self.assertEqual(wizard.user_id, self.env.user)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.product_id, self.product)
        self.assertEqual(wizard.line_ids.product_qty, 1.0)
        self.assertEqual(wizard.line_ids.price_unit, self.product.lst_price)

    def test_action_create_purchase_order(self):
        """The wizard creates a purchase order with matching line values."""
        order_date = fields.Datetime.now()
        wizard = self._create_wizard(order_date=order_date)

        order = wizard.action_create()

        self.assertEqual(order.partner_id, self.vendor)
        self.assertEqual(order.user_id, self.env.user)
        self.assertEqual(order.date_order, order_date)
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_id, self.product)
        self.assertEqual(order.order_line.product_qty, 3.0)
        self.assertEqual(order.order_line.price_unit, 115.0)
        self.assertEqual(order.order_line.tax_ids, self.purchase_tax)

    def test_action_update_existing_purchase_order(self):
        """Wizard lines are appended to every selected purchase order."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
        })
        wizard = self._create_wizard(
            type='existing_order',
            purchase_ids=[Command.set(purchase_order.ids)],
        )

        wizard.action_update_order()

        self.assertEqual(len(purchase_order.order_line), 1)
        self.assertEqual(purchase_order.order_line.product_id, self.product)
        self.assertEqual(purchase_order.order_line.product_qty, 3.0)
        self.assertEqual(purchase_order.order_line.price_unit, 115.0)
        self.assertEqual(purchase_order.order_line.tax_ids, self.purchase_tax)

    def test_action_create_view(self):
        """Create-and-view returns the purchase order form action."""
        wizard = self._create_wizard()

        action = wizard.action_create_view()
        order = self.env['purchase.order'].browse(action['res_id'])

        self.assertTrue(order.exists())
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'purchase.order')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['views'], [(False, 'form')])
        self.assertEqual(
            action['view_id'],
            self.env.ref('purchase.purchase_order_form').id,
        )
