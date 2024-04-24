# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'HR Job'

    arabic_name = fields.Char('Arabic Name')
