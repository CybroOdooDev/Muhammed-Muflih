from odoo import models, fields


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    is_force_close = fields.Boolean(
        'Force Close', default=False,
        help="Enable to trigger force cancellation workflow for the linked purchase order.")

    def action_create_returns(self):
        """ Override action_create_returns to set receipt canceled flags and context
        on the purchase order when force close is enabled.
        """
        action = super().action_create_returns()
        purchase_id = self.picking_id.purchase_id
        if self.is_force_close and purchase_id:
            context = dict(action['context'])
            context['is_force_close'] = True
            context['return_purchase_id'] = purchase_id.id
            purchase_id.is_receipt_canceled = True
            purchase_id.force_cancel_receipt = action['res_id']
            action['context'] = context
        return action
