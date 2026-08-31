# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pos_show_logo_on_receipt = fields.Boolean(
        string='Show Logo on POS Receipt',
        default=False,
        help="When enabled, this customer's image will be printed on the POS receipt "
             "whenever they are selected on an order.",
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Expose only the boolean toggle to the POS frontend.
        image_1920 is already loaded by default in POS partner data."""
        result = super()._load_pos_data_fields(config_id)
        result += ['pos_show_logo_on_receipt','image_1920']
        return result
