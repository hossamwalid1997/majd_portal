{
    'name': 'Construction Project customization',
    'version': '15.0.18',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': "www.pragtech.co.in",
    'category': 'Construction',
    'description': """
Construction Project Planning and Controlling
=============================================
Project Planning, budgeting, costing
<keywords>
construction project planning and controlling
project planning and controlling
project planning
project controlling
construction
construction management
construction app
construction module
    """,
    'depends': ['base','product', 'project', 'stock', 'account','sale_management','pragtech_ppc'],  # 'web_list_view_sticky'],
    'data': [
        'security/access_rules.xml',
        'security/ir.model.access.csv',
        'views/project_view.xml',
        'views/task_view.xml',
        'views/product_view.xml',
        'views/sub_project_view.xml',
        'views/task_library_view.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
}
