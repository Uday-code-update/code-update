# -*- coding: utf-8 -*-
{
    'name': "Reporting",

    'summary': """
        Reporting""",

    'description': """
        Reporting
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Reporting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'report_xlsx', 'commitment_order', ],

    # always loaded
    'data': [
        'views/report.xml',
        'views/wizard_report.xml',
        'views/commit_report.xml',
        'views/product_planned_pdfreport.xml',
    ],
}
