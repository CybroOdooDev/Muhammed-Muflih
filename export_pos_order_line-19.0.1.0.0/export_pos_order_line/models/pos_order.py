from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_open_export(self):
        """Open the list view of POS order lines for export."""
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'pos.order.line',
            'target': 'new',
            'views': [[False, 'list']],
        }


class PosOrderLine(models.Model):
    """Inherited pos.order.line model to add related display fields."""

    _inherit = 'pos.order.line'

    order_date = fields.Datetime(related='order_id.date_order')
    pos_reference = fields.Char(related='order_id.pos_reference')
    order_reference = fields.Char(related='order_id.name', string="POS Order Reference")
    categ_id = fields.Many2one(related='product_id.categ_id')
    product_list_price = fields.Float(related='product_id.list_price')

