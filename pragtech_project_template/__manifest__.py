{
    'name': 'Project WBS Templates',
    'version': '15.0.1.0.1',
    'category': 'Construction',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'summary': 'This Module provides Auto Generation of subprojects, WBS and WBS groups using templates.',
    'description': """
Project WBS Templates
=======================================
While the user clicks the project templates, the new window should open
with existing projects and subprojects.
Users are allowed to select the model project and subproject.
Once users select and click generate models then the subprojects, related
WBS, WBS groups with material and labor details will be auto generated
with reference to the new project.
    """,
    'depends': [

        'project', 'pragtech_ppc',
    ],
    'data': [

        'security/ir.model.access.csv',
        'views/project_view.xml',
        'views/project_holiday_view.xml',

        'wizard/wbs_template_wizard.xml',
        'data/week_days_data.xml',
        'data/month_data.xml',

    ],

    'license': 'OPL-1',
    'price': 249,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
