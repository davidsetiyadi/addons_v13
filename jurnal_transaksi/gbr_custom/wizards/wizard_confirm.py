import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form


class GbrConfirm(models.TransientModel):
	_name = 'gbr.confirm'
	_description = 'Gbr Confirm'

	confirm_date = fields.Datetime(string='Confirm Date', default=fields.Date.context_today, required=True)
	confirm_id = fields.Many2one('res.users', string='Confirm by', default=lambda self: self.env.user)

	def button_process(self):
		payment_obj = self.env['gbr.payment.voucher']
		for payment in payment_obj.browse(self.env.context.get('active_ids')):
			payment.write({'confirm_date': self.confirm_date,'confirm_id': self.env.user.id})
			
		return True

	def button_process_am(self):
		payment_obj = self.env['account.move']
		for payment in payment_obj.browse(self.env.context.get('active_ids')):
			payment.write({'confirm_date': self.confirm_date,'confirm_id': self.env.user.id})
			
		return True
	def button_process_so(self):
		payment_obj = self.env['sale.order']
		for payment in payment_obj.browse(self.env.context.get('active_ids')):
			payment.write({'confirm_date': self.confirm_date,'confirm_id': self.env.user.id})
			
		return True