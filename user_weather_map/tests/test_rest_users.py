# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################


from unittest.mock import patch, Mock

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError




class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


    @patch("requests.get")
    def test_check_city_valid(self, mock_get):
        """Test valid city validation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'cod': 200,
            'name': 'London'
        }
        mock_get.return_value = mock_response

        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_valid_user',
            'api_key': 'test_api_key',
            'city': 'London',
        })

        user._check_city()


    @patch("requests.get")
    def test_check_city_invalid(self, mock_get):
        """Test invalid city validation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'cod': '404',
            'message': 'city not found'
        }
        mock_get.return_value = mock_response



        with self.assertRaises(ValidationError) as error:
            user = self.env['res.users'].create({
                'name': 'Test User',
                'login': 'test_invalid_user',
                'api_key': 'test_api_key',
                'city': 'InvalidCity',
            })
            user._check_city()

        self.assertEqual(str(error.exception), 'city not found')


    def test_check_city_without_api_key(self):
        """Test city validation when API key is not set"""

        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_no_api_key',
            'city': 'London',
        })

        user._check_city()
