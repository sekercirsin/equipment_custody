# -*- coding: utf-8 -*-
{
    'name': 'Ekipman Zimmet Takip',
    'version': '18.0.1.0.0',
    'summary': 'Mühendisler için ekipman zimmet ve tahsis takip modülü',
    'category': 'Human Resources',
    'author': 'MS Spektral Case Study',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/equipment_views.xml',
        'views/custody_request_views.xml',
        'views/wizard_views.xml',
        'views/menu_views.xml',
        'report/custody_report_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

