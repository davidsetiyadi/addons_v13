import json
from datetime import datetime, timedelta
import time

from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError, RedirectWarning

from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import random

import ast


TYPE = [('head','Head'),('tpi','TPI-GHE')]
SALE = [('sale','Penjualan Barang')]
CODE_SELECTION = [('new','New'),('credit','CR'),('cash','CH'),('debit_note','DN'),('credit_note','CN'),('retur_credit','RTC'),('mm','MM')]

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",default=lambda self: self.env.user.employee_id.divisi_id)
	option = fields.Selection(TYPE, string="Options")
	title = fields.Selection(SALE, string="Title")
	purchase_id = fields.Many2one('purchase.order', string="No P.O")
	purchase_char_id = fields.Many2one('gbr.po.number', string='NO PO', required=False, readonly=True,
		states={'draft': [('readonly', False)]})
	is_customer = fields.Boolean('Pelanggan')
	is_quotation = fields.Boolean('Quotation')
	is_order = fields.Boolean('Sale Orders')
	other_partner = fields.Char('Customer 2')
	phone = fields.Char('Telephone')
	sales_id = fields.Many2one('hr.employee', string="Sales")
	department_id = fields.Many2one('hr.department', string="Divisi2")
	h_jual = fields.Char("H.Jual")
	gbr_sale_total = fields.Monetary(string='Totals', compute="_amount_all_gbr", store=True, readonly=True,tracking=4)
	discount = fields.Float('Discount')
	percent_disc = fields.Float('Discount (%)')
	subject = fields.Char('Subject')
	tender = fields.Char('Tender')
	warranty = fields.Char('Warranty')
	no_append = fields.Char('NO Append', default=lambda self: _('New'), copy=False)
	number_join = fields.Char(compute='_compute_number_join', string="Number Join",store=True, copy=False)
	total_weight = fields.Float(string='Total Berat', compute="_amount_all_2")
	total_volume = fields.Float(string='Total Volume', compute="_amount_all_2")
	total_qty = fields.Float(string='Total Qty', compute="_amount_all_2")
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	
	def _amount_all_2(self):
		product_obj = self.env['product.product']
		for order in self:
			total_volume = total_weight = amount_untaxed = amount_tax = amount_disc = product_qty = discount = 0.0
			product_uom = ''
			for line in order.order_line:				
				product_qty += line.product_uom_qty / line.product_uom.factor or 1
				total_weight += line.weight
				total_volume += line.volume				
				
			order.update({				
				'total_qty': product_qty,
				'total_weight': total_weight,
				'total_volume': total_volume,				
			})

	def _get_creation_message(self):
		# OVERRIDE
		if self.is_order:
			return _('Sale Order Created')			
		elif self.is_quotation:
			return _('Quotation Created')
		else:
			return super()._get_creation_message()
		

	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:
				quot_seq = self.env.context.get('quot_seq', False)
				sale_order_gbr = self.env.context.get('sale_order_gbr', False)
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				if quot_seq:
					vals['no'] = str(divisi_id.quot_seq).zfill(5)
					divisi_id.write({'quot_seq': divisi_id.quot_seq+1 })
				elif sale_order_gbr:
					vals['no'] = str(divisi_id.sale_order).zfill(5)
					divisi_id.write({'sale_order': divisi_id.sale_order+1 })

			if vals.get('no_append', _('New')) == _('New'):
				awalan_pembelian = self.env.company.awalan_pembelian
				vals['no_append'] = str(awalan_pembelian)+'/' + time.strftime('%m')+'/'+ time.strftime('%Y')
			
		result = super(SaleOrder, self).create(vals)
		return result


	def name_get(self):
		if self._context.get('default_is_penjualan'):
			res = []
			for order in self:
				name = order.name
				if order.number_join:
					name = '%s - %s' % ( order.number_join,name)
				res.append((order.id, name))
			return res
		return super(SaleOrder, self).name_get()

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		if not self.env.context.get('default_is_penjualan'):
			return super(SaleOrder, self)._name_search(name, args, operator, limit, name_get_uid=name_get_uid)
	  
		if self._context.get('default_is_penjualan'):
			if operator == 'ilike' and not (name or '').strip():
				domain = []
			elif operator in ('ilike', 'like', '=', '=like', '=ilike'):
				domain = expression.AND([
					args or [],
					['|', ('name', operator, name), ('number_join', operator, name)]
				])
				order_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
				return models.lazy_name_get(self.browse(order_ids).with_user(name_get_uid))
		return super(SaleOrder, self)._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

	@api.model
	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(SaleOrder, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(SaleOrder, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		
	@api.depends('no','no_append')
	def _compute_number_join(self):		
		for sales in self:			
			sales.number_join = sales.no +'/'+sales.no_append

	@api.onchange('is_customer','partner_id')
	def _get_partner(self):
		partner_config = self.company_id.other_customer_id.id
		if self.is_customer == True:
			self.partner_id = partner_config

	@api.onchange('partner_id','discount')
	def _get_value_price(self):
		for order in self:
			if order.partner_id:				
				order.pricelist_id = order.partner_id.property_product_pricelist.id

			if order.discount > 0.0:
				order.percent_disc = order.discount/100 * order.amount_untaxed
			else:
				order.percent_disc = 0.0


	@api.depends('order_line.price_total','percent_disc')
	def _amount_all_gbr(self):
		for order in self:
			amount_untaxed = gbr_total = disc = discount = 0.0
			for line in order.order_line:
				amount_untaxed += line.price_subtotal
				gbr_total += line.price_total
				discount = order.percent_disc
				
			order.update({				
				'amount_untaxed': amount_untaxed,
				'gbr_sale_total': gbr_total - discount,
			})			


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	gift = fields.Char('Bonus')
	disc1 = fields.Float('Discount')
	discount_amount = fields.Float('Discount (Amount)')
	discount_2 = fields.Float(string='Discount (%)_', digits='Discount', default=0.0)
	note = fields.Text('Catatan')
	default_code = fields.Char('Kode')
	barcode = fields.Char('Kode (2)')
	qty_available = fields.Float(compute='_compute_qty_available',string='Sisa Stock', store=True)
	warehouse_id = fields.Many2one('stock.warehouse',related='order_id.warehouse_id', copy=False, readonly=False,string="Warehouse")
	location_id = fields.Many2one('stock.location',related='warehouse_id.lot_stock_id', string='Location', required=False)
	gbr_price_unit = fields.Float('GBR Price')
	volume = fields.Float('M3',compute="_amount_all",store=True)
	weight = fields.Float('Weight',compute="_amount_all",store=True)

	@api.depends('product_uom','product_uom_qty')
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
				'volume': volume * order.product_uom_qty,
				'weight': weight * order.product_uom_qty,
			})


	@api.depends('location_id','warehouse_id','product_id')
	def _compute_qty_available(self):
		for moveline in self:
			gbr_qty_avalible = 0.0
			# products = self.env['product.product']
			if moveline.location_id:
				product = moveline.product_id.with_context(location=moveline.location_id.id)
				gbr_qty_avalible += product.qty_available			
		
			moveline.qty_available = gbr_qty_avalible

	@api.onchange('product_uom', 'product_uom_qty')
	def product_uom_change(self):
		if self._context.get('is_gbr'):
			partner = self.order_id.partner_id.id
			if self.order_id.partner_id.is_sale:
				value = """ SELECT price_unit from sale_order_line where product_id = %s and order_partner_id = %s order by id DESC limit 1 """ %(self.product_id.id, partner)
				res = self.env.cr.execute(value)
				result = self.env.cr.fetchone()			
				self.price_unit = result[0]
		
	
	@api.onchange('product_id')
	def product_id_change_sale(self):
		if self._context.get("is_gbr_sales"):
			vals = {}	
			partner = self.order_id.partner_id.id
			if self.order_id.partner_id.is_sale:
				value = """ SELECT price_unit from sale_order_line where product_id = %s and order_partner_id = %s order by id DESC limit 1 """ %(self.product_id.id, partner)
				res = self.env.cr.execute(value)
				result = self.env.cr.fetchone()
			
				self.price_unit = result[0]
				self.default_code = self.product_id.default_code
				self.barcode = self.product_id.barcode
				self.product_uom = self.product_id.uom_id.id
				self.gift = 0.00
				self.qty_available = self.product_id.qty_available
				self.name = self.product_id.name				


			else:
				self.default_code = self.product_id.default_code
				self.barcode = self.product_id.barcode
				self.qty_available = self.product_id.qty_available
				self.gift = 0.00
				self.name = self.product_id.name				

				if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
					vals['product_uom'] = self.product_id.uom_id
					vals['product_uom_qty'] = self.product_uom_qty or 0.0

				product = self.product_id.with_context(
				lang=self.order_id.partner_id.lang,
				partner=self.order_id.partner_id,
				quantity=vals.get('product_uom_qty') or self.product_uom_qty,
				date=self.order_id.date_order,
				pricelist=self.order_id.pricelist_id.id,
				uom=self.product_uom.id
				)
				vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

				self._compute_tax_id()
				if self.order_id.pricelist_id and self.order_id.partner_id:
						vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
						self.update(vals)
		else:	
			order = super(SaleOrderLine, self).product_id_change()
			return order


	@api.onchange('product_id')
	def product_id_change(self):
		if not self.order_id.partner_id:
			raise ValidationError(_('Sorry, No Result Partner,, make sure select partner in advance'))

		if self._context.get("is_gbr"):
			vals = {}	
			partner = self.order_id.partner_id.id
			if self.order_id.partner_id.is_sale:
				value = """ SELECT price_unit from sale_order_line where product_id = %s and order_partner_id = %s order by id DESC limit 1 """ %(self.product_id.id, partner)
				res = self.env.cr.execute(value)
				result = self.env.cr.fetchone()
			
				self.price_unit = result[0]
				self.default_code = self.product_id.default_code
				self.barcode = self.product_id.barcode
				self.product_uom = self.product_id.uom_id.id
				self.gift = 0.00
				self.qty_available = self.product_id.qty_available
				self.name = self.product_id.name				


			else:
				self.default_code = self.product_id.default_code
				self.barcode = self.product_id.barcode
				self.qty_available = self.product_id.qty_available
				self.gift = 0.00
				self.name = self.product_id.name				

				if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
					vals['product_uom'] = self.product_id.uom_id
					vals['product_uom_qty'] = self.product_uom_qty or 0.0

				product = self.product_id.with_context(
				lang=self.order_id.partner_id.lang,
				partner=self.order_id.partner_id,
				quantity=vals.get('product_uom_qty') or self.product_uom_qty,
				date=self.order_id.date_order,
				pricelist=self.order_id.pricelist_id.id,
				uom=self.product_uom.id
				)
				vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

				self._compute_tax_id()
				if self.order_id.pricelist_id and self.order_id.partner_id:
					vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
					self.update(vals)
		else:	
			order = super(SaleOrderLine, self).product_id_change()
			return order
	
	@api.onchange('discount_amount','discount_2')
	def discount_change(self):
		discount_percent = 0
		if self.price_unit != 0:
			discount_percent = self.discount_amount / self.price_unit * 100
		self.discount = self.discount_2 + discount_percent
		
		return {}
			
