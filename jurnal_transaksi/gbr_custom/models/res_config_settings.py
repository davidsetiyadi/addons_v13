# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	# invoice_terms = fields.Text(related='company_id.invoice_terms', string="Terms & Conditions", readonly=False)
	# partner_id = fields.Text(related='company_id.invoice_terms', string="Terms & Conditions", readonly=False)
	partner_id = fields.Many2one('res.partner', string='Nama', related='company_id.partner_id', help='Nama', readonly=False)
	street = fields.Char(string='Alamat', related='company_id.street', help='Alamat', readonly=False)
	city = fields.Char(string='Kota', related='company_id.city', help='Kota', readonly=False)
	country_id = fields.Many2one('res.country', string='Negara', related='company_id.country_id', help='Negara', readonly=False)
	phone = fields.Char(string='Telepon', related='company_id.phone', help='Telepon', readonly=False)
	fax = fields.Char(string='Fax', related='company_id.fax', help='Fax', readonly=False)
	email = fields.Char(string='Email', related='company_id.email', help='', readonly=False)
	website = fields.Char(string='Website', related='company_id.website', help='', readonly=False)
	faktur_pjk = fields.Char(string='Faktur Pajak', related='company_id.faktur_pjk', help='', readonly=False)
	faktur_rtr_pjk = fields.Char(string='Faktur ret Pjk', related='company_id.faktur_rtr_pjk', help='', readonly=False)
	ttd = fields.Char(string='TTD', related='company_id.ttd', help='', readonly=False)
	heading = fields.Char(string='Heading', related='company_id.heading', help='Heading pada laporan', readonly=False)
	singkatan = fields.Char(string='Singkatan', related='company_id.singkatan', help='Singkatan Perusahaan', readonly=False)
	other_customer_id = fields.Many2one('res.partner', string="Pelanggan", related='company_id.other_customer_id', readonly=False)
	awalan_voucher =fields.Char(related='company_id.awalan_voucher',string="Awalan No Voucher", readonly=False)
	awalan_pembelian =fields.Char(related='company_id.awalan_pembelian',string="Awalan No Pembelian", readonly=False)
	account_debit_note_id = fields.Many2one('account.account', related='company_id.account_debit_note_id', string="Hutang Debit Note Hutang Pembelian", readonly=False)
	account_credit_note_id = fields.Many2one('account.account',related='company_id.account_credit_note_id',  string="Hutang Credit Note Hutang Pembelian", readonly=False)
	account_p_debit_note_id = fields.Many2one('account.account',related='company_id.account_p_debit_note_id',  string="Piutang Debit Note Hutang Pembelian", readonly=False)
	account_p_credit_note_id = fields.Many2one('account.account',related='company_id.account_p_credit_note_id',  string="Piutang Credit Note Hutang Pembelian", readonly=False)
	account_deposit_id = fields.Many2one('account.account', string="Deposit Pembelian",related='company_id.account_deposit_id',readonly=False)
	account_p_deposit_id = fields.Many2one('account.account', string="Deposit Penjalan",related='company_id.account_p_deposit_id',readonly=False)
	account_retur_credit_id = fields.Many2one('account.account', string="Hutang Retur Pembelian Credit",related='company_id.account_retur_credit_id',readonly=False)	
	account_retur_debit_id = fields.Many2one('account.account', string="Piutang Retur Pembelian Credit",related='company_id.account_retur_debit_id',readonly=False)	

class GbrConfigSettings(models.TransientModel):
	_name = 'gbr.config.settings'
	_inherit = 'res.config.settings'

	# def on_change_company_id(self, cr, uid, ids, company_id, context=None):
	# 	website_data = self.env['res.company'].read([company_id])[0]
	# 	values = {}
	# 	for fname, v in website_data.items():
	# 		if fname in self._columns:
	# 			values[fname] = v[0] if v and self._columns[fname]._type == 'many2one' else v
	# 	return {'value' : values}

	# 	self.env['res.company'].browse(self._context.get('company_id'))

	# @api.onchange('company_id')
	# def onchange_company_id(self):
		

	def set_values(self):
		super(GbrConfigSettings, self).set_values()

	# @api.model
	# def create(self, vals):
	# 	config_id = super(GbrConfigSettings, self).create(vals)
	# 	self.write(vals)
	# 	return config_id
	
	mata_uang_ids = fields.One2many('res.currency','company_id',related='company_id.mata_uang_ids',string="Mata Uangs", readonly=False)
	country_ids = fields.One2many('res.country','company_id',related='company_id.country_ids',string="Negara(s)", readonly=False)
	state_ids  = fields.One2many('res.country.state','company_id',related='company_id.state_ids' ,string="Daerah", readonly=False)
	kota_ids = fields.One2many('vit.kota','company_id',related='company_id.kota_ids' ,string="Kota/Kab", readonly=False)
	kecamatan_ids = fields.One2many('vit.kecamatan','company_id',related='company_id.kecamatan_ids' ,string="Kecamatan", readonly=False)
	kelurahan_ids = fields.One2many('vit.kelurahan','company_id',related='company_id.kelurahan_ids' ,string="Kelurahan", readonly=False)
	divisi_ids = fields.One2many('gbr.divisi','company_id',related='company_id.divisi_ids' ,string="Divisi", readonly=False)
	jenis_pembelian_ids = fields.One2many('gbr.jenis.pembelian','company_id',related='company_id.jenis_pembelian_ids' ,string="Jenis Pembelian", readonly=False)
	jenis_penjualan_ids = fields.One2many('gbr.jenis.penjualan','company_id',related='company_id.jenis_penjualan_ids' ,string="Jenis Penjualan", readonly=False)
	owner_ids = fields.One2many('gbr.owner.machine','company_id',related='company_id.owner_ids' ,string="Owner", readonly=False)
	libur_ids = fields.One2many('gbr.libur.nasional','company_id',related='company_id.libur_ids' ,string="Liburan", readonly=False)
	