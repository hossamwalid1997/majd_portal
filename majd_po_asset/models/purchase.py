from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    # Set Employee and Analytic Account if already set in PO.
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.employee_id:
            res['employee_id'] = self.employee_id
        if self.analytic_account_id:
            res['analytic_account_id'] = self.analytic_account_id
        return res
