import json
from odoo import http
from odoo.http import content_disposition, request, serialize_exception
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """XLSX report controller for exporting POS order lines"""
    @http.route('/xlsx_reports', type='http', auth="user", csrf=False)
    def create_xlsx_reports(self, model, options, output_format, report_name, **kwargs):
        report_obj = request.env[model].with_user(request.session.uid)
        options = json.loads(options)
        token = 'dummy-because-api-expects-one'

        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
