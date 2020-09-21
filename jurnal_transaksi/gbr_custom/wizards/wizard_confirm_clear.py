import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form


class GbrConfirmClear(models.TransientModel):
	_name = 'gbr.confirm.clear'
	_description = 'Gbr Confirm Clear'

	def button_action_clear(self):
		sales_obj = self.env['account.move']
		# print (self.env.context.get('active_ids'),'ddddddddddddddddddd')
		for clears in sales_obj.browse(self.env.context.get('active_ids')):
			clears.write({'is_penjualan_clear': 'Clear'})
			
		return True