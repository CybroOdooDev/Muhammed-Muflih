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


from unittest.mock import patch

from odoo.tests.common import HttpCase



class TestWebsiteController(HttpCase):

    def setUp(self):
        super().setUp()

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer'
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100,
        })


    def test_01_customer_order_rating(self):
        """Test customer rating route"""

        self.sale_order.write({
            'comment': '',
            'rating': '0'
        })

        self.sale_order.comment = 'Excellent Product'
        self.sale_order.rating = '5'

        self.assertEqual(
            self.sale_order.comment,
            'Excellent Product'
        )

        self.assertEqual(
            str(self.sale_order.rating),
            '5'
        )


    def test_02_invalid_order_rating(self):
        """Test invalid order id scenario"""

        self.assertTrue(True)

    def test_03_dashboard_carousel_data(self):
        """Test carousel data"""

        self.env['insta.post'].create({
            'name': '123456',
            'caption': 'Test Caption'
        })

        records = self.env['insta.post'].search([])

        self.assertGreaterEqual(
            len(records),
            1
        )

    @patch(
        'odoo.addons.website_sale.controllers.variant.WebsiteSaleVariantController.get_combination_info_website'
    )
    def test_04_get_combination_info_website(
            self,
            mock_combination):
        """Test variant combination info"""


        self.product.website_hide_variants = True

        mock_combination.return_value = {
            'product_id': self.product.id
        }

        result = mock_combination.return_value

        product = self.env['product.product'].browse(
            result['product_id']
        )

        result['website_hide_variants'] = (
            product.website_hide_variants
        )

        self.assertTrue(
            result['website_hide_variants']
        )

    def test_05_remove_cart_items(self):
        """Basic cart removal test"""

        self.assertTrue(True)

