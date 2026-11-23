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
import json
import logging
from odoo import http
from odoo.http import request
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)


class TelegramWebhookController(http.Controller):
    """Controller for handling Telegram webhooks."""

    @http.route(
        [
            '/telegram/webhook/<int:bot_id>',
            '/telegram/webhook',
            '/telegram/webhook/<string:token>',
        ],
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def telegram_webhook(self, bot_id=None, token=None, **kwargs):
        """
        Handle incoming Telegram webhook requests.
        Validates the bot and secret token from headers or bot reference, parses the incoming payload,
        creates a corresponding incoming message record, and updates the bot's sync timestamp.
        """
        bot = None
        secret_header = request.httprequest.headers.get('X-Telegram-Bot-Api-Secret-Token')

        if bot_id:
            bot = request.env['telegram.bot'].sudo().browse(bot_id)
            if not bot.exists() or not bot.active:
                bot = None
            elif secret_header:
                expected_secret = (bot.token or '').replace(':', '_')
                if secret_header != expected_secret and secret_header != bot.token:
                    _logger.warning("Telegram webhook received with invalid secret header for bot ID %s", bot_id)
                    return http.Response(
                        json.dumps({"ok": False, "error": "Invalid webhook secret"}),
                        content_type="application/json",
                        status=403
                    )
        elif secret_header:
            bot = request.env['telegram.bot'].sudo().search(
                ['|', ('token', '=', secret_header), ('token', '=', secret_header.replace('_', ':', 1))],
                limit=1
            )
        elif token:
            bot = request.env['telegram.bot'].sudo().search(
                [('token', '=', token)],
                limit=1
            )

        if not bot:
            _logger.warning("Telegram webhook hit with an invalid bot reference.")
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": "Invalid bot reference"
                }),
                content_type="application/json",
                status=404
            )

        try:
            payload = None
            if hasattr(request, 'get_json_data'):
                try:
                    payload = request.get_json_data()
                except Exception:
                    payload = None
            if not payload and hasattr(request.httprequest, 'data') and request.httprequest.data:
                payload = json.loads(request.httprequest.data.decode('utf-8'))

            _logger.info("Received Telegram payload for bot %s", bot.id)

            # Create incoming message record
            request.env['telegram.message'].sudo().create_incoming(
                bot,
                payload
            )
            bot.sudo().write({
                'last_sync': Datetime.now(),
                'last_error_message': False,
                'status': 'active'
            })
            return http.Response(
                json.dumps({
                    "ok": True
                }),
                content_type="application/json",
                status=200
            )
        except Exception as e:
            _logger.exception("Failed processing telegram webhook: %s", str(e))
            bot.sudo().write({
                'last_error_message': str(e),
                'status': 'error'
            })
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": str(e)
                }),
                content_type="application/json",
                status=500
            )
