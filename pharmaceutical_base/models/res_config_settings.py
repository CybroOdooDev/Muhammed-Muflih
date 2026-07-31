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

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ResConfigSettings(models.TransientModel):
    """Configuration settings for the Pharmaceutical ERP module, allowing toggling of major features."""
    _inherit = 'res.config.settings'
    module_pharma_vendor_qualification = fields.Boolean(
        string='Enable Vendor Qualification',
        help='Approved Vendor List (AVL), vendor questionnaire portal, and AVL '
             'enforcement on purchase orders.',
    )
    module_pharma_capa_deviation = fields.Boolean(
        string='Enable CAPA &amp; Deviation Management',
        help='Deviation and CAPA models, menus, and their couplings on the '
             'OOS / IPQC / QC / BMR workflow.',
    )
    module_pharma_sop_training = fields.Boolean(
        string='Enable SOP &amp; Training Management',
        help='SOP lifecycle, auto-generated training records, and '
             'training-gated BMR step sign-off.',
    )
    module_pharma_traceability_coa = fields.Boolean(
        string='Enable Traceability, CoA &amp; Audit Trail',
        help='Certificate of Analysis, Batch Genealogy, and Audit Trail.',
    )

    # GMP quarantine-to-stock locations, stored per company on res.company.
    pharma_quarantine_location_id = fields.Many2one(
        related='company_id.pharma_quarantine_location_id',
        readonly=False,
        string='Quarantine Location',
        help='Internal location where incoming goods are received and held '
             'pending QC disposition.',
    )
    pharma_released_location_id = fields.Many2one(
        related='company_id.pharma_released_location_id',
        readonly=False,
        string='Released Stock Location',
        help='Internal location material is moved to when QC approves the lot.',
    )
    pharma_rejected_location_id = fields.Many2one(
        related='company_id.pharma_rejected_location_id',
        readonly=False,
        string='Rejected Location',
        help='Internal location material is moved to when QC rejects the lot.',
    )

    pharma_gmp_certificate_required = fields.Boolean(
        related='company_id.pharma_gmp_certificate_required',
        readonly=False,
        string='GMP Certificate',
        help='Require GMP certificate upload for vendor qualification. Hide the field when disabled.',
    )

    # Qualification / passing scores, stored per company on res.company.
    pharma_vendor_approval_percentage = fields.Float(
        related='company_id.pharma_vendor_approval_percentage',
        readonly=False,
        string='Vendor Qualification Approval (%)',
        help='Minimum audit score (%) required for vendor approval. Lower scores are marked Not Qualified.',
    )
    pharma_training_passing_score = fields.Float(
        related='company_id.pharma_training_passing_score',
        readonly=False,
        string='SOP Training Passing Score (%)',
        help='Minimum assessment score (%) required to pass SOP training. Lower scores are marked Failed.',
    )

    def set_values(self):
        """Block an out-of-range score while its module toggle is enabled, then save."""
        if self.module_pharma_vendor_qualification and not 0 < self.pharma_vendor_approval_percentage <= 100:
            raise ValidationError(_(
                'The Vendor Qualification Approval Percentage must be greater '
                'than zero and at most 100 when Vendor Qualification is enabled.'))
        if self.module_pharma_sop_training and not 0 < self.pharma_training_passing_score <= 100:
            raise ValidationError(_(
                'The SOP Training Passing Score must be greater than zero '
                'and at most 100 when SOP & Training Management is enabled.'))
        return super().set_values()

    # Vendor Qualification, CAPA & Deviation, SOP & Training and Traceability/CoA
    # are delivered as separately-installable modules (pharma_vendor_qualification,
    # pharma_capa_deviation, pharma_sop_training, pharma_traceability_coa). Their
    # ``module_*`` booleans are handled natively by Odoo, which installs/uninstalls
    # those modules on save.
