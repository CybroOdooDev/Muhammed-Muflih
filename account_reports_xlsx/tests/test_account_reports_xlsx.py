# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
################################################################################
import io
import json
import zipfile
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


class MockResponse:
    """Mock response object for testing get_xlsx_report method."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestAccountReportsXlsx(TransactionCase):
    """Unit test suite for Accounting Reports in Excel (account_reports_xlsx)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Ensure company has a currency
        cls.currency = cls.company.currency_id

        # Create partners
        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Test Customer Partner',
            'email': 'customer@test.com',
        })
        cls.partner_supplier = cls.env['res.partner'].create({
            'name': 'Test Supplier Partner',
            'email': 'supplier@test.com',
        })

        # Find or create accounts
        cls.account_receivable = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', 'in', cls.company.id)
        ], limit=1)

        cls.account_payable = cls.env['account.account'].search([
            ('account_type', '=', 'liability_payable'),
            ('company_ids', 'in', cls.company.id)
        ], limit=1)

        cls.account_income = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id)
        ], limit=1)

        cls.account_expense = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('company_ids', 'in', cls.company.id)
        ], limit=1)

        # Find journals
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id)
        ], limit=1)

        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id)
        ], limit=1)

        # Create and post a customer invoice
        cls.customer_invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner_customer.id,
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'journal_id': cls.sale_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Test Services',
                    'quantity': 1.0,
                    'price_unit': 500.0,
                    'account_id': cls.account_income.id if cls.account_income else False,
                })
            ]
        })
        cls.customer_invoice.action_post()

        # Create and post a vendor bill
        cls.vendor_bill = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner_supplier.id,
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'journal_id': cls.purchase_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Test Supplies',
                    'quantity': 1.0,
                    'price_unit': 200.0,
                    'account_id': cls.account_expense.id if cls.account_expense else False,
                })
            ]
        })
        cls.vendor_bill.action_post()

    def test_01_module_installation(self):
        """Verify module is installed."""
        module = self.env['ir.module.module'].search([('name', '=', 'account_reports_xlsx')], limit=1)
        self.assertTrue(module, "account_reports_xlsx module should be found.")

    def test_02_account_financial_report_model(self):
        """Test account.financial.report hierarchy, level compute, and ordering."""
        parent_report = self.env['account.financial.report'].create({
            'name': 'Test Financial Parent',
            'type': 'sum',
            'sequence': 10,
        })
        self.assertEqual(parent_report.level, 0, "Top level report must have level 0.")

        child_report = self.env['account.financial.report'].create({
            'name': 'Test Financial Child',
            'type': 'account_type',
            'account_type_ids': 'income_other',
            'parent_id': parent_report.id,
            'sequence': 20,
        })
        self.assertEqual(child_report.level, 1, "Child report level must be parent.level + 1.")

        grandchild_report = self.env['account.financial.report'].create({
            'name': 'Test Financial Grandchild',
            'type': 'accounts',
            'parent_id': child_report.id,
            'sequence': 30,
        })
        self.assertEqual(grandchild_report.level, 2, "Grandchild report level must be 2.")

        # Test multi-recordset level computation
        records = parent_report + child_report + grandchild_report
        records._get_level()
        self.assertEqual(parent_report.level, 0)
        self.assertEqual(child_report.level, 1)
        self.assertEqual(grandchild_report.level, 2)

        # Test _get_children_by_order
        ordered_children = parent_report._get_children_by_order()
        self.assertIn(child_report, ordered_children)
        self.assertIn(grandchild_report, ordered_children)

    def test_03_account_move_line_query_get(self):
        """Test custom _query_get method on account.move.line under different context scenarios."""
        aml_model = self.env['account.move.line']

        # Scenario 1: Basic dates and posted state
        ctx_basic = {
            'date_from': fields.Date.today() - relativedelta(days=30),
            'date_to': fields.Date.today(),
            'state': 'posted',
            'strict_range': True,
            'company_id': self.company.id,
        }
        tables, where_clause, params = aml_model.with_context(ctx_basic)._query_get()
        self.assertTrue(tables, "Tables should not be empty.")
        self.assertIn('account_move_line', tables.lower())

        # Scenario 2: Aged balance context (switches date field to date_maturity)
        ctx_aged = {
            'date_to': fields.Date.today(),
            'aged_balance': True,
            'state': 'posted',
        }
        tables_aged, where_clause_aged, params_aged = aml_model.with_context(ctx_aged)._query_get()
        self.assertTrue(tables_aged)

        # Scenario 3: Initial balance context
        ctx_init_bal = {
            'date_from': fields.Date.today(),
            'initial_bal': True,
            'strict_range': True,
        }
        tables_init, where_clause_init, params_init = aml_model.with_context(ctx_init_bal)._query_get()
        self.assertTrue(tables_init)

        # Scenario 4: Specific journal, partner, and account filters
        ctx_filters = {
            'journal_ids': self.sale_journal.ids,
            'partner_ids': self.partner_customer,
            'account_ids': self.account_income if self.account_income else self.env['account.account'],
            'state': 'all',
        }
        tables_f, where_f, params_f = aml_model.with_context(ctx_filters)._query_get()
        self.assertTrue(tables_f)

    def test_04_account_common_report_wizards(self):
        """Test base models account.common.report.xlsx and account.common.account.report.xlsx."""
        common_wizard = self.env['account.common.report.xlsx'].create({
            'company_id': self.company.id,
            'target_move': 'posted',
            'date_from': fields.Date.today() - relativedelta(days=10),
            'date_to': fields.Date.today(),
        })

        # Test _onchange_company_id
        common_wizard._onchange_company_id()
        self.assertTrue(common_wizard.journal_ids, "Journals should be populated on company change.")

        # Test _build_contexts
        data = {'form': common_wizard.read([])[0]}
        ctx = common_wizard._build_contexts(data)
        self.assertEqual(ctx.get('state'), 'posted')
        self.assertEqual(ctx.get('company_id'), self.company.id)
        self.assertTrue(ctx.get('strict_range'))

        # Test base _print_report raises NotImplementedError
        with self.assertRaises(NotImplementedError):
            common_wizard._print_report(data)

        # Test account.common.account.report.xlsx pre_print_report
        account_wizard = self.env['account.common.account.report.xlsx'].create({
            'display_account': 'movement',
        })
        prep_data = account_wizard.pre_print_report({'form': {}})
        self.assertEqual(prep_data['form'].get('display_account'), 'movement')

    def test_05_accounting_financial_report_wizard_and_xlsx(self):
        """Test accounting.report.xlsx wizard and Excel generation for financial reports."""
        report_record = self.env.ref('account_reports_xlsx.account_financial_report_profitandloss0', raise_if_not_found=False)
        if not report_record:
            report_record = self.env['account.financial.report'].create({
                'name': 'Test Profit and Loss',
                'type': 'sum',
                'sign': -1,
            })

        wizard = self.env['accounting.report.xlsx'].create({
            'account_report_id': report_record.id,
            'target_move': 'posted',
            'date_from': fields.Date.today() - relativedelta(days=30),
            'date_to': fields.Date.today(),
            'enable_filter': True,
            'filter_cmp': 'filter_date',
            'date_from_cmp': fields.Date.today() - relativedelta(days=60),
            'date_to_cmp': fields.Date.today() - relativedelta(days=31),
            'label_filter': 'Comparison Period',
        })

        # Test check_report action structure
        action = wizard.check_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')
        self.assertIn('data', action)

        # Test check_report_xlsx alias
        alias_action = wizard.check_report_xlsx()
        self.assertEqual(alias_action.get('report_type'), 'xlsx')

        # Test comparison context building
        data = {'form': wizard.read([])[0]}
        cmp_ctx = wizard._build_comparison_context(data)
        self.assertEqual(cmp_ctx.get('state'), 'posted')
        self.assertTrue(cmp_ctx.get('strict_range'))

        # Test get_xlsx_report execution and binary output
        mock_response = MockResponse()
        options = json.loads(action['data']['options'])
        wizard.get_xlsx_report(options, mock_response)

        xlsx_bytes = mock_response.stream.getvalue()
        self.assertTrue(len(xlsx_bytes) > 0, "Generated Excel report should not be empty.")

        # Validate that the bytes form a valid XLSX (ZIP) file
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as z:
            self.assertIn('[Content_Types].xml', z.namelist())

        # Test financial report compute helper directly
        env_obj = self.env['report.account_reports_xlsx.report_financial']
        account_lines = env_obj.get_account_lines(options['form'])
        self.assertIsInstance(account_lines, list)

    def test_06_general_ledger_wizard_and_xlsx(self):
        """Test account.report.general.ledger.xlsx wizard and Excel generation."""
        wizard = self.env['account.report.general.ledger.xlsx'].create({
            'target_move': 'posted',
            'display_account': 'movement',
            'initial_balance': True,
            'sortby': 'sort_date',
            'date_from': fields.Date.today() - relativedelta(days=30),
            'date_to': fields.Date.today(),
            'journal_ids': [Command.set(self.sale_journal.ids)],
        })

        # Test check_report action
        action = wizard.check_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')
        self.assertIn('data', action)

        # Test get_xlsx_report execution and binary output
        mock_response = MockResponse()
        options = json.loads(action['data']['options'])
        wizard.get_xlsx_report(options, mock_response)

        xlsx_bytes = mock_response.stream.getvalue()
        self.assertTrue(len(xlsx_bytes) > 0, "General Ledger Excel report must not be empty.")

        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as z:
            self.assertIn('[Content_Types].xml', z.namelist())

        # Test general ledger helper methods
        gl_report = self.env['report.account_reports_xlsx.report_generalledger']
        accounts = self.env['account.account'].browse(options['ids']) or self.env['account.account'].search([], limit=5)
        move_entries = gl_report.with_context(options['form'].get('used_context', {}))._get_account_move_entry(
            accounts, init_balance=True, sortby='sort_date', display_account='all'
        )
        self.assertIsInstance(move_entries, list)

        # Test with sort_journal_partner
        move_entries_sort2 = gl_report.with_context(options['form'].get('used_context', {}))._get_account_move_entry(
            accounts, init_balance=False, sortby='sort_journal_partner', display_account='all'
        )
        self.assertIsInstance(move_entries_sort2, list)

    def test_07_partner_ledger_wizard_and_xlsx(self):
        """Test account.report.partner.ledger.xlsx wizard and Excel generation."""
        wizard = self.env['account.report.partner.ledger.xlsx'].create({
            'target_move': 'posted',
            'result_selection': 'customer_supplier',
            'amount_currency': True,
            'reconciled': False,
            'partner_ids': [Command.set([self.partner_customer.id, self.partner_supplier.id])],
            'date_from': fields.Date.today() - relativedelta(days=30),
            'date_to': fields.Date.today(),
        })

        # Test pre_print_report
        data = {'form': {}}
        data = wizard.pre_print_report(data)
        self.assertEqual(data['form'].get('result_selection'), 'customer_supplier')
        self.assertTrue(data['form'].get('amount_currency'))

        # Test check_report action
        action = wizard.check_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')

        # Test get_xlsx_report execution and binary output
        mock_response = MockResponse()
        options = json.loads(action['data']['options'])
        wizard.get_xlsx_report(options, mock_response)

        xlsx_bytes = mock_response.stream.getvalue()
        self.assertTrue(len(xlsx_bytes) > 0, "Partner Ledger Excel report must not be empty.")

        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as z:
            self.assertIn('[Content_Types].xml', z.namelist())

        # Test partner ledger helper line method
        pl_report = self.env['report.account_reports_xlsx.report_partnerledger']
        lines = pl_report._lines(options, self.partner_customer)
        self.assertIsInstance(lines, list)

    def test_08_aged_partner_balance_wizard_and_xlsx(self):
        """Test account.aged.trial.balance.xlsx wizard and Excel generation."""
        wizard = self.env['account.aged.trial.balance.xlsx'].create({
            'date_from': fields.Date.today(),
            'period_length': 30,
            'result_selection': 'customer',
            'target_move': 'posted',
        })

        # Test _aged_buckets computation
        buckets = wizard._aged_buckets(fields.Date.today(), 30)
        self.assertIn('0', buckets)
        self.assertIn('4', buckets)
        self.assertEqual(buckets['0']['name'], '+120')

        # Test check_report action
        action = wizard.check_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')

        # Test get_xlsx_report execution and binary output
        mock_response = MockResponse()
        options = json.loads(action['data']['options'])
        wizard.get_xlsx_report(options, mock_response)

        xlsx_bytes = mock_response.stream.getvalue()
        self.assertTrue(len(xlsx_bytes) > 0, "Aged Partner Balance Excel report must not be empty.")

        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as z:
            self.assertIn('[Content_Types].xml', z.namelist())

        # Test UserError validations
        with self.assertRaises(UserError):
            invalid_period_wizard = self.env['account.aged.trial.balance.xlsx'].create({
                'date_from': fields.Date.today(),
                'period_length': 0,
            })
            invalid_period_wizard._print_report({'form': {}})

        with self.assertRaises(UserError):
            missing_date_wizard = self.env['account.aged.trial.balance.xlsx'].create({
                'date_from': False,
                'period_length': 30,
            })
            missing_date_wizard._print_report({'form': {}})

    def test_09_controller_security_and_allowed_models(self):
        """Test controller validation of allowed report models and access check."""
        from ..controllers.main import ALLOWED_REPORT_MODELS, XLSXReportController
        controller = XLSXReportController()

        # Test that unauthorized models are blocked with AccessError
        with self.assertRaises(AccessError):
            controller.get_report_xlsx('res.users', '{}', 'xlsx', 'test')

        with self.assertRaises(AccessError):
            controller.get_report_xlsx('account.move', '{}', 'xlsx', 'test')

        # Test allowed models set contains all four report wizard models
        self.assertIn('accounting.report.xlsx', ALLOWED_REPORT_MODELS)
        self.assertIn('account.report.general.ledger.xlsx', ALLOWED_REPORT_MODELS)
        self.assertIn('account.report.partner.ledger.xlsx', ALLOWED_REPORT_MODELS)
        self.assertIn('account.aged.trial.balance.xlsx', ALLOWED_REPORT_MODELS)

