from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_company(self):
        result = super()._loader_params_res_company()
        result['search_params']['fields'].append('pos_order_limit')
        return result
