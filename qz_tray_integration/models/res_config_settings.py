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
        string="Printer",
        config_parameter='qz_tray_integration.available_printers',
        help="Select the default printer from detected available printers."
    )
    qz_has_certificate = fields.Boolean(
        string="Certificate Configured",
        compute="_compute_qz_has_certificate",
    )
    qz_silent_printing = fields.Boolean(
        string="Enable Silent Printing (Digital Certificate)",
        config_parameter='qz_tray_integration.qz_silent_printing',
        help="Enable completely silent printing using cryptographic digital signatures."
    )
    qz_certificate = fields.Text(
        string="Digital Certificate (.crt)",
        help="Paste your X.509 Digital Certificate in PEM format."
    )
    qz_private_key = fields.Text(
        string="Private Key (.key)",
        help="Paste your RSA Private Key in PEM format (kept securely on the server)."
    )

    def _compute_qz_has_certificate(self):
        """Check if certificate and private key are already generated."""
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
        res.update(
            qz_certificate=get_param('qz_tray_integration.qz_certificate', ''),
            qz_private_key=get_param('qz_tray_integration.qz_private_key', ''),
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        set_param = getattr(ICP, 'set_str', getattr(ICP, 'set_param', None))
        if set_param:
            set_param('qz_tray_integration.qz_certificate', self.qz_certificate or '')
            set_param('qz_tray_integration.qz_private_key', self.qz_private_key or '')

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
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        set_param = getattr(ICP, 'set_str', getattr(ICP, 'set_param', None))
        if set_param:
            set_param('qz_tray_integration.detected_printers', ','.join(printers))
            current = get_param('qz_tray_integration.available_printers', '')
            if not current and printers:
                set_param('qz_tray_integration.available_printers', printers[0])
        return True

    def _install_qz_certificate(self, cert_pem):
        """Install the certificate into QZ Tray's trusted certificate store.

        This writes the certificate to ~/.qz/auth/override.crt which makes
        QZ Tray treat it as fully trusted — no permission dialogs will appear
        for any operation (connect, print, find printers).

        Also updates ~/.qz/allowed.dat with the certificate fingerprint so
        remembered decisions persist across QZ Tray restarts.
        """
        import os
        import hashlib

        home_dir = os.path.expanduser('~')
        qz_dir = os.path.join(home_dir, '.qz')
        auth_dir = os.path.join(qz_dir, 'auth')

        # Ensure directories exist
        os.makedirs(auth_dir, exist_ok=True)

        # Write certificate to override.crt — this is the key to silent printing
        override_crt_path = os.path.join(auth_dir, 'override.crt')
        with open(override_crt_path, 'w') as f:
            f.write(cert_pem)
        _logger.info("QZ Tray: Installed certificate to %s", override_crt_path)

        # Calculate certificate fingerprint (SHA-1 of DER-encoded cert)
        try:
            from cryptography import x509 as x509_mod
            cert_obj = x509_mod.load_pem_x509_certificate(cert_pem.encode('utf-8'))
            der_bytes = cert_obj.public_bytes(
                __import__('cryptography.hazmat.primitives.serialization',
                           fromlist=['Encoding']).Encoding.DER
            )
            fingerprint = hashlib.sha1(der_bytes).hexdigest()

            # Extract CN and O from the certificate subject
            cn = ''
            org = ''
            for attr in cert_obj.subject:
                if attr.oid.dotted_string == '2.5.4.3':  # CN
                    cn = attr.value
                elif attr.oid.dotted_string == '2.5.4.10':  # O
                    org = attr.value

            not_before = cert_obj.not_valid_before_utc.strftime('%Y-%m-%d %H:%M:%S')
            not_after = cert_obj.not_valid_after_utc.strftime('%Y-%m-%d %H:%M:%S')

            # Build allowed.dat entry — format: fingerprint\tCN\tO\tnotBefore\tnotAfter\tblocked
            entry = f"{fingerprint}\t{cn}\t{org}\t{not_before}\t{not_after}\tfalse\n"

            # Write/overwrite allowed.dat
            allowed_path = os.path.join(qz_dir, 'allowed.dat')
            with open(allowed_path, 'w') as f:
                f.write(entry)
            _logger.info("QZ Tray: Updated allowed.dat with fingerprint %s", fingerprint)

            # Clear blocked.dat to remove any previous blocks
            blocked_path = os.path.join(qz_dir, 'blocked.dat')
            with open(blocked_path, 'w') as f:
                f.write('')

        except Exception as e:
            _logger.warning("QZ Tray: Could not update allowed.dat: %s", e)

    def action_generate_qz_certificate(self):
        """Generate a self-signed X.509 digital certificate and RSA private key."""
        self.ensure_one()
        try:
            import datetime
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u'Odoo QZ Tray'),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'Odoo ERP'),
            ])

            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.now(datetime.timezone.utc)
            ).not_valid_after(
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
            ).sign(key, hashes.SHA256())

            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
            key_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            ICP = self.env['ir.config_parameter'].sudo()
            set_param = getattr(ICP, 'set_str', getattr(ICP, 'set_param', None))
            if set_param:
                set_param('qz_tray_integration.qz_certificate', cert_pem)
                set_param('qz_tray_integration.qz_private_key', key_pem)
                set_param('qz_tray_integration.qz_silent_printing', 'True')

            self.qz_certificate = cert_pem
            self.qz_private_key = key_pem
            self.qz_silent_printing = True

            # Install cert into QZ Tray's trust store for fully silent operation
            self._install_qz_certificate(cert_pem)

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            _logger.exception("Failed to generate QZ Tray certificate: %s", e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to generate certificate: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

