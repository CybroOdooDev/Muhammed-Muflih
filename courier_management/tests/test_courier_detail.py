# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestCourierDetail(TransactionCase):
    """Test Courier Detail logic"""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Courier Product',
            'weight': 2.0,
        })
        
        # Clear existing rules to avoid test conflicts
        self.env['courier.weight.price'].search([]).unlink()
        
        # Create some weight rules
        self.rule_1 = self.env['courier.weight.price'].create({
            'name': 'Rule 1',
            'minimum_weight': 1.0,
            'maximum_weight': 5.0,
            'price': 10.0,
        })
        self.rule_2 = self.env['courier.weight.price'].create({
            'name': 'Rule 2',
            'minimum_weight': 5.1,
            'maximum_weight': 10.0,
            'price': 20.0,
        })

    def test_compute_total_weight_and_sub_total(self):
        """Test the computation of total weight, weight price, and subtotal."""
        # 1. Test weight within matching rule 1
        detail_1 = self.env['courier.detail'].create({
            'product_id': self.product.id,
            'quantity': 2,
        })
        # total_weight = 2 * 2.0 = 4.0
        # Matches Rule 1, price = 10.0
        self.assertEqual(detail_1.total_weight, 4.0)
        self.assertEqual(detail_1.weight_price, 10.0)
        self.assertEqual(detail_1.sub_total, 10.0)

        # 2. Test weight within matching rule 2
        detail_2 = self.env['courier.detail'].create({
            'product_id': self.product.id,
            'quantity': 4,
        })
        # total_weight = 4 * 2.0 = 8.0
        # Matches Rule 2, price = 20.0
        self.assertEqual(detail_2.total_weight, 8.0)
        self.assertEqual(detail_2.weight_price, 20.0)
        self.assertEqual(detail_2.sub_total, 20.0)

        # 3. Test weight < min rule
        self.product_small = self.env['product.product'].create({
            'name': 'Small Product',
            'weight': 0.5,
        })
        detail_3 = self.env['courier.detail'].create({
            'product_id': self.product_small.id,
            'quantity': 1,
        })
        # total_weight = 0.5 < min(1.0)
        # Should set to min(prices) = 10.0
        self.assertEqual(detail_3.total_weight, 0.5)
        self.assertEqual(detail_3.weight_price, 10.0)

        # 4. Test weight > max rule
        detail_4 = self.env['courier.detail'].create({
            'product_id': self.product.id,
            'quantity': 10,
        })
        # total_weight = 20.0 > max(10.0)
        # Should set to max(prices) = 20.0
        self.assertEqual(detail_4.total_weight, 20.0)
        self.assertEqual(detail_4.weight_price, 20.0)
