from odoo import api, fields, models
from odoo.tools import safe_eval

class GoogleMapDrawingShapeMixin(models.AbstractModel):
    _name = 'google.map.drawing.shape.mixin'
    _description = 'Google Maps Shape Mixin'
    _rec_name = 'shape_name'

    shape_name = fields.Char(string='Name')
    shape_area = fields.Float(string='Area')
    shape_radius = fields.Float(string='Radius')
    shape_description = fields.Text(string='Description')
    shape_type = fields.Selection([
        ('polygon', 'Polygon')],
        string='Type', default='polygon', required=True)
    shape_paths = fields.Text(string='Paths')

    def decode_shape_paths(self):
        self.ensure_one()
        return safe_eval(self.shape_paths)