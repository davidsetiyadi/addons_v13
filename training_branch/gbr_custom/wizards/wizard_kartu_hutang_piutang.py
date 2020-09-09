# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re
from datetime import timedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import datetime

from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class GbrKartuHutangPiutang(models.TransientModel):
	_name = "gbr.kartu.hutang.piutang"
	_description = "Grouping Kartu Hutang Piutang"

	name = fields.Char('Name')
	tanggal_awal = fields.Date('Tanggal Awal')
	tanggal_akhir = fields.Date('Tanggal Akhir')
	vendor_id = fields.Many2one('res.partner', 'Vendor')
	pelanggan_id = fields.Many2one('res.partner', 'Pelanggan')
	divisi_id = fields.Many2one('gbr.divisi', string='Divisi')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
	is_pembelian_credit = fields.Boolean('Pembelian Credit',default=True)
	is_rtr_pembelian_credit = fields.Boolean('Retur Pembelian Credit',default=True)
	is_debet_credit_note = fields.Boolean('Debet/Credit Note',default=True)
	is_deposit = fields.Boolean('Deposit',default=True)
	is_invoice_statement = fields.Boolean('Invoice Statement',default=True)
	is_penjualan_credit = fields.Boolean('Penjualan Credit',default=True)
	is_retur_penjualan_credit = fields.Boolean('Retur Penjualan Credit',default=True)


	def open_partner_ledger(self):
		return {
			'type': 'ir.actions.client',
			'name': _('Partner Ledger'),
			'tag': 'account_report',
			'options': {'partner_ids': [self.vendor_id.id]},
			'ignore_session': 'both',
			'context': "{'model':'account.partner.ledger'}"
		}
		
	def open_partner_ledger2(self):
		return {
			'type': 'ir.actions.client',
			'name': _('Partner Ledger'),
			'tag': 'account_report',
			'options': {'partner_ids': [self.pelanggan_id.id]},
			'ignore_session': 'both',
			'context': "{'model':'account.partner.ledger'}"
		}

