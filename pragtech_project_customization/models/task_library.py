from odoo import api, fields, models


class ProjectTaskLibrary(models.Model):
    _inherit = 'project.task.library'
    _description = 'Project Task Library'

    material_percentage = fields.Float('Material Percentage')
    material_percentage_line = fields.One2many('material.percentage.library', 'library_task_id', string='Material Percentage Lines')

    @api.onchange('material_percentage')
    def onchange_material_percentage(self):
        for record in self:
            for line in record.material_percentage_line:
                line.write({"waste":line.quantity * record.material_percentage,})
                line.write({"loading":(line.quantity + line.waste) * record.material_percentage,})
                line.write({"overhead":(line.quantity + line.waste + line.transfer + line.loading) * record.material_percentage,})
                line.write({"subtotal":(line.quantity + line.waste + line.transfer + line.loading + line.overhead),})

