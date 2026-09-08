    # -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, Command
from odoo.exceptions import ValidationError, UserError
from odoo.addons.account.models.account_payment import AccountPayment


class AccountPayment(models.Model):
    """ This model represents account.payment."""
    _inherit = 'account.payment'

    pdc_payment = fields.Boolean("Cheque Payment", help="Is cheque payment")
    maturity_date = fields.Date(string="Maturity Date", help="Cheque date")
    cheque_no = fields.Char(string="Cheque Number", help="Cheque Number")
    bank_account_id = fields.Many2one('account.account', string='Account',
                                   related="journal_id.default_account_id",
                                   help="Account Number")
    bank_name = fields.Char(string="Bank Name", help="Bank Name")
    move_line_ids = fields.Many2many(
        'account.move.line',
        relation='rel_payment_move_line', copy=False, store=True, readonly=False)
    # compute = '_compute_is_reconcile_line',
    is_reconcile_line = fields.Boolean(
        string='Reconcile line',)
    new_reference = fields.Float(string='New Reference', compute='_compute_new_reference', store=True, readonly=False)
    reconciled_entry_ids = fields.Many2many('account.reconciled', copy=False)
    remaining_reconciled = fields.Float(string='Remaining Reconciled Amount',
                                        copy=False)
    already_paying = fields.Float(string="Already Paid", copy=False)
    reconcile_button = fields.Boolean(string="Reconcile Button Is Visible",
                                      compute="_compute_reconcile_button")
    is_vendor_account_payment = fields.Boolean(string='Vendor Account Payment',
                                               help="Payment based on vendor account instead of partner",default=False)
    vendor_account_id = fields.Many2one(comodel_name='account.account',
                                        string='Vendor Account',help="Vendor account for account-based payment",)
    custom_payment = fields.Boolean(string="Custom Payment",default=False)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        """CORE FUNCTION - Adds vendor account to journal entries"""
        line_vals_list = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance
        )

        if self.is_vendor_account_payment and self.vendor_account_id and len(line_vals_list) >= 2:
            line_vals_list[1]['account_id'] = self.vendor_account_id.id
            line_vals_list[0]['partner_id'] = False
            line_vals_list[1]['partner_id'] = False

        return line_vals_list

    @api.depends('company_id', 'partner_id', 'pdc_payment')
    def _compute_journal_id(self):
        for payment in self:
            # If pdc_payment is True, blank the journal_id
            if payment.pdc_payment:
                payment.journal_id = False
                continue

            company = payment.company_id or self.env.company

            # Only set default journal if journal_id is false (for non-PDC payments)
            if payment.journal_id:
                continue

            # Try to get the account.1_cash journal first
            try:
                cash_journal = self.env.ref('account.1_cash')
                if cash_journal and cash_journal.company_id == company:
                    payment.journal_id = cash_journal
                    continue
                else:
                    pass
            except ValueError:
                pass

            # default customer payment method logic
            partner = payment.partner_id
            payment_type = payment.payment_type if payment.payment_type in ('inbound', 'outbound') else None
            if not bool(payment._origin) and (partner or payment_type):
                try:
                    field_name = f'property_{payment_type}_payment_method_line_id'
                    default_payment_method_line = payment.partner_id.with_company(payment.company_id)[field_name]
                    journal = default_payment_method_line.journal_id
                    if journal:
                        payment.journal_id = journal
                        continue
                except Exception:
                    pass

            # Fallback to the first available journal
            if not payment.journal_id or company != payment.journal_id.company_id:
                fallback_journal = self.env['account.journal'].search([
                    ('company_id', '=', company.id),
                    ('type', 'in', ['bank', 'cash', 'credit']),
                ], limit=1)
                payment.journal_id = fallback_journal

    @api.depends('already_paying', 'remaining_reconciled', 'state')
    def _compute_reconcile_button(self):
        for rec in self:
            if (rec.state == 'in_process' and rec.remaining_reconciled != 0):
                rec.reconcile_button = True
            else:
                rec.reconcile_button = False

    @api.depends('amount', 'reconciled_invoice_ids', 'state', 'move_line_ids.adjusted_amount_residual_currency')
    def _compute_new_reference(self):
        for rec in self:
            if rec.state == 'draft':
                adjusted_amount = sum(rec.move_line_ids.mapped('adjusted_amount_residual_currency'))
                rec.new_reference = rec.amount - adjusted_amount
            elif rec.reconciled_invoice_ids:
                payment_amount = 0.0
                for inv in rec.reconciled_invoice_ids:
                    if inv.invoice_payments_widget:
                        widget_data = inv.invoice_payments_widget if isinstance(inv.invoice_payments_widget, dict) else json.loads(inv.invoice_payments_widget)
                        if widget_data.get('content'):
                            for payment in widget_data['content']:
                                if payment.get('account_payment_id') == rec.id:
                                    payment_amount += payment.get('amount', 0.0)
                rec.new_reference = rec.amount - payment_amount
            else:
                adjusted_amount = sum(rec.move_line_ids.mapped('adjusted_amount_residual_currency'))
                rec.new_reference = rec.amount - adjusted_amount

    def action_reconciled_entry(self):
        return {
            'type': 'ir.actions.act_window',
            'name': ('Reconciled Entries'),
            'view_mode': 'list',
            'res_model': 'account.reconciled',
            'domain': [('payment_id', '=', self.id)],
            "target": 'current',
            "context": {'default_payment_id': self.id},
        }


    def action_post(self):
        """
            Move the record to the 'Posted'
            state and recalculate balance amount.
        """
        res = super().action_post()
    #     self.calculate_balance_amount()
    #     if self.pdc_payment:
        if self.env.context.get('from_payment_register'):
            return res
        if self.move_line_ids and self.custom_payment:
            paying = self.move_line_ids.mapped('adjusted_amount_residual')
            total = sum(paying) + self.new_reference
            if round(total, 2) != self.amount:
                raise ValidationError(
                    "Payment amount and paying amount must be equal"
                )

            self.remaining_reconciled = self.amount
            self.action_reconcile()
        return res
    #

    @api.onchange('partner_id', 'payment_type')
    def _onchange_is_reconcile_line(self):
        """Function to compute movelines based on selected partner"""
        payment_type = {
            'inbound': [['out_invoice'], 'asset_receivable'],
            'outbound': [['in_invoice'], 'liability_payable']
        }
        for rec in self:
            if rec.partner_id:
                rec.move_line_ids = self.env['account.move.line'].search([
                    ('account_id.account_type', '=',
                     payment_type[rec.payment_type][1]),
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_id', '!=', rec.move_id.id),
                    ('payment_id', '=', False),
                    ('move_type', 'in', payment_type[rec.payment_type][0]),
                    ('amount_residual', '!=', 0),
                    ('parent_state', '=', 'posted'),
                    ('currency_id', '=', rec.currency_id.id)
                ], order='date ASC')
                rec.is_reconcile_line = True if rec.move_line_ids else False
            else:
                rec.is_reconcile_line = False
                rec.move_line_ids = False

    # @api.onchange('move_line_ids')
    # def _onchange_move_line_ids_validation(self):
        # """Validate that adjusted_amount_residual_currency doesn't exceed amount_residual"""
        # for line in self.move_line_ids:
            # print("aaaaaaaaaaaa")
            # if line.adjusted_amount_residual_currency > line.amount_residual:
                # raise UserError(
                    # f"Payment amount ({line.adjusted_amount_residual_currency}) cannot exceed "
                    # f"the due amount ({line.amount_residual}) for invoice {line.move_name or line.name}. "
                    # f"Please adjust the payment amount."
                # )

    def action_fifo_payment_assignment(self):
        """Automatically assign payment amounts using FIFO method"""
        if not self.move_line_ids:
            raise UserError("No journal items available for FIFO assignment.")

        # Get total available payment amount
        total_payment = self.amount or 0.0

        # Sort move lines by date first, then by ID if same date (FIFO - First In, First Out)
        sorted_lines = self.move_line_ids.sorted(lambda x: (x.date, x.id))

        # Reset all adjusted amounts first using SQL
        self.env.cr.execute("""
            UPDATE account_move_line
            SET adjusted_amount_residual = 0.0,
                adjusted_amount_residual_currency = 0.0
            WHERE id IN %s
        """, (tuple(self.move_line_ids.ids),))

        # Assign payment amounts in FIFO order
        remaining_payment = total_payment

        for line in sorted_lines:
            if remaining_payment <= 0:
                break

            # Use absolute value of amount_residual (handles both debit/credit lines)
            amount_due = abs(line.amount_residual)

            # Assign the minimum of remaining payment and amount due
            payment_amount = min(remaining_payment, amount_due)

            # Write directly to database using SQL
            self.env.cr.execute("""
                UPDATE account_move_line
                SET adjusted_amount_residual = %s,
                    adjusted_amount_residual_currency = %s
                WHERE id = %s
            """, (payment_amount, payment_amount, line.id))

            remaining_payment -= payment_amount

        # Commit the transaction
        self.env.cr.commit()


    def action_reconcile(self):
        """
            Function that call default recalculation function
            with custom move_line_ids
        """
        move_line_ids = self.move_line_ids.filtered(
            lambda x: x.adjusted_amount_residual > 0)

        move_line_ids += self.get_reconcile_move_line()
        move_line_ids = move_line_ids.with_context(
            split_payment=True, split_payment_type=self.payment_type)
        # reconciled_items = []
        for reconciled_line in move_line_ids:
            if reconciled_line.adjusted_amount_residual != 0:
                # reconciled_items.append(
                account_reconciled =  self.env['account.reconciled'].sudo().create({
                        'payment_id': self.id,
                        'amount': reconciled_line.adjusted_amount_residual,
                        'total_amount':reconciled_line.credit if
                        self.payment_type == 'outbound' else
                        reconciled_line.debit ,
                        # 'amount_due': reconciled_line.amount_residual,
                        'move_line_id': reconciled_line.id,
                        'partner_currency_id': self.currency_id.id,
                        # 'partner_amount': reconciled_line.adjusted_amount_residual,

                    })
                self.reconciled_entry_ids = [Command.link(account_reconciled.id)]
        # self.reconciled_entry_ids = [Command.link(reconciled_items.id)]
        # self.is_reconciled_line = True
        # self.remaining_reconciled = self.new_reference
        # self.calculate_balance_amount()
        move_line_ids._reconcile_plan([move_line_ids])
        self.already_paying = sum(self.reconciled_entry_ids.mapped('amount'))
        self.remaining_reconciled = self.amount - self.already_paying
        self._onchange_is_reconcile_line()

    def get_reconcile_move_line(self):
        """Function that returns the payment line"""
        if self.payment_type == 'inbound':
            return self.move_id.invoice_line_ids.filtered(
                lambda x: x.credit > 0
            )
        else:
            return self.move_id.invoice_line_ids.filtered(
                lambda x: x.debit > 0
            )
