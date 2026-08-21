from odoo import models


class PosSessions(models.Model):
    _inherit = 'pos.session'

    def action_update_config(self):
        """it open the change pos config wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Pos Config',
            'res_model': 'change.pos.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_config_id': self.config_id.id,
                'default_session_id': self.id
            }
        }