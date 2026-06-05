# -*- coding: utf-8 -*-
################################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################


from odoo.tests import tagged
from odoo.tests.common import TransactionCase




@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a new POS Config for testing
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config for Settings',
        })


    def test_res_config_settings_related_field(self):
        """Test that pos_show_mass_edit_button behaves as a related field"""
        
        # Create setting record linked to the POS config
        config_settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })

        # Check default value in settings reflects default value in POS config
        self.assertTrue(
            config_settings.pos_show_mass_edit_button,
            "The pos_show_mass_edit_button should default to True matching pos_config_id"
        )
        
        # Modify configuration setting
        config_settings.write({
            'pos_show_mass_edit_button': False,
        })
        
        # Execute settings update
        config_settings.execute()
        
        # Verify the related field successfully wrote back to POS config
        self.assertFalse(
            self.pos_config.show_mass_edit_button,
            "Writing to pos_show_mass_edit_button in settings should write back to pos.config"
        )

