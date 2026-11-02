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
# -*- coding: utf-8 -*-

from odoo.tests.common import HttpCase, tagged
from odoo import fields
from datetime import timedelta
import json


@tagged('post_install', '-at_install')
class TestWebsiteBargainController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.website = cls.env.ref('base.default_website', raise_if_not_found=False) or cls.env['website'].search([], limit=1)

        cls.user = cls.env.ref('base.user_admin')

        cls.product = cls.env['product.product'].create({
            'name': 'Auction Product',
            'type': 'consu',
        })

        cls.template = cls.env['bargain.template'].create({
            'name': 'Auction Template',
            'product_id': cls.product.product_tmpl_id.id,
        })

        cls.auction = cls.env['website.bargain'].create({
            'website_id': cls.website.id,
            'template_id': cls.template.id,
            'auction_manager_id': cls.user.id,
            'product_id': cls.product.product_tmpl_id.id,
            'initial_price': 100,
            'is_buy_now': True,
            'price_buy_now': 150,
            'start_time': fields.Datetime.now(),
            'end_time': fields.Datetime.now() + timedelta(days=1),
            'state': 'running',
        })


    def test_01_auction_timer(self):
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/auction/timer',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)

    def test_02_subscribe(self):
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/subscribe/bid',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id,
                    'text': 'subscribe',
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)


    def test_03_buy_now(self):
        self.authenticate(self.user.login, 'admin')
        response = self.url_open(
            '/buy/now',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'auction_id': self.auction.id,
                    'product_id': self.product.id,
                }
            }),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
