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
from odoo.exceptions import ValidationError


class CourierDimensionPrice(models.Model):
    """This is for creating courier dimension price rule"""
    _name = 'courier.dimension.price'
    _description = "Courier Dimension PriceRule"

    name = fields.Char(string="Name", required=True,
                       help="Name of courier dimension price")
    length = fields.Integer(string="Length", required=True,
                            help="Length of box")
    width = fields.Integer(string="Width", required=True, help="Width of box")
    height = fields.Integer(string="Height", required=True,
                            help="Height of box")
    volumetric_weight = fields.Float(string="Volumetric Weight(kg)",
                                     compute='_compute_volumetric_weight',
                                     help="Weight of the courier")
    company_id = fields.Many2one('res.company', string="Company",
                                 required=True,
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Choose company")
    currency_id = fields.Many2one("res.currency", string='Currency',
                                  related='company_id.currency_id',
                                  help="Company currency")
    price = fields.Monetary(string="Price", required=True,
                            help="The price based on weight")

    @api.constrains('length', 'width', 'height')
    def _check_available_combinations(self):
        """Returns validation based on length, width and height"""
        for rec in self:
            if rec.length <= 0 or rec.width <= 0 or rec.height <= 0:
                raise ValidationError(self.env._('Invalid Combination'))

    @api.depends('length', 'width', 'height')
    def _compute_volumetric_weight(self):
        """Compute the volumetric weight of courier"""
        for rec in self:
            rec.volumetric_weight = (rec.length * rec.width * rec.height) / \
                                    5000
