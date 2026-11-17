# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
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
################################################################################
import json
from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
try:
    from odoo.http.stream import content_disposition
except ImportError:
    from odoo.http import content_disposition
try:
    from odoo.http.dispatcher import serialize_exception as _serialize_exception
except ImportError:
    from odoo.http import serialize_exception as _serialize_exception
from odoo.tools import html_escape

ALLOWED_REPORT_MODELS = {
    'accounting.report.xlsx',
    'account.report.general.ledger.xlsx',
    'account.report.partner.ledger.xlsx',
    'account.aged.trial.balance.xlsx',
}


class XLSXReportController(http.Controller):

    @http.route('/account_xlsx', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name, **kw):
        """
        Function to retrieve an XLSX report.

        :param model: The model for which the report is generated.
        :type model: str
        :param options: Options for the report.
        :type options: str (JSON format)
        :param output_format: Output format for the report ('xlsx' in this case).
        :type output_format: str
        :param report_name: Name of the report.
        :type report_name: str
        :param kw: Additional keyword arguments.
        :return: Response containing the XLSX report.
        :rtype: werkzeug.wrappers.Response
        """
        if model not in ALLOWED_REPORT_MODELS:
            raise AccessError(_("Unauthorized report model: %s", model))

        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        report_obj.check_access('read')
        options = json.loads(options)
        token = kw.get('token', 'dummy-because-api-expects-one')
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                        ('Content-Disposition', content_disposition(f"{report_name}.xlsx"))
                    ]
                )
                report_obj.get_xlsx_report(options, response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
