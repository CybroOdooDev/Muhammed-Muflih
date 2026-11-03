# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAgeRestrictedProductPos(TransactionCase):
    """Test suite for age restricted products in Point of Sale."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Age Restrict POS',
        })

        cls.product_tmpl_restricted = cls.env['product.template'].create({
            'name': 'Restricted Product',
            'available_in_pos': True,
            'is_age_restrict': True,
        })

        cls.product_tmpl_unrestricted = cls.env['product.template'].create({
            'name': 'Standard Product',
            'available_in_pos': True,
            'is_age_restrict': False,
        })

    def test_01_default_values(self):
        """Test default value of is_age_restrict on product template and variant."""
        tmpl = self.env['product.template'].create({
            'name': 'Default Product',
            'available_in_pos': True,
        })
        self.assertFalse(tmpl.is_age_restrict, "Template is_age_restrict should default to False.")
        self.assertFalse(
            tmpl.product_variant_id.is_age_restrict,
            "Variant is_age_restrict should default to False.",
        )

    def test_02_restricted_template_and_variant_sync(self):
        """Test is_age_restrict value propagates from template to variant."""
        self.assertTrue(
            self.product_tmpl_restricted.is_age_restrict,
            "Template should have is_age_restrict set to True.",
        )
        self.assertTrue(
            self.product_tmpl_restricted.product_variant_id.is_age_restrict,
            "Variant should reflect is_age_restrict as True.",
        )

        # Toggle restriction off on template
        self.product_tmpl_restricted.write({'is_age_restrict': False})
        self.assertFalse(
            self.product_tmpl_restricted.is_age_restrict,
            "Template should have is_age_restrict updated to False.",
        )
        self.assertFalse(
            self.product_tmpl_restricted.product_variant_id.is_age_restrict,
            "Variant should reflect updated is_age_restrict as False.",
        )

    def test_03_variant_write_syncs_to_template(self):
        """Test updating is_age_restrict directly on variant writes back to template."""
        variant = self.product_tmpl_unrestricted.product_variant_id
        self.assertFalse(variant.is_age_restrict)
        self.assertFalse(self.product_tmpl_unrestricted.is_age_restrict)

        variant.write({'is_age_restrict': True})
        self.assertTrue(
            self.product_tmpl_unrestricted.is_age_restrict,
            "Template should update when is_age_restrict is set on variant.",
        )
        self.assertTrue(
            variant.is_age_restrict,
            "Variant should remain True after writing is_age_restrict.",
        )

    def test_04_load_pos_data_fields(self):
        """Test that _load_pos_data_fields on product.product appends is_age_restrict."""
        pos_fields = self.env['product.product']._load_pos_data_fields(self.pos_config.id)
        self.assertIn(
            'is_age_restrict',
            pos_fields,
            "'is_age_restrict' must be included in product.product pos data fields.",
        )

    def test_05_multi_recordset_operations(self):
        """Test multi-recordset reads and batch writes for is_age_restrict."""
        tmpls = self.env['product.template'].create([
            {'name': 'Batch Product 1', 'is_age_restrict': False},
            {'name': 'Batch Product 2', 'is_age_restrict': False},
            {'name': 'Batch Product 3', 'is_age_restrict': True},
        ])
        variants = tmpls.mapped('product_variant_id')

        # Batch update
        tmpls.write({'is_age_restrict': True})
        self.assertTrue(
            all(tmpls.mapped('is_age_restrict')),
            "All templates in batch should have is_age_restrict set to True.",
        )
        self.assertTrue(
            all(variants.mapped('is_age_restrict')),
            "All variants in batch should have is_age_restrict set to True.",
        )
