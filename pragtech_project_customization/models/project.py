from datetime import datetime, timedelta, date

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'
    _description = 'Project '

    total_planned_cost = fields.Float(string="Total Planned cost", compute="total_planned_all_wbs_cost")
    profit_project = fields.Float('Profit %')
    profit_project_value = fields.Float('Profit Value', compute="total_total_project_value")
    total_project_value = fields.Float('Total Project Value', compute="total_project_wbs_value")

    lags_project = fields.Float('Lags')
    quotation_status = fields.Selection([('quotation', 'Quotation Done'), ('tobe', 'To be Quotations')],
                                        'Quotations Status', default='tobe', readonly=True)
    manager_status = fields.Selection([('draft', 'Draft'), ('manager', 'Send To Manager'), ('approval', 'Approval')],
                                      'Manager Status', default='draft', readonly=True)
    sale_id = fields.Many2one('sale.order', 'Quotations', readonly=True)

    duration_project = fields.Integer('Duration (Days)', )
    related_details_project = fields.Many2one('project.project', string='Related Sub Project',
                                              domain="[('id', '!=', id)]")
    type_of_related_project = fields.Selection(
        [('finish_to_start', 'Finish to Start'), ('start_to_start', 'Start to Start'),
         ('finish_to_finish', 'Finish to Finish')], string='Type of Related',
        default='finish_to_start', )

    # calculate total planned wbs cost
    def total_planned_all_wbs_cost(self):
        self.total_planned_cost = 0
        total_wbs = 0
        for record in self:
            all_wbs = self.env['project.task'].search([("project_id", "=", record.id)])
            for wbs in all_wbs:
                total_wbs += wbs.planned_cost
                record.total_planned_cost = total_wbs
                break

    # calculate profit project value cost
    def total_total_project_value(self):
        self.profit_project_value = 0
        total_profit = 0
        for record in self:
            all_wbs_profit = self.env['project.task'].search([("project_id", "=", record.id)])
            for wbs_profit in all_wbs_profit:
                profit_value_char = float(wbs_profit.profit_value_char)
                #total_profit += profit_value_char
                record.profit_project_value = wbs_profit.profit_value
                break
                
    # calculate profit project wbs value cost
    def total_project_wbs_value(self):
        self.total_project_value = 0
        total_value = 0
        total_qty = []
        #for record in self:
        all_wbs = self.env['project.task'].search([("project_id", "=", self.id)])

        #print("111111111111111111111",all_wbs)
        for wbs_value in all_wbs:
            if wbs_value.sub_project and wbs_value.wbs_task_ids and wbs_value.labour_estimate_line:
                
                
                total_qty.append(len(wbs_value))

                #print("2222222222222222222222",wbs_value.total_wbs_value / wbs_value.quantity / len(total_qty))
                total_wbs_value_char = float(wbs_value.unit_price_2)
                total_value += total_wbs_value_char
                self.total_project_value = total_value
                #print("ddddddddddddddddddddddddddddd",self.total_project_value)
        #print("ccccccccccccccccccccccccccccccccc",len(total_qty))
                #break
                
    def genrate_product_2(self):
        for record in self:
            all_wbs = self.env['project.task'].search([("project_id", "=", self.id)])
            
            for wbs in all_wbs:
                if wbs.sub_project and wbs.wbs_task_ids and wbs.labour_estimate_line:
                    #print("fffffffffffffffffffffffff",wbs)
                    product_wbs = self.env['product.product'].search([("name", "=", wbs.name)])
                    if not product_wbs:
                        wbs.action_product_done()

    def genrate_product(self):
        for record in self:
            all_subproject = self.env['sub.project'].search([("project_id", "=", record.id)])
            all_wbs = self.env['project.task'].search([("project_id", "=", record.id)])
            
            for wbs_record in all_wbs:
                if wbs_record.sub_project and wbs_record.wbs_task_ids and wbs_record.labour_estimate_line:
                    product_wbs = self.env['product.product'].search([("name", "=", wbs_record.name)])
              
                    for product_wbs_value in product_wbs:
                        #print("44444444444444444444444444444444",wbs_record.total_wbs_value)
                        new_sub_wbs = self.env['sub.project'].search([("name", "=", product_wbs_value.name)])
                        for new_sub_wbs_value in new_sub_wbs:
                            product_wbs_value.write({"lst_price": new_sub_wbs_value.unit_price})
                            
                    if not product_wbs:
                        #print("3333333333333333333333333333333",len(wbs_record))
                        products_wbs_ = self.env['product.product'].create(
                        {"name": wbs_record.name, "lst_price": wbs_record.unit_price, "wbs_id": wbs_record.id,})
                   
            
            '''for subproject in all_subproject:
                product_master = self.env['product.product'].search([("name", "=", subproject.name)])
                for product in product_master:
                    new_subproject = self.env['sub.project'].search([("name", "=", product.name)])
                    for new_sub_product in new_subproject:
                        product.write({"lst_price": new_sub_product.subproject_amount})
                if not product_master:
                    products = self.env['product.product'].create(
                        {"name": subproject.name, "lst_price": subproject.subproject_amount, "wbs_id": subproject.id,
                         "detailed_type": "consu", })'''

    def action_send_to_manager(self):
        self.write({"manager_status": "manager", })

    def action_approval_to_project(self):
        self.write({"manager_status": "approval", })

    def create_quotations(self):
        self.genrate_product_2()
        # if self.quotation_status == 'quotation':
        # raise UserError(_('Quotation is already created.'))
        for record in self:
            tax_id = self.env['account.tax'].search([('name', '=', 'Non GST Supplies')])
            sale_order = self.env['sale.order'].create(
                {"partner_id": record.partner_id.id, "amount_total": record.total_project_value, })
            all_wbs_value = self.env['project.task'].search([("project_id", "=", record.id)])
            
                
            all_subproject = self.env['sub.project'].search([("project_id", "=", record.id)])
            order_lines = []
            order_lines_new = []
            for sub_project_name in all_subproject:
                val = (0, 0, {'display_type': 'line_section','name': sub_project_name.name,"order_id": sale_order.id,})
                order_lines.append(val)
            
                for all_wbs in all_wbs_value:
                    
                    products = self.env['product.product'].search([("wbs_id", "=", all_wbs.id)])
                    if all_wbs.sub_project.id == sub_project_name.id:
                        for product_id in products:
                    
                            #print("5555555555555555555555555",sub_project_name.name)
                            vals = (0, 0, { 
                    "product_id": product_id.id,
                             "order_id": sale_order.id,
                             "tax_id": tax_id,
                             "price_unit": product_id.lst_price,
                             "product_uom_qty":all_wbs.quantity_2,
                             "product_uom":all_wbs.uom_id.id,"order_id": sale_order.id,})
                            order_lines.append(vals)
            sale_order.update({'order_line': order_lines}) 
            sale_order.update({'order_line': order_lines_new}) 
            record.write({'sale_id': sale_order.id, 'quotation_status': 'quotation'})
           
                        

                            
                            
                            
                   
                    
                    
                   
                    

    @api.onchange('type_of_related_project', 'related_details_project', 'duration_project')
    def onchange_holiday_duration_parameters(self):
        # Auto update the Dates
        for rec in self:
            if rec.type_of_related_project == 'finish_to_start' and rec.related_details_project and rec.duration_project:
                if rec.related_details_project.start_date and rec.related_details_project.finish_date:
                    start_date, finish_date = rec.calculate_finish_start_days()
                    rec.start_date = start_date
                    rec.finish_date = finish_date
                else:
                    raise UserError("Dates and not set for the Related Project : " + rec.related_details_project.name)
            if rec.type_of_related_project == 'start_to_start' and rec.related_details_project and rec.duration_project:
                if rec.related_details_project.start_date and rec.related_details_project.finish_date:
                    start_date, finish_date = rec.calculate_start_to_start_days()
                    rec.start_date = start_date
                    rec.finish_date = finish_date
                else:
                    raise UserError("Dates and not set for the Related Project : " + rec.related_details_project.name)
            if rec.type_of_related_project == 'finish_to_finish' and rec.related_details_project and rec.duration_project:
                if rec.related_details_project.start_date and rec.related_details_project.finish_date:
                    start_date, finish_date = rec.calculate_finish_to_finish_days()
                    rec.start_date = start_date
                    rec.finish_date = finish_date
                else:
                    raise UserError("Dates and not set for the Related Project : " + rec.related_details_project.name)

    def get_days_between_dts(self, start, end):
        delta = end - start
        days = []
        months = []
        dates = []
        for i in range(delta.days + 1):
            day = start + timedelta(days=i)
            days.append(day.strftime("%A"))
            months.append(day.month)
            dates.append(day)
        return days, months, dates

    def check_confirm_related_planned_dt(self, date):
        day = date.strftime("%A")
        month = date.month
        week_holiday_ids = self.env['project.holiday.config'].search(
            [('active', '=', True), ('week_day_ids.name', '=', day),
             ('month_ids.month_id', '=', month)])
        date_holiday_ids = self.env['project.holiday.config'].search(
            [('active', '=', True), ('start_date', '=', date), ])
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
            [('active', '=', True), ('start_date', '=', date), ])
        return len(week_holiday_ids.mapped('week_day_ids.name')) + len(date_holiday_ids)

    def check_holidays(self, prev_dt, related_finish_dt):
        count_holidays = 0

        for dt in self.get_date_range(prev_dt, related_finish_dt):
            holiday_on_dt = self.count_dt_holiday(dt)
            if holiday_on_dt > 0:
                count_holidays = count_holidays + 1

        if count_holidays > 0:
            prev_dt = related_finish_dt + timedelta(days=1)
            related_finish_dt = related_finish_dt + timedelta(days=count_holidays)
            # return self.check_holidays(prev_dt, related_finish_dt)
        return related_finish_dt

    def calculate_finish_start_days(self):
        related_start_dt = self.related_details_project.finish_date + timedelta(days=1)
        confirm_related_start_dt = self.check_confirm_related_planned_dt(related_start_dt)

        # get days for the related task
        base = confirm_related_start_dt
        date_list = [base + timedelta(days=x) for x in range(self.duration_project)]
        for index in date_list:
            is_holiday = self.count_dt_holiday(index)

            if is_holiday:
                date_list.append(date_list[-1] + timedelta(days=1))

        related_finish_dt = date_list[-1]
        return confirm_related_start_dt, related_finish_dt

    def calculate_start_to_start_days(self):
        start_date = self.related_details_project.start_date
        start_date = self.check_confirm_related_planned_dt(start_date)
        finish_date = start_date
        return start_date, finish_date

    def calculate_finish_to_finish_days(self):
        start_date = self.related_details_project.finish_date
        start_date = self.check_confirm_related_planned_dt(start_date)
        finish_date = start_date
        return start_date, finish_date