class RekPengBrgPenj(models.Model):
	_name = 'rek.peng.brg.penj'
	_inherit = ['mail.thread', 'mail.activity.mixin']    
	_description = "pengeluaran barang penjualan"
	_rec_name = "no"

	name = fields.Char('Name',required=True, copy=False, index=True, default=lambda self: _('New'))
	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	date = fields.Date(string='Date', default=fields.Date.context_today, required=True, copy=False, tracking=True)
	catatan = fields.Char('catatan')
	catatan_2 = fields.Char('catatan *2')
	catatan_3 = fields.Char('catatan *3')
	# divisi = fields.Selection([('head', 'Head'), ('tpi_ghe', 'TPI - GHE')], readonly=False, default='head', copy=True, string="Divisi")
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",default=lambda self: self.env.user.employee_id.divisi_id)
	penjualan_ids = fields.Many2many('account.move','rekap_account_move_rel','move_id','rekap_id', string='Penjualan')
	list_penjualan_ids = fields.One2many('account.move.line', 'rekap_id', 'List Penjualan')
	company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
	is_semua_data = fields.Boolean(string='Semua Data',default=True)

	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			seq_date = None
			
			if 'company_id' in vals:
				vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
					'rek.peng.brg.penj', sequence_date=seq_date) or _('New')
			else:
				vals['name'] = self.env['ir.sequence'].next_by_code('rek.peng.brg.penj', sequence_date=seq_date) or _('New')
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				vals['no'] = str(divisi_id.rkp_peng_brg).zfill(5)
				divisi_id.write({'rkp_peng_brg': divisi_id.rkp_peng_brg +1 })
			
		result = super(RekPengBrgPenj, self).create(vals)
		return result

	@api.model
	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):
			if len(domain) == 0:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(RekPengBrgPenj, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(RekPengBrgPenj, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	def button_refresh(self):
		#cari semua account move line yang rekap_id = self id, kosongkan.
		#cari semua account move line , dari penjualan_ids, writekan.
		aml_obj = self.env['account.move.line']
		aml_ids = aml_obj.search([('rekap_id','=',self.id)])
		for amls in aml_ids:
			amls.write({'rekap_id':False})

		moves_ids = [x.id for x in self.penjualan_ids]
		if moves_ids:
			penj_aml_ids = aml_obj.search([('move_id','in',moves_ids),('product_id','!=',False)])
			for penj_aml_id in penj_aml_ids:
				penj_aml_id.write({'rekap_id':self.id})

		return True#self.write({'state': 'cancel'})

class GbrInvoiceStatement(models.Model):
	_name = 'gbr.invoice.statement'
	_inherit = ['mail.thread', 'mail.activity.mixin']  
	_description = 'Invoice Statement Penjualan'
	_rec_name = "no"

	active = fields.Boolean('Archive',default=True,
		help="If unchecked, it will allow you to hide the statement without removing it.")
	name = fields.Char('Name',required=True, copy=False, index=True, default=lambda self: _('New'))
	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	no_append = fields.Char('NO Append', default=lambda self: _('New')) #ghe/07/2020
	date_start = fields.Date('Date Start', required=True, tracking=1, default=lambda *a: time.strftime('%Y-%m-%d'))
	date_end = fields.Date('Date To', required=True, tracking=2, default=lambda *a: time.strftime('%Y-%m-%d'))
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",default=lambda self: self.env.user.employee_id.divisi_id)
	employee_id = fields.Many2one('hr.employee', string="Sales", tracking=3)
	currency_id = fields.Many2one('res.currency', string="MU", tracking=4)
	partner_id = fields.Many2one('res.partner', string="Pelanggan", tracking=5)
	discount 	= fields.Float('Discount')
	discount_percent = fields.Float('Discount %')
	credit		= fields.Float('Credit')
	catatan 	= fields.Char('Catatan') 
	catatan_2	= fields.Char('Catatan 2') 
	catatan_3	= fields.Char('Catatan 3') 
	total_harga = fields.Float('Total Harga')
	total_discount = fields.Float('Total Discount')
	total_pajak  = fields.Float('Total Pajak')
	total_retur = fields.Float('Total Retur')
	total_adjust = fields.Float('Total Adjust')
	total_deposit = fields.Float('Total Deposit')
	total_amount = fields.Float('Total Amount')
	line_ids = fields.One2many('gbr.invoice.statement.line','statement_id', string='Line_ids')
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	
	
	@api.model
	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):
			if len(domain) == 0:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(GbrInvoiceStatement, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(GbrInvoiceStatement, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		
	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				vals['no'] = str(divisi_id.invoice_stat_pen).zfill(5)
				divisi_id.write({'invoice_stat_pen': divisi_id.invoice_stat_pen +1 })
		if vals.get('no_append', _('New')) == _('New'):
			awalan_pembelian = self.env.company.awalan_pembelian
			vals['no_append'] = str(awalan_pembelian)+'/' + time.strftime('%m')+'/'+ time.strftime('%Y') # '/%(range_year)s/'
			# lambda *a: time.strftime('%Y-%m-%d')
			
		result = super(GbrInvoiceStatement, self).create(vals)
		return result

	def unlink(self):
		for line in self:
			if line.line_ids:
				raise UserError(_('In statement to delete a  statement line, you must first cancel it to delete related statement items.')) 
		ret = super(GbrInvoiceStatement, self).unlink()			
		return ret

	# onchange

class GbrInvoiceStatementLine(models.Model):
	_name = 'gbr.invoice.statement.line'
	# _inherit = ['mail.thread', 'mail.activity.mixin']  
	_description = 'Invoice Statement Line'
	_rec_name = "invoice_id"

	statement_id = fields.Many2one('gbr.invoice.statement', string='Line_ids')
	invoice_id = fields.Many2one('account.move', 'List')
	partner_id = fields.Many2one('res.partner', string="Pelanggan")
	no = fields.Char('NO',related='invoice_id.no')
	ref = fields.Char('Ref',related='invoice_id.ref')		
	invoice_date = fields.Date('Tanggal',related='invoice_id.invoice_date')
	currency_id = fields.Many2one('res.currency' , string='MU',related='invoice_id.currency_id')
	harga_jual = fields.Float(compute='_compute_jual',string='Harga Jual')
	discount = fields.Float('Discount')
	nilai_jual =fields.Float(compute='_compute_jual',string='Nilai Jual')
	invoice_payment_term_id = fields.Many2one('account.payment.term', 'Jatuh Tempo',related='invoice_id.invoice_payment_term_id')
	invoice_date_due = fields.Date('Tanggal Jatuh Tempo',related='invoice_id.invoice_date_due')	
	sale_2_id = fields.Many2one('sale.order', string='Sale Order',related='invoice_id.sale_2_id')
	purchase_char_id = fields.Many2one('gbr.po.number', string='Purchase Order', related='invoice_id.purchase_char_id')
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",related='invoice_id.divisi_id')
	type_code = fields.Selection(CODE_SELECTION,string='Mlk',related='invoice_id.type_code')


	def _compute_jual(self):
		for statement_line in self:
			harga_jual = 0.0
			nilai_jual = 0.0
			# products = self.env['product.product']
			if statement_line.invoice_id:
				harga_jual = statement_line.invoice_id.amount_untaxed
				nilai_jual = statement_line.invoice_id.amount_total
		
			statement_line.harga_jual = harga_jual
			statement_line.nilai_jual = nilai_jual
	
