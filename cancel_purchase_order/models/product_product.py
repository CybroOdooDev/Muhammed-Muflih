from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'


    def _prepare_out_svl_vals(self, quantity, company, lot=False):
        """ Prepare outgoing stock valuation layer values and update product
        standard price when force close context is set.
        """
        vals = super()._prepare_out_svl_vals(quantity, company, lot)
        if self._context.get('is_force_close') and self._context.get('return_purchase_id'):
            purchase_id = self.env['purchase.order'].browse(self._context.get('return_purchase_id'))
            order_line = purchase_id.order_line.filtered(lambda x: x.product_id.id == self.id)
            if purchase_id.currency_id != purchase_id.company_id.currency_id:
                unit_cost = purchase_id.currency_id._convert(
                    order_line.price_unit,
                    purchase_id.company_id.currency_id,
                    purchase_id.company_id,
                    purchase_id.date_order
                )
                unit_value = unit_cost * vals['quantity']
            else:
                unit_cost = order_line.price_unit
                unit_value = order_line.price_unit * vals['quantity']
            vals['unit_cost'] = unit_cost
            vals['value'] = unit_value
            self._force_update_product_standard(purchase_id)
        return vals

    def _force_update_product_standard(self, purchase_id):
        """ Restore the product standard cost from the purchase order cost history snapshot.
        """
        history_id = purchase_id.cost_history_id.line_ids.filtered(
            lambda x:  x.product_id.id == self.id)
        if history_id:
            self.with_company(self.env.company).write({
                'standard_price': history_id.standard_cost
            })
