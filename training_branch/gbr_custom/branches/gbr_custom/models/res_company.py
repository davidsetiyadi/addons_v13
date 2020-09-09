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

class Country(models.Model):
	_inherit = 'res.country'

	company_id = fields.Many2one('res.company',string='Company',default=1)

class CountryState(models.Model):
	_inherit = 'res.country.state'

	company_id = fields.Many2one('res.company',string='Company',default=1)
	
class ResCompany(models.Model):
	_inherit = "res.company"
	# _description = "Company GBR Inherit"

	fax = fields.Char("Fax")
	npwp =fields.Char("NPWP")
	address=fields.Text('Alamat')
	country = fields.Many2one('res.country', string="Negara")
	faktur_pjk = fields.Char('Faktur Pjk')
	faktur_rtr_pjk = fields.Char('Faktur Return Pjk')
	ttd = fields.Char('TTD')
	heading = fields.Char('Heading pada Laporan')
	singkatan = fields.Char('Singkatan')
	other_customer_id = fields.Many2one('res.partner')
	mata_uang_ids = fields.One2many('res.currency','company_id',string="Mata Uang")
	country_ids = fields.One2many('res.country','company_id',string="Negara")
	state_ids  = fields.One2many('res.country.state','company_id',string="Daerah")
	kota_ids = fields.One2many('vit.kota','company_id',string="Kota/Kab")
	kecamatan_ids = fields.One2many('vit.kecamatan','company_id',string="Kecamatan")
	kelurahan_ids = fields.One2many('vit.kelurahan','company_id',string="Kelurahan")
	divisi_ids = fields.One2many('gbr.divisi','company_id',string="Divisi")
	jenis_pembelian_ids = fields.One2many('gbr.jenis.pembelian','company_id',string="Jenis Pembelian")
	jenis_penjualan_ids = fields.One2many('gbr.jenis.penjualan','company_id',string="Jenis Penjualan")
	owner_ids = fields.One2many('gbr.owner.machine','company_id',string="Owner")
	libur_ids = fields.One2many('gbr.libur.nasional','company_id',string="Liburan")
	awalan_voucher =fields.Char("Awalan No Voucher",default="GHE")
	awalan_pembelian =fields.Char("Awalan No Pembelian",default="GHE")

	# account_credit_no_item_gbr_id = fields.Many2one('account.account', string="Hutang Pembelian Credit Tanpa Item")
	# account_credit_gbr_id = fields.Many2one('account.account', string="Hutang Pembelian Credit *2")
	# account_retur_credit_id = fields.Many2one('account.account', string="Hutang Retur Pembelian Credit")	
	# account_deposit_id = fields.Many2one('account.account', string="Deposit Pembelian")
	# account_debit_no_item_id = fields.Many2one('account.account', string="Hutang Debit Note Hutang Tanpa Item")
	# account_debit_note_id = fields.Many2one('account.account', string="Hutang Debit Note Hutang Pembelian")
	# account_credit_no_item_id = fields.Many2one('account.account', string="Hutang Credit Note Hutang Tanpa Item")
	# account_credit_note_id = fields.Many2one('account.account', string="Hutang Credit Note Hutang Pembelian")

	# account_debit_no_item_gbr_id = fields.Many2one('account.account', string="Piutang Pembelian Credit Tanpa Item")
	# account_retur_debit_id = fields.Many2one('account.account', string="Piutang Retur Pembelian Credit")	
	# account_p_debit_no_item_id = fields.Many2one('account.account', string="Piutang Debit Note Hutang Tanpa Item")
	# account_p_debit_note_id = fields.Many2one('account.account', string="Piutang Debit Note Hutang Pembelian")
	# account_p_credit_no_item_id = fields.Many2one('account.account', string="Piutang Credit Note Hutang Tanpa Item")
	# account_p_credit_note_id = fields.Many2one('account.account', string="Piutang Credit Note Hutang Pembelian")
	# account_p_deposit_id = fields.Many2one('account.account', string="Deposit Penjalan")
	# account_p_inv_stat_id = fields.Many2one('account.account', string="Piutang Invoice Statement Penjualan")
	# account_p_hold_receive_id = fields.Many2one('account.account', string="Hold/Pending Penerimaan Piutang")
	
