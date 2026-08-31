# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_receipt_restriction = fields.Boolean(
        string='Receipt Restriction',
        related='pos_config_id.receipt_restriction',
        readonly=False,
        help="Restrict the number of times a receipt can be printed for an order in Point of Sale."
    )
    pos_restriction_limit = fields.Integer(
        string='Restriction Limit',
        related='pos_config_id.restriction_limit',
        readonly=False,
        help="Maximum allowed number of times a receipt can be printed per POS order."
    )
    pos_white_label_receipt = fields.Boolean(
        string='White Label Receipt',
        related='pos_config_id.white_label_receipt',
        readonly=False,
        help="Enable white-label receipt layout with custom header branding and removed Odoo footers."
    )

