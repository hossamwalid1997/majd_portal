{
    'name': 'Portal Attendance (GEO)',
    'version': '15.0.0.1',
    'description': 'Portal Attendance (Geo)',
    'category': 'Attendance',
    'author': 'Hossam Walid',
    'depends': [
        "base",
        "hr",
        "hr_attendance",
        "website",
    ],
    'data': [
        'views/hr_attendance_portal.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sb_geo_attendance_portal/static/src/css/portal.css',
            'sb_geo_attendance_portal/static/src/js/portal_attendance.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False
}
