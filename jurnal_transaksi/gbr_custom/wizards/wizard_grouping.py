# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re
from datetime import timedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import datetime

from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class GbrGroup4a_tm(models.TransientModel):
	_name = "gbr.group.4a_tm"
	_description = "Grouping Master Vndr"

	name = fields.Char('Name')
	type = fields.Char('Type')
	group_id = fields.Many2one('gbr.group.4a','Master Group')
	group_1_ids = fields.One2many('gbr.group.4','group_id',related='group_id.group_1_ids', string = "Kelompok 1", readonly=False)
	group_2_ids = fields.One2many('gbr.group.4','group2_id',related='group_id.group_2_ids', string = "Kelompok 2", readonly=False)
	group_3_ids = fields.One2many('gbr.group.4','group3_id',related='group_id.group_3_ids', string = "Grouping 1", readonly=False)
	group_4_ids = fields.One2many('gbr.group.4','group4_id',related='group_id.group_4_ids', string = "Grouping 2", readonly=False)
	group_5_ids = fields.One2many('gbr.group.4','group5_id',related='group_id.group_5_ids', string = "Grouping 3", readonly=False)
	group_7_ids = fields.One2many('gbr.group.7','group_cust_id',related='group_id.group_7_ids', string = "Kelompok *1", readonly=False)
	group_8_ids = fields.One2many('gbr.group.8','group_cust_2_id',related='group_id.group_8_ids', string = "Kelompok *2", readonly=False)

	@api.model
	def default_get(self,fields):
		group_1_ids = group_2_ids = group_3_ids = group_4_ids = []
		group_id = False
		res = super(GbrGroup4a_tm, self).default_get(fields)		
		gbr_group = self.env['gbr.group.4a'].search([])[0]
		if gbr_group:
			group_id = gbr_group.id
		res.update({'group_id': group_id,
					# 'group_1_ids' : group_1_ids,
					# 'group_2_ids' : group_2_ids,
					# 'group_3_ids' : group_3_ids,
					# 'group_4_ids' : group_4_ids,

					})
		return res

	def button_close(self):
		self.ensure_one()
		self.name = "Vendors"		
		context = { 'default_is_value': 1, 'default_supplier_rank':1,'search_default_supplier':1,
					'res_partner_search_mode': 'supplier','default_is_company':1,'default_country_id':100,
					'search_view_ref': 'gbr_custom.view_gbr_res_partner_filter',					
					'tree_view_ref': 'gbr_custom.view_vendor_gbr_inherit_tree' , 
					'form_view_ref': 'gbr_custom.view_vendor_gbr_inherit_form','disable_search':True
					}
		return {
			'name': _('Vendors'),
			'context': context,
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'res.partner',
			'view_id': False,#self.env.ref('gbr_custom.product_product_tree_view').id,
			'type': 'ir.actions.act_window',
			'domain': [('is_value', '=', True)],
			'search_view_id':self.env.ref('gbr_custom.view_gbr_res_partner_filter').id,
			# 'target': 'new',
		}

	def button_close2(self):
		self.ensure_one()
		self.name = "Pelanggan"		
		context = { 'default_is_customer': 1, 'default_customer_rank':1,'search_default_customer':1,
					'res_partner_search_mode': 'customer','default_is_company':1,'default_country_id':100,
					'search_view_ref': 'gbr_custom.view_gbr_res_partner_filter',					
					'tree_view_ref': 'gbr_custom.view_pelanggan_gbr_tree' , 
					'form_view_ref': 'gbr_custom.view_pelanggan_gbr_form','disable_search':True
					}
		return {
			'name': _('Pelanggan'),
			'context': context,
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'res.partner',
			'view_id': False,#self.env.ref('gbr_custom.product_product_tree_view').id,
			'type': 'ir.actions.act_window',
			'domain': [('is_customer', '=', True)],
			'search_view_id':self.env.ref('gbr_custom.view_gbr_res_partner_filter').id,
			# 'target': 'new',
		}

class GbrGroup99_tm(models.TransientModel):
	_name = "gbr.group.99_tm"
	_description = "Grouping Master 2"

	name = fields.Char('Name')
	type = fields.Char('Type')
	group_id = fields.Many2one('gbr.group.99','Master Group')
	group_1_ids = fields.One2many('gbr.group.1','group_id',related='group_id.group_1_ids', string = "Group 1", readonly=False)
	group_2_ids = fields.One2many('gbr.group.2','group_id',related='group_id.group_2_ids', string = "Group 2", readonly=False)
	group_3_ids = fields.One2many('gbr.group.3','group_id',related='group_id.group_3_ids', string = "Group 3", readonly=False)
	group_4_ids = fields.One2many('gbr.group.ii','group_id',related='group_id.group_4_ids', string = "Group 4", readonly=False)


	@api.model
	def default_get(self,fields):
		group_1_ids = group_2_ids = group_3_ids = group_4_ids = []
		group_id = False
		res = super(GbrGroup99_tm, self).default_get(fields)
		if self._context.get('default_type') == 'product':
			gbr_group = self.env['gbr.group.99'].search([('type','=','product')])[0]
			if gbr_group:
				group_id = gbr_group.id
		res.update({'group_id': group_id,
					# 'group_1_ids' : group_1_ids,
					# 'group_2_ids' : group_2_ids,
					# 'group_3_ids' : group_3_ids,
					# 'group_4_ids' : group_4_ids,

					})
		return res

	def button_close(self):
		self.ensure_one()
		self.name = "Item"		
		context = { 'default_type': 'product', 'search_view_ref': 'gbr_custom.gbr_custom_product_search',
					'quantity_available_locations_domain': ('internal',),
					'tree_view_ref': 'gbr_custom.product_product_tree_view' , 
					'form_view_ref': 'gbr_custom.gbr_product_template_form_view','disable_search':True 
					}
		return {
			'name': _('Item'),
			'context': context,
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'product.product',
			'view_id': False,#self.env.ref('gbr_custom.product_product_tree_view').id,
			'type': 'ir.actions.act_window',
			'search_view_id':self.env.ref('gbr_custom.gbr_custom_product_search').id,
			# 'target': 'new',
		}
		
	# otomatis tambah line, 
	# kalau tambah baris otomatis tambah Groups,
	# kalau delete otomatis hapus group juga