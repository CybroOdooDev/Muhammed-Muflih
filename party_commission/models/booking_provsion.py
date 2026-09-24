# -- coding: utf-8 --
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class BookingProvsion(models.Model):
    _name = 'booking.provsion'
    _description = 'Booking Provsion'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'), tracking=True)
    customer_ids = fields.Many2many('res.partner', string='Customers')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    sales_excutive_id = fields.Many2one('hr.employee', string='Sales Executive')
    party_records = fields.Many2many(
        'booking.provsion',
        'booking_provision_rel',
        'provision_id',
        'related_provision_id',
        string='Party Records'
    )
    line_ids = fields.One2many('booking.provsion.line', 'booking_provision_id', string='Commission Lines')
    journal_line_ids = fields.One2many('booking.provsion.journal.line', 'booking_provision_id', string='Journal Lines')
    allowed_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_allowed_partner_ids',
        string='Allowed Partners'
    )
    commission_percentage_on_sales = fields.Float(
        string='Commission percentage on sales',
        compute='_compute_commission_percentage_on_sales',
        store=True
    )
    state = fields.Selection([('draft', 'Draft'),('to_review', 'To Review'),('confirmed', 'Confirmed'),], default='draft', tracking=True)
    all_party_confirmed = fields.Boolean(
        string='All Linked Records Confirmed',
        compute='_compute_all_party_confirmed'
    )

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    date = fields.Date(string='Journal Date', default=fields.Date.context_today)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain="[('type', '=', 'general')]",
        default=lambda self: self._default_journal_id()
    )
    move_id = fields.Many2one('account.move', string='Journal Entry', copy=False, readonly=True)

    @api.depends('state', 'party_records.state')
    def _compute_all_party_confirmed(self):
        for rec in self:
            records = rec.party_records or rec
            rec.all_party_confirmed = all(r.state == 'confirmed' for r in records)

    @api.model
    def _default_journal_id(self):
        journal = self.env.ref('account.1_general', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
        if not journal:
            journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        return journal

    @api.depends('party_records.customer_ids', 'customer_ids')
    def _compute_allowed_partner_ids(self):
        for rec in self:
            partners = rec.party_records.mapped('customer_ids') | rec.customer_ids
            rec.allowed_partner_ids = partners

    def action_to_review(self):
        for rec in self:
            records = rec.party_records or rec
            lines_copy = []
            processed_partners = set()

            for r in records:
                partners = r.customer_ids or r.line_ids.mapped('customer_id')
                for partner in partners:
                    if partner.id in processed_partners:
                        continue
                    processed_partners.add(partner.id)

                    partner_records = records.filtered(
                        lambda p: partner in p.customer_ids or partner in p.line_ids.mapped('customer_id')
                    )
                    net_comm_total = sum(partner_records.mapped('line_ids').mapped('net_commission'))

                    account = partner.property_account_payable_id
                    if not account:
                        account = self.env['account.account'].search([
                            ('account_type', '=', 'liability_payable'),
                            ('company_id', '=', self.env.company.id)
                        ], limit=1)

                    if account:
                        lines_copy.append((0, 0, {
                            'account_id': account.id,
                            'partner_id': partner.id,
                            'debit': 0.0,
                            'credit': net_comm_total,
                        }))

            rec.write({'state': 'to_review'})
            if lines_copy:
                records.write({'journal_line_ids': [(5, 0, 0)] + lines_copy})

    def write(self, vals):
        if not self.env.su:
            for rec in self:
                records = rec.party_records or rec
                all_confirmed = all(r.state == 'confirmed' for r in records)
                if all_confirmed and any(k != 'state' for k in vals.keys()):
                    raise UserError(_("You cannot modify a confirmed Booking Provision record."))

        res = super().write(vals)
        if not self.env.context.get('skip_party_records_sync'):
            sync_fields = {'journal_line_ids', 'date', 'journal_id'}
            if sync_fields.intersection(vals.keys()):
                for rec in self:
                    related = rec.party_records - rec
                    if related:
                        sync_vals = {}
                        if 'journal_id' in vals:
                            sync_vals['journal_id'] = rec.journal_id.id if rec.journal_id else False
                        if 'date' in vals:
                            sync_vals['date'] = rec.date
                        if 'journal_line_ids' in vals:
                            lines_copy = [(0, 0, {
                                'account_id': line.account_id.id,
                                'partner_id': line.partner_id.id if line.partner_id else False,
                                'debit': line.debit,
                                'credit': line.credit,
                            }) for line in rec.journal_line_ids]
                            sync_vals['journal_line_ids'] = [(5, 0, 0)] + lines_copy

                        if sync_vals:
                            related.with_context(skip_party_records_sync=True).write(sync_vals)
        return res

    def unlink(self):
        raise UserError(_("Deleting Booking Provision records is not allowed."))

    def action_confirm(self):
        for rec in self:
            if not rec.journal_id:
                raise UserError(_("Please configure a Journal before confirming."))
            if not rec.journal_line_ids:
                raise UserError(_("Please add at least one Journal Line before confirming."))

            total_debit = sum(rec.journal_line_ids.mapped('debit'))
            total_credit = sum(rec.journal_line_ids.mapped('credit'))
            if not float_is_zero(total_debit - total_credit, precision_rounding=rec.currency_id.rounding or 0.01):
                raise UserError(_("Cannot confirm: Total Debit (%.2f) does not equal Total Credit (%.2f).") % (total_debit, total_credit))

            rec.write({'state': 'confirmed'})

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_view_journal_entry(self):
        self.ensure_one()
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(False, 'form')],
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

    def create_journal_entry(self):
        active_ids = self.env.context.get('active_ids')
        records = self.env['booking.provsion'].browse(active_ids) if active_ids else self
        if not records:
            raise UserError(_("No records selected."))

        references = set(records.mapped('name'))
        if len(references) > 1:
            raise UserError(_("Please select records with the same reference."))

        if any(rec.state != 'confirmed' for rec in records):
            raise UserError(_("Please select records that are in Confirmed state."))

        if any(rec.move_id for rec in records):
            raise UserError(_("A Journal Entry has already been created for one or more selected records."))

        journal = records[0].journal_id
        if not journal:
            raise UserError(_("Please configure a Journal before creating a journal entry."))

        journal_lines = records[0].journal_line_ids
        if not journal_lines:
            raise UserError(_("No journal lines defined on the Booking Provision."))

        total_net_commission = sum(records.mapped('line_ids').mapped('net_commission'))

        move_lines = []
        for jline in journal_lines:
            if jline.partner_id:
                partner_records = records.filtered(
                    lambda r: jline.partner_id in r.customer_ids or jline.partner_id in r.line_ids.mapped('customer_id')
                )
                net_comm = sum(partner_records.mapped('line_ids').mapped('net_commission')) if partner_records else (jline.credit or 0.0)
                debit = jline.debit or 0.0
                credit = net_comm if partner_records or not jline.credit else jline.credit
                partner_id = jline.partner_id.id
            else:
                debit = total_net_commission if total_net_commission else (jline.debit or 0.0)
                credit = jline.credit or 0.0
                partner_id = False

            jline.sudo().write({
                'debit': debit,
                'credit': credit,
            })

            move_lines.append((0, 0, {
                'account_id': jline.account_id.id,
                'partner_id': partner_id,
                'debit': debit,
                'credit': credit,
                'name': records[0].name,
            }))

        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': records[0].date or fields.Date.context_today(self),
            'ref': records[0].name,
            'move_type': 'entry',
            'line_ids': move_lines,
        })
        move.action_post()
        records.sudo().write({'move_id': move.id})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Journal entry created successfully'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'name': _('Journal Entry'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'views': [(False, 'form')],
                    'view_mode': 'form',
                    'res_id': move.id,
                    'target': 'current',
                }
            }
        }
