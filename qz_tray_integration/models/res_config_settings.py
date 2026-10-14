# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Configuration settings for QZ Tray integration."""
    _inherit = 'res.config.settings'

    qz_enable = fields.Boolean(
        string="Enable QZ Tray",
        config_parameter='qz_tray_integration.qz_enable',
        help="Enable direct printing via QZ Tray."
    )
    available_printers = fields.Selection(
        selection='_get_available_printers',
        string="Available Printers",
        config_parameter='qz_tray_integration.available_printers',
        help="Select the default printer from detected available printers."
    )

    @api.model
    def _get_available_printers(self):
        """Fetch detected printers from config parameter for selection options."""
        ICP = self.env['ir.config_parameter'].sudo()
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        param = get_param('qz_tray_integration.detected_printers', '')
        printers = [p.strip() for p in param.split(',') if p.strip()] if param else []
        saved_printer = get_param('qz_tray_integration.available_printers', '')
        if saved_printer and saved_printer not in printers:
            printers.append(saved_printer)
        return [(p, p) for p in printers]

    def action_connect_qz(self):
        """Connect to QZ Tray desktop application."""
        self.ensure_one()
        if not self.qz_enable:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('QZ Tray Integration'),
                    'message': _('Please enable QZ Tray integration first.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        # Delegate to the frontend QZ Tray WebSocket client action
        return {
            'type': 'ir.actions.client',
            'tag': 'qz_connect_action',
        }

    def action_check_available_printers(self):
        """Detect available printers via frontend QZ Tray library."""
        self.ensure_one()
        if not self.qz_enable:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('QZ Tray Integration'),
                    'message': _('Please enable QZ Tray integration first.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        # Delegate to the frontend QZ Tray printers find client action
        return {
            'type': 'ir.actions.client',
            'tag': 'qz_find_printers_action',
        }

    @api.model
    def save_detected_printers(self, printers):
        """Persist printers detected by the frontend QZ Tray library."""
        if not printers or not isinstance(printers, list):
            return False
        ICP = self.env['ir.config_parameter'].sudo()
        set_param = getattr(ICP, 'set_str', getattr(ICP, 'set_param', None))
        if set_param:
            set_param('qz_tray_integration.detected_printers', ','.join(printers))
        return True
