import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form


class WizardsFilter(models.TransientModel):
	_name = 'purchase.filter'
	_description = 'Purchase Filter'

	@api.model
	def default_get(self,fields):
		res = super(WizardsFilter, self).default_get(fields)
		active_ids = self._context.get('active_ids')
		if not active_ids:
			return res		

		if self._context.get('from_pembelian'):
			purchase_id = self.env['account.move'].browse(active_ids)
			if purchase_id.purchase_2_id:
				purchase_obj = self.env['purchase.order'].browse(purchase_id.purchase_2_id.id)
		elif self._context.get('from_penjualan'):
			sale_id = self.env['account.move'].browse(active_ids)
			if sale_id.sale_2_id:
				purchase_obj = self.env['sale.order'].browse(sale_id.sale_2_id.id)
		else:
			purchase_obj = self.env['purchase.order'].browse(active_ids)
		filter_ids = []
		sql_group_1_ids = ''
		sql_group_2_ids = ''
		sql_group_3_ids = ''
		
		for data in purchase_obj:
			if data.partner_id:
				query_product_ids = """ 
					SELECT pp.default_code,pt.vendor_id,pp.barcode,pp.buying_price,pt.name,pt.uom_id,pp.id,pp.category_uom_id from product_product pp 
					inner join product_template pt on pt.id = pp.product_tmpl_id 
					where pt.vendor_id= %s %s %s %s group by 
					pt.name,pp.default_code,pt.vendor_id,pp.barcode,pp.buying_price,pt.uom_id,pp.id """ % (data.partner_id.id,sql_group_1_ids,sql_group_2_ids,sql_group_3_ids)
				
				query_poline_ids = """
					SELECT l.product_id,l.product_qty,l.product_uom,l.price,l.discount,l.amount_total,l.name,t.group_1_id,t.group_2_id,t.group_3_id,
					p.barcode, p.default_code,p.category_uom_id from purchase_order_line as l inner join product_product p on p.id = l.product_id inner join product_template t on p.product_tmpl_id = t.id where l.order_id = %s 
					""" %( data.id,)

				query_soline_ids = """
					SELECT l.product_id,l.product_uom_qty,l.product_uom,l.price_unit,l.discount,l.price_total,l.name,t.group_1_id,t.group_2_id,t.group_3_id,
					p.barcode, p.default_code,p.category_uom_id from sale_order_line as l inner join product_product p on p.id = l.product_id inner join product_template t on p.product_tmpl_id = t.id where l.order_id = %s 
					""" %( data.id,)

				if self._context.get('from_pembelian'):
					product_ids = self.env.cr.execute(query_poline_ids)
					results = self.env.cr.fetchall()	

				elif self._context.get('from_penjualan'):
					product_ids = self.env.cr.execute(query_soline_ids)
					results = self.env.cr.fetchall()	
					

				else:
					product_ids = self.env.cr.execute(query_product_ids)
					results = self.env.cr.fetchall()				

			for rec in results:
				if self._context.get('from_pembelian'):
					line = (0,0, {	
						'product_id' : rec[0],
						'product_qty' : rec[1],
						'uom_id' : rec[2],
						'price': rec[3],
						'price_2': rec[3],
						'disc1':rec[4] or 0,
						'disc1_2':rec[4] or 0,
						'amount_total' : rec[5],
						'product_name': rec[6],
						'group_1_id': rec[7],
						'group_2_id': rec[8],
						'group_3_id': rec[9],
						'kode': rec[10],
						'barcode_ean': rec[11],
						'category_uom_id': rec[12],
						'name': rec[6],
						})
					filter_ids.append(line)
				elif self._context.get('from_penjualan'):
					line = (0,0, {	
						'product_id' : rec[0],
						'product_qty' : rec[1],
						'uom_id' : rec[2],
						'price': rec[3],
						'price_2': rec[3],
						'disc1':rec[4] or 0,
						'disc1_2':rec[4] or 0,
						'amount_total' : rec[5],
						'product_name': rec[6],
						'group_1_id': rec[7],
						'group_2_id': rec[8],
						'group_3_id': rec[9],
						'kode': rec[10],
						'barcode_ean': rec[11],
						'category_uom_id': rec[12],
						'name': rec[6],
						})
					filter_ids.append(line)
				else:
					line = (0,0, {
						'code' :rec[0],
						'barcode':rec[2],
						'price_unit':rec[3],
						'name':rec[4],
						'category_uom_id':rec[7],
						'uom_id': rec[5],
						'product_id' : rec[6]
						})
					filter_ids.append(line)
			
		if len(filter_ids) >= 1:
			if not self._context.get("nodefault"):
				res.update({
					'filter_ids' : filter_ids,
					'name' : data.partner_id.name,
					'date' : data.date_order,
					'warehouse_id' : data.warehouse_id.id,
					})
		else:
			raise ValidationError(_('Sorry, No Result Found.'))
			# raise UserError(_('Sorry, No Result Found'))
			# err_msg = _('Sorry, No Result Found.')
			# redir_msg = _('Go to UOM Categories')
			# raise RedirectWarning(err_msg, self.env.ref('gbr_custom.wizard_purchase_filter_view').id, redir_msg)
		return res

	def get_list_purchase(self):		
		active_ids = self._context.get('active_ids')
		if not active_ids:
			return res	

		purchase_line_obj = self.env['purchase.order.line']

		for data in self:
			for line in data.filter_ids:
				if line.product_qty > 0:
					purchase_line_obj.create({
						'product_id' : line.product_id.id,
						'default_code' : line.code,
						'barcode' : line.barcode,
						'name' :line.name,
						'product_qty' :line.product_qty,
						'price_unit' : line.price_unit,
						'price' : line.price_unit,
						'order_id' :active_ids[0],
						'date_planned' : data.date,
						'product_uom' : line.uom_id.id,
						'discount' : line.discount,
						'disc1' :line.disc1,
						'disc2' : line.disc2,
						'disc3': line.disc3,
						'amount_total' : line.amount_total,
						'note' : line.note,

						})
		return True

	def get_list_po(self):		
		active_ids = self._context.get('active_ids')
		if not active_ids:
			return res	

		account_line_obj = self.env['account.move.line']
		move = self.env['account.move'].search([('id','=',active_ids[0])])[0]
		for data in self:
			new_lines = self.env['account.move.line']
			for line in data.filter_ids:
				if line.is_confirm :					
					move.write({'invoice_line_ids': [(0, 0, {
				                'product_id'	: line.product_id.id,
				                'quantity'		: line.product_qty,
				                'discount_2' 	: line.disc1,
				                'discount'		: line.disc1,
				                'price_unit'	: line.price,
				                'product_uom_id': line.uom_id.id,
				                'name'			: line.product_id.name,
					            })],})				
		return True



	name = fields.Char('Name')
	date = fields.Date('Tanggal')
	warehouse_id = fields.Many2one('stock.warehouse', string="Gudang")
	filter_ids = fields.One2many('purchase.filter.line','filter_id', string="Filters")
	kode = fields.Char(string='Item Kode')
	barcode_ean = fields.Char(string='Item Kode (2)')
	item_nama = fields.Char(string='Item Nama')
	group_1_id = fields.Many2one('gbr.group.1', string="Item Group 1")
	group_2_id = fields.Many2one('gbr.group.2', string="Item Group 2")
	group_3_id = fields.Many2one('gbr.group.3', string="Item Group 3")
	# @api.multi
	def get_filter(self):
		self.ensure_one()
		self.name = "New name"
		purchase_filter_obj = self.env['purchase.filter.filter']
		self = self.with_context(nodefault=True)
		filter_id = purchase_filter_obj.create({'name': 'GBR Filter'})
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'purchase.filter.filter',
			'res_id': filter_id.id,
			'view_id': False,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	# def button_journal_entries(self):
	# 	return {
	# 		'name': _('Journal Entries'),
	# 		'view_mode': 'tree,form',
	# 		'res_model': 'account.move',
	# 		'view_id': False,
	# 		'type': 'ir.actions.act_window',
	# 		'domain': [('id', 'in', self.mapped('move_line_ids').mapped('move_id').ids)],
	# 		'context': {
	# 			'journal_id': self.journal_id.id,
	# 		}
	# 	}
		
