from odoo import fields, models, api


class Product(models.Model):
    _inherit = 'product.template'

    product_name = fields.Char(string='Product Name')
    product_description = fields.Text(string='Description')

    category_id = fields.Many2one('product.categories', string='Category')
    brand_id = fields.Many2one('product.brand', string='Brand')



