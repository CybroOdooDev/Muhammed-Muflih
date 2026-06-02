from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    time_limit_for_quiz=fields.Float(string="Time Limit for Quiz", config_parameter='quiz_idle_timer.time_limit_for_quiz')