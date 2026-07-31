# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ResCompany(models.Model):
    """Adds the GMP quarantine-to-stock location configuration to the company."""
    _inherit = 'res.company'

    pharma_quarantine_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Quarantine Location',
        domain="[('usage', '=', 'internal')]",
        help='Internal location where incoming goods are received and held '
             'pending QC disposition.',
    )
    pharma_released_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Released Stock Location',
        domain="[('usage', '=', 'internal')]",
        help='Internal location material is moved to when QC approves the lot.',
    )
    pharma_rejected_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Rejected Location',
        domain="[('usage', '=', 'internal')]",
        help='Internal location material is moved to when QC rejects the lot.',
    )

    pharma_gmp_certificate_required = fields.Boolean(
        string='GMP Certificate',
        help='Require GMP certificate upload for vendor qualification. Hide the field when disabled.',
    )

    pharma_vendor_approval_percentage = fields.Float(
        string='Vendor Qualification Approval (%)',
        default=70.0,
        help='Minimum audit score (%) required for vendor approval. Lower scores are marked Not Qualified.',
    )
    pharma_training_passing_score = fields.Float(
        string='SOP Training Passing Score (%)',
        default=80.0,
        help='Minimum assessment score (%) required to pass SOP training. Lower scores are marked Failed.',
    )

    @api.constrains(
        'pharma_quarantine_location_id',
        'pharma_released_location_id',
        'pharma_rejected_location_id',
    )
    def _check_pharma_locations(self):
        """Ensure the configured locations are internal and all distinct."""
        for company in self:
            locations = [
                ('Quarantine Location', company.pharma_quarantine_location_id),
                ('Released Stock Location', company.pharma_released_location_id),
                ('Rejected Location', company.pharma_rejected_location_id),
            ]
            configured = [(label, loc) for label, loc in locations if loc]

            for label, loc in configured:
                if loc.usage != 'internal':
                    raise ValidationError(_(
                        "The %s must be an internal location.", label))

            location_ids = [loc.id for _label, loc in configured]
            if len(location_ids) != len(set(location_ids)):
                raise ValidationError(_(
                    "The Quarantine, Released Stock and Rejected locations "
                    "must all be different from one another."))

    @api.constrains(
        'pharma_vendor_approval_percentage',
        'pharma_training_passing_score',
    )
    def _check_pharma_scores(self):
        """Keep the qualification and passing scores within 0-100, never zero.

        A zero score would silently pass every audit and every assessment, so
        it is rejected outright rather than treated as "no threshold".
        """
        for company in self:
            scores = [
                ('Vendor Qualification Approval Percentage',
                 company.pharma_vendor_approval_percentage),
                ('SOP Training Passing Score',
                 company.pharma_training_passing_score),
            ]
            for label, score in scores:
                if not 0 < score <= 100:
                    raise ValidationError(_(
                        "The %s must be greater than 0 and at most 100.", label))
