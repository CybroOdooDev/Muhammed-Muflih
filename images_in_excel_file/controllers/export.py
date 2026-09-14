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
import io
import logging
from odoo.addons.web.controllers.export import ExportXlsxWriter

_logger = logging.getLogger(__name__)

IMAGE_MAX_PX     = 90
IMAGE_ROW_HEIGHT = 70
IMAGE_COL_WIDTH  = 14


def _is_module_installed():
    try:
        from odoo.http import request
        if request and getattr(request, 'env', None):
            registry = request.env.registry
            if hasattr(registry, '_init_modules') and registry._init_modules:
                return 'images_in_excel_file' in registry._init_modules
            count = request.env['ir.module.module'].sudo().search_count([
                ('name', '=', 'images_in_excel_file'),
                ('state', '=', 'installed')
            ])
            return count > 0
    except Exception:
        pass
    return False


def _is_image_field(field_name: str) -> bool:
    if not field_name:
        return False
    name = str(field_name).lower().split('/')[-1]
    return name == 'image' or name.startswith('image_')


def _to_png_stream(raw: bytes):
    from PIL import Image as PILImage
    with PILImage.open(io.BytesIO(raw)) as im:
        w, h = im.size
        mode = 'RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB'
        im = im.convert(mode)
        out = io.BytesIO()
        im.save(out, format='PNG')
        out.seek(0)
    s = min(IMAGE_MAX_PX / w, IMAGE_MAX_PX / h, 1.0) if (w and h) else 0.3
    return out, s, s


def _decode_image_data(cell_value):
    if not cell_value:
        return None

    # Handle Odoo BinaryValue / BinaryBytes or objects with to_base64()
    if hasattr(cell_value, 'to_base64'):
        try:
            cell_value = cell_value.to_base64()
        except Exception:
            cell_value = str(cell_value)

    if isinstance(cell_value, bytes):
        if cell_value.startswith((b'\x89PNG', b'\xff\xd8', b'GIF8', b'RIFF')):
            return cell_value
        s = cell_value.strip()
        missing_padding = len(s) % 4
        if missing_padding:
            s += b'=' * (4 - missing_padding)
        try:
            return base64.b64decode(s)
        except Exception:
            return None

    if isinstance(cell_value, str):
        s = cell_value.strip()
        if s.startswith('data:') and ',' in s:
            s = s.split(',', 1)[1]
        s = "".join(s.split())
        missing_padding = len(s) % 4
        if missing_padding:
            s += '=' * (4 - missing_padding)
        try:
            return base64.b64decode(s)
        except Exception:
            return None

    return None


def _patch_xlsx_writer():
    _orig_init       = ExportXlsxWriter.__init__
    _orig_write_cell = ExportXlsxWriter.write_cell

    def _new_init(self, field_names, columns_headers, row_count, **kwargs):
        _orig_init(self, field_names, columns_headers, row_count, **kwargs)
        self._img_field_names = []
        for f in field_names:
            if isinstance(f, dict):
                name = f.get('name', '')
            elif isinstance(f, str):
                name = f
            else:
                name = getattr(f, 'name', str(f))
            self._img_field_names.append(name)
        self._img_row_heights_set = set()
        self._img_col_widths_set  = set()

    def _new_write_cell(self, row, col, cell_value):
        if not _is_module_installed():
            return _orig_write_cell(self, row, col, cell_value)

        try:
            field_name = self._img_field_names[col]
        except (AttributeError, IndexError):
            field_name = ''

        if not (field_name and _is_image_field(field_name) and cell_value):
            return _orig_write_cell(self, row, col, cell_value)

        try:
            raw = _decode_image_data(cell_value)
            if raw:
                stream, xs, ys = _to_png_stream(raw)
                self.worksheet.insert_image(
                    row, col, 'img.png',
                    {
                        'image_data'     : stream,
                        'x_scale'        : xs,
                        'y_scale'        : ys,
                        'x_offset'       : 2,
                        'y_offset'       : 2,
                        'object_position': 1,
                    }
                )
                if row not in self._img_row_heights_set:
                    self.worksheet.set_row(row, IMAGE_ROW_HEIGHT)
                    self._img_row_heights_set.add(row)
                if col not in self._img_col_widths_set:
                    self.worksheet.set_column(col, col, IMAGE_COL_WIDTH)
                    self._img_col_widths_set.add(col)
                return
        except Exception as exc:
            _logger.warning("Failed to embed image for field %s at row %s col %s: %s", field_name, row, col, exc)

        _orig_write_cell(self, row, col, cell_value)

    ExportXlsxWriter.__init__   = _new_init
    ExportXlsxWriter.write_cell = _new_write_cell


_patch_xlsx_writer()
