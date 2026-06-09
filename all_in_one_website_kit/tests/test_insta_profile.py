
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
from unittest.mock import patch, MagicMock


class TestInstaProfile(common.TransactionCase):
    def setUp(self):
        super(TestInstaProfile, self).setUp()
        
        self.profile_basic = self.env['insta.profile'].create({
            'access_token': 'IGAA_test_token'
        })
        
        self.profile_graph = self.env['insta.profile'].create({
            'access_token': 'EAAG_test_token'
        })

    @patch('odoo.addons.all_in_one_website_kit.models.insta_profile.requests.get')
    def test_01_action_fetch_basic(self, mock_get):
        """Test action_fetch with basic display API (IGAA token)"""
        
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            'id': '12345',
            'username': 'basic_user'
        }
        
        self.profile_basic.action_fetch()
        
        self.assertEqual(self.profile_basic.username, 'basic_user')
        self.assertEqual(self.profile_basic.account_id, '12345')
        self.assertEqual(self.profile_basic.name, 'basic_user')
        
        mock_get.assert_called_once()
        self.assertIn('graph.instagram.com', mock_get.call_args[0][0])

    @patch('odoo.addons.all_in_one_website_kit.models.insta_profile.requests.get')
    def test_02_action_fetch_graph(self, mock_get):
        """Test action_fetch with graph API"""
        
        # We need to mock multiple requests for graph API fetch
        def side_effect(*args, **kwargs):
            mock = MagicMock()
            url = args[0]
            if 'me/accounts' in url:
                mock.json.return_value = {'data': [{'id': 'page_id_123'}]}
            elif 'instagram_business_account' in url:
                mock.json.return_value = {'instagram_business_account': {'id': 'insta_acc_123'}}
            elif 'fields=name,username' in url:
                mock.json.return_value = {
                    'name': 'Business Name',
                    'username': 'business_user',
                    'id': 'acc_123',
                    'profile_picture_url': 'http://example.com/pic.jpg'
                }
            elif 'example.com' in url:
                mock.content = b'image_data'
            return mock
            
        mock_get.side_effect = side_effect
        
        self.profile_graph.action_fetch()
        
        self.assertEqual(self.profile_graph.name, 'Business Name')
        self.assertEqual(self.profile_graph.username, 'business_user')
        self.assertEqual(self.profile_graph.account_id, 'acc_123')
        self.assertTrue(self.profile_graph.profile_image_url)

    @patch('odoo.addons.all_in_one_website_kit.models.insta_profile.requests.get')
    def test_03_action_fetch_error(self, mock_get):
        """Test action_fetch handling errors"""
        
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            'error': {'message': 'Invalid token'}
        }
        
        with self.assertRaises(UserError) as e:
            self.profile_basic.action_fetch()
            
        self.assertIn('Invalid token', str(e.exception))

    @patch('odoo.addons.all_in_one_website_kit.models.insta_profile.requests.get')
    def test_04_action_get_post_basic(self, mock_get):
        """Test action_get_post with basic API"""
        
        def side_effect(*args, **kwargs):
            mock = MagicMock()
            url = args[0]
            if 'graph.instagram.com/me/media' in url:
                mock.json.return_value = {
                    'data': [{
                        'id': 'post_1',
                        'caption': 'Basic post caption',
                        'media_type': 'IMAGE',
                        'media_url': 'http://example.com/post.jpg'
                    }]
                }
            elif 'example.com' in url:
                mock.content = b'post_image_data'
            return mock
            
        mock_get.side_effect = side_effect
        
        self.profile_basic.action_get_post()
        
        post = self.env['insta.post'].search([('name', '=', 'post_1')])
        self.assertTrue(post)
        self.assertEqual(post.caption, 'Basic post caption')
        self.assertEqual(post.profile_id, self.profile_basic)

    @patch('odoo.addons.all_in_one_website_kit.models.insta_profile.requests.get')
    def test_05_action_get_post_graph(self, mock_get):
        """Test action_get_post with graph API"""
        
        # Ensure account_id is set
        self.profile_graph.account_id = 'acc_123'
        
        def side_effect(*args, **kwargs):
            mock = MagicMock()
            url = args[0]
            if '/media?access_token' in url:
                mock.json.return_value = {
                    'data': [{'id': 'post_2'}]
                }
            elif '?fields=id,caption' in url:
                mock.json.return_value = {
                    'id': 'post_2',
                    'caption': 'Graph post caption',
                    'media_type': 'IMAGE',
                    'media_url': 'http://example.com/post2.jpg'
                }
            elif 'example.com' in url:
                mock.content = b'post_image_data'
            return mock
            
        mock_get.side_effect = side_effect
        
        self.profile_graph.action_get_post()
        
        post = self.env['insta.post'].search([('name', '=', 'post_2')])
        self.assertTrue(post)
        self.assertEqual(post.caption, 'Graph post caption')
        self.assertEqual(post.profile_id, self.profile_graph)

    @patch('odoo.addons.all_in_one_website_kit.models.insta_profile.requests.get')
    def test_06_action_get_post_error(self, mock_get):
        """Test action_get_post handling errors"""
        
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            'error': {'message': 'Failed to fetch posts'}
        }
        
        with self.assertRaises(UserError) as e:
            self.profile_basic.action_get_post()
            
        self.assertIn('Failed to fetch posts', str(e.exception))
