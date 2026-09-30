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
    total_profit_percentage = fields.Float(
        string='Total Profit %',
        compute='_compute_total_profit_percentage',
        store=True
    )
    state = fields.Selection([('draft', 'Draft'),('to_review', 'To Review'),('confirmed', 'Confirmed'),('done','Done')], default='draft', tracking=True)
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
    commission_percentage = fields.Float(string='Commission Percentage')

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

    def apply_commission_to_all(self):
    
        if self.line_ids:
            for rec in self.line_ids:
                if rec.commission_percentage:
                    raise UserError(_("Commission percentage is already set"))
                if self.commission_percentage:
                  rec.commission_value=0
                  rec.commission_percentage=self.commission_percentage

    is_journal_readonly = fields.Boolean(
        string='Is Journal Readonly',
        compute='_compute_is_journal_readonly'
    )

    @api.depends('state', 'move_id')
    @api.depends_context('uid')
    def _compute_is_journal_readonly(self):
        is_invoicing = self.env.user.has_group('account.group_account_invoice')
        for rec in self:
            if rec.state == 'confirmed' and not rec.move_id and is_invoicing:
                rec.is_journal_readonly = False
            else:
                rec.is_journal_readonly = True

    def action_to_review(self):
        for rec in self:
            rec.write({'state': 'to_review'})

    def write(self, vals):
        if not self.env.su:
            is_invoicing = self.env.user.has_group('account.group_account_invoice')
            allowed_confirmed_keys = {'journal_id', 'date', 'journal_line_ids', 'state'}
            for rec in self:
                if rec.state == 'done':
                    raise UserError(_("You cannot modify a Booking Provision record that is in 'Done' state."))
                if rec.state == 'confirmed':
                    if rec.move_id:
                        raise UserError(_("You cannot modify a confirmed Booking Provision record."))
                    if not is_invoicing:
                        raise UserError(_("Only users with Accounting: Invoicing rights can edit journal details in Confirmed state."))
                    if not set(vals.keys()).issubset(allowed_confirmed_keys):
                        raise UserError(_("You cannot modify non-journal fields of a confirmed Booking Provision record."))

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
                                'label': line.label,
                                'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False,
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
        self.write({'state': 'confirmed'})

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

    @api.depends('line_ids.net_sales', 'line_ids.profit')
    def _compute_total_profit_percentage(self):
        for rec in self:
            total_sales = sum(rec.line_ids.mapped('net_sales'))
            total_profit = sum(rec.line_ids.mapped('profit'))
            rec.total_profit_percentage = (total_profit * 100.0 / total_sales) if total_sales else 0.0

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
            journal = self.env.ref('account.1_general', raise_if_not_found=False)
        if not journal:
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

        allowed_partners = records.mapped('customer_ids') | records.mapped('line_ids.customer_id')

        # Check if selected records already have journal lines on the record
        existing_jlines = records.filtered('journal_line_ids')[:1].journal_line_ids if records else False
        line_vals = []
        if existing_jlines:
            for jline in existing_jlines:
                line_vals.append((0, 0, {
                    'account_id': jline.account_id.id,
                    'partner_id': jline.partner_id.id if jline.partner_id else False,
                    'label': getattr(jline, 'label', False),
                    'analytic_account_id': jline.analytic_account_id.id if jline.analytic_account_id else False,
                    'debit': jline.debit or 0.0,
                    'credit': jline.credit or 0.0,
                }))
        else:
            # Prefill from each record's customer party_commission_account_id and net_commission
            for rec in records:
                partners = rec.customer_ids or rec.line_ids.mapped('customer_id')
                if partners:
                    for partner in partners:
                        partner_lines = rec.line_ids.filtered(lambda l: l.customer_id == partner)
                        net_comm = sum(partner_lines.mapped('net_commission')) if partner_lines else sum(rec.line_ids.mapped('net_commission'))
                        currency = rec.currency_id or self.env.company.currency_id
                        credit_val = currency.round(net_comm) if currency else round(net_comm, 2)
                        account = partner.party_commission_account_id
                        line_vals.append((0, 0, {
                            'account_id': account.id if account else False,
                            'partner_id': partner.id,
                            'label': f"Party Commission - {partner.name}" if partner.name else (rec.name or ''),
                            'analytic_account_id': False,
                            'debit': 0.0,
                            'credit': credit_val,
                        }))
                else:
                    net_comm = sum(rec.line_ids.mapped('net_commission'))
                    if net_comm:
                        currency = rec.currency_id or self.env.company.currency_id
                        credit_val = currency.round(net_comm) if currency else round(net_comm, 2)
                        line_vals.append((0, 0, {
                            'account_id': False,
                            'partner_id': False,
                            'label': rec.name or '',
                            'analytic_account_id': False,
                            'debit': 0.0,
                            'credit': credit_val,
                        }))

        wizard = self.env['create.journal.wizard'].create({
            'booking_provision_ids': [(6, 0, records.ids)],
            'journal_id': journal.id if journal else False,
            'date': records[0].date or fields.Date.context_today(self),
            'allowed_partner_ids': [(6, 0, allowed_partners.ids)],
            'line_ids': line_vals,
        })

        return {
            'name': _('Create Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'create.journal.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }
