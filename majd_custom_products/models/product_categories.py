from odoo import fields, models, api


class ProductCategories(models.Model):
    _name = 'product.categories'

    name = fields.Char(string='Name', required=True)
