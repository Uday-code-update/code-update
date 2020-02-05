# -*- coding: utf-8 -*-
{
    'name': "Commitment Order",

    'summary': """
        Commit Order To Sale Order""",

    'description': """
        Commit Order To Sale Order
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Commitment Order',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale', 'stock', 'fleet', 'portal', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/commit_sequence.xml',

        'views/commitmentorder.xml',
        'views/sale_order_popup.xml',
        'views/inherit.xml',
        'views/productionplanned.xml',
        'views/productionvechile.xml',
        'views/commitmentstockmoveline.xml',
        # 'views/portal_templates.xml',

    ],
}
