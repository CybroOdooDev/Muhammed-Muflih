# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    """Inherits the stock move model for adding new fields and functions"""
    _inherit = 'stock.move'

    cw_uom_id = fields.Many2one(
        'uom.uom', string='CW-Uom',
        compute='_compute_cw_fields', store=True, readonly=False, precompute=True,
        help="Catch weight unit of measure used for this product.")
    cw_demand = fields.Float(
        string='CW-Demand',
        digits=(16, 4),
        compute='_compute_cw_fields', store=True, readonly=False, precompute=True,
        help="The demand quantity in catch weight units.")
    cw_reserved = fields.Float(
        string='CW-Reserved',
        compute='_compute_cw_fields', store=True, readonly=False, precompute=True,
        digits=(16, 4),
        help="The reserved quantity in catch weight units.")
    cw_done = fields.Float(
        string='CW-Done', digits=(16, 4),
        compute='_compute_cw_done', store=True, readonly=False,
        help="The completed quantity in catch weight units.")
    cw_hide = fields.Boolean(
        string='Is CW Product',
        compute="_compute_hide", default=False, store=True, precompute=True,
        help="A flag indicating whether this is a catch weight product.")

    @api.depends('product_id')
    def _compute_hide(self):
        """Compute method for product setups"""
        for rec in self:
            rec.cw_hide = bool(rec.product_id.catch_weigth_ok)

    @api.depends('product_id', 'product_uom_qty')
    def _compute_cw_fields(self):
        """Calculating cw demand, cw uom and cw reserved"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_demand = rec.product_uom_qty * rec.product_id.average_cw_qty
                rec.cw_reserved = rec.product_uom_qty * rec.product_id.average_cw_qty
                rec.cw_uom_id = rec.product_id.cw_uom_id
            else:
                rec.cw_demand = 0.0
                rec.cw_reserved = 0.0
                rec.cw_uom_id = False

    @api.depends('product_id', 'quantity')
    def _compute_cw_done(self):
        """Calculating cw done based on move quantity"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_done = rec.quantity * rec.product_id.average_cw_qty
            else:
                rec.cw_done = 0.0

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id(self):
        """Calculating cw demand and cw uom"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_demand = rec.product_uom_qty * rec.product_id.average_cw_qty
                rec.cw_uom_id = rec.product_id.cw_uom_id
                rec.cw_reserved = rec.product_uom_qty * rec.product_id.average_cw_qty
            else:
                rec.cw_demand = 0.0
                rec.cw_uom_id = False
                rec.cw_reserved = 0.0

    @api.onchange('cw_done')
    def _onchange_cw_done(self):
        """Calculating done qty"""
        for rec in self:
            if (rec.product_id.catch_weigth_ok
                    and rec.product_id.average_cw_qty != 0):
                rec.quantity = rec.cw_done / rec.product_id.average_cw_qty

    @api.onchange('quantity')
    def _onchange_cw_cty(self):
        """Calculating cw done"""
        for rec in self:
            if rec.product_id.catch_weigth_ok:
                rec.cw_done = rec.quantity * rec.product_id.average_cw_qty

    @api.onchange('cw_demand')
    def _onchange_cw_demand(self):
        """Calculating cw qty"""
        for rec in self:
            if (rec.product_id.catch_weigth_ok
                    and rec.product_id.average_cw_qty != 0):
                if rec.cw_uom_id == rec.uom_id:
                    rec.product_uom_qty = rec.cw_demand
                else:
                    rec.product_uom_qty = (rec.cw_demand /
                                           rec.product_id.average_cw_qty)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """Calculating cw demand"""
        for rec in self:
            if (rec.product_id.catch_weigth_ok
                    and rec.product_id.average_cw_qty != 0):
                if rec.cw_uom_id == rec.uom_id:
                    rec.cw_demand = rec.product_uom_qty
                else:
                    rec.cw_demand = (rec.product_uom_qty *
                                     rec.product_id.average_cw_qty)
