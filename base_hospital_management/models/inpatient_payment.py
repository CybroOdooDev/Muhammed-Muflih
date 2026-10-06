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
from odoo import fields, models


class InpatientPayment(models.Model):
    """Class holding Payment details of Inpatient"""
    _name = 'inpatient.payment'
    _description = "Inpatient Payments"

    name = fields.Char(string='Name', help='Name of payment')
    subtotal = fields.Float(string='Subtotal', help='Total payment')
    inpatient_id = fields.Many2one('hospital.inpatient',
                                   string='Inpatient',
                                   help='Inpatient related to the payment')
    date = fields.Datetime(string='Date', help="Date of payment")
    tax_ids = fields.Many2many('account.tax', string='Tax',
                               help='Tax for the test')
