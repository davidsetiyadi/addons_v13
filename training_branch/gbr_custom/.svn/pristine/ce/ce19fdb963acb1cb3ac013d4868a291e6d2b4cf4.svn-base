# -*- coding: utf-8 -*-

import copy
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import formatLang, format_date, parse_date


class AccountReconciliation(models.AbstractModel):
	_inherit = 'account.reconciliation.widget'

	@api.model
	def _domain_move_lines_for_manual_reconciliation(self, account_id, partner_id=False, excluded_ids=None, search_str=False):
		""" Create domain criteria that are relevant to manual reconciliation. """
		if not self.env.context.get('create_from_voucher_payment'):
			return super(AccountReconciliation, self)._domain_move_lines_for_manual_reconciliation(account_id, partner_id, excluded_ids,search_str )

		domain = ['&', '&', ('reconciled', '=', False), ('account_id', '=', account_id), '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('move_id.journal_id.post_at', '=', 'bank_rec')]
		if partner_id:
			domain = expression.AND([domain, [('partner_id', '=', partner_id)]])
		if excluded_ids:
			domain = expression.AND([[('id', 'not in', excluded_ids)], domain])
		if search_str:
			str_domain = self._domain_move_lines(search_str=search_str)
			domain = expression.AND([domain, str_domain])
		# filter on account.move.line having the same company as the given account
		account = self.env['account.account'].browse(account_id)
		domain = expression.AND([domain, [('company_id', '=', account.company_id.id)]])
		if self._context.get('create_from_voucher_payment'):
			if len(self._context.get('payment_move_ids')) == 1:
				domain = expression.AND([domain, [('move_id', '=', self._context.get('payment_move_ids') )]])
			if len(self._context.get('payment_move_ids')) > 1:
				domain = expression.AND([domain, [('move_id', 'in', tuple(self._context.get('payment_move_ids')) )]])
		
		return domain


