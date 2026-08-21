# -*- coding: utf-8 -*-
from odoo import models, fields



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vendor_category_ids=fields.Many2many('res.partner.category',string='Vendor Categories',related='company_id.vendor_category_ids')



   

    




