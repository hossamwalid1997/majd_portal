# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Middle East Human Resource Leaves Management',
    'category': 'Human Resources',
    'version': '1.0',
    'sequence': 20,
    'description': """
     Holidays Management
    """,
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'http://www.synconics.com',
    'license': 'OPL-1',
    'images': [],
    'depends': [
        'hr_holidays', 'hr_fiscal_year', 'hr_payroll_base', 'saudi_hr_contract'
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'data/hr_holidays_data.xml',
        'data/hr_payroll_data.xml',
        'data/resource_calender_data.xml',
        'views/hr_public_holidays_view.xml',
        # 'views/hr_leave_allocation_views.xml',
        'views/hr_holidays_view.xml',
        'menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
