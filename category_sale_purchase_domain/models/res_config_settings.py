# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_customer_category_ids = fields.Many2many(
        'res.partner.category',
        string='Customer Categories',
        related='company_id.customer_category_ids', readonly=False,help="Categories related to customer")
    company_vendor_category_ids = fields.Many2many(
        'res.partner.category',
        string='Vendor Categories',
        related='company_id.vendor_category_ids', readonly=False,help="Categories related to vendor")




