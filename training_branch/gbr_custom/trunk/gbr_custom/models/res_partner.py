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
KURS = [('idr','IDR'),('sin','SGD')]
KURS2 = [('idr','IDR'),('sin','SGD')]
PAJAK = [('pjk','PJK'),('ppn','PPN')]
MU = [('idr','IDR'),('sin','SGD')]
TITLE = [('bpk','Bpk.'),('cv','CV.'),('ibu','Ibu.'),('mr','Mr.'),('mrs','Mrs.'),('ms','Ms.'),('pt','PT.'),('ud','UD')]
RELIGION = [('budha','Budha'),('hindu','Hindu'),('islam','Islam'),('katolik','Katolik'),('kong','Kong Hu Cu'),('kris','Kristen')]
OPTION1 = [('tp_promo','Tanpa Promo'),('0','---')]
OPTION2 = [('tp_promo','Tanpa Promo'),('0','---')]
PROTECT1 = [('warn', 'Warning'),('error', 'Error')]
PROTECT2 = [('warn', 'Warning'),('error', 'Error')]
PROTECT3 = [('warn', 'Warning'),('error', 'Error')]
GENDER = [('pria','Pria'),('wanita','Wanita')]

KURS_JUAL = [('sale_rate', 'Kurs Jual *1'),('sale_rate_2','Kurs Jual *2'),('sale_rate_3', 'Kurs Jual *3'),('sale_rate_4', 'Kurs Jual *4'),('sale_rate_5','Kurs Jual *5')]
HARGA_JUAL = [('price_1', 'HJ *1'),('price_2','HJ *2'),('price_3', 'HJ *3'),('price_4', 'HJ *4'),('price_5','HJ *5')]

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'
	_description = 'Res Partner GBR inherit'

	is_value = fields.Boolean('Value', default=True)

