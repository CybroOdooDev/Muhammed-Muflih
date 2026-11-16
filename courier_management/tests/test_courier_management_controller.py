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
from odoo.tests.common import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestCourierManagementController(HttpCase):
    """Test Courier Management Controller"""

    def setUp(self):
        super().setUp()
        # Use a plain internal user — courier routes use auth="user",
        # so any authenticated user can exercise the route logic.
        self.test_user = self.env['res.users'].create({
            'name': 'Courier Test User',
            'login': 'courier_test_user',
            'password': 'courier_test_pass',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.partner = self.test_user.partner_id
        
        self.category = self.env['courier.category'].create({
            'courier_category': 'Controller Category',
        })
        self.courier_type = self.env['courier.type'].create({
            'courier_type': 'Controller Type',
        })
        self.dimension = self.env['courier.dimension.price'].create({
            'name': 'Controller Dimension',
            'length': 10,
            'width': 10,
            'height': 10,
            'price': 15.0,
        })
        
        self.request = self.env['courier.request'].create({
            'sender_id': self.partner.id,
            'receiver_id': self.env.user.partner_id.id,
            'category_id': self.category.id,
            'type_id': self.courier_type.id,
            'l_w_h_id': self.dimension.id,
            'total_kilometres': 10.0,
            'delivery_date': '2030-01-01',
        })

    def test_get_my_courier_requests(self):
        """Test my courier requests list route."""
        self.authenticate('courier_test_user', 'courier_test_pass')
        response = self.url_open('/my/courier/requests')
        self.assertEqual(response.status_code, 200)

    def test_get_my_courier_request_form(self):
        """Test courier request form route."""
        self.authenticate('courier_test_user', 'courier_test_pass')
        response = self.url_open(f'/my/courier/requests/form/{self.request.id}')
        self.assertEqual(response.status_code, 200)

    def test_courier_requests_group_by(self):
        """Test group by JSON route."""
        self.authenticate('courier_test_user', 'courier_test_pass')
        response = self.url_open(
            '/courier/requests/group/by',
            data='{"jsonrpc": "2.0", "method": "call", "params": {"search_value": "1"}, "id": 1}',
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        
        response2 = self.url_open(
            '/courier/requests/group/by',
            data='{"jsonrpc": "2.0", "method": "call", "params": {"search_value": "2"}, "id": 2}',
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response2.status_code, 200)

    def test_courier_requests_search(self):
        """Test search JSON route."""
        self.authenticate('courier_test_user', 'courier_test_pass')
        response = self.url_open(
            '/courier/requests/search',
            data=f'{{"jsonrpc": "2.0", "method": "call", "params": {{"search_value": "{self.request.name}"}}, "id": 1}}',
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
