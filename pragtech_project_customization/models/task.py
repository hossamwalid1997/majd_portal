import json
from datetime import datetime, timedelta, date

from odoo import api, fields, models
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.translate import _


class Task(models.Model):
    _inherit = 'project.task'
    _description = 'Task'

    material_percentage_wbs = fields.Float('Material Percentage')
    planned_cost = fields.Float('Planned Cost', compute="total_planned_cost")
    profit_value = fields.Float('Profit Value', compute="total_profit_value_cost")
    profit_value_char = fields.Char('Profit Value')
    total_wbs_value = fields.Float('Total WBS Value', compute="total_wbs_value_cost")
    total_wbs_value_char = fields.Char('Total WBS Value')
    duration = fields.Integer('Duration (Days)', )
    related_details = fields.Many2one('project.task', string='Related Task Details',
                                      domain="[('project_id', '=', project_id),('id', '!=', id),('is_wbs','=',1),('is_task','=',0)]")
    type_of_related = fields.Selection([('finish_to_start', 'Finish to Start'), ('start_to_start', 'Start to Start'),
                                        ('finish_to_finish', 'Finish to Finish')], string='Type of Related',
                                       default='finish_to_start', )
    lags = fields.Float('Lags')
    material_percentage_wbs_line = fields.One2many('material.percentage.wbs', 'library_wbs_task_id',
                                                   string='Material Percentage Lines')
    custom_actual_cost = fields.Float('Custom Actual Cost', compute="total_custom_actual_cost")
    
    quantity = fields.Integer("Quantity", default=1, )
    unit_price = fields.Float("Unit Price",  compute="_compute_total_price")
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True,)
    unit_price_2 = fields.Char("Unit Price 1")
    quantity_2 = fields.Char("Quantity 2", default=1, )
    
    @api.onchange('uom_id')
    def onchange_wbs_value_new1(self):
        #print("1111111111111111111",self.total_wbs_value)
        self.write({"unit_price_2":self.total_wbs_value})
        #print("ccccccccccccccccccccc",self.unit_price_2)
    
    @api.depends('total_wbs_value', 'quantity')
    def _compute_total_price(self):
        for record in self:
            
            if record.quantity == 0:
                record.quantity = 1
            record.unit_price = (record.total_wbs_value) / (float(record.quantity_2))
            record.quantity_2 = record.quantity
            #record.write({"total_wbs_value":record.unit_price,})
            
            
    def action_product_done(self):
        product = self.env['product.product'].search([("name","=",self.name)])
        #if product:
            #raise UserError('Product is already created.')
        products_wbs_ = self.env['product.product'].create(
                        {"name": self.name, "lst_price": (float(self.unit_price_2)) / (float(self.quantity_2)), "wbs_id": self.id,
                         "detailed_type": "consu", })
    
    @api.constrains('related_details')
    def _check_category_recursion(self):
        if not self._check_recursion():
            
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True
    
    def write(self, vals):
        #if vals.get('planed_start_date') or vals.get('planned_finish_date'):
        for rec in self:
            wbs_ids = self.env['project.task'].search([("related_details","=",rec.id)])
            for wbs in wbs_ids:
                wbs.onchange_holiday_duration_parameters()
        return super(Task, self).write(vals)

    @api.onchange('type_of_related', 'related_details', 'duration')
    def onchange_holiday_duration_parameters(self):
        # Auto update the Dates
        for rec in self:
            if rec.type_of_related == 'finish_to_start' and rec.related_details and rec.duration:
                if rec.related_details.planed_start_date and rec.related_details.planned_finish_date:
                    planed_start_date, planned_finish_date = rec.calculate_finish_start_days()
                    #rec.planed_start_date = planed_start_date
                    rec.write({"planed_start_date":planed_start_date,"planned_finish_date":planned_finish_date,})
                    #rec.planned_finish_date = planned_finish_date
                else:
                    raise UserError(
                        "Dates and not set for the Related WBS : " + rec.related_details.name)
            if rec.type_of_related == 'start_to_start' and rec.related_details and rec.duration:
                if rec.related_details.planed_start_date and rec.related_details.planned_finish_date:
                    planed_start_date, planned_finish_date = rec.calculate_start_to_start_days()
                    rec.planed_start_date = planed_start_date
                    rec.planned_finish_date = planned_finish_date
                else:
                    raise UserError(
                        "Dates and not set for the Related WBS : " + rec.related_details.name)
            if rec.type_of_related == 'finish_to_finish' and rec.related_details and rec.duration:
                if rec.related_details.planed_start_date and rec.related_details.planned_finish_date:
                    planed_start_date, planned_finish_date = rec.calculate_finish_to_finish_days()
                    rec.planed_start_date = planed_start_date
                    rec.planned_finish_date = planned_finish_date
                else:
                    raise UserError(
                        "Dates and not set for the Related WBS : " + rec.related_details.name)

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
        #print('self.get_date_range(prev_dt, related_finish_dt)',self.get_date_range(prev_dt, related_finish_dt))
        for dt in self.get_date_range(prev_dt, related_finish_dt):
            holiday_on_dt = self.count_dt_holiday(dt)
            if holiday_on_dt > 0:
                count_holidays = count_holidays + 1
        #print('=============Holidays', prev_dt, related_finish_dt, count_holidays)
        if count_holidays > 0:
            prev_dt = related_finish_dt + timedelta(days=1)
            related_finish_dt = related_finish_dt + timedelta(days=count_holidays)
            # return self.check_holidays(prev_dt, related_finish_dt)
        return related_finish_dt

    def calculate_finish_start_days(self):
        related_start_dt = self.related_details.planned_finish_date + timedelta(days=1)
        confirm_related_start_dt = self.check_confirm_related_planned_dt(related_start_dt)

        # get days for the related task
        base = confirm_related_start_dt
        date_list = [base + timedelta(days=x) for x in range(self.duration)]
        for index in date_list:
            is_holiday = self.count_dt_holiday(index)
            #print('========= before if', index, is_holiday, date_list[-1])
            if is_holiday:
                date_list.append(date_list[-1] + timedelta(days=1))

        related_finish_dt = date_list[-1]
        return confirm_related_start_dt, related_finish_dt

    def calculate_start_to_start_days(self):
        planed_start_date = self.related_details.planed_start_date
        planed_start_date = self.check_confirm_related_planned_dt(planed_start_date)
        planned_finish_date = planed_start_date
        return planed_start_date, planned_finish_date

    def calculate_finish_to_finish_days(self):
        planed_start_date = self.related_details.planned_finish_date
        planed_start_date = self.check_confirm_related_planned_dt(planed_start_date)
        planned_finish_date = planed_start_date
        return planed_start_date, planned_finish_date

    @api.onchange('material_percentage_wbs')
    def onchange_material_percentage_wbs(self):
        for line in self.material_estimate_line:
            rate = (line.material_uom_qty * line.material_rate)
            line.waste = (line.material_uom_qty * line.material_rate) * (self.material_percentage_wbs)    
            line.loading = ((line.material_uom_qty * line.material_rate)+ line.waste) * (self.material_percentage_wbs)
            line.transfer = ((line.material_uom_qty * line.material_rate) + line.waste) * (self.material_percentage_wbs)
            line.overhead = ((line.material_uom_qty * line.material_rate) + line.waste + line.transfer + line.loading) * self.material_percentage_wbs
            line.sub_total = (line.waste + line.transfer + line.loading + line.overhead + rate +  line.profit_id)

    # calculate total planned cost
    def total_planned_cost(self):
        total_labour = 0
        total_material = 0
        for labour in self.labour_estimate_line:
            total_labour += labour.sub_total
        for material in self.material_estimate_line:
            total_material += material.sub_total
        self.planned_cost = total_labour + total_material
    
    # calculate total actual cost
    def total_custom_actual_cost(self):
        total_labour = 0
        total_material = 0
        for labour in self.labour_estimate_line:
            total_labour += labour.sub_total
        for material in self.material_estimate_line:
            total_material += material.sub_total
        self.custom_actual_cost = total_labour + total_material

    # calculate total profit value cost
    def total_profit_value_cost(self):
        for record in self:
            record.profit_value = record.project_id.profit_project * record.planned_cost
            record.profit_value_char = record.project_id.profit_project * record.planned_cost

    # calculate total wbs value cost
    def total_wbs_value_cost(self):
        for record in self:
            record.total_wbs_value = record.planned_cost + record.profit_value 
            record.total_wbs_value_char = record.planned_cost + record.profit_value
            self.unit_price_2 = record.planned_cost + record.profit_value
            #if record.quantity:
                #record.write({"total_wbs_value":record.unit_price,})   

    # calculate days
    def total_day(self):
        for record in self:
            record.duration = (record.planned_finish_date - record.planed_start_date).days
            
            
