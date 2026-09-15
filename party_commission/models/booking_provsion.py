from odoo import api, fields, models, _

class BookingProvsion(models.Model):
    _name = 'booking.provsion'
    _description = 'Booking Provsion'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'), tracking=True)
    customer_ids = fields.Many2many('res.partner', string='Customers')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    line_ids = fields.One2many('booking.provsion.line', 'booking_provision_id', string='Commission Lines')
    commission_percentage_on_sales = fields.Float(
        string='Commission percentage on sales',
        compute='_compute_commission_percentage_on_sales',
        store=True
    )
    state = fields.Selection([('draft', 'Draft'),('to_review', 'To Review'),('confirmed', 'Confirmed'),], default='draft', tracking=True)

    move_id = fields.Many2one('account.move', string='Journal Entry', copy=False, readonly=True)
    journal_line_ids = fields.One2many('booking.provsion.journal.line', 'booking_provision_id', string='Journal Lines')

    def action_to_review(self):
        for rec in self:
            rec.state = 'to_review'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
            if not rec.move_id:
                journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
                account = self.env['account.account'].search([('deprecated', '=', False)], limit=1)
                move_vals = {
                    'move_type': 'entry',
                    'date': fields.Date.today(),
                    'ref': rec.name,
                }
                if journal:
                    move_vals['journal_id'] = journal.id
                if account:
                    move_vals['line_ids'] = [
                        (0, 0, {
                            'name': _('Party Commission - %s') % rec.name,
                            'account_id': account.id,
                            'debit': 0.0,
                            'credit': 0.0,
                        }),
                        (0, 0, {
                            'name': _('Party Commission - %s') % rec.name,
                            'account_id': account.id,
                            'debit': 0.0,
                            'credit': 0.0,
                        }),
                    ]
                move = self.env['account.move'].create(move_vals)
                rec.move_id = move.id

            if not rec.journal_line_ids:
                account = self.env['account.account'].search([('deprecated', '=', False)], limit=1)
                self.env['booking.provsion.journal.line'].create([
                    {
                        'booking_provision_id': rec.id,
                        'date': fields.Date.today(),
                        'account_id': account.id if account else False,
                        'debit': 0.0,
                        'credit': 0.0,
                    }
                ])

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_view_journal_entry(self):
        self.ensure_one()
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }

    @api.depends('line_ids.net_sales', 'line_ids.net_commission')
    def _compute_commission_percentage_on_sales(self):
        for rec in self:
            total_sales = sum(rec.line_ids.mapped('net_sales'))
            total_commission = sum(rec.line_ids.mapped('net_commission'))
            rec.commission_percentage_on_sales = (total_commission * 100.0 / total_sales) if total_sales else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('booking.provsion') or _('New')
        return super().create(vals_list)





