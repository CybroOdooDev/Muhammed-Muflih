# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class AccountReconciled(models.Model):
    _name = 'account.reconciled'
    _description = 'Account Reconciled'

    payment_id = fields.Many2one('account.payment', string='Payment Ref',
                                 required=True)
    move_line_id = fields.Many2one('account.move.line',
                                   string='Account Move Line', required=True)
    move_name = fields.Char(related='move_line_id.move_name', string='Number')
    name = fields.Char(related='move_line_id.name', string='Label')
    total_amount = fields.Float(string="Total Amount")
    # amount_due = fields.Float(string="Amount Due")
    amount = fields.Float(string='Amount')
    partner_currency_id = fields.Many2one('res.currency')
    # partner_amount = fields.Float(string='Foreign Currency')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,)