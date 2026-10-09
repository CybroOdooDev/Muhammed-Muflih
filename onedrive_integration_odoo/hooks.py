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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import SUPERUSER_ID, api


def uninstall_hook(cr, registry):
    """
    Delete System Parameters
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'onedrive_integration_odoo.client_id')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'onedrive_integration_odoo.client_secret')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'onedrive_integration_odoo.folder_id')]).unlink()
    env['ir.config_parameter'].sudo().search(
        [('key', '=', 'onedrive_integration_odoo.onedrive_button')]).unlink()
