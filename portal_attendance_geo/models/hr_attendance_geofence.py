from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
from odoo.tools import safe_eval

class HrAttendanceGeofence(models.Model):
    _name = "hr.attendance.geofence"
    _description = "Attendance Geofence"
    _order = "id desc"
    
    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s: s.env.company.id, index=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_geofence_rel', 'geofence_id', 'emp_id', string='Employees')
    shape_name = fields.Char(string='Name')
    shape_area = fields.Float(string='Area')
    shape_radius = fields.Float(string='Radius')
    shape_description = fields.Text(string='Description')
    shape_type = fields.Selection([
        ('polygon', 'Polygon')],
        string='Type', default='polygon')
    shape_paths = fields.Text(string='Paths')
