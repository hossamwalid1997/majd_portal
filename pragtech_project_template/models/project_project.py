import datetime

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def action_generate_project_template(self):
        print('\n\n generate_project_template')
        view_id = self.env.ref(
            'pragtech_project_template.wbs_template_wizard_view').id
        return {
            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'res_model': "wbs.template.wizard",
            'multi': "True",
            'target': 'new',
            'views': [[view_id, 'form']],
            'context': {'default_project_id': self.id, 'project_name': self.name}
        }
