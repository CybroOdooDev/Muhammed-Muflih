# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class ReportResult(models.TransientModel):
    _name = 'report.result'
    _description = 'Report Result'

    date = fields.Date(string='Date')
    voucher = fields.Char(string='Voucher')
    customer_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    salesman_id = fields.Many2one('hr.employee', string='Salesman')
    qty = fields.Float(string='Qty')
    rate = fields.Float(string='Rate')
    net_sales = fields.Float(string='Net Sales')
    cogs = fields.Float(string='COGS')
    printing_charges = fields.Float(string='Printing Charges')
    party_commission = fields.Float(string='Party Commission')
    profit = fields.Float(string='Profit')
    profit_percentage = fields.Float(string='Profit %')
    wizard_id = fields.Many2one('profit.report.wizard', string='Wizard')
