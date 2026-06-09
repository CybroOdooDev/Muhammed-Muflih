# -*- coding: utf-8 -*-


from odoo.tests.common import TransactionCase



class TestStockPicking(TransactionCase):
    """Test cases for stock picking return order functionality"""

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
            'reason': 'Test Return',
        })


    def test_inherited_fields(self):
        """Test inherited fields exist in stock.picking"""

        stock_picking = self.env['stock.picking']

        self.assertIn('return_order_id', stock_picking._fields)
        self.assertIn('return_order_pick_id', stock_picking._fields)
        self.assertIn('return_order_picking', stock_picking._fields)

    def test_sale_return_default_state(self):
        """Test default state of sale return"""


        self.assertEqual(
            self.sale_return.state,
            'draft'
        )


    def test_return_order_relations(self):
        """Test return order relations"""

        self.assertEqual(
            self.sale_return.product_id,
            self.product
        )

        self.assertEqual(
            self.sale_return.order_id,
            self.sale_order
        )


    def test_return_order_picking_field(self):
        """Test return_order_picking field"""

        picking = self.env['stock.picking'].new({
            'return_order_picking': True
        })

        self.assertTrue(
            picking.return_order_picking
        )

    def test_state_update_logic(self):
        """
        Simulate completed return process.
        """

        self.sale_return.write({
            'state': 'confirm'
        })

        self.assertEqual(
            self.sale_return.state,
            'confirm'
        )

        self.sale_return.write({
            'state': 'done'
        })

        self.assertEqual(
            self.sale_return.state,
            'done'
        )

