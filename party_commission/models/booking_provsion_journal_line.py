from odoo import fields, models

class BookingProvsionJournalLine(models.Model):
    _name = 'booking.provsion.journal.line'
    _description = 'Booking Provision Journal Line'

    booking_provision_id = fields.Many2one('booking.provsion', string='Booking Provision', ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    account_id = fields.Many2one('account.account', string='Account')
    debit = fields.Float(string='Debit', default=0.0)
    credit = fields.Float(string='Credit', default=0.0)
