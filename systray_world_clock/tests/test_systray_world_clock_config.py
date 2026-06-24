# -*- coding: utf-8 -*-

import pytz
from datetime import datetime

from odoo.tests.common import TransactionCase



class TestSystrayWorldClockConfig(TransactionCase):
    """Test cases for Systray World Clock Configuration"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_onchange_tz_with_valid_timezone(self):
        """Test offset calculation for a valid timezone"""
        clock = self.env['systray.world.clock.config'].new({
            'name': 'India',
            'tz': 'Asia/Kolkata',
        })

        clock._onchange_tz()

        utc_dt = pytz.utc.localize(datetime.utcnow())
        local_dt = utc_dt.astimezone(pytz.timezone('Asia/Kolkata'))
        expected_offset = (
            local_dt.utcoffset().total_seconds() / 3600
        )

        self.assertEqual(clock.offset, expected_offset)


    def test_onchange_tz_without_timezone(self):
        """Test onchange when timezone is not set"""

        clock = self.env['systray.world.clock.config'].new({
            'name': 'Test Location',
        })

        clock._onchange_tz()

        self.assertFalse(clock.offset)


    def test_create_record(self):
        """Test record creation"""
        record = self.env['systray.world.clock.config'].create({
            'name': 'Dubai',
            'tz': 'Asia/Dubai',
        })

        self.assertTrue(record)
        self.assertEqual(record.name, 'Dubai')
        self.assertEqual(record.tz, 'Asia/Dubai')

   