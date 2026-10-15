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

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def get_qz_config(self):
        """Fetch current QZ Tray configuration for the frontend client."""
        ICP = self.env['ir.config_parameter'].sudo()
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        qz_enable = get_param('qz_tray_integration.qz_enable', 'False') in ('True', 'true', '1', True)
        default_printer = get_param('qz_tray_integration.available_printers', '')
        qz_silent_printing = get_param('qz_tray_integration.qz_silent_printing', 'False') in ('True', 'true', '1', True)
        qz_certificate = get_param('qz_tray_integration.qz_certificate', '')
        detected_printers = get_param('qz_tray_integration.detected_printers', '')
        printers_list = [p.strip() for p in detected_printers.split(',') if p.strip()] if detected_printers else []
        if default_printer and default_printer not in printers_list:
            printers_list.append(default_printer)
        return {
            'qz_enable': bool(qz_enable),
            'default_printer': default_printer,
            'detected_printers': printers_list,
            'qz_silent_printing': bool(qz_silent_printing and qz_certificate),
            'qz_certificate': qz_certificate if qz_silent_printing else False,
        }

    @api.model
    def sign_qz_data(self, to_sign):
        """Cryptographically sign data for QZ Tray using the stored RSA private key."""
        if not to_sign:
            return False
        ICP = self.env['ir.config_parameter'].sudo()
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        private_key_pem = get_param('qz_tray_integration.qz_private_key', '')
        if not private_key_pem:
            return False
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
            )
            signature = private_key.sign(
                to_sign.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA512(),
            )
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            _logger.error("Error signing QZ Tray data: %s", e)
            return False

    @api.model
    def render_report_for_qz(self, report_ref, res_ids=None, data=None, context=None):
        """Render report and return formatted payload for QZ Tray printing."""
        report = self._get_report(report_ref)
        if not report:
            raise UserError(_("Report '%s' was not found.", report_ref))

        ctx = dict(self.env.context)
        if context and isinstance(context, dict):
            ctx.update(context)

        # Ensure res_ids is formatted properly
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        elif res_ids and not isinstance(res_ids, list):
            res_ids = list(res_ids)
        elif not res_ids:
            res_ids = None

        if not data or not isinstance(data, dict):
            data = {}

        report_type = report.report_type or 'qweb-pdf'

        if report_type == 'qweb-text':
            text_content, _ = self.with_context(ctx)._render_qweb_text(report_ref, res_ids or [], data=data)
            if isinstance(text_content, bytes):
                text_content = text_content.decode('utf-8', errors='replace')
            return {
                'format': 'command',
                'type': 'raw',
                'flavor': 'plain',
                'data': text_content,
                'report_name': report.name or report.report_name,
            }
        else:
            pdf_content, _ = self.with_context(ctx)._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
            return {
                'format': 'pdf',
                'type': 'pixel',
                'flavor': 'base64',
                'data': base64.b64encode(pdf_content).decode('ascii'),
                'report_name': report.name or report.report_name,
            }
