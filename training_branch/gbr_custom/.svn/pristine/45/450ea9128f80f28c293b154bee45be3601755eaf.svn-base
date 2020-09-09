import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form
import locale



class GbrJournalKhusus(models.TransientModel):
	_name = 'gbr.journal.khusus'
	_description = 'GBR Journal Khusus'

	date = fields.Date(string='Tanggal', default=fields.Date.context_today, required=True)
	date_end = fields.Date(string='Tanggal 2', default=fields.Date.context_today, required=True)
	j_pemb = fields.Boolean(string='Jurnal Pembelian') 
	j_rtr_pemb = fields.Boolean(string='Jurnal Retur Pembelian') 
	j_dn_cn_hut_pemb = fields.Boolean(string='Jurnal Debit Note/Credit Note Hutang Pembelian') 
	j_dp_pembelian = fields.Boolean(string='Jurnal Deposit Pemelian')
	j_pemb_hutang = fields.Boolean(string='Jurnal Pembayaran Hutang')
	j_pnj =fields.Boolean(string='Jurnal Penjualan')
	j_rtr_penj =fields.Boolean(string='Jurnal Retur Penjualan')
	j_dn_cn_ptg_penj =fields.Boolean(string='Jurnal Debit/Credit Note Piutang Penjualan')
	j_dp_penj = fields.Boolean(string='Jurnal Deposit Penjualan')
	j_inv_statement =fields.Boolean(string='Jurnal Invoice Penjualan')
	j_pen_piutang = fields.Boolean(string='Jurnal Penerimaan Piutang')
	j_kas_msk = fields.Boolean(string='Jurnal Kas Masuk')
	j_kas_klr =fields.Boolean(string='Jurnal Kas Keluar')
	j_trns_kas = fields.Boolean(string='Jurnal Transfer Kas')


	def button_process_journal(self):
		#Semua debit/credit akan di sesuaikan dengan settingan yang baru.
		# misalnya sebelum nya pakai Pembayaran cash , ketika ganti akun 
		# maka transaksi yang sudah di create akan di ganti
		partner_obj = self.env['res.partner']
		category_obj = self.env['product.category']
		account_move_obj = self.env['account.move']
		if self.j_pemb: #Jurnal Pembelian
			#Journal item pada module pembelian akan di reset.
			# debit Harga pokok Penjualan >> dari product dan category
			# Update account harga pokok pembelian kategory
			self._cr.execute('''SELECT pt.categ_id from account_move_line aml inner join account_move am 
				on am.id = aml.move_id inner join product_product pp on pp.id = aml.product_id inner join 
				product_template pt on pt.id = pp.product_tmpl_id  WHERE am.type = 'in_invoice' and am.is_pembelian = true 
				and am.DATE between %s and %s group by pt.categ_id''',(self.date , self.date_end))
			for category in self._cr.fetchall():
				if category[0]:
					categorys = category_obj.browse(category[0])
					debit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id inner join 
						product_product pp on pp.id = aml.product_id inner join product_template pt on pt.id = pp.product_tmpl_id where  
						aml.debit > 0 and am.type = 'in_invoice' and am.is_pembelian = true and pt.categ_id = %s and 
						am.date between %s and %s )'''
					self._cr.execute(debit_sql, (categorys.property_account_expense_categ_id.id,category[0],self.date , self.date_end))	
					self._cr.commit()

			# Update account harga pokok pembelian per Item/
			# property_account_income_id
			
			self._cr.execute('''SELECT (SELECT value_reference FROM ir_property
				WHERE name IN ('property_account_expense_id','property_account_expense_id') AND res_id = CONCAT('product.template,',pt.id)) AS income_id ,
				aml.product_id FROM product_template pt INNER JOIN product_product pp ON pt.id = pp.product_tmpl_id inner join account_move_line aml on 
				aml.product_id = pp.id inner join account_move am on am.id = aml.move_id where aml.debit > 0 and am.type = 'in_invoice' and am.is_pembelian = true 
				and am.date between %s and %s
				group by aml.product_id, pt.id having (SELECT value_reference FROM ir_property
				WHERE name IN ('property_account_expense_id','property_account_expense_id') AND res_id = CONCAT('product.template,',pt.id)) 
				is not null ''',(self.date , self.date_end))
			for expense_id,product_id in self._cr.fetchall():	
				credit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.debit > 0 and am.type = 'in_invoice' and am.is_pembelian = true and aml.product_id = %s 
						and am.date between %s and %s )'''
				
				self._cr.execute(credit_sql, ( int(expense_id[16:]),product_id,self.date , self.date_end))	
				self._cr.commit()

			# looping dari vendor.			
			self._cr.execute('''SELECT partner_id from account_move where type = 'in_invoice' and 
							is_pembelian = true and DATE between %s and %s group by partner_id ''',(self.date , self.date_end) )
			for partner in self._cr.fetchall():
				if partner[0]:
					partners = partner_obj.browse(partner[0])
					credit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.credit > 0 and am.type = 'in_invoice' and am.is_pembelian = true and am.partner_id = %s 
						and am.date between %s and %s )'''

					self._cr.execute(credit_sql, (partners.property_account_payable_id.id,partner[0],self.date , self.date_end))	
					self._cr.commit()

		# 	UPDATE stock_move as q set price_unit = 

		# 	(
		# 		select (SELECT value_reference FROM ir_property
		# 		WHERE name IN ('property_account_receivable_id','property_account_receivable_id') AND res_id = CONCAT('	res.partner,',rp.id)) AS receivable_id 
		# 		FROM res_partner rp INNER JOIN account_move am ON am.partner_id = rp.id) 
		# 		where q.product_id = %s 
		# 		,(product_id,) )			
	
		if self.j_rtr_pemb: #Jurnal Retur Pembelian
			# credit ke retur pembelian IDF

			# debit hutang usaha
			# credit retur pembelian idr
			self._cr.execute('''SELECT pt.categ_id from account_move_line aml inner join account_move am 
				on am.id = aml.move_id inner join product_product pp on pp.id = aml.product_id inner join 
				product_template pt on pt.id = pp.product_tmpl_id  WHERE am.type = 'in_invoice' and am.is_pembelian = true 
				and am.DATE between %s and %s group by pt.categ_id''',(self.date , self.date_end))
			for category in self._cr.fetchall():
				if category[0]:
					categorys = category_obj.browse(category[0])
					debit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id inner join 
						product_product pp on pp.id = aml.product_id inner join product_template pt on pt.id = pp.product_tmpl_id where  
						aml.credit > 0 and am.type = 'in_invoice' and am.is_pembelian = true and pt.categ_id = %s and 
						am.date between %s and %s )'''
					self._cr.execute(debit_sql, (categorys.property_account_expense_categ_id.id,category[0],self.date , self.date_end))	
					self._cr.commit()

			# Update account harga pokok pembelian per Item/
			# property_account_income_id
			
			self._cr.execute('''SELECT (SELECT value_reference FROM ir_property
				WHERE name IN ('property_account_expense_id','property_account_expense_id') AND res_id = CONCAT('product.template,',pt.id)) AS income_id ,
				aml.product_id FROM product_template pt INNER JOIN product_product pp ON pt.id = pp.product_tmpl_id inner join account_move_line aml on 
				aml.product_id = pp.id inner join account_move am on am.id = aml.move_id where aml.credit > 0 and am.type = 'in_invoice' and am.is_pembelian = true 
				and am.date between %s and %s
				group by aml.product_id, pt.id having (SELECT value_reference FROM ir_property
				WHERE name IN ('property_account_expense_id','property_account_expense_id') AND res_id = CONCAT('product.template,',pt.id)) 
				is not null ''',(self.date , self.date_end))
			for expense_id,product_id in self._cr.fetchall():	
				credit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.credit > 0 and am.type = 'in_invoice' and am.is_pembelian = true and aml.product_id = %s 
						and am.date between %s and %s )'''
				
				self._cr.execute(credit_sql, ( int(expense_id[16:]),product_id,self.date , self.date_end))	
				self._cr.commit()

			# looping dari vendor.			
			self._cr.execute('''SELECT partner_id from account_move where type = 'in_invoice' and 
							is_pembelian = true and DATE between %s and %s group by partner_id ''',(self.date , self.date_end) )
			for partner in self._cr.fetchall():
				if partner[0]:
					partners = partner_obj.browse(partner[0])
					credit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.debit > 0 and am.type = 'in_invoice' and am.is_pembelian = true and am.partner_id = %s 
						and am.date between %s and %s )'''

					self._cr.execute(credit_sql, (partners.property_account_payable_id.id,partner[0],self.date , self.date_end))	
					self._cr.commit()


		if self.j_dn_cn_hut_pemb:
			print ('debit_note')
			# cari semu debit note. group partner.
			self._cr.execute('''SELECT partner_id from account_move where type = 'in_refund' and 
							is_debit_note_pembelian = true and DATE between %s and %s group by partner_id ''',(self.date , self.date_end) )
			for partner in self._cr.fetchall():
				partners = partner_obj.browse(partner)
				acc = partners._get_vendor_accounts()
				debit_note_pembelian = acc['debit_note_hutang']

				credit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.credit > 0 and am.type = 'in_refund' and am.is_debit_note_pembelian = true and am.partner_id = %s 
						and am.date between %s and %s )'''

				debit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.debit > 0 and am.type = 'in_refund' and am.is_debit_note_pembelian = true and am.partner_id = %s 
						and am.date between %s and %s )'''

				self._cr.execute(credit_sql, (debit_note_pembelian.id,partner[0],self.date , self.date_end))	
				self._cr.execute(debit_sql, (partners.property_account_payable_id.id,partner[0],self.date , self.date_end))	
				self._cr.commit()

			print ('credit_note')
			self._cr.execute('''SELECT partner_id from account_move where type = 'in_receipt' and 
							is_credit_note_pembelian = true and DATE between %s and %s group by partner_id ''',(self.date , self.date_end) )
			for partner in self._cr.fetchall():
				partners = partner_obj.browse(partner)
				acc = partners._get_vendor_accounts()
				credit_note_pembelian = acc['credit_note_hutang']

				credit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.credit > 0 and am.type = 'in_receipt' and am.is_credit_note_pembelian = true and am.partner_id = %s 
						and am.date between %s and %s )'''

				debit_sql = '''UPDATE account_move_line set account_id = %s where id in (	
						select aml.id from account_move_line aml inner join account_move am on am.id = aml.move_id 
						where aml.debit > 0 and am.type = 'in_receipt' and am.is_credit_note_pembelian = true and am.partner_id = %s 
						and am.date between %s and %s )'''

				self._cr.execute(debit_sql, (credit_note_pembelian.id,partner[0],self.date , self.date_end))	
				self._cr.execute(credit_sql, (partners.property_account_payable_id.id,partner[0],self.date , self.date_end))	
				self._cr.commit()


		# 	credit note 
		# 	debit >> Ongkos pembelian
		# 	credit >> Hutang usaha
		# 	print ('sukses')

		if self.j_dp_pembelian:
			debit >> uang muka pembelian
			credit >> bank/cash
			print ('sukses')

		# if self.j_pemb_hutang:
		# 	print ('sukses')

		# if self.j_pnj:
		# 	credit >>  Penjualan idr

		# if self.j_rtr_penj:
		# 	debit >> retur Penjualan idr
		# 	print ('sukses')

		# if self.j_dn_cn_ptg_penj:
		# 	Debit note
		# 	Credit >> Penjualan idr
		# 	Debit >> Piutang Usaha idr

		# 	Credit note
		# 	credit >> piutang usaha
		# 	debit >> potongan penjualan

		# 	print ('sukses')

		# if self.j_dp_penj:
		# 	credit >> setoran piutah
		# 	debit >> piutang invoice statement >> putang usaha
		# 	print ('sukses')

		# if self.j_inv_statement:
		# 	debit >> piutang invoice statement >> putang usaha
		# 	print ('sukses')

		# if self.j_pen_piutang:
		# 	print ('sukses')
		
		# if self.j_kas_msk:
		# 	print ('sukses')

		# if self.j_kas_klr:
		# 	print ('sukses')

		# if self.j_trns_kas:
		# 	print ('sukses')

		return True