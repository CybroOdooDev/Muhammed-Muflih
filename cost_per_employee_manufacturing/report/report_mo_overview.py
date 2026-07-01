# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
# ###############################################################################
from odoo import models


class ReportMoOverview(models.AbstractModel):
    """Override method for adding cost per employee"""
    _inherit = 'report.mrp.report_mo_overview'

    def _get_report_data(self, production_id):
        """Generate a detailed cost and component report for a manufacturing order."""
        production = self.env['mrp.production'].browse(production_id)
        # Necessary to fetch the right quantities for multi-warehouse
        production = production.with_context(warehouse_id=production.warehouse_id.id)

        components = self._get_components_data(production, level=1, current_index='')
        operations = self._get_operations_data(production, level=1, current_index='')
        initial_mo_cost, initial_bom_cost, initial_real_cost = self._compute_cost_sums(components, operations)

        if production.bom_id:
            currency = (production.company_id or self.env.company).currency_id
            missing_components = (bom_line for bom_line in production.bom_id.bom_line_ids if bom_line not in (production.move_raw_ids.bom_line_id + self._get_kit_bom_lines(production.bom_id)))
            missing_operations = (bom_line for bom_line in production.bom_id.operation_ids if bom_line not in production.workorder_ids.operation_id)
            for line in missing_components:
                line_cost = line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line.product_qty
                initial_bom_cost += currency.round(line_cost * production.product_uom_qty / production.bom_id.product_qty)
            for operation in missing_operations:
                cost = (operation._get_duration_expected(production.product_id, production.product_qty) / 60.0) * operation.workcenter_id.costs_hour
                bom_cost = self.env.company.currency_id.round(cost)
                initial_bom_cost += currency.round(bom_cost * production.product_uom_qty / production.bom_id.product_qty)

        remaining_cost_share, byproducts = self._get_byproducts_data(production, initial_mo_cost, initial_bom_cost, initial_real_cost, level=1, current_index='')
        summary = self._get_mo_summary(production, components, operations, initial_mo_cost, initial_bom_cost, initial_real_cost, remaining_cost_share)
        cost_per_employee = {'cost_per_employe': production.cost_per_hour}
        extra_lines = self._get_report_extra_lines(summary, components, operations, cost_per_employee, production)
        return {
            'id': production.id,
            'name': production.display_name,
            'summary': summary,
            'components': components,
            'operations': operations,
            'byproducts': byproducts,
            'extras': extra_lines,
            'cost_breakdown': self._get_cost_breakdown_data(production, extra_lines, remaining_cost_share),
            'cost_per_employ': production.cost_per_hour,
        }

    def _get_report_extra_lines(self, summary, components, operations, cost_per_employee, production):
        """Compute additional cost-related details for the manufacturing order report."""
        currency = summary.get('currency', self.env.company.currency_id)
        unit_mo_cost = currency.round(summary.get('mo_cost', 0) / (summary.get('quantity') or 1))
        unit_bom_cost = currency.round(summary.get('bom_cost', 0) / (summary.get('quantity') or 1))
        unit_real_cost = currency.round(summary.get('real_cost', 0) / (summary.get('quantity') or 1))
        extras = {
            'unit_mo_cost': unit_mo_cost + cost_per_employee['cost_per_employe'],
            'unit_bom_cost': unit_bom_cost,
            'unit_real_cost': unit_real_cost + cost_per_employee['cost_per_employe'],
        }
        if production.state == 'done':
            production_qty = summary.get('quantity') or 1.0
            extras['total_mo_cost_components'] = sum(compo.get('summary', {}).get('mo_cost', 0.0) for compo in components)
            extras['total_bom_cost_components'] = sum(compo.get('summary', {}).get('bom_cost', 0.0) for compo in components)
            extras['total_real_cost_components'] = sum(compo.get('summary', {}).get('real_cost', 0.0) for compo in components)
            extras['unit_mo_cost_components'] = extras['total_mo_cost_components'] / production_qty
            extras['unit_bom_cost_components'] = extras['total_bom_cost_components'] / production_qty
            extras['unit_real_cost_components'] = extras['total_real_cost_components'] / production_qty
            extras['total_mo_cost_operations'] = operations.get('summary', {}).get('mo_cost', 0.0)
            extras['total_bom_cost_operations'] = operations.get('summary', {}).get('bom_cost', 0.0)
            extras['total_real_cost_operations'] = operations.get('summary', {}).get('real_cost', 0.0)
            extras['unit_mo_cost_operations'] = extras['total_mo_cost_operations'] / production_qty
            extras['unit_bom_cost_operations'] = extras['total_bom_cost_operations'] / production_qty
            extras['unit_real_cost_operations'] = extras['total_real_cost_operations'] / production_qty
            extras['total_mo_cost'] = extras['total_mo_cost_components'] + extras['total_mo_cost_operations']
            extras['total_bom_cost'] = extras['total_bom_cost_components'] + extras['total_bom_cost_operations']
            extras['total_real_cost'] = extras['total_real_cost_components'] + extras['total_real_cost_operations']
        return extras
