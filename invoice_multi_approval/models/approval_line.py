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
from odoo import _, fields, models
from odoo.exceptions import UserError


class ApprovalLine(models.Model):
    """This class creates a model 'approval.line' and adds fields"""
    _name = 'approval.line'
    _description = 'Approval Line In Move'

    move_id = fields.Many2one(
        'account.move',
        string="Approval lines",
        ondelete='cascade',
        help="Approval line",
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        help="Approver of the invoice",
    )
    approval_status = fields.Boolean(
        string='Status',
        help="Status of approvals",
    )

    def write(self, vals):
        """Prevent approvers from modifying approval status of other users."""
        if 'approval_status' in vals and not self.env.is_admin():
            is_manager = self.env.user.has_group(
                'invoice_multi_approval.group_approve_manager'
            )
            for line in self:
                if line.approver_id != self.env.user and not is_manager:
                    raise UserError(
                        _("You cannot approve or modify approval lines of "
                          "other users.")
                    )
        return super().write(vals)
