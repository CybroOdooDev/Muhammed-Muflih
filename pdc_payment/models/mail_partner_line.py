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
from odoo import api, fields, models

class MailPartnerLine(models.Model):
    _name = "mail.partner.line"
    _description = "Mail Partner Line"

    bulk_mail_id = fields.Many2one('bulk.mail', string="Bulk Mail", ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    email = fields.Char(string="Email", required=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.email = self.partner_id.email

    def action_add_multiple_partners(self):
        bulk_mail_id = self.env.context.get('bulk_mail_id') or self.bulk_mail_id.id
        if not bulk_mail_id and self.env.context.get('active_id'):
            bulk_mail_id = self.env.context.get('active_id')
        if bulk_mail_id:
            bulk_mail = self.env['bulk.mail'].browse(bulk_mail_id)
            return bulk_mail.action_add_multiple_partners()