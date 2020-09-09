# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_round, float_is_zero
from odoo.osv import expression

class MrpProduction(models.Model):
	""" Manufacturing Orders """
	_inherit = 'mrp.production'

	divisi_id = fields.Many2one('gbr.divisi', string='Divisi')
	kode = fields.Char(string='Kode', related='product_id.default_code')
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	qty_available = fields.Float(compute='_compute_qty_available',string='Sisa Stock', store=True)

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(MrpProduction, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(MrpProduction, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	@api.depends('location_src_id','product_id')
	def _compute_qty_available(self):
		for moveline in self:
			gbr_qty_avalible = 0.0
			# products = self.env['product.product']
			if moveline.location_src_id:
				product = moveline.product_id.with_context(location=moveline.location_src_id.id)
				gbr_qty_avalible += product.qty_available			
		
			moveline.qty_available = gbr_qty_avalible

	def action_confirm_gbr(self):
		self.action_confirm()
		self.action_assign()
		return self.open_produce_product()		
		# if self.bom_id.type == 'phantom':
			# raise UserError(_('You cannot produce a MO with a bom kit product.'))
		# mrp_produce_obj = self.env['mrp.product.produce']
		# mrp_produce_id = mrp_produce_obj.with_context(active_id=self.id).create({'serial':False})
		# mrp_produce_id.do_produce()
		# self.button_mark_done()
		
		return True


class MrpUnbuild(models.Model):
	_inherit = "mrp.unbuild"

	divisi_id = fields.Many2one('gbr.divisi', string='Divisi')
	kode = fields.Char(string='Kode', related='product_id.default_code')
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	tanggal = fields.Date(string='Tanggal',default=fields.Date.context_today)
	catatan = fields.Char(string='Catatan')
	move_raw_ids = fields.One2many('mrp.unbuild.line', 'mrp_id', 'Components', copy=True)
	qty_available = fields.Float(compute='_compute_qty_available',string='Sisa Stock', store=True)

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 0:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(MrpUnbuild, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(MrpUnbuild, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	@api.depends('location_id','product_id')
	def _compute_qty_available(self):
		for moveline in self:
			gbr_qty_avalible = 0.0
			# products = self.env['product.product']
			if moveline.location_id:
				product = moveline.product_id.with_context(location=moveline.location_id.id)
				gbr_qty_avalible += product.qty_available			
		
			moveline.qty_available = gbr_qty_avalible

	@api.onchange('location_id')
	def _onchange_location_id(self):
		if self.location_id:
			if self.env.context.get('disable_search'):
				self.location_dest_id = self.location_id.id


	def _get_move_raw_values(self, bom_line, line_data):
		quantity = line_data['qty']
		# alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
		# alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
		source_location = self.location_id
		data = {
			# 'name': self.name,
			# 'reference': self.name,
			'date': self.tanggal,
			# 'date_expected': self.date_planned_start,
			'bom_line_id': bom_line.id,
			# 'picking_type_id': self.picking_type_id.id,
			'name': bom_line.product_id.id,
			'product_uom_qty': quantity,
			# 'product_uom': bom_line.product_uom_id.id,
			'location_id': source_location.id,
			# 'location_dest_id': self.product_id.with_context(force_company=self.company_id.id).property_stock_production.id,
			# 'raw_material_production_id': self.id,
			# 'company_id': self.company_id.id,
			# 'operation_id': bom_line.operation_id.id or alt_op,
			'price_unit': bom_line.product_id.standard_price,
			# 'procure_method': 'make_to_stock',
			# 'origin': self.name,
			# 'state': 'draft',
			
		}
		return data


	def _get_moves_raw_values(self):
		moves = []
		for production in self:
			print ('adfadfadfadfadf',production.product_id, production.bom_id)
			factor = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
			boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id)
			for bom_line, line_data in lines:
				if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or\
						bom_line.product_id.type not in ['product', 'consu']:
					continue
				moves.append(production._get_move_raw_values(bom_line, line_data))
		return moves

	@api.onchange('bom_id')
	def _onchange_move_gbr(self):
		if self.bom_id and self.product_qty > 0:
			# keep manual entries
			# print ('adfadfadfadfadf',self.product_id, self.bom_id,self.product_qty)
			list_move_raw = []
		# 	list_move_raw = [(4, move.id) for move in self.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
			moves_raw_values = self._get_moves_raw_values()
		# 	print ('move_raw_values',moves_raw_values,list_move_raw)
		# 	# move_raw_dict = {move.bom_line_id.id: move for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)}

			for move_raw_values in moves_raw_values:
				print ('move_raw_values',move_raw_values)
		# 		# if move_raw_values['bom_line_id'] in move_raw_dict:
		# 			# update existing entries
		# 			# list_move_raw += [(1, move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
		# 		# else:
		# 			# add new entries
				list_move_raw += [(0, 0, move_raw_values)]
			print ('list_move_raw',list_move_raw)
			self.move_raw_ids = list_move_raw
		# else:
		# 	self.move_raw_ids = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]

	

class MrpUnbuildLine(models.Model):
	_name = "mrp.unbuild.line"

	date = fields.Date(string='Tanggal',default=fields.Date.context_today)
	location_id = fields.Many2one('stock.location', string='Gudang')  
	name = fields.Many2one('product.product', string='Nama')
	kode = fields.Char(string='Kode', related='name.default_code')	
	product_uom_qty = fields.Float('Jumlah', default=1.0,required=True)
	catatan = fields.Char(string='Catatan')
	price_unit = fields.Float('HPP', default=0.0,required=False)
	mrp_id = fields.Many2one('mrp.unbuild', string='MRP')
	bom_line_id = fields.Many2one('mrp.bom.line', 'BoM Line', check_company=True)
