from odoo import models, fields


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    is_force_close = fields.Boolean(
        'Force Close', default=False,
        help="Enable to trigger force cancellation workflow for the linked purchase order.")

    def refund_moves(self):
        """ Override refund_moves to set bill canceled flags on purchase order
        when force close is enabled on reversal wizard.
        """
        action = super().refund_moves()
        purchase_id = self.move_ids.line_ids.purchase_line_id.order_id
        if self.is_force_close and purchase_id:
            purchase_id.is_bill_canceled = True
            purchase_id.force_cancel_bill = action['res_id']
        return action
