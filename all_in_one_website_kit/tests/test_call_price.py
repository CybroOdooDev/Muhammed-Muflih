
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

from odoo.tests import common


class TestCallPrice(common.TransactionCase):
    def setUp(self):
        super(TestCallPrice, self).setUp()
        
        self.product_template = self.env['product.template'].create({
            'name': 'Test Product Template',
            'list_price': 100.0,
        })
        
        self.call_price = self.env['call.price'].create({
            'first_name': 'John',
            'last_name': 'Doe',
            'product_id': self.product_template.id,
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'quantity': 5,
            'message': 'Test message'
        })

    def test_01_default_state(self):
        """Test default state is draft"""
        self.assertEqual(self.call_price.state, 'draft', 'Default state should be draft')

    def test_02_action_done(self):
        """Test action_done changes state to done"""
        self.call_price.action_done()
        self.assertEqual(self.call_price.state, 'done', 'State should be changed to done')

    def test_03_action_cancel(self):
        """Test action_cancel changes state to cancel"""
        self.call_price.action_cancel()
        self.assertEqual(self.call_price.state, 'cancel', 'State should be changed to cancel')

    def test_04_create_form(self):
        """Test create_form method correctly creates a record"""
        
        self.env['call.price'].create_form(
            first='Jane',
            last='Smith',
            product_id=self.product_template.id,
            phone='0987654321',
            email='jane.smith@example.com',
            message='Another test message',
            qty=10
        )
        
        created_record = self.env['call.price'].search([('email', '=', 'jane.smith@example.com')])
        
        self.assertTrue(created_record, 'Record should be created by create_form')
        self.assertEqual(created_record.first_name, 'Jane')
        self.assertEqual(created_record.last_name, 'Smith')
        self.assertEqual(created_record.product_id.id, self.product_template.id)
        self.assertEqual(created_record.phone, '0987654321')
        self.assertEqual(created_record.message, 'Another test message')
        self.assertEqual(created_record.quantity, 10)
