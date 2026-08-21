# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveLine(models.Model):
    """Inherited the model account.move.line and override the compute
    function _compute_quantity"""
    _inherit = 'account.move.line'

    @api.depends('display_type')
    def _compute_quantity(self):
        """Changes the actual functionality of _compute_quantity function in
        accordance"""
        for line in self:
            line.quantity = line.quantity if line.display_type == 'product' else False
