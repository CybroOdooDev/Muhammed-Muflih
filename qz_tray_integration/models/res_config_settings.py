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
import base64
import logging
import os
import subprocess
import tempfile

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


def _extract_binary_text(val):
    """Safely extract plain text string from BinaryValue, base64 str, or bytes."""
    if not val:
        return ''
    if hasattr(val, 'content'):
        raw = val.content
    elif isinstance(val, bytes):
        raw = val
    elif isinstance(val, str):
        try:
            raw = base64.b64decode(val)
        except Exception:
            raw = val.encode('utf-8')
    else:
        try:
            raw = bytes(val)
        except Exception:
            raw = b''
    return raw.decode('utf-8', errors='replace').strip()


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
        string="Printer",
        config_parameter='qz_tray_integration.available_printers',
        help="Select the default printer from detected available printers."
    )
    qz_has_certificate = fields.Boolean(
        string="Certificate Configured",
        compute="_compute_qz_has_certificate",
    )
    qz_certificate_file = fields.Binary(
        string="Digital Certificate",
        help="Attach your purchased digital certificate file (.txt or .crt) from QZ Industries (https://qz.io)."
    )
    qz_certificate_filename = fields.Char(string="Certificate Filename")
    qz_private_key_file = fields.Binary(
        string="Private Key",
        help="Attach the private key file (.pem or .key) provided with your purchased QZ Tray certificate."
    )
    qz_private_key_filename = fields.Char(string="Private Key Filename")

    def _compute_qz_has_certificate(self):
        """Check if certificate and private key are attached and configured."""
        ICP = self.env['ir.config_parameter'].sudo()
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        has_cert = bool(get_param('qz_tray_integration.qz_certificate', '')) and bool(get_param('qz_tray_integration.qz_private_key', ''))
        for rec in self:
            rec.qz_has_certificate = has_cert

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

    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        cert_text = get_param('qz_tray_integration.qz_certificate', '')
        cert_filename = get_param('qz_tray_integration.qz_certificate_filename', 'digital-certificate.txt' if cert_text else '')
        key_text = get_param('qz_tray_integration.qz_private_key', '')
        key_filename = get_param('qz_tray_integration.qz_private_key_filename', 'private-key.pem' if key_text else '')

        res.update(
            qz_certificate_file=base64.b64encode(cert_text.encode('utf-8')).decode('ascii') if cert_text else False,
            qz_certificate_filename=cert_filename,
            qz_private_key_file=base64.b64encode(key_text.encode('utf-8')).decode('ascii') if key_text else False,
            qz_private_key_filename=key_filename,
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        set_param = getattr(ICP, 'set_str', getattr(ICP, 'set_param', None))
        if not set_param:
            return

        cert_pem = _extract_binary_text(self.qz_certificate_file)
        if cert_pem:
            set_param('qz_tray_integration.qz_certificate', cert_pem)
            set_param('qz_tray_integration.qz_certificate_filename', self.qz_certificate_filename or 'digital-certificate.txt')
        else:
            set_param('qz_tray_integration.qz_certificate', '')
            set_param('qz_tray_integration.qz_certificate_filename', '')

        key_pem = _extract_binary_text(self.qz_private_key_file)
        if key_pem:
            set_param('qz_tray_integration.qz_private_key', key_pem)
            set_param('qz_tray_integration.qz_private_key_filename', self.qz_private_key_filename or 'private-key.pem')
        else:
            set_param('qz_tray_integration.qz_private_key', '')
            set_param('qz_tray_integration.qz_private_key_filename', '')

        has_both = bool(cert_pem and key_pem)
        set_param('qz_tray_integration.qz_silent_printing', str(has_both))

        if cert_pem:
            self._install_qz_certificate(cert_pem)

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
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        set_param = getattr(ICP, 'set_str', getattr(ICP, 'set_param', None))
        if set_param:
            set_param('qz_tray_integration.detected_printers', ','.join(printers))
            current = get_param('qz_tray_integration.available_printers', '')
            if not current and printers:
                set_param('qz_tray_integration.available_printers', printers[0])
        return True

    def _install_qz_certificate(self, cert_pem):
        """Install the certificate into local QZ Tray's trusted root and whitelist store if available."""
        if not cert_pem:
            return
        home_dir = os.path.expanduser('~')
        qz_dir = os.path.join(home_dir, '.qz')
        os.makedirs(qz_dir, exist_ok=True)

        override_path = os.path.join(qz_dir, 'override.crt')
        try:
            with open(override_path, 'w') as f:
                f.write(cert_pem)
            _logger.info("QZ Tray: Saved override certificate to %s", override_path)
        except Exception as e:
            _logger.warning("QZ Tray: Could not save %s: %s", override_path, e)

        prefs_path = os.path.join(qz_dir, 'prefs.properties')
        try:
            prefs_lines = []
            if os.path.exists(prefs_path):
                with open(prefs_path, 'r') as f:
                    prefs_lines = [line for line in f if not line.startswith('authcert.override')]
            prefs_lines.append(f"authcert.override={override_path}\n")
            with open(prefs_path, 'w') as f:
                f.writelines(prefs_lines)
            _logger.info("QZ Tray: Configured %s with authcert.override", prefs_path)
        except Exception as e:
            _logger.warning("QZ Tray: Could not update %s: %s", prefs_path, e)

        autostart_dir = os.path.join(home_dir, '.config', 'autostart')
        autostart_file = os.path.join(autostart_dir, 'qz-tray.desktop')
        try:
            os.makedirs(autostart_dir, exist_ok=True)
            desktop_entry = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=QZ Tray\n"
                f'Exec=env QZ_OPTS="-Dauthcert.override={override_path}" "/opt/qz-tray/qz-tray" --honorautostart\n'
                "Path=/opt/qz-tray\n"
                "Icon=/opt/qz-tray/qz-tray.svg\n"
                "Terminal=false\n"
                "StartupNotify=false\n"
            )
            with open(autostart_file, 'w') as f:
                f.write(desktop_entry)
            os.chmod(autostart_file, 0o755)
        except Exception as e:
            _logger.warning("QZ Tray: Could not update %s: %s", autostart_file, e)

        qz_bin = '/opt/qz-tray/qz-tray'
        if os.path.exists(qz_bin):
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as tmp:
                    tmp.write(cert_pem)
                    tmp_file = tmp.name
                subprocess.run([qz_bin, '--allow', tmp_file], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.unlink(tmp_file)
                _logger.info("QZ Tray: Added certificate to allowed.dat via CLI")
            except Exception as e:
                _logger.warning("QZ Tray: Failed to run qz-tray --allow: %s", e)
