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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Controller for generating dynamic sales reports in Excel format."""
import json

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.http.dispatcher import serialize_exception
from odoo.http.stream import content_disposition
from odoo.tools import html_escape


class TBXLSXReport(http.Controller):
    """Controller class to generate dynamic sale reports in Excel format.

    Methods:
        get_report_xlsx: Generate a dynamic sale report in Excel format and
        send it as a response to a HTTP POST request.
    """

    @http.route('/sale_dynamic_xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_data,
                        report_name, dfr_data):
        """Generate a dynamic sale report in Excel format and send it as a
        response to a HTTP POST request."""
        if model != 'sales.report':
            msg = "Unauthorized model access"
            raise AccessError(msg)
        request.env[model].check_access('read')
        report_obj = request.env[model]
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx')),
                    ],
                )
                report_obj.get_sale_xlsx_report(options, response, report_data,
                                                dfr_data)
                response.set_cookie('fileToken', token)
                return response
            return request.not_found()
        except Exception as e:
            se = serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se,
            }
            return request.make_response(html_escape(json.dumps(error)))
