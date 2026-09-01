# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_order_limit = fields.Integer(
        related='pos_config_id.pos_order_limit', readonly=False,help='POS Order Total Limit')
