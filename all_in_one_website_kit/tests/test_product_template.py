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


class TestProductTemplate(common.TransactionCase):
    def setUp(self):
        super(TestProductTemplate, self).setUp()
        
        # Create a product attribute and values to generate multiple variants
        self.attribute = self.env['product.attribute'].create({
            'name': 'Test Color',
            'create_variant': 'always',
        })
        self.attr_val_red = self.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': self.attribute.id,
        })
        self.attr_val_blue = self.env['product.attribute.value'].create({
            'name': 'Blue',
            'attribute_id': self.attribute.id,
        })
        
        # Create a product template with variants
        self.product_template = self.env['product.template'].create({
            'name': 'Test Template with Variants',
            'list_price': 100.0,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': self.attribute.id,
                'value_ids': [(6, 0, [self.attr_val_red.id, self.attr_val_blue.id])],
            })]
        })
        
        # The template should now have 2 variants
        self.variants = self.product_template.product_variant_ids

    def test_01_price_call_field(self):
        """Test the simple boolean field price_call"""
        
        self.assertFalse(self.product_template.price_call, 'price_call should be False by default')
        self.product_template.write({'price_call': True})
        self.assertTrue(self.product_template.price_call, 'price_call should be True after update')

    def test_02_inverse_website_hide_variants(self):
        """Test that writing to template's website_hide_variants propagates to all variants"""
        
        self.assertEqual(len(self.variants), 2, 'Should have exactly 2 variants')
        
        # Initial state should be False on all
        self.assertFalse(self.product_template.website_hide_variants)
        for variant in self.variants:
            self.assertFalse(variant.website_hide_variants)
            
        # Write True to template
        self.product_template.write({'website_hide_variants': True})
        
        # Verify it propagates to variants (inverse method)
        for variant in self.variants:
            self.assertTrue(variant.website_hide_variants, 'Variant should be hidden because template is hidden')

    def test_03_compute_website_hide_variants(self):
        """Test that website_hide_variants is computed correctly from variants"""
        
        # Hide the first variant
        self.variants[0].write({'website_hide_variants': True})
        
        # Template should still be False because not ALL variants are hidden
        self.assertFalse(self.product_template.website_hide_variants, 'Template should not be hidden if only some variants are')
        
        # Hide the second variant
        self.variants[1].write({'website_hide_variants': True})
        
        # Now template should be True because ALL variants are hidden
        self.assertTrue(self.product_template.website_hide_variants, 'Template should be hidden if all variants are hidden')
