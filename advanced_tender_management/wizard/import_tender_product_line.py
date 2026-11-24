# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
import base64
import io
import openpyxl
import xlrd
from odoo import models, fields, _
from odoo.exceptions import UserError


class ImportTenderProductLine(models.TransientModel):
    """Import tender product lines from xlsx files"""
    _name = "import.tender.product.line"
    _description = 'Import Tender Product Line'

    file = fields.Binary(string="File", required=True, help='tender file')
    tender_id = fields.Many2one(
        'tender.management',
        string='Tender',
        default=lambda self: self.env.context.get('active_id'),
        help='related tender'
    )

    def action_import_tender_product_lines(self):
        """Function for importing records from xlsx/xls file to tender product lines"""
        if not self.file:
            raise UserError(_('Please upload an Excel file.'))

        tender = self.tender_id or self.env['tender.management'].browse(self.env.context.get('active_id'))
        if not tender:
            raise UserError(_('No tender found. Please open the wizard from a tender.'))

        file_content = base64.b64decode(self.file)
        row_value = []

        # 1. Try reading as .xlsx via openpyxl
        try:
            wb = openpyxl.load_workbook(filename=io.BytesIO(file_content), data_only=True)
            sheet = wb.active
            rows = [list(r) for r in sheet.iter_rows(values_only=True) if any(r is not None for r in r)]
            if len(rows) > 1:
                row_value = rows[1:]  # skip header row
        except Exception:
            # 2. Fallback to xlrd for legacy .xls files
            try:
                book = xlrd.open_workbook(file_contents=file_content)
                sheet = book.sheet_by_index(0)
                for r in range(1, sheet.nrows):
                    row_value.append(sheet.row_values(r))
            except Exception as err:
                raise UserError(_('Please insert a valid Excel file (.xlsx or .xls): %s') % err)

        tender_product_lines = []
        default_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False) or self.env['uom.uom'].search([], limit=1)

        for row in row_value:
            if not row or not any(row):
                continue
            col0 = str(row[0]).strip() if row[0] is not None else ''
            col1 = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ''
            qty_raw = row[2] if len(row) > 2 and row[2] is not None else 1
            try:
                qty = int(float(qty_raw))
            except (ValueError, TypeError):
                qty = 1

            if not col0:
                continue

            # Section line (when description is missing)
            if not col1:
                tender_product_lines.append(fields.Command.create({
                    'name': col0,
                    'display_type': 'line_section'
                }))
                continue

            product_record = self.env['product.product'].search([('name', '=ilike', col0)], limit=1)
            if not product_record:
                product_record = self.env['product.product'].search([('default_code', '=ilike', col0)], limit=1)

            if product_record:
                tender_product_lines.append(fields.Command.create({
                    'product_id': product_record.id,
                    'name': col1 or product_record.name,
                    'product_qty': qty
                }))
            else:
                new_product = self.env['product.product'].create({
                    'name': col0,
                    'uom_id': default_uom.id if default_uom else False,
                    'uom_po_id': default_uom.id if default_uom else False,
                })
                tender_product_lines.append(fields.Command.create({
                    'product_id': new_product.id,
                    'name': col1 or col0,
                    'product_qty': qty
                }))

        if tender_product_lines:
            tender.write({
                'tender_product_line_ids': tender_product_lines
            })
