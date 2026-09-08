from odoo import api, fields, models, _
class BulkMailPartnerWizardLine(models.TransientModel):
    _name = "bulk.mail.partner.wizard.line"
    _description = "Add Multiple Partners Wizard Line"

    wizard_id = fields.Many2one('bulk.mail.partner.wizard', string="Wizard", ondelete="cascade")
    selected = fields.Boolean(string="Select", default=False)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    email = fields.Char(string="Email")