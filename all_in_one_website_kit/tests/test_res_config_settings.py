
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo.tests import common


class TestResConfigSettings(common.TransactionCase):
    def setUp(self):
        super(TestResConfigSettings, self).setUp()

    def test_01_res_config_settings(self):
        """Test setting and getting configuration parameters"""
        
        # Create config settings record
        config = self.env['res.config.settings'].create({
            'comment_configuration': True,
            'is_show_recent_so_q': True,
            'sale_count': 10,
            'is_show_recent_po_rfq': True,
            'purchase_count': 5,
            'is_show_project': False,
            'project_count': 0,
            'is_show_recent_invoice_bill': True,
            'account_count': 20,
        })
        
        # Execute to save the parameters
        config.execute()
        
        # Fetch the parameters using ir.config_parameter
        get_param = self.env['ir.config_parameter'].sudo().get_param
        
        # Assert parameters match what was set
        self.assertTrue(get_param('customer_order_comment.comment_configuration'))
        self.assertTrue(get_param('portal_dashboard.is_show_recent_so_q'))
        self.assertEqual(int(get_param('portal_dashboard.sale_count', 0)), 10)
        self.assertTrue(get_param('portal_dashboard.is_show_recent_po_rfq'))
        self.assertEqual(int(get_param('portal_dashboard.purchase_count', 0)), 5)
        self.assertFalse(get_param('portal_dashboard.is_show_project'))
        self.assertEqual(int(get_param('portal_dashboard.project_count', 0)), 0)
        self.assertTrue(get_param('portal_dashboard.is_show_recent_invoice_bill'))
        self.assertEqual(int(get_param('portal_dashboard.account_count', 0)), 20)
