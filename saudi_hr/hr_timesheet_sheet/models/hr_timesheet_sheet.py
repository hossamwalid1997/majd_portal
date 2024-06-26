# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# Copyright 2018 Brainbean Apps
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from dateutil.relativedelta import relativedelta
from dateutil.rrule import (MONTHLY, WEEKLY)
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
            Override method for apply domain on user
        """
        context = dict(self.env.context)
        if context.get('default_project_id') and context.get('company_id'):
            args.extend([('project_id', '=', context['default_project_id']),
                         ('company_id', '=',  context['company_id']),
                         ])
        if context.get('timesheet_ids'):
            timesheet_ids = self.env['account.analytic.line'].browse(context['timesheet_ids'])
            args.extend([('id', 'not in', timesheet_ids.mapped('task_id').ids)])
        return super(ProjectTask, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        context = self._context or {}
        domain = domain or []
        if context.get('default_project_id') and context.get('company_id'):
            domain.extend([('project_id', '=', context['default_project_id']),
                         ('company_id', '=',  context['company_id']),
                         ])
        if context.get('timesheet_ids'):
            timesheet_ids = self.env['account.analytic.line'].browse(context['timesheet_ids'])
            domain.extend([('id', 'not in', timesheet_ids.mapped('task_id').ids)])
        return super(ProjectTask, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)


class Sheet(models.Model):
    _name = 'hr_timesheet.sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _table = 'hr_timesheet_sheet'
    _order = 'id desc'
    _description = 'Timesheet Sheet'

    def _default_date_start(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.sheet_range or WEEKLY
        today = fields.Date.context_today(self)
        if r == WEEKLY:
            if user.company_id.timesheet_week_start:
                delta = relativedelta(
                    weekday=int(user.company_id.timesheet_week_start),
                    days=6)
            else:
                delta = relativedelta(days=today.weekday())
            return today - delta
        elif r == MONTHLY:
            return today + relativedelta(day=1)
        return today

    def _default_date_end(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.sheet_range or WEEKLY
        today = fields.Date.context_today(self)
        if r == WEEKLY:
            if user.company_id.timesheet_week_start:
                delta = relativedelta(weekday=(int(
                    user.company_id.timesheet_week_start) + 6) % 7)
            else:
                delta = relativedelta(days=6-today.weekday())
            return today + delta
        elif r == MONTHLY:
            return today + relativedelta(months=1, day=1, days=-1)
        return today

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(
        string="Note",
        states={'confirm': [('readonly', True)], 'done': [('readonly', True)]},
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        default=lambda self: self._default_employee(),
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        related='employee_id.user_id',
        string='User',
        store=True,
        readonly=True,
    )
    date_start = fields.Date(
        string='Date From',
        default=lambda self: self._default_date_start(),
        required=True,
        index=True,
        states={'draft': [('readonly', False)]},
    )
    date_end = fields.Date(
        string='Date To',
        default=lambda self: self._default_date_end(),
        required=True,
        index=True,
        states={'draft': [('readonly', False)]},
    )
    timesheet_ids = fields.One2many(
        comodel_name='account.analytic.line',
        inverse_name='sheet_id',
        string='Timesheets',
        readonly=True,
        states={
            'draft': [('readonly', False)],
        }
    )
    line_ids = fields.One2many(
        comodel_name='hr_timesheet.sheet.line',
        compute='_compute_line_ids',
        string='Timesheet Sheet Lines',
        states={
            'draft': [('readonly', False)],
        }
    )
    state = fields.Selection([
        ('draft', 'Open'),
        ('confirm', 'Waiting Approval'),
        ('done', 'Approved')],
        default='draft',
        string='Status', required=True, readonly=True, index=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', default=lambda self: self.env.company,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
    )
    add_line_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Select Project',
        help='If selected, the associated project is added '
             'to the timesheet sheet when clicked the button.',
        states={
            'draft': [('readonly', False)],
        },
    )
    add_line_task_id = fields.Many2one(
        comodel_name='project.task',
        string='Select Task',
        help='If selected, the associated task is added '
             'to the timesheet sheet when clicked the button.',
        states={
            'draft': [('readonly', False)],
        },
    )
    total_time = fields.Float(
        compute='_compute_total_time',
        store=True,
    )

    @api.depends('timesheet_ids.unit_amount')
    def _compute_total_time(self):
        for sheet in self:
            sheet.total_time = sum(sheet.mapped('timesheet_ids.unit_amount'))

    @api.constrains('date_start', 'date_end')
    def _check_start_end_dates(self):
        for sheet in self:
            if sheet.date_start > sheet.date_end:
                raise ValidationError(
                    _('The start date cannot be later than the end date.'))

    @api.constrains('date_start', 'date_end', 'employee_id')
    def _check_sheet_date(self, forced_user_id=False):
        for sheet in self:
            new_user_id = forced_user_id or sheet.user_id and sheet.user_id.id
            if new_user_id:
                self.env.cr.execute(
                    """
                    SELECT id
                    FROM hr_timesheet_sheet
                    WHERE (date_start <= %s and %s <= date_end)
                        AND user_id=%s
                        AND company_id=%s
                        AND id <> %s""",
                    (sheet.date_end, sheet.date_start, new_user_id,
                     sheet.company_id.id, sheet.id))
                if any(self.env.cr.fetchall()):
                    raise ValidationError(
                        _('You cannot have 2 sheets that overlap!\n'
                          'Please use the menu \'Timesheet Sheet\' '
                          'to avoid this problem.'))

    @api.constrains('company_id', 'employee_id')
    def _check_company_id_employee_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.employee_id.company_id and \
                    rec.company_id != rec.employee_id.company_id:
                raise ValidationError(
                    _('The Company in the Timesheet Sheet and in '
                      'the Employee must be the same.'))

    @api.constrains('company_id', 'department_id')
    def _check_company_id_department_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.department_id.company_id and \
                    rec.company_id != rec.department_id.company_id:
                raise ValidationError(
                    _('The Company in the Timesheet Sheet and in '
                      'the Department must be the same.'))

    @api.constrains('company_id', 'add_line_project_id')
    def _check_company_id_add_line_project_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.add_line_project_id.company_id and \
                    rec.company_id != rec.add_line_project_id.company_id:
                raise ValidationError(
                    _('The Company in the Timesheet Sheet and in '
                      'the Project must be the same.'))

    @api.constrains('company_id', 'add_line_task_id')
    def _check_company_id_add_line_task_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.add_line_task_id.company_id and \
                    rec.company_id != rec.add_line_task_id.company_id:
                raise ValidationError(
                    _('The Company in the Timesheet Sheet and in '
                      'the Task must be the same.'))

    @api.constrains('company_id')
    def _check_company_id(self):
        for rec in self.sudo():
            if not rec.company_id:
                continue
            for field in rec.timesheet_ids:
                if rec.company_id and field.company_id and \
                        rec.company_id != field.company_id:
                    raise ValidationError(_(
                        'You cannot change the company, as this %s (%s) '
                        'is assigned to %s (%s).'
                    ) % (rec._name, rec.display_name,
                         field._name, field.display_name))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.user_id = self.employee_id.user_id

    def _compute_line_ids(self):
        for sheet in self:
            if not all([sheet.date_start, sheet.date_end]):
                continue
            dates = sheet._get_dates()
            if not dates:
                continue
            timesheets = self.env['account.analytic.line'].search([
                ('project_id', '!=', False),
                ('date', '<=', sheet.date_end),
                ('date', '>=', sheet.date_start),
                ('employee_id', '=', sheet.employee_id.id),
                ('sheet_id', 'in', [sheet.id, False]),
                ('company_id', '=', sheet.company_id.id),
            ])
            lines = self.env['hr_timesheet.sheet.line']
            for date in dates:
                for project in timesheets.mapped('project_id'):
                    timesheet = timesheets.filtered(
                        lambda x: (x.project_id == project))
                    lines |= self._collect_lines_from_timesheets(
                        project,
                        timesheet,
                        date
                    )
            sheet.line_ids = lines

    @api.onchange('date_start', 'date_end', 'timesheet_ids')
    def _onchange_dates_or_timesheets(self):
        self._compute_line_ids()

    def copy(self, default=None):
        if not self.env.context.get('allow_copy_timesheet'):
            raise UserError(_('You cannot duplicate a sheet.'))
        return super().copy(default=default)

    @api.model
    def create(self, vals):
        if 'employee_id' in vals:
            if not self.env['hr.employee'].browse(vals['employee_id']).user_id:
                raise UserError(
                    _('In order to create a sheet for this employee, '
                      'you must link him/her to an user.'))
        res = super().create(vals)
        res.write({'state': 'draft'})
        self.delete_empty_lines(True)
        return res

    def write(self, vals):
        if 'employee_id' in vals:
            new_user_id = self.env['hr.employee'].\
                browse(vals['employee_id']).user_id.id
            if not new_user_id:
                raise UserError(
                    _('In order to create a sheet for this employee, '
                      'you must link him/her to an user.'))
            self._check_sheet_date(forced_user_id=new_user_id)
        res = super().write(vals)
        if self.state == 'draft':
            for rec in self:
                rec.delete_empty_lines(True)
        return res

    def name_get(self):
        # week number according to ISO 8601 Calendar
        return [(r['id'], _('Week ') + str(
            r['date_start'].isocalendar()[1]))
            for r in self.sudo().read(['date_start'], load='_classic_write')]
        # It's a cheesy name because you may have ranges different of weeks.

    def unlink(self):
        sheets = self.read(['state'])
        for sheet in sheets:
            if sheet['state'] in ('confirm', 'done'):
                raise UserError(
                    _('You cannot delete a timesheet sheet '
                      'which is already confirmed.'))
        analytic_timesheet_toremove = self.env['account.analytic.line']
        for sheet in self:
            analytic_timesheet_toremove += \
                sheet.timesheet_ids.filtered(lambda t: not t.task_id)
        analytic_timesheet_toremove.unlink()
        return super().unlink()

    def action_timesheet_draft(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(
                _('Only an HR Officer or Manager can refuse sheets '
                  'or reset them to draft.'))
        self.write({'state': 'draft'})
        return True

    def action_timesheet_confirm(self):
        for sheet in self:
            partner = []
            if sheet.employee_id and sheet.employee_id.parent_id \
                    and sheet.employee_id.parent_id.user_id.partner_id:
                partner.append(sheet.employee_id.parent_id.user_id.partner_id.id)
                self.message_subscribe(partner_ids=partner)
            sheet.reset_add_line()
        self.write({'state': 'confirm'})
        return True

    def action_timesheet_done(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(
                _('Only an HR Officer or Manager can approve sheets.'))
        if self.filtered(lambda sheet: sheet.state != 'confirm'):
            raise UserError(_("Cannot approve a non-submitted sheet."))
        self.write({'state': 'done'})

    def action_timesheet_refuse(self):
        return self.action_timesheet_draft()

    def button_add_line(self):
        for rec in self:
            if rec.state == 'draft':
                rec.add_line()
                rec.reset_add_line()
        return True

    def reset_add_line(self):
        for sheet in self:
            sheet.add_line_task_id = False
            sheet.add_line_project_id = False

    def _get_date_name(self, date):
        return date.strftime("%a\n%b %d")

    def _get_dates(self):
        start = self.date_start
        end = self.date_end
        if end < start:
            return []
        # time_period = end - start
        # number_of_days = time_period/timedelta(days=1)
        dates = [start]
        while start != end:
            start += relativedelta(days=1)
            dates.append(start)
        return dates

    def _get_line_name(self, project, task=None):
        name = '{}'.format(project.name)
        if task:
            name += ' - {}'.format(task.name)
        return name

    def _get_new_line_name(self):
        return self._get_line_name(
            self.add_line_project_id,
            self.add_line_task_id,
        )

    def _collect_lines_from_timesheets(self, project, timesheet, date):
        tasks = [task for task in timesheet.mapped('task_id')]
        if not timesheet or not all(
                [t.task_id for t in timesheet]):
            tasks += [self.env['project.task']]

        name_x = self._get_date_name(date)
        lines = self.env['hr_timesheet.sheet.line']
        for task in tasks:
            name_y = self._get_line_name(project, task)
            values = {
                'value_x': name_x,
                'value_y': name_y,
                'date': date,
                'project_id': project.id,
                'task_id': task.id,
            }
            lines |= self.env['hr_timesheet.sheet.line'].create(
                self._get_default_analytic_line(
                    values=values,
                    timesheet=timesheet.filtered(
                        lambda t: date == t.date
                        and t.task_id.id == task.id),
                )
            )

        return lines

    def _get_default_analytic_line(
            self,
            values,
            timesheet=None):

        timesheet = self.clean_timesheets(timesheet)
        values.update({
            'count_timesheets': len(timesheet),
            'unit_amount': 0.0,
        })
        if self.id:
            values.update({
                'sheet_id': self.id,
            })
        if timesheet:
            amount = sum([t.unit_amount for t in timesheet])
            values.update({
                'unit_amount': amount,
            })
        return values

    @api.model
    def _prepare_empty_analytic_line(self):
        return {
            'name': '/',
            'employee_id': self.employee_id.id,
            'date': self.date_start,
            'project_id': self.add_line_project_id.id,
            'task_id': self.add_line_task_id.id,
            'sheet_id': self.id,
            'unit_amount': 0.0,
            'company_id': self.company_id.id,
        }

    @api.model
    def add_line(self):
        if self.add_line_project_id:
            values = self._prepare_empty_analytic_line()
            name_line = self._get_new_line_name()
            if self.line_ids.mapped('value_y'):
                self.delete_empty_lines(False)
            if name_line not in self.line_ids.mapped('value_y'):
                self.timesheet_ids |= \
                    self.env['account.analytic.line'].create(values)

    def clean_timesheets(self, timesheet):
        if self.id:
            for aal in timesheet.filtered(lambda a: not a.sheet_id):
                aal.write({'sheet_id': self.id})
        repeated = timesheet.filtered(lambda t: t.name == "/")
        if len(repeated) > 1:
            timesheet = repeated.merge_timesheets()
        return timesheet

    def delete_empty_lines(self, allow_empty_rows=False):
        for name in self.line_ids.mapped('value_y'):
            row = self.line_ids.filtered(lambda l: l.value_y == name)
            if row:
                ts_row = self.env['account.analytic.line'].search([
                    ('project_id', '=', row[0].project_id.id),
                    ('task_id', '=', row[0].task_id.id),
                    ('date', '<=', self.date_end),
                    ('date', '>=', self.date_start),
                    ('employee_id', '=', self.employee_id.id),
                    ('sheet_id', '=', self.id),
                    ('company_id', '=', self.company_id.id),
                ])
                if allow_empty_rows and self.add_line_project_id:
                    check = any([l.unit_amount for l in row])
                else:
                    check = not all([l.unit_amount for l in row])
                if check:
                    ts_row.filtered(
                        lambda t: t.name == '/' and not t.unit_amount).unlink()

    # ------------------------------------------------
    # OpenChatter methods and notifications
    # ------------------------------------------------

    def _track_subtype(self, init_values):
        if self:
            record = self[0]
            if 'state' in init_values and record.state == 'confirm':
                return 'hr_timesheet_sheet.mt_timesheet_confirmed'
            elif 'state' in init_values and record.state == 'done':
                return 'hr_timesheet_sheet.mt_timesheet_approved'
        return super()._track_subtype(init_values)

    @api.model
    def _needaction_domain_get(self):
        empids = self.env['hr.employee'].search(
            [('parent_id.user_id', '=', self.env.uid)])
        if not empids:
            return False
        return ['&', ('state', '=', 'confirm'),
                ('employee_id', 'in', empids.ids)]


class SheetLine(models.TransientModel):
    _name = 'hr_timesheet.sheet.line'
    _description = 'Timesheet Sheet Line'

    sheet_id = fields.Many2one(
        comodel_name='hr_timesheet.sheet',
        ondelete='cascade',
    )
    date = fields.Date(
        string='Date',
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )
    value_x = fields.Char(
        string='Date Name',
    )
    value_y = fields.Char(
        string='Project Name',
    )
    unit_amount = fields.Float(
        string="Quantity",
        default=0.0,
    )
    count_timesheets = fields.Integer(
        default=0,
    )

    @api.onchange('unit_amount')
    def onchange_unit_amount(self):
        """This method is called when filling a cell of the matrix.
        It checks if there exists timesheets associated  to that cell.
        If yes, it does several comparisons to see if the unit_amount of
        the timesheets should be updated accordingly."""
        self.ensure_one()
        if self.unit_amount < 0.0:
            self.write({'unit_amount': 0.0})
        if self.unit_amount and not self.count_timesheets:
            self._create_timesheet(self.unit_amount)
        elif self.count_timesheets:
            timesheets = self._find_timesheets()
            if len(timesheets) != self.count_timesheets:
                _logger.info('Found timesheets %s, expected %s',
                             len(timesheets), self.count_timesheets)
                self.count_timesheets = len(timesheets)
            if not self.unit_amount:
                new_ts = timesheets.filtered(lambda t: t.name == '/')
                other_ts = timesheets.filtered(lambda t: t.name != '/')
                if new_ts:
                    new_ts.unlink()
                for timesheet in other_ts:
                    timesheet.write({'unit_amount': 0.0})
                self.count_timesheets = len(other_ts)
            else:
                if self.count_timesheets == 1:
                    timesheets.write({'unit_amount': self.unit_amount})
                elif self.count_timesheets > 1:
                    amount = sum([t.unit_amount for t in timesheets])
                    new_ts = timesheets.filtered(lambda t: t.name == '/')
                    other_ts = timesheets.filtered(lambda t: t.name != '/')
                    diff_amount = self.unit_amount - amount
                    if new_ts:
                        if len(new_ts) > 1:
                            new_ts = new_ts.merge_timesheets()
                            self.count_timesheets = len(
                                self.sheet_id.timesheet_ids)
                        if new_ts.unit_amount + diff_amount >= 0.0:
                            new_ts.unit_amount += diff_amount
                            if not new_ts.unit_amount:
                                new_ts.unlink()
                                self.count_timesheets -= 1
                        else:
                            amount = self.unit_amount - new_ts.unit_amount
                            new_ts.write({'unit_amount': 0.0})
                            new_ts.unlink()
                            self.count_timesheets -= 1
                            self._diff_amount_timesheets(amount, other_ts)
                    else:
                        if diff_amount > 0.0:
                            self._create_timesheet(diff_amount)
                        else:
                            amount = self.unit_amount
                            self._diff_amount_timesheets(amount, other_ts)
                else:
                    raise ValidationError(
                        _('Error code: Cannot have 0 timesheets.'))

    def _create_timesheet(self, amount):
        values = self._line_to_timesheet(amount)
        if self.env['account.analytic.line'].create(values):
            self.count_timesheets += 1

    @api.model
    def _diff_amount_timesheets(self, amount, timesheets):
        for timesheet in timesheets:
            diff_amount = timesheet.unit_amount - amount
            if diff_amount >= 0.0:
                timesheet.unit_amount = diff_amount
                break
            else:
                amount -= timesheet.unit_amount
                timesheet.write({'unit_amount': 0.0})

    @api.model
    def _line_to_timesheet(self, amount):
        task = self.task_id.id if self.task_id else False
        return {
            'name': '/',
            'employee_id': self.sheet_id.employee_id.id,
            'date': self.date,
            'project_id': self.project_id.id,
            'task_id': task,
            'sheet_id': self.sheet_id.id,
            'unit_amount': amount,
            'company_id': self.sheet_id.company_id.id,
        }

    @api.model
    def _find_timesheets(self):
        return self.env['account.analytic.line'].search([
            ('project_id', '=', self.project_id.id),
            ('task_id', '=', self.task_id.id),
            ('date', '=', self.date),
            ('employee_id', '=', self.sheet_id.employee_id.id),
            ('sheet_id', '=', self.sheet_id.id),
            ('company_id', '=', self.sheet_id.company_id.id),
        ])
