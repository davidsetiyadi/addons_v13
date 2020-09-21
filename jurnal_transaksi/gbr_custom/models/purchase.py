import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.osv import expression
from odoo.release import version
from odoo.tools.float_utils import float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import random

import ast
import time

MU = [('idr','IDR'),('sin','SGD')]
TYPE = [('jen_pemb', 'Pembelian Barang')]
TYPE2 = [('pjk','PJK'),('ppn','PPN')]
class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	READONLY_STATES = {
		'purchase': [('readonly', True)],
		'done': [('readonly', True)],
		'cancel': [('readonly', True)],
	}

	is_purchase_gbr = fields.Boolean('Active', default=True)
	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	no_append = fields.Char('NO Append', default=lambda self: _('New'), copy=False) #ghe/07/2020
	# divisi = fields.Selection([('head', 'Head'), ('tpi_ghe', 'TPI - GHE')], readonly=False, states=READONLY_STATES,  default='head', copy=False, string="Divisi")
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",readonly=False, states=READONLY_STATES,default=lambda self: self.env.user.employee_id.divisi_id, copy=False)
	mu_transaction = fields.Selection(MU, string="M.U")
	is_print_qty = fields.Boolean('Print Total Quantity', default=True)
	is_print_price = fields.Boolean('Print Harga PO', default=True)
	discount = fields.Float('Discount')
	disc_perc = fields.Float('Discount%')
	order_taxes = fields.Float('PJK/PPN')
	total_qty = fields.Float(string='Total Qty', compute="_amount_all")
	total_weight = fields.Float(string='Total Berat', compute="_amount_all")
	total_volume = fields.Float(string='Total Volume', compute="_amount_all")
	uom = fields.Char('Satuan')
	amount_disc = fields.Float('Amount Discount', compute="_amount_all",store=True)
	amount_disc_total = fields.Float('Amount Discount Total', compute="_amount_all_2")
	type_order = fields.Selection(TYPE, string="Jenis Pembelian")
	address = fields.Char('Kirim ke')
	close_date = fields.Date('Tutup')
	option = fields.Selection(TYPE2, string="%PJK/PPN")
	tax_gbr = fields.Float('Tax')
	warehouse_id = fields.Many2one('stock.warehouse', string="Gudang",required=False, readonly=True, states={'draft': [('readonly', False)]})
	print_user_id = fields.Many2one('res.users', string="Print By",required=False,tracking=True)
	gbr_invoice_id = fields.Many2one('account.move',  compute='_compute_gbr_invoice_id', string="Pembelian")
	number_join = fields.Char(compute='_compute_number_join', string="Number Join",store=True, copy=False)
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	confirm_date = fields.Datetime(string='Confirm Date', copy=False, tracking=True)
	confirm_id = fields.Many2one('res.users', string='Confirm by', copy=False, tracking=True)

	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:
				
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				vals['no'] = str(divisi_id.purchase_seq).zfill(5)
				divisi_id.write({'purchase_seq': divisi_id.purchase_seq +1 })
		if vals.get('no_append', _('New')) == _('New'):
			awalan_pembelian = self.env.company.awalan_pembelian

			vals['no_append'] = str(awalan_pembelian)+'/' + time.strftime('%m')+'/'+ time.strftime('%Y') # '/%(range_year)s/'
			# lambda *a: time.strftime('%Y-%m-%d')
			
		result = super(PurchaseOrder, self).create(vals)
		return result

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		if not self.env.context.get('default_is_pembelian'):
			return super(PurchaseOrder, self)._name_search(name, args, operator, limit, name_get_uid=name_get_uid)

		args = args or []
		domain = []
		if name:
			domain = ['|','|', ('name', operator, name), ('partner_ref', operator, name),('number_join',operator,name)]

		purchase_order_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
		return models.lazy_name_get(self.browse(purchase_order_ids).with_user(name_get_uid))
		# 

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(PurchaseOrder, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(PurchaseOrder, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	@api.depends('name', 'partner_ref','number_join')
	def name_get(self):
		# result = super(PurchaseOrder, self).name_get()
		# print ('resultsss',result)
		result = []
		for po in self:
			new_name = po.name
			if self.env.context.get('default_is_pembelian'):
				new_name = po.no +'/'+po.no_append+' ('+po.name+')'
			# name = po.name
			if po.partner_ref:
				new_name += ' (' + po.partner_ref + ')'
			if self.env.context.get('show_total_amount') and po.amount_total:
				new_name += ': ' + formatLang(self.env, po.amount_total, currency_obj=po.currency_id)
			result.append((po.id, new_name))
		return result


	def action_view_invoice_gbr(self,context={}):
		action = self.env.ref('account.action_move_in_invoice_type')
		result = action.read()[0]
		create_bill = self.env.context.get('create_bill', False)
		result['context'] = {
			'default_type': 'in_invoice',
			'default_company_id': self.company_id.id,
			'default_purchase_id': self.id,
		}
		if len(self.invoice_ids) > 1 and not create_bill:
			result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
		else:
			res = self.env.ref('gbr_custom.view_2_move_form', False)
			form_view = [(res and res.id or False, 'form')]
			if 'views' in result:
				result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				result['views'] = form_view
			if not create_bill:
				result['res_id'] = self.invoice_ids.id or False
		result['context']['default_origin'] = self.name
		result['context']['default_reference'] = self.partner_ref
		return result

	def action_create_bill_gbr2(self,context={}):
		action = self.env.ref('account.action_move_in_invoice_type')
		result = action.read()[0]
		create_bill = self.env.context.get('create_bill', False)
		result['context'] = {
			'default_type': 'in_invoice',
			'default_company_id': self.company_id.id,
			'default_purchase_id': self.id,
		}
		if len(self.invoice_ids) > 1 and not create_bill:
			result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
		else:
			res = self.env.ref('gbr_custom.view_2_move_form', False)
			form_view = [(res and res.id or False, 'form')]
			if 'views' in result:
				result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				result['views'] = form_view
			if not create_bill:
				result['res_id'] = self.invoice_ids.id or False
		result['context']['default_origin'] = self.name
		result['context']['default_reference'] = self.partner_ref
		return result
	
	@api.depends('no','no_append')
	def _compute_number_join(self):		
		for purchase in self:			
			purchase.number_join = purchase.no +'/'+purchase.no_append

	@api.onchange('warehouse_id')
	def onchange_warehouse_id(self):
		if self.warehouse_id :
			picking_type_id = 1
			#search picking type , invcoming, where warehouse_id 
			picking_type = self.env['stock.picking.type']
			picking_type_ids = picking_type.search([('code','=','incoming'),('warehouse_id','=',self.warehouse_id.id)])
			if picking_type_ids:
				picking_type_id = picking_type_ids[0]

			self.picking_type_id = picking_type_id		
		return{}

	@api.onchange('disc_perc')
	def onchange_total_disc_perc(self):
		if self.env.context.get("noonchange"):					
			# self.with_context(noonchange=False).discount = self.disc_perc/100 * self.amount_untaxed
			self.discount = self.disc_perc/100 * self.amount_untaxed			
			# self.amount_total = self.amount_untaxed - self.amount_disc - self.discount + self.order_taxes	
		
		return{}

	@api.onchange('discount')
	def onchange_total_disc(self):		
		if not self.env.context.get("noonchange"):
			if self.amount_untaxed != 0:
				self.disc_perc = self.discount / self.amount_untaxed * 100

		return{}


	@api.depends('discount','order_line.price_total','order_line.discount','order_line.disc1','order_line.disc2','order_line.disc3','order_line.product_qty','order_line.product_uom')
	def _amount_all(self):
		product_obj = self.env['product.product']
		for order in self:
			total_volume = total_weight = amount_untaxed = amount_tax = amount_disc = product_qty = discount = 0.0
			product_uom = ''
			for line in order.order_line:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
				amount_disc += line.discount+(line.disc1/100*line.price_subtotal)+(line.disc2/100*line.price_subtotal)+(line.disc3/100*line.price_subtotal)
				product_qty += line.product_qty / line.product_uom.factor
				total_weight += line.weight
				total_volume += line.cubic
				if line.product_id:
					product_uom = line.product_id.uom_id.name
				discount += order.disc_perc/100 * line.price_subtotal
				
			order.update({
				'amount_untaxed': order.currency_id.round(amount_untaxed),
				'amount_tax': order.currency_id.round(amount_tax),
				'amount_disc': order.currency_id.round(amount_disc),
				'total_qty': product_qty,
				'total_weight': total_weight,
				'total_volume': total_volume,
				'uom': product_uom,
				'amount_total': amount_untaxed - amount_disc - order.discount,
			})

			# if order.disc_perc > 0 or order.tax_gbr > 0:
			# 	order.update({
			# 		# 'discount':discount,
			# 		'order_taxes' : order.tax_gbr/100 * order.amount_total,
			# 		'amount_total': amount_untaxed - amount_disc - discount + order.order_taxes,
			# })

	def _amount_all_2(self):
		for order in self:
			amount_disc_total = 0
			amount_disc_total = order.amount_disc + order.discount
			order.update({			
				'amount_disc_total': amount_disc_total,
			})

	def print_quotation(self):
		self.write({'print_user_id': self.env.user.id})
		purchase = super(PurchaseOrder, self).print_quotation()		
		return purchase
		# return self.env.ref('purchase.report_purchase_quotation').report_action(self)

	# @api.depends('commercial_partner_id')
	def _compute_gbr_invoice_id(self):
		invoices = self.env['account.move']
		for purchase in self:
			purchase.gbr_invoice_id = False
			invoice_ids = invoices.search([('purchase_2_id','=',purchase.id)])
			if invoice_ids:
				purchase.gbr_invoice_id = invoice_ids[0].id
	
	def action_filter_data(self):
		active_ids = self.env.context.get('active_ids')
		if not active_ids:
			return ''

		return {
			'name': _('Filter Data'),
			'res_model': len(active_ids) == 1 and 'gbr.filter.data' or 'gbr.filter.data',
			'view_mode': 'form',
			'view_id': len(active_ids) != 1 and self.env.ref('gbr_custom.view_gbr_filter_data_po_form').id or self.env.ref('gbr_custom.view_gbr_filter_data_po_form').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	default_code = fields.Char('Kode')
	barcode = fields.Char('Kode (2)')
	discount = fields.Float('Discount')
	discount_2 = fields.Float('Discount_2')
	discount_amount = fields.Float('Discount Amount')
	# discount_total = fields.Float('Discount Total')
	disc_item = fields.Float('Discount 2')
	disc1 = fields.Float('Disc %')
	disc2 = fields.Float('Disc %2')
	disc3 = fields.Float('Disc %3')
	sat_kecil = fields.Float('Jml-Sat Kecil')
	pb1 = fields.Float('(Pb) Real')
	pb2 = fields.Float('(Pb) %Real')	
	pb3 = fields.Float('(Pb) Blm Real')
	pb4 = fields.Float('(Pb)% Blm')	
	note = fields.Char('Catatan')
	cubic = fields.Float('M3',compute="_amount_all",store=True)
	weight = fields.Float('Weight',compute="_amount_all",store=True)
	price = fields.Float('Harga')
	item_note = fields.Char('Item Catatan')
	term1 = fields.Float('(Term) Real')
	term2 = fields.Float('(Term) %Real')	
	term3 = fields.Float('(Term) Blm Real')
	term4 = fields.Float('(Term)% Blm')	
	amount_total = fields.Float('Nilai')
	warehouse_id = fields.Many2one('stock.warehouse',related='order_id.warehouse_id', copy=False, readonly=False,string="Warehouse")
	location_id = fields.Many2one('stock.location',compute='_compute_location_id', string='Location', required=False, store=True)
	gbr_qty_avalible = fields.Float(compute='_compute_qty_available',copy=False,string="Sisa Stock", store=True)

	@api.depends('warehouse_id')
	def _compute_location_id(self):
		for moveline in self:
			location_id = False
			# products = self.env['product.product']
			if moveline.warehouse_id:
				location_id = moveline.warehouse_id.lot_stock_id.id
		
			moveline.location_id = location_id

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

	@api.depends('product_uom','product_qty')
	def _amount_all(self):
		for order in self:
			volume = 0
			weight = 0
			if order.product_id:
				if order.product_id.kubikasi_uom_id:
					volume = order.product_id.volume * order.product_id.kubikasi_uom_id.factor #100
					volume = volume / order.product_uom.factor					

					weight = order.product_id.weight * order.product_id.kubikasi_uom_id.factor #100
					weight = weight / order.product_uom.factor

			order.update({			
				'cubic': volume * order.product_qty,
				'weight': weight * order.product_qty,
			})


	@api.onchange('product_id')
	def onchange_product(self):
		self = self.with_context(noonchange=True)
		for rec in self:
			if 	rec.product_id:
				rec.default_code = rec.product_id.default_code
				rec.barcode = rec.product_id.barcode
				rec.price = rec.product_id.buying_price
				rec.discount = 0
				rec.discount_amount = 0
				rec.discount_2 = 0
				rec.amount_total = rec.price_subtotal
				rec.cubic = rec.product_id.volume
				rec.weight = rec.product_id.weight	
			
	
	@api.onchange('product_qty', 'product_uom')
	def _onchange_quantity_2(self):
		if not self.product_id:
			return
		if self.env.context.get('disc_percent'):
			params = {'order_id': self.order_id}
			seller = self.product_id._select_seller(
				partner_id=self.partner_id,
				quantity=self.product_qty,
				date=self.order_id.date_order and self.order_id.date_order.date(),
				uom_id=self.product_uom,
				params=params)

			if seller or not self.date_planned:
				self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

			if not seller:
				if self.product_id.seller_ids.filtered(lambda s: s.name.id == self.partner_id.id):
					self.price_unit = 0.0
				return

			price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, self.product_id.supplier_taxes_id, self.taxes_id, self.company_id) if seller else 0.0
			if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
				price_unit = seller.currency_id._convert(
					price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

			if seller and self.product_uom and seller.product_uom != self.product_uom:
				price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

			self.price_unit = price_unit
			self.price = price_unit
			 
			self._onchange_price_discount_2()

	@api.onchange('discount_amount', 'discount_2')
	def _onchange_price_discount_2(self): 
		discount_percent = 0
		if self.price_unit != 0:
			discount_percent = self.discount_amount / self.price_unit * 100
		self.discount = self.discount_2 + discount_percent    	

		return {}

	@api.onchange('discount','product_qty')
	def onchange_discount(self):
		if self.env.context.get('disc_percent'):
			if self.product_id:
				if self.product_id.kubikasi_uom_id:
					volume = self.product_id.volume * self.product_id.kubikasi_uom_id.factor #100
					volume = volume / self.product_uom.factor

					weight = self.product_id.weight * self.product_id.kubikasi_uom_id.factor #100
					weight = weight / self.product_uom.factor

					self.cubic = volume * self.product_qty
					self.weight = weight * self.product_qty
					# 10 liter = 1 CTN10 || 10 / 0.1 = 1
					# 1 liter  = 1 pcs

			if self.price > 0:
				self = self.with_context(disc_percent=False)
				self.amount_total = self.price_subtotal-(self.discount/100 * self.price_subtotal)
				

	@api.onchange('price')
	def onchange_price_item(self):
		if self.env.context.get('disc_percent'):
			self.price_unit = self.price
			self.amount_total = self.price_subtotal-(self.discount/100 * self.price_subtotal)

	# @api.onchange('disc1','disc2','disc3','price','product_qty')
	# def onchange_value_disc_item(self):
	# 	if self.disc1 == 0 or self.disc2 == 0 or self.disc3 == 0:
	# 		self.disc_item = 0
	# 		self.amount_total = self.price_subtotal - 0

	# 	# if self.discount > 0:
	# 	# 	self.disc_item = self.discount * 0.1
	# 	self = self.with_context(disc_percent=False)
		

	# 	if self.price > 0:
	# 		self.price_unit = self.price

	# 	if self.product_qty > 0:
	# 		self.price_subtotal = self.product_qty * self.price
	# 		self.amount_total = self.price_subtotal - 0

	# 	if  self.disc1 > 0 or self.disc2 > 0 or self.disc3 > 0:
	# 		self.amount_total = self.price_subtotal-(self.disc1/100 * self.price_subtotal + self.disc2/100*self.price_subtotal + self.disc3/100 * self.price_subtotal)
		
	# 	return{}

	

		


	
	