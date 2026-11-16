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
from datetime import timedelta
from odoo.fields import Date

@tagged('post_install', '-at_install')
class TestCourierRequest(TransactionCase):
    """Test Courier Request logic"""

    def setUp(self):
        super().setUp()
        self.env['courier.category'].search([]).unlink()
        self.env['courier.type'].search([]).unlink()
        self.env['courier.priority'].search([]).unlink()
        self.env['courier.dimension.price'].search([]).unlink()
        self.env['courier.distance.price'].search([]).unlink()
        
        self.partner_sender = self.env['res.partner'].create({
            'name': 'Test Sender',
            'phone': '1234567890',
            'email': 'sender@test.com',
        })
        self.partner_receiver = self.env['res.partner'].create({
            'name': 'Test Receiver',
            'phone': '0987654321',
            'email': 'receiver@test.com',
        })
        self.category = self.env['courier.category'].create({
            'courier_category': 'Test Category',
        })
        self.courier_type = self.env['courier.type'].create({
            'courier_type': 'Test Type',
        })
        self.priority = self.env['courier.priority'].create({
            'name': 'High Priority',
            'charges': 50.0,
        })
        self.dimension = self.env['courier.dimension.price'].create({
            'name': 'Test Dimension',
            'length': 10,
            'width': 10,
            'height': 10,
            'price': 15.0,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Courier Product',
            'weight': 1.0,
        })

        self.request_vals = {
            'sender_id': self.partner_sender.id,
            'receiver_id': self.partner_receiver.id,
            'category_id': self.category.id,
            'type_id': self.courier_type.id,
            'priority_id': self.priority.id,
            'l_w_h_id': self.dimension.id,
            'total_kilometres': 10.0,
            'delivery_date': Date.context_today(self.env.user) + timedelta(days=5),
        }

    def test_courier_request_create_and_sequence(self):
        """Test sequence generation on create."""
        req = self.env['courier.request'].create(self.request_vals)
        self.assertNotEqual(req.name, 'New')
        self.assertTrue(req.name)

    def test_action_state_transitions(self):
        """Test courier request state transitions."""
        req = self.env['courier.request'].create(self.request_vals)
        
        # Action collected without details should raise ValidationError
        with self.assertRaises(ValidationError):
            req.action_collected()

        # Add details
        self.env['courier.detail'].create({
            'courier_requests_id': req.id,
            'product_id': self.product.id,
            'quantity': 1,
        })

        req.action_collected()
        self.assertEqual(req.state, 'collected')

        req.action_dispatched()
        self.assertEqual(req.state, 'dispatched')

        req.action_in_transit()
        self.assertEqual(req.state, 'in_transit')

        req.action_arrived_at_destination()
        self.assertEqual(req.state, 'arrived_at_destination')

        req.action_out_for_delivery()
        self.assertEqual(req.state, 'out_for_delivery')

        req.action_delivered()
        self.assertEqual(req.state, 'delivered')

        req.action_cancelled()
        self.assertEqual(req.state, 'cancelled')

    def test_onchange_validations(self):
        """Test onchange validation for delivery date and total kilometres."""
        req = self.env['courier.request'].create(self.request_vals)

        # Invalid delivery date
        req.delivery_date = Date.context_today(self.env.user) - timedelta(days=1)
        with self.assertRaises(ValidationError):
            req._onchange_delivery_date()

        # Invalid total_kilometres
        req.total_kilometres = 0.5
        with self.assertRaises(ValidationError):
            req._onchange_total_kilometres()

    def test_computations(self):
        """Test total calculations, distance amount, priority amount."""
        self.env['courier.distance.price'].create({
            'name': 'Test Distance',
            'minimum_distance': 1.0,
            'maximum_distance': 20.0,
            'price': 100.0,
        })

        req = self.env['courier.request'].create(self.request_vals)
        
        # Test distance amount compute
        req._compute_distance_amount()
        self.assertEqual(req.distance_amount, 100.0)

        # Test priority amount
        self.assertEqual(req.priority_amount, 50.0)

        # Test volumetric weight price
        self.assertEqual(req.volumetric_weight_price, 15.0)

        # Directly set total_courier_charges and verify _compute_total
        req.write({'total_courier_charges': 20.0})
        self.assertEqual(req.total_courier_charges, 20.0)

        req._compute_total()
        # 100 (dist) + 50 (prio) + 15 (vol) + 20 (charge) = 185.0
        self.assertEqual(req.total, 185.0)

        # Test _onchange_courier_details_ids by creating a real line and invoking it
        self.env['courier.detail'].create({
            'courier_requests_id': req.id,
            'product_id': self.product.id,
            'quantity': 1,
        })
        req._onchange_courier_details_ids()
        # After onchange, total_courier_charges reflects sum of sub_totals
        self.assertEqual(
            req.total_courier_charges,
            sum(req.courier_details_ids.mapped('sub_total'))
        )

    def test_action_create_and_view_invoice(self):
        """Test invoice creation."""
        xml_ids = [
            ('courier_management.volumetric_weight_charges_product', 'Volumetric Charges'),
            ('courier_management.additional_charges_priority_product', 'Priority Charges'),
            ('courier_management.distance_charges_product', 'Distance Charges'),
        ]
        for xml_id, name in xml_ids:
            if not self.env.ref(xml_id, raise_if_not_found=False):
                prod = self.env['product.product'].create({'name': name})
                self.env['ir.model.data'].create({
                    'name': xml_id.split('.')[1],
                    'module': 'courier_management',
                    'model': 'product.product',
                    'res_id': prod.id,
                })

        req = self.env['courier.request'].create(self.request_vals)

        self.env['courier.detail'].create({
            'courier_requests_id': req.id,
            'product_id': self.product.id,
            'quantity': 1,
        })

        req.action_create_invoice()
        self.assertEqual(req.state, 'invoiced')
        self.assertEqual(req.invoice_count, 1)

        action = req.action_view_invoices()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['domain'], [('courier_ref_id', '=', req.id)])
