from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_refunded_or_refund_order = fields.Boolean('Is Refunded/Refund Order')

    def update_refund_status(self):
        matching = ['REFUND', 'استرداد الأموال']
        order_ids = self.search(['|', ('name', 'ilike', matching[0]),
                                 ('name', 'ilike', matching[1])])
        order_ids.write({'is_refunded_or_refund_order': True})
        for order in order_ids:
            refunded_order_ids = order.mapped(
                'lines.refunded_orderline_id.order_id')
            for rec in refunded_order_ids:
                rec.write({'is_refunded_or_refund_order': True})

    def get_refund_info(self):
        return True if self.refund_orders_count > 0 or len(
            self.refunded_order_id) > 0 else False


class PosOrderReport(models.AbstractModel):
    _name = 'report.pos_order_pdf_report.pos_order_report_template'
    _description = 'Pos Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        order_ids = self.env['pos.order'].browse(docids)
        has_refund_print_access = self.env.user.has_group(
            'pos_order_pdf_report.group_pos_refund_user')
        if not has_refund_print_access:
            order_ids = order_ids.filtered(
                lambda order: not order.get_refund_info())
        if order_ids:
            return {
                'docs': order_ids,
                'doc_model': 'pos.order',
                'data': data,
            }
        else:
            raise ValidationError(
                "You can't print the Refund or Refunded Orders")
