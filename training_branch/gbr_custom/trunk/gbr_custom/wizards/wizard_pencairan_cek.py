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



class GbrPencairan(models.TransientModel):
	"""
	Account move reversal wizard, it cancel an account move by reversing it.
	"""
	_name = 'gbr.pencairan'
	_description = 'GBR Pencairan'

	move_id = fields.Many2one('account.move', string='Journal Entry',
		domain=[('state', '=', 'posted'), ('type', 'not in', ('out_refund', 'in_refund'))])
	date = fields.Date(string='Tanggal', default=fields.Date.context_today, required=True)
	tanggal_char	= fields.Char('Tanggal Char',readonly=True,compute='get_tanggal_char') 
	reason = fields.Char(string='Reason')   
	journal_id = fields.Many2one('account.journal', string='Cair Ke', required=True)
	source_acc_id = fields.Many2one('account.account', string='Source', compute='get_account')
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
	
	@api.depends('date')
	def get_tanggal_char(self):
		for payment in self:	
			tanggal_char = ''			
			if payment.date:
				date_format = '%A, %d %B %Y'
				locale.setlocale(locale.LC_ALL, ('id_ID','UTF-8') )
				tanggal_chars = payment.date.strftime(date_format)
				tanggal_char = str(tanggal_chars)
			payment.update({
				'tanggal_char': tanggal_char,
				})	
	@api.depends('journal_id')
	def get_account(self):
		for payment in self:	
			source_acc_id = False
			destination_acc_id = False
			if payment.journal_id:
				source_acc_id = payment.journal_id.default_credit_account_id.id
			
			payment.update({
				'source_acc_id': source_acc_id,
				})	

	def reverse_moves(self):
		# moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id
		gbr_line = self.env['gbr.pencairan.cek.line'].browse(self.env.context['active_ids'])
		move_line = gbr_line.move_line_id
		AccountMove = self.env['account.move'].with_context(default_type='entry')
		name = 'Pencairan CH/BG: %s' % str(gbr_line.name)	
		move_vals = {
			    'date': self.date,
			    'ref': self.reason,
			    'journal_id': self.journal_id.id,
			    'currency_id': self.journal_id.currency_id.id or self.company_id.currency_id.id,

			    'partner_id': gbr_line.partner_id.id,
			    'line_ids': [
			        # Receivable / Payable / Transfer line.
			        # Credit ke Cek IDR 
			        # Debit ke BANK
			        (0, 0, {
			            'name': name ,
			            'amount_currency': abs(move_line.amount_currency),
			            'currency_id': False,#self.journal_id.currency_id.id or self.company_id.currency_id.id,
			            'quantity': 1,
			            'sequence': 10,
			            'display_type': False,
			            'debit': move_line.debit,
			            'credit': 0.0,
			            'date_maturity': self.date,
			            'partner_id': gbr_line.partner_id.id,
			            'account_id': self.journal_id.default_debit_account_id.id,
			            # 'payment_id': payment.id,
			        }),
			        # Liquidity line.
			        (0, 0, {
			            'name': name,
			            'amount_currency': - move_line.amount_currency,
			            'currency_id': False,#self.journal_id.currency_id.id or self.company_id.currency_id.id,
			            'quantity': 1,
			            'sequence': 10,
			            'display_type': False,
			            'debit': 0.0,
			            'credit': move_line.debit,
			            'date_maturity': self.date,
			            'partner_id': gbr_line.partner_id.id,
			            'account_id': move_line.account_id.id,
			            'is_pencairan_cek': True,
			            # 'payment_id': payment.id,
			        }),
			    ],
			}

		moves = AccountMove.create(move_vals)
		moves._check_balanced()
		moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
		
		for line in moves.line_ids:
			if line.account_id.id == move_line.account_id.id:
				(move_line + line ).reconcile()
				break
		
		# account_move_line = self.env['account.move.line'].browse(554)
		# (account_move_line + move_line).reconcile()


		active_ids = self.env.context['active_ids']
		account_idss = []
		account_obj = self.env['account.account']
		account_line_obj = self.env['account.move.line']
		gbr_line_obj = self.env['gbr.pencairan.cek.line']
		gbr_obj = self.env['gbr.pencairan.cek']
		account_ids = account_obj.search([('gol_check_bg','=','yes')])
		pencairan_data = []
		# full_reconcile_id
		# cari account move line
		for account in account_ids:
			account_idss.append(account.id)

		if len(account_ids) > 1 :
			account_move_line_ids = account_line_obj.search([('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','in',tuple(account_idss) ),('debit','>',0)])
		else:
			account_move_line_ids = account_line_obj.search([('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','=',account_ids[0].id),('debit','>',0)])
		
		# 	
		gbr_pencairan_id = gbr_obj.search([],limit=1)
		gbr_line = gbr_line_obj.search([('pencairan_id','=',gbr_pencairan_id.id)])
		
		gbr_line.unlink()
		
		for move_line in account_move_line_ids:
			pencairan_ids =  {
					'name'			: move_line.name,
					'db_cr'			: 'DB',
					'amount' 		: move_line.debit,
					'discount'		: 0,
					'nilai_jual'	: move_line.debit,
					'perkiraan'		: move_line.account_id.id,					
					'partner_id'	: move_line.partner_id.id,
					'date'			: move_line.date,
					'move_line_id'	: move_line.id,
							}
			pencairan_data.append((0,0,pencairan_ids))

		# gbr = gbr_obj.browse(gbr_pencairan_id.id)
		# gbr_pencairan_id.write({'pencairan_ids': pencairan_data ,})	#show blank page
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'gbr.pencairan.cek',
			'res_id': gbr_pencairan_id.id,
			'view_id': self.env.ref('gbr_custom.wizard_gbr_pencairan_cek_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	def reverse_moves2(self):
		# moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id
		gbr_line = self.env['gbr.pencairan.cek.line'].browse(self.env.context['active_ids'])
		move_line = gbr_line.move_line_id
		AccountMove = self.env['account.move'].with_context(default_type='entry')
		name = 'Pencairan CH/BG: %s' % str(gbr_line.name)	
		move_vals = {
			    'date': self.date,
			    'ref': self.reason,
			    'journal_id': self.journal_id.id,
			    'currency_id': self.journal_id.currency_id.id or self.company_id.currency_id.id,

			    'partner_id': gbr_line.partner_id.id,
			    'line_ids': [
			        # Receivable / Payable / Transfer line.
			        # Kas Keluar
			        # Debit ke Cek IDR 
			        # Credit ke BANK
			        (0, 0, {
			            'name': name ,
			            'amount_currency': abs(move_line.amount_currency),
			            'currency_id': False,#self.journal_id.currency_id.id or self.company_id.currency_id.id,
			            'quantity': 1,
			            'sequence': 10,
			            'display_type': False,
			            'credit': move_line.credit,
			            'debit': 0.0,
			            'date_maturity': self.date,
			            'partner_id': gbr_line.partner_id.id,
			            'account_id': self.journal_id.default_debit_account_id.id,
			            # 'payment_id': payment.id,
			        }),
			        # Liquidity line.
			        (0, 0, {
			            'name': name,
			            'amount_currency': - move_line.amount_currency,
			            'currency_id': False,#self.journal_id.currency_id.id or self.company_id.currency_id.id,
			            'quantity': 1,
			            'sequence': 10,
			            'display_type': False,
			            'credit': 0.0,
			            'debit': move_line.credit,
			            'date_maturity': self.date,
			            'partner_id': gbr_line.partner_id.id,
			            'account_id': move_line.account_id.id,
			            'is_pencairan_cek': True,
			            # 'payment_id': payment.id,
			        }),
			    ],
			}

		moves = AccountMove.create(move_vals)
		moves._check_balanced()
		moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
		
		for line in moves.line_ids:
			if line.account_id.id == move_line.account_id.id:
				(move_line + line ).reconcile()
				break
		
		# account_move_line = self.env['account.move.line'].browse(554)
		# (account_move_line + move_line).reconcile()


		active_ids = self.env.context['active_ids']
		account_idss = []
		account_obj = self.env['account.account']
		account_line_obj = self.env['account.move.line']
		gbr_line_obj = self.env['gbr.pencairan.cek.line']
		gbr_obj = self.env['gbr.pencairan.cek']
		account_ids = account_obj.search([('gol_check_bg','=','yes')])
		pencairan_data = []
		# full_reconcile_id
		# cari account move line
		for account in account_ids:
			account_idss.append(account.id)

		if len(account_ids) > 1 :
			account_move_line_ids = account_line_obj.search([('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','in',tuple(account_idss) ),('credit','>',0)])
		else:
			account_move_line_ids = account_line_obj.search([('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','=',account_ids[0].id),('credit','>',0)])
		
		
		gbr_pencairan_id = gbr_obj.search([],limit=1)
		gbr_line = gbr_line_obj.search([('pencairan_id','=',gbr_pencairan_id.id)])
		
		gbr_line.unlink()
		
		for move_line in account_move_line_ids:
			pencairan_ids =  {
					'name'			: move_line.name,
					'db_cr'			: 'DB',
					'amount' 		: move_line.debit,
					'discount'		: 0,
					'nilai_jual'	: move_line.debit,
					'perkiraan'		: move_line.account_id.id,					
					'partner_id'	: move_line.partner_id.id,
					'date'			: move_line.date,
					'move_line_id'	: move_line.id,
							}
			pencairan_data.append((0,0,pencairan_ids))

		# gbr = gbr_obj.browse(gbr_pencairan_id.id)
		# gbr_pencairan_id.write({'pencairan_ids': pencairan_data ,})	#show blank page
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'gbr.pencairan.cek',
			'res_id': gbr_pencairan_id.id,
			'view_id': self.env.ref('gbr_custom.wizard_gbr_pencairan_cek2_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}


class GbrPencairanCek(models.TransientModel):
	_name = "gbr.pencairan.cek"
	_description = "Pencairan Cek"

	name = fields.Char('Name')
	type = fields.Char('Type')
	date_start = fields.Date('Tanggal Awal',default=fields.Date.context_today)
	date_end = fields.Date('Tanggal Akhir',default=fields.Date.context_today)
	date_start2 = fields.Date('Tanggal Awal 2',default=fields.Date.context_today)
	date_end2 = fields.Date('Tanggal Akhir 2',default=fields.Date.context_today)
	cari_1 = fields.Char('Cari CH/BG')
	cari_2 = fields.Char('Cari CH/BG 2')
	pencairan_ids = fields.One2many('gbr.pencairan.cek.line','pencairan_id', string="Pencairan")
	pencairan_lns_id = fields.One2many('gbr.pencairan.cek.line','pencairan_lns_id', string="Pencairan 2")
	
	def button_search(self):		#
		account_idss = []
		account_obj = self.env['account.account']
		account_line_obj = self.env['account.move.line']
		gbr_line_obj = self.env['gbr.pencairan.cek.line']
		account_ids = account_obj.search([('gol_check_bg','=','yes')])
		pencairan_data = []
		pencairan2_data = []	
		# full_reconcile_id
		# cari account move line
		for account in account_ids:
			account_idss.append(account.id)

		if len(account_ids) > 1 :
			account_move_line_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start),('date','<=',self.date_end),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','in',tuple(account_idss) ),('debit','>',0)])
			account_move_line2_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start2),('date','<=',self.date_end2),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','!=',False),('account_id','in',tuple(account_idss) ),('debit','>',0)])
		else:
			account_move_line_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start),('date','<=',self.date_end),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','=',account_ids[0].id),('debit','>',0)])
			account_move_line2_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start2),('date','<=',self.date_end2),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','!=',False),('account_id','=',account_ids[0].id),('debit','>',0)])
		
		gbr_line = gbr_line_obj.search(['|',('pencairan_lns_id','=',self.id),('pencairan_id','=',self.id)])
		gbr_line.unlink()
		for move_line in account_move_line_ids:
			pencairan_ids =  {
					'name'	: move_line.name,
					'db_cr'		: 'DB',
					'amount' 	: move_line.debit,
					'discount'		: 0,
					'nilai_jual'	: move_line.debit,
					'perkiraan': move_line.account_id.id,
					
					'partner_id': move_line.partner_id.id,
					'date': move_line.date,
					'move_line_id': move_line.id,
							}
			pencairan_data.append((0,0,pencairan_ids))

		for move_line in account_move_line2_ids:
			pencairan2_ids =  {
					'name'	: move_line.name,
					'db_cr'		: 'DB',
					'amount' 	: move_line.debit,
					'discount'		: 0,
					'nilai_jual'	: move_line.debit,
					'perkiraan': move_line.account_id.id,
					'full_reconcile_id': move_line.full_reconcile_id.id,
					'partner_id': move_line.partner_id.id,
					'date': move_line.date,
					'move_line_id': move_line.id,
							}
			pencairan2_data.append((0,0,pencairan2_ids))

		self.write({'pencairan_ids': pencairan_data ,'pencairan_lns_id': pencairan2_data})	
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'gbr.pencairan.cek',
			'res_id': self.id,
			'view_id': self.env.ref('gbr_custom.wizard_gbr_pencairan_cek_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	def button_search_2(self):
		
		account_idss = []
		account_obj = self.env['account.account']
		account_line_obj = self.env['account.move.line']
		gbr_line_obj = self.env['gbr.pencairan.cek.line']
		account_ids = account_obj.search([('gol_check_bg','=','yes')])
		pencairan_data = []
		pencairan2_data = []	
		# full_reconcile_id
		# cari account move line
		for account in account_ids:
			account_idss.append(account.id)

		if len(account_ids) > 1 :
			account_move_line_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start),('date','<=',self.date_end),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','in',tuple(account_idss) ),('credit','>',0)])
			account_move_line2_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start2),('date','<=',self.date_end2),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','!=',False),('account_id','in',tuple(account_idss) ),('credit','>',0)])
		else:
			account_move_line_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start),('date','<=',self.date_end),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','=',account_ids[0].id),('credit','>',0)])
			account_move_line2_ids = account_line_obj.search([('is_pencairan_cek','!=',True),('date','>=',self.date_start2),('date','<=',self.date_end2),('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','!=',False),('account_id','=',account_ids[0].id),('credit','>',0)])
		
		gbr_line = gbr_line_obj.search(['|',('pencairan_lns_id','=',self.id),('pencairan_id','=',self.id)])
		gbr_line.unlink()
		for move_line in account_move_line_ids:
			pencairan_ids =  {
					'name'	: move_line.name,
					'db_cr'		: 'DB',
					'amount' 	: move_line.credit,
					'discount'		: 0,
					'nilai_jual'	: move_line.credit,
					'perkiraan': move_line.account_id.id,
					
					'partner_id': move_line.partner_id.id,
					'date': move_line.date,
					'move_line_id': move_line.id,
							}
			pencairan_data.append((0,0,pencairan_ids))

		for move_line in account_move_line2_ids:
			pencairan2_ids =  {
					'name'	: move_line.name,
					'db_cr'		: 'DB',
					'amount' 	: move_line.credit,
					'discount'		: 0,
					'nilai_jual'	: move_line.credit,
					'perkiraan': move_line.account_id.id,
					'full_reconcile_id': move_line.full_reconcile_id.id,
					'partner_id': move_line.partner_id.id,
					'date': move_line.date,
					'move_line_id': move_line.id,
							}
			pencairan2_data.append((0,0,pencairan2_ids))

		self.write({'pencairan_ids': pencairan_data ,'pencairan_lns_id': pencairan2_data})	
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'gbr.pencairan.cek',
			'res_id': self.id,
			'view_id': self.env.ref('gbr_custom.wizard_gbr_pencairan_cek2_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

class GbrPencairanCekLine(models.TransientModel):
	_name = 'gbr.pencairan.cek.line'
	_description = 'Pencairan Cek Line'

	name = fields.Char('Note')
	pencairan_id = fields.Many2one('gbr.pencairan.cek', string="Pencairan")
	pencairan_lns_id = fields.Many2one('gbr.pencairan.cek', string="Pencairan 2")
	is_selected = fields.Boolean('Select')
	db_cr = fields.Char('DB/CR')	
	date = fields.Date('Tanggal')
	partner_id = fields.Many2one('res.partner' ,'Vendor/Pelanggan')
	currency_id = fields.Many2one('res.currency' , string='MU')
	amount = fields.Float('Nilai')
	discount = fields.Float('Discount')
	nilai_jual =fields.Float('Nilai Jual')
	perkiraan = fields.Many2one('account.account', 'Perkiraan')
	information = fields.Char('Information')
	tgl_cair = fields.Date('Tgl Cair')
	partner2_id = fields.Many2one('res.partner' ,'Cair Ke')
	move_line_id = fields.Many2one('account.move.line', 'Move Line')
	full_reconcile_id = fields.Many2one('account.full.reconcile', 'Reconcile')

	def button_reconcile(self):
		action = self.env.ref('gbr_custom.action_view_gbr_pencairan').read()[0]
		return action

	def button_reconcile2(self):
		action = self.env.ref('gbr_custom.action_view_gbr_pencairan2').read()[0]
		return action
	
	def button_cancel(self):
		# cari lawan transaksi nya lalu unlink

		# button_draft
		# button_cancel


		active_ids = self.env.context['active_ids']
		account_idss = []
		account_obj = self.env['account.account']
		account_line_obj = self.env['account.move.line']
		gbr_line_obj = self.env['gbr.pencairan.cek.line']
		gbr_obj = self.env['gbr.pencairan.cek']
		account_ids = account_obj.search([('gol_check_bg','=','yes')])
		pencairan_data = []
		# full_reconcile_id
		# cari account move line

		account_move_line_ids = account_line_obj.search([('full_reconcile_id','=',self.full_reconcile_id.id),('id','!=',self.move_line_id.id)])
		for move_line in account_move_line_ids:
			move_line.move_id.button_draft()
			move_line.move_id.button_cancel()

		for account in account_ids:
			account_idss.append(account.id)

		if len(account_ids) > 1 :
			account_move_line_ids = account_line_obj.search([('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','in',tuple(account_idss) ),('debit','>',0)])
		else:
			account_move_line_ids = account_line_obj.search([('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','=',account_ids[0].id),('debit','>',0)])
		

		gbr_pencairan_id = gbr_obj.search([],limit=1)
		# gbr_line = gbr_line_obj.search([])
		gbr_line = gbr_line_obj.search([('pencairan_id','=',gbr_pencairan_id.id)])
		
		gbr_line.unlink()

		for move_line in account_move_line_ids:
			pencairan_ids =  {
				'name'			: move_line.name,
				'db_cr'			: 'DB',
				'amount' 		: move_line.debit,
				'discount'		: 0,
				'nilai_jual'	: move_line.debit,
				'perkiraan'		: move_line.account_id.id,					
				'partner_id'	: move_line.partner_id.id,
				'date'			: move_line.date,
				'move_line_id'	: move_line.id,
							}
			pencairan_data.append((0,0,pencairan_ids))

		# gbr = gbr_obj.browse(gbr_pencairan_id.id)
		# gbr_pencairan_id.write({'pencairan_ids': pencairan_data ,})	#show blank page
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'gbr.pencairan.cek',
			'res_id': gbr_pencairan_id.id,
			'view_id': self.env.ref('gbr_custom.wizard_gbr_pencairan_cek_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	def button_cancel2(self):
		# cari lawan transaksi nya lalu unlink

		# button_draft
		# button_cancel


		active_ids = self.env.context['active_ids']
		account_idss = []
		account_obj = self.env['account.account']
		account_line_obj = self.env['account.move.line']
		gbr_line_obj = self.env['gbr.pencairan.cek.line']
		gbr_obj = self.env['gbr.pencairan.cek']
		account_ids = account_obj.search([('gol_check_bg','=','yes')])
		pencairan_data = []
		# full_reconcile_id
		# cari account move line

		account_move_line_ids = account_line_obj.search([('full_reconcile_id','=',self.full_reconcile_id.id),('id','!=',self.move_line_id.id)])
		for move_line in account_move_line_ids:
			move_line.move_id.button_draft()
			move_line.move_id.button_cancel()

		for account in account_ids:
			account_idss.append(account.id)

		if len(account_ids) > 1 :
			account_move_line_ids = account_line_obj.search([('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','in',tuple(account_idss) ),('debit','>',0)])
		else:
			account_move_line_ids = account_line_obj.search([('parent_state','=','posted'),('partner_id','!=',False),('full_reconcile_id','=',False),('account_id','=',account_ids[0].id),('debit','>',0)])
		
		
		gbr_pencairan_id = gbr_obj.search([],limit=1)
		gbr_line = gbr_line_obj.search([('pencairan_id','=',gbr_pencairan_id.id)])
		
		gbr_line.unlink()
		
		for move_line in account_move_line_ids:
			pencairan_ids =  {
				'name'			: move_line.name,
				'db_cr'			: 'DB',
				'amount' 		: move_line.debit,
				'discount'		: 0,
				'nilai_jual'	: move_line.debit,
				'perkiraan'		: move_line.account_id.id,					
				'partner_id'	: move_line.partner_id.id,
				'date'			: move_line.date,
				'move_line_id'	: move_line.id,
							}
			pencairan_data.append((0,0,pencairan_ids))

		# gbr = gbr_obj.browse(gbr_pencairan_id.id)
		# gbr_pencairan_id.write({'pencairan_ids': pencairan_data ,})	#show blank page
		# return {
	 #        "type": "ir.actions.do_nothing",
	 #    }
		return {
			'name': _('Filter'),
			'context': self.env.context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'gbr.pencairan.cek',
			'res_id': gbr_pencairan_id.id,
			'view_id': self.env.ref('gbr_custom.wizard_gbr_pencairan_cek2_form').id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}