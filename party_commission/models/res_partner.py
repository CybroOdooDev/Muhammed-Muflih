from odoo import  fields, models

class ResPartner(models.Model):
    _inherit='res.partner'

    party_commission_account_id = fields.Many2one('account.account',string='Party Commission Account')