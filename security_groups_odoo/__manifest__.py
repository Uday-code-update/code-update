# -*- coding: utf-8 -*-
{
    'name': "Hide Menu from user",

    'summary': """
        Hide Menu from user""",

    'description': """
        Hide Menu from user
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Security',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'commitment_order'],
    'data': [
        'views/hide_menu_view.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
    ],
}
