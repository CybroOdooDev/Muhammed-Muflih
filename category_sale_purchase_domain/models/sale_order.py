# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_category_ids=fields.Many2many('res.partner.category',string='Customer Categories',related='company_id.customer_category_ids')    




