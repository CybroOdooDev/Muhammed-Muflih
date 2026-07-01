# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
# ###############################################################################
from odoo.tests.common import TransactionCase


class TestMrpProduction(TransactionCase):
    """Test cases for MRP Production cost per hour computation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.employee_model = cls.env["hr.employee"]
        cls.production_model = cls.env["mrp.production"]
        cls.workcenter_model = cls.env["mrp.workcenter"]
        cls.workorder_model = cls.env["mrp.workorder"]

        # Create a storable product for manufacturing orders
        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "type": "consu",
        })

        # Logged in employee
        cls.employee = cls.env.user.employee_id
        if not cls.employee:
            cls.employee = cls.employee_model.create({
                "name": "Test Employee",
                "user_id": cls.env.user.id,
            })


        # Set employee hourly cost
        cls.employee.hour_per_cost = 100.0

        # Create work center
        cls.workcenter = cls.workcenter_model.create({
            "name": "Test Work Center",
            "time_efficiency": 100,
        })

        # Add employee cost line if model exists
        if hasattr(cls.workcenter, "cost_per_employee_ids"):
            employee_cost_model = cls.env[
                cls.workcenter.cost_per_employee_ids._name
            ]
            employee_cost_model.create({
                "mrp_workcenter_id": cls.workcenter.id,
                "employee_id": cls.employee.id,
            })



    def test_compute_cost_per_hour(self):
        """Test computation of cost_per_hour."""


        production = self.production_model.create({
            "product_id": self.product.id,
            "product_uom_id": self.product.uom_id.id,
            "product_qty": 1,
        })

        workorder = self.workorder_model.create({
            "name": "Test Workorder",
            "production_id": production.id,
            "workcenter_id": self.workcenter.id,
            "product_uom_id": self.product.uom_id.id,
            "duration": 2.0,
        })

        production.invalidate_recordset()
        production._compute_cost_per_hour()

        expected_cost = self.employee.hour_per_cost * workorder.duration


        self.assertEqual(
            production.cost_per_hour,
            expected_cost,
            "Cost per hour computation is incorrect.",
        )
