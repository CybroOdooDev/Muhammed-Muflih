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
from odoo import api, fields, models


class MailActivity(models.Model):
    """Inherited mail.activity model mostly to add dashboard functionalities"""
    _inherit = "mail.activity"

    activity_tag_ids = fields.Many2many('activity.tag',
                                        string='Activity Tags',
                                        help='Select activity tags.')
    state = fields.Selection([
        ('planned', 'Planned'),
        ('today', 'Today'),
        ('done', 'Done'),
        ('overdue', 'Overdue')], string='State', help='State of the activity',
        compute='_compute_state', store=True)

    def _action_done(self, feedback=False, attachment_ids=None):
        """Delegate to super _action_done which archives completed activities in Odoo 20"""
        return super()._action_done(feedback=feedback, attachment_ids=attachment_ids)

    @api.model
    def get_activity(self, activity_id=False):
        """Method for returning model and id of activity"""
        if not activity_id:
            return {}
        activity = self.browse(int(activity_id))
        return {
            'model': activity.res_model,
            'res_id': activity.res_id
        }
