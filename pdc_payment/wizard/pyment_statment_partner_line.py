from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PaymentStatementPartnerLine(models.TransientModel):
    _name = "payment.statement.partner.line"
    _description = "Payment Statement Partner Line"

    statement_id = fields.Many2one('payment.statement', string="Statement", ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string="Name", required=True)

    @api.onchange('partner_id')
    def mail_checking(self):
        if self.partner_id and not self.partner_id.email:
            raise UserError(_("Selected partner '%s' does not have an email address. Please add an email address to this partner.") % self.partner_id.name)




