# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date
from odoo.tools.float_utils import float_round

from datetime import date, timedelta
from itertools import groupby
from stdnum.iso7064 import mod_97_10
from itertools import zip_longest
from hashlib import sha256
from json import dumps
from odoo.osv import expression

import json
import re
import logging
import psycopg2

_logger = logging.getLogger(__name__)

#forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')
SALE = [('cash','Penjualan Cash'),('credit','Penjualan Credit')]
PURCHASE = [('cash','Pembelian Cash'),('credit','Pembelian Credit')]
CODE_SELECTION = [('KK','KK'),('KM','KM'),('new','New'),('credit','CR'),('cash','CH'),('debit_note','DN'),('credit_note','CN'),('retur_credit','RTC'),('mm','MM'),('deposit','DP')]
TYPE_KAS_MSK = [('RTRP','Retur Pembelian'),('PH','Pembayaran Hutang'),('PNJ','Penjualan'),('DPPNJ','Deposit Penjualan'),('PNPTG','Penerimaan Piutang'),('KMU','Kas Masuk Umum')]
TYPE_KAS_KLR = [('PB','Pembelian'),('DPPB','Deposit Pembelian'),('PH','Pembayaran Hutang'),('PNJ','Penjualan'),('RTRPNJ','Retur Penjualan'),('PNPTG','Penerimaan Piutang'),('KKU','Kas Keluar Umum')]
CEK_BG = [('---','---'),('yes','Modul pencairan CH/BG [Default: Yes/Ya]'),('no','Modul pencairan CH/BG [Default: No/Tidak]')]

class AccountAccount(models.Model):
	_inherit = "account.account"
	_description = "Account"
	
	gol_check_bg = fields.Selection(CEK_BG, string="Gol Check BG")

