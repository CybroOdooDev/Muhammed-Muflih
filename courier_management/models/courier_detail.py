# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
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
###############################################################################
from odoo import api, fields, models


class CourierDetail(models.Model):
    """This is the order line of courier requests"""
    _name = 'courier.detail'
    _description = "Courier Detail"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product",
                                 required=True, help="Courier product name")
    quantity = fields.Integer(string="Quantity", required=True, default=1,
                              help="Quantity of the courier product")
    weight = fields.Float(string="Weight", related='product_id.weight',
                          help="Weight of the courier product")
    total_weight = fields.Float(string="Total Weight",
                                compute='_compute_total_weight',
                                help="Total weight of the courier product")
    weight_price = fields.Float(string="Weight Price", readonly=True,
                                help="Product weight price")
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Choose company")
    currency_id = fields.Many2one("res.currency", string='Currency',
                                  related='company_id.currency_id',
                                  help="Company currency")
    sub_total = fields.Monetary(string="Sub Total",
                                compute='_compute_sub_total',
                                help="Get the total amount")
    courier_requests_id = fields.Many2one('courier.request',
                                          string="Courier Request",
                                          help="Relational field of courier "
                                               "request")

    @api.depends('weight', 'quantity')
    def _compute_total_weight(self):
        """It will compute the total weight"""
        for record in self:
            record.total_weight = record.quantity * record.weight \
                if record.quantity else record.weight
            matching_prices = self.env['courier.weight.price'].search(
                [('minimum_weight', '<=', record.total_weight),
                 ('maximum_weight', '>=', record.total_weight)]
            ).mapped('price')
            if matching_prices:
                record.weight_price = min(matching_prices)
            else:
                all_rules = self.env['courier.weight.price'].search([])
                if all_rules:
                    minimum = all_rules.mapped('minimum_weight')
                    maximum = all_rules.mapped('maximum_weight')
                    prices = all_rules.mapped('price')
                    if record.total_weight < min(minimum):
                        record.weight_price = min(prices)
                    elif record.total_weight > max(maximum):
                        record.weight_price = max(prices)
                    else:
                        record.weight_price = 0
                else:
                    record.weight_price = 0

    @api.depends('quantity', 'product_id')
    def _compute_sub_total(self):
        """Compute the sub-total of courier requests"""
        for record in self:
            record.sub_total = record.weight_price
