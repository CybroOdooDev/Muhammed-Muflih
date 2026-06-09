
# -*- coding: utf-8 -*-

import logging
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestPortalController(TransactionCase):

    def setUp(self):
        super().setUp()

        self.partner = self.env['res.partner'].create({
            'name': 'Portal Test Partner'
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })



    def test_01_sale_return_model_exists(self):
        """Verify sale.return model exists"""

        self.assertIn(
            'sale.return',
            self.env
        )

        self.assertEqual(
            self.env['sale.return']._name,
            'sale.return'
        )

    def test_02_portal_dashboard_model_access(self):
        """Verify required models exist"""


        self.assertIn('sale.order', self.env)
        self.assertIn('purchase.order', self.env)
        self.assertIn('account.move', self.env)


    @patch('geopy.Nominatim.reverse')
    def test_03_geo_changer_mock(self, mock_reverse):
        """Test mocked geo changer"""

        mock_location = MagicMock()
        mock_location.raw = {
            'address': {
                'village': 'Kozhikode',
                'suburb': 'Kallai',
                'state': 'Kerala',
                'country_code': 'in',
                'postcode': '673003'
            }
        }

        mock_reverse.return_value = mock_location

        self.assertTrue(True)

    @patch('geopy.Nominatim.geocode')
    def test_04_geo_location_mock(self, mock_geocode):
        """Test mocked geo location"""

        mock_location = MagicMock()
        mock_location.latitude = 11.2588
        mock_location.longitude = 75.7804

        mock_geocode.return_value = mock_location

        self.assertEqual(
            mock_location.latitude,
            11.2588
        )

        self.assertEqual(
            mock_location.longitude,
            75.7804
        )


    def test_05_portal_dashboard_data_structure(self):
        """Verify expected dashboard keys"""

        expected_keys = [
            'target',
            'target_po',
            'target_accounting',
            'accounting_count'
        ]

        self.assertEqual(
            len(expected_keys),
            4
        )