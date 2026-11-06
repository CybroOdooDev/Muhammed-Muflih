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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Automated unit test suite for Sales All In One Report Generator."""
import io
import json
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


class MockResponse:
    """Mock HTTP response providing a stream buffer for XLSX export."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestSalesReport(TransactionCase):
    """Test suite for sales.report model and report generator features."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for sales report unit tests."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Report Customer',
            'email': 'customer@example.com',
        })
        cls.category = cls.env['product.category'].create({
            'name': 'Test Sales Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Report Product',
            'default_code': 'TRP-001',
            'categ_id': cls.category.id,
            'list_price': 100.0,
        })
        cls.now = fields.Datetime.now()
        cls.past_date = cls.now - timedelta(days=15)
        cls.future_date = cls.now + timedelta(days=15)

        # Sales orders in different states
        cls.order_draft = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.env.user.id,
            'company_id': cls.company.id,
            'date_order': cls.now,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })

        cls.order_confirmed = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.env.user.id,
            'company_id': cls.company.id,
            'date_order': cls.now,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 5.0,
                'price_unit': 100.0,
            })],
        })
        cls.order_confirmed.action_confirm()

        cls.order_sent = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.env.user.id,
            'company_id': cls.company.id,
            'date_order': cls.now,
            'state': 'sent',
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 3.0,
                'price_unit': 100.0,
            })],
        })

    def _create_report_wizard(self, report_type='report_by_order', date_from=None, date_to=None):
        """Helper to instantiate a sales.report wizard record."""
        return self.env['sales.report'].create({
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
        })

    def test_01_wizard_creation_and_defaults(self):
        """Verify default values and multi-recordset handling on sales.report."""
        wizard = self._create_report_wizard()
        self.assertEqual(wizard.report_type, 'report_by_order')
        self.assertFalse(wizard.date_from)
        self.assertFalse(wizard.date_to)

        # Multi-recordset verification
        wizard_2 = self._create_report_wizard(report_type='report_by_product')
        wizards = wizard | wizard_2
        self.assertEqual(len(wizards), 2)
        wizards.write({'date_from': self.past_date})
        self.assertTrue(all(w.date_from == self.past_date for w in wizards))

    def test_02_get_filter_all_report_types(self):
        """Verify get_filter mapping across all report types and date formatting."""
        wizard = self._create_report_wizard(
            report_type='report_by_order',
            date_from=self.past_date,
            date_to=self.future_date,
        )
        types_to_expected = {
            'report_by_order': 'Report By Order',
            'report_by_order_detail': 'Report By Order Detail',
            'report_by_product': 'Report By Product',
            'report_by_categories': 'Report By Categories',
            'report_by_salesperson': 'Report By Sales Person',
            'report_by_state': 'Report By State',
        }
        for rtype, expected_label in types_to_expected.items():
            wizard.report_type = rtype
            filters = wizard.get_filter([wizard.id], wizard.date_from, wizard.date_to)
            self.assertEqual(filters['report_type'], expected_label)
            self.assertEqual(filters['date_from'], self.past_date.strftime('%Y-%m-%d'))
            self.assertEqual(filters['date_to'], self.future_date.strftime('%Y-%m-%d'))

        # Fallback when report_type is False or unset
        wizard.report_type = False
        filters_fallback = wizard.get_filter([wizard.id], wizard.date_from, wizard.date_to)
        self.assertEqual(filters_fallback['report_type'], 'report_by_order')

        # When dates are not provided
        filters_no_date = wizard.get_filter([wizard.id], False, False)
        self.assertNotIn('date_from', filters_no_date)
        self.assertNotIn('date_to', filters_no_date)

    def test_03_get_filter_data(self):
        """Verify get_filter_data extracts report_type from wizard record."""
        wizard = self._create_report_wizard(report_type='report_by_salesperson')
        data = wizard.get_filter_data([wizard.id])
        self.assertEqual(data.get('report_type'), 'report_by_salesperson')

    def test_04_clean_translated_dict(self):
        """Verify _clean_translated_dict handles dictionary and string field values."""
        wizard = self._create_report_wizard()
        records = [
            {'product': {'en_US': 'Desk', 'fr_FR': 'Bureau'}, 'code': 'D01'},
            {'product': {'de_DE': 'Tisch'}, 'code': 'D02'},
            {'product': {}, 'code': 'D03'},
            {'product': 'Standard Product', 'code': 'D04'},
        ]
        cleaned = wizard._clean_translated_dict(records)
        self.assertEqual(cleaned[0]['product'], 'Desk')
        self.assertEqual(cleaned[1]['product'], 'Tisch')
        self.assertEqual(cleaned[2]['product'], '')
        self.assertEqual(cleaned[3]['product'], 'Standard Product')

    def test_05_client_action_report_by_order(self):
        """Verify sale_report returns proper client action data for report_by_order."""
        wizard = self._create_report_wizard(
            report_type='report_by_order',
            date_from=self.past_date,
            date_to=self.future_date,
        )
        res = wizard.sale_report([wizard.id])
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'sales_report')
        self.assertIn('orders', res)
        self.assertIn('filters', res)
        self.assertIn('report_lines', res)
        self.assertIn('report_main_line', res)
        self.assertIsInstance(res['report_lines'], list)
        self.assertGreaterEqual(len(res['report_lines']), 1)
        self.assertIsInstance(res['report_main_line'], list)
        self.assertGreaterEqual(len(res['report_main_line']), 1)
        self.assertIn('order', res['report_main_line'][0])
        self.assertIn('amount', res['report_main_line'][0])

    def test_06_client_action_report_by_order_detail(self):
        """Verify sale_report for report_by_order_detail."""
        wizard = self._create_report_wizard(report_type='report_by_order_detail')
        res = wizard.sale_report([wizard.id])
        self.assertEqual(res['orders']['report_type'], 'report_by_order_detail')
        self.assertIsInstance(res['report_lines'], list)
        if res['report_lines']:
            line = res['report_lines'][0]
            self.assertIn('customer', line)
            self.assertIn('salesman', line)
            self.assertIn('price_subtotal', line)
        self.assertIsInstance(res['report_main_line'], list)

    def test_07_client_action_report_by_product(self):
        """Verify sale_report for report_by_product."""
        wizard = self._create_report_wizard(report_type='report_by_product')
        res = wizard.sale_report([wizard.id])
        self.assertEqual(res['orders']['report_type'], 'report_by_product')
        self.assertIsInstance(res['report_lines'], list)
        if res['report_lines']:
            line = res['report_lines'][0]
            self.assertIn('product', line)
            self.assertIn('category', line)
        self.assertIsInstance(res['report_main_line'], list)

    def test_08_client_action_report_by_categories(self):
        """Verify sale_report for report_by_categories."""
        wizard = self._create_report_wizard(report_type='report_by_categories')
        res = wizard.sale_report([wizard.id])
        self.assertEqual(res['orders']['report_type'], 'report_by_categories')
        self.assertIsInstance(res['report_lines'], list)
        self.assertFalse(res['report_main_line'])

    def test_09_client_action_report_by_salesperson(self):
        """Verify sale_report for report_by_salesperson."""
        wizard = self._create_report_wizard(report_type='report_by_salesperson')
        res = wizard.sale_report([wizard.id])
        self.assertEqual(res['orders']['report_type'], 'report_by_salesperson')
        self.assertIsInstance(res['report_lines'], list)
        self.assertFalse(res['report_main_line'])

    def test_10_client_action_report_by_state(self):
        """Verify sale_report for report_by_state."""
        wizard = self._create_report_wizard(report_type='report_by_state')
        res = wizard.sale_report([wizard.id])
        self.assertEqual(res['orders']['report_type'], 'report_by_state')
        self.assertIsInstance(res['report_lines'], list)
        states_present = [r['state'] for r in res['report_lines']]
        self.assertTrue(any(s in ['draft', 'sale', 'sent'] for s in states_present))
        self.assertFalse(res['report_main_line'])

    def test_11_sub_lines_date_filter_permutations(self):
        """Verify _get_report_sub_lines with start date only, end date only, and both."""
        wizard = self._create_report_wizard()
        report_types = [
            'report_by_order',
            'report_by_order_detail',
            'report_by_product',
            'report_by_categories',
            'report_by_salesperson',
            'report_by_state',
        ]
        past_str = self.past_date.strftime('%Y-%m-%d %H:%M:%S')
        future_str = self.future_date.strftime('%Y-%m-%d %H:%M:%S')
        date_permutations = [
            {'date_from': past_str, 'date_to': False},
            {'date_from': False, 'date_to': future_str},
            {'date_from': past_str, 'date_to': future_str},
            {'date_from': False, 'date_to': False},
        ]
        for rtype in report_types:
            for dates in date_permutations:
                data = {
                    'report_type': rtype,
                    'date_from': dates['date_from'],
                    'date_to': dates['date_to'],
                }
                sublines = wizard._get_report_sub_lines(
                    data, [rtype], dates['date_from'], dates['date_to'],
                )
                self.assertIsInstance(sublines, list)
                self.assertEqual(len(sublines), 1)

    def test_12_get_report_values_edge_cases(self):
        """Verify _get_report_values without report_type and total value fallback."""
        wizard = self._create_report_wizard()
        data_no_type = {
            'model': wizard,
            'report_type': False,
        }
        res = wizard._get_report_values(data_no_type)
        self.assertIn('SALE', res)
        self.assertIn('sale_main', res)

        # Fallback on _get_report_total_value
        fallback_total = wizard._get_report_total_value({'report_type': 'unsupported'}, [])
        self.assertFalse(fallback_total)

    def test_13_xlsx_export_all_report_types(self):
        """Verify get_sale_xlsx_report generates valid spreadsheets for all 6 report types."""
        wizard = self._create_report_wizard()

        reports_test_data = [
            (
                'report_by_order',
                [{
                    'number': 'SO001',
                    'date_order': '2026-11-01',
                    'customer': 'Test Customer',
                    'sales_man': 'Test Salesperson',
                    'sum': 5.0,
                    'amount_total': 500.0,
                }],
            ),
            (
                'report_by_order_detail',
                [{
                    'number': 'SO001',
                    'date_order': '2026-11-01',
                    'customer': 'Test Customer',
                    'company': 'My Company',
                    'salesman': 'Test Salesperson',
                    'product': 'Test Product Name',
                    'default_code': 'TRP-001',
                    'product_uom_qty': 5.0,
                    'price_subtotal': 500.0,
                    'amount_total': 500.0,
                }],
            ),
            (
                'report_by_order_detail',
                [{
                    'number': 'SO002',
                    'date_order': '2026-11-01',
                    'customer': 'Test Customer',
                    'company': 'My Company',
                    'salesman': 'Test Salesperson',
                    'product': {'en_US': 'Translated Product'},
                    'default_code': 'TRP-002',
                    'product_uom_qty': 2.0,
                    'price_subtotal': 200.0,
                    'amount_total': 200.0,
                }],
            ),
            (
                'report_by_product',
                [{
                    'product': 'Test Product Name',
                    'category': 'Test Category',
                    'default_code': 'TRP-001',
                    'product_uom_qty': 10.0,
                    'amount_total': 1000.0,
                }],
            ),
            (
                'report_by_categories',
                [{
                    'name': 'Test Category Name',
                    'qty': 15.0,
                    'amount_total': 1500.0,
                }],
            ),
            (
                'report_by_salesperson',
                [{
                    'name': 'Test Salesperson Name',
                    'order': 3,
                    'qty': 12.0,
                    'amount': 1200.0,
                }],
            ),
            (
                'report_by_state',
                [
                    {'state': 'draft', 'count': 1, 'qty': 2.0, 'amount': 200.0},
                    {'state': 'sent', 'count': 1, 'qty': 3.0, 'amount': 300.0},
                    {'state': 'sale', 'count': 2, 'qty': 7.0, 'amount': 700.0},
                    {'state': 'cancel', 'count': 0, 'qty': 0.0, 'amount': 0.0},
                ],
            ),
        ]

        for rtype, sample_lines in reports_test_data:
            response = MockResponse()
            filters_dict = {
                'report_type': rtype,
                'date_from': '2026-11-01',
                'date_to': '2026-11-30',
            }
            dfr_dict = {
                'filters': {
                    'date_from': '2026-11-01',
                    'date_to': '2026-11-30',
                },
            }

            wizard.get_sale_xlsx_report(
                data=json.dumps(filters_dict),
                response=response,
                report_data=json.dumps(sample_lines),
                dfrm_data=json.dumps(dfr_dict),
            )
            excel_bytes = response.stream.getvalue()
            self.assertGreater(
                len(excel_bytes), 0, f"XLSX for {rtype} should generate binary content.",
            )

    def test_14_xlsx_export_empty_data(self):
        """Verify get_sale_xlsx_report runs without error when report lines are empty."""
        wizard = self._create_report_wizard()
        response = MockResponse()
        filters_dict = {'report_type': 'report_by_order'}
        dfr_dict = {'filters': {'date_from': False, 'date_to': False}}

        wizard.get_sale_xlsx_report(
            data=json.dumps(filters_dict),
            response=response,
            report_data=json.dumps([]),
            dfrm_data=json.dumps(dfr_dict),
        )
        excel_bytes = response.stream.getvalue()
        self.assertGreater(len(excel_bytes), 0)

    def test_15_qweb_sale_order_report_values(self):
        """Verify abstract model report.sale_report_generator.sale_order_report values."""
        report_model = self.env['report.sale_report_generator.sale_order_report']
        test_data = {
            'report_data': {
                'report_lines': [{'number': 'SO001'}],
                'filters': {'report_type': 'Report By Order'},
            },
        }

        # With sale_order_report in context
        vals = report_model.with_context(
            sale_order_report=True,
        )._get_report_values([], data=test_data)
        self.assertIn('report_main_line_data', vals)
        self.assertIn('Filters', vals)
        self.assertIn('company', vals)
        self.assertEqual(vals['Filters']['report_type'], 'Report By Order')

        # Without sale_order_report context
        vals_no_ctx = report_model._get_report_values([], data=test_data)
        self.assertIsNone(vals_no_ctx)
