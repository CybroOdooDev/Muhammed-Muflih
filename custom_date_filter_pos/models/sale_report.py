from odoo import models, fields


class SaleReport(models.Model):
    """Inherit Sale Report to add create_date field for date filtering."""
    _inherit = 'sale.report'

    create_date = fields.Datetime('Create Date')

    def _select_additional_fields(self):
        """Add create_date field to SQL SELECT query for sales analysis report."""
        res = super()._select_additional_fields()
        res['create_date'] = "s.create_date"
        return res

    def _group_by_sale(self):
        """Include create_date in SQL GROUP BY query for sales analysis report."""
        res = super()._group_by_sale()
        res += """,
            s.create_date"""
        return res

