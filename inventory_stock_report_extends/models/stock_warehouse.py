from odoo import models, fields, api


class StockReportQuantity(models.AbstractModel):
    _name = 'report.inventory_stock_report_extends.report_stock_info'
    _description = 'Stock Report Quantity'

    @api.model
    def _get_report_values(self, docids, data=None):
        product = self.env['product.product']
        headers = False
        if self.env.user.stock_report_type == 'warehouse':
            headers = self.env.user.stock_selected_warehouse_id
            data = product.product_product_report(docids, headers)
        else:
            headers = self.env.user.stock_selected_location_id
            to_date = self.env.user.stock_report_context
            data = product.product_product_report_with_location(docids, headers, to_date)
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'data': data,
            'header': product.get_current_company(headers),
        }


class StockReportCost(models.AbstractModel):
    _name = 'report.inventory_stock_report_extends.stock_info_with_cost'
    _description = 'Stock Report Cost'

    @api.model
    def _get_report_values(self, docids, data=None):
        product = self.env['product.product']
        headers = False
        if self.env.user.stock_report_type == 'warehouse':
            headers = self.env.user.stock_selected_warehouse_id
            data = product.product_product_report(docids, headers)
        else:
            headers = self.env.user.stock_selected_location_id
            to_date = self.env.user.stock_report_context
            data = product.product_product_report_with_location(docids, headers,
                                                                to_date)
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'data': data,
            'header': product.get_current_company(headers),
        }


class StockReportSerial(models.AbstractModel):
    _name = 'report.inventory_stock_report_extends.info_with_serial'
    _description = 'Stock Report Serial'

    @api.model
    def _get_report_values(self, docids, data=None):
        product = self.env['product.product']
        headers = False
        if self.env.user.stock_report_type == 'warehouse':
            headers = self.env.user.stock_selected_warehouse_id
            data = product.product_product_report_with_serial(docids, headers)
        else:
            headers = self.env.user.stock_selected_location_id
            to_date = self.env.user.stock_report_context
            data = product.product_product_report_with_serial_location(
                docids, headers, to_date)
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'data': data,
            'header': product.get_current_company(headers),
        }


class StockReportSerialCost(models.AbstractModel):
    _name = 'report.inventory_stock_report_extends.info_cost_serial'
    _description = 'Stock Report Serial Cost'

    @api.model
    def _get_report_values(self, docids, data=None):
        product = self.env['product.product']
        headers = False
        if self.env.user.stock_report_type == 'warehouse':
            headers = self.env.user.stock_selected_warehouse_id
            data = product.product_product_report_with_serial(docids, headers)
        else:
            headers = self.env.user.stock_selected_location_id
            to_date = self.env.user.stock_report_context
            data = product.product_product_report_with_serial_location(
                docids, headers, to_date)
        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'data': data,
            'header': product.get_current_company(headers),
        }


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'
    
    def session_info(self):
        info = super().session_info()
        info["show_report"] = self.env.user.has_group('inventory_stock_report_extends.can_print_inventory_report')
        return info


