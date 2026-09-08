from odoo import api, fields, models, _
class BulkMailPartnerWizard(models.TransientModel):
    _name = "bulk.mail.partner.wizard"
    _description = "Add Multiple Partners Wizard"

    bulk_mail_id = fields.Many2one('bulk.mail', string="Bulk Mail", required=True)
    partner_type = fields.Selection([('customer', 'Customer'), ('vendor', 'Vendor')], string="Partner Type")
    line_ids = fields.One2many('bulk.mail.partner.wizard.line', 'wizard_id', string="Partner Lines")

    def action_add_partners(self):
        self.ensure_one()
        selected_lines = self.line_ids.filtered(lambda l: l.selected)
        if self.bulk_mail_id and selected_lines:
            existing_partner_ids = set(self.bulk_mail_id.partner_line_ids.mapped('partner_id.id'))
            new_lines = []
            for line in selected_lines:
                if line.partner_id.id not in existing_partner_ids:
                    new_lines.append((0, 0, {
                        'partner_id': line.partner_id.id,
                        'email': line.partner_id.email or line.email,
                    }))
            if new_lines:
                self.bulk_mail_id.write({'partner_line_ids': new_lines})
        return {'type': 'ir.actions.act_window_close'}

    def action_select_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.mail.partner.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_deselect_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.mail.partner.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }