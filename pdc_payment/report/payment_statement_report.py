# -*- coding: utf-8 -*-
from odoo import api, models


class ReportPaymentStatement(models.AbstractModel):
    _name = 'report.pdc_payment.report_payment_statement'
    _description = 'Payment Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data and 'partners' in data:
            report_data = data
        elif docids:
            wizard = self.env['payment.statement'].browse(docids[0])
            report_data = wizard._get_report_data()
        else:
            report_data = {}

        return {
            'doc_ids': docids,
            'doc_model': 'payment.statement',
            'data': report_data,
            'company': self.env.company,
        }
