# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import timedelta
from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSalesIncentive(TransactionCase):
    """Test suite for Sales Incentive Calculation module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.salesperson = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson_inc',
            'email': 'salesperson@test.com',
        })

        cls.today = fields.Date.today()
        cls.start_date = cls.today - timedelta(days=30)
        cls.end_date = cls.today - timedelta(days=1)

        # Deactivate any existing active challenges and schemes from test database
        cls.env['gamification.challenge'].search([
            ('incentive_calculation', '=', True)
        ]).write({'incentive_calculation': False})
        cls.env['sales.incentive'].search([
            ('active_calculation', '=', True)
        ]).write({'active_calculation': False})

        # Gamification goal definition and challenge
        cls.goal_definition = cls.env['gamification.goal.definition'].create({
            'name': 'Sales Target Test Goal',
            'computation_mode': 'manually',
        })

        cls.challenge = cls.env['gamification.challenge'].create({
            'name': 'Monthly Sales Challenge',
            'incentive_calculation': True,
        })

        cls.challenge_line = cls.env['gamification.challenge.line'].create({
            'challenge_id': cls.challenge.id,
            'definition_id': cls.goal_definition.id,
            'target_goal': 1000.0,
        })

        cls.goal = cls.env['gamification.goal'].create({
            'definition_id': cls.goal_definition.id,
            'user_id': cls.salesperson.id,
            'line_id': cls.challenge_line.id,
            'target_goal': 1000.0,
            'current': 800.0,
            'start_date': cls.start_date,
            'end_date': cls.end_date,
        })

        # Find or create journal and accounts for approval testing
        cls.journal = cls.env['account.journal'].search([], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Incentive General Journal',
                'type': 'general',
                'code': 'INCJ',
                'company_id': cls.env.company.id,
            })

        accounts = cls.env['account.account'].search([
            ('active', '=', True),
        ], limit=2)
        if len(accounts) >= 2:
            cls.debit_account = accounts[0]
            cls.credit_account = accounts[1]
        elif accounts:
            cls.debit_account = accounts[0]
            cls.credit_account = accounts[0]
        else:
            cls.debit_account = cls.env['account.account'].create({
                'name': 'Incentive Expense Account',
                'code': 'INCEXP01',
                'account_type': 'expense',
                'company_ids': [fields.Command.link(cls.env.company.id)],
            })
            cls.credit_account = cls.env['account.account'].create({
                'name': 'Incentive Payable Account',
                'code': 'INCPAY01',
                'account_type': 'liability_current',
                'company_ids': [fields.Command.link(cls.env.company.id)],
            })

    def test_goal_achievement_percentage(self):
        """Test calculation of target_achievement_percentage on gamification.goal."""
        # 800 / 1000 * 100 = 80.0%
        self.assertEqual(self.goal.target_achievement_percentage, 80.0)

        # When target_goal is 0
        zero_goal = self.env['gamification.goal'].create({
            'definition_id': self.goal_definition.id,
            'user_id': self.salesperson.id,
            'target_goal': 0.0,
            'current': 500.0,
            'end_date': self.end_date,
        })
        self.assertEqual(zero_goal.target_achievement_percentage, 0.0)

    def test_challenge_incentive_calculation_onchange(self):
        """Test onchange validation for gamification.challenge when another is active."""
        new_challenge = self.env['gamification.challenge'].new({
            'name': 'Second Challenge',
            'incentive_calculation': True,
        })
        with self.assertRaises(UserError):
            new_challenge._onchange_incentive_calculation()

    def test_sales_incentive_linear_calculation(self):
        """Test linear calculation method with percentage and fixed amount rewards."""
        linear_scheme = self.env['sales.incentive'].create({
            'name': 'Linear Scheme Test',
            'calculation_method': 'linear',
            'active_calculation': True,
            'select_incentive_ids': [
                (0, 0, {
                    'upto_percent': 50.0,
                    'reward': 5.0,
                    'incentive_type': 'percent',
                }),
                (0, 0, {
                    'upto_percent': 80.0,
                    'reward': 100.0,
                    'incentive_type': 'amount',
                }),
            ],
        })

        # Test onchange validation when another scheme is already active
        another_scheme = self.env['sales.incentive'].new({
            'name': 'Duplicate Active Scheme',
            'active_calculation': True,
        })
        with self.assertRaises(UserError):
            another_scheme._onchange_active_calculation()

        # Compute incentive
        action = linear_scheme.action_incentive_compute()
        self.assertEqual(action.get('res_model'), 'calculate.incentive')

        # Check created calculate.incentive record
        calc_record = self.env['calculate.incentive'].search([
            ('salesperson_id', '=', self.salesperson.id),
        ], limit=1)
        self.assertTrue(calc_record, "A calculate.incentive record must be created")
        self.assertEqual(calc_record.goal, 1000.0)
        self.assertEqual(calc_record.achieved, 800.0)
        self.assertEqual(calc_record.achievement_percentage, 80.0)
        # Because achieved is 80%, highest matching tier is 80% which gives fixed 100.0
        self.assertEqual(calc_record.incentive, 100.0)
        self.assertEqual(calc_record.status, 'unpaid')

    def test_sales_incentive_tiered_calculation(self):
        """Test tiered ('step') commission calculation method."""
        # Deactivate any previous schemes first
        self.env['sales.incentive'].search([]).write({'active_calculation': False})

        tiered_scheme = self.env['sales.incentive'].create({
            'name': 'Tiered Scheme Test',
            'calculation_method': 'step',
            'active_calculation': True,
            'select_incentive_ids': [
                (0, 0, {
                    'upto_percent': 50.0,
                    'reward': 5.0,
                    'incentive_type': 'percent',
                }),
                (0, 0, {
                    'upto_percent': 100.0,
                    'reward': 10.0,
                    'incentive_type': 'percent',
                }),
            ],
        })

        # Target 1000, Current 800 (80% achieved)
        # Tier 1: 50% of 1000 = 500 * 5% = 25.0
        # Remainder: (800 - 500) = 300 * 10% = 30.0
        # Expected total incentive: 25.0 + 30.0 = 55.0
        tiered_scheme.action_incentive_compute()

        calc_record = self.env['calculate.incentive'].search([
            ('salesperson_id', '=', self.salesperson.id),
        ], limit=1)
        self.assertTrue(calc_record)
        self.assertEqual(calc_record.incentive, 55.0)

    def test_warnings_and_validations(self):
        """Test send_warnings raises UserError when conditions are not satisfied."""
        scheme = self.env['sales.incentive'].create({
            'name': 'Warning Test Scheme',
            'calculation_method': 'linear',
        })

        # When challenge or docs is empty
        empty_challenge = self.env['gamification.challenge'].browse()
        empty_docs = self.env['gamification.goal'].browse()
        with self.assertRaises(UserError):
            scheme.send_warnings(empty_challenge, empty_docs)

        # When a goal has no end date
        no_end_date_goal = self.env['gamification.goal'].create({
            'definition_id': self.goal_definition.id,
            'user_id': self.salesperson.id,
            'line_id': self.challenge_line.id,
            'target_goal': 500.0,
            'current': 100.0,
            'end_date': False,
        })
        with self.assertRaises(UserError):
            scheme.send_warnings(self.challenge, no_end_date_goal)
        no_end_date_goal.unlink()

    def test_calculate_incentive_lifecycle_and_submission(self):
        """Test calculate.incentive date check and submission to accountant."""
        calc = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'goal': 1000.0,
            'achieved': 800.0,
            'achievement_percentage': 80.0,
            'incentive': 150.0,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': 'unpaid',
        })

        # Test date check (end_date was yesterday, so date_check should be True)
        calc._compute_date_check()
        self.assertTrue(calc.date_check)

        # Test future date check (end_date in future -> date_check should be False)
        calc.end_date = self.today + timedelta(days=10)
        calc._compute_date_check()
        self.assertFalse(calc.date_check)

        # Restore end_date
        calc.end_date = self.end_date

        # Test submission with 0 incentive raises UserError
        calc.incentive = 0.0
        with self.assertRaises(UserError):
            calc.action_submit_to_accountant()

        # Submit with valid incentive
        calc.incentive = 150.0
        calc.action_submit_to_accountant()
        self.assertEqual(calc.status, 'submit')
        self.assertTrue(calc.check)

        # Verify created approve.incentive
        approve_record = self.env['approve.incentive'].search([
            ('salesperson_id', '=', self.salesperson.id),
            ('status', '=', 'submit'),
        ], limit=1)
        self.assertTrue(approve_record)
        self.assertEqual(approve_record.incentive, 150.0)

    def test_approve_incentive_approval_and_rejection(self):
        """Test approve.incentive action_approve and action_rejected workflows."""
        # Create calculate.incentive in submitted status
        calc = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'goal': 1000.0,
            'achieved': 800.0,
            'achievement_percentage': 80.0,
            'incentive': 200.0,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': 'submit',
            'check': True,
        })

        approve_rec = self.env['approve.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'goal': 1000.0,
            'achieved': 800.0,
            'achievement_percentage': 80.0,
            'incentive': 200.0,
            'status': 'submit',
            'start_date': self.start_date,
            'end_date': self.end_date,
        })

        # Test approval without journal/accounts raises UserError
        with self.assertRaises(UserError):
            approve_rec.action_approve()

        # Assign journal and accounts
        approve_rec.write({
            'journal_id': self.journal.id,
            'debit_account_id': self.debit_account.id,
            'credit_account_id': self.credit_account.id,
        })

        # Test successful approval
        approve_rec.action_approve()
        self.assertEqual(approve_rec.status, 'paid')
        self.assertTrue(approve_rec.check)
        self.assertEqual(calc.status, 'paid')
        self.assertTrue(calc.check)

        # Test rejection on a second record
        calc2 = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'goal': 500.0,
            'achieved': 200.0,
            'achievement_percentage': 40.0,
            'incentive': 50.0,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': 'submit',
            'check': True,
        })

        approve_rec2 = self.env['approve.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'goal': 500.0,
            'achieved': 200.0,
            'achievement_percentage': 40.0,
            'incentive': 50.0,
            'status': 'submit',
            'start_date': self.start_date,
            'end_date': self.end_date,
        })

        approve_rec2.action_rejected()
        self.assertEqual(approve_rec2.status, 'reject')
        self.assertTrue(approve_rec2.check)
        self.assertEqual(calc2.status, 'reject')
        self.assertTrue(calc2.check)

    def test_filter_and_unlink_expired_calc_records(self):
        """Test filtering and unlinking expired calculate.incentive records."""
        scheme = self.env['sales.incentive'].create({
            'name': 'Filter Expired Test',
            'calculation_method': 'linear',
        })

        future_calc = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'incentive': 100.0,
            'end_date': self.today + timedelta(days=5),
        })
        same_date_calc = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'incentive': 100.0,
            'end_date': self.end_date,
        })

        calc_records = future_calc | same_date_calc
        unlink_ids = scheme.filter_expired_calc_records(calc_records, self.goal)
        self.assertIn(same_date_calc.id, unlink_ids)
        self.assertFalse(future_calc.exists(), "Future records should be immediately unlinked")

        scheme.unlink_expired_calc_records(unlink_ids)
        self.assertFalse(same_date_calc.exists(), "Same date records should be unlinked")

    def test_challenge_incentive_calculation_db_constrains(self):
        """Test database constraint on gamification.challenge for incentive_calculation."""
        # self.challenge already has incentive_calculation=True
        with self.assertRaises(ValidationError):
            self.env['gamification.challenge'].create({
                'name': 'Duplicate Active Challenge DB',
                'incentive_calculation': True,
            })

        inactive_challenge = self.env['gamification.challenge'].create({
            'name': 'Inactive Challenge DB',
            'incentive_calculation': False,
        })
        with self.assertRaises(ValidationError):
            inactive_challenge.write({'incentive_calculation': True})

    def test_sales_incentive_active_calculation_db_constrains(self):
        """Test database constraint on sales.incentive for active_calculation."""
        self.env['sales.incentive'].search([]).write({'active_calculation': False})
        self.env['sales.incentive'].create({
            'name': 'Active Scheme DB 1',
            'active_calculation': True,
        })
        with self.assertRaises(ValidationError):
            self.env['sales.incentive'].create({
                'name': 'Active Scheme DB 2',
                'active_calculation': True,
            })

        inactive_scheme = self.env['sales.incentive'].create({
            'name': 'Inactive Scheme DB',
            'active_calculation': False,
        })
        with self.assertRaises(ValidationError):
            inactive_scheme.write({'active_calculation': True})

    def test_multi_recordset_goal_computation(self):
        """Test target_achievement_percentage computation across multi-recordset."""
        salesperson2 = self.env['res.users'].create({
            'name': 'Salesperson Two',
            'login': 'salesperson_two_inc',
            'email': 'sp2@test.com',
        })
        goal1 = self.env['gamification.goal'].create({
            'definition_id': self.goal_definition.id,
            'user_id': self.salesperson.id,
            'target_goal': 1000.0,
            'current': 500.0,
            'end_date': self.end_date,
        })
        goal2 = self.env['gamification.goal'].create({
            'definition_id': self.goal_definition.id,
            'user_id': salesperson2.id,
            'target_goal': 2000.0,
            'current': 1500.0,
            'end_date': self.end_date,
        })
        goal3 = self.env['gamification.goal'].create({
            'definition_id': self.goal_definition.id,
            'user_id': self.salesperson.id,
            'target_goal': 0.0,
            'current': 100.0,
            'end_date': self.end_date,
        })
        goals = goal1 | goal2 | goal3
        goals._compute_target_achievement_percentage()
        self.assertEqual(goal1.target_achievement_percentage, 50.0)
        self.assertEqual(goal2.target_achievement_percentage, 75.0)
        self.assertEqual(goal3.target_achievement_percentage, 0.0)

    def test_multi_recordset_calculate_incentive_date_check(self):
        """Test date_check computed field across multi-recordset."""
        calc_past = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'end_date': self.today - timedelta(days=5),
            'incentive': 100.0,
        })
        calc_today = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'end_date': self.today,
            'incentive': 150.0,
        })
        calc_future = self.env['calculate.incentive'].create({
            'salesperson_id': self.salesperson.id,
            'end_date': self.today + timedelta(days=5),
            'incentive': 200.0,
        })
        multi_calc = calc_past | calc_today | calc_future
        multi_calc._compute_date_check()
        self.assertTrue(calc_past.date_check)
        self.assertTrue(calc_today.date_check)
        self.assertFalse(calc_future.date_check)

    def test_multi_recordset_compute_incentive_multiple_goals(self):
        """Test action_incentive_compute processing multiple goals for multiple salespeople."""
        self.env['sales.incentive'].search([]).write({'active_calculation': False})
        scheme = self.env['sales.incentive'].create({
            'name': 'Multi Goal Linear Scheme',
            'calculation_method': 'linear',
            'active_calculation': True,
            'select_incentive_ids': [
                (0, 0, {
                    'upto_percent': 50.0,
                    'reward': 100.0,
                    'incentive_type': 'amount',
                }),
            ],
        })

        salesperson2 = self.env['res.users'].create({
            'name': 'Second Salesperson Goal',
            'login': 'second_salesperson_goal_inc',
            'email': 'sp_goal2@test.com',
        })
        self.env['gamification.goal'].create({
            'definition_id': self.goal_definition.id,
            'challenge_id': self.challenge.id,
            'user_id': salesperson2.id,
            'line_id': self.challenge_line.id,
            'target_goal': 1000.0,
            'current': 600.0,
            'start_date': self.start_date,
            'end_date': self.end_date,
        })

        scheme.action_incentive_compute()

        calcs = self.env['calculate.incentive'].search([
            ('salesperson_id', 'in', [self.salesperson.id, salesperson2.id]),
        ])
        self.assertGreaterEqual(len(calcs), 2, "Records should be computed for both salespeople")
