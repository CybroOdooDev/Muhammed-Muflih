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
from odoo.exceptions import ValidationError

class BulkMail(models.Model):
    _name = "bulk.mail"
    _description = "Bulk Mail"

    name = fields.Char(string="Name", required=True)
    type = fields.Selection([('customer', 'Customer'), ('vendor', 'Vendor')], string="Type", default='customer')
    partner_line_ids = fields.One2many('mail.partner.line', 'bulk_mail_id', string="Partner Lines")

    @api.constrains('type')
    def _check_unique_type(self):
        for record in self:
            if record.type:
                existing = self.search_count([('type', '=', record.type), ('id', '!=', record.id)])
                if existing > 0:
                    raise ValidationError(_("A Bulk Mail record of type '%s' already exists. You cannot create a new one.") % (dict(self._fields['type'].selection).get(record.type)))

    def action_add_multiple_partners(self):
        self.ensure_one()
        domain = [('customer_rank', '>', 0)] if self.type == 'customer' else [('supplier_rank', '>', 0)]
        partners = self.env['res.partner'].search(domain)
        
        wizard = self.env['bulk.mail.partner.wizard'].create({
            'bulk_mail_id': self.id,
            'partner_type': self.type,
            'line_ids': [(0, 0, {
                'partner_id': partner.id,
                'email': partner.email,
                'selected': False,
            }) for partner in partners]
        })
        
        return {
            'name': _('Add Multiple Partners'),
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.mail.partner.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }









