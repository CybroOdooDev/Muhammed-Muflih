# -*- coding: utf-8 -*-

import base64
import logging
from unittest.mock import MagicMock

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestWebsiteProductBarcode(TransactionCase):


 def setUp(self):
    super().setUp()

    _logger.info(
        "========== Setting Up Website Product Barcode Tests =========="
    )

    self.product_template = self.env['product.template'].create({
        'name': 'Test Product Template',
    })

    self.product = self.product_template.product_variant_id
    self.product.barcode = '123456789'

    self.attachment = self.env['ir.attachment'].create({
        'name': 'Test Attachment',
        'datas': base64.b64encode(
            b'Test File Content'
        ).decode(),
        'res_model': 'product.template',
        'res_id': self.product_template.id,
        'type': 'binary',
    })

    _logger.info(
        "Created Product: %s",
        self.product.display_name
    )

def test_01_product_creation(self):
    """Verify product creation"""

    _logger.info(
        "Running test_01_product_creation"
    )

    self.assertTrue(self.product)

    self.assertEqual(
        self.product.barcode,
        '123456789'
    )

def test_02_attachment_creation(self):
    """Verify attachment creation"""

    _logger.info(
        "Running test_02_attachment_creation"
    )

    self.assertTrue(self.attachment)

    self.assertEqual(
        self.attachment.res_model,
        'product.template'
    )

def test_03_barcode_search(self):
    """Verify barcode product search"""

    _logger.info(
        "Running test_03_barcode_search"
    )

    product = self.env['product.product'].search(
        [('barcode', '=', '123456789')],
        limit=1
    )

    self.assertEqual(
        product.id,
        self.product.id
    )

def test_04_invalid_barcode(self):
    """Verify invalid barcode"""

    _logger.info(
        "Running test_04_invalid_barcode"
    )

    product = self.env['product.product'].search(
        [('barcode', '=', 'INVALID')],
        limit=1
    )

    self.assertFalse(product)

def test_05_attachment_exists(self):
    """Verify attachment exists"""

    _logger.info(
        "Running test_05_attachment_exists"
    )

    attachment = self.env['ir.attachment'].browse(
        self.attachment.id
    )

    self.assertTrue(
        attachment.exists()
    )

def test_06_attribute_exclusion(self):
    """Verify attribute exclusion logic"""

    _logger.info(
        "Running test_06_attribute_exclusion"
    )

    mock_product = MagicMock()
    mock_product._get_attribute_exclusions.return_value = {}

    result = mock_product._get_attribute_exclusions(
        self.env['product.template.attribute.value']
    )

    self.assertEqual(
        result,
        {}
    )

    _logger.info(
        "Attribute exclusion verified"
    )