class TaskMaterialLine(models.Model):
    _inherit = 'task.material.line'
    
    
    @api.onchange('material_uom_qty')
    def onchange_wbs_quantity_new(self):
        for record in self:
            rate = (self.material_uom_qty * self.material_rate)
            self.waste = (self.material_uom_qty * self.material_rate) * (self.wbs_id.material_percentage_wbs)
            self.loading = ((self.material_uom_qty * self.material_rate) + self.waste) * self.wbs_id.material_percentage_wbs
            self.transfer = ((self.material_uom_qty * self.material_rate) + self.waste) * self.wbs_id.material_percentage_wbs
            self.overhead = ((self.material_uom_qty * self.material_rate) + self.waste + self.transfer + self.loading) * self.wbs_id.material_percentage_wbs
            self.sub_total = (self.waste + self.transfer + self.loading + self.overhead + rate +  self.profit_id)
            
            
    @api.onchange('profit_id')
    def onchange_profit_id_new(self):
        for record in self:
            self.sub_total = self.profit_id +  self.sub_total
            
            
class TaskLabourLine(models.Model):
    _inherit = 'task.labour.line'
    
    
    @api.onchange('labour_uom_qty')
    def onchange_wbs_quantity_labour_new(self):
        for record in self:
            rate = (self.labour_uom_qty * self.labour_rate)
            self.sub_total = ( rate +  self.labour_profit_id +  self.labour_overhead)
            
            
    @api.onchange('labour_profit_id')
    def onchange_labour_profit_id_new(self):
        for record in self:
            self.sub_total = self.labour_profit_id   + self.sub_total
            
            
    @api.onchange('labour_overhead')
    def onchange_labour_overhead_new(self):
        for record in self:
            self.sub_total =  self.labour_overhead  + self.sub_total
            
class Sale(models.Model):
    _inherit = 'sale.order.line'
    

    qty_wbs = fields.Float("Wbs Quantity")
    
    
   
        
        
     
