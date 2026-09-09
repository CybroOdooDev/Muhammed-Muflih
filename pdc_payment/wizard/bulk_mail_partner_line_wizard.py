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
from odoo import fields,models
class BulkMailPartnerWizardLine(models.TransientModel):
    _name = "bulk.mail.partner.wizard.line"
    _description = "Add Multiple Partners Wizard Line"

    wizard_id = fields.Many2one('bulk.mail.partner.wizard', string="Wizard", ondelete="cascade")
    selected = fields.Boolean(string="Select", default=False)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    email = fields.Char(string="Email")