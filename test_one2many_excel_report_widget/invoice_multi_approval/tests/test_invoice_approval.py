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
class TestInvoiceApprovalConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create users
        cls.manager = cls.env['res.users'].create({
            'name': 'Approval Manager',
            'login': 'approval_manager_cfg',
            'group_ids': [(6, 0, [cls.env.ref('invoice_multi_approval.group_approve_manager').id])]
        })
        cls.approver_1 = cls.env['res.users'].create({
            'name': 'Approver 1',
            'login': 'approver_1_cfg',
            'group_ids': [(6, 0, [cls.env.ref('invoice_multi_approval.group_approver').id])]
        })
        cls.approver_2 = cls.env['res.users'].create({
            'name': 'Approver 2',
            'login': 'approver_2_cfg',
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

    def test_06_invoice_approval_config(self):
        # By default we set all to True in setUpClass, so no_approve should be True
        self.assertTrue(self.config.no_approve)

        # Test turning off all approvals
        self.config.write({
            'approve_customer_invoice': False,
            'approve_vendor_bill': False,
            'approve_customer_credit': False,
            'approve_vendor_credit': False,
        })
        self.assertFalse(self.config.no_approve)
