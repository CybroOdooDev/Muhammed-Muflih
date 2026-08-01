# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import hashlib
import os
import shutil
import unicodedata
import json
from odoo import _, http, tools
from odoo.exceptions import AccessError
from odoo.http import request

class MediaAssetUploadController(http.Controller):
    """Direct multipart upload for media.asset's file field.

    Bypasses the standard binary widget's call_kw/base64 flow, whose
    request body is size-checked before the web.max_file_upload_size
    system parameter is applied. Modified to support up to 50GB file sizes
    without causing MemoryError in the Odoo server.
    """

    # 53687091200 bytes = 50 GB limit
    @http.route('/media_repository/asset/upload_file', type='http', auth='user', methods=['POST'], max_content_length=53687091200)
    def upload_media_asset_file(self, model, id, ufile, **kwargs):
        """Handle direct multipart HTTP POST file upload for media assets.

        Bypasses standard base64 encoding to stream large files (up to 50 GB)
        directly to the Odoo filestore without memory spikes.

        :param str model: Model name, expected to be 'media.asset'.
        :param int/str id: ID of the target media.asset record.
        :param FileStorage ufile: The uploaded file object sent via multipart form.
        :param dict kwargs: Additional request arguments.
        :return: Response containing JSON with uploaded file name or error details.
        :rtype: odoo.http.Response
        """
        if model != 'media.asset':
            return request.make_response(json.dumps({'error': _("Invalid model.")}), [('Content-Type', 'application/json')])

        asset = request.env['media.asset'].browse(int(id))
        try:
            asset.check_access_rights('write')
            asset.check_access_rule('write')
        except AccessError:
            return request.make_response(json.dumps(
                {'error': _("You are not allowed to upload a file on this record.")}), [('Content-Type', 'application/json')])

        files = request.httprequest.files.getlist('ufile')
        if not files:
            return request.make_response(json.dumps({'error': _("No file uploaded.")}), [('Content-Type', 'application/json')])
        uploaded_file = files[0]

        filename = uploaded_file.filename
        if request.httprequest.user_agent.browser == 'safari':
            filename = unicodedata.normalize('NFD', filename)

        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'media.asset'),
            ('res_field', '=', 'file'),
            ('res_id', '=', asset.id),
        ])
        attachments.unlink()

        # Stream the uploaded file directly to a temporary file on disk 
        # instead of reading everything into memory (ufile.read())
        filestore_path = tools.config.filestore(request.env.cr.dbname)
        temp_path = os.path.join(filestore_path, f'tmp_upload_{asset.id}')
        
        # Save Werkzeug FileStorage spooled file to our temp file
        with open(temp_path, 'wb') as f:
            uploaded_file.save(f)

        # Calculate SHA1 and File Size safely in chunks
        sha1 = hashlib.sha1()
        file_size = 0
        with open(temp_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha1.update(chunk)
                file_size += len(chunk)

        checksum = sha1.hexdigest()

        # Move it to the proper Odoo filestore path format (sha[:2]/sha)
        final_dir = os.path.join(filestore_path, checksum[:2])
        os.makedirs(final_dir, exist_ok=True)
        final_path = os.path.join(final_dir, checksum)
        
        if os.path.exists(final_path):
            os.remove(temp_path)
        else:
            shutil.move(temp_path, final_path)

        # Create an empty attachment record first
        attachment = request.env['ir.attachment'].sudo().create({
            'name': filename,
            'res_model': 'media.asset',
            'res_field': 'file',
            'res_id': asset.id,
            'type': 'binary',
        })
        
        # Manually update the attachment record with the filestore info via SQL,
        # bypassing the ORM's memory checks for raw fields.
        # Cap file_size to PostgreSQL integer max to prevent 'integer out of range' errors
        safe_file_size = min(file_size, 2147483647)
        store_fname = f"{checksum[:2]}/{checksum}"
        request.env.cr.execute("""
            UPDATE ir_attachment
            SET store_fname = %s, checksum = %s, file_size = %s
            WHERE id = %s
        """, (store_fname, checksum, safe_file_size, attachment.id))

        attachment.invalidate_recordset()
        asset.invalidate_recordset(['file'])
        asset.file_name = filename
        asset._compute_file_size()
        asset.flush_recordset(['file_name', 'file_size'])

        return request.make_response(json.dumps({'file_name': filename}), [('Content-Type', 'application/json')])
