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


class CourierWeightPrice(models.Model):
    """This is for creating courier weight price rule"""
    _name = 'courier.weight.price'
    _description = "Courier Weight PriceRule"

    name = fields.Char(string="Name", required=True,
                       help="Name of courier weight price rule")
    minimum_weight = fields.Float(string="Minimum Weight", required=True,
                                  help="Minimum weight")
    maximum_weight = fields.Float(string="Maximum Weight", required=True,
                                  help="Maximum weight")
    company_id = fields.Many2one('res.company', string="Company",
                                 required=True,
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Choose company")
    currency_id = fields.Many2one("res.currency", string='Currency',
                                  related='company_id.currency_id',
                                  help="Company currency")
    price = fields.Monetary(string="Price", required=True,
                            help="The price based on courier weight")

    @api.constrains('maximum_weight', 'minimum_weight')
    def _check_weight(self):
        """Returns validations based on the weight"""
        for rec in self:
            if rec.minimum_weight <= 0 or rec.maximum_weight <= 0:
                raise ValidationError(self.env._('Weight must be greater than zero'))
            if rec.minimum_weight >= rec.maximum_weight:
                raise ValidationError(
                    self.env._('Minimum Weight must be less than Maximum Weight'))
