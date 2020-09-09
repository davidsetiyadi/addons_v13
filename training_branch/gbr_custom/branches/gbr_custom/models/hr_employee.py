import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.osv import expression
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import random

import ast
JOB_VOCATION = [('SL', 'Sales'),('SP','Supir'),('HL', 'Helper'),('CL', 'Collector'),('AD','Admin')]

class Employee(models.Model):
	_inherit = "hr.employee"
	_description = "GBR Employe Inherit"

	address = fields.Text('Alamat', require=True)
	komisi = fields.Float('Komisi', require=True)
	note = fields.Text('Catatan', require=True)
	user_active = fields.Date('Non - Aktif', require=True)
	sales_id = fields.Many2one('gbr.jenis.penjualan', string='Jenis Penj')
	divisi_id = fields.Many2one('gbr.divisi', string='Divisi')
	position = fields.Selection(JOB_VOCATION, string='Position', index=True)
	position_string = fields.Char(
		'Tipe', compute='_compute_string_position', readonly=True)
	is_sales = fields.Boolean('Sales')
	is_supir = fields.Boolean('Supir')
	is_helper = fields.Boolean('Helper')
	is_collector = fields.Boolean('Collector')
	is_admin = fields.Boolean('Admin')
	group_1_ids = fields.Many2many('gbr.group.1','employee_group_1_rel','employee_id', 'group_id', string='Grouping *1')
	group_2_ids = fields.Many2many('gbr.group.2','employee_group_2_rel','employee_id', 'group_id', string='Grouping *2')
	group_3_ids = fields.Many2many('gbr.group.3','employee_group_3_rel','employee_id', 'group_id', string='Grouping *3')
	is_semua_data = fields.Boolean(string='Semua Data',default=True)

	@api.model
	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 0:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(Employee, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(Employee, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	def _compute_string_position(self):
		
		for move in self:
			info = ''
			if move.is_sales:
				info += 'SL '
			if move.is_supir:
				info += 'SP '
			if move.is_helper:
				info += 'HL '
			if move.is_collector:
				info += 'CL '
			if move.is_admin:
				info += 'AD '
					# info += _(' (reserved)')
			move.position_string = info