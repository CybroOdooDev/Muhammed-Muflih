from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'lst_price' in vals or 'list_price' in vals:
            for product in self:
                message = {
                    "value": {
                        'charge_id': product.id,
                        'lst_price': product.lst_price,
                    },
                    "channel": 'POS_PRODUCT_PRICE_UPDATE',
                }
                self.env["bus.bus"]._sendone('POS_PRODUCT_PRICE_UPDATE', "notification_pos_realtime_price", message)
        return res

