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
from datetime import datetime
from odoo import api, fields, models


class Task(models.Model):
    """inherited the 'project.task' for running the timer """
    _inherit = 'project.task'

    task_timer = fields.Boolean(string='Timer', default=False,
                                help='Activated when task configured stage')
    is_user_working = fields.Boolean(string='Is Current User Working',
                                     compute='_compute_is_user_working',
                                     help="Technical field indicating whether "
                                          "the current user is working. ")
    duration = fields.Float(string='Real Duration', store=True, copy=False,
                            compute='_compute_duration', readonly=False,
                            help='Shows the total duration in minutes')
    is_status_stage = fields.Boolean(string='Stage Status',
                                     help='To set the status of task at the '
                                          'initial time.')
    check_stage = fields.Integer(string='Stage',
                                 compute='_compute_check_stage',
                                 help='To check the stage whether it is '
                                      'configured or not')

    @api.depends('timesheet_ids.timer_duration')
    def _compute_duration(self):
        """Compute cumulative duration in minutes from timesheets."""
        for task in self:
            task.duration = sum(task.timesheet_ids.mapped('timer_duration'))

    def _compute_check_stage(self):
        """To check the stage whether it is configured or not, for that
        assigning the configured stage id to this field."""
        for rec in self:
            config = self.env['timer.configuration'].search(
                [('project_id', '=', rec.project_id.id)], limit=1
            )
            rec.check_stage = config.stage_id.id if config else False

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks._update_task_timer_stage()
        return tasks

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' in vals or 'project_id' in vals:
            self._update_task_timer_stage()
        elif 'task_timer' in vals:
            self._handle_timer_toggle()
        return res

    def _update_task_timer_stage(self):
        """Checks the status of timer setting and updates task_timer."""
        timer_setting = self.env['ir.config_parameter'].sudo().get_bool(
            'automatic_project_task_timer.timer_setting')
        for task in self:
            task.is_status_stage = False
            is_timer_stage = False
            if timer_setting and task.project_id:
                config = self.env['timer.configuration'].search(
                    [('project_id', '=', task.project_id.id)], limit=1
                )
                if config and task.stage_id == config.stage_id:
                    is_timer_stage = True
            if task.task_timer != is_timer_stage:
                task.write({'task_timer': is_timer_stage})

    def _compute_is_user_working(self):
        """ Checks whether the current user is working """
        for order in self:
            if order.timesheet_ids.filtered(
                    lambda x: (x.user_id.id == self.env.user.id) and (
                            not x.date_end)):
                order.is_user_working = True
            else:
                order.is_user_working = False

    def _handle_timer_toggle(self):
        """Start or stop timesheet lines when task_timer changes."""
        time_line_obj = self.env['account.analytic.line']
        for rec in self:
            if rec.task_timer:
                open_lines = time_line_obj.search([
                    ('task_id', '=', rec.id),
                    ('user_id', '=', self.env.user.id),
                    ('date_end', '=', False),
                ])
                if not open_lines:
                    time_line_obj.create({
                        'name': '%s : %s' % (self.env.user.name, rec.name),
                        'task_id': rec.id,
                        'user_id': self.env.user.id,
                        'project_id': rec.project_id.id,
                        'date_start': fields.Datetime.now(),
                    })
            else:
                open_lines = time_line_obj.search([
                    ('task_id', '=', rec.id),
                    ('date_end', '=', False),
                ])
                now = fields.Datetime.now()
                for time_line in open_lines:
                    start = time_line.date_start or now
                    diff = now - start.replace(second=0, microsecond=0)
                    total_seconds = max(diff.total_seconds(), 0)
                    time_line.write({
                        'date_end': now,
                        'date_start': start,
                        'timer_duration': round(total_seconds / 60.0, 2),
                        'unit_amount': round(total_seconds / 3600.0, 2),
                    })
                rec.duration = sum(rec.timesheet_ids.mapped('timer_duration'))

    def toggle_start(self):
        """The time sheet record will be created or stopped
        by checking all the conditions."""
        self._handle_timer_toggle()

    def get_working_duration(self):
        """Get the additional duration for 'open times'
        i.e. productivity lines with no date_end."""
        self.ensure_one()
        duration = 0
        now = fields.Datetime.now()
        for time in self.timesheet_ids.filtered(lambda t: not t.date_end):
            if not isinstance(time.date_start, datetime):
                time.date_start = now
            else:
                duration += (now - time.date_start).total_seconds() / 60
        return duration
