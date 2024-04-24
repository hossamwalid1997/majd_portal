from odoo import fields, models, api


class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char(string='Name', required=True)