from datetime import datetime

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _


class MaterialPercentageMaster(models.Model):
    _name = 'material.percentage.library'
    _description = 'Material Percentage Master'

    library_task_id = fields.Many2one('project.task.library', string='Project Library Task')
    item_number = fields.Char('Item Number')
    name = fields.Char('Item Discription')
    material_product_id = fields.Many2one('product.product', string='Material Used')
    material_unit_id = fields.Many2one('uom.uom', string='Unit of Measure')
    quantity = fields.Float('QTY')
    waste = fields.Float('Waste %')
    transfer = fields.Float('Transfer')
    loading = fields.Float('Loading %' )
    overhead = fields.Float('Overhead %')
    subtotal = fields.Float('Subtotal')


    @api.onchange('material_product_id')
    def onchange_material_product_id(self):
        for record in self:
            product_ids = self.env['product.product'].search([("id","=",record.material_product_id.id)])
            record.item_number = product_ids.default_code
            record.name = product_ids.name
            record.material_unit_id = product_ids.uom_id.id

    @api.onchange('quantity')
    def onchange_quantity(self):
        for record in self:
            record.write({"waste":record.quantity * record.library_task_id.material_percentage,})
            record.write({"loading":(record.quantity + record.waste) * record.library_task_id.material_percentage,})
            record.write({"overhead":(record.quantity + record.waste + record.transfer + record.loading) * record.library_task_id.material_percentage,})
            record.write({"subtotal":(record.quantity + record.waste + record.transfer + record.loading + record.overhead),})

    @api.onchange('transfer')
    def onchange_transfer(self):
        for record in self:
            record.write({"waste":record.quantity * record.library_task_id.material_percentage,})
            record.write({"loading":(record.quantity + record.waste) * record.library_task_id.material_percentage,})
            record.write({"overhead":(record.quantity + record.waste + record.transfer + record.loading) * record.library_task_id.material_percentage,})
            record.write({"subtotal":(record.quantity + record.waste + record.transfer + record.loading + record.overhead),})




class MaterialPercentageWbsMaster(models.Model):
    _name = 'material.percentage.wbs'
    _description = 'Material Percentage Wbs Master'

    library_wbs_task_id = fields.Many2one('project.task', string='Project Library Task')
    item_number = fields.Char('Item Number')
    name = fields.Char('Item Discription')
    material_product_id = fields.Many2one('product.product', string='Material Used')
    material_unit_id = fields.Many2one('uom.uom', string='Unit of Measure')
    quantity = fields.Float('QTY')
    waste = fields.Float('Waste %')
    transfer = fields.Float('Transfer')
    loading = fields.Float('Loading %' )
    overhead = fields.Float('Overhead %' )
    subtotal = fields.Float('Subtotal')



    @api.onchange('material_product_id')
    def onchange_material_product_id(self):
        for record in self:
            product_ids = self.env['product.product'].search([("id","=",record.material_product_id.id)])
            record.item_number = product_ids.default_code
            record.name = product_ids.name
            record.material_unit_id = product_ids.uom_id.id

    @api.onchange('quantity')
    def onchange_wbs_quantity(self):
        for record in self:
            record.write({"waste":record.quantity * record.library_wbs_task_id.material_percentage_wbs,})
            record.write({"loading":(record.quantity + record.waste) * record.library_wbs_task_id.material_percentage_wbs,})
            record.write({"overhead":(record.quantity + record.waste + record.transfer + record.loading) * record.library_wbs_task_id.material_percentage_wbs,})
            record.write({"subtotal":(record.quantity + record.waste + record.transfer + record.loading + record.overhead),})

    @api.onchange('transfer')
    def onchange_wbs_transfer(self):
        for record in self:
            record.write({"waste":record.quantity * record.library_wbs_task_id.material_percentage_wbs,})
            record.write({"loading":(record.quantity + record.waste) * record.library_wbs_task_id.material_percentage_wbs,})
            record.write({"overhead":(record.quantity + record.waste + record.transfer + record.loading) * record.library_wbs_task_id.material_percentage_wbs,})
            record.write({"subtotal":(record.quantity + record.waste + record.transfer + record.loading + record.overhead),})
   
