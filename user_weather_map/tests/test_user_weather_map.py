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

import json
from unittest.mock import Mock, patch
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWeatherNotification(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @patch('odoo.addons.user_weather_map.controllers.user_weather_map.requests.get')
    @patch('odoo.addons.user_weather_map.controllers.user_weather_map.geocoder.ip')
    def test_weather_notification_auto_location(
            self, mock_geocoder, mock_requests):
        """Test weather notification with auto location"""
        user = self.env.user
        user.write({
            'api_key': 'test_api_key',
            'location_set': 'auto',
        })

        mock_geo = Mock()
        mock_geo.status_code = 200
        mock_geo.latlng = [10.52, 76.21]
        mock_geocoder.return_value = mock_geo

        mock_weather = Mock()
        mock_weather.status_code = 200
        mock_weather.json.return_value = {
            'name': 'Kochi',
            'main': {'temp': 300}
        }
        mock_requests.return_value = mock_weather

        response = self.url_open(
            '/weather/notification/check',
            data=json.dumps({}),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)


    @patch('odoo.addons.user_weather_map.models.res_users.requests.get')
    @patch('odoo.addons.user_weather_map.controllers.user_weather_map.requests.get')
    def test_weather_notification_manual_location(self, mock_requests, mock_model_requests):
        """Test weather notification with manual location"""

        mock_model_weather = Mock()
        mock_model_weather.json.return_value = {
            'cod': 200,
            'name': 'London'
        }
        mock_model_requests.return_value = mock_model_weather

        user = self.env.user
        user.write({
            'api_key': 'test_api_key',
            'location_set': 'manual',
            'city': 'London',
        })

        mock_weather = Mock()
        mock_weather.status_code = 200
        mock_weather.json.return_value = {
            'name': 'London',
            'main': {'temp': 290}
        }
        mock_requests.return_value = mock_weather

        response = self.url_open(
            '/weather/notification/check',
            data=json.dumps({}),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)

    def test_weather_notification_without_api_key(self):
        """Test weather notification without API key"""

        user = self.env.user
        user.write({
            'api_key': False,
        })

        response = self.url_open(
            '/weather/notification/check',
            data=json.dumps({}),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
