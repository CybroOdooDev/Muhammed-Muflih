# -*- coding: utf-8 -*-
import io
import json
import logging
import zipfile

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


_logger = logging.getLogger(__name__)


class XLSXResponse:
    """Minimal response object expected by get_xlsx_report."""

    def __init__(self):
        _logger.info("Initializing XLSX response stream.")
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestAdvancedExcelReports(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info("Setting up advanced Excel report test records.")
        cls.partner = cls.env['res.partner'].create({
            'name': 'Excel Report Partner',
            'street': 'Report Street',
            'phone': '555-0100',
        })
        _logger.info("Created test partner with ID %s.", cls.partner.id)
        cls.product = cls.env['product.product'].create({
            'name': 'Excel Report Product',
            'list_price': 100.0,
            'standard_price': 25.0,
        })
        _logger.info("Created test product with ID %s.", cls.product.id)

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Excel Sale Line',
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        _logger.info("Created test sale order with ID %s.", cls.sale_order.id)

        income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not income_account:
            income_account = cls.env['account.account'].search([
                ('account_type', '=', 'income'),
            ], limit=1)
        _logger.info("Using income account with ID %s.", income_account.id)

        cls.invoice = cls.env['account.move'].create({
            'partner_id': cls.partner.id,
            'move_type': 'out_invoice',
            'name': 'INV-XLSX-TEST',
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Excel Invoice Line',
                'quantity': 1.0,
                'price_unit': 150.0,
                'account_id': income_account.id,
            })],
        })
        _logger.info("Created test invoice with ID %s.", cls.invoice.id)

        picking_type = cls.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', 'in', [False, cls.env.company.id]),
        ], limit=1)
        _logger.info("Using outgoing picking type with ID %s.", picking_type.id)
        source_location = picking_type.default_location_src_id
        destination_location = (
            picking_type.default_location_dest_id
            or cls.env.ref('stock.stock_location_customers')
        )
        cls.picking = cls.env['stock.picking'].create({
            'name': 'PICK-XLSX-TEST',
            'partner_id': cls.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': destination_location.id,
            'origin': 'SO-XLSX-TEST',
            'move_ids': [(0, 0, {
                # 'name': 'Excel Stock Move',
                'product_id': cls.product.id,
                'product_uom_qty': 3.0,
                'product_uom': cls.product.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': destination_location.id,
            })],
        })
        _logger.info("Created test picking with ID %s.", cls.picking.id)

    def _assert_report_action(self, record, model, report_name):
        _logger.info(
            "Checking XLSX report action for model %s and record IDs %s.",
            model,
            record.ids
        )
        action = record.with_context(active_ids=record.ids).print_excel_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], model)
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(action['data']['report_name'], report_name)
        self.assertEqual(json.loads(action['data']['options']), record.ids)
        _logger.info("XLSX report action check passed for model %s.", model)

    def _assert_xlsx_contains(self, record, expected_strings):
        _logger.info(
            "Generating XLSX report for model %s and record IDs %s.",
            record._name,
            record.ids
        )
        response = XLSXResponse()
        record.get_xlsx_report(record.ids, response)
        response.stream.seek(0)

        self.assertGreater(len(response.stream.getvalue()), 0)
        with zipfile.ZipFile(response.stream) as workbook:
            workbook_files = workbook.namelist()
            self.assertIn('xl/workbook.xml', workbook_files)
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()

        for expected_string in expected_strings:
            _logger.info("Checking XLSX content for string: %s.", expected_string)
            self.assertIn(expected_string, shared_strings)
        _logger.info("XLSX content check passed for model %s.", record._name)

    def test_sale_order_report_action(self):
        """Sale order action returns XLSX report metadata."""
        _logger.info("Starting sale order report action test.")
        self._assert_report_action(
            self.sale_order,
            'sale.order',
            'Sale/Quotation Excel Report'
        )
        _logger.info("Finished sale order report action test.")

    def test_invoice_report_action(self):
        """Invoice action returns XLSX report metadata."""
        _logger.info("Starting invoice report action test.")
        self._assert_report_action(
            self.invoice,
            'account.move',
            'Invoice Excel Report'
        )
        _logger.info("Finished invoice report action test.")

    def test_picking_report_action(self):
        """Picking action returns XLSX report metadata."""
        _logger.info("Starting picking report action test.")
        self._assert_report_action(
            self.picking,
            'stock.picking',
            'Picking Order Excel Report'
        )
        _logger.info("Finished picking report action test.")

    def test_sale_order_xlsx_report_content(self):
        """Sale order XLSX contains the expected header and line data."""
        _logger.info("Starting sale order XLSX content test.")
        self._assert_xlsx_contains(self.sale_order, [
            'SALE ORDER - %s' % self.sale_order.name,
            'Customer Name',
            'Excel Sale Line',
            'Total Amount',
        ])
        _logger.info("Finished sale order XLSX content test.")

    def test_invoice_xlsx_report_content(self):
        """Invoice XLSX contains the expected header and line data."""
        _logger.info("Starting invoice XLSX content test.")
        self._assert_xlsx_contains(self.invoice, [
            'INVOICE - %s' % self.invoice.name,
            'Customer/Vendor Name',
            'Excel Invoice Line',
            'Total Amount',
        ])
        _logger.info("Finished invoice XLSX content test.")

    def test_picking_xlsx_report_content(self):
        """Picking XLSX contains the expected header and move data."""
        _logger.info("Starting picking XLSX content test.")
        self._assert_xlsx_contains(self.picking, [
            'Delivery - %s' % self.picking.name,
            'Customer/Vendor Name',
            # 'Excel Stock Move',
            'SO-XLSX-TEST',
        ])
        _logger.info("Finished picking XLSX content test.")
