from odoo import models, fields, _
from odoo.exceptions import UserError
import json
import io

import xlsxwriter
from odoo.tools.json import json_default


class orderLineExportWizard(models.TransientModel):
    _name = 'pos.orderline.export.wizard'
    _description = 'Order Line Export Wizard'

    line_ids = fields.Many2many('pos.order.line', compute="_compute_line_ids")
    report_type = fields.Selection([('all', 'Complete'), ('with', 'With Lot')])

    def _compute_line_ids(self):
        """Compute active order line records from context."""
        self.line_ids = self.env.context.get('active_ids', False)

    def button_print_all(self):
        """Export all non-refunded POS order lines to Excel."""
        data = self.line_ids.filtered(lambda rec: not rec.order_id.is_refunded_or_refund_order).read([
            'order_date', 'order_reference', 'categ_id', 'product_list_price', 'order_id',
            'product_ref', 'product_id', 'qty', 'price_unit', 'margin', 'pack_lot_ids', 'pos_reference'
        ])
        if not data:
            raise UserError(_("No valid POS order lines found to export."))
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'pos.orderline.export.wizard',
                'output_format': 'xlsx',
                'options': json.dumps(data, default=json_default),
                'report_name': 'POS Order Line'
            },
        }

    def button_print_serial(self):
        """Export only POS order lines containing serial or lot numbers to Excel."""
        data = self.line_ids.filtered(lambda rec: not rec.order_id.is_refunded_or_refund_order).read([
            'order_date', 'order_reference', 'categ_id', 'product_list_price', 'order_id',
            'product_ref', 'product_id', 'qty', 'price_unit', 'margin', 'pack_lot_ids', 'pos_reference'
        ])
        context = [item for item in data if item.get('pack_lot_ids')]
        if not context:
            raise UserError(_("No order lines with Serial / Lot numbers were found among the selected records."))
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': 'pos.orderline.export.wizard',
                'output_format': 'xlsx',
                'options': json.dumps(context, default=json_default),
                'report_name': 'POS Order Line'
            },
        }

    def get_xlsx_report(self, data, response):
        """Generate and stream the XLSX report using xlsxwriter."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        title = workbook.add_format({'font_size': '10px', 'align': 'center',
                                     'bold': True})
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        sheet.write(0, 0, 'Order Date', title)
        sheet.write(0, 1, 'Order Ref', title)
        sheet.write(0, 2, 'Receipt Number', title)
        sheet.write(0, 3, 'Internal Reference', title)
        sheet.write(0, 4, 'Product Name', title)
        sheet.write(0, 5, 'Product Category', title)
        sheet.write(0, 6, 'Serial Number', title)
        sheet.write(0, 7, 'Quantity', title)
        sheet.write(0, 8, 'Unit Price', title)
        sheet.write(0, 9, 'Margin', title)
        sheet.write(0, 10, 'List Price', title)
        sheet.write(0, 11, 'Lot Number', title)
        row = 1
        max_width = {
            'name': 10,
            'pos_reference': 10,
            'product_id': 10,
            'product_ref': 10,
            'categ_id': 10,
            'lot_name': 10
        }
        for item in data:
            order_date = str(item.get('order_date') or '')
            order_ref = item.get('order_reference') or ''
            pos_ref = item.get('pos_reference') or ''
            product_ref = item.get('product_ref') or ''
            product_name = item['product_id'][1] if item.get('product_id') else ''
            categ_name = item['categ_id'][1] if item.get('categ_id') else ''

            max_width['pos_reference'] = max(max_width['pos_reference'], len(pos_ref))
            max_width['name'] = max(max_width['name'], len(order_ref))
            max_width['product_id'] = max(max_width['product_id'], len(product_name))
            max_width['product_ref'] = max(max_width['product_ref'], len(product_ref))
            max_width['categ_id'] = max(max_width['categ_id'], len(categ_name))

            lot_ids = self.env['pos.pack.operation.lot'].browse(item.get('pack_lot_ids', []))
            if lot_ids:
                for lot in lot_ids:
                    lot_name = lot.lot_name or ''
                    max_width['lot_name'] = max(max_width['lot_name'], len(lot_name))
                    sheet.write(row, 0, order_date, txt)
                    sheet.write(row, 1, order_ref, txt)
                    sheet.write(row, 2, pos_ref, txt)
                    sheet.write(row, 3, product_ref, txt)
                    sheet.write(row, 4, product_name, txt)
                    sheet.write(row, 5, categ_name, txt)
                    sheet.write(row, 6, item.get('price_unit', ''), txt)
                    sheet.write(row, 7, 1, txt)
                    sheet.write(row, 8, item.get('price_unit', ''), txt)
                    sheet.write(row, 9, item.get('margin', ''), txt)
                    sheet.write(row, 10, item.get('product_list_price', ''), txt)
                    sheet.write(row, 11, lot_name, txt)
                    row += 1
            else:
                sheet.write(row, 0, order_date, txt)
                sheet.write(row, 1, order_ref, txt)
                sheet.write(row, 2, pos_ref, txt)
                sheet.write(row, 3, product_ref, txt)
                sheet.write(row, 4, product_name, txt)
                sheet.write(row, 5, categ_name, txt)
                sheet.write(row, 6, item.get('price_unit', ''), txt)
                sheet.write(row, 7, item.get('qty', ''), txt)
                sheet.write(row, 8, item.get('price_unit', ''), txt)
                sheet.write(row, 9, item.get('margin', ''), txt)
                sheet.write(row, 10, item.get('product_list_price', ''), txt)
                sheet.write(row, 11, "", txt)
                row += 1

        sheet.set_column(0, 0, 16)
        sheet.set_column(1, 1, max(max_width['name'], 12))
        sheet.set_column(2, 2, max(max_width['pos_reference'], 12))
        sheet.set_column(3, 3, max(max_width['product_ref'], 12))
        sheet.set_column(4, 4, max(max_width['product_id'], 15))
        sheet.set_column(5, 5, max(max_width['categ_id'], 15))
        sheet.set_column(6, 10, 10)
        sheet.set_column(11, 11, max(max_width['lot_name'], 12))

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
