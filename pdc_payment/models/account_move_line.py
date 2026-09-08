# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from datetime import date

from odoo.addons.account.models.account_move_line import AccountMoveLine

from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    """ This model represents account.move.line."""
    _inherit = 'account.move.line'

    adjusted_amount_residual = fields.Float('Adjusted Amount', copy=False)
    adjusted_amount_residual_currency = fields.Float(
        'Foreign Currency', digits=(16, 3), copy=False)

    @api.onchange('adjusted_amount_residual_currency')
    def _onchange_adjusted_amount_residual_currency(self):
        """
            Onchange method to update the 'adjusted_amount_residual_currency'
            based on the selected currency.
        """
        amount = self.currency_id._convert(
            self.adjusted_amount_residual_currency,
            self.company_id.currency_id,
            self.company_id, self.move_id.date, False)
        self.adjusted_amount_residual = amount

    @api.onchange('adjusted_amount_residual')
    def _onchange_adjusted_amount_residual(self):
        for rec in self:
            if (rec.adjusted_amount_residual > abs(rec.amount_residual) and
                    rec.move_id.move_type == 'in_invoice'):
                raise UserError(_('Paying must be less than or equal to '
                                  'amount due'))

    def _reconcile_plan_with_sync_extend(self, plan_list, all_amls):
        # Parameter allowing to disable the exchange journal entries on partials.
        disable_partial_exchange_diff = bool(
            self.env['ir.config_parameter'].sudo().get_param('account.disable_partial_exchange_diff'))

        # ==== Prefetch the fields all at once to speedup the reconciliation ====
        # All of those fields will be cached by the orm. Since the amls are split into multiple batches, the orm is not
        # able to prefetch the data for all of them at once. For that reason, we force the orm to populate the cache
        # before doing anything.
        all_amls.move_id
        all_amls.matched_debit_ids
        all_amls.matched_credit_ids

        # ==== Track the invoice's state to call the hook when they become paid ====
        pre_hook_data = all_amls._reconcile_pre_hook()
        # ==== Collect amls data ====
        # All residual amounts are collected and updated until the creation of partials in batch.
        # This is done that way to minimize the orm time for fields invalidation/mark as recompute and
        # recomputation.
        split_type = self._context.get('split_payment_type', 'other')

        if self._context.get('split_payment'):
            aml_values_map = {}
            for aml in all_amls:
                # print("aml")
                if split_type == 'inbound':
                    # Customer payments/invoices
                    values = {
                        'aml': aml,
                        'amount_residual': aml.adjusted_amount_residual if aml.debit else aml.amount_residual,
                        'amount_residual_currency':aml.adjusted_amount_residual_currency if aml.debit else aml.amount_residual_currency,
                    }
                elif split_type == 'outbound':
                    # Vendor payments/bills
                    # print(aml, aml.adjusted_amount_residual,
                    #       aml.amount_residual_currency , aml.credit, aml.amount_residual)
                    values = {
                        'aml': aml,
                        'amount_residual': -abs(
                            aml.adjusted_amount_residual) if aml.credit else aml.amount_residual,
                        'amount_residual_currency': -abs(
                            aml.adjusted_amount_residual_currency) if aml.credit else aml.amount_residual_currency,
                    }
                else:
                    # Other entries (credit notes, opening balances)
                    values = {
                        'aml': aml,
                        'amount_residual': aml.adjusted_amount_residual,
                        'amount_residual_currency': aml.amount_residual_currency,
                    }
                aml_values_map[aml] = values
        else:
            aml_values_map = {
                aml: {
                    'aml': aml,
                    'amount_residual': aml.amount_residual,
                    'amount_residual_currency': aml.amount_residual_currency,
                }
                for aml in all_amls
            }
        # ==== Prepare the partials ====
        partials_values_list = []
        exchange_diff_values_list = []
        exchange_diff_partial_index = []
        all_plan_results = []
        partial_index = 0
        for plan in plan_list:
            plan_results = self \
                .with_context(
                no_exchange_difference=self._context.get(
                    'no_exchange_difference') or disable_partial_exchange_diff,
                no_exchange_difference_no_recursive=self._context.get(
                    'no_exchange_difference_no_recursive', False),
            ) \
                ._prepare_reconciliation_plan(plan, aml_values_map)
            # print("plan_results", plan_results)
            all_plan_results.append(plan_results)
            for results in plan_results:
                partials_values_list.append(results['partial_values'])
                if results.get('exchange_values') and results['exchange_values']['move_values']['line_ids']:
                    # print("11111111111111", results.get('exchange_values'), results['exchange_values']['move_values']['line_ids'])
                    exchange_diff_values_list.append(results['exchange_values'])
                    exchange_diff_partial_index.append(partial_index)
                    partial_index += 1

        # ==== Create the partials ====
        # Link the newly created partials to the plan. There are needed later for caba exchange entries.
        partials = self.env['account.partial.reconcile'].create(partials_values_list)
        start_range = 0
        for plan_results, plan in zip(all_plan_results, plan_list):
            size = len(plan_results)
            plan['partials'] = partials[start_range:start_range + size]
            start_range += size

        # ==== Create the partial exchange journal entries ====

        exchange_moves = self._create_exchange_difference_moves(exchange_diff_values_list)
        for index, exchange_move in zip(exchange_diff_partial_index, exchange_moves):
            partials[index].exchange_move_id = exchange_move

        # ==== Create entries for cash basis taxes ====
        def is_cash_basis_needed(amls):
            return any(amls.company_id.mapped('tax_exigibility')) \
                and amls.account_id.account_type in (
                'asset_receivable', 'liability_payable')

        if not self._context.get(
                'move_reverse_cancel') and not self._context.get(
                'no_cash_basis'):
            for plan in plan_list:
                if is_cash_basis_needed(plan['amls']):
                    plan['partials'].with_context(
                        no_exchange_difference_no_recursive=False)._create_tax_cash_basis_moves()

        # ==== Prepare full reconcile creation ====
        # First, we need to find all sub-set of amls that are candidates for a full.

        def is_line_reconciled(aml, has_multiple_currencies):
            # Check if the journal item passed as parameter is now fully reconciled.
            if aml.reconciled:
                return True
            if not aml.matched_debit_ids and not aml.matched_credit_ids:
                # Suppose a journal item having balance = 0 but an amount_currency like an exchange difference.
                return False
            if has_multiple_currencies:
                return aml.company_currency_id.is_zero(aml.amount_residual)
            else:
                return aml.currency_id.is_zero(aml.amount_residual_currency)

        full_batches = []
        all_aml_ids = set()
        number2lines = all_amls._reconciled_by_number()
        for plan in plan_list:
            for aml in plan['amls']:
                if 'full_batch_index' in aml_values_map[aml]:
                    continue

                involved_amls = plan['amls']._filter_reconciled_by_number(number2lines)
                all_aml_ids.update(involved_amls.ids)
                full_batch_index = len(full_batches)
                has_multiple_currencies = len(involved_amls.currency_id) > 1
                is_fully_reconciled = all(
                    is_line_reconciled(involved_aml, has_multiple_currencies)
                    for involved_aml in involved_amls
                )
                full_batches.append({
                    'amls': involved_amls,
                    'is_fully_reconciled': is_fully_reconciled,
                })
                for involved_aml in involved_amls:
                    if aml_values_map.get(involved_aml):
                        aml_values_map[involved_aml]['full_batch_index'] = full_batch_index

        # ==== Prefetch the fields all at once to speedup the reconciliation ====
        # Again, we do the same optimization for the prefetching. We need to do it again since most of the values have
        # been invalidated with the creation of the account.partial.reconcile records.
        all_amls = self.browse(list(all_aml_ids))
        all_amls.move_id
        all_amls.matched_debit_ids
        all_amls.matched_credit_ids

        # ==== Prepare the full exchange journal entries ====
        # This part could be bypassed using the 'no_exchange_difference' key inside the context. This is useful
        # when importing a full accounting including the reconciliation like Winbooks.

        exchange_diff_values_list = []
        exchange_diff_full_batch_index = []
        if not self._context.get('no_exchange_difference'):
            for full_batch_index, full_batch in enumerate(full_batches):
                involved_amls = full_batch['amls']
                if not full_batch['is_fully_reconciled']:
                    continue

                # In normal cases, the exchange differences are already generated by the partial at this point meaning
                # there is no journal item left with a zero amount residual in one currency but not in the other.
                # However, after a migration coming from an older version with an older partial reconciliation or due to
                # some rounding issues (when dealing with different decimal places for example), we could need an extra
                # exchange difference journal entry to handle them.
                exchange_lines_to_fix = self.env['account.move.line']
                amounts_list = []
                exchange_max_date = date.min
                for aml in involved_amls:
                    if not aml.company_currency_id.is_zero(aml.amount_residual):
                        exchange_lines_to_fix += aml
                        amounts_list.append({'amount_residual': aml.amount_residual})
                    elif not aml.currency_id.is_zero(aml.amount_residual_currency):
                        exchange_lines_to_fix += aml
                        amounts_list.append({'amount_residual_currency': aml.amount_residual_currency})
                    exchange_max_date = max(exchange_max_date, aml.date)
                exchange_diff_values = exchange_lines_to_fix._prepare_exchange_difference_move_vals(
                    amounts_list,
                    company=involved_amls.company_id,
                    exchange_date=exchange_max_date,
                )

                # Exchange difference for cash basis entries.
                # If we are fully reversing the entry, no need to fix anything since the journal entry
                # is exactly the mirror of the source journal entry.
                caba_lines_to_reconcile = None
                if is_cash_basis_needed(
                        involved_amls) and not self._context.get(
                        'move_reverse_cancel') and not self._context.get(
                        'no_cash_basis'):
                    caba_lines_to_reconcile = involved_amls._add_exchange_difference_cash_basis_vals(
                        exchange_diff_values)

                # Prepare the exchange difference.
                if exchange_diff_values['move_values']['line_ids']:
                    exchange_diff_full_batch_index.append(full_batch_index)
                    exchange_diff_values_list.append(exchange_diff_values)
                    full_batch['caba_lines_to_reconcile'] = caba_lines_to_reconcile

        # ==== Create the full exchange journal entries ====
        exchange_moves = self._create_exchange_difference_moves(exchange_diff_values_list)
        for full_batch_index, exchange_move in zip(exchange_diff_full_batch_index, exchange_moves):
            full_batch = full_batches[full_batch_index]
            amls = full_batch['amls']
            full_batch['exchange_move'] = exchange_move
            exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == amls.account_id)
            full_batch['amls'] |= exchange_move_lines

        # ==== Create the full reconcile ====
        # Note we are using Command.link and not Command.set because Command.set is triggering an unlink that is
        # slowing down the assignation of the co-fields. Indeed, unlink is forcing a flush.
        full_reconcile_values_list = []
        full_reconcile_full_batch_index = []
        for full_batch_index, full_batch in enumerate(full_batches):
            amls = full_batch['amls']
            involved_partials = amls.matched_debit_ids + amls.matched_credit_ids
            if full_batch['is_fully_reconciled']:
                full_reconcile_values_list.append({
                    'exchange_move_id': full_batch.get('exchange_move') and full_batch['exchange_move'].id,
                    'partial_reconcile_ids': [Command.link(partial.id) for partial in involved_partials],
                    'reconciled_line_ids': [Command.link(aml.id) for aml in amls],
                })
                full_reconcile_full_batch_index.append(full_batch_index)

        self.env['account.full.reconcile'].create(full_reconcile_values_list)

        # === Cash basis rounding autoreconciliation ===
        # In case a cash basis rounding difference line got created for the transition account, we reconcile it with the corresponding lines
        # on the cash basis moves (so that it reaches full reconciliation and creates an exchange difference entry for this account as well)
        for full_batch in full_batches:
            if not full_batch.get('caba_lines_to_reconcile'):
                continue

            caba_lines_to_reconcile = full_batch['caba_lines_to_reconcile']
            exchange_move = full_batch['exchange_move']
            for (dummy, account, repartition_line), amls_to_reconcile in caba_lines_to_reconcile.items():
                if not account.reconcile:
                    continue

                exchange_line = exchange_move.line_ids.filtered(
                    lambda l: l.account_id == account and l.tax_repartition_line_id == repartition_line
                )

                (exchange_line + amls_to_reconcile) \
                    .filtered(lambda l: not l.reconciled) \
                    .reconcile()

        all_amls._reconcile_post_hook(pre_hook_data)
        if self._context.get('split_payment'):
            all_amls.write({
                'adjusted_amount_residual': 0.0,
                'adjusted_amount_residual_currency': 0.0,
                # 'is_split_reconciliation': False
            })

    AccountMoveLine._reconcile_plan_with_sync = _reconcile_plan_with_sync_extend