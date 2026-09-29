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
from random import randint
from odoo import fields, models


class ActivityTag(models.Model):
    """Model to add tags to an activity"""
    _name = "activity.tag"
    _description = "Activity Tag"

    name = fields.Char(string='Tag Name',
                       help='Name of the activity tag.',
                       required=True,
                       translate=True)
    color = fields.Integer(string='Color',
                           help='Field that gives color to the tag.',
                           default=randint(1, 11))

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"), ]