class ResUsers(models.Model):
    _inherit = 'res.users'

    stock_selected_warehouse_id = fields.Many2one(
        'stock.warehouse', string="Stock Report Warehouse")
    stock_selected_location_id = fields.Many2one(
        'stock.location', string="Stock Report Locations")
    stock_report_context = fields.Datetime('Stock Report Context')
    stock_report_type = fields.Selection(
        selection=[('warehouse', 'Warehouse'), ('location', 'Location')])

    @api.model
    def update_location_report_context(self, context):
        if context.get('is_location_report'):
            self.env.user.sudo().write({
                'stock_selected_location_id': context.get('location'),
                'stock_report_context': context.get('to_date'),
                'stock_report_type': 'location'
            })
        else:
            self.env.user.sudo().write({
                'stock_report_type': 'warehouse'
            })


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def action_update_context(self):
        self.env.user.sudo().write({
            'stock_selected_warehouse_id': self.id,
            'stock_report_type': 'warehouse'
        })
        return True

    def action_remove_context(self):
        self.env.user.sudo().write({
            'stock_selected_warehouse_id': False
        })
        return True

    def get_current_warehouses(self):
        self.env.user.sudo().write({
            'stock_selected_warehouse_id': False,
            'stock_selected_location_id': False,
            'stock_report_type': 'warehouse'
        })
        warehouse_ids = self.env['stock.warehouse'].search([], order='name')
        return warehouse_ids.sudo().read(fields=['id', 'name', 'code'])


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def action_print_stock_report(self, active_ids, context, item):
        warehouse = self.env.user.stock_selected_warehouse_id
        if item['key'] == 'product_product_report_with_cost_serial':
            data = self.product_product_report_with_serial(active_ids, warehouse)
        elif item['key'] == 'product_product_report_with_serial':
            data = self.product_product_report_with_serial(active_ids, warehouse)
        elif item['key'] == 'product_product_report_with_cost':
            data = self.product_product_report(active_ids, warehouse)
        else:
            data = self.product_product_report(active_ids, warehouse)
        vals = {
            'data': data,
            'warehouse': warehouse,
            'header': self.get_current_company(warehouse),
            'user': self.env.user
        }
        return self.env.ref(item['xml_id']).report_action(None, data=vals)


    def product_product_report_with_serial(self, active_ids, warehouse_id):
        product_id = self.product_product_report(active_ids, warehouse_id)
        for rec in product_id:
            rec['serials'] = self.get_sequence_for_report(rec, warehouse_id)
        return product_id

    def product_product_report(self, active_ids, warehouse_id):
        if warehouse_id:
            product = self.with_context(warehouse=warehouse_id.id).browse(active_ids)
        else:
            product = self.browse(active_ids)
        return product.with_user(self.env.uid).read(fields=[
            'qty_available', 'total_value', 'default_code', 'name', 'avg_cost', 'tracking'])

    def product_product_report_with_location(self, active_ids, location, to_date=None):
        if to_date and location:
            product = self.with_context(to_date=to_date, location=location.id).browse(active_ids)
        elif to_date:
            product = self.with_context(to_date=to_date).browse(active_ids)
        elif location:
            product = self.with_context(location=location.id).browse(active_ids)
        else:
            product = self.browse(active_ids)
        return product.with_user(self.env.uid).read(fields=[
            'qty_available', 'total_value', 'default_code', 'name', 'avg_cost', 'tracking'])

    def product_product_report_with_serial_location(self, active_ids, location, to_date=None):
        product_id = self.product_product_report_with_location(active_ids, location,
                                                                to_date)
        for rec in product_id:
            rec['serials'] = self.get_sequence_for_report_location(rec, location)
        return product_id

    def get_current_company(self, warehouse):
        time_plus = fields.datetime.strptime(self.env.user.tz_offset, '%z')
        time_stamp = fields.Datetime.now() + time_plus.utcoffset()
        return f"{self.env.company.name} - {warehouse.name if warehouse else ''} - {time_stamp}"

    def get_current_warehouse_id(self):
        return self.env.user.stock_selected_warehouse_id

    def get_sequence_for_report(self, product, warehouse):
        if product['tracking'] != 'serial':
            return False
        if warehouse:
            lot_ids = self.env['stock.quant'].search([
                ('product_id', '=', product['id']),
                ('location_id.usage', '=', 'internal'),
                ('inventory_quantity_auto_apply', '>', 0),
                ('location_id', '=', warehouse.lot_stock_id.id)
            ])
        else:
            lot_ids = self.env['stock.quant'].search([
                ('product_id', '=', product['id']),
                ('inventory_quantity_auto_apply', '>', 0),
                ('location_id.usage', '=', 'internal'),
                ('location_id.company_id', '=', self.env.company.id)
            ])
        return [[rec.lot_id.name, rec.available_quantity] for rec in lot_ids if rec.lot_id]

    def get_sequence_for_report_location(self, product, location):
        if product['tracking'] != 'serial':
            return False
        if location:
            lot_ids = self.env['stock.quant'].search([
                ('product_id', '=', product['id']),
                ('location_id', '=', location.id),
                ('inventory_quantity_auto_apply', '>', 0)
            ])
        else:
            lot_ids = self.env['stock.quant'].search([
                ('product_id', '=', product['id']),
                ('location_id.company_id', '=', self.env.company.id),
                ('inventory_quantity_auto_apply', '>', 0)
            ])
        return [[rec.lot_id.name, rec.available_quantity] for rec in lot_ids if rec.lot_id]


class StockReportQuantity(models.AbstractModel):
    _name = 'report.inventory_stock_report_extends.available_device'
    _description = 'Report Available Device'

    def get_current_company(self):
        time_plus = fields.datetime.strptime(self.env.user.tz_offset, '%z')
        time_stamp = fields.Datetime.now() + time_plus.utcoffset()
        return f"{self.env.company.name} - {time_stamp}"

    @api.model
    def _get_report_values(self, docids, data=None):
        query = f"""
        SELECT
            pt.name->>'en_US' AS item,
            sl.name AS name,
            pp.default_code AS default_code,
            po.date_order AS purchase_date,
            pol.price_unit
        FROM
            stock_quant sq
        JOIN
            product_product pp ON sq.product_id = pp.id
        JOIN 
            product_template pt ON pp.product_tmpl_id = pt.id
        JOIN
            stock_lot sl ON sq.lot_id = sl.id
        JOIN
            stock_location ls ON sq.location_id = ls.id
        JOIN
            stock_move_line sml ON sq.lot_id = sml.lot_id  -- Link via move line
        JOIN
            stock_move sm ON sml.move_id = sm.id  -- Get parent move
        JOIN
            purchase_order_line pol ON sm.purchase_line_id = pol.id  -- Now from stock_move
        JOIN
            purchase_order po ON pol.order_id = po.id
        WHERE
            sm.state = 'done'  -- Check state on stock_move
            AND sq.quantity > 0
            AND pt.tracking != 'none'
            AND ls.usage = 'internal'
            AND 
                po.company_id = {self.env.company.id}
        """
        self._cr.execute(query)
        stock_data = self._cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'product.product',
            'data': stock_data,
            'header': self.get_current_company(),
        }
