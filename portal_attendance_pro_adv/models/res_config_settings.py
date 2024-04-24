from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hr_attendance_geolocation = fields.Boolean(related="company_id.hr_attendance_geolocation", string="Geolocation", readonly=False)
    hr_attendance_geofence = fields.Boolean(related="company_id.hr_attendance_geofence", string="Geofence", readonly=False)
    hr_attendance_photo = fields.Boolean(related="company_id.hr_attendance_photo", string="Photo", readonly=False)
    hr_attendance_ip = fields.Boolean(related="company_id.hr_attendance_ip", string="IP Address", readonly=False)
    hr_attendance_reason = fields.Boolean(related="company_id.hr_attendance_reason", string="Reason", readonly=False)
    google_map_view_api_key = fields.Char(string='Google Maps View Api Key',config_parameter='portal_attendance_pro_adv.gmap_api_key')