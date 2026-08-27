# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosCustomMessage(models.Model):
    _name = 'pos.custom.message'
    _inherit = ['pos.load.mixin']
    _description = "Pos Custom Message"
    _rec_name = 'title'

    message_type = fields.Selection([("inform", 'Information'), (
        'warning', 'Warning'), ('alert', 'Alert')], default='inform',
                                    required=True)
    title = fields.Char(string="Title", required=True)
    message = fields.Text(string="Message")
    input_time = fields.Char(
        compute="get_time", string="Message Execution Time")
    hours = fields.Char(size=2, required=True)
    minutes = fields.Char(size=2, required=True)
    period = fields.Selection(
        [('AM', 'AM'), ('PM', 'PM')], default='PM', required=True)
    point_of_sale_ids = fields.Many2many('pos.config', string="Assign To POS")

    @api.model
    def _load_pos_data_domain(self, data, config):
        """ Return domain for loading custom messages assigned to the current POS config. """
        return [('id', 'in', config.custom_message_ids.ids)] if config.custom_message_ids else [('id', '=', False)]

    @api.model
    def _load_pos_data_fields(self, config):
        """ Return list of fields to load in the POS frontend model. """
        return ['id', 'message_type', 'title', 'input_time', 'hours', 'minutes',
                'period', 'message']

    @api.depends('hours', 'minutes', 'period')
    def get_time(self):
        """ Compute the 24-hour formatted execution time string (HH:MM) from hours, minutes, and period. """
        for self_obj in self:
            if not self_obj.hours or not self_obj.minutes or not self_obj.period:
                self_obj.input_time = False
                continue
            try:
                h = int(self_obj.hours)
                m = int(self_obj.minutes)
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    self_obj.input_time = False
                    continue
                if self_obj.period == 'AM':
                    h = 0 if h == 12 else h
                elif self_obj.period == 'PM':
                    h = 12 if h == 12 else h + 12
                self_obj.input_time = f"{h:02d}:{m:02d}"
            except (ValueError, TypeError):
                self_obj.input_time = False

    @api.constrains('hours', 'minutes')
    def validate_hours_minute(self):
        """ Validate that hours (1-12) and minutes (0-59) are valid integer formats. """
        for record in self:
            if not record.hours or not record.minutes:
                continue
            if not (record.hours.isdigit() and record.minutes.isdigit()):
                raise ValidationError("Hour and minute must be integer type")
            if not int(record.hours) in range(1, 13):
                raise ValidationError(
                    "Invalid Time Format, Hours must be in range(1-12)")
            if not int(record.minutes) in range(0, 60):
                raise ValidationError("Minute must be in range (0-60)")
            if len(record.hours) == 1:
                record.hours = '0' + record.hours
            if len(record.minutes) == 1:
                record.minutes = '0' + record.minutes


class PosConfig(models.Model):
    """ Inherit pos.config to add relation to custom messages. """
    _inherit = 'pos.config'

    custom_message_ids = fields.Many2many(
        'pos.custom.message', string="Custom Messages")


class ResConfigSettings(models.TransientModel):
    """ Inherit res.config.settings to manage POS custom messages in POS settings. """
    _inherit = 'res.config.settings'

    pos_custom_message_ids = fields.Many2many(
        related='pos_config_id.custom_message_ids', readonly=False)


class PosSession(models.Model):
    """ Inherit pos.session to include pos.custom.message in loaded POS data models. """
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """ Add pos.custom.message to the list of models loaded into POS session. """
        data = super()._load_pos_data_models(config_id)
        data += ['pos.custom.message']
        return data
