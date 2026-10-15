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
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class QzTrayController(http.Controller):
    """Controller providing certificate delivery and digital signing for QZ Tray."""

    @http.route('/qz/certificate', type='http', auth='user', methods=['GET'], csrf=False)
    def qz_get_certificate(self):
        """Serve the digital certificate in plain text for qz.security.setCertificatePromise."""
        ICP = request.env['ir.config_parameter'].sudo()
        get_param = getattr(ICP, 'get_str', getattr(ICP, 'get_param', lambda k, d='': d))
        cert_pem = get_param('qz_tray_integration.qz_certificate', '')
        return request.make_response(
            cert_pem or '',
            headers=[
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Cache-Control', 'no-store, no-cache, must-revalidate'),
            ]
        )

    @http.route(['/qz/sign'], type='http', auth='user', methods=['GET', 'POST'], csrf=False)
    def qz_sign_request(self, **kwargs):
        """Sign requested data using the backend private key for qz.security.setSignaturePromise."""
        to_sign = kwargs.get('request') or kwargs.get('data')
        if not to_sign and request.httprequest.data:
            try:
                to_sign = request.httprequest.data.decode('utf-8')
            except Exception:
                pass

        if not to_sign:
            return request.make_response('', headers=[('Content-Type', 'text/plain; charset=utf-8')])

        try:
            signature = request.env['ir.actions.report'].sign_qz_data(to_sign)
            return request.make_response(
                signature or '',
                headers=[
                    ('Content-Type', 'text/plain; charset=utf-8'),
                    ('Cache-Control', 'no-store, no-cache, must-revalidate'),
                ]
            )
        except Exception as e:
            _logger.error("Error generating QZ Tray signature: %s", e)
            return request.make_response('', status=500, headers=[('Content-Type', 'text/plain; charset=utf-8')])
