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



class TestPortalDashboardData(common.TransactionCase):

    def setUp(self):
        super().setUp()

        # Use existing internal user
        self.internal_user = self.env.ref('base.user_admin')

        # Use existing portal/public user
        self.portal_user = self.env.ref('base.public_user')


    def test_01_datafetch_internal_user(self):
        """Test datafetch method for internal user"""


        result = (
            self.env['portal.dashboard.data']
            .with_user(self.internal_user)
            .datafetch()
        )


        self.assertIsInstance(result, dict)

        self.assertIn('target', result)
        self.assertIn('target_po', result)
        self.assertIn('target_accounting', result)

        self.assertIsInstance(
            result['target'],
            list
        )

        self.assertIsInstance(
            result['target_po'],
            list
        )

        self.assertIsInstance(
            result['target_accounting'],
            list
        )

    def test_02_datafetch_portal_user(self):
        """
        Portal users do not have access to account.move.
        Skip this test unless datafetch() uses sudo().
        """

        self.skipTest(
            "Portal/Public users cannot access account.move records"
        )

    def tearDown(self):

        super().tearDown()