# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression

class GbrGroup10(models.Model):
	_name = "gbr.group.10"
	_description = "Grup Stock Masuk/Keluar"

	name = fields.Char('Name')
	
# class Location(models.Model):
	# _inherit = "stock.location"
	
	# scrap_location = fields.Boolean('Is a Scrap Location?', default=False, help='Check this box to allow using this location to put scrapped/damaged goods.')

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	gbr_move_id = fields.Many2one('account.move', string="Invoice Picking")
	divisi_id = fields.Many2one('gbr.divisi', string='Divisi')
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	catatan = fields.Char('catatan')
	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	is_barang_masuk = fields.Boolean('Barang Masuk', default=False)
	is_barang_keluar = fields.Boolean('Barang Keluar', default=False)
	is_pindah_gudang = fields.Boolean('Pindah Gudang', default=False)
	group_gbr_stock_id = fields.Many2one('gbr.group.10', 'Grouping')
	hpp = fields.Float('Hpp', compute="_amount_all_gbr",store=True)

	
	@api.depends('move_ids_without_package.price_unit')
	def _amount_all_gbr(self):
		for picking in self:		
			gbr_total = 0.0
			for line in picking.move_ids_without_package:
				gbr_total += line.total_price_unit
				
			picking.update({				
				'hpp': gbr_total,
			})			

	@api.onchange('picking_type_id', 'partner_id')
	def onchange_picking_type(self):
		res = super(StockPicking, self).onchange_picking_type()
		if self.picking_type_id and self.is_barang_masuk:
			location_id = self.env['stock.location'].search([('usage','=','inventory'),('scrap_location', '=', False)])			
			self.location_id = location_id[0].id or False 	
			# self.location_dest_id = location_dest_id
		if self.picking_type_id and self.is_barang_keluar:
			location_id = self.env['stock.location'].search([('usage','=','inventory'),('scrap_location', '=', False)])			
			self.location_dest_id = location_id[0].id or False 	
		return res

	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			is_barang_masuk = vals.get('is_barang_masuk')
			is_barang_keluar = vals.get('is_barang_keluar')
			is_pindah_gudang = vals.get('is_pindah_gudang')
			if divisi and is_pindah_gudang:
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				vals['no'] = str(divisi_id.brg_pindah_gudang).zfill(5)
				divisi_id.write({'brg_pindah_gudang': divisi_id.brg_pindah_gudang +1 })
			
			elif divisi and is_barang_masuk:
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				vals['no'] = str(divisi_id.brg_masuk).zfill(5)
				divisi_id.write({'brg_masuk': divisi_id.brg_masuk +1 })

			elif divisi and is_barang_keluar:
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				vals['no'] = str(divisi_id.brg_keluar).zfill(5)
				divisi_id.write({'brg_keluar': divisi_id.brg_keluar +1 })

		result = super(StockPicking, self).create(vals)
		return result

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(StockPicking, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(StockPicking, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	def action_confirm_gbr(self):
		self.action_confirm()
		self.action_assign()
		return self.button_validate()		
		
		return True

class StockMove(models.Model):
	_inherit = 'stock.move'

	total_price_unit = fields.Float('Total Price Unit')
	gbr_location_id = fields.Many2one('stock.location',string='Gudang',related='picking_id.location_id')
	qty_available = fields.Float(compute='_compute_qty_available',string='Sisa Stock', store=True)
	# location_id = fields.Many2one(
 #        'stock.location', "Source Location",
 #        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
 #        check_company=True, readonly=True, required=True,
 #        states={'draft': [('readonly', False)]})


	@api.depends('location_id','product_id')
	def _compute_qty_available(self):
		for moveline in self:
			gbr_qty_avalible = 0.0
			# products = self.env['product.product']
			if moveline.location_id:
				product = moveline.product_id.with_context(location=moveline.location_id.id)
				gbr_qty_avalible += product.qty_available			
		
			moveline.qty_available = gbr_qty_avalible
	
	def _get_computed_price_unit(self):
		self.ensure_one()
		price_unit = 0
		if self.product_id:
			price_unit = self.product_id.standard_price     

		if self.product_uom != self.product_id.uom_id:
			price_unit = self.product_id.uom_id._compute_price(price_unit, self.product_uom)

		company = self.picking_id.company_id
		# if self.picking_id.currency_id != company.currency_id:
		# 	price_unit = company.currency_id._convert(
		# 		price_unit, self.picking_id.currency_id, company, self.picking_id.date)
		return price_unit


	@api.onchange('product_uom')
	def _onchange_uom_id(self):
		''' Recompute the 'price_unit' depending of the unit of measure. '''
		if self._context.get('disable_search'):	
			self.price_unit = self._get_computed_price_unit()
			self.total_price_unit = self._get_computed_price_unit() * self.product_uom_qty

	@api.onchange('product_uom_qty','price_unit')
	def _onchange_uom_qty_id(self):
		''' Recompute the 'price_unit' depending of the unit of measure. '''
		if self._context.get('disable_search'):	
			self.total_price_unit = self.price_unit * self.product_uom_qty
