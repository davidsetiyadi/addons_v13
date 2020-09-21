import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form
PURCHASE = [('hpp','Laporan Harga Pokok dan Total Transaksi'),('pembelian','Laporan Total Pembelian dan Hutang'),('penjualan','Laporan Total Penjualan dan Piutang')]

class GbrProsesLaporan(models.TransientModel):
	_name = 'gbr.proses.laporan'
	_description = 'Gbr Proses Laporan'

	start_date = fields.Datetime(string='Tanggal Awal')
	end_date = fields.Datetime(string='Tanggal Akhir')

	last_process_date = fields.Datetime(string='Terakhir Proses')
	state = fields.Selection(PURCHASE, string="Kelompok Laporan",default='hpp')

# <record id="action_account_report_ar" model="ir.actions.client">
#             <field name="name">Aged Receivable</field>
#             <field name="tag">account_report</field>
#             <field name="context" eval="{'model': 'account.aged.receivable'}" />
#         </record>
#         <record id="action_account_report_ap" model="ir.actions.client">
#             <field name="name">Aged Payable</field>
#             <field name="tag">account_report</field>
#             <field name="context" eval="{'model': 'account.aged.payable'}" />
#         </record>
	def button_laporan(self):
		if self.state == 'penjualan':
			return {
			'type': 'ir.actions.client',
			'name': _('Partner Ledger'),
			'tag': 'account_report',
			'options': {'partner_ids': [self.vendor_id.id]},
			'ignore_session': 'both',
			'context': "{'model':'account.partner.ledger'}"
			}
		elif self.state == 'pembelian':
			return {
			'type': 'ir.actions.client',
			'name': _('Partner Ledger'),
			'tag': 'account_report',
			'options': {'partner_ids': [self.pelanggan_id.id]},
			'ignore_session': 'both',
			'context': "{'model':'account.partner.ledger'}"
		}
		
	# def open_partner_ledger2(self):
	# 	return {
	# 		'type': 'ir.actions.client',
	# 		'name': _('Partner Ledger'),
	# 		'tag': 'account_report',
	# 		'options': {'partner_ids': [self.pelanggan_id.id]},
	# 		'ignore_session': 'both',
	# 		'context': "{'model':'account.partner.ledger'}"
	# 	}