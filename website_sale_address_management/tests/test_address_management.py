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
from unittest.mock import patch

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_address_management.controllers.\
    website_sale_address_management import CustomWebsiteSale
from odoo.tests import TransactionCase, tagged

PREFIX = 'website_sale_address_management.'


@tagged('post_install', '-at_install')
class TestWebsiteSaleAddressManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_in = cls.env.ref('base.in')
        cls.country_us = cls.env.ref('base.us')
        cls.Config = cls.env['ir.config_parameter'].sudo()
        cls.Settings = cls.env['res.config.settings']
        cls.website = cls.env.ref('website.default_website')

    def _set_param(self, key, value):
        if isinstance(value, bool):
            if hasattr(self.Config, 'set_bool'):
                self.Config.set_bool(key, value)
            else:
                self.Config.set_param(key, value)
        elif isinstance(value, int) and not isinstance(value, bool):
            if hasattr(self.Config, 'set_int'):
                self.Config.set_int(key, value)
            else:
                self.Config.set_param(key, value)
        elif value is None or value is False:
            if hasattr(self.Config, 'set_bool'):
                self.Config.set_bool(key, False)
            elif hasattr(self.Config, 'set_str'):
                self.Config.set_str(key, None)
            else:
                self.Config.set_param(key, False)
        else:
            if hasattr(self.Config, 'set_str'):
                self.Config.set_str(key, str(value))
            else:
                self.Config.set_param(key, value)

    def _get_param_bool(self, key):
        if hasattr(self.Config, 'get_bool'):
            return self.Config.get_bool(key)
        return self.Config.get_param(key) in ('True', 'true', '1', True)

    def _get_param_int(self, key):
        if hasattr(self.Config, 'get_int'):
            return self.Config.get_int(key)
        val = self.Config.get_param(key)
        return int(val) if (val and str(val).isdigit()) else 0

    def _clear(self):
        for prefix in ('billing', 'shipping'):
            for key in ('phone', 'street', 'street2', 'city', 'zip_code'):
                self._set_param(
                    '%sis_%s_%s' % (PREFIX, prefix, key), False)
                self._set_param(
                    '%sis_%s_%s_is_required' % (PREFIX, prefix, key), False)

    def test_01_mandatory_fields_logic(self):
        """Required flags are stored as 'True' and removed when unset."""
        key = PREFIX + 'is_billing_street_is_required'
        self._set_param(key, True)
        self.assertTrue(self._get_param_bool(key))
        # set_param(False) deletes the parameter, get_param returns False.
        self._set_param(key, False)
        self.assertFalse(self._get_param_bool(key))

    def test_02_default_country_application(self):
        for prefix, country in (('billing', self.country_in),
                                ('shipping', self.country_us)):
            key = PREFIX + prefix + '_country'
            self._set_param(key, country.id)
            self.assertEqual(self._get_param_int(key), country.id)

    def test_03_field_visibility_toggles(self):
        key = PREFIX + 'is_billing_phone'
        self._set_param(key, True)
        self.assertTrue(self._get_param_bool(key))
        self._set_param(key, False)
        self.assertFalse(self._get_param_bool(key))

    def test_04_field_config_helper(self):
        """Only toggled-on fields are visible; required needs visible."""
        self._clear()
        self._set_param(PREFIX + 'billing_country', False)
        cfg = self.Settings.get_address_field_config('billing')
        self.assertFalse(any(cfg[f]['visible'] for f in
                             ('phone', 'street', 'street2', 'city', 'zip')))
        self.assertFalse(cfg['default_country_id'])

        self._set_param(PREFIX + 'is_billing_phone', True)
        self._set_param(PREFIX + 'is_billing_phone_is_required', True)
        self._set_param(PREFIX + 'is_billing_street_is_required', True)
        self._set_param(PREFIX + 'billing_country', self.country_in.id)
        cfg = self.Settings.get_address_field_config('billing')
        self.assertTrue(cfg['phone'] == {'visible': True, 'required': True})
        # required but hidden -> not required
        self.assertEqual(cfg['street'], {'visible': False, 'required': False})
        self.assertEqual(cfg['default_country_id'], self.country_in.id)
        # shipping is independent
        cfg = self.Settings.get_address_field_config('delivery')
        self.assertFalse(cfg['phone']['visible'])

        self._set_param(PREFIX + 'is_shipping_zip_code', True)
        self._set_param(PREFIX + 'shipping_country', self.country_us.id)
        cfg = self.Settings.get_address_field_config('shipping')
        self.assertTrue(cfg['zip']['visible'])
        self.assertFalse(cfg['zip']['required'])
        self.assertEqual(cfg['default_country_id'], self.country_us.id)

    def test_05_onchange_resets_required(self):
        """Switching a field off switches its 'required' flag off."""
        names = ('phone', 'street', 'city', 'zip_code')
        vals = {}
        for prefix in ('billing', 'shipping'):
            for name in names:
                vals['is_%s_%s' % (prefix, name)] = False
                vals['is_%s_%s_is_required' % (prefix, name)] = True
        settings = self.Settings.new(vals)
        settings._onchange_fields()
        for prefix in ('billing', 'shipping'):
            for name in names:
                self.assertFalse(
                    settings['is_%s_%s_is_required' % (prefix, name)])
        # fields left on keep their required flag
        settings = self.Settings.new({
            'is_billing_phone': True, 'is_billing_phone_is_required': True})
        settings._onchange_fields()
        self.assertTrue(settings.is_billing_phone_is_required)

    def test_06_controller_mandatory_fields(self):
        self._clear()
        controller = CustomWebsiteSale()
        with MockRequest(self.env, website=self.website):
            for getter, prefix in (
                (controller._get_mandatory_billing_address_fields,
                 'billing'),
                (controller._get_mandatory_delivery_address_fields,
                 'shipping'),
            ):
                fields = getter(self.country_in)
                self.assertFalse(fields & {'phone', 'street', 'city', 'zip'})
                self._set_param(PREFIX + 'is_%s_street' % prefix, True)
                self._set_param(
                    PREFIX + 'is_%s_street_is_required' % prefix, True)
                self.assertIn('street', getter(self.country_in))

    def test_07_controller_validation(self):
        self._clear()
        controller = CustomWebsiteSale()
        partner = self.env['res.partner']
        values = {'name': 'Test', 'country_id': self.country_in.id}
        with MockRequest(self.env, website=self.website):
            _inv, missing, _msg = controller._validate_address_values(
                values, partner, 'billing', False, 'name,street,city')
            # phone, street, city and zip are not configured as required
            # (email and state_id stay mandatory in core)
            self.assertFalse(missing & {'phone', 'street', 'city', 'zip'})
            self._set_param(PREFIX + 'is_billing_city', True)
            self._set_param(PREFIX + 'is_billing_city_is_required', True)
            _inv, missing, msgs = controller._validate_address_values(
                values, partner, 'billing', False, 'name')
            self.assertIn('city', missing)
            self.assertTrue(msgs)
            # delivery used as billing: required on either side applies
            _inv, missing, _msg = controller._validate_address_values(
                values, partner, 'delivery', True, 'name')
            self.assertIn('city', missing)
            # invalid email is reported
            invalid, _missing, _msg = controller._validate_address_values(
                dict(values, email='bad'), partner, 'billing', False, '')
            self.assertIn('email', invalid)

    def test_08_validation_accepts_core_kwargs(self):
        """Extra core arguments are forwarded to the core validation."""
        self._clear()
        controller = CustomWebsiteSale()
        values = {'name': 'Test', 'country_id': self.country_in.id}
        with MockRequest(self.env, website=self.website):
            invalid, missing, _msg = controller._validate_address_values(
                values, self.env['res.partner'], 'billing', False, 'name',
                is_main_address=True)
        self.assertFalse(invalid)
        self.assertFalse(missing & {'phone', 'street', 'city', 'zip'})

    def test_09_partial_address_keeps_optional_fields_optional(self):
        """Core asks for the whole address once a part of it is given, but
        the fields that are not configured as required stay optional."""
        self._clear()
        controller = CustomWebsiteSale()
        values = {
            'name': 'Test',
            'country_id': self.country_in.id,
            'street': 'MG Road',
        }
        with MockRequest(self.env, website=self.website):
            _inv, missing, _msg = controller._validate_address_values(
                values, self.env['res.partner'], 'billing', False, 'name')
            self.assertFalse(missing & {'phone', 'street', 'city', 'zip'})
            self._set_param(PREFIX + 'is_billing_city', True)
            self._set_param(PREFIX + 'is_billing_city_is_required', True)
            _inv, missing, msgs = controller._validate_address_values(
                values, self.env['res.partner'], 'billing', False, 'name')
            self.assertIn('city', missing)
            self.assertTrue(msgs)

    def _prepare_form_values(self, controller, partner, order):
        """Return the address form values, without any country coming from
        the current user."""
        with MockRequest(self.env, website=self.website), patch.object(
            WebsiteSale, '_get_default_country',
            return_value=self.env['res.country'],
        ):
            return controller._prepare_address_form_values(
                partner, address_type='billing', order_sudo=order)

    def test_10_default_country_in_address_form(self):
        """The configured default country is preselected on a new address
        of the cart, and does not replace the country of an address."""
        self._clear()
        self._set_param(PREFIX + 'billing_country', False)
        self._set_param(PREFIX + 'shipping_country', False)
        controller = CustomWebsiteSale()
        customer = self.env['res.partner'].create({'name': 'Cart Customer'})
        order = self.env['sale.order'].create({
            'partner_id': customer.id,
            'website_id': self.website.id,
        })
        new_address = self.env['res.partner']
        values = self._prepare_form_values(controller, new_address, order)
        self.assertFalse(values['country'])

        self._set_param(PREFIX + 'billing_country', self.country_in.id)
        values = self._prepare_form_values(controller, new_address, order)
        self.assertEqual(values['country'], self.country_in)
        self.assertEqual(values['states'], self.country_in.state_ids)
        self.assertEqual(values['country_states'], self.country_in.state_ids)

        # The delivery address uses its own default country.
        self._set_param(PREFIX + 'shipping_country', self.country_us.id)
        with MockRequest(self.env, website=self.website), patch.object(
            WebsiteSale, '_get_default_country',
            return_value=self.env['res.country'],
        ):
            values = controller._prepare_address_form_values(
                new_address, address_type='delivery', order_sudo=order)
        self.assertEqual(values['country'], self.country_us)

        # An existing address keeps its own country.
        existing = self.env['res.partner'].create({
            'name': 'Existing Address',
            'parent_id': customer.id,
            'type': 'delivery',
            'country_id': self.country_us.id,
        })
        values = self._prepare_form_values(controller, existing, order)
        self.assertEqual(values['country'], self.country_us)

    def test_11_address_form_template_extension(self):
        """The module extends the core address fields template instead of
        replacing the address form."""
        view = self.env.ref(
            'website_sale_address_management.address_form_fields')
        self.assertTrue(view.active)
        self.assertEqual(
            view.inherit_id, self.env.ref('website_sale.address_form_fields'))
        for fname in ('phone', 'street', 'street2', 'city', 'zip'):
            self.assertIn("addr_cfg['%s']['visible']" % fname, view.arch_db)

    def test_12_partner_mandatory_fields(self):
        """res.partner mandatory fields reflect the module configuration."""
        self._clear()
        partner = self.env['res.partner']
        # Initially none of the managed fields are required
        fields_billing = partner._get_mandatory_billing_address_fields(self.country_in)
        self.assertFalse(fields_billing & {'phone', 'street', 'city', 'zip'})

        self._set_param(PREFIX + 'is_billing_phone', True)
        self._set_param(PREFIX + 'is_billing_phone_is_required', True)
        self._set_param(PREFIX + 'is_shipping_city', True)
        self._set_param(PREFIX + 'is_shipping_city_is_required', True)

        fields_billing = partner._get_mandatory_billing_address_fields(self.country_in)
        self.assertIn('phone', fields_billing)
        self.assertNotIn('city', fields_billing)

        fields_shipping = partner._get_mandatory_delivery_address_fields(self.country_in)
        self.assertIn('city', fields_shipping)
        self.assertNotIn('phone', fields_shipping)

    def test_13_address_template_buttons(self):
        """The address template adds Save address and Discard buttons."""
        view = self.env.ref(
            'website_sale_address_management.address')
        self.assertTrue(view.active)
        self.assertEqual(
            view.inherit_id, self.env.ref('website_sale.address'))
        self.assertIn('save_address', view.arch_db)
        self.assertIn('Discard', view.arch_db)
        self.assertIn('discard_url', view.arch_db)

