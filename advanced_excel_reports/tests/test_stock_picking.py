# -*- coding: utf-8 -*-
import io
import json
import logging
import zipfile

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


_logger = logging.getLogger(__name__)


class XLSXResponse:
    """Minimal response object used by stock.picking XLSX report tests."""

    def __init__(self):
        _logger.info("Initializing stock picking XLSX response stream.")
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestStockPickingExcelReport(TransactionCase):
    """Test stock.picking XLSX report action and workbook content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info("Setting up stock picking XLSX report test records.")
        cls.partner = cls.env['res.partner'].create({
            'name': 'Stock Picking XLSX Partner',
            'street': 'Picking Street',
            'zip': '24680',
            'phone': '555-0144',
        })
        _logger.info("Created stock picking test partner ID %s.", cls.partner.id)
        cls.product = cls.env['product.product'].create({
            'name': 'Stock Picking XLSX Product',
            'list_price': 90.0,
            'standard_price': 30.0,
        })
        _logger.info("Created stock picking test product ID %s.", cls.product.id)

        cls.picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', 'in', [False, cls.env.company.id]),
        ], limit=1)
        if not cls.picking_type:
            raise AssertionError("An outgoing picking type is required.")
        _logger.info(
            "Using outgoing picking type ID %s.",
            cls.picking_type.id
        )
        cls.source_location = (
            cls.picking_type.default_location_src_id
            or cls.env.ref('stock.stock_location_stock')
        )
        cls.destination_location = (
            cls.picking_type.default_location_dest_id
            or cls.env.ref('stock.stock_location_customers')
        )
        _logger.info(
            "Using source location ID %s and destination location ID %s.",
            cls.source_location.id,
            cls.destination_location.id
        )

        cls.picking = cls.env['stock.picking'].create({
            'name': 'PICK-XLSX-CASE',
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.source_location.id,
            'location_dest_id': cls.destination_location.id,
            'origin': 'PICK-XLSX-REF',
            'move_ids': [(0, 0, {
                # 'name': 'Stock Picking XLSX Move',
                'product_id': cls.product.id,
                'product_uom_qty': 4.0,
                'product_uom': cls.product.uom_id.id,
                'location_id': cls.source_location.id,
                'location_dest_id': cls.destination_location.id,
            })],
        })
        _logger.info(
            "Created stock picking ID %s for XLSX test.",
            cls.picking.id
        )
        _logger.info("Finished setting up stock picking XLSX report records.")

    def _get_xlsx_shared_strings(self, picking):
        _logger.info(
            "Generating XLSX shared strings for stock picking ID %s.",
            picking.id
        )
        response = XLSXResponse()
        picking.get_xlsx_report(picking.ids, response)
        _logger.info(
            "Generated stock picking XLSX report for record IDs %s.",
            picking.ids
        )
        response.stream.seek(0)
        _logger.info(
            "Generated XLSX stream size for stock picking ID %s: %s bytes.",
            picking.id,
            len(response.stream.getvalue())
        )
        self.assertGreater(len(response.stream.getvalue()), 0)

        with zipfile.ZipFile(response.stream) as workbook:
            _logger.info(
                "Reading workbook files for stock picking ID %s: %s.",
                picking.id,
                workbook.namelist()
            )
            self.assertIn('xl/workbook.xml', workbook.namelist())
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()
            _logger.info(
                "Read %s characters from XLSX shared strings for stock "
                "picking ID %s.",
                len(shared_strings),
                picking.id
            )
            return shared_strings

    def test_print_excel_report_action(self):
        """print_excel_report returns the expected XLSX action payload."""
        _logger.info("Testing stock.picking print_excel_report action.")
        action = self.picking.with_context(
            active_ids=self.picking.ids
        ).print_excel_report()
        _logger.info("Received stock picking report action: %s.", action)

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'stock.picking')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(
            action['data']['report_name'],
            'Picking Order Excel Report'
        )
        self.assertEqual(
            json.loads(action['data']['options']),
            self.picking.ids
        )
        _logger.info("Stock picking print_excel_report action test passed.")

    def test_get_xlsx_report_content(self):
        """get_xlsx_report writes picking header and move values."""
        _logger.info("Testing stock picking XLSX workbook content.")
        shared_strings = self._get_xlsx_shared_strings(self.picking)

        expected_values = [
            'Delivery - %s' % self.picking.name,
            'Company Name : %s' % self.env.company.name,
            'Customer/Vendor Name',
            self.partner.name,
            self.partner.street,
            self.partner.zip,
            self.partner.phone,
            'Scheduled Date',
            'Effective Date',
            'Operation Type',
            self.picking_type.display_name,
            'Source Location',
            self.source_location.complete_name,
            'Destination Location',
            self.destination_location.complete_name,
            'State',
            'Responsible Person',
            'Source Document',
            'PICK-XLSX-REF',
            'Product',
            'Description',
            'Deadline',
            'Quantity',
            'Quantity Done',
            self.product.name,
            # 'Stock Picking XLSX Move',
        ]
        print(expected_values)
        _logger.info(
            "Checking %s expected strings in stock picking XLSX workbook.",
            len(expected_values)
        )
        for value in expected_values:
            _logger.info("Checking stock picking XLSX shared string: %s.", value)
            self.assertIn(value, shared_strings)
        _logger.info("Stock picking XLSX workbook content test passed.")
