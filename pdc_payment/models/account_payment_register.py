from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        return super(
            AccountPaymentRegister,
            self.with_context(from_payment_register=True)
        ).action_create_payments()
