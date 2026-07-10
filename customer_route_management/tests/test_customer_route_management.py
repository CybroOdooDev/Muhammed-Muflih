from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestCustomerRouteManagement(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.delivery_route = cls.env["delivery.route"].create({
            "name": "North Route",
        })
        cls.route_line = cls.env["route.line"].create({
            "route": "North Zone",
            "delivery_route_link_id": cls.delivery_route.id,
        })
        cls.partner_a.location_id = cls.route_line
        cls.child_contact = cls.env["res.partner"].create({
            "name": "partner_a_child",
            "parent_id": cls.partner_a.id,
            "location_id": cls.route_line.id,
            "company_id": False,
        })
        cls.other_partner = cls.env["res.partner"].create({
            "name": "other_partner",
            "company_id": False,
        })

    def test_route_line_keeps_route_customers(self):
        self.assertEqual(self.delivery_route.route_line_ids, self.route_line)
        self.assertEqual(
            self.route_line.cust_list_ids,
            self.partner_a | self.child_contact,
        )

    def test_get_all_dues_includes_parent_and_child_posted_invoices(self):
        parent_invoice = self.init_invoice(
            move_type="out_invoice",
            partner=self.partner_a,
            amounts=[100.0],
            post=True,
        )
        child_invoice = self.init_invoice(
            move_type="out_invoice",
            partner=self.child_contact,
            amounts=[50.0],
            post=True,
        )
        self.init_invoice(
            move_type="out_invoice",
            partner=self.other_partner,
            amounts=[75.0],
            post=True,
        )
        self.init_invoice(
            move_type="out_invoice",
            partner=self.partner_a,
            amounts=[25.0],
            post=False,
        )

        dues = self.partner_a.get_all_dues()
        due_names = {due["name"] for due in dues}

        self.assertEqual(due_names, {parent_invoice.name, child_invoice.name})
        self.assertEqual(len(dues), 2)
        self.assertSetEqual(
            {due["amount_residual_signed"] for due in dues},
            {100.0, 50.0},
        )
