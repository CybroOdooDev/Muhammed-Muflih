# -*- coding: utf-8 -*-
{
    'name': 'Copy transfer lines',
    'description': 'Copy transfer lines module transfer move lines of related'
                   'stock.picking to current account.move lines',
    'summary': 'Copy transfer lines module creates the invoice lines in the '
               'account.move correspondence to the related stock.picking models'
               'move_lines',
    'version': '19.0.1.0.0',
    'author': '',
    'company': '',
    'maintainer': '',
    'website': "",
    'depends': ['account', 'stock'],
    'data': [
        'views/view_move_form_inherited.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
