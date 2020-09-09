import json
from datetime import datetime, timedelta
import time
from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.osv import expression
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import random
import locale

import ast
TYPE_NUMBER = [('dnh','Debit Note Hutang'),('cnh','Credit Note Hutang'),('dpp','Deposit Pembelian'),
				('rtcp','Retur Pembelian'),('pembh','Pembayaran Hutang')]
CODE_SELECTION = [('KK','KK'),('KM','KM'),('new','New'),('credit','CR'),('cash','CH'),('debit_note','DN'),('credit_note','CN'),('retur_credit','RTC'),('mm','MM')]
TYPE_KAS_MSK = [('RTRP','Retur Pembelian'),('PH','Pembayaran Hutang'),('PNJ','Penjualan'),('DPPNJ','Deposit Penjualan'),('PNPTG','Penerimaan Piutang'),('KMU','Kas Masuk Umum')]
TYPE_KAS_KLR = [('PB','Pembelian'),('DPPB','Deposit Pembelian'),('PH','Pembayaran Hutang'),('PNJ','Penjualan'),('RTRPNJ','Retur Penjualan'),('PNPTG','Penerimaan Piutang'),('KKU','Kas Keluar Umum')]

class account_payment(models.Model):
	_inherit = "account.payment"

	no 			= fields.Char('No',required=True, copy=False, index=True, default=lambda self: _('New'))
	divisi_id 	= fields.Many2one('gbr.divisi', tracking=True, string="Divisi",states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.employee_id.divisi_id)
	no_so_id 	= fields.Many2one('sale.order', string="SO") 
	no_po_id 	= fields.Many2one('sale.order', string="PO") 
	penjualan_id = fields.Many2one('account.move', string="Penjualan")
	pembelian_id = fields.Many2one('account.move', string="Pembelian")
	catatan 	= fields.Char('Catatan') 
	catatan_2	= fields.Char('Catatan 2') 
	catatan_3	= fields.Char('Catatan 3') 
	employee_id = fields.Many2one('hr.employee', string="Employee")
	no_po_char	= fields.Char(string="No Deposit Pembelian", tracking=True, copy=False,states={'draft': [('readonly', False)]},)  
	is_semua_data = fields.Boolean(string='Semua Data',default=True)
	tanggal_2 = fields.Date('Tanggal 2')
	tanggal_3 = fields.Date('Tanggal 3')
	tanggal_char	= fields.Char('Tanggal Char',readonly=True,compute='get_tanggal_char') 
	type_code = fields.Selection(CODE_SELECTION,string='Mlk',compute='get_tanggal_char')
	source_acc_id = fields.Many2one('account.account', string='Source', compute='get_account')
	destination_acc_id = fields.Many2one('account.account', string='Destination', compute='get_account')
	type_kas_keluar = fields.Selection(TYPE_KAS_KLR, string='Type Kas Keluar')
	type_kas_masuk = fields.Selection(TYPE_KAS_MSK, string='Type Kas masuk')
	
	# default get ambil divisi ketika bayar. cash penjualan maupun pembelian, masuk ke dalam penjualan cash


	@api.model
	def default_get(self, default_fields):
		rec = super(account_payment, self).default_get(default_fields)
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		active_model = self._context.get('active_model')

		# Check for selected invoices ids
		if not active_ids or active_model != 'account.move':
			return rec
		if self._context.get('disable_search'):
			type_code = 'new'
			invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))
			if invoices[0].is_pembelian == True:
				type_code = 'KK'
				rec.update({'type_kas_keluar': 'PB'})
			if invoices[0].is_penjualan == True:
				type_code = 'KM'
				rec.update({'type_kas_masuk': 'PNJ'})
			rec.update({
				'divisi_id': invoices[0].divisi_id.id,							
				'type_code':type_code
				})
			return rec

		return rec
		
	@api.onchange('journal_id','destination_journal_id')
	def onchange_account_id(self):
		# tanggal_char = ''
		if self.journal_id:
			self.source_acc_id = self.journal_id.default_credit_account_id.id
		if self.destination_journal_id:
			self.destination_acc_id = self.destination_journal_id.default_debit_account_id.id

	@api.depends('journal_id','destination_journal_id')
	def get_account(self):
		for payment in self:	
			source_acc_id = False
			destination_acc_id = False
			if payment.journal_id:
				source_acc_id = payment.journal_id.default_credit_account_id.id
			if payment.destination_journal_id:
				destination_acc_id = payment.destination_journal_id.default_debit_account_id.id
			payment.update({
				'source_acc_id': source_acc_id,
				'destination_acc_id': destination_acc_id,
				})	


	@api.onchange('payment_date')
	def onchange_payment_date(self):
		# tanggal_char = ''
		if self.payment_date:			
			date_format = '%A, %d %B %Y'

			locale.setlocale(locale.LC_ALL, ('id_ID','UTF-8') )
			tanggal_char = self.payment_date.strftime(date_format)
			# print ('tanggal_char',str(tanggal_char))
			self.tanggal_char = str(tanggal_char)

	@api.depends('payment_date')
	def get_tanggal_char(self):
		for payment in self:	
			tanggal_char = ''
			type_code = 'KM'
			if payment.payment_type == 'outbound':
				type_code = 'KK'
			if payment.payment_date:
				date_format = '%A, %d %B %Y'
				locale.setlocale(locale.LC_ALL, ('id_ID','UTF-8') )
				tanggal_chars = payment.payment_date.strftime(date_format)
				tanggal_char = str(tanggal_chars)
			payment.update({
				'tanggal_char': tanggal_char,
				'type_code': type_code,
				})	

	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:
				default_payment_type = self.env.context.get('default_payment_type', False)				
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				if default_payment_type == 'inbound':
					vals['no'] = str(divisi_id.deposit_penj).zfill(5)
					divisi_id.write({'deposit_penj': divisi_id.deposit_penj+1 })
				elif default_payment_type == 'transfer':
					vals['no'] = str(divisi_id.transfer).zfill(5)
					divisi_id.write({'transfer': divisi_id.transfer+1 })			
			
		result = super(account_payment, self).create(vals)
		return result

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(account_payment, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(account_payment, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	@api.onchange('no_so_id','penjualan_id')
	def onchange_penjualan_id(self):
		if self.penjualan_id:
			if self.penjualan_id.partner_id:
				self.partner_id = self.penjualan_id.partner_id.id
		elif self.no_so_id :
			if self.no_so_id.partner_id:
				self.partner_id = self.no_so_id.partner_id.id

	@api.onchange('no_po_id','pembelian_id')
	def onchange_pembelian_id(self):
		if self.pembelian_id:
			if self.pembelian_id.partner_id:
				self.partner_id = self.pembelian_id.partner_id.id
		elif self.no_po_id :
			if self.no_po_id.partner_id:
				self.partner_id = self.no_po_id.partner_id.id

	def _get_creation_message(self):
		# OVERRIDE
		if self.payment_type == 'transfer':
			return _('Transfer Kas')					
		else:
			return super()._get_creation_message()

	# deposit customer , KM 
	# deposit supplier ,KK
	def post(self):
		""" Create the journal items for the payment and update the payment's state to 'posted'.
			A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
			and another in the destination reconcilable account (see _compute_destination_account_id).
			If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
			If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
		"""
		AccountMove = self.env['account.move'].with_context(default_type='entry')
		for rec in self:

			if rec.state != 'draft':
				raise UserError(_("Only a draft payment can be posted."))

			if any(inv.state != 'posted' for inv in rec.invoice_ids):
				raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

			# keep the name in case of a payment reset to draft
			type_code = 'new'
			if not rec.name:
				# Use the right sequence to set the name
				if rec.payment_type == 'transfer':
					sequence_code = 'account.payment.transfer'
					# type_code = 'KM'
				else:
					if rec.partner_type == 'customer':
						if rec.payment_type == 'inbound':
							sequence_code = 'account.payment.customer.invoice'
							type_code = 'KM'
						if rec.payment_type == 'outbound':
							sequence_code = 'account.payment.customer.refund'
							type_code = 'KK'
					if rec.partner_type == 'supplier':
						if rec.payment_type == 'inbound':
							type_code = 'KM'
							sequence_code = 'account.payment.supplier.refund'
						if rec.payment_type == 'outbound':
							sequence_code = 'account.payment.supplier.invoice'
							type_code = 'KK'
				rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
				if not rec.name and rec.payment_type != 'transfer':
					raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

			

			prepare_move_lines = rec._prepare_payment_moves()
			if rec.payment_type == 'inbound':
				type_code = 'KM'
				prepare_move_lines[0]['type_kas_keluar'] = 'KMU'

			elif rec.payment_type == 'outbound':
				type_code = 'KK'
				prepare_move_lines[0]['type_kas_keluar'] = 'KKU'

			prepare_move_lines[0]['type_kas_keluar'] = rec.type_kas_keluar
			prepare_move_lines[0]['type_kas_masuk'] = rec.type_kas_masuk
			prepare_move_lines[0]['type_code'] = type_code
			prepare_move_lines[0]['divisi_id'] = rec.divisi_id.id
			
			moves = AccountMove.with_context(default_type_code=type_code).create(prepare_move_lines)
			moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

			# Update the state / move before performing any reconciliation.
			move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
			rec.write({'state': 'posted', 'move_name': move_name})

			if rec.payment_type in ('inbound', 'outbound'):
				# ==== 'inbound' / 'outbound' ====
				if rec.invoice_ids:
					(moves[0] + rec.invoice_ids).line_ids \
						.filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id)\
						.reconcile()
			elif rec.payment_type == 'transfer':
				# ==== 'transfer' ====
				moves.mapped('line_ids')\
					.filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
					.reconcile()

		return True

class GbrVoucherNumber(models.Model):	
	_name = "gbr.voucher.number"
	_description = "GBR Voucher Number"


	name = fields.Char('Owner', required=True)
	type = fields.Selection(TYPE_NUMBER,string='Type')

	_sql_constraints = [
		('name_uniq', 'unique(name,type)', 'Voucher Reference must be unique!'),
	]

class GbrPaymentVoucher(models.Model):	
	_name = "gbr.payment.voucher"	
	_inherit = ['mail.thread', 'mail.activity.mixin']    
	_description = "Pembayaran"
	_rec_name = "no"


	name = fields.Char(readonly=True, copy=False)  # The name is attributed upon post()
	# reconciled_invoice_ids = fields.Many2many('account.move', string='Reconciled Invoices', compute='_compute_reconciled_invoice_ids', help="Invoices whose journal items have been reconciled with these payments.")
	# has_invoices = fields.Boolean(compute="_compute_reconciled_invoice_ids", help="Technical field used for usability purposes")
	# reconciled_invoices_count = fields.Integer(compute="_compute_reconciled_invoice_ids")
	# compute='_compute_reconciled_invoice_ids'
	# divisi = fields.Selection([('head', 'Head'), ('tpi_ghe', 'TPI - GHE')], readonly=True, default='head', copy=False, string="Divisi")
	divisi_id = fields.Many2one('gbr.divisi', string="Divisi",default=lambda self: self.env.user.employee_id.divisi_id)
	state = fields.Selection([('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, tracking=True, default='draft', copy=False, string="Status")
	partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
	voucher_number_id = fields.Many2one('gbr.voucher.number', string='No', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
	no = fields.Char('NO',required=True, copy=False, index=True, default=lambda self: _('New'))
	no_append = fields.Char('NO Append', default=lambda self: _('New'), copy=False)
	employee_id = fields.Many2one('hr.employee', string="Collector")
	catatan = fields.Char(string='Catatan', readonly=True, states={'draft': [('readonly', False)]})
	payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False, tracking=True)
	invoice_lines_ids = fields.Many2many('account.move', 'gbr_payment_voucher_account_move_rel', 'payment_voucher_id', 'account_move_id', string='Invoice Lines', copy=False)
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)
	amount = fields.Monetary(string='Amount', compute='_compute_amount', readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
	amount_total = fields.Monetary(string='Amount Total', compute='_compute_amount',store=True)
	payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')], string='Payment Type', required=True, readonly=True, states={'draft': [('readonly', False)]})
	partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], tracking=True, readonly=True, states={'draft': [('readonly', False)]})
	journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True, domain="[('type', 'in', ('bank', 'cash'))]")
	company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
	payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=False, readonly=True, states={'draft': [('readonly', False)]},
		help="Manual: Get paid by cash, check or any other method outside of SGEEDE.\n"\
		"Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n"\
		"Check: Pay bill by check and print it from SGEEDE.\n"\
		"Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n"\
		"SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")
	# move_reconciled = fields.Boolean(compute="_get_move_reconciled", readonly=True)
	is_semua_data = fields.Boolean(string='Semua Data',default=True)

	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		if self._context.get('disable_search'):			
			if len(domain) == 1:
				domain = expression.AND([domain, [('id', '=', 0)]])
				return super(GbrPaymentVoucher, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
		return super(GbrPaymentVoucher, self.sudo()).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

	def _get_creation_message(self):
		# OVERRIDE
		if self.payment_type == 'outbound':
			return _('Pembayaran Hutang Created')			
		elif self.payment_type == 'inbound':
			return _('Penerimaan Piutang Created')
		else:
			return super()._get_creation_message()

	@api.model
	def create(self, vals):		
		if vals.get('no', _('New')) == _('New'):
			divisi = vals.get('divisi_id')
			if divisi:

				pemb_hutang = self.env.context.get('pemb_hutang', False)
				pen_piutang = self.env.context.get('pen_piutang', False)
				divisi_id = self.env['gbr.divisi'].search([('id','=',divisi)])
				
				if pemb_hutang:
					vals['no'] = str(divisi_id.pemb_hutang).zfill(5)
					divisi_id.write({'pemb_hutang': divisi_id.pemb_hutang+1 })
				elif pen_piutang:
					vals['no'] = str(divisi_id.pen_piutang).zfill(5)
					divisi_id.write({'pen_piutang': divisi_id.pen_piutang+1 })

			if vals.get('no_append', _('New')) == _('New'):
				awalan_voucher = self.env.company.awalan_voucher
				vals['no_append'] = str(awalan_voucher)+'/' + time.strftime('%m')+'/'+ time.strftime('%Y')
			
		result = super(GbrPaymentVoucher, self).create(vals)
		return result

	@api.model
	def default_get(self, default_fields):
		rec = super(GbrPaymentVoucher, self).default_get(default_fields)
		active_ids = self._context.get('active_ids') or self._context.get('active_id')
		active_model = self._context.get('active_model')

		# Check for selected invoices ids
		if not active_ids or active_model != 'account.move':
			return rec

		invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))

		# Check all invoices are open
		if not invoices or any(invoice.state != 'posted' for invoice in invoices):
			raise UserError(_("You can only register payments for open invoices"))
		# Check if, in batch payments, there are not negative invoices and positive invoices
		dtype = invoices[0].type
		for inv in invoices[1:]:
			if inv.type != dtype:
				if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
						(dtype == 'in_invoice' and inv.type == 'in_refund')):
					raise UserError(_("You cannot register payments for vendor bills and supplier refunds at the same time."))
				if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
						(dtype == 'out_invoice' and inv.type == 'out_refund')):
					raise UserError(_("You cannot register payments for customer invoices and credit notes at the same time."))

		amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id, rec.get('payment_date') or fields.Date.today())
		rec.update({
			'currency_id': invoices[0].currency_id.id,
			'amount': abs(amount),
			'payment_type': 'inbound' if amount > 0 else 'outbound',
			'partner_id': invoices[0].commercial_partner_id.id,
			'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
			'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
			'invoice_ids': [(6, 0, invoices.ids)],
		})
		return rec

	def cancel(self):
		self.write({'state': 'cancelled'})

	def post(self):		
		self.write({'state': 'posted'})
		return self.open_payment_matching_screen()

	def unlink(self):
		if any(bool(rec.invoice_lines_ids) for rec in self):
			raise UserError(_("You cannot delete a payment that is already posted."))
		
		return super(GbrPaymentVoucher, self).unlink()
	 
	def action_draft(self):		
		self.write({'state': 'draft'})

	def button_journal_entries(self):
		#cari vendor payment
		# cari vendor payment dari invoice paid
		# reconciled_moves.filtered(lambda move: move.is_invoice())
		invoice_ids = []
		payment_ids = []
		for invoice in self.invoice_lines_ids:
			if invoice.invoice_payment_state != 'not_paid':
				# cari invoice yang sudah dibayar
				invoice_ids.append(invoice.id)

		if len(invoice_ids) == 1:
			self._cr.execute(
				'''
				SELECT move.id as move_id , line.id as move_line_id,rec_line.id as rec_id, payment.id as payment_id 
				FROM account_move move
				JOIN account_move_line line ON line.move_id = move.id
				JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
				JOIN account_move_line rec_line ON
					(rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
					OR
					(rec_line.id = part.debit_move_id AND line.id = part.credit_move_id) 
				JOIN account_payment payment ON payment.id = rec_line.payment_id
				JOIN account_journal journal ON journal.id = rec_line.journal_id
				WHERE payment.state IN ('posted', 'sent')
				AND journal.post_at = 'pay_val' 	
				AND move.id = %s ;
				''', [invoice_ids[0]])

			res = self._cr.fetchall()
			# print ('ressssssssssssss',res,invoice_ids)
			for result in res:
				if result[3]:
					payment_ids.append(result[3])

		if len(invoice_ids) > 1:
			self._cr.execute(
				'''
				SELECT move.id as move_id , line.id as move_line_id,rec_line.id as rec_id, payment.id as payment_id 
				FROM account_move move
				JOIN account_move_line line ON line.move_id = move.id
				JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
				JOIN account_move_line rec_line ON
					(rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
					OR
					(rec_line.id = part.debit_move_id AND line.id = part.credit_move_id) 
				JOIN account_payment payment ON payment.id = rec_line.payment_id
				JOIN account_journal journal ON journal.id = rec_line.journal_id
				WHERE payment.state IN ('posted', 'sent')
				AND journal.post_at = 'pay_val' 	
				AND move.id in %s ;
				''', [tuple(invoice_ids)])

			res = self._cr.fetchall()
			# print ('ressssssssssssss',res,invoice_ids)
			for result in res:
				if result[3]:
					payment_ids.append(result[3])
		
		return {
			'name': _('Journal Items'),
			'view_mode': 'tree,form',
			'res_model': 'account.move.line',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('payment_id', 'in', tuple(payment_ids) )],
		}

	def open_payment_matching_screen(self):
		# Open reconciliation view for customers/suppliers
		move_line_id = False
		# for move_line in self.move_line_ids:
		# 	if move_line.account_id.reconcile:
		# 		move_line_id = move_line.id
		# 		break
		move_ids = []
		if not self.partner_id:
			raise UserError(_("Payments without a customer can't be matched"))
		action_context = {}
		action_context = self._context.copy()
		action_context.update({'company_ids': [self.company_id.id], 'partner_ids': [self.partner_id.commercial_partner_id.id]})

		if self.partner_type == 'customer':
			action_context.update({'mode': 'customers'})
		elif self.partner_type == 'supplier':
			action_context.update({'mode': 'suppliers'})
		
		moves_ids = [x.id for x in self.invoice_lines_ids]

		action_context.update({'payment_move_ids': moves_ids})

		if move_line_id:
			action_context.update({'move_line_id': move_line_id})
		print ('contexaaaaaaa',action_context)
		return {
			'type': 'ir.actions.client',
			'tag': 'manual_reconciliation_view',
			'context': action_context,
		}
	
	def button_invoices(self):
		return {
			'name': _('Paid Invoices'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (self.env.ref('account.view_move_form').id, 'form')],
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', [x.id for x in self.reconciled_invoice_ids])],
			'context': {'create': False},
		}

	@api.depends('invoice_lines_ids')
	def _compute_amount(self):
		for payment_voucher in self:
			amount = amount_total = 0.0
			for invoice in payment_voucher.invoice_lines_ids:
				amount +=  invoice.amount_total_signed
				amount_total += invoice.amount_residual_signed
			payment_voucher.update({
				'amount': amount,
				'amount_total': amount_total		
			})	
	# @api.depends('move_line_ids.reconciled') #linkan pembelian ke po, ada nomor po, 
	#											# linkan pembelian ke penerimaan.
 #    def _get_move_reconciled(self):
 #        for payment in self:
 #            rec = True
 #            for aml in payment.move_line_ids.filtered(lambda x: x.account_id.reconcile):
 #                if not aml.reconciled:
 #                    rec = False
 #                    break
 #            payment.move_reconciled = rec

