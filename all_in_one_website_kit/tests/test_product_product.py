
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


class TestProductProduct(common.TransactionCase):
    def setUp(self):
        super(TestProductProduct, self).setUp()
        
        # Create a product template
        self.product_template = self.env['product.template'].create({
            'name': 'Test Variant Template',
            'list_price': 150.0,
        })
        
        # Get the automatically created product variant
        self.product_variant = self.product_template.product_variant_id

    def test_01_website_hide_variants_field(self):
        """Test website_hide_variants field on product.product"""
        
        # By default, the boolean field should be False
        self.assertFalse(self.product_variant.website_hide_variants, 'website_hide_variants should be False by default')
        
        # Write to the field
        self.product_variant.write({'website_hide_variants': True})
        
        # Verify the value was updated
        self.assertTrue(self.product_variant.website_hide_variants, 'website_hide_variants should be True after update')
