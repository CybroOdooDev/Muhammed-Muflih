# -*- coding: utf-8 -*-
import io
import json
import logging
import zipfile

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


_logger = logging.getLogger(__name__)


class XLSXResponse:
    """Minimal response object used by account.move XLSX report tests."""

    def __init__(self):
        _logger.info("Initializing account move XLSX response stream.")
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestAccountMoveExcelReport(TransactionCase):
    """Test account.move XLSX report action and generated workbook content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info("Setting up account move XLSX report test records.")
        cls.partner = cls.env['res.partner'].create({
            'name': 'Account Move XLSX Partner',
            'street': 'Invoice Street',
            'zip': '12345',
            'phone': '555-0199',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Account Move XLSX Product',
            'list_price': 200.0,
            'standard_price': 50.0,
        })
        cls.income_account = cls._get_account('income')
        cls.expense_account = cls._get_account('expense')
        cls.invoice = cls._create_move(
            move_type='out_invoice',
            name='INV-XLSX-CASE',
            payment_reference='INV-XLSX-REF',
            line_name='Invoice XLSX Line',
            account=cls.income_account,
        )
        cls.vendor_bill = cls._create_move(
            move_type='in_invoice',
            name='BILL-XLSX-CASE',
            payment_reference='BILL-XLSX-REF',
            line_name='Vendor Bill XLSX Line',
            account=cls.expense_account,
        )
        _logger.info(
            "Finished setting up account move XLSX records: invoice ID %s, "
            "vendor bill ID %s.",
            cls.invoice.id,
            cls.vendor_bill.id
        )

    @classmethod
    def _get_account(cls, account_kind):
        _logger.info("Searching for %s account.", account_kind)
        account = cls.env['account.account'].search([
            ('account_type', '=', account_kind),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not account:
            _logger.info(
                "No company-specific %s account found; searching globally.",
                account_kind
            )
            account = cls.env['account.account'].search([
                ('account_type', '=', account_kind),
            ], limit=1)
        if not account:
            _logger.error("No %s account found for XLSX test.", account_kind)
            raise AssertionError("A %s account is required." % account_kind)
        _logger.info(
            "Using %s account ID %s for XLSX test.",
            account_kind,
            account.id
        )
        return account

    @classmethod
    def _create_move(cls, move_type, name, payment_reference, line_name,
                     account):
        _logger.info(
            "Creating account move %s with name %s and account ID %s.",
            move_type,
            name,
            account.id
        )
        move = cls.env['account.move'].create({
            'partner_id': cls.partner.id,
            'move_type': move_type,
            'name': name,
            'payment_reference': payment_reference,
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'name': line_name,
                'quantity': 2.0,
                'discount': 10.0,
                'price_unit': 100.0,
                'account_id': account.id,
            })],
        })
        _logger.info("Created account move ID %s for XLSX test.", move.id)
        return move

    def _get_xlsx_shared_strings(self, move):
        _logger.info(
            "Generating XLSX shared strings for account move ID %s.",
            move.id
        )
        response = XLSXResponse()
        move.get_xlsx_report(move.ids, response)
        response.stream.seek(0)
        _logger.info(
            "Generated XLSX stream size for move ID %s: %s bytes.",
            move.id,
            len(response.stream.getvalue())
        )
        self.assertGreater(len(response.stream.getvalue()), 0)

        with zipfile.ZipFile(response.stream) as workbook:
            _logger.info(
                "Reading workbook files for move ID %s: %s.",
                move.id,
                workbook.namelist()
            )
            self.assertIn('xl/workbook.xml', workbook.namelist())
            shared_strings = workbook.read('xl/sharedStrings.xml').decode()
            _logger.info(
                "Read XLSX shared strings for account move ID %s.",
                move.id
            )
            return shared_strings

    def test_print_excel_report_action(self):
        """print_excel_report returns the expected XLSX action payload."""
        _logger.info("Testing account.move print_excel_report action.")
        action = self.invoice.with_context(
            active_ids=self.invoice.ids
        ).print_excel_report()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['model'], 'account.move')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(action['data']['report_name'], 'Invoice Excel Report')
        self.assertEqual(
            json.loads(action['data']['options']),
            self.invoice.ids
        )
        _logger.info("Account move print_excel_report action test passed.")

    def test_get_xlsx_report_invoice_content(self):
        """get_xlsx_report writes invoice header and line values."""
        _logger.info("Testing customer invoice XLSX workbook content.")
        shared_strings = self._get_xlsx_shared_strings(self.invoice)

        expected_values = [
            'INVOICE - %s' % self.invoice.name,
            'Company Name : %s' % self.env.company.name,
            'Customer/Vendor Name',
            self.partner.name,
            'Date',
            'Journal',
            'Currency',
            'State',
            'Source Document',
            'INV-XLSX-REF',
            'Product',
            'Description',
            'Quantity',
            'Account',
            'Discount %',
            'Unit Price',
            'Tax',
            'Subtotal',
            self.product.name,
            'Invoice XLSX Line',
            self.income_account.display_name,
            'Total Amount',
        ]
        for value in expected_values:
            _logger.info("Checking invoice XLSX shared string: %s.", value)
            self.assertIn(value, shared_strings)
        _logger.info("Customer invoice XLSX workbook content test passed.")

    def test_get_xlsx_report_vendor_bill_content(self):
        """get_xlsx_report writes vendor bill header and line values."""
        _logger.info("Testing vendor bill XLSX workbook content.")
        shared_strings = self._get_xlsx_shared_strings(self.vendor_bill)

        expected_values = [
            'VENDOR BILL - %s' % self.vendor_bill.name,
            'Company Name : %s' % self.env.company.name,
            'Customer/Vendor Name',
            self.partner.name,
            'Source Document',
            'BILL-XLSX-REF',
            self.product.name,
            'Vendor Bill XLSX Line',
            self.expense_account.display_name,
            'Total Amount',
        ]
        for value in expected_values:
            _logger.info("Checking vendor bill XLSX shared string: %s.", value)
            self.assertIn(value, shared_strings)
        _logger.info("Vendor bill XLSX workbook content test passed.")
