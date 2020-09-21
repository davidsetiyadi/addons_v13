import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form
PURCHASE = [('or','Or'),('and','And')]

class GbrFilterData(models.TransientModel):
	_name = 'gbr.filter.data'
	_description = 'Gbr Filter Data'
	#Filter data pembayaran hutang

	confirm_date = fields.Datetime(string='Confirm Date Awal')
	confirm_date_end = fields.Datetime(string='Confirm Date Akhir')
	input_date = fields.Datetime(string='Input Date Awal')
	input_date_end = fields.Datetime(string='Input Date Akhir')
	mod_date = fields.Datetime(string='Change Date Awal')
	mod_date_end = fields.Datetime(string='Change Date Akhir')
	confirm_id = fields.Many2one('res.users', string='Konf Oleh')
	input_id = fields.Many2one('res.users', string='Input Oleh')
	mod_id = fields.Many2one('res.users', string='Ubah Oleh')
	is_konf = fields.Boolean('Belum Konfirmasi')
	type = fields.Selection(PURCHASE, string="Type",default='and',required=True)

	#prdouct item


	def button_action_and(self):
		self.write({'type':'and'})
		# return True
		return {
			"type": "ir.actions.do_nothing",
		}

	def button_action_or(self):
		self.write({'type':'or'})
		return {
			"type": "ir.actions.do_nothing",
		}

	def button_process(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 0
			if self.confirm_date:
				n += 1
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		# ['|',('payment_id', 'in', tuple(payment_ids) )]
		# domain = [('confirm_date', '>=',self.confirm_date)]
		return {
			'name': _('Pembayaran Hutang'),
			'view_mode': 'tree,form',
			'res_model': 'gbr.payment.voucher',
			'view_id': False,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_po(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_purchase_gbr', '=', True))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_purchase_gbr', '=', True))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		# ['|',('payment_id', 'in', tuple(payment_ids) )]
		# domain = [('confirm_date', '>=',self.confirm_date)]
		# context nya di isi
		context =	"{'form_view_ref': 'gbr_custom.view_purchase_order_gbr_form_view', "\
            		"			   'tree_view_ref': 'gbr_custom.view_purchase_order_gbr_tree_view', "\
            		"			   'disable_search':True,'search_view_ref': 'gbr_custom.purchase_order_view_search'}"

		return {
			'name': _('Purchase Order'),
			'view_mode': 'tree,form',
			'res_model': 'purchase.order',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}
	def button_process_pembelian(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_pembelian', '=', True))
			domain.append(('type', '=', 'in_invoice'))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_pembelian', '=', True))
			domain.append(('type', '=', 'in_invoice'))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		
		# context nya di isi
		context =	"{'default_type': 'in_invoice','default_is_pembelian': True, 'form_view_ref': 'gbr_custom.view_2_move_form', "\
					"'default_type_pembelian': 'credit','tree_view_ref': 'gbr_custom.view_invoice_2_tree', "\
					"'disable_search':True,'search_view_ref': 'gbr_custom.view_gbr_account_invoice_filter'}"

		return {
			'name': _('Pembelian'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_retur_pembelian(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_refund', '=', True))
			domain.append(('type', '=', 'in_refund'))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_refund', '=', True))
			domain.append(('type', '=', 'in_refund'))
			if self.confirm_date:
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		# context nya di isi
		context =	"{'default_type': 'in_refund','default_is_refund': True, 'form_view_ref': 'gbr_custom.view_3_move_form', "\
					"'default_type_code': 'retur_credit','tree_view_ref': 'gbr_custom.view_invoice_tree', "\
					"'disable_search':True,'search_view_ref': 'gbr_custom.view_account_invoice_filter'}"

		return {
			'name': _('Pembelian'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_partner(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_value', '=', True))
			domain.append(('is_semua_data', '=', True))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_value', '=', True))
			domain.append(('is_semua_data', '=', True))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		context =	"{'form_view_ref': 'gbr_custom.view_vendor_gbr_inherit_form', "\
            		"'default_is_value' : 1,	'default_supplier_rank': 1,'search_default_supplier': 1,'tree_view_ref': 'gbr_custom.view_vendor_gbr_inherit_tree', "\
            		"'default_is_company': True ,'default_country_id': 100,'disable_search':True,'search_view_ref': 'gbr_custom.view_gbr_res_partner_filter'}"

		return {
			'name': _('Vendor'),
			'view_mode': 'tree,form',
			'res_model': 'res.partner',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_pelanggan(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_customer', '=', True))
			domain.append(('is_semua_data', '=', True))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_customer', '=', True))
			domain.append(('is_semua_data', '=', True))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		context =	"{'form_view_ref': 'gbr_custom.view_pelanggan_gbr_form', "\
            		"'default_customer_rank': 1,'default_is_customer': 1, 'default_is_company': 1,'tree_view_ref': 'gbr_custom.view_pelanggan_gbr_tree', "\
            		"'search_default_customer': 1,'default_country_id': 100,'disable_search':True,'search_view_ref': 'gbr_custom.view_gbr_p_res_partner_filter'}"

		return {
			'name': _('Pelanggan'),
			'view_mode': 'tree,form',
			'res_model': 'res.partner',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_product(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_semua_data', '=', True))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_semua_data', '=', True))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		context =	"{'form_view_ref': 'gbr_custom.gbr_product_template_form_view', "\
            		"'search_default_consumable': 1, 'default_type': 'product','tree_view_ref': 'gbr_custom.product_product_tree_view', "\
            		"'quantity_available_locations_domain': ('internal',),'disable_search':True,'search_view_ref': 'gbr_custom.gbr_custom_product_search'}"

		return {
			'name': _('Item'),
			'view_mode': 'tree,form',
			'res_model': 'product.product',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_dn_p(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_debit_note_pembelian', '=', True))
			domain.append(('type', '=', 'in_refund'))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_debit_note_pembelian', '=', True))
			domain.append(('type', '=', 'in_refund'))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		# ['|',('payment_id', 'in', tuple(payment_ids) )]
		# domain = [('confirm_date', '>=',self.confirm_date)]
		# context nya di isi
		context =	"{'default_is_debit_note_pembelian': True,'default_type_code': 'debit_note','form_view_ref': 'gbr_custom.view_4_move_form', "\
            		"'tree_view_ref': 'gbr_custom.view_invoice_3_tree', "\
            		"'default_type': 'in_refund','disable_search':True,'search_view_ref': 'gbr_custom.view_account_invoice_filter'}"

		return {
			'name': _('Debit Note Hutang Pembelian'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_cn_p(self):
		# return ke form dengan filter yang sudha di buat tadi
		# return True
		domain = []
		if self.type == 'and':
			domain.append(('is_credit_note_pembelian', '=', True))
			domain.append(('type', '=', 'in_receipt'))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_credit_note_pembelian', '=', True))
			domain.append(('type', '=', 'in_receipt'))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		# ['|',('payment_id', 'in', tuple(payment_ids) )]
		# domain = [('confirm_date', '>=',self.confirm_date)]
		# context nya di isi
		context =	"{'default_is_credit_note_pembelian': True,'default_type_code': 'credit_note','form_view_ref': 'gbr_custom.view_4_move_form', "\
            		"'tree_view_ref': 'gbr_custom.view_invoice_3_tree', "\
            		"'default_type': 'in_receipt','disable_search':True,'search_view_ref': 'gbr_custom.view_account_invoice_filter'}"
		
		return {
			'name': _('Credit Note Hutang Pembelian'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_pv(self):
		domain = []
		if self.type == 'and':
			domain.append(('payment_type', '=', 'outbound'))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('payment_type', '=', 'outbound'))
			if self.confirm_date:
				n += 1
				if n != 0:
					domain.append('|')
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		
		context = "{'default_payment_type': 'outbound', "\
					"'default_partner_type': 'supplier',  "\
			 		"'res_partner_search_mode': 'supplier',  "\
			   		"'tree_view_ref': 'gbr_custom.view_gbr_account_payment_tree',  "\
			    	"'form_view_ref': 'gbr_custom.view_gbr_account_payment_form',  "\
			      	"'disable_search':True,'default_type_kas_keluar': 'DPPB',    "\
		       		"'default_type_code': 'deposit','search_view_ref':'gbr_custom.view_gbr_account_payment_search'}"
		return {
			'name': _('Deposit'),
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_quot(self):
		domain = []
		if self.type == 'and':
			domain.append(('is_quotation', '=', True))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 0
			domain.append(('is_quotation', '=', True))
			if self.confirm_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		context =	"{'tree_view_ref':'gbr_custom.view_quotation_gbr_tree',"\
					"'form_view_ref':'gbr_custom.view_quotation_gbr_form',"\
					"'default_is_quotation':True,'quot_seq':True,"\
					"'disable_search':True}"
		return {
			'name': _('Quotation'),
			'view_mode': 'tree,form',
			'res_model': 'sale.order',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_sale(self):
		domain = []
		if self.type == 'and':
			domain.append(('is_order', '=', True))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 0
			domain.append(('is_order', '=', True))
			if self.confirm_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		context =	"{'tree_view_ref':'gbr_custom.view_quotation_gbr_tree',"\
					"'form_view_ref':'gbr_custom.view_quotation_gbr_form',"\
					"'default_is_order':True,'sale_order_gbr':True,"\
					"'disable_search':True}"

		return {
			'name': _('Sale Order'),
			'view_mode': 'tree,form',
			'res_model': 'sale.order',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}

	def button_process_pen_ecrn(self):
		domain = []
		if self.type == 'and':
			domain.append(('is_penj_eceran', '=', True))
			domain.append(('type', '=', 'out_invoice'))
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))
		else:
			#cek berapa bnyak yang aktif.
			n = 1
			domain.append(('is_penj_eceran', '=', True))
			domain.append(('type', '=', 'out_invoice'))
			if self.confirm_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_date_end:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.confirm_id:		
				# print ('nnnnnnnnn',n)
				if n != 0:
					domain.append('|')
				n += 1
			if self.input_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.mod_id:				
				if n != 0:
					domain.append('|')
				n += 1
			if self.is_konf:
				if n != 0:
					domain.append('|')
				n += 1
			
			if self.confirm_date:
				domain.append(('confirm_date','>=',self.confirm_date))
			if self.confirm_date_end:
				domain.append(('confirm_date','<=',self.confirm_date_end))
			if self.input_date:
				domain.append(('create_date','>=',self.input_date))
			if self.input_date:
				domain.append(('create_date','<=',self.input_date_end))
			if self.mod_date:
				domain.append(('write_date','>=',self.mod_date))
			if self.mod_date_end:
				domain.append(('write_date','<=',self.mod_date_end))
			if self.confirm_id:
				domain.append(('confirm_id','=',self.confirm_id.id))
			if self.input_id:
				domain.append(('create_uid','=',self.input_id.id))
			if self.mod_id:
				domain.append(('write_uid','=',self.mod_id.id))
			if self.is_konf:
				domain.append(('confirm_id','=',False))

		context =	"{'default_is_penj_eceran':True,"\
					"'default_type': 'out_invoice',"\
					"'form_view_ref': 'gbr_custom.view_penj_04_move_form',"\
					"'default_partner_id.name': 'Cash','default_type_code': 'mm',"\
					"'disable_search':True}"
		return {
			'name': _('Sale Order'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'context': context,
			# 'target': 'new',
			'type': 'ir.actions.act_window',
			'domain': domain,
		}
