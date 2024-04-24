from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime, timedelta
import random


class WizardWBSTemplate(models.TransientModel):
    _name = 'wbs.template.wizard'
    _description = 'WBS Template'

    name = fields.Char('Name ')
    project_ids = fields.Many2many('project.project', string="Projects")
    sub_project_ids = fields.Many2many('sub.project', string="Sub Projects")
    project_wbs_ids = fields.Many2many('project.task', string='Project WBS Name', domain=[
        ('is_wbs', '=', True), ('project_id', '!=', False)], )
    start_date = fields.Date(
        'Start Date', default=fields.date.today(), required=True)
    end_date = fields.Date(
        'End Date', default=str(datetime.now() + timedelta(days=+30)), required=True)

    def generate_random_number(self, length):
        return int(''.join([str(random.randint(0, 10)) for _ in range(length)]))

    def generate_wbs_models(self):
        # print('\nn========= self._context ', self._context)
        for sub_proj in self.sub_project_ids:
            copy_sub_project_ids = sub_proj.copy_data()
            data_dict = copy_sub_project_ids[0]
            project_id = int(self._context.get('default_project_id'))
            data_dict['project_id'] = project_id
            number = self.generate_random_number(4)
            data_dict['name'] = data_dict['name'] + ' : ' + self._context.get('project_name') + str(number)
            data_dict['start_date'] = self.start_date
            data_dict['end_date'] = self.end_date
            sub_project_id = self.env['sub.project'].sudo().create(data_dict)
            wbs = self.env['project.task'].search([('project_id', 'in', self.project_ids.ids),
                                                   ('sub_project', 'in', sub_proj.ids), ('is_wbs', '=', 1),
                                                   ('is_task', '=', 0)])

            # print('\n\n\ wbs-------- ', wbs)
            for wb in wbs:
                copy_wb = wb.copy_data()[0]
                number = self.generate_random_number(4)
                copy_wb['name'] = copy_wb['name'] + ' : ' + sub_project_id.name + str(number)
                copy_wb['planed_start_date'] = self.start_date
                copy_wb['planned_finish_date'] = self.end_date
                copy_wb['is_wbs'] = 1
                copy_wb['is_task'] = 0
                copy_wb['sub_project'] = sub_project_id.id
                copy_wb['project_id'] = project_id
                wbs_task_lst = []
                for wbs_task_id in wb.wbs_task_ids:
                    cpy_wbs_task_id = wbs_task_id.copy().copy_data()[0]
                    cpy_wbs_task_id['planed_start_date'] = self.start_date
                    cpy_wbs_task_id['planned_finish_date'] = self.end_date
                    cpy_task_ids = []
                    for tid in wbs_task_id.mapped('task_ids'):
                        c = tid.copy().copy_data()[0]
                        cpy_task_ids.append((0, 0, c))
                    cpy_wbs_task_id.update({
                        'task_ids': cpy_task_ids
                    })
                    if cpy_wbs_task_id:
                        wbs_task_lst.append((0, 0, cpy_wbs_task_id))

                copy_wb.update({
                    'wbs_task_ids': wbs_task_lst,
                })

                # print('==========================vals of generate', copy_wb)
                task = self.env['project.task'].create(copy_wb)

                # here goes material
                # print('==============wbbbb', wb)
                material_line_lst = []
                for material_id in wb.material_estimate_line:
                    cpy_material_id = material_id.copy().copy_data()[0]
                    cpy_material_id['wbs_id'] = task.id
                    cpy_material_id['material_line_id'] = task.id
                    # print('=================material', cpy_material_id)
                    material_line_lst.append((0, 0, cpy_material_id))

                # here goes labour
                labour_line_lst = []
                for labour_id in wb.labour_estimate_line:
                    cpy_labour_id = labour_id.copy().copy_data()[0]
                    cpy_labour_id['wbs_id'] = task.id
                    cpy_labour_id['labour_line_id'] = task.id
                    # print('=================labour', cpy_labour_id)
                    labour_line_lst.append((0, 0, cpy_labour_id))

                task.write({
                    'labour_estimate_line': labour_line_lst,
                    'material_estimate_line': material_line_lst
                })
                print('\n\n\n task created ===..... ', task)
                # stop