class PurchaseFilterFilter(models.TransientModel):
	_name = 'purchase.filter.filter'
	_description = 'Purchase Filter filter'

	name = fields.Char('Name')
	group_1_ids = fields.Many2many('gbr.group.1', string="Group 1")
	group_2_ids = fields.Many2many('gbr.group.2', string="Group 2")
	group_3_ids = fields.Many2many('gbr.group.3', string="Group 3")

	def button_confirm(self):
		self.ensure_one()
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		ctx = self._context.copy()
		ctx.update(From_filter=True)
		group_1_ids = [x.id for x in self.group_1_ids]
		group_2_ids = [x.id for x in self.group_2_ids]
		group_3_ids = [x.id for x in self.group_3_ids]
		res = {}
		# ctx.update(group_1_ids=(group_1_ids ) )
		# ctx.update(group_2_ids=(group_2_ids ) )
		# ctx.update(group_3_ids=(group_3_ids ) )

		# print ('active_isdsss',active_ids,self._context)
		# self.name = "New name"
		# purchase_filter_obj = self.env['purchase.filter.filter']
		# filter_id = purchase_filter_obj.create({'name': 'GBR Filter'})
		filter_ids = []
		sql_group_1_ids = ''
		sql_group_2_ids = ''
		sql_group_3_ids = ''
		
		if len(group_1_ids) == 1:
			sql_group_1_ids = ' AND PT.group_1_id = '+str(group_1_ids[0]) +' '
		if len(group_1_ids) > 1:
			sql_group_1_ids = ' AND PT.group_1_id in '+str(tuple(group_1_ids) ) +' '

		if len(group_2_ids) == 1:
			sql_group_2_ids = ' AND PT.group_1_id = '+str(group_2_ids[0] )+' '
		if len(group_2_ids) > 1:
			sql_group_2_ids = ' AND PT.group_1_id in '+str(tuple(group_2_ids)) +' '

		if len(group_3_ids) == 1:
			sql_group_3_ids = ' AND PT.group_1_id = '+str(group_3_ids[0]) +' '
		if len(group_3_ids) > 1:
			sql_group_3_ids = ' AND PT.group_1_id in '+str(tuple(group_3_ids)) +' '

		purchase = self.env['purchase.order'].browse(active_ids)
		for data in purchase:
			if data.partner_id:
				query_product_ids = """ 
			SELECT pp.default_code,pt.vendor_id,pp.barcode,pp.buying_price,pt.name,pt.uom_id,pp.id,pp.category_uom_id from product_product pp 
			inner join product_template pt on pt.id = pp.product_tmpl_id 
			where pt.vendor_id= %s %s %s %s group by 
			pt.name,pp.default_code,pt.vendor_id,pp.barcode,pp.buying_price,pt.uom_id,pp.id """ % (data.partner_id.id,sql_group_1_ids,sql_group_2_ids,sql_group_3_ids)
				
				product_ids = self.env.cr.execute(query_product_ids)
				results = self.env.cr.fetchall()				

			for rec in results:
				line = (0,0, {
					'code' :rec[0],
					'barcode':rec[2],
					'price_unit':rec[3],
					'name':rec[4],
					'category_uom_id':rec[7],
					'uom_id': rec[5],
					'product_id' : rec[6]
					})
				filter_ids.append(line)
		
			if len(filter_ids) >= 1:			
				res.update({
					'filter_ids' : filter_ids,
					'name' : data.partner_id.name,
					'date' : data.date_order,
					'warehouse_id' : data.warehouse_id.id,
					})
		purchase_filter_obj = self.env['purchase.filter']
		filter_id = purchase_filter_obj.create(res)
		# create
		
		# return {
		#        "type": "ir.actions.do_nothing",
		#    }			
		return {
			'name': _('Filter'),
			'context': ctx,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'purchase.filter',
			'res_id': filter_id.id,
			'view_id': False,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	def button_batal(self):

		return {
			"type": "ir.actions.do_nothing",
		}

class WizardsFilterLine(models.TransientModel):
	_name = 'purchase.filter.line'
	_description = 'Purchase Filter'

	name = fields.Char('Nama')
	date_planned = fields.Date('Date Scheduled')
	filter_id = fields.Many2one('purchase.filter', string="Filter")
	product_id = fields.Many2one('product.product', string='Product')
	code = fields.Char('Code')
	barcode = fields.Char('Kode (2)')
	product_qty = fields.Integer('Order')
	category_uom_id = fields.Many2one('uom.category', string="Satuan Kategory 2")
	product_uom = fields.Many2one('uom.category', string="Satuan Kategory")
	uom_id = fields.Many2one('uom.uom', string="Satuan")
	price_unit = fields.Float('@Harga')
	
	price_total = fields.Float('Subtotal')
	disc1 = fields.Float('Disc%')
	disc1_2 = fields.Float('Disc% 2')
	disc2 = fields.Float('Disc-2%')
	disc3 = fields.Float('Disc-3%')
	discount = fields.Float('Discount')
	amount_total = fields.Float('Total')
	note = fields.Char('Catatan')
	group = fields.Many2one('gbr.group.1', string="Group")
	#====Pembelian=====
	is_confirm = fields.Boolean('Confirm')
	group_1_id = fields.Many2one('gbr.group.1', related='product_id.group_1_id',string="Group 1")
	group_2_id = fields.Many2one('gbr.group.2',related='product_id.group_2_id', string="Group 2")
	group_3_id = fields.Many2one('gbr.group.3',related='product_id.group_3_id', string="Group 3")
	kode = fields.Char(string='Kode',related='product_id.barcode')
	barcode_ean = fields.Char(string='Kode (3)',related='product_id.default_code')
	product_name  = fields.Char(string='Product Name',related='product_id.name')
	price =  fields.Float('Harga')
	price_2 = fields.Float('Harga 2')

	@api.onchange('product_qty','price_total','amount_total','discount','disc1','disc2','disc3')
	def get_product_pricetotal(self):
		if self._context.get('from_purchase'):			
			if self.product_qty == 0:
				self.price_total = 0
				self.amount_total = 0

			if self.product_qty > 0:
				self.price_total = self.price_unit * self.product_qty
				self.amount_total = self.price_unit * self.product_qty

			if self.discount > 0 or self.disc1 > 0 or self.disc2 > 0 or self.disc3 > 0:
				self.amount_total = self.price_total-(self.discount + self.disc1/100 * self.price_total + self.disc2/100*self.price_total + self.disc3/100 * self.price_total)

		return{}

	@api.onchange('product_qty')
	def get_price(self):
		if self._context.get('from_pembelian'):
			self.amount_total = (self.price * self.product_qty ) - (self.disc1 * self.price * 0.01 * self.product_qty)
		if self._context.get('from_purchase'):
			self.amount_total = (self.price * self.product_qty ) - (self.disc1 * self.price * 0.01 * self.product_qty)

	@api.onchange('uom_id')
	def _onchange_uom_id(self):
		if not self.product_id:
			return
		price_unit = 0		
		price = self.product_id.buying_price * self.product_id.uom_id.factor
		price_unit = price / self.uom_id.factor
		# 1000 / CTN 10 = 1000 * 0.1
		# 100 / pcs
		# price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
		self.price_unit = price_unit
		if self._context.get('from_purchase'):
			self.get_product_pricetotal()


	