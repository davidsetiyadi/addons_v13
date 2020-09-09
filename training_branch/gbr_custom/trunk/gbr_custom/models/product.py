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

KURS_JUAL = [('sale_rate', 'Kurs Jual *1'),('sale_rate_2','Kurs Jual *2'),('sale_rate_3', 'Kurs Jual *3'),('sale_rate_4', 'Kurs Jual *4'),('sale_rate_5','Kurs Jual *5')]

class ProductProduct(models.Model):
	_inherit = "product.product"
	_description = "Product"

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):	
			if len(domain) == 0:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(ProductProduct, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(ProductProduct, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	def _get_default_category_id(self):
		if self._context.get('categ_id') or self._context.get('default_categ_id'):
			return self._context.get('categ_id') or self._context.get('default_categ_id')
		category = self.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
		if not category:
			category = self.env['uom.category'].search([], limit=1)
		if category:
			return category.id
		else:
			err_msg = _('You must define at least one UOM category in order to be able to create products.')
			redir_msg = _('Go to UOM Categories')
			raise RedirectWarning(err_msg, self.env.ref('product.product_category_action_form').id, redir_msg)

	def _get_default_currency_id(self):
		if self._context.get('currency_id') or self._context.get('default_currency_id'):
			return self._context.get('currency_id') or self._context.get('default_currency_id')
		currency = self.env.ref('base.IDR', raise_if_not_found=False)
		if not currency:
			currency = self.env['res.currency'].search([('name','=','IDR')], limit=1)
		if currency:
			return currency.id
		else:
			err_msg = _('You must define at least one currency in order to be able to create products.')
			redir_msg = _('Go to currency')
			raise RedirectWarning(err_msg, self.env.ref('product.product_category_action_form').id, redir_msg)

	def _get_company_currency_id(self):
		for product in self:		
			# currency = self.env.ref('base.IDR', raise_if_not_found=False)
			# if not currency:
				# currency = self.env['res.currency'].search([('name','=','IDR')], limit=1)			
			product.update({
					'mu_id': self.env.company.currency_id.id				
				})	
		

	@api.depends('buying_price','sale_rate','currency_1_id')
	def _get_buying_price(self):
		for product in self:
			amount = 0.0
			# jika menggunakan currency default : harga - (harga * diskon)
			# jika menggunakan currency asing : harga  * nilai currency - (harga* nilai currency * diskon)
			date = self._context.get('date') or fields.Date.today()
			company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
			# the subquery selects the last rate before 'date' for the given currency/company
			if product.currency_1_id:
				currency_rates = product.currency_1_id._get_rates_buy(company, date)	
				# print ('currency_rates',currency_rates[product.currency_1_id.id])
				rate = currency_rates[product.currency_1_id.id]
				amount = product.buying_price * rate - (product.buying_price * rate * 0.01 * product.disc_buying_price)				

			product.update({
				'price_buy': self.env.company.currency_id.round(amount)				
			})	

	@api.depends('buying_price','sale_rate','currency_1_id')
	def _get_buying_price_2(self):
		for product in self:
			amount = 0.0
			# jika menggunakan currency default : harga - (harga * diskon)
			# jika menggunakan currency asing : harga  * nilai currency - (harga* nilai currency * diskon)
			date = self._context.get('date') or fields.Date.today()
			company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
			# the subquery selects the last rate before 'date' for the given currency/company
			if product.currency_1_id:
				# currency_rates = product.currency_1_id._get_rates_buy(company, date)	
				# print ('currency_rates',currency_rates[product.currency_1_id.id])
				rate = 1 #currency_rates[product.currency_1_id.id]
				amount = product.buying_price * rate - (product.buying_price * rate * 0.01 * product.disc_buying_price)				

			product.update({
				'price_buy_currencyless': self.env.company.currency_id.round(amount)				
			})	


	@api.depends('buying_price','sale_rate','currency_1_id')
	def _get_price_1(self):
		for product in self:
			amount = 0.0			
			sale_rate = product.sale_rate
			amount_1 = 0.0
			amount_2 = 0.0
			amount_3 = 0.0
			amount_4 = 0.0
			amount_5 = 0.0
			amount_6 = 0.0
			if product.currency_2_id:				
				amount_1 = (product.sale_price - (product.sale_price *	product.disc_sale_price * 0.01) ) * product.currency_2_id.sudo()[sale_rate]
			if product.currency_3_id:				
				amount_2 = (product.sale_price_2 - (product.sale_price_2 *	product.disc_sale_price_2 * 0.01) ) * product.currency_3_id.sudo()[sale_rate]
			if product.currency_4_id:				
				amount_3 = (product.sale_price_3 - (product.sale_price_3 *	product.disc_sale_price_3 * 0.01) ) * product.currency_4_id.sudo()[sale_rate]
			if product.currency_5_id:				
				amount_4 = (product.sale_price_4 - (product.sale_price_4 *	product.disc_sale_price_4 * 0.01) ) * product.currency_5_id.sudo()[sale_rate]
			if product.currency_6_id:				
				amount_5 = (product.sale_price_5 - (product.sale_price_5 *	product.disc_sale_price_5 * 0.01) ) * product.currency_6_id.sudo()[sale_rate]
			if product.currency_7_id:				
				amount_6 = product.sale_price_6 * product.currency_7_id.sudo()[sale_rate]
			
			# amount = product.sale_price - (product.sale_price *	product.disc_sale_price * 0.01)
			# amount = amount * currency_id.
			
			product.update({
				'price_1': self.env.company.currency_id.round(amount_1),	
				'price_2': self.env.company.currency_id.round(amount_2),
				'price_3': self.env.company.currency_id.round(amount_3),
				'price_4': self.env.company.currency_id.round(amount_4),
				'price_5': self.env.company.currency_id.round(amount_5),			
				'price_6': self.env.company.currency_id.round(amount_6),			
			})
			# print('ssssssssssssssssssssssssssssssssssssss',product.currency_2_id.sudo()[sale_rate])

		
		
	# harga	jumlah	satuan	terkecil
	# 10000	2	10	500
	# 5500	1	10	550
	# 			50
	# 			0,1

	@api.depends('buying_price','sale_rate','currency_1_id','sale_price')
	def _get_price_1_prcnt(self):
		for product in self:
			amount = 0.0
			amount_1 = 0.0
			amount_2 = 0.0
			amount_3 = 0.0
			amount_4 = 0.0
			amount_5 = 0.0
			amount_6 = 0.0
			
			price_per = product.per_price
			price_per2 = product.per_price_1
			price_per3 = product.per_price_2
			price_per4 = product.per_price_3
			price_per5 = product.per_price_4
			price_per6 = product.per_price_5
			price_per7 = product.per_price_6
			if product.per_price == 0:
				price_per = 1
			if product.per_price_1 == 0:
				price_per2 = 1
			if product.per_price_2 == 0:
				price_per3 = 1
			if product.per_price_3 == 0:
				price_per4 = 1
			if product.per_price_4 == 0:
				price_per5 = 1
			if product.per_price_5 == 0:
				price_per6 = 1
			if product.per_price_6 == 0:
				price_per7 = 1
			

			price_buy = product.price_buy * 1/price_per * product.uom_price_1_id.factor
			price_sale = product.price_1 * 1/price_per2 * product.uom_price_2_id.factor

			price_sale_2 = product.price_2 * 1/price_per3 * product.uom_price_3_id.factor
			price_sale_3 = product.price_3 * 1/price_per4 * product.uom_price_4_id.factor
			price_sale_4 = product.price_4 * 1/price_per5 * product.uom_price_5_id.factor
			price_sale_5 = product.price_5 * 1/price_per6 * product.uom_price_6_id.factor
			price_sale_6 = product.price_6 * 1/price_per7 * product.uom_price_7_id.factor

			if price_buy == 0:
				price_buy = 1
			amount = (price_sale - price_buy) / price_buy 
			amount_1 = (price_sale_2 - price_buy) / price_buy
			amount_2 = (price_sale_3 - price_buy) / price_buy
			amount_3 = (price_sale_4 - price_buy) / price_buy
			amount_4 = (price_sale_5 - price_buy) / price_buy
			amount_5 = (price_sale_6 - price_buy) / price_buy
			product.update({
				'price_1_prcnt': amount * 100	,
				'price_2_prcnt': amount_1 * 100,			
				'price_3_prcnt': amount_2 * 100,
				'price_4_prcnt': amount_3 * 100,
				'price_5_prcnt': amount_4 * 100,
				'price_6_prcnt': amount_5 * 100,
			})	


	
			
	category_uom_id = fields.Many2one('uom.category', string='Category UOM', default=_get_default_category_id,required='1')
	laporan_uom_id = fields.Many2one('uom.uom',string='Laporan UOM 1')
	laporan_uom_2_id = fields.Many2one('uom.uom',string='Laporan UOM 2')
	dec = fields.Float('Dec', digits='Product Price')
	is_input_expired = fields.Boolean('Input Expired')
	min_stock = fields.Float('Min Stock', digits='Product Price')
	min_stock_uom_id = fields.Many2one('uom.uom',string='Min Stock UOM')
	sat_eceran_uom_id = fields.Many2one('uom.uom',string='Satuan Eceran')
	sale_rate = fields.Selection(KURS_JUAL, string='Kurs Jual', required='1',default='sale_rate')
	buying_price = fields.Float('Harga Beli', digits='Product Price')
	sale_price = fields.Float('Harga Jual *1', digits='Product Price', default=0)
	sale_price_2 = fields.Float('Harga Jual *2', digits='Product Price')
	sale_price_3 = fields.Float('Harga Jual *3', digits='Product Price')
	sale_price_4 = fields.Float('Harga Jual *4', digits='Product Price')
	sale_price_5 = fields.Float('Harga Jual *5', digits='Product Price')
	sale_price_6 = fields.Float('Min Harga Jual', digits='Product Price')
	sale_price_prcnt = fields.Float('Harga Jual *1 %', digits='Product Price')
	sale_price_2_prcnt = fields.Float('Harga Jual *2 %', digits='Product Price')
	sale_price_3_prcnt = fields.Float('Harga Jual *3 %', digits='Product Price')
	sale_price_4_prcnt = fields.Float('Harga Jual *4 %', digits='Product Price')
	sale_price_5_prcnt = fields.Float('Harga Jual *5 %', digits='Product Price')
	sale_price_6_prcnt = fields.Float('Min Harga Jual %', digits='Product Price')
	uom_price_1_id = fields.Many2one('uom.uom',string='UOM 1')
	uom_price_2_id = fields.Many2one('uom.uom',string='UOM 2')
	uom_price_3_id = fields.Many2one('uom.uom',string='UOM 3')
	uom_price_4_id = fields.Many2one('uom.uom',string='UOM 4')
	uom_price_5_id = fields.Many2one('uom.uom',string='UOM 5')
	uom_price_6_id = fields.Many2one('uom.uom',string='UOM 6')
	uom_price_7_id = fields.Many2one('uom.uom',string='UOM 7')
	currency_1_id = fields.Many2one('res.currency',string='Cur 1',default=_get_default_currency_id)
	currency_2_id = fields.Many2one('res.currency',string='Cur 2',default=_get_default_currency_id)
	currency_3_id = fields.Many2one('res.currency',string='Cur 3',default=_get_default_currency_id)
	currency_4_id = fields.Many2one('res.currency',string='Cur 4',default=_get_default_currency_id)
	currency_5_id = fields.Many2one('res.currency',string='Cur 5',default=_get_default_currency_id)
	currency_6_id = fields.Many2one('res.currency',string='Cur 6',default=_get_default_currency_id)
	currency_7_id = fields.Many2one('res.currency',string='Cur 7',default=_get_default_currency_id)
	per_price = fields.Float('Per Buy', digits='Product Per')
	per_price_1 = fields.Float('Per *1', digits='Product Per')
	per_price_2 = fields.Float('Per *2', digits='Product Per')
	per_price_3 = fields.Float('Per *3', digits='Product Per')
	per_price_4 = fields.Float('Per *4', digits='Product Per')
	per_price_5 = fields.Float('Per *5', digits='Product Per')
	per_price_6 = fields.Float('Per *6', digits='Product Per')
	disc_buying_price = fields.Float('Disc Harga Beli', digits='Product Price', default=0)
	disc_sale_price = fields.Float('Disc Harga Jual *1', digits='Product Price', default=0)
	disc_sale_price_2 = fields.Float('Disc Harga Jual *2', digits='Product Price', default=0)
	disc_sale_price_3 = fields.Float('Disc Harga Jual *3', digits='Product Price', default=0)
	disc_sale_price_4 = fields.Float('Disc Harga Jual *4', digits='Product Price', default=0)
	disc_sale_price_5 = fields.Float('Disc Harga Jual *5', digits='Product Price', default=0)
	price_1_prcnt = fields.Float('*1 %', digits='Product Price',readonly=True, compute='_get_price_1_prcnt')
	price_2_prcnt = fields.Float('*2 %', digits='Product Price',readonly=True, compute='_get_price_1_prcnt')
	price_3_prcnt = fields.Float('*3 %', digits='Product Price',readonly=True, compute='_get_price_1_prcnt')
	price_4_prcnt = fields.Float('*4 %', digits='Product Price',readonly=True, compute='_get_price_1_prcnt')
	price_5_prcnt = fields.Float('*5 %', digits='Product Price',readonly=True, compute='_get_price_1_prcnt')
	price_6_prcnt = fields.Float('Harga Jual %', digits='Product Price',readonly=True, compute='_get_price_1_prcnt')
	price_buy = fields.Monetary(string='Nilai beli', digits='Product Price',readonly=True, compute='_get_buying_price', tracking=True)
	price_buy_currencyless = fields.Monetary(string='Nilai beli 2', digits='Product Price',readonly=True, compute='_get_buying_price_2', tracking=True)
	# amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)

	price_1 = fields.Monetary('Nilai *1', digits='Product Price',readonly=True, compute='_get_price_1')
	price_2 = fields.Monetary('Nilai *2', digits='Product Price',readonly=True, compute='_get_price_1')
	price_3 = fields.Monetary('Nilai *3', digits='Product Price',readonly=True, compute='_get_price_1')
	price_4 = fields.Monetary('Nilai *4', digits='Product Price',readonly=True, compute='_get_price_1')
	price_5 = fields.Monetary('Nilai *5', digits='Product Price',readonly=True, compute='_get_price_1')
	price_6 = fields.Monetary('Nilai min h Jual', digits='Product Price',readonly=True, compute='_get_price_1')
	keterangan = fields.Char('KETERANGAN')
	mu = fields.Char('MU 2')
	mu_id = fields.Many2one('res.currency',string='MU',compute=_get_company_currency_id)
	harga_char = fields.Char('HARGA')
	set_percent = fields.Char('SET %')
	per_char =fields.Char('PER')
	sat_char = fields.Char('SAT')
	disc_char = fields.Char('DISC %')
	percent = fields.Char('%')
	nilai_idr = fields.Char('NILAI IDR')
	vendor_id = fields.Many2one('res.partner','Vendor', related='product_tmpl_id.vendor_id', readonly=False)
	group_1_id = fields.Many2one('gbr.group.1','Group 1', related='product_tmpl_id.group_1_id', readonly=False,store=True)
	group_2_id = fields.Many2one('gbr.group.2','Group 2', related='product_tmpl_id.group_2_id', readonly=False,store=True)
	group_3_id = fields.Many2one('gbr.group.3','Group 3', related='product_tmpl_id.group_3_id', readonly=False,store=True)
	group_ii_id = fields.Many2one('gbr.group.ii','Group ii', related='product_tmpl_id.group_ii_id', readonly=False,store=True)
	is_user_set_po = fields.Boolean('Purchase Order',default=True)
	is_user_set_pem = fields.Boolean('Pembelian/ Input Stock Awal',default=True)
	is_user_set_retur_pem = fields.Boolean('Retur Pembelian',default=True)
	is_user_set_quotation = fields.Boolean('Quotation',default=True)
	is_user_set_so = fields.Boolean('Sales Order',default=True)
	is_user_set_penj_ecrn = fields.Boolean('Penjualan Eceran',default=True)
	is_user_set_penj = fields.Boolean('Penjualan',default=True)
	is_user_set_r_penj = fields.Boolean('Retur Penjualan',default=True)
	is_user_set_b_p_gdg = fields.Boolean('Barang Pindah Gudang' ,default=True)
	is_user_set_b_tf = fields.Boolean('Barang Transfer/Untransfer',default=True)
	is_user_set_b_msk = fields.Boolean('Barang Masuk Lainnya',default=True)
	is_user_set_b_klr = fields.Boolean('Barang Keluar Lainnya' ,default=True)
	is_user_set_non_tax = fields.Boolean('Non Taxable/Tanpa Pajak')
	is_user_set_hj_manual = fields.Boolean('POS: Harga Jual Boleh Diisi Manual')
	is_user_set_p_no_disc_glbl = fields.Boolean('POS: Tidak DIhitung dalam diskon global')
	is_user_set_p_no_charge = fields.Boolean('POS: Tidak Dihitung dalam Charges Pembayaran non Tunai')
	is_user_set_item_bnus = fields.Boolean('POS: Penjualan Sebagai Item Bonus')
	is_user_set_cttn_penj_item = fields.Boolean('POS: Pengisian Catatan Penjualan Item')
	is_user_set_no_otorisasi = fields.Boolean('Tanpa Otorisasi untuk harga jual dibawah minimum')
	is_user_set_can_be_minus = fields.Boolean('Boleh Penjualan Stock Minus')
	is_user_set_except_barcode = fields.Boolean('Diperkecualikan Saat cetak barcode')
	is_user_set_not_sp_disc = fields.Boolean('Tidak berlaku untuk special diskon')
	is_user_set_not_item_bnus = fields.Boolean('Tidak Berlaku untuk item bonus Penjualan')
	is_user_set_not_hj = fields.Boolean('Hiraukan setting/pilihan Harga Jual Pada Pelanggan')
	is_user_set_incl_ppk = fields.Boolean('Harga Beli sudah termasuk ppk')
	is_user_set_incl_ppn = fields.Boolean('Harga Beli Sudah Termasuk PPN')
	history_sales =  fields.Char(string='History Sales')
	harga_baru = fields.Char(string='Harga Baru')
	#history_sales =  fields.Char(string='History Sales', compute="_compute_history_sales")
	#harga_baru = fields.Char(string='Harga Baru', compute="_compute_history_sales")
	gbr_pricelist = fields.Char(string='Price List')
	is_noted = fields.Boolean('Is Catatan')
	noted = fields.Char('List Catatan')
	memo1 = fields.Text('Memo')
	memo2 = fields.Text("Memo 2")
	memo3 = fields.Text('Memo 3')
	memo4 = fields.Text("Memo 4")
	persediaan_id = fields.Many2one('account.account', 'Persediaan')
	pemb_cash_id= fields.Many2one('account.account', 'Pembelian Cash')
	pemb_cash_disc_id = fields.Many2one('account.account', 'Pembelian Cash [Discount]')
	pemb_cash_ppn_id = fields.Many2one('account.account', 'Pembelian Cash [Tax PPN}')
	pemb_cred_id = fields.Many2one('account.account', 'Pembelian Credit')
	pemb_cred_disc_id= fields.Many2one('account.account', 'Pembelian Credit [Discount]')
	pemb_cred_tax_id = fields.Many2one('account.account', 'Pembelian Credit [Tax PPN]')
	rtr_pemb_cash_id= fields.Many2one('account.account', 'Retur Pembelian Cash')
	rtr_pemb_cash_disc_id= fields.Many2one('account.account', 'Retur Pembelian Cash [Discount]')
	rtr_pemb_cash_tax_id= fields.Many2one('account.account', 'Retur Pembelian Cash [Tax PPN]')
	rtr_pemb_cred_id= fields.Many2one('account.account', 'Retur Pembelian Credit')
	rtr_pemb_cred_disc_id= fields.Many2one('account.account', 'Retur Pembelian Credit [Discount]')
	rtr_pemb_cred_tax_id= fields.Many2one('account.account', 'Retur Pembelian Credit [Tax PPN]')
	debit_not_hut_pemb_id = fields.Many2one('account.account', 'Debit Note Hutang Pembelian')
	credit_not_hut_pemb_id = fields.Many2one('account.account', 'Credit Note Hutang Pembelian')
	penj_ecrn_id = fields.Many2one('account.account', 'Account Penjualan Eceran')
	penj_ecrn_disc_id= fields.Many2one('account.account', 'Penjualan Eceran [Discount]')
	penj_ecrn_tax_id= fields.Many2one('account.account', 'Penjualan Eceran [Tax PPn]')
	ret_penj_ecrn_id= fields.Many2one('account.account', '[Retur Tukar tambah] Penjualan Eceran')
	ret_penj_ecrn_dis_id = fields.Many2one('account.account', '[Retur Tukar tambah] Penjualan Eceran [Discount]')
	ret_penj_ecrn_tax_id= fields.Many2one('account.account', '[Retur Tukar tambah] Penjualan Eceran [Tax PPn]')
	penj_cash_id = fields.Many2one('account.account', 'Penjualan Cash')
	penj_cash_disc_id= fields.Many2one('account.account', 'Penjualan Cash [Discount]')
	penj_cash_tax_id = fields.Many2one('account.account', 'Penjualan Cash [Tax-PPn]')
	penj_credit_id = fields.Many2one('account.account', 'Penjualan Credit')
	penj_credit_disc_id= fields.Many2one('account.account', 'Penjualan Credit [Discount]')
	penj_credit_tax_id= fields.Many2one('account.account', 'Penjualan Credit [Tax-PPn]')
	ret_penj_cash_id= fields.Many2one('account.account', 'Retur Penjualan Cash')
	ret_penj_cash_disc_id= fields.Many2one('account.account', 'Retur Penjualan Cash [Discount]')
	ret_penj_cash_tax_id = fields.Many2one('account.account', 'Retur Penjualan Cash [Tax-PPn]')
	ret_penj_cash_hpp_id= fields.Many2one('account.account', 'Retur Penjualan Cash [Item Rusak - HPP]')
	ret_penj_cash_cost_id= fields.Many2one('account.account', 'Retur Penjualan Cash [Item Rusak - Cost]')
	ret_penj_credit_id= fields.Many2one('account.account', 'Retur Penjualan Credit')
	ret_penj_credit_disc_id= fields.Many2one('account.account', 'Retur Penjualan Credit [Discount]')
	ret_penj_credit_tax_id= fields.Many2one('account.account', 'Retur Penjualan Credit [Tax-PPn]')
	ret_penj_credit_hpp_id= fields.Many2one('account.account', 'Retur Penjualan Credit [Item Rusak - HPP]')
	ret_penj_credit_cost_id= fields.Many2one('account.account', 'Retur Penjualan Credit [Item Rusak - Cost]')
	deb_not_piutang_penj_id= fields.Many2one('account.account', 'Debit Note Piutang Penjualan')
	cred_not_piutang_penj_id= fields.Many2one('account.account', 'Credit Note Piutang Penjualan')
	nama_alias_ids = fields.One2many('gbr.nama.alias', 'product_id', string='Nama Alias')
	penjualan_product_qty = fields.Float(compute='_compute_penjualan_product_qty', string='Penjualan Qty')
	panjang = fields.Float('Panjang')
	lebar = fields.Float('Lebar')
	tinggi = fields.Float('Tinggi')
	kubikasi_uom_id = fields.Many2one('uom.uom',string='Kubikasi UOM')
	total_kubikasi = fields.Float('Total Kubikasi' ,compute='_compute_kubikasi')							
	is_semua_data = fields.Boolean(string='Semua Data',default=True)


	@api.onchange('panjang', 'lebar', 'tinggi')
	def onchange_p_l_t(self):
		self.volume = float(self.panjang if self.panjang else 0) * float(self.lebar if self.lebar else 0) * float(
			self.tinggi if self.tinggi else 0)
		self.total_kubikasi = self.volume

	def _compute_kubikasi(self):
		
		for product in self:
			kubikasi = product.volume

			product.total_kubikasi = kubikasi

	def _compute_penjualan_product_qty(self):
		date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
		move = self.env['account.move']
		partner =  self.env['res.partner']
		moveline = self.env['account.move.line']
		move_ids = move.search([('state','not in',('cancel','draft'))#,
			#('type', '=', 'out_receipt')
			,'|',('is_penjualan','=',True),('is_penj_eceran','=',True)
			])		
		moves_ids = [x.id for x in move_ids]
		for product in self:
			quantity = 0
			if moves_ids:
				move_line_ids = moveline.search([('move_id','in',moves_ids ),
					('product_id','=',product.id)],order="id desc")					
				for moveline in move_line_ids:
					quantity += moveline.quantity / moveline.product_uom_id.factor * product.uom_id.factor

			product.penjualan_product_qty = quantity

	def action_view_penjualan(self):
		# return True
		# Product bisa Smart Button ke Sales Order (Dan bisa group by kategori pelanggan)

		action = self.env.ref('gbr_custom.action_penjualan_report_all').read()[0]

		action['domain'] = ['&','&', ('state', '=', 'posted'), ('product_id', 'in', self.ids),'|',('is_penj_eceran','=',True),('is_penjualan','=',True)]
		action['context'] = {
			'search_default_last_year_purchase': 1,
			'search_default_kategori': 1, 'search_default_order_month': 1,
			'graph_measure': 'quantity'
		}
		return action

	def _compute_history_sales(self):
		history_sales = 'history_sales'
		harga_baru = 'harga baru'
		for product in self:
			
			today = fields.Date.today()
			# first = today.replace(day=1)
			first = today - datetime.timedelta(days=0)
			lastMonth = first - datetime.timedelta(days=30)
			# print(lastMonth.strftime("%Y%m"),'sssss',lastMonth)
			quantity = 0
			quantity_k = 0
			quantity_lk = 0
			move = self.env['account.move']
			partner =  self.env['res.partner']
			moveline = self.env['account.move.line']
			move_ids = move.search([('state','not in',('cancel','draft')),
				('type', '=', 'out_receipt'),('invoice_date','>=',lastMonth),('invoice_date','<=',first)
				,'|',('is_penjualan','=',True),('is_penj_eceran','=',True)
				])				
			moves_ids = [x.id for x in move_ids]
			if moves_ids:
				move_line_ids = moveline.search([('move_id','in',moves_ids ),
					('product_id','=',product.id)],order="id desc")					
				for moveline in move_line_ids:
					quantity += moveline.quantity / moveline.product_uom_id.factor * product.uom_id.factor
					
			#LK luar kerpi
			#K kepri
			partner_idk = partner.search([('is_customer','=',True),('state_id.code','=','08')])
			partner_ldk = partner.search([('is_customer','=',True),'|',('state_id.code','!=','08'),('state_id','=',False)])
			
			kepri_partner_ids = [x.id for x in partner_idk]
			lk_partner_ids = [x.id for x in partner_ldk]

			if kepri_partner_ids:
				kepri_move_ids = move.search([('state','not in',('cancel','draft')),
				('type', '=', 'out_receipt'),('partner_id','in',kepri_partner_ids)
				,'|',('is_penjualan','=',True),('is_penj_eceran','=',True)])
				kepri_move_ids = [x.id for x in kepri_move_ids]
				if kepri_move_ids:
					kepri_move_line_ids = moveline.search([('move_id','in',kepri_move_ids ),
					('product_id','=',product.id)],order="id desc")
					for moveline in kepri_move_line_ids:
						quantity_k += moveline.quantity / moveline.product_uom_id.factor * product.uom_id.factor

			if lk_partner_ids:
				lk_move_ids = move.search([('state','not in',('cancel','draft')),
				('type', '=', 'out_receipt'),('partner_id','in',lk_partner_ids)
				,'|',('is_penjualan','=',True),('is_penj_eceran','=',True)])
				lk_move_ids = [x.id for x in lk_move_ids]
				if lk_move_ids:
					lk_move_line_ids = moveline.search([('move_id','in',lk_move_ids ),
					('product_id','=',product.id)],order="id desc")
					for moveline in lk_move_line_ids:
						quantity_lk += moveline.quantity / moveline.product_uom_id.factor * product.uom_id.factor

			# harga uom LK3 , k36475
			# nomor 1 & 2 itu kita sendiri isi manual punya (sebagai histori penjualan),
			# K = qty pelanggan kepri
			# LK = qty pelanggan luar kepri
			# quantity from account_move_line, qty * product uom / uom default
			# 10 CTN(10) =    100 pcs 
			# 10 / 0.1 = 100 * factor
			# type penjualan

			product.history_sales = str(quantity)+' '+str(product.uom_id.name)
			product.harga_baru = str(quantity_lk)+' '+str(product.uom_id.name)+' LK || K'+str(quantity_k)

	@api.onchange('buying_price','per_price','uom_price_1_id','disc_buying_price')
	def onchange_buying_price(self):	
		# if self.env.context.get("noonchange"):
			# self.sale_price_prcnt = 0
		amount_1 = 0.0
		amount_2 = 0.0
		amount_3 = 0.0
		amount_4 = 0.0
		amount_5 = 0.0
		amount_6 = 0.0
		price_per = self.per_price		
		if self.per_price == 0:
			price_per = 1

		price_buy = self.price_buy_currencyless * 1/price_per * self.uom_price_1_id.factor		
		if price_buy == 0:
			price_buy = 1
		if self.sale_price_prcnt != 0:
			amount_1 = ((price_buy / self.uom_price_2_id.factor) + (price_buy / self.uom_price_2_id.factor * self.sale_price_prcnt * 0.01) )* self.per_price_1
			self.sale_price = amount_1

		if self.sale_price_2_prcnt != 0:
			amount_2 = ((price_buy / self.uom_price_3_id.factor) + (price_buy / self.uom_price_3_id.factor * self.sale_price_2_prcnt * 0.01) )* self.per_price_2
			self.sale_price_2 = amount_2

		if self.sale_price_3_prcnt != 0:
			amount_3 = ((price_buy / self.uom_price_4_id.factor) + (price_buy / self.uom_price_4_id.factor * self.sale_price_3_prcnt * 0.01) )* self.per_price_3
			self.sale_price_3 = amount_3

		if self.sale_price_4_prcnt != 0:
			amount_4 = ((price_buy / self.uom_price_5_id.factor) + (price_buy / self.uom_price_5_id.factor * self.sale_price_4_prcnt * 0.01) )* self.per_price_4
			self.sale_price_4 = amount_4

		if self.sale_price_5_prcnt != 0:
			amount_5 = ((price_buy / self.uom_price_6_id.factor) + (price_buy / self.uom_price_6_id.factor * self.sale_price_5_prcnt * 0.01) )* self.per_price_5
			self.sale_price_5 = amount_5

		if self.sale_price_6_prcnt != 0:
			amount_6 = ((price_buy / self.uom_price_7_id.factor) + (price_buy / self.uom_price_7_id.factor * self.sale_price_6_prcnt * 0.01) )* self.per_price_6
			self.sale_price_6 = amount_6

		return {}

	# kalau currency di ubah yang tidak nol ikut berubah.
	# harga nilai tanpa currency.

	@api.onchange('sale_price_prcnt')
	def onchange_per_price_1(self):		
		self = self.with_context(noonchange=True)
		self.currency_2_id = self.currency_1_id
		self.uom_price_2_id = self.uom_price_1_id
		self.per_price_1 = self.per_price
		if self.sale_price_prcnt != 0:
			self.sale_price = self.price_buy_currencyless + (self.price_buy_currencyless * self.sale_price_prcnt * 0.01)
		# self.with_context(noonchange=True).sale_price = self.price_buy + (self.price_buy * self.sale_price_prcnt * 0.01)
		# kalau nol jangan di onchange ke price buy      
		return {}

	@api.onchange('currency_1_id')
	def onchange_currency_1_id(self):		
		if self.sale_price_prcnt != 0:
			self.currency_2_id = self.currency_1_id
		if self.sale_price_2_prcnt != 0:
			self.currency_3_id = self.currency_1_id

		if self.sale_price_3_prcnt != 0:
			self.currency_4_id = self.currency_1_id

		if self.sale_price_4_prcnt != 0:
			self.currency_5_id = self.currency_1_id

		if self.sale_price_5_prcnt != 0:
			self.currency_6_id = self.currency_1_id

		if self.sale_price_6_prcnt != 0:
			self.currency_7_id = self.currency_1_id
		return {}

	@api.onchange('sale_price','currency_2_id')
	def onchange_sale_price(self):		
		if self.env.context.get("noonchange"):
			self.sale_price_prcnt = 0
		return {}

	@api.onchange('per_price','per_price_1')
	def onchange_per_price_1_id(self):		
		price_per = self.per_price		
		if self.per_price == 0:
			price_per = 1
		
		price_buy = self.price_buy_currencyless * 1/price_per * self.uom_price_1_id.factor		
		if price_buy == 0:
			price_buy = 1
		
		if self.sale_price_prcnt != 0:
			amount = ((price_buy / self.uom_price_2_id.factor) + (price_buy / self.uom_price_2_id.factor * self.sale_price_prcnt * 0.01) )* self.per_price_1
			self.sale_price = amount

		return {}
	 

class ProductTemplate(models.Model):
	_inherit = "product.template"
	_description = "Product"

	sale_rate = fields.Selection(KURS_JUAL, string='Kurs Jual', default='sale_rate')
	seller_id = fields.Many2one('product.supplierinfo', 'Vendor 2', compute='_compute_product_vendor_id')
	vendor_id = fields.Many2one('res.partner', 'Vendor')
	group_1_id = fields.Many2one('gbr.group.1', 'Group 1')
	group_2_id = fields.Many2one('gbr.group.2', 'Group 2')
	group_3_id = fields.Many2one('gbr.group.3', 'Group 3')
	group_ii_id = fields.Many2one('gbr.group.ii', 'Group ii')

	@api.depends('seller_ids')
	def _compute_product_vendor_id(self):
		for p in self:
			p.seller_id = p.seller_ids[:1].id

class GbrNamaAlias(models.Model):
	_name = "gbr.nama.alias"
	_description = "Nama Alias"

	name = fields.Char('Name')
	product_id = fields.Many2one('product.product',string='Product')

class GbrGroup1(models.Model):
	_name = "gbr.group.1"
	_description = "Group 1"

	name = fields.Char('Name')
	group_id = fields.Many2one('gbr.group.99' , 'Group Master Item')

class GbrGroup2(models.Model):
	_name = "gbr.group.2"
	_description = "Group 2"

	name = fields.Char('Name')
	group_id = fields.Many2one('gbr.group.99' , 'Group Master item')
		
class GbrGroup3(models.Model):
	_name = "gbr.group.3"
	_description = "Group 3"

	name = fields.Char('Name')
	group_id = fields.Many2one('gbr.group.99' , 'Group Master Item')

class GbrGroupii(models.Model):
	_name = "gbr.group.ii"
	_description = "Group ii"

	name = fields.Char('Name')	
	group_id = fields.Many2one('gbr.group.99' , 'Group Master Item')


class GbrGroup4(models.Model):
	_name = "gbr.group.4"
	_description = "Grouping Vendor"

	name = fields.Char('Name')
	type = fields.Char('Type')
	group_id = fields.Many2one('gbr.group.4a' , 'Kelompok 1')
	group2_id = fields.Many2one('gbr.group.4a' , 'Kelompok 2')
	group3_id = fields.Many2one('gbr.group.4a' , 'Grouping 1')
	group4_id = fields.Many2one('gbr.group.4a' , 'Grouping 2')
	group5_id = fields.Many2one('gbr.group.4a' , 'Grouping 3')

class GbrGroup4a(models.Model):
	_name = "gbr.group.4a"
	_inherit = ['mail.thread', 'mail.activity.mixin']  
	_description = "Grouping Master Vendor"


	name = fields.Char('Name')
	type = fields.Char('Type')
	group_1_ids = fields.One2many('gbr.group.4' , 'group_id','Kelompok 1')
	group_2_ids = fields.One2many('gbr.group.4' , 'group2_id','Kelompok 2')
	group_3_ids = fields.One2many('gbr.group.4' , 'group3_id','Grouping 1')
	group_4_ids = fields.One2many('gbr.group.4' , 'group4_id','Grouping 2')
	group_5_ids = fields.One2many('gbr.group.4' , 'group5_id','Grouping 3')
	group_7_ids = fields.One2many('gbr.group.7' , 'group_cust_id','Kelompok *1')
	group_8_ids = fields.One2many('gbr.group.8' , 'group_cust_2_id','Kelompok *2')

class GbrGroup5(models.Model):
	_name = "gbr.group.5"
	_description = "Group Level"

	name = fields.Char('Name')

class GbrGroup6(models.Model):
	_name = "gbr.group.6"
	_description = "Group user"

	name = fields.Char('Name')

class GbrGroup7(models.Model):
	_name = "gbr.group.7"
	_description = "Kelompok Pelanggan 1"

	name = fields.Char('Name')
	group_cust_id = fields.Many2one('gbr.group.4a' , 'Kelompok 1')

class GbrGroup8(models.Model):
	_name = "gbr.group.8"
	_description = "Kelompok Pelanggan 2"

	name = fields.Char('Name')
	group_cust_2_id = fields.Many2one('gbr.group.4a' , 'Kelompok 2')

class GbrGroup99(models.Model):
	_name = "gbr.group.99"
	_inherit = ['mail.thread', 'mail.activity.mixin']  
	_description = "Grouping Master"


	name = fields.Char('Name')
	type = fields.Char('Type')
	group_1_ids = fields.One2many('gbr.group.1' , 'group_id','Groups 1')
	group_2_ids = fields.One2many('gbr.group.2' , 'group_id','Groups 2')
	group_3_ids = fields.One2many('gbr.group.3' , 'group_id','Groups 3')
	group_4_ids = fields.One2many('gbr.group.ii' , 'group_id','Groups 4')


class GbrPoNumber(models.Model):
	_name = "gbr.po.number"
	_description = "GBR Purchase Order"

	name = fields.Char('Name')