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
from odoo import fields, models


class ScrapManagementReport(models.TransientModel):
    """This class defining model for the wizard for printing scrap management
    report."""
    _name = 'scrap.management.report'
    _description = 'Report of Scrap Management'

    filter = fields.Selection(
        default="product_wise", selection=[('product_wise', 'Product Wise'),
                                           ('state_wise', 'State Wise')],
        help="field to choose filter of report", string="Based On")
    product_ids = fields.Many2many('product.product',
                                   string="Product",
                                   help="Field to choose product for report")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),
                              ('confirm', 'Confirm')],
                             default="done", string="State",
                             help="Field to specify state of report")
    from_date = fields.Date(string="Start date",
                            help="Field to choose start date of report")
    to_date = fields.Date(string="End date",
                          help="Field to end date filter of report")

    def action_print_pdf(self):
        """
        Summary:
           function to print pdf
        Return:
           pdf report
        """
        if self.filter == 'product_wise':
            query = """SELECT scrap_management.scrap_management_number,
            scrap_management.scrap_order_id,
            COALESCE(product_template.name->>'en_US', product_template.name::text) AS product,
            scrap_management.state,
            stock_move.product_id,
            scrap_management.date,
            COALESCE(stock_move.reference, '') AS name
            FROM scrap_management
            INNER JOIN stock_move ON scrap_management.scrap_order_id = stock_move.id
            INNER JOIN product_product ON product_product.id = stock_move.product_id
            INNER JOIN product_template ON product_template.id = product_product.product_tmpl_id
            WHERE 1=1
            """
            params = []
            if self.product_ids:
                query += " AND stock_move.product_id IN %s"
                params.append(tuple(self.product_ids.ids))
            if self.from_date:
                query += " AND scrap_management.date >= %s"
                params.append(self.from_date)
            if self.to_date:
                query += " AND scrap_management.date <= %s"
                params.append(self.to_date)
            self.env.cr.execute(query, params)
            datas = self.env.cr.dictfetchall()
            data = {
                'form': self.read()[0],
                'datas': datas,
                'from_date': self.from_date,
                'to_date': self.to_date
            }
            return self.env.ref(
                'company_scrap_management'
                '.action_scrap_management_product_wise').report_action(
                None,
                data=data)
        if self.filter == 'state_wise':
            query = """SELECT scrap_management.scrap_management_number,
            COALESCE(stock_move.reference, '') AS name,
            scrap_management.scrap_order_id,
            scrap_management.state,
            stock_move.product_id,
            scrap_management.date
            FROM scrap_management
            INNER JOIN stock_move ON scrap_management.scrap_order_id = stock_move.id
            WHERE 1=1
            """
            params = []
            if self.state:
                query += " AND scrap_management.state = %s"
                params.append(self.state)
            if self.from_date:
                query += " AND scrap_management.date >= %s"
                params.append(self.from_date)
            if self.to_date:
                query += " AND scrap_management.date <= %s"
                params.append(self.to_date)
            self.env.cr.execute(query, params)
            datas = self.env.cr.dictfetchall()
            data = {
                'form': self.read()[0],
                'datas': datas,
                'state': self.state,
                'from_date': self.from_date,
                'to_date': self.to_date
            }
            return self.env.ref(
                'company_scrap_management'
                '.action_scrap_management_state_wise').report_action(None,
                                                                     data=data)
