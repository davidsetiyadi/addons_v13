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


class Department(models.Model):
	_inherit = "hr.department"
	_description = "GBR inherit hr_department" 

	price = fields.Many2one('product.pricelist', string='Harga Jual', required=False)
	price2 =fields.Many2one('product.pricelist', string='Harga Jual2', readonly=True)
	


		
class GbrDivisi(models.Model):
	_name = "gbr.divisi"
	_description ="GBR divisi" 

	name = fields.Char('Nama', required=True)
	# price = fields.Many2one('product.pricelist', string='Harga Jual', required=False)
	purchase_seq = fields.Integer('Purchase',default=1)
	quot_seq = fields.Integer('Quotation',default=1)
	sale_order  = fields.Integer('Sale order',default=1)
	rkp_peng_brg = fields.Integer('Rekap Pengeluaran Barang',default=1)
	penj_ecrn = fields.Integer('Penjualan Eceran',default=1)
	penjualan = fields.Integer('Penjualan',default=1)
	penjualan_cash = fields.Integer('Penjualan Cash',default=1)
	ret_penjualan = fields.Integer('Retur Penjualan',default=1)
	deb_note_penj = fields.Integer('Debit Note Penjualan',default=1)
	cred_note_penj = fields.Integer('Credit Note Penjualan',default=1)
	deposit_penj = fields.Integer('Deposit Penjualan',default=1)
	invoice_stat_pen = fields.Integer('Invoice statement Penjualan',default=1)
	pen_piutang = fields.Integer('Penerimaan Piutang',default=1)
	pemb_hutang = fields.Integer('Pembayaran Hutang',default=1)
	kas_masuk = fields.Integer('Kas Masuk',default=1)
	kas_keluar = fields.Integer('Kas Keluar',default=1)
	transfer = fields.Integer('Transfer',default=1)
	brg_pindah_gudang = fields.Integer('Pindah Gudang', default=1)
	brg_keluar = fields.Integer('Barang Keluar', default=1)
	brg_masuk = fields.Integer('Barang Masuk', default=1)
	company_id = fields.Many2one('res.company',string='Company',default=1)



	@api.model
	def run_reset_sequence(self):
		department_ids = self.search([])		
		for department in department_ids:
			department.write({
					'purchase_seq': 1,
					'quot_seq': 1,
					'sale_order': 1,
					'rkp_peng_brg': 1,
					'penj_ecrn': 1,
					'penjualan': 1,
					'penjualan_cash': 1,
					'ret_penjualan': 1,
					'deb_note_penj': 1,
					'cred_note_penj': 1,
					'deposit_penj': 1,
					'invoice_stat_pen': 1,
					'pen_piutang': 1,
					'transfer':1
			})
		return True

class GbrJenisPembelian(models.Model):
	_name = "gbr.jenis.pembelian"
	_description ="GBR Jenis Pembelian" 

	name = fields.Char('Jenis', required=True)
	company_id = fields.Many2one('res.company',string='Company',default=1)

class GbrJenisPenjualan(models.Model):
	_name = "gbr.jenis.penjualan"
	_description = "GBR Jenis Penjualan"

	name = fields.Char('Jenis', required=True)
	no = fields.Char('No Penj Pre', required=True)
	company_id = fields.Many2one('res.company',string='Company',default=1)

class GbrOwnerMachine(models.Model):
	_name = "gbr.owner.machine"
	_description = "GBR Owner Machine"

	name = fields.Char('Owner', required=True)
	company_id = fields.Many2one('res.company',string='Company',default=1)

class GbrLiburNasional(models.Model):
	_name = "gbr.libur.nasional"
	_description = "GBR Libur Nasional"

	date = fields.Date('Tanggal', required=True)
	reason = fields.Char('Liburan', required=True)
	company_id = fields.Many2one('res.company',string='Company',default=1)


class kelurahan(models.Model):
	_inherit = 'vit.kelurahan'
	_description = 'Kelurahan'

	company_id = fields.Many2one('res.company',string='Company')

class kecamatan(models.Model):
	_inherit = 'vit.kecamatan'
	_description = 'Kecamatan'
	company_id = fields.Many2one('res.company',string='Company')

class kota(models.Model):
	_inherit = 'vit.kota'
	_description = 'Kota'
	company_id = fields.Many2one('res.company',string='Company',default=1)
   
