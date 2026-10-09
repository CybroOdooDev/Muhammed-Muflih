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
import base64
import requests
from odoo.exceptions import UserError
from odoo import exceptions, fields, models, _


class UploadFile(models.TransientModel):
    """
    For opening wizard view
    """
    _name = "upload.file"
    _description = "Upload File"

    file = fields.Binary(string="Attachment", help="Select a file to upload")
    file_name = fields.Char(string="File Name", help="Name of the attachment")

    def action_upload_file(self):
        """
        Upload file to onedrive
        """
        if not self.file:
            raise exceptions.UserError(_('Please Attach a file to upload.'))
        token = self.env['onedrive.dashboard'].search([], order='id desc',
                                                      limit=1)
        if isinstance(self.file, (str, bytes)):
            try:
                file_content = base64.b64decode(self.file)
            except Exception:
                file_content = self.file if isinstance(self.file, bytes) else self.file.encode('utf-8')
        else:
            attachment = self.env["ir.attachment"].search(
                [('res_id', '=', self.id), ('res_model', '=', 'upload.file')],
                limit=1)
            file_content = attachment.raw if attachment else b''
        folder = self.env['ir.config_parameter'].sudo().get_str(
            'onedrive_integration_odoo.onedrive_folder', '')
        if not token or not folder:
            raise exceptions.UserError(
                _('Please setup Access Token and Folder Name.'))
        if token.token_expiry_date <= str(fields.Datetime.now()):
            token.generate_onedrive_refresh_token()

        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder}/{self.file_name}:/content"
        headers = {
                'Authorization': f'Bearer {token.onedrive_access_token }',
                'Content-Type': 'application/octet-stream'
            }
        try:
            response = requests.put(url, headers=headers, data=file_content)
            if response.status_code in [200, 201]:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'message': 'File uploaded successfully to OneDrive.'
                                   'Please refresh',
                    }
                }
            else:
                raise UserError(
                    _("Upload failed: %s - %s") %
                    (response.status_code, response.text)
                )
        except requests.RequestException as e:
            raise UserError(_("Network error: %s") % str(e))