class AccountMove(models.Model):
	_inherit = "account.move"
	_description = "Journal Entries"

	type_penjualan = fields.Selection(SALE, string="Type Penjualan")
	type_pembelian = fields.Selection(PURCHASE, string="Type Pembelian")
	type_kas_keluar = fields.Selection(TYPE_KAS_KLR, string='Type Kas Keluar')
	type_kas_masuk = fields.Selection(TYPE_KAS_MSK, string='Type Kas masuk')
	type_code = fields.Selection(CODE_SELECTION,string='Mlk') #Penerimaan putang kas masuk #pembayaran hutang kas keluar
	purchase_2_id = fields.Many2one('purchase.order', string='PO', required=False, readonly=True,
		states={'draft': [('readonly', False)]})
	purchase_char_id = fields.Many2one('gbr.po.number', string='NO PO', required=False, readonly=True,
		states={'draft': [('readonly', False)]})
	sale_2_id = fields.Many2one('sale.order', string='SO', required=False, readonly=True,
		states={'draft': [('readonly', False)]})
	pembelian_2_id = fields.Many2one('account.move', string='Pembelian', required=False, readonly=True,
		states={'draft': [('readonly', False)]})
	warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True,default=1,
		states={'draft': [('readonly', False)]})
	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",default=lambda self: self.env.user.employee_id.divisi_id)
	is_update_cost_price = fields.Boolean(string='Update Cost Price', default=True,
		help='Update Cost price')
	pelanggan = fields.Char(string='Pelanggan', required=False, readonly=True,
		states={'draft': [('readonly', False)]})
	is_shipped = fields.Boolean(compute="_compute_is_shipped",string="Shipped")
	picking_count = fields.Integer(compute='_compute_picking', string='Picking count', default=0, store=True)
	picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Receptions', copy=False, store=True)
	is_refund = fields.Boolean('Refund Invoice', default=False)
	is_pembelian = fields.Boolean('is Pembelian', default=False)
	is_retur_penj = fields.Boolean('Retur Penjualan', default=False)
	is_penjualan = fields.Boolean('is Penjualan', default=False)
	is_penjualan_cash = fields.Boolean('is Penjualan Cash', default=False)
	is_penj_eceran = fields.Boolean('is Penjualan Eceran', default=False)
	employee_id = fields.Many2one('hr.employee', string='Employee')
	group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
	gbr_picking_ids = fields.One2many('stock.picking', 'gbr_move_id', string='Picking Lines', states={'cancel': [('readonly', True)], 'posted': [('readonly', True)]}, copy=False)
	is_debit_note_pembelian = fields.Boolean(string='Debit Note Pembelian', default=False)
	is_credit_note_pembelian = fields.Boolean(string='Credit Note Pembelian', default=False)
	is_debit_note_penjualan = fields.Boolean(string='Debit Note Penjualan', default=False)
	is_credit_note_penjualan = fields.Boolean(string='Credit Note Penjualan', default=False)
	group_cust_id = fields.Many2one('gbr.group.7',related='partner_id.group_cust_id', string='Kelompok Pelanggan')
	gbr_daerah = fields.Char(compute='_compute_daerah',copy=False,string="Daerah", store=True)
	total_weight = fields.Float(string='Total Berat', compute="_amount_all_kubikasi")
	total_volume = fields.Float(string='Total Volume', compute="_amount_all_kubikasi")
	is_semua_data = fields.Boolean(string='Semua Data',default=True)



	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 2:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(AccountMove, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(AccountMove, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
	
	def _amount_all_kubikasi(self):
		for order in self:
			total_volume = total_weight = amount_untaxed = amount_tax = amount_disc = product_qty = discount = 0.0
			product_uom = ''
			for line in order.invoice_line_ids:				
				total_weight += line.weight
				total_volume += line.volume				
				
			order.update({				
				'total_weight': total_weight,
				'total_volume': total_volume,				
			})

	@api.depends('partner_id')
	def _compute_daerah(self):
		for move in self:
			gbr_daerah = ''
			if move.partner_id:
				if move.partner_id.state_id:
					gbr_daerah += ' '+str(move.partner_id.state_id.name)
				if move.partner_id.kota_id:
					gbr_daerah += ', '+str(move.partner_id.kota_id.name)
				if move.partner_id.kecamatan_id:
					gbr_daerah += ', '+str(move.partner_id.kecamatan_id.name)
				if move.partner_id.kelurahan_id:
					gbr_daerah += ', '+str(move.partner_id.kelurahan_id.name)
			move.gbr_daerah = gbr_daerah
	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:
				penj_ecrn = self.env.context.get('default_is_penj_eceran', False)
				penjualan = self.env.context.get('default_is_penjualan', False)
				type_code = self.env.context.get('default_type_code', False)
				ret_penj = self.env.context.get('default_is_retur_penj', False)
				credit_penj = self.env.context.get('default_is_credit_note_penjualan', False)
				debit_penj = self.env.context.get('default_is_debit_note_penjualan', False)
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				if penj_ecrn:
					vals['no'] = str(divisi_id.penj_ecrn).zfill(5)
					divisi_id.write({'penj_ecrn': divisi_id.penj_ecrn + 1 })
				
				#after post penjualan get number
				# elif penjualan:
				# 	type_penjualan = vals.get('type_penjualan')
				# 	if type_penjualan == 'cash':
				# 		vals['no'] = divisi_id.penjualan_cash
				# 		divisi_id.write({'penjualan_cash': vals['no']+1 })
				# 	else:
				# 		vals['no'] = divisi_id.penjualan
				# 		divisi_id.write({'penjualan': vals['no']+1 })

				elif ret_penj:
					vals['no'] = str(divisi_id.ret_penjualan).zfill(5)
					divisi_id.write({'ret_penjualan': divisi_id.ret_penjualan + 1 })
				elif credit_penj:
					vals['no'] = str(divisi_id.cred_note_penj).zfill(5)
					divisi_id.write({'cred_note_penj': divisi_id.cred_note_penj+1 })
				elif debit_penj:
					vals['no'] = str(divisi_id.deb_note_penj).zfill(5)
					divisi_id.write({'deb_note_penj': divisi_id.deb_note_penj+1 })
				elif type_code == 'KK':
					vals['no'] = str(divisi_id.kas_keluar).zfill(5)
					divisi_id.write({'kas_keluar': divisi_id.kas_keluar+1 })
				elif type_code == 'KM':
					vals['no'] = str(divisi_id.kas_masuk).zfill(5)
					divisi_id.write({'kas_masuk': divisi_id.kas_masuk+1 })
			
		result = super(AccountMove, self).create(vals)
		return result
	
	@api.depends('purchase_2_id','purchase_2_id.order_line.move_ids.returned_move_ids',
				 'purchase_2_id.order_line.move_ids.state',
				 'purchase_2_id.order_line.move_ids.picking_id','gbr_picking_ids')
	def _compute_picking(self):
		for move in self:
			pickings = []
			pickings = self.env['stock.picking']
			# if move.purchase_2_id:
			if move.is_pembelian:
				
				######close due using direct receipt#########
				# for line in move.purchase_2_id.order_line:
				# 	# We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
				# 	# do some recursive search, but that could be prohibitive if not done correctly.
				# 	moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
				# 	pickings |= moves.mapped('picking_id')	
				#==========================================
				picking_ids = pickings.search([('gbr_move_id','=',self.id)]) 
				pickings = picking_ids				
			if move.is_refund:
				pickings = self.env['stock.picking']				
				# find gbr_move_id = self.id
				picking_ids = pickings.search([('gbr_move_id','=',self.id)]) 
				pickings = picking_ids
			if move.is_retur_penj:								
				picking_ids = pickings.search([('gbr_move_id','=',self.id)]) 
				pickings = picking_ids
			if move.is_penjualan:								
				picking_ids = pickings.search([('gbr_move_id','=',self.id)]) 
				pickings = picking_ids
			if move.is_penj_eceran:								
				picking_ids = pickings.search([('gbr_move_id','=',self.id)]) 
				pickings = picking_ids
			move.picking_ids = pickings
			move.picking_count = len(pickings)

	@api.depends('purchase_2_id','purchase_2_id.picking_ids', 'purchase_2_id.picking_ids.state')
	def _compute_is_shipped(self):
		for move in self:
			move.is_shipped = False
			if move.purchase_2_id:
				if move.purchase_2_id.picking_ids and all([x.state in ['done', 'cancel'] for x in move.purchase_2_id.picking_ids]):
					move.is_shipped = True
				else:
					move.is_shipped = False

	
	def _get_destination_location(self):        
		location_ids = self.env['stock.location'].search([('usage','=','supplier')])
		return location_ids[:1]

	def _get_destination_location_incoming(self):        		
		location_id = False
		
		picking_type_ids = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', self.warehouse_id.id)])
		for picking_type in picking_type_ids:
			if picking_type.default_location_dest_id:
				location_id = picking_type.default_location_dest_id.id
		return location_id
	
	def _get_picking_type_return(self):        

		picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', self.warehouse_id.id)])
		return picking_type[:1]

	def _get_picking_type_return_penj(self):        
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', self.warehouse_id.id)])
		return picking_type[:1]

	def _get_picking_type_incoming(self):        
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', self.warehouse_id.id)])
		return picking_type[:1]

	def _get_picking_type_outgoing(self):        
		picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', self.warehouse_id.id)])
		return picking_type[:1]

	def _get_source_location_incoming(self):    
		location_ids = self.env['stock.location'].search([('usage','=','supplier')])
		return location_ids[:1]

	def _get_customer_location(self):    
		location_ids = self.env['stock.location'].search([('usage','=','customer')])
		return location_ids[:1]

		
	def _get_source_location(self):    
		location_id = False
		picking_type_ids = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', self.warehouse_id.id)])
		for picking_type in picking_type_ids:
			if picking_type.default_location_src_id:
				location_id = picking_type.default_location_src_id.id
		return location_id

	def _force_picking_done(self, picking):
		"""Force picking in order to be set as done."""
		pick_to_do = self.env['stock.picking']
		pick_to_backorder = self.env['stock.picking']
		for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
			for move_line in move.move_line_ids:
				move_line.qty_done = move_line.product_uom_qty
			if picking._check_backorder():
				pick_to_backorder |= picking
				continue
			pick_to_do |= picking
		# Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
		if pick_to_do:
			pick_to_do.action_done()			
		
		return True

	@api.model
	def _prepare_picking_incoming(self):
		if not self.group_id:
			self.group_id = self.group_id.create({
				'name': self.name,
				'partner_id': self.partner_id.id
			})

		if not self.partner_id.property_stock_supplier.id:
			raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
		return {
			'picking_type_id': self._get_picking_type_incoming().id,
			'partner_id': self.partner_id.id,
			'user_id': False,
			'date': self.invoice_date,
			'origin': self.name,
			'gbr_move_id': self.id,
			'location_dest_id': self._get_destination_location_incoming(),
			'location_id': self._get_source_location_incoming().id,
			'company_id': self.company_id.id,
		}

	@api.model
	def _prepare_picking_return(self):
		if not self.group_id:
			self.group_id = self.group_id.create({
				'name': self.name,
				'partner_id': self.partner_id.id
			})

		if not self.partner_id.property_stock_supplier.id:
			raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
		return {
			'picking_type_id': self._get_picking_type_return().id,
			'partner_id': self.partner_id.id,
			'user_id': False,
			'date': self.invoice_date,
			'origin': self.name,
			'gbr_move_id': self.id,
			'location_dest_id': self._get_destination_location().id,#retur from pembelian
			'location_id': self._get_source_location(), #from location to supplier
			'company_id': self.company_id.id,
		}

	@api.model
	def _prepare_picking_outgoing(self):
		if not self.group_id:
			self.group_id = self.group_id.create({
				'name': self.name,
				'partner_id': self.partner_id.id
			})

		if not self.partner_id.property_stock_supplier.id:
			raise UserError(_("You must set a Customer Location for this partner %s") % self.partner_id.name)
		return {
			'picking_type_id': self._get_picking_type_outgoing().id,
			'partner_id': self.partner_id.id,
			'user_id': False,
			'date': self.invoice_date,
			'origin': self.name,
			'gbr_move_id': self.id,
			'location_dest_id': self._get_customer_location().id,
			'location_id': self._get_source_location(),
			'company_id': self.company_id.id,
		}

	@api.model
	def _prepare_picking_return_penj(self):
		if not self.group_id:
			self.group_id = self.group_id.create({
				'name': self.name,
				'partner_id': self.partner_id.id
			})

		if not self.partner_id.property_stock_supplier.id:
			raise UserError(_("You must set a Customer Location for this partner %s") % self.partner_id.name)
		return {
			'picking_type_id': self._get_picking_type_return_penj().id,
			'partner_id': self.partner_id.id,
			'user_id': False,
			'date': self.invoice_date,
			'origin': self.name,
			'gbr_move_id': self.id,
			'location_dest_id': self._get_destination_location_incoming(), #retur from penjualan
			'location_id': self._get_customer_location().id,
			'company_id': self.company_id.id,
		}

	def _create_picking_return(self):
		StockPicking = self.env['stock.picking']
		for order in self:
			if any([ptype in ['product', 'consu'] for ptype in order.invoice_line_ids.mapped('product_id.type')]):
				pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
				if not pickings:
					res = order._prepare_picking_return()
					picking = StockPicking.create(res)
				else:
					picking = pickings[0]
				moves = order.invoice_line_ids._create_stock_moves(picking)
				moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
				seq = 0
				for move in sorted(moves, key=lambda move: move.date_expected):
					seq += 5
					move.sequence = seq
				moves._action_assign()
				# moves._action_done()
				self._force_picking_done(picking)
				picking.message_post_with_view('mail.message_origin_link',
					values={'self': picking, 'origin': order},
					subtype_id=self.env.ref('mail.mt_note').id)
		return True

	def _create_picking_return_penj(self):
		StockPicking = self.env['stock.picking']
		for order in self:
			if any([ptype in ['product', 'consu'] for ptype in order.invoice_line_ids.mapped('product_id.type')]):
				pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
				if not pickings:
					res = order._prepare_picking_return_penj()
					picking = StockPicking.create(res)
				else:
					picking = pickings[0]
				moves = order.invoice_line_ids._create_stock_moves_incoming(picking)
				moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
				seq = 0
				for move in sorted(moves, key=lambda move: move.date_expected):
					seq += 5
					move.sequence = seq
				moves._action_assign()
				# moves._action_done()
				self._force_picking_done(picking)
				picking.message_post_with_view('mail.message_origin_link',
					values={'self': picking, 'origin': order},
					subtype_id=self.env.ref('mail.mt_note').id)
		return True

	def _create_picking_outgoing(self):
		StockPicking = self.env['stock.picking']
		for order in self:
			if any([ptype in ['product', 'consu'] for ptype in order.invoice_line_ids.mapped('product_id.type')]):
				pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
				if not pickings:
					res = order._prepare_picking_outgoing()
					picking = StockPicking.create(res)
				else:
					picking = pickings[0]
				moves = order.invoice_line_ids._create_stock_moves_incoming(picking)
				moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
				seq = 0
				for move in sorted(moves, key=lambda move: move.date_expected):
					seq += 5
					move.sequence = seq
				moves._action_assign()
				# moves._action_done()
				self._force_picking_done(picking)
				picking.message_post_with_view('mail.message_origin_link',
					values={'self': picking, 'origin': order},
					subtype_id=self.env.ref('mail.mt_note').id)
		return True

	def _create_picking_incoming(self):
		StockPicking = self.env['stock.picking']
		for order in self:
			if any([ptype in ['product', 'consu'] for ptype in order.invoice_line_ids.mapped('product_id.type')]):
				pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
				if not pickings:
					res = order._prepare_picking_incoming()
					picking = StockPicking.create(res)
				else:
					picking = pickings[0]
				moves = order.invoice_line_ids._create_stock_moves_incoming(picking)
				moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
				seq = 0
				for move in sorted(moves, key=lambda move: move.date_expected):
					seq += 5
					move.sequence = seq
				moves._action_assign()
				# moves._action_done()
				self._force_picking_done(picking)
				picking.message_post_with_view('mail.message_origin_link',
					values={'self': picking, 'origin': order},
					subtype_id=self.env.ref('mail.mt_note').id)
		return True

	def action_post_penj_eceran(self):
		self.action_post()
		self.env.cr.commit()
		return self.action_invoice_register_payment()

	def action_post(self):
		if self.is_update_cost_price:
			inv_line_obj = self.env['account.move.line']	
			price_unit = 0		
			inv_line_ids = inv_line_obj.search([('product_id','!=',False),('move_id','=',self.id)])			
			if self.type == 'in_invoice':
				if self.is_pembelian:
					for line in inv_line_ids:
						#=================================
						#harga invoice di jadikan harga default					
						# subtotal / uom factor  / qty = harga satuan
						# 100 / 0.5 (pack 2) / 10 = 20 
						# 20 * uom factor  = buying_price
						#===============
						if line.quantity:
							price_unit = (line.price_total / line.product_uom_id.factor/ line.quantity) * line.product_id.uom_id.factor
							if line.product_id:
								line.product_id.write({'buying_price':price_unit })

		if self.is_pembelian:
			inv_line_obj = self.env['account.move.line']	
			inv_line_ids = inv_line_obj.search([('product_id','!=',False),('move_id','=',self.id)])	
			for line in inv_line_ids:
				if line.product_id:
					line.product_id.write({'vendor_id': self.partner_id.id })

		if self.is_refund:
			self._create_picking_return()

		if self.is_pembelian:			 
			self._create_picking_incoming()

		if self.is_retur_penj:
			self._create_picking_return_penj()

		if self.is_penjualan:
			
			if self.no == 'New' and self.divisi_id:				
				if self.type_penjualan == 'cash':
					self.write({'no': str(self.divisi_id.penjualan_cash).zfill(5),'type_code':'cash'})
					self.divisi_id.write({'penjualan_cash': self.divisi_id.penjualan_cash+1 })
				else:					
					self.write({'no': str(self.divisi_id.penjualan).zfill(5),'type_code':'credit'})
					self.divisi_id.write({'penjualan': self.divisi_id.penjualan+1 })

			self._create_picking_outgoing()

		if self.is_penj_eceran:
			self._create_picking_outgoing()


		moves = super(AccountMove, self).action_post()
		return moves

	def button_action_cash(self):
		if self.state == 'draft':
			self.write({'type_penjualan':'credit'})
			self.write({'type_pembelian':'credit'})
		# return True

	def button_action_credit(self):
		if self.state == 'draft':
			self.write({'type_penjualan':'cash'})
			self.write({'type_pembelian':'cash'})
		# return True

	@api.model
	def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
		quantity = stock_move.product_qty - sum(
			stock_move.move_dest_ids
			.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
			.mapped('move_line_ids.product_qty')
		)
		quantity = float_round(quantity, precision_rounding=stock_move.product_uom.rounding)
		return {
			'product_id': stock_move.product_id.id,
			'quantity': quantity,
			'move_id': stock_move.id,
			'uom_id': stock_move.product_id.uom_id.id,
		}
	def _prepare_stock_retur(self, picking):
		location_id = picking.location_id.id
		move_dest_exists = False
		product_return_moves = [(5,)]
		if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
			location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id

		for move in picking.move_lines:
			if move.scrapped:
				continue
			if move.move_dest_ids:
				move_dest_exists = True
			product_return_moves.append((0, 0, self._prepare_stock_return_picking_line_vals_from_move(move)))	
			
		move_dest_exists = move_dest_exists
		parent_location_id = picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id
		original_location_id = picking.location_id.id		

		return_values  = {
						'picking_id': picking.id,
						'location_id': location_id,
						'move_dest_exists': move_dest_exists,
						'product_return_moves': product_return_moves,
						'parent_location_id': parent_location_id,
						'original_location_id': original_location_id,
					}
		return return_values
		
	def button_draft(self):
		#retur stock and removes picking.
		# all done , related to gbr_move_id, refund
		stock_return_obj = self.env['stock.return.picking']
		picking_obj = self.env['stock.picking']
		if self.is_refund:
			return_values = []
			for picking in self.gbr_picking_ids:
				if picking.state == 'done':					
					stock_retur_id = stock_return_obj.create(self._prepare_stock_retur(picking))
					new_picking_id, pick_type_id = stock_retur_id._create_returns()
					new_pickings = picking_obj.search([('id','=',new_picking_id)])
					self._force_picking_done(new_pickings)
					new_pickings.write({'gbr_move_id': None})
				picking.write({'gbr_move_id': None})

		if self.is_pembelian or self.is_retur_penj:
			return_values = []
			for picking in self.gbr_picking_ids:
				if picking.state == 'done':					
					stock_retur_id = stock_return_obj.create(self._prepare_stock_retur(picking))
					new_picking_id, pick_type_id = stock_retur_id._create_returns()
					new_pickings = picking_obj.search([('id','=',new_picking_id)])
					self._force_picking_done(new_pickings)
					new_pickings.write({'gbr_move_id': None})
				picking.write({'gbr_move_id': None})
		if self.is_penj_eceran or self.is_penjualan:
			#return stock in
			return_values = []
			for picking in self.gbr_picking_ids:
				if picking.state == 'done':					
					stock_retur_id = stock_return_obj.create(self._prepare_stock_retur(picking))
					new_picking_id, pick_type_id = stock_retur_id._create_returns()
					new_pickings = picking_obj.search([('id','=',new_picking_id)])
					self._force_picking_done(new_pickings)
					new_pickings.write({'gbr_move_id': None})
				picking.write({'gbr_move_id': None})

		moves = super(AccountMove, self).button_draft()		
		return moves

	def action_view_picking(self):
		""" This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
		"""
		action = self.env.ref('stock.action_picking_tree_all')
		result = action.read()[0]
		# override the context to get rid of the default filtering on operation type
		result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.purchase_2_id.name, 'default_picking_type_id': self.purchase_2_id.picking_type_id.id}
		pick_ids = self.mapped('picking_ids')
		# choose the view_mode accordingly
		if not pick_ids or len(pick_ids) > 1:
			result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
		elif len(pick_ids) == 1:
			res = self.env.ref('stock.view_picking_form', False)
			form_view = [(res and res.id or False, 'form')]
			if 'views' in result:
				result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
			else:
				result['views'] = form_view
			result['res_id'] = pick_ids.id
		return result

	def _get_creation_message(self):
		# OVERRIDE
		if not self.is_invoice(include_receipts=True):
			return super()._get_creation_message()

		if self.is_refund:
			return _('Retur Pembelian Created')			
		elif self.is_pembelian:
			return _('Pembelian Created')
		elif self.is_retur_penj:
			return _('Retur Penjualan Created')			
		elif self.is_penjualan:
			return _('Penjualan Created')
		elif self.is_penj_eceran:
			return _('Penjualan Eceran Created')			
		elif self.is_debit_note_pembelian:
			return _('Debit Note Pembelian Created')
		elif self.is_credit_note_pembelian:
			return _('Credit Note Pembelian Created')
		elif self.is_debit_note_penjualan:
			return _('Debit Note Penjualan Created')
		elif self.is_credit_note_penjualan:
			return _('Credit Note Penjualan Created')
		elif self.type_code == 'KK':
			return _('Kas Keluar Created')
		elif self.type_code == 'KM':
			return _('Kas Masuk Created')
			
		return {
			'out_invoice': _('Invoice Created'),
			'out_refund': _('Refund Created'),
			'in_invoice': _('Vendor Bill Created'),
			'in_refund': _('Credit Note Created'),
			'out_receipt': _('Sales Receipt Created'),
			'in_receipt': _('Purchase Receipt Created'),
		}[self.type]
		

	
	def _get_move_display_name(self, show_ref=False):
		''' Helper to get the display name of an invoice depending of its type.
		:param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
		:return:            A string representing the invoice.
		'''
		self.ensure_one()
		draft_name = ''
		if self.state == 'draft':
			draft_name += {
				'out_invoice': _('Draft Invoice'),
				'out_refund': _('Draft Credit Note'),
				'in_invoice': _('Draft Bill'),
				'in_refund': _('Draft Vendor Credit Note'),
				'out_receipt': _('Draft Sales Receipt'),
				'in_receipt': _('Draft Purchase Receipt'),
				'entry': _('Draft Entry'),
			}[self.type]
			if self.is_refund:
				draft_name = 'Draft Retur Pembelian'
			elif self.is_pembelian:
				draft_name = 'Draft Pembelian'
			elif self.is_retur_penj:
				draft_name = 'Draft Retur Penjualan'
			elif self.is_penjualan:
				draft_name = 'Draft Penjualan'
			elif self.is_penj_eceran:
				draft_name = 'Draft Penjualan Eceran'
			elif self.is_debit_note_pembelian:
				draft_name = 'Draft Debit Note Pembelian'
			elif self.is_credit_note_pembelian:
				draft_name = 'Draft Credit Note Pembelian'
			elif self.is_debit_note_penjualan:
				draft_name = 'Draft Debit Note Penjualan'
			elif self.is_credit_note_penjualan:
				draft_name = 'Draft Credit Note Penjualan'
			elif self.type_code == 'KK':
				draft_name = 'Draft Kas Keluar'
			elif self.type_code == 'KM':
				draft_name = 'Draft Kas Masuk'

			if not self.name or self.name == '/':
				draft_name += ' (* %s)' % str(self.id)
			else:
				draft_name += ' ' + self.name
		return (draft_name or self.name) + (show_ref and self.ref and ' (%s)' % self.ref or '')
	

class AccountMoveLine(models.Model):
	""" Override AccountInvoice_line to add the link to the purchase order line it is related to"""
	_inherit = 'account.move.line'
	
	barcode = fields.Char(related='product_id.barcode', store=False, copy=False, readonly=False, string="Barcode")
	rekap_id = fields.Many2one('rek.peng.brg.penj',string='Rekap')
	warehouse_id = fields.Many2one('stock.warehouse',related='move_id.warehouse_id', copy=False, readonly=False,string="Warehouse")
	discount_amount = fields.Float('Discount (Amount)')
	discount_2 = fields.Float(string='Discount (%)_', digits='Discount', default=0.0)
	location_id = fields.Many2one('stock.location',compute='_compute_location_id', string='Location', required=False, store=True)
	gbr_qty_avalible = fields.Float(compute='_compute_qty_available',copy=False,string="Sisa Stock", store=True)
	volume = fields.Float('M3',compute="_amount_all_kubikasi",store=True)
	weight = fields.Float('Weight',compute="_amount_all_kubikasi",store=True)
	is_pencairan_cek = fields.Boolean('Pencairan Cek',default=False)

	@api.depends('warehouse_id')
	def _compute_location_id(self):
		for moveline in self:
			location_id = False
			# products = self.env['product.product']
			if moveline.warehouse_id:
				location_id = moveline.warehouse_id.lot_stock_id.id
		
			moveline.location_id = location_id

	@api.depends('quantity','product_uom_id')
	def _amount_all_kubikasi(self):
		for order in self:
			volume = 0
			weight = 0
			if order.product_id:
				if order.product_id.kubikasi_uom_id:
					volume = order.product_id.volume * order.product_id.kubikasi_uom_id.factor #100
					volume = volume / order.product_uom_id.factor					

					weight = order.product_id.weight * order.product_id.kubikasi_uom_id.factor #100
					weight = weight / order.product_uom_id.factor

			order.update({			
				'volume': volume * order.quantity,
				'weight': weight * order.quantity,
			})

	@api.depends('location_id','warehouse_id','product_id')
	def _compute_qty_available(self):
		for moveline in self:
			gbr_qty_avalible = 0.0
			# products = self.env['product.product']
			if moveline.location_id:
				if moveline.product_id:
					product = moveline.product_id.with_context(location=moveline.location_id.id)
					gbr_qty_avalible += product.qty_available			
		
			moveline.gbr_qty_avalible = gbr_qty_avalible


	@api.onchange('discount_amount', 'discount_2')
	def _onchange_price_discount_2(self): 
		discount_percent = 0
		if self.price_unit != 0:
			discount_percent = self.discount_amount / self.price_unit * 100
		self.discount = self.discount_2 + discount_percent    	

		return {}

	def _get_computed_account(self):
		self.ensure_one()

		if not self.product_id:
			return

		fiscal_position = self.move_id.fiscal_position_id
		accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
		if self.move_id.partner_id:
			accountss = self.move_id.partner_id._get_vendor_accounts()

		if self.move_id.is_sale_document(include_receipts=True):
			# Out invoice.
			if self.move_id.is_debit_note_penjualan:
				return accountss['debit_note_piutang']
			elif self.move_id.is_credit_note_penjualan:
				return accountss['credit_note_piutang']

			return accounts['income']
		elif self.move_id.is_purchase_document(include_receipts=True):
			# In invoice.
			if self.move_id.is_debit_note_pembelian:				
				return accountss['debit_note_hutang']
			elif self.move_id.is_credit_note_pembelian:
				return accountss['credit_note_hutang']

				# return (kalau ada di partner pakai partner kalau tidak ambil global)
			return accounts['expense']
			
	def _get_stock_move_price_unit(self):
		self.ensure_one()
		line = self[0]
		order = line.move_id

		price_unit = line.price_unit		
		if line.product_uom_id.id != line.product_id.uom_id.id:
			price_unit *= line.product_uom_id.factor / line.product_id.uom_id.factor
		if order.currency_id != order.company_id.currency_id:
			price_unit = order.currency_id._convert(
				price_unit, order.company_id.currency_id, self.company_id, self.date or fields.Date.today(), round=False)
			
		return price_unit

	def _prepare_stock_moves_incoming(self, picking):
		""" Prepare the stock moves data for one order line. This function returns a list of
		dictionary ready to be used in stock.move's create()
		"""
		self.ensure_one()
		res = []
		if self.product_id.type not in ['product', 'consu']:
			return res
		qty = 0.0
		price_unit = self._get_stock_move_price_unit()
		# for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
		# 	qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
		template = {
			# truncate to 2000 to avoid triggering index limit error
			# TODO: remove index in master?
			'name': (self.name or '')[:2000],
			'product_id': self.product_id.id,
			'product_uom': self.product_uom_id.id,
			'date': self.move_id.invoice_date,
			'date_expected': self.move_id.invoice_date,
			'location_id': picking.location_id.id,
			'location_dest_id': picking.location_dest_id.id,#self.move_id._get_destination_location_incoming(),
			'picking_id': picking.id,
			'partner_id': self.move_id.partner_id.id,
			#'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
			'state': 'draft',
			'company_id': self.move_id.company_id.id,
			'price_unit': price_unit,
			'picking_type_id': picking.picking_type_id.id, #self.move_id._get_picking_type_incoming().id,
			'group_id': self.move_id.group_id.id,
			'origin': self.move_id.name,
			#'propagate_date': self.propagate_date,#
			#'propagate_date_minimum_delta': self.propagate_date_minimum_delta,#
			'description_picking': self.product_id._get_description(self.move_id._get_picking_type_incoming()),
			#'propagate_cancel': self.propagate_cancel,#
			'route_ids': self.move_id.warehouse_id and [(6, 0, [x.id for x in self.move_id.warehouse_id.route_ids])] or [],
			'warehouse_id': self.move_id.warehouse_id.id,
		}
		diff_quantity = self.quantity - qty
		if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom_id.rounding) > 0:
			po_line_uom = self.product_uom_id
			quant_uom = self.product_id.uom_id
			product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
			template['product_uom_qty'] = product_uom_qty
			template['product_uom'] = product_uom.id
			res.append(template)
		return res

	def _prepare_stock_moves(self, picking):
		""" Prepare the stock moves data for one order line. This function returns a list of
		dictionary ready to be used in stock.move's create()
		"""
		self.ensure_one()
		res = []
		if self.product_id.type not in ['product', 'consu']:
			return res
		qty = 0.0
		price_unit = self._get_stock_move_price_unit()
		# for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
		# 	qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
		template = {
			# truncate to 2000 to avoid triggering index limit error
			# TODO: remove index in master?
			'name': (self.name or '')[:2000],
			'product_id': self.product_id.id,
			'product_uom': self.product_uom_id.id,
			'date': self.move_id.invoice_date,
			'date_expected': self.move_id.invoice_date,
			'location_id': picking.location_id.id,
			'location_dest_id': self.move_id._get_destination_location().id,
			'picking_id': picking.id,
			'partner_id': self.move_id.partner_id.id,
			#'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
			'state': 'draft',
			'company_id': self.move_id.company_id.id,
			'price_unit': price_unit,
			'picking_type_id': self.move_id._get_picking_type_return().id,
			'group_id': self.move_id.group_id.id,
			'origin': self.move_id.name,
			#'propagate_date': self.propagate_date,#
			#'propagate_date_minimum_delta': self.propagate_date_minimum_delta,#
			'description_picking': self.product_id._get_description(self.move_id._get_picking_type_return()),
			#'propagate_cancel': self.propagate_cancel,#
			'route_ids': self.move_id.warehouse_id and [(6, 0, [x.id for x in self.move_id.warehouse_id.route_ids])] or [],
			'warehouse_id': self.move_id.warehouse_id.id,
		}
		diff_quantity = self.quantity - qty
		if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom_id.rounding) > 0:
			po_line_uom = self.product_uom_id
			quant_uom = self.product_id.uom_id
			product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
			template['product_uom_qty'] = product_uom_qty
			template['product_uom'] = product_uom.id
			res.append(template)
		return res

	def _create_stock_moves(self, picking):
		values = []
		for line in self.filtered(lambda l: not l.display_type):
			if line.product_id:
				for val in line._prepare_stock_moves(picking):
					values.append(val)
		return self.env['stock.move'].create(values)

	def _create_stock_moves_incoming(self, picking):
		values = []
		for line in self.filtered(lambda l: not l.display_type):
			if line.product_id:
				for val in line._prepare_stock_moves_incoming(picking):
					values.append(val)
		return self.env['stock.move'].create(values)

	def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
		"""Retrieve the price before applying the pricelist
			:param obj product: object of current product record
			:parem float qty: total quentity of product
			:param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
			:param obj uom: unit of measure of current order line
			:param integer pricelist_id: pricelist id of sales order"""
		PricelistItem = self.env['product.pricelist.item']
		field_name = 'lst_price'
		currency_id = None
		product_currency = None
		if rule_id:
			pricelist_item = PricelistItem.browse(rule_id)
			if pricelist_item.pricelist_id.discount_policy == 'without_discount':
				while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
					price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.move_id.partner_id)
					pricelist_item = PricelistItem.browse(rule_id)

			if pricelist_item.base == 'standard_price':
				field_name = 'standard_price'
			if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
				field_name = 'price'
				product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
				product_currency = pricelist_item.base_pricelist_id.currency_id
			currency_id = pricelist_item.pricelist_id.currency_id

		product_currency = product_currency or(product.company_id and product.company_id.currency_id) or self.env.company.currency_id
		if not currency_id:
			currency_id = product_currency
			cur_factor = 1.0
		else:
			if currency_id.id == product_currency.id:
				cur_factor = 1.0
			else:
				cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.move_id.date_invoice or fields.Date.today())

		product_uom = self.env.context.get('uom') or product.uom_id.id
		if uom and uom.id != product_uom:
			# the unit price is in a different uom
			uom_factor = uom._compute_price(1.0, product.uom_id)
		else:
			uom_factor = 1.0

		return product[field_name] * uom_factor * cur_factor, currency_id
		
	def _get_computed_price_unit(self):
		self.ensure_one()

		if not self.product_id:
			return self.price_unit
		elif self.move_id.is_sale_document(include_receipts=True):
			# Out invoice.
			price_unit = self.product_id.lst_price
			
			if self.move_id.partner_id.property_product_pricelist.discount_policy == 'with_discount':
				price_unit = self.product_id.with_context(pricelist=self.move_id.partner_id.property_product_pricelist.id).price

			product_context = dict(self.env.context,location=self.warehouse_id.lot_stock_id.id, partner_id=self.move_id.partner_id.id, date=self.move_id.invoice_date, uom=self.product_uom_id.id)

			final_price, rule_id = self.move_id.partner_id.property_product_pricelist.with_context(product_context).get_product_price_rule(self.product_id, self.quantity or 1.0, self.move_id.partner_id)			
			base_price, currency = self.with_context(product_context)._get_real_price_currency(self.product_id, rule_id, self.quantity, self.product_uom_id, self.move_id.partner_id.property_product_pricelist.id)
			
			if currency != self.move_id.partner_id.property_product_pricelist.currency_id:
				base_price = currency._convert(
					base_price, self.order_id.pricelist_id.currency_id,
					self.move_id.company_id or self.env.company, self.move_id.date_invoice or fields.Date.today())
			# negative discounts (= surcharge) are included in the display price
			if self.move_id.partner_id.is_sale :
				move_line_ids = []
				move = self.env['account.move']
				moveline = self.env['account.move.line']
				move_ids = move.search([('partner_id','=',self.partner_id.id),('state','not in',('cancel','draft')),('type', '=', 'out_receipt') ])				
				moves_ids = [x.id for x in move_ids]
				if moves_ids:
					move_line_ids = moveline.search([('partner_id','=',self.partner_id.id),('move_id','in',moves_ids )], limit=1,order="id desc")					
					if move_line_ids:
						price_unit = move_line_ids[0].product_uom_id._compute_price(move_line_ids[0].price_unit, move_line_ids.product_uom_id)
				# move_id
				# cari kesemua penjualan, cari harga jual terakhir.
				# cari id move id nya. 

				# harga jual / uom factor
				# 100 / 0.5 = 200 
				# 200 * factor 
				# def _compute_price(self, price, to_unit):
			if self.move_id.partner_id.is_sale and (price_unit != 0) :
				price_unit = price_unit
			else:
				price_unit = max(base_price, final_price)

		elif self.move_id.is_purchase_document(include_receipts=True):
			# In invoice.
			price_unit = self.product_id.standard_price

		else:
			return self.price_unit

		if self.product_uom_id != self.product_id.uom_id:
			price_unit = self.product_id.uom_id._compute_price(price_unit, self.product_uom_id)

		company = self.move_id.company_id
		if self.move_id.currency_id != company.currency_id:
			price_unit = company.currency_id._convert(
				price_unit, self.move_id.currency_id, company, self.move_id.date)
		return price_unit

	def _create_writeoff(self, writeoff_vals):
		""" Create a writeoff move per journal for the account.move.lines in self. If debit/credit is not specified in vals,
			the writeoff amount will be computed as the sum of amount_residual of the given recordset.
			:param writeoff_vals: list of dicts containing values suitable for account_move_line.create(). The data in vals will
				be processed to create bot writeoff account.move.line and their enclosing account.move.
		"""
		#kalau dari gbr , gunakan cara biasa, 
		#ype_kas_masuk  
		#type_kas_keluar
		#mlk , type_code
		if not self._context.get('disable_search'):	
			return super(AccountMoveLine, self)._create_writeoff(writeoff_vals)

		def compute_writeoff_counterpart_vals(values):
			line_values = values.copy()
			line_values['debit'], line_values['credit'] = line_values['credit'], line_values['debit']
			if 'amount_currency' in values:
				line_values['amount_currency'] = -line_values['amount_currency']
			return line_values
		# Group writeoff_vals by journals
		writeoff_dict = {}
		for val in writeoff_vals:
			journal_id = val.get('journal_id', False)
			if not writeoff_dict.get(journal_id, False):
				writeoff_dict[journal_id] = [val]
			else:
				writeoff_dict[journal_id].append(val)

		partner_id = self.env['res.partner']._find_accounting_partner(self[0].partner_id).id
		company_currency = self[0].account_id.company_id.currency_id
		writeoff_currency = self[0].account_id.currency_id or company_currency
		line_to_reconcile = self.env['account.move.line']
		# Iterate and create one writeoff by journal
		writeoff_moves = self.env['account.move']
		for journal_id, lines in writeoff_dict.items():
			total = 0
			total_currency = 0
			writeoff_lines = []
			date = fields.Date.today()
			for vals in lines:
				# Check and complete vals
				if 'account_id' not in vals or 'journal_id' not in vals:
					raise UserError(_("It is mandatory to specify an account and a journal to create a write-off."))
				if ('debit' in vals) ^ ('credit' in vals):
					raise UserError(_("Either pass both debit and credit or none."))
				if 'date' not in vals:
					vals['date'] = self._context.get('date_p') or fields.Date.today()
				vals['date'] = fields.Date.to_date(vals['date'])
				if vals['date'] and vals['date'] < date:
					date = vals['date']
				if 'name' not in vals:
					vals['name'] = self._context.get('comment') or _('Write-Off')
				if 'analytic_account_id' not in vals:
					vals['analytic_account_id'] = self.env.context.get('analytic_id', False)
				#compute the writeoff amount if not given
				if 'credit' not in vals and 'debit' not in vals:
					amount = sum([r.amount_residual for r in self])
					vals['credit'] = amount > 0 and amount or 0.0
					vals['debit'] = amount < 0 and abs(amount) or 0.0
				vals['partner_id'] = partner_id
				total += vals['debit']-vals['credit']
				if 'amount_currency' not in vals and writeoff_currency != company_currency:
					vals['currency_id'] = writeoff_currency.id
					sign = 1 if vals['debit'] > 0 else -1
					vals['amount_currency'] = sign * abs(sum([r.amount_residual_currency for r in self]))
					total_currency += vals['amount_currency']

				writeoff_lines.append(compute_writeoff_counterpart_vals(vals))

			# Create balance line
			writeoff_lines.append({
				'name': _('Write-Off'),
				'debit':  total > 0 and total or 0.0,
				'credit': total < 0 and -total or 0.0,
				'amount_currency': total_currency,
				'currency_id': total_currency and writeoff_currency.id or False,
				'journal_id': joutotalrnal_id,
				'account_id': self[0].account_id.id,
				'partner_id': partner_id
				})

			# Create the move
			# type_code KK , kas keluar , amount negatif ke KM, amount positif KK
			# CN penerimaan Hutang masuk ke Kas Keluar , write off Debit Hutang usaha, manidir personal credit,
			# dari pembayaran hutang, credit smw masuk ke KK
			# CN penerimaan piutang ke Kas Keluar ,, write off debit piutang usaha ,,mandiri bisnis credit,, 
			# dari penerimaan piutang
			type_code = 'new'
			type_kas_keluar = ''
			type_kas_masuk = ''
			
			if self._context.get('pemb_hutang'):				
				type_kas_keluar = 'PH'
				type_kas_keluar = 'PH'
				if total < 0 :
					type_code = 'KK'
				else:
					type_code = 'KM'

			if self._context.get('pen_piutang'):
				type_kas_keluar = 'PNPTG'
				type_kas_keluar = 'PNPTG'
				if total < 0 :
					type_code = 'KK'
				else:
					type_code = 'KM'
				


			writeoff_move = self.env['account.move'].create({
				'journal_id': journal_id,
				'date': date,
				'state': 'draft',
				'line_ids': [(0, 0, line) for line in writeoff_lines],
				'type_code': type_code,
				'type_kas_masuk': type_kas_masuk,
				'type_kas_keluar': type_kas_keluar,
				'partner_id': partner_id
			})
			writeoff_moves += writeoff_move
			line_to_reconcile += writeoff_move.line_ids.filtered(lambda r: r.account_id == self[0].account_id).sorted(key='id')[-1:]

		#post all the writeoff moves at once
		if writeoff_moves:
			writeoff_moves.post()

		# Return the writeoff move.line which is to be reconciled
		return line_to_reconcile
