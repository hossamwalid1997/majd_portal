# -*- coding: utf-8 -*-
{
    'name': "Majd Purchase Order & Assets",

    'summary': """
        Majd Purchase Order & Assets""",

    'description': """
        Majd Purchase Order & Assets
    """,

    'author': "Salman Bam",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'purchase', 'hr', 'account', 'pragtech_purchase'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase.xml',
        'views/account.xml',
    ],
}
