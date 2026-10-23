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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAutomaticProjectTaskTimer(TransactionCase):
    """Test suite for Automatic Project Task Timer functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Enable timer setting in system parameters
        cls.env['ir.config_parameter'].sudo().set_param(
            'automatic_project_task_timer.timer_setting', True
        )

        # Create test project
        cls.project = cls.env['project.project'].create({
            'name': 'Timer Test Project',
            'allow_timesheets': True,
        })

        # Create stages
        cls.stage_draft = cls.env['project.task.type'].create({
            'name': 'Draft',
            'sequence': 1,
            'project_ids': [(4, cls.project.id)],
        })
        cls.stage_in_progress = cls.env['project.task.type'].create({
            'name': 'In Progress',
            'sequence': 2,
            'project_ids': [(4, cls.project.id)],
        })

        # Configure timer for In Progress stage
        cls.timer_config = cls.env['timer.configuration'].create({
            'project_id': cls.project.id,
            'stage_id': cls.stage_in_progress.id,
        })

    def test_timer_start_and_stop_lifecycle(self):
        """Test timer automatically starts on entering configured stage and stops on leaving."""
        # Create task in Draft stage
        task = self.env['project.task'].create({
            'name': 'Test Timer Task',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,
        })

        self.assertFalse(task.task_timer, "Timer should not be active in Draft stage")
        self.assertFalse(task.is_user_working, "User should not be marked as working")
        self.assertEqual(len(task.timesheet_ids), 0, "No timesheets should exist initially")

        # Move task to In Progress stage -> Timer should start
        task.write({'stage_id': self.stage_in_progress.id})
        self.assertTrue(task.task_timer, "Timer should be active in In Progress stage")
        self.assertTrue(task.is_user_working, "User should be marked as working")
        self.assertEqual(len(task.timesheet_ids), 1, "An active timesheet line should be created")

        open_line = task.timesheet_ids.filtered(lambda t: not t.date_end)
        self.assertTrue(open_line, "There should be an open timesheet without date_end")
        self.assertTrue(open_line.date_start, "Timesheet line should have a start date")

        # Test working duration helper
        duration = task.get_working_duration()
        self.assertGreaterEqual(duration, 0, "Working duration should return a valid non-negative number")

        # Move task out of In Progress stage -> Timer should stop
        task.write({'stage_id': self.stage_draft.id})
        self.assertFalse(task.task_timer, "Timer should deactivate when leaving configured stage")
        self.assertFalse(task.is_user_working, "User should no longer be marked as working")

        closed_line = task.timesheet_ids[0]
        self.assertTrue(closed_line.date_end, "Timesheet line must have an end date once stopped")
        self.assertGreaterEqual(closed_line.timer_duration, 0, "Timer duration in minutes should be calculated")
        self.assertGreaterEqual(task.duration, 0, "Task real duration should be persisted")

    def test_timer_disabled_when_setting_turned_off(self):
        """Test timer does not start if the global configuration parameter is disabled."""
        self.env['ir.config_parameter'].sudo().set_param(
            'automatic_project_task_timer.timer_setting', False
        )
        task = self.env['project.task'].create({
            'name': 'Task With Disabled Setting',
            'project_id': self.project.id,
            'stage_id': self.stage_draft.id,
        })

        task.write({'stage_id': self.stage_in_progress.id})
        self.assertFalse(task.task_timer, "Timer should not activate when global setting is disabled")
        self.assertEqual(len(task.timesheet_ids), 0, "No timesheet should be created")
