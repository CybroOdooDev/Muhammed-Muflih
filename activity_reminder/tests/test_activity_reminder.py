# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import common, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestActivityReminder(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test user to receive the reminder
        cls.test_user = cls.env['res.users'].create({
            'name': 'Activity Test User',
            'login': 'activity_test_user',
            'email': 'recipient@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]
        })

        # Ensure the current user has a valid email to avoid validation or parsing issues
        cls.env.user.email = 'sender@example.com'

    def test_activity_cron_reminder_email(self):
        """Test that the activity_cron cron job finds due activities and sends reminder emails."""
        # Clean/count existing mail messages/mails with this subject to ensure clear assertion
        initial_mail_count = self.env['mail.mail'].search_count([
            ('subject', 'like', 'Reminder: Activity Test Activity is due')
        ])

        # Create a mail.activity record with reminder_due_date = today
        activity = self.env['mail.activity'].create({
            'summary': 'Test Activity',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'user_id': self.test_user.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.test_user.partner_id.id,
        })

        # Run the cron function on persistent mail.activity model
        self.env['mail.activity'].activity_cron()

        # Check if the mail was created
        sent_mails = self.env['mail.mail'].search([
            ('subject', 'like', 'Reminder: Activity Test Activity is due')
        ])

        self.assertEqual(len(sent_mails), initial_mail_count + 1, "Exactly one reminder email should be created and sent")
        latest_mail = sent_mails[0]
        self.assertEqual(latest_mail.email_to, self.test_user.email)
        self.assertEqual(latest_mail.email_from, self.env.user.email)

    def test_wizard_transfers_reminder_due_date(self):
        """Test that scheduling via mail.activity.schedule wizard passes reminder_due_date to created mail.activity."""
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': str([partner.id]),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Wizard Test Activity',
            'reminder_due_date': fields.Date.today(),
            'date_deadline': fields.Date.today(),
            'activity_user_id': self.test_user.id,
        })
        activities = wizard._action_schedule_activities()
        self.assertTrue(activities, "Activity should be created by wizard")
        self.assertEqual(activities.reminder_due_date, fields.Date.today(), "Reminder due date must be copied from wizard to mail.activity")
