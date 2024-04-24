from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    # Overriding the creation of asset to add employee and analytic account
    def _auto_create_asset(self):
        assets = super()._auto_create_asset()
        analytic_account_id = self.analytic_account_id
        employee_id = self.employee_id

        for asset in assets:
            if analytic_account_id:
                asset.account_analytic_id = analytic_account_id
            if employee_id:
                asset.employee_id = employee_id

        return assets


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    employee_id = fields.Many2one('hr.employee', string='Employee')
