from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class Product(models.Model):
    _inherit = 'product.product'

    wbs_id = fields.Many2one('project.task', 'Project Wbs')
