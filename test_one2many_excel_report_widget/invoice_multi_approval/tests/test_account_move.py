# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestInvoiceMultiApprovalAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create users
        cls.manager = cls.env['res.users'].create({
            'name': 'Approval Manager',
            'login': 'approval_manager',
            'group_ids': [(6, 0, [cls.env.ref('invoice_multi_approval.group_approve_manager').id])]
        })
        cls.approver_1 = cls.env['res.users'].create({
            'name': 'Approver 1',
            'login': 'approver_1',
            'group_ids': [(6, 0, [cls.env.ref('invoice_multi_approval.group_approver').id])]
        })
        cls.approver_2 = cls.env['res.users'].create({
            'name': 'Approver 2',
            'login': 'approver_2',
            'group_ids': [(6, 0, [cls.env.ref('invoice_multi_approval.group_approver').id])]
        })

        # Update the default config
        cls.config = cls.env.ref('invoice_multi_approval.default_invoice_multi_approval_config')
        cls.config.write({
            'approve_customer_invoice': True,
            'invoice_approver_ids': [(6, 0, [cls.approver_1.id, cls.approver_2.id])],
            'approve_vendor_bill': True,
            'bill_approver_ids': [(6, 0, [cls.approver_1.id, cls.approver_2.id])],
            'approve_customer_credit': True,
            'cust_credit_approver_ids': [(6, 0, [cls.approver_1.id, cls.approver_2.id])],
            'approve_vendor_credit': True,
            'vend_credit_approver_ids': [(6, 0, [cls.approver_1.id, cls.approver_2.id])],
        })

        # Partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })

        # Product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product'
        })

    def test_01_customer_invoice_approval(self):
        # Create invoice
        invoice = self.env['account.move'].with_user(self.env.user).create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
            })]
        })

        # Check approvers are added
        approver_ids = invoice.approval_ids.mapped('approver_id')
        self.assertIn(self.manager, approver_ids)
        self.assertIn(self.approver_1, approver_ids)
        self.assertIn(self.approver_2, approver_ids)

        # Check document not fully approved
        self.assertFalse(invoice.document_fully_approved)

        # Approver 1 approves
        invoice.with_user(self.approver_1).action_invoice_approve()
        
        # document still not fully approved because approver_2 didn't approve
        self.assertFalse(invoice.users_approved)
        self.assertFalse(invoice.document_fully_approved)

        # Approver 2 approves
        invoice.with_user(self.approver_2).action_invoice_approve()

        # Both users approved, check users_approved
        invoice.invalidate_recordset()
        self.assertTrue(invoice.users_approved)
        self.assertTrue(invoice.document_fully_approved)

    def test_02_manager_approval(self):
        # Create invoice
        invoice = self.env['account.move'].with_user(self.env.user).create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
            })]
        })

        # Manager approves
        invoice.with_user(self.manager).action_invoice_approve()

        # Document is fully approved because manager approved
        self.assertTrue(invoice.document_fully_approved)

    def test_03_vendor_bill_approval(self):
        bill = self.env['account.move'].with_user(self.env.user).create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
            })]
        })
        approver_ids = bill.approval_ids.mapped('approver_id')
        self.assertIn(self.approver_1, approver_ids)
        self.assertIn(self.approver_2, approver_ids)
        bill.with_user(self.approver_1).action_invoice_approve()
        bill.with_user(self.approver_2).action_invoice_approve()
        bill.invalidate_recordset()
        self.assertTrue(bill.users_approved)
        self.assertTrue(bill.document_fully_approved)

    def test_04_customer_credit_note_approval(self):
        refund = self.env['account.move'].with_user(self.env.user).create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
            })]
        })
        approver_ids = refund.approval_ids.mapped('approver_id')
        self.assertIn(self.approver_1, approver_ids)
        refund.with_user(self.approver_1).action_invoice_approve()
        refund.with_user(self.approver_2).action_invoice_approve()
        refund.invalidate_recordset()
        self.assertTrue(refund.document_fully_approved)

    def test_05_vendor_credit_note_approval(self):
        refund = self.env['account.move'].with_user(self.env.user).create({
            'move_type': 'in_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
            })]
        })
        approver_ids = refund.approval_ids.mapped('approver_id')
        self.assertIn(self.approver_1, approver_ids)
        refund.with_user(self.approver_1).action_invoice_approve()
        refund.with_user(self.approver_2).action_invoice_approve()
        refund.invalidate_recordset()
        self.assertTrue(refund.document_fully_approved)

    def test_07_compute_fields(self):
        invoice = self.env['account.move'].with_user(self.env.user).create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100.0,
            })]
        })
        
        # Test page visibility
        self.assertTrue(invoice.page_visibility)

        # Test check_approve_ability
        # Currently running as self.env.user (which is not approver_1 or approver_2)
        invoice._compute_check_approve_ability()
        self.assertFalse(invoice.check_approve_ability)

        invoice_as_approver = invoice.with_user(self.approver_1)
        invoice_as_approver._compute_check_approve_ability()
        self.assertTrue(invoice_as_approver.check_approve_ability)

        # Test is_approved
        invoice_as_approver._compute_is_approved()
        self.assertFalse(invoice_as_approver.is_approved)

        invoice_as_approver.action_invoice_approve()
        invoice_as_approver._compute_is_approved()
        self.assertTrue(invoice_as_approver.is_approved)
