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
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestCourierWeightPrice(TransactionCase):
    """Test Courier Weight Price Rule"""

    def test_weight_validation(self):
        """Test validations on minimum and maximum weight."""
        # Test zero or negative weight
        with self.assertRaises(ValidationError):
            self.env['courier.weight.price'].create({
                'name': 'Invalid Weight Rule 1',
                'minimum_weight': 0.0,
                'maximum_weight': 10.0,
                'price': 100.0,
            })
            
        with self.assertRaises(ValidationError):
            self.env['courier.weight.price'].create({
                'name': 'Invalid Weight Rule 2',
                'minimum_weight': 10.0,
                'maximum_weight': -5.0,
                'price': 100.0,
            })

        # Test minimum > maximum
        with self.assertRaises(ValidationError):
            self.env['courier.weight.price'].create({
                'name': 'Invalid Weight Rule 3',
                'minimum_weight': 20.0,
                'maximum_weight': 10.0,
                'price': 100.0,
            })

        # Test valid creation
        rule = self.env['courier.weight.price'].create({
            'name': 'Valid Weight Rule',
            'minimum_weight': 5.0,
            'maximum_weight': 15.0,
            'price': 50.0,
        })
        self.assertTrue(rule.id, "Valid weight rule should be created successfully")
