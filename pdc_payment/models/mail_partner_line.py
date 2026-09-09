# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Technologies(<https://www.cybrosys.com>)
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

class MailPartnerLine(models.Model):
    _name = "mail.partner.line"
    _description = "Mail Partner Line"

    bulk_mail_id = fields.Many2one('bulk.mail', string="Bulk Mail", ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    email = fields.Char(string="Email", compute="_compute_email", store=True, readonly=False, precompute=True, required=True)
    sale_executive_id = fields.Many2one('hr.employee', string="Sales Executive", related="partner_id.x_studio_sales_executive", store=True)
    sale_excutive_mail = fields.Char(string="Sales Executive Mail", compute="_compute_sale_excutive_mail", store=True, readonly=False, precompute=True, required=True)

    @api.depends('partner_id', 'partner_id.email')
    def _compute_email(self):
        for line in self:
            line.email = line.partner_id.email if line.partner_id else False

    @api.depends('partner_id', 'partner_id.x_studio_sales_executive', 'partner_id.x_studio_sales_executive.work_email')
    def _compute_sale_excutive_mail(self):
        for line in self:
            if line.partner_id and line.partner_id.x_studio_sales_executive:
                line.sale_excutive_mail = line.partner_id.x_studio_sales_executive.work_email
            else:
                line.sale_excutive_mail = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if not self.partner_id.email:
                raise UserError(_("Selected partner '%s' does not have an email address. Please add an email address to this partner.") % self.partner_id.name)
            if not (self.partner_id.x_studio_sales_executive and self.partner_id.x_studio_sales_executive.work_email):
                raise UserError(_("Selected partner '%s' does not have a Sales Executive email address. Please add an executive email address to this partner.") % self.partner_id.name)
            self.email = self.partner_id.email
            self.sale_excutive_mail = self.partner_id.x_studio_sales_executive.work_email
        else:
            self.email = False
            self.sale_excutive_mail = False

    def action_add_multiple_partners(self):
        bulk_mail_id = self.env.context.get('bulk_mail_id') or self.bulk_mail_id.id
        if not bulk_mail_id and self.env.context.get('active_id'):
            bulk_mail_id = self.env.context.get('active_id')
        if bulk_mail_id:
            bulk_mail = self.env['bulk.mail'].browse(bulk_mail_id)
            return bulk_mail.action_add_multiple_partners()