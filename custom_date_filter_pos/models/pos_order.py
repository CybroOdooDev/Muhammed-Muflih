from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    customer_phone = fields.Char(
        'Customer Mobile',
        compute='_compute_customer_phone',
        search='_search_customer_phone',
        help="phone number"
    )

    @api.depends('partner_id.phone')
    def _compute_customer_phone(self):
        """Compute customer phone number from the linked partner record."""
        for order in self:
            order.customer_phone =  order.partner_id.phone or False

    def _search_customer_phone(self, operator, value):
        """Search domain implementation for customer_phone field filtering."""
        return [('partner_id.phone', operator, value)]


