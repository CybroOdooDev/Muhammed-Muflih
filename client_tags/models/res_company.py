# -*- coding: utf-8 -*-

from odoo import models, fields
class ResCompany(models.Model):
    _inherit = 'res.company'

    customer_tag_ids = fields.Many2many('res.partner.category', 'res_company_customer_tag_rel','company_id', 'tag_id',string='Customer Tags')
    vendor_tag_ids = fields.Many2many('res.partner.category', 'res_company_vendor_tag_rel','company_id', 'tag_id',string='Vendor Tags')