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

class Currency(models.Model):
	_inherit = "res.currency"
	_description = "Currency"	
	
	def _get_rates_sale_1(self, company, date):
		self.env['res.currency.rate'].flush(['sale_rate', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.sale_rate FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS sale_rate
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates

	def _get_rates_sale_2(self, company, date):
		self.env['res.currency.rate'].flush(['sale_rate_2', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.sale_rate_2 FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS sale_rate_2
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates

	def _get_rates_sale_3(self, company, date):
		self.env['res.currency.rate'].flush(['sale_rate_3', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.sale_rate_3 FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS sale_rate_3
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates

	def _get_rates_sale_4(self, company, date):
		self.env['res.currency.rate'].flush(['sale_rate_4', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.sale_rate_4 FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS sale_rate_4
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates

	def _get_rates_sale_5(self, company, date):
		self.env['res.currency.rate'].flush(['sale_rate_5', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.sale_rate_5 FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS sale_rate_5
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates
	
	def _get_rates_tax(self, company, date):
		self.env['res.currency.rate'].flush(['tax_rate', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.tax_rate FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS tax_rate
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates

	def _get_rates_ledger(self, company, date):
		self.env['res.currency.rate'].flush(['ledger_rate', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.ledger_rate FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS ledger_rate
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates

	is_kurs_dasar = fields.Boolean(default=False, string="Mu x Kurs = MU Dasar")	
	mata_uang = fields.Char('Mata Uang')
	terbilang1 = fields.Char('Terbilang (Sen)')
	terbilang2 = fields.Char('Terbilang (MU)')	
	auto_pay_km_id = fields.Many2one('account.account', 'Auto Pay KM')
	auto_pay_kk_id = fields.Many2one('account.account', 'Auto Pay KK')
	sale_rate = fields.Float(digits=0, default=1.0,string="Kurs Jual *1" ,compute='_compute_current_sale_rate')
	sale_rate_2 = fields.Float(digits=0, default=1.0,string="Kurs Jual *2" ,compute='_compute_current_sale_rate_2')
	sale_rate_3 = fields.Float(digits=0, default=1.0,string="Kurs Jual *3" ,compute='_compute_current_sale_rate_3')
	sale_rate_4 = fields.Float(digits=0, default=1.0,string="Kurs Jual *4" ,compute='_compute_current_sale_rate_4')
	sale_rate_5 = fields.Float(digits=0, default=1.0,string="Kurs Jual *5" ,compute='_compute_current_sale_rate_5')
	company_id = fields.Many2one('res.company',string='Company')

	@api.depends('rate_ids.sale_rate')
	def _compute_current_sale_rate(self):
		date = self._context.get('date') or fields.Date.today()
		company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
		# the subquery selects the last rate before 'date' for the given currency/company
		currency_rates = self._get_rates_sale_1(company, date)
		for currency in self:
			currency.sale_rate = currency_rates.get(currency.id) or 1.0
	
	@api.depends('rate_ids.sale_rate_2')
	def _compute_current_sale_rate_2(self):
		date = self._context.get('date') or fields.Date.today()
		company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
		# the subquery selects the last rate before 'date' for the given currency/company
		currency_rates = self._get_rates_sale_2(company, date)
		for currency in self:
			currency.sale_rate_2 = currency_rates.get(currency.id) or 1.0

	@api.depends('rate_ids.sale_rate_3')
	def _compute_current_sale_rate_3(self):
		date = self._context.get('date') or fields.Date.today()
		company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
		# the subquery selects the last rate before 'date' for the given currency/company
		currency_rates = self._get_rates_sale_3(company, date)
		for currency in self:
			currency.sale_rate_3 = currency_rates.get(currency.id) or 1.0

	@api.depends('rate_ids.sale_rate_4')
	def _compute_current_sale_rate_4(self):
		date = self._context.get('date') or fields.Date.today()
		company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
		# the subquery selects the last rate before 'date' for the given currency/company
		currency_rates = self._get_rates_sale_4(company, date)
		for currency in self:
			currency.sale_rate_4 = currency_rates.get(currency.id) or 1.0

	@api.depends('rate_ids.sale_rate_5')
	def _compute_current_sale_rate_5(self):
		date = self._context.get('date') or fields.Date.today()
		company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
		# the subquery selects the last rate before 'date' for the given currency/company
		currency_rates = self._get_rates_sale_5(company, date)
		for currency in self:
			currency.sale_rate_5 = currency_rates.get(currency.id) or 1.0
	

	def _get_rates_buy(self, company, date):
		self.env['res.currency.rate'].flush(['buying_rate', 'currency_id', 'company_id', 'name'])
		query = """SELECT c.id,
						  COALESCE((SELECT r.buying_rate FROM res_currency_rate r
								  WHERE r.currency_id = c.id AND r.name <= %s
									AND (r.company_id IS NULL OR r.company_id = %s)
							   ORDER BY r.company_id, r.name DESC
								  LIMIT 1), 1.0) AS buying_rate
				   FROM res_currency c
				   WHERE c.id IN %s"""
		self._cr.execute(query, (date, company.id, tuple(self.ids)))
		currency_rates = dict(self._cr.fetchall())
		return currency_rates
	
	

class CurrencyRate(models.Model):
	_inherit = "res.currency.rate"
	_description = "Currency Rate"	
	
	time = fields.Float(string='Pukul')
	buying_rate = fields.Float(digits=0, default=1.0,string="Kurs Beli")
	sale_rate = fields.Float(digits=0, default=1.0,string="Kurs Jual *1")
	sale_rate_2 = fields.Float(digits=0, default=1.0,string="Kurs Jual *2")
	sale_rate_3 = fields.Float(digits=0, default=1.0,string="Kurs Jual *3")
	sale_rate_4 = fields.Float(digits=0, default=1.0,string="Kurs Jual *4")
	sale_rate_5 = fields.Float(digits=0, default=1.0,string="Kurs Jual *5")
	tax_rate = fields.Float(digits=0, default=1.0,string="Kurs Pajak")
	ledger_rate = fields.Float(digits=0, default=1.0,string="Kurs Buku")
	# compute="_compute_time"
	
