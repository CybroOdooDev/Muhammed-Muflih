# -*- coding: utf-8 -*-
from odoo import models, fields


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    bank_fee_account = fields.Many2one('account.account', string='Bank Fee Account',help="Bank Fee Account")
    bank_fee = fields.Float(string='Bank Fee (%)',help="Bank Fee percentage")
    bank_fee_fixed = fields.Float(string='Bank Fee Fixed',help="Bank Fee Fixed")
