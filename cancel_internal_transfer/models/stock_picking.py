from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def cancel_internal_transfer(self):
        """Automatically cancels internal stock transfers scheduled 2 days ago."""
        # Calculate start and end date of 2 days ago
        date_start = fields.Date.start_of(fields.Date.subtract(fields.Datetime.today(), days=2), granularity='day')
        date_end = fields.Date.end_of(fields.Date.subtract(fields.Datetime.today(), days=2), granularity='day')
        
        # Search for internal transfers in draft, waiting, confirmed, or assigned state scheduled 2 days ago
        picking_ids = self.sudo().search([
            ('picking_type_id.code', '=', 'internal'),
            ('state', 'in', ('draft', 'waiting', 'assigned')),
            ('scheduled_date', '>=', date_start),
            ('scheduled_date', '<=', date_end),
        ])
        for item in picking_ids:
            # Skip if any move is already completed
            if any(move.state == 'done' and not move.scrapped for move in item.move_ids):
                continue
            try:
                item.action_cancel()
            except:
                pass

