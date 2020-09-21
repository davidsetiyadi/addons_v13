# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class MrpProductProduce(models.TransientModel):
	_inherit = "mrp.product.produce"
	_description = "Record Production"

	def do_produce(self):
		""" Save the current wizard and go back to the MO. """
		self.ensure_one()
		self._record_production()
		self._check_company()
		if self.env.context.get('disable_search'):
			production = self.env['mrp.production']
			active_id = self.env.context.get('active_id')
			production = self.env['mrp.production'].browse(active_id)
			production.button_mark_done()
			
		return {'type': 'ir.actions.act_window_close'}