# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
    # Check that no other employee with user_id = user.id exists besides the existing one

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase




@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_auto_employee_creation_standard_user(self):
        """Test that a new hr.employee is automatically created for a standard internal user."""
        initial_emp_count = self.env['hr.employee'].search_count([('name', '=', 'Test Standard User')])
        self.assertEqual(initial_emp_count, 0)

        user = self.env['res.users'].create({
            'name': 'Test Standard User',
            'login': 'test_standard_user@example.com',
            'email': 'test_standard_user@example.com',
        })

        employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
        self.assertEqual(len(employee), 1, "An employee should be created for this user")
        self.assertEqual(employee.name, user.name, "Employee name should match user name")
        self.assertEqual(employee.private_street, user.partner_id.name, "Employee private_street should match user partner name")

    def test_no_employee_creation_share_user(self):
        """Test that no employee is created for portal/share users."""
        user = self.env['res.users'].create({
            'name': 'Test Share User',
            'login': 'test_share_user@example.com',
            'email': 'test_share_user@example.com',
            'group_ids': [Command.clear(), Command.link(self.env.ref('base.group_portal').id)],
        })

        employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
        self.assertEqual(len(employee), 0, "No employee should be created for portal/share users")

    def test_no_employee_creation_when_already_exists(self):
        """Test that no additional employee is created if the user is linked to an employee at creation."""

        existing_employee = self.env['hr.employee'].create({
            'name': 'Existing Employee',
        })
        user = self.env['res.users'].create({
            'name': 'Test User With Existing Employee',
            'login': 'test_existing_emp_user@example.com',
            'email': 'test_existing_emp_user@example.com',
            'create_employee_id': existing_employee.id,
        })

        new_employees = self.env['hr.employee'].search([('user_id', '=', user.id), ('id', '!=', existing_employee.id)])
        self.assertEqual(len(new_employees), 0, "No additional employee should be created")
