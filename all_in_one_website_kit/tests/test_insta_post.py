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
from odoo.exceptions import UserError
from unittest.mock import patch





class TestInstaPost(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.insta_post = self.env['insta.post'].create({
            'name': '1234567890',
            'caption': 'Original Caption',
        })

    def test_01_create_post(self):
        """Test insta post creation"""

        self.assertEqual(
            self.insta_post.name,
            '1234567890'
        )

        self.assertEqual(
            self.insta_post.caption,
            'Original Caption'
        )

    @patch(
        'odoo.addons.all_in_one_website_kit.models.insta_post.requests.get'
    )
    def test_02_action_update_post_basic_api(self, mock_get):
        """Test IGAA token"""

        mock_get.return_value.json.return_value = {
            'caption': 'Updated Caption via Basic API'
        }

        self.insta_post.action_update_post(
            'IGAA_test_token'
        )

        self.assertEqual(
            self.insta_post.caption,
            'Updated Caption via Basic API'
        )

        mock_get.assert_called_once()

    @patch(
        'odoo.addons.all_in_one_website_kit.models.insta_post.requests.get'
    )
    def test_03_action_update_post_graph_api(self, mock_get):
        """Test Graph API"""

        mock_get.return_value.json.return_value = {
            'caption': 'Updated Caption via Graph API'
        }

        self.insta_post.action_update_post(
            'EAAG_test_token'
        )

        self.assertEqual(
            self.insta_post.caption,
            'Updated Caption via Graph API'
        )

        mock_get.assert_called_once()

    @patch(
        'odoo.addons.all_in_one_website_kit.models.insta_post.requests.get'
    )
    def test_04_action_update_post_error(self, mock_get):
        """Test API error handling"""

        mock_get.return_value.json.return_value = {
            'error': {
                'message': 'Invalid OAuth access token.'
            }
        }

        with self.assertRaises(UserError):
            self.insta_post.action_update_post(
                'invalid_token'
            )