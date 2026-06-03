# -*- coding: utf-8 -*-
import io
import json
import logging
import zipfile

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


_logger = logging.getLogger(__name__)


class XLSXResponse:
    """Minimal response object used by sale.order XLSX report tests."""

    def __init__(self):
        _logger.info("Initializing sale order XLSX response stream.")
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestSaleOrderExcelReport(TransactionCase):
    """Test sale.order XLSX report action and generated workbook content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info("Setting up sale order XLSX report test records.")
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sale Order XLSX Partner',
            'street': 'Sale Street',
            'zip': '67890',
            'phone': '555-0177',
        })
        _logger.info("Created sale order test partner ID %s.", cls.partner.id)
        cls.product = cls.env['product.product'].create({
            'name': 'Sale Order XLSX Product',
            'list_price': 125.0,
            'standard_price': 40.0,
        })
        _logger.info("Created sale order test product ID %s.", cls.product.id)
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'name': 'SO-XLSX-CASE',
            'client_order_ref': 'SO-XLSX-REF',
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Sale Order XLSX Line',
                'product_uom_qty': 3.0,
                'price_unit': 125.0,
            })],
        })
        _logger.info(
            "Created sale order ID %s for XLSX test.",
            cls.sale_order.id
        )
        _logger.info("Finished setting up sale order XLSX report records.")

    def _get_xlsx_shared_strings(self, sale_order):
        _logger.info(
            "Generating XLSX shared strings for sale order ID %s.",
            sale_order.id
        )
        response = XLSXResponse()
        sale_order.get_xlsx_report(sale_order.ids, response)
        _logger.info(
            "Generated sale order XLSX report for record IDs %s.",
            sale_order.ids
        )
        response.stream.seek(0)
        _logger.info(
            "Generated XLSX stream size for sale order ID %s: %s bytes.",
            sale_order.id,
            len(response.stream.getvalue())
        )
        self.assertGreater(len(response.stream.getvalue()), 0)

        with zipfile.ZipFile(response.stream) as workbook:
            _logger.info(
                "Reading workbook files for sale order ID %s: %s.",
                sale_order.id,
                workbook.namelist()
            )
            self.assertIn('xl/workbook.xml', workbook.namelist())
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()
            _logger.info(
                "Read %s characters from XLSX shared strings for sale order "
                "ID %s.",
                len(shared_strings),
                sale_order.id
            )
            return shared_strings

    def test_print_excel_report_action(self):
        """print_excel_report returns the expected XLSX action payload."""
        _logger.info("Testing sale.order print_excel_report action.")
        action = self.sale_order.with_context(
            active_ids=self.sale_order.ids
        ).print_excel_report()
        _logger.info("Received sale order report action: %s.", action)

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'sale.order')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(
            action['data']['report_name'],
            'Sale/Quotation Excel Report'
        )
        self.assertEqual(
            json.loads(action['data']['options']),
            self.sale_order.ids
        )
        _logger.info("Sale order print_excel_report action test passed.")

    def test_get_xlsx_report_content(self):
        """get_xlsx_report writes sale order header and line values."""
        _logger.info("Testing sale order XLSX workbook content.")
        shared_strings = self._get_xlsx_shared_strings(self.sale_order)

        expected_values = [
            'SALE ORDER - %s' % self.sale_order.name,
            'Company Name : %s' % self.env.company.name,
            'Customer Name',
            self.partner.name,
            self.partner.street,
            self.partner.zip,
            self.partner.phone,
            'Date',
            'Payment Term',
            'Price List',
            'State',
            'Sales Team',
            'Sales Persons',
            'Source Document',
            'SO-XLSX-REF',
            'Fiscal Position',
            'Product',
            'Description',
            'Quantity',
            'Delivered',
            'Invoiced',
            'Unit Price',
            'Tax',
            'Subtotal',
            self.product.name,
            'Sale Order XLSX Line',
            'Total Amount',
        ]
        _logger.info(
            "Checking %s expected strings in sale order XLSX workbook.",
            len(expected_values)
        )
        for value in expected_values:
            _logger.info("Checking sale order XLSX shared string: %s.", value)
            self.assertIn(value, shared_strings)
        _logger.info("Sale order XLSX workbook content test passed.")
