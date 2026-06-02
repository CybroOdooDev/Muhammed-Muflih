# -*- coding: utf-8 -*-
from odoo import fields, models
class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"


    customer_tag_ids =fields.Many2many(related='company_id.customer_tag_ids', readonly=False,string='Customer Tags')
    vendor_tag_ids = fields.Many2many( related='company_id.vendor_tag_ids',readonly=False,string='Vendor Tags')