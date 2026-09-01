from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    pos_order_limit = fields.Integer('Total Limit', default=9999,help='POS Order Total Limit')


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pos_order_limit = fields.Integer('Total Limit', default=9999,help='POS Order Total Limit')
