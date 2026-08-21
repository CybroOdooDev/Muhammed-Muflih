# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    customer_category_ids = fields.Many2many(
        'res.partner.category', string='Customer Categories',
        relation='rel_sale_partner_category',column1='rec_id',column2='tag_id',help="Categories related to sale partner")
    vendor_category_ids = fields.Many2many(
        'res.partner.category', string='Vendor Categories',
        relation='rel_purchase_partner_category',column1='rec_id',column2='tag_id',help="Categories related to purchase partner")
