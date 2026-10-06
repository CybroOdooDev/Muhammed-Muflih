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
from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    """
    Adding inpatient field to invoicing model.
    """
    _inherit = "account.payment.register"

    @api.model
    def create(self, vals_list):
        """Create records to inpatient payment"""
        for vals in vals_list:
            self.env['inpatient.payment'].sudo().create({
                'name': vals['communication'],
                'subtotal': vals['amount'],
                'inpatient_id': self.env['hospital.inpatient'].sudo().search([(
                    'patient_id', '=', vals['partner_id'])],
                    order='create_date desc', limit=1).id,
                'date': vals['payment_date']
            })
        return super().create(vals_list)
