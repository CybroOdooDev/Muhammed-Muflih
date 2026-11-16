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
class TestCourierDimensionPrice(TransactionCase):
    """Test Courier Dimension Price Rule"""

    def test_dimension_validation(self):
        """Test validations on length, width, and height."""
        # Test zero or negative dimensions
        invalid_combinations = [
            (0, 10, 10),
            (10, -5, 10),
            (10, 10, 0),
        ]

        for length, width, height in invalid_combinations:
            with self.assertRaises(ValidationError):
                self.env['courier.dimension.price'].create({
                    'name': f'Invalid Dimension Rule {length}x{width}x{height}',
                    'length': length,
                    'width': width,
                    'height': height,
                    'price': 20.0,
                })

    def test_volumetric_weight_computation(self):
        """Test compute volumetric weight."""
        rule = self.env['courier.dimension.price'].create({
            'name': 'Valid Dimension Rule',
            'length': 100,
            'width': 50,
            'height': 50,
            'price': 100.0,
        })
        # (100 * 50 * 50) / 5000 = 250000 / 5000 = 50.0
        self.assertEqual(rule.volumetric_weight, 50.0, "Volumetric weight should be correctly computed")
