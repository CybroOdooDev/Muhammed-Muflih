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


class IrAttachment(models.Model):
    """Inherited for making the attachments public"""
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        """update the public field of the attachment"""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            vals['public'] = True

        return super().create(vals_list)
