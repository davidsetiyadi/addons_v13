import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form

CODE_SELECTION = [('new','New'),('credit','CR'),('cash','CH'),('debit_note','DN'),('credit_note','CN'),('retur_credit','RTC'),('mm','MM')]

class StatementFilter(models.TransientModel):
	_name = 'statement.filter'
	_description = 'Purchase Filter'

	@api.model
	def default_get(self,fields):
		res = super(StatementFilter, self).default_get(fields)
		active_ids = self._context.get('active_ids')
		if not active_ids:
			return res		

		statements = self.env['gbr.invoice.statement'].browse(active_ids)
		filter_ids = []
				
		for data in statements:
			if data.partner_id:
				# select id from ACCOUNT_Move where gbr.invoice.statement.line				
				query_product_ids = """ 
				SELECT id, invoice_date,partner_id,currency_id,amount_untaxed, amount_total, sale_2_id, purchase_char_id, 
				divisi_id, invoice_date_due,type_code,invoice_payment_term_id,no,ref from ACCOUNT_Move where partner_id = %s and invoice_date <= '%s' 
				and invoice_payment_state = 'not_paid' and state = 'posted' and id not in (select invoice_id from gbr_invoice_statement_line where partner_id = %s ) and 
				(is_retur_penj = true or is_penjualan = true or is_debit_note_penjualan = true OR is_credit_note_penjualan = TRUE )
				""" % (data.partner_id.id,data.date_start,data.partner_id.id)
				
				product_ids = self.env.cr.execute(query_product_ids)
				results = self.env.cr.fetchall()				

				# cari account move 

				# penjualan credit cr 
				# debit note penjualan dn
				# credit note cn
				# retur penjualan rtc
				# deposit dp
				# belum ada di statement view
				# belum bayar

				for rec in results:
					line = (0,0, {
						'invoice_id' :rec[0],
						'invoice_date':rec[1],
						'partner_id':rec[2],
						'currency_id':rec[3],
						'harga_jual':rec[4],
						'discount': 0,
						'nilai_jual' : rec[5],
						'sale_order_id': rec[6],
						'purchase_order_id': rec[7],
						'divisi_id': rec[8],
						'invoice_date_due': rec[9],
						'type_code': rec[10],
						'jt_tmpo': rec[11],
						'no': rec[12],
						'ref': rec[13]
						})
					filter_ids.append(line)
				
		
		if len(filter_ids) >= 1:			
			res.update({
				'filter_ids' : filter_ids,
				'name' : data.partner_id.name,
				'date_start' : data.date_start,
				'partner_id' : data.partner_id.id
				})
		else:
			raise ValidationError(_('Sorry, No Result Found.'))
			# raise UserError(_('Sorry, No Result Found'))
			# err_msg = _('Sorry, No Result Found.')
			# redir_msg = _('Go to UOM Categories')
			# raise RedirectWarning(err_msg, self.env.ref('gbr_custom.wizard_purchase_filter_view').id, redir_msg)

		return res

	def get_list_statement(self):		
		active_ids = self._context.get('active_ids')
		if not active_ids:
			return res	

		statement_line_obj = self.env['gbr.invoice.statement.line']

		for data in self:
			for line in data.filter_ids:
				if line.is_confirm > 0:
					statement_line_obj.create({
						'invoice_id' : line.invoice_id.id,						
						'statement_id' :active_ids[0],	
						'partner_id': line.partner_id.id,
						})
		return True

	name = fields.Char('Name')
	date_start = fields.Date('Tanggal')
	partner_id= fields.Many2one('res.partner', string='Pelanggan')
	is_jt_tmpo = fields.Boolean('Jatuh Tempo', default=True)
	is_not_jt_tmpo = fields.Boolean('Belum Jatuh Tempo', default=True)
	filter_ids = fields.One2many('statement.filter.line','statement_id', string="Filters")

	


class StatementFilterLine(models.TransientModel):
	_name = 'statement.filter.line'
	_description = 'Purchase Filter'

	name = fields.Char('Nama')
	no = fields.Char('NO')
	ref = fields.Char('Ref')
	statement_id = fields.Many2one('statement.filter', string="Filter")
	is_confirm = fields.Boolean('Confirm')
	invoice_id = fields.Many2one('account.move', 'List')
	invoice_date = fields.Date('Tanggal')
	partner_id = fields.Many2one('res.partner' ,'Pelanggan')
	currency_id = fields.Many2one('res.currency' , string='MU')
	harga_jual = fields.Float('Harga Jual')
	discount = fields.Float('Discount')
	nilai_jual =fields.Float('Nilai Jual')
	jt_tmpo = fields.Many2one('account.payment.term', 'Jatuh Tempo')
	invoice_date_due = fields.Date('Tanggal Jatuh Tempo')	
	sale_order_id = fields.Many2one('sale.order', string='Sale Order')
	purchase_order_id= fields.Many2one('gbr.po.number', string='Purchase Order')
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi")
	type_code = fields.Selection(CODE_SELECTION,string='Mlk')
	



	