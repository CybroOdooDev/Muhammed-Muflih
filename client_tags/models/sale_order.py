from odoo import fields, models,api
class Sale_Order(models.Model):
    _inherit = 'sale.order'

    custom_tags_ids=fields.Many2many(related='company_id.customer_tag_ids',string='Customer Tags')