class ResPartner(models.Model):
	_inherit = "res.partner"
	_description = "Res Partner GBR Inherit"

	title = fields.Selection(TITLE, string='Title')
	gbr_category_id = fields.Many2one('res.partner.category',string="GBR Category")
	is_value = fields.Boolean('Value')
	is_customer = fields.Boolean('Customer')
	address = fields.Text('Alamat')
	npwp = fields.Char('NPWP')
	phone2=fields.Char('TPhone 2')
	phone3=fields.Char('TPhone 3')
	fax = fields.Char('Fax')
	nominal_credit = fields.Float('Nominal')
	kurs = fields.Selection(KURS, string="Max Crd")
	kurs2 = fields.Selection(KURS2, string="Max Crd 2")
	kurs_2_id = fields.Many2one('res.currency', string="Transaksi Mata Uang")
	kurs_id = fields.Many2one('res.currency', string="Max Crd 3")
	pajak_type = fields.Selection(PAJAK, string="Pajak")
	account_taxId = fields.Many2one('account.tax',string='Tax')
	contact_person1 = fields.Char('Hubungi')
	contact_person2 = fields.Char('Hubung2')
	contact_person3 = fields.Char('Hubung3')
	contact_number1 = fields.Char('Telephone')
	contact_number2 = fields.Char('Telephone 2')
	contact_number3= fields.Char('Telephone 3')
	department_id = fields.Many2one('hr.department', string="Kelompok")
	mu_transaction = fields.Selection(MU, string="Default MU Transaksi Pembelian")
	default_mu_jual_id = fields.Many2one('res.currency', string="Default MU Jual")
	h_jual = fields.Selection(HARGA_JUAL,string="H. Jual")
	is_value_sale_price = fields.Boolean('MU')
	location_id = fields.Many2one('res.country.state','Daerah')
	gender = fields.Selection(GENDER, string='gender')
	non_active = fields.Date('Non-active')
	is_mix = fields.Boolean('Gabungan dari bebarapa pedagang eceran')
	is_sale = fields.Boolean('Penjualan : Harga jual diambil dari harga jual terakhir')
	is_black_list = fields.Boolean('Pelanggan diblack list')
	is_limit = fields.Boolean('Tanpa cek limit saat Simpan penjualan')
	religion = fields.Selection(RELIGION, string="Agama")
	ktp = fields.Char('No. KTP')
	born = fields.Char('Temp Lahir')
	birth = fields.Date('tgl')
	relation = fields.Char('Hubungan')
	status = fields.Char('Status (1)')
	pend_akh = fields.Char('Pend Akh')
	term_cred = fields.Char('Term')
	global_dis = fields.Float('Global Disc')
	item_disc = fields.Float('Item Disc')
	option_promo1 = fields.Selection(OPTION1, 'Promo')
	option_promo2 = fields.Selection(OPTION2, 'Promo2')
	protect1 = fields.Selection(PROTECT1, string='Protect')
	protect2 = fields.Selection(PROTECT2, string='Protect 2')
	protect3 = fields.Selection(PROTECT3, string='Protect 3')
	nominal_maxCrd = fields.Char('Max Cred')
	nominal_maxCrd2 = fields.Char('Max Cred2')
	max_payment_term_credit = fields.Char('Max Jth Temp')
	max_payment_term_credit2 = fields.Char('Max Jth Temp2')
	max_payment_term = fields.Many2one('account.payment.term', string="Max Day")
	pricelist_id = fields.Many2one('product.pricelist', string="Harga Jual")
	type_sale_id = fields.Many2one('gbr.jenis.penjualan')
	no_tax_fakture = fields.Char('No Faktur Pajak')
	memo1 = fields.Text('Memo')
	memo2 = fields.Text("Memo 2")
	account_credit_no_item_gbr_id = fields.Many2one('account.account', string="Hutang Pembelian Credit Tanpa Item")
	account_credit_gbr_id = fields.Many2one('account.account', string="Hutang Pembelian Credit *2")
	account_retur_credit_id = fields.Many2one('account.account', string="Hutang Retur Pembelian Credit")	
	account_deposit_id = fields.Many2one('account.account', string="Account Deposit Pembelian")
	account_debit_no_item_id = fields.Many2one('account.account', string="Hutang Debit Note Hutang Tanpa Item")
	account_debit_note_id = fields.Many2one('account.account', string="Hutang Debit Note Hutang Pembelian") #
	account_credit_no_item_id = fields.Many2one('account.account', string="Hutang Credit Note Hutang Tanpa Item")
	account_credit_note_id = fields.Many2one('account.account', string="Hutang Credit Note Hutang Pembelian") #
	account_debit_no_item_gbr_id = fields.Many2one('account.account', string="Piutang Pembelian Credit Tanpa Item")
	account_retur_debit_id = fields.Many2one('account.account', string="Piutang Retur Pembelian Credit")	
	account_p_debit_no_item_id = fields.Many2one('account.account', string="Piutang Debit Note Hutang Tanpa Item")
	account_p_debit_note_id = fields.Many2one('account.account', string="Piutang Debit Note Hutang Pembelian")#
	account_p_credit_no_item_id = fields.Many2one('account.account', string="Piutang Credit Note Hutang Tanpa Item")
	account_p_credit_note_id = fields.Many2one('account.account', string="Piutang Credit Note Hutang Pembelian")#
	account_p_deposit_id = fields.Many2one('account.account', string="Deposit Penjualan")
	account_p_inv_stat_id = fields.Many2one('account.account', string="Piutang Invoice Statement Penjualan")
	account_p_hold_receive_id = fields.Many2one('account.account', string="Hold/Pending Penerimaan Piutang")

	is_personal = fields.Selection([('company','Corporate/Perusahaan'),('personal','Personal')],'Personal')
	group_id = fields.Many2one('gbr.group.4', 'Group')
	group2_id = fields.Many2one('gbr.group.4', 'Group 2')
	group3_id = fields.Many2one('gbr.group.4', 'Grouping 1')
	group4_id = fields.Many2one('gbr.group.4', 'Grouping 2')
	group5_id = fields.Many2one('gbr.group.4', 'Grouping 3')
	group_user_ids = fields.Many2many('gbr.group.6', 'partner_group_6_rel','partner_id', 'group_id', string='Group User')
	group_level_ids = fields.Many2many('gbr.group.5', 'partner_group_5_rel','partner_id', 'group_id', string='Group Level')
	group_cust_id = fields.Many2one('gbr.group.7', string='Grouping Pelanggan')
	group_cust_2_id = fields.Many2one('gbr.group.8', string='Grouping Pelanggan 2')
	# is_user_level_1 
	is_group_user_po = fields.Boolean('is Purchase Order',default=True)
	is_group_user_pch = fields.Boolean('is Pembelian Cash',default=True)
	is_group_user_pcr = fields.Boolean('Pembelian Credit',default=True)
	is_group_user_rpch = fields.Boolean('Retur Pembelian Cash',default=True)
	is_group_user_rpcr = fields.Boolean('Retur Pembelian Credit',default=True)
	is_group_user_dnh = fields.Boolean('Debit Note Hutang',default=True)
	is_group_user_cnh = fields.Boolean('Credit Note Hutang',default=True)
	is_group_user_dp = fields.Boolean('is Deposit Pembelian',default=True)
	is_user_level_1 = fields.Boolean('User Level 1',default=True)
	is_user_level_2 = fields.Boolean('User Level 2',default=True)
	is_user_level_3 = fields.Boolean('User Level 3',default=True)
	is_user_level_4 = fields.Boolean('User Level 4',default=True)
	is_user_level_5 = fields.Boolean('User Level 5',default=True)
	is_user_level_6 = fields.Boolean('User Level 6',default=True)
	is_user_level_7 = fields.Boolean('User Level 7',default=True)
	is_user_level_8 = fields.Boolean('User Level 8',default=True)
	is_user_level_9 = fields.Boolean('User Level 9',default=True)
	is_user_level_10 = fields.Boolean('User Level 10',default=True)
	is_user_level_11 = fields.Boolean('User Level 11',default=True)
	is_user_level_12 = fields.Boolean('User Level 12',default=True)
	is_user_level_13 = fields.Boolean('User Level 13',default=True)
	is_user_level_14 = fields.Boolean('User Level 14',default=True)
	is_user_level_15 = fields.Boolean('User Level 15',default=True)
	is_user_level_16 = fields.Boolean('User Level 16',default=True)
	is_user_level_17 = fields.Boolean('User Level 17',default=True)
	is_user_level_18 = fields.Boolean('User Level 18',default=True)
	is_user_level_19 = fields.Boolean('User Level 19',default=True)
	is_user_level_20 = fields.Boolean('User Level 20',default=True)
	is_user_level_21 = fields.Boolean('User Level 21',default=True)
	is_user_level_22 = fields.Boolean('User Level 22',default=True)
	is_user_level_23 = fields.Boolean('User Level 23',default=True)
	is_user_level_24 = fields.Boolean('User Level 24',default=True)
	is_user_level_25 = fields.Boolean('User Level 25',default=True)
	is_user_level_26 = fields.Boolean('User Level 26',default=True)
	is_user_level_27 = fields.Boolean('User Level 27',default=True)
	is_user_level_28 = fields.Boolean('User Level 28',default=True)
	is_user_level_29 = fields.Boolean('User Level 29',default=True)
	is_user_level_30 = fields.Boolean('User Level 30',default=True)
	is_noted = fields.Boolean('Catatan')
	noted = fields.Char('List Catatan')
	sales_employee_id = fields.Many2one('hr.employee', string="Sales")
	collector_employee_id = fields.Many2one('hr.employee', string="Collector")
	is_semua_data = fields.Boolean(string='Semua Data',default=True)

	
	def _get_vendor_accounts(self):
		return {
			'debit_note_hutang': self.account_debit_note_id or self.env.company.account_debit_note_id,
			'credit_note_hutang': self.account_credit_note_id or self.env.company.account_credit_note_id,
			'debit_note_piutang': self.account_p_debit_note_id  or self.env.company.account_p_debit_note_id,
			'credit_note_piutang': self.account_p_credit_note_id or self.env.company.account_p_credit_note_id
		}

	@api.onchange('is_personal')
	def onchange_is_personal(self):		
		if self.is_personal == 'personal':
			self.is_company = False
		elif self.is_personal == 'company':
			self.is_company = True		      
		return {}

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(ResPartner, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(ResPartner, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)