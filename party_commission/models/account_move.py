from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_ids = fields.Many2many(
        'account.move',
        'account_move_invoice_rel',
        'move_id',
        'invoice_id',
        string='Invoices',
        domain="[('move_type', '=', 'out_invoice')]"
    )
