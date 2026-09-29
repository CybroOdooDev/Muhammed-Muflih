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
import json
import xml.etree.ElementTree as ET
from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """Excel report for one2many fields"""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self,
                        report_name='excel', **kwargs):
        """Used to get the report data that are fetched from the one2many"""
        model = kwargs.get('current_model')
        model_id = kwargs.get('id')
        field = kwargs.get('field')

        model_id_val = False
        if model_id and str(model_id).lower() not in ('false', 'none', 'undefined', '0', ''):
            try:
                model_id_val = int(model_id)
            except (ValueError, TypeError):
                model_id_val = False

        domain = []
        if model_id_val and field and field in request.env.get(model, {})._fields:
            domain = [(field, '=', model_id_val)]

        names = []
        if model and model in request.env:
            views = request.env['ir.ui.view'].sudo().search([
                ('model', '=', model),
                ('type', 'in', ['list', 'tree'])
            ], order='id asc', limit=1)
            if views and views.arch:
                try:
                    arch_str = views.arch if isinstance(views.arch, str) else str(views.arch)
                    tree = ET.fromstring(arch_str)
                    names = [f.get('name') for f in tree.findall('.//field') if f.get('name')]
                except Exception:
                    names = []

            # Filter names to existing fields on the model
            names = [fn for fn in names if fn in request.env[model]._fields]

            # Ensure product_id or product_template_id is included if present on model
            if 'product_id' in request.env[model]._fields and 'product_id' not in names:
                if 'name' in names:
                    names.insert(names.index('name'), 'product_id')
                else:
                    names.insert(0, 'product_id')
            elif 'product_template_id' in request.env[model]._fields and 'product_template_id' not in names and 'product_id' not in names:
                if 'name' in names:
                    names.insert(names.index('name'), 'product_template_id')
                else:
                    names.insert(0, 'product_template_id')

            # Fallback if names empty
            if not names:
                names = [fn for fn, fobj in request.env[model]._fields.items()
                         if fobj.store and fobj.type not in ('one2many', 'many2many', 'binary')]

            report_data = request.env[model].sudo().search_read(
                domain=domain,
                fields=names
            )
        else:
            report_data = []

        uid = getattr(request.session, 'uid', None) or request.env.uid
        report_obj = request.env['one2many.report.excel'].sudo().with_user(uid)
        output_format = 'xlsx'
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(report_data, names or ['id'], response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

