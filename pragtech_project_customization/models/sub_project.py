from datetime import datetime, timedelta, date

from odoo import models, fields, api
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class SubProject(models.Model):
    _inherit = 'sub.project'
    _description = 'Sub Project'

    duration_subproject = fields.Integer('Duration (Days)', )
    related_details_subproject = fields.Many2one('sub.project', string='Related Sub Project',
                                                 domain="[('project_id', '=', project_id),('id', '!=', id)]")
    type_of_related_subproject = fields.Selection(
        [('finish_to_start', 'Finish to Start'), ('start_to_start', 'Start to Start'),
         ('finish_to_finish', 'Finish to Finish')], string='Type of Related',
        default='finish_to_start', )
    lags_subproject = fields.Float('Lags')
    subproject_amount = fields.Float('Amount', compute="total_sub_project_amount")
    quantity = fields.Integer("Quantity", default=1, )
    unit_price = fields.Float("Unit Price",  compute="_compute_total_price")
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', )

    @api.depends('subproject_amount', 'quantity')
    def _compute_total_price(self):
        for record in self:
            record.unit_price = record.subproject_amount/record.quantity

    # calculate days
    def total_sub_project_day(self):
        for record in self:
            record.duration_subproject = (record.end_date - record.start_date).days

    # calculate amount
    def total_sub_project_amount(self):
        self.subproject_amount = 0
        total_value = 0
        for record in self:
            all_wbs = self.env['project.task'].search([("sub_project", "=", record.id)])
            for wbs_value in all_wbs:
                total_wbs_value_char = float(wbs_value.total_wbs_value_char)
                #total_value += total_wbs_value_char
                record.subproject_amount = wbs_value.total_wbs_value
                break

    def write(self, vals):
        # if vals.get('start_date') or vals.get('end_date'):
        subproject_ids = self.env['sub.project'].search([("related_details_subproject", "=", self.id)])
        for subproject in subproject_ids:
            subproject.onchange_holiday_duration_parameters()
        return super(SubProject, self).write(vals)

    @api.onchange('type_of_related_subproject', 'related_details_subproject', 'duration_subproject')
    def onchange_holiday_duration_parameters(self):
        # Auto update the Dates
        for rec in self:
            if rec.type_of_related_subproject == 'finish_to_start' and rec.related_details_subproject and rec.duration_subproject:
                if rec.related_details_subproject.start_date and rec.related_details_subproject.end_date:
                    start_date, end_date = rec.calculate_finish_start_days()
                    rec.start_date = start_date
                    rec.end_date = end_date
                else:
                    raise UserError(
                        "Dates and not set for the Related SubProject : " + rec.related_details_subproject.name)
            if rec.type_of_related_subproject == 'start_to_start' and rec.related_details_subproject and rec.duration_subproject:
                if rec.related_details_subproject.start_date and rec.related_details_subproject.end_date:

                    start_date, end_date = rec.calculate_start_to_start_days()
                    rec.start_date = start_date
                    rec.end_date = end_date
                else:
                    raise UserError(
                        "Dates and not set for the Related SubProject : " + rec.related_details_subproject.name)
            if rec.type_of_related_subproject == 'finish_to_finish' and rec.related_details_subproject and rec.duration_subproject:
                if rec.related_details_subproject.start_date and rec.related_details_subproject.end_date:
                    start_date, end_date = rec.calculate_finish_to_finish_days()
                    rec.start_date = start_date
                    rec.end_date = end_date
                else:
                    raise UserError(
                        "Dates and not set for the Related SubProject : " + rec.related_details_subproject.name)

    def get_days_between_dts(self, start, end):
        delta = end - start
        days = []
        months = []
        dates = []
        for i in range(delta.days + 1):
            day = start + timedelta(days=i)
            days.append(day.strftime("%A"))
            months.append(day.month)
            dates.append(day.date())
        return days, months, dates

    def check_confirm_related_planned_dt(self, date):
        day = date.strftime("%A")
        month = date.month
        week_holiday_ids = self.env['project.holiday.config'].search(
            [('active', '=', True), ('week_day_ids.name', '=', day),
             ('month_ids.month_id', '=', month)])
        date_holiday_ids = self.env['project.holiday.config'].search(
            [('active', '=', True), ('start_date', '=', date.date()), ])
        if week_holiday_ids or date_holiday_ids:
            return self.check_confirm_related_planned_dt(date + timedelta(days=1))
        else:
            return date

    def get_date_range(self, start, end):
        delta = end - start
        rng = []
        for i in range(delta.days + 1):
            dt = start + timedelta(days=i)
            rng.append(dt)
        return rng

    def count_dt_holiday(self, date):
        day = date.strftime("%A")
        month = date.month
        week_holiday_ids = self.env['project.holiday.config'].search(
            [('active', '=', True), ('week_day_ids.name', '=', day),
             ('month_ids.month_id', '=', month)])
        date_holiday_ids = self.env['project.holiday.config'].search(
            [('active', '=', True), ('start_date', '=', date.date()), ])
        return len(week_holiday_ids.mapped('week_day_ids.name')) + len(date_holiday_ids)

    def check_holidays(self, prev_dt, related_finish_dt):
        count_holidays = 0
        # print('self.get_date_range(prev_dt, related_finish_dt)', self.get_date_range(prev_dt, related_finish_dt))
        for dt in self.get_date_range(prev_dt, related_finish_dt):
            holiday_on_dt = self.count_dt_holiday(dt)
            if holiday_on_dt > 0:
                count_holidays = count_holidays + 1
        # print('=============Holidays', prev_dt, related_finish_dt, count_holidays)
        if count_holidays > 0:
            prev_dt = related_finish_dt + timedelta(days=1)
            related_finish_dt = related_finish_dt + timedelta(days=count_holidays)
            # return self.check_holidays(prev_dt, related_finish_dt)
        return related_finish_dt

    def calculate_finish_start_days(self):
        related_start_dt = self.related_details_subproject.end_date + timedelta(days=1)
        confirm_related_start_dt = self.check_confirm_related_planned_dt(related_start_dt)

        # get days for the related task
        base = confirm_related_start_dt
        date_list = [base + timedelta(days=x) for x in range(self.duration_subproject)]
        for index in date_list:
            is_holiday = self.count_dt_holiday(index)
            # print('========= before if', index, is_holiday, date_list[-1])
            if is_holiday:
                date_list.append(date_list[-1] + timedelta(days=1))

        related_finish_dt = date_list[-1]
        return confirm_related_start_dt, related_finish_dt

    def calculate_start_to_start_days(self):
        start_date = self.related_details_subproject.start_date
        start_date = self.check_confirm_related_planned_dt(start_date)
        end_date = start_date
        return start_date, end_date

    def calculate_finish_to_finish_days(self):
        start_date = self.related_details_subproject.end_date
        start_date = self.check_confirm_related_planned_dt(start_date)
        end_date = start_date
        return start_date, end_date
