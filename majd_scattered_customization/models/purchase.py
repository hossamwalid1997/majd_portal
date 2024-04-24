# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_wbs = fields.Many2one(required=False)
    project_id = fields.Many2one(required=False)
    sub_project = fields.Many2one(required=False)


