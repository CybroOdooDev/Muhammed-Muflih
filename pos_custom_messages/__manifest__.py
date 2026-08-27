# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name":  "POS Custom Messages",
    "summary":  """The POS user can add custom message notifications or reminders to be shown on the POS screen at the mentioned time.Break Message|Custom Message|Message|Notification Message""",
    "category":  "Point of Sale",
    "version":  "19.0.1.0.0",
    "sequence":  1,
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/Odoo-POS-Custom-Messages.html",
    "description":  """Odoo POS Custom Messages
Pos message notification
POS message alerts on screen
POS screen message popup
Screen alert pop up
POS message alert""",
    "live_test_url":  "http://odoodemo.webkul.com/?module=pos_custom_messages&custom_url=/pos/web",
    "depends":  ['point_of_sale'],
    "data":  [
        'views/pos_custom_message_view.xml',
        'security/ir.model.access.csv',
    ],
    "demo":  ['data/pos_custom_message_data.xml'],
    "images":  ['static/description/Banner.png'],
    "application":  True,
    "installable":  True,
    "assets":  {
       'point_of_sale._assets_pos': [
            "/pos_custom_messages/static/src/js/pos_custom_messages.js",
            '/pos_custom_messages/static/src/xml/pos_custom_messages.xml',
            '/pos_custom_messages/static/src/css/style.css',
        ],
    },
    "auto_install":  False,
    "price":  49,
    "currency":  "USD",
}
