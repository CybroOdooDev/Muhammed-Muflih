# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    receipt_restriction = fields.Boolean(
        string='Receipt Restriction',
        default=True,
        help="Restrict the number of times a receipt can be printed for an order in Point of Sale."
    )
    restriction_limit = fields.Integer(
        string='Restriction Limit',
        default=1,
        help="Maximum allowed number of times a receipt can be printed per POS order."
    )
    white_label_receipt = fields.Boolean(
        string='White Label Receipt',
        default=False,
        help="Enable white-label receipt layout with custom header branding and removed Odoo footers."
    )

