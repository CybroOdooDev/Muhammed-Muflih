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

from odoo.tests.common import TransactionCase



class TestWebsiteFields(TransactionCase):
    """Test Website inherited fields"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()



        cls.website = cls.env['website'].create({
            'name': 'Test Website',
        })


    def test_custom_fields_exist(self):
        """Verify custom fields exist"""


        website_fields = self.env['website']._fields

        self.assertIn('mobile_number', website_fields)
        self.assertIn('company', website_fields)
        self.assertIn('address', website_fields)
        self.assertIn('phone', website_fields)
        self.assertIn('mobile', website_fields)
        self.assertIn('email', website_fields)
        self.assertIn('website', website_fields)
        self.assertIn('vat', website_fields)
        self.assertIn('address_in_online', website_fields)
        self.assertIn('hide_marker_icons', website_fields)
        self.assertIn('show_phone_icon', website_fields)
        self.assertIn('country_flag', website_fields)
        self.assertIn('facebook', website_fields)
        self.assertIn('twitter', website_fields)
        self.assertIn('linked_in', website_fields)
        self.assertIn('instagram', website_fields)
        self.assertIn('git_hub', website_fields)

    def test_default_boolean_values(self):
        """Verify default boolean values"""

        self.assertFalse(self.website.company)
        self.assertFalse(self.website.address)
        self.assertFalse(self.website.phone)
        self.assertFalse(self.website.mobile)
        self.assertFalse(self.website.email)
        self.assertFalse(self.website.website)
        self.assertFalse(self.website.vat)
        self.assertFalse(self.website.address_in_online)
        self.assertFalse(self.website.hide_marker_icons)
        self.assertFalse(self.website.show_phone_icon)
        self.assertFalse(self.website.country_flag)
        self.assertFalse(self.website.facebook)
        self.assertFalse(self.website.twitter)
        self.assertFalse(self.website.linked_in)
        self.assertFalse(self.website.instagram)
        self.assertFalse(self.website.git_hub)

    def test_mobile_number_write(self):
        """Verify mobile number write"""

        self.website.write({
            'mobile_number': '+919999999999'
        })

        self.assertEqual(
            self.website.mobile_number,
            '+919999999999'
        )


    def test_boolean_field_write(self):
        """Verify boolean fields can be updated"""


        self.website.write({
            'company': True,
            'address': True,
            'phone': True,
            'mobile': True,
            'email': True,
            'website': True,
            'vat': True,
            'facebook': True,
            'twitter': True,
            'linked_in': True,
            'instagram': True,
            'git_hub': True,
        })

        self.assertTrue(self.website.company)
        self.assertTrue(self.website.address)
        self.assertTrue(self.website.phone)
        self.assertTrue(self.website.mobile)
        self.assertTrue(self.website.email)
        self.assertTrue(self.website.website)
        self.assertTrue(self.website.vat)
        self.assertTrue(self.website.facebook)
        self.assertTrue(self.website.twitter)
        self.assertTrue(self.website.linked_in)
        self.assertTrue(self.website.instagram)
        self.assertTrue(self.website.git_hub)


    def test_related_social_fields(self):
        """Verify related social media fields"""

        self.website.company_id.write({
            'social_facebook': 'facebook_test',
            'social_twitter': 'twitter_test',
            'social_linkedin': 'linkedin_test',
            'social_instagram': 'instagram_test',
            'social_github': 'github_test',
        })

        self.assertEqual(
            self.website.social_facebook,
            'facebook_test'
        )

        self.assertEqual(
            self.website.social_twitter,
            'twitter_test'
        )

        self.assertEqual(
            self.website.social_linked_in,
            'linkedin_test'
        )

        self.assertEqual(
            self.website.social_instagram,
            'instagram_test'
        )

        self.assertEqual(
            self.website.social_git_hub,
            'github_test'
        )


    def test_country_flag_field(self):
        """Verify country flag field"""

        self.website.write({
            'country_flag': True
        })

        self.assertTrue(self.website.country_flag)
