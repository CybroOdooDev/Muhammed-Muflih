from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'list_price' in vals:
            for template in self:
                for variant in template.product_variant_ids:
                    message = {
                        "value": {
                            'charge_id': variant.id,
                            'lst_price': variant.lst_price,
                        },
                        "channel": 'POS_PRODUCT_PRICE_UPDATE',
                    }
                    self.env["bus.bus"]._sendone('POS_PRODUCT_PRICE_UPDATE', "notification_pos_realtime_price", message)
        return res