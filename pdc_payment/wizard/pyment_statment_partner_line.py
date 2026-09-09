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

class PaymentStatementPartnerLine(models.TransientModel):
    _name = "payment.statement.partner.line"
    _description = "Payment Statement Partner Line"

    statement_id = fields.Many2one('payment.statement', string="Statement", ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string="Name", required=True)

    @api.onchange('partner_id')
    def mail_checking(self):
        if self.partner_id and not self.partner_id.email:
            raise UserError(_("Selected partner '%s' does not have an email address. Please add an email address to this partner.") % self.partner_id.name)
        if self.partner_id and not (self.partner_id.x_studio_sales_executive and self.partner_id.x_studio_sales_executive.work_email):
            raise UserError(_("Selected partner '%s' does not have a Sales Executive email address. Please add an executive email address to this partner.") % self.partner_id.name)





