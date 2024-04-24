import datetime
from odoo import api, fields, models


class ProjectHolidayConfig(models.Model):
    _name = 'project.holiday.config'
    _rec_name = 'name'
    _description = 'Project Holiday Configuration'

    name = fields.Char('Name')
    start_date = fields.Datetime("Holiday Date", default=fields.Datetime.today)
    week_day_ids = fields.Many2many('project.week.days')
    month_ids = fields.Many2many('project.months')
    active = fields.Boolean('Active', default=False, copy=False)

class WeekDays(models.Model):
    _name = 'project.week.days'
    _rec_name = 'name'
    _description = 'Week Days'

    name = fields.Char('Week name')
    week_id = fields.Integer('Week ID')

class ProjectMonth(models.Model):
    _name = 'project.months'
    _rec_name = 'name'
    _description = 'Months'

    name = fields.Char('Month name')
    month_id = fields.Integer('Month ID')
