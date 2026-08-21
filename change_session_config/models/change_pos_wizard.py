from odoo import models, fields


class ChangePosWizard(models.TransientModel):
    _name = 'change.pos.wizard'
    _description = 'Change Pos Wizard'

    session_id = fields.Many2one('pos.session', required=True)
    config_id = fields.Many2one('pos.config', required=True)

    def action_update_config(self):
        """Update the Point of Sale for the selected POS session."""
        self.session_id.config_id = self.config_id.id

