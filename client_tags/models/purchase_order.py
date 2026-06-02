from odoo import fields, models
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    vendor_tags_ids = fields.Many2many(related='company_id.vendor_tag_ids', string='vendor Tags')
