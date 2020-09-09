# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import psycopg2
import werkzeug

from werkzeug import url_encode

from odoo import api, http, registry, SUPERUSER_ID, _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq

_logger = logging.getLogger(__name__)

def urlplus(url, params):
	return werkzeug.Href(url)(params or None)

class GBR_CustomController(http.Controller): 

	@http.route('/gbr_menu/get_action', type='http', auth='user', website=True)
	def groups_tokens(self, group_id=False, pm_id=None, **kwargs):
		# order = request.env['sale.order'].sudo().browse(order_id)
		# if not order: 702 620

		# return request.redirect("/my/orders")
		# http://192.168.56.102:8069/gbr_menu/get_action?order_id=%27test%27&pm_id=%27ssdsd%27
		if group_id == 'product':
			# cari action id = groups 
			# cari action menu_id = grouping
			action = request.env['ir.actions.actions'].search([('name','=','Grouping Item'),('type','=','ir.actions.act_window')])[0]# Grouping Product
			menu_id = request.env['ir.ui.menu'].search([('name','=','Grouping Item')])[0] #616 action=698&cids=1&menu_id=616
			# menu_id  		
			return request.redirect("/web#action=%s&cids=1&menu_id=%s"% (action.id,menu_id.id) ) 
		if group_id == 'vendor':
			action = request.env['ir.actions.actions'].search([('name','=','Grouping Vendor'),('type','=','ir.actions.act_window')])[0]# Grouping Product
			menu_id = request.env['ir.ui.menu'].search([('name','=','Grouping Vendor')])[0] #616 action=698&cids=1&menu_id=616
			# menu_id  		
			return request.redirect("/web#action=%s&cids=1&menu_id=%s"% (action.id,menu_id.id) ) 
		if group_id == 'pelanggan':
			action = request.env['ir.actions.actions'].search([('name','=','Grouping Pelanggan'),('type','=','ir.actions.act_window')])[0]# Grouping Product
			menu_id = request.env['ir.ui.menu'].search([('name','=','Grouping Pelanggan')])[0] #616 action=698&cids=1&menu_id=616
			# menu_id  		
			return request.redirect("/web#action=%s&cids=1&menu_id=%s"% (action.id,menu_id.id) )

		return request.redirect("/web#action=698&cids=1&menu_id=616")
								#menu_id=616&action=698
	# def gbr_menu_groups_1(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
	# 	context = {} #dict(self.env.context or {})
	# 	return request.redirect("/my/orders")
	# 	return request.redirect('/web#action=322&cids=1&menu_id=214')
	# 	return werkzeug.Href('http://192.168.56.102:8069/web#action=322&cids=1&menu_id=214')(None)
	# 	action = {
	# 			'name': _('Cash Control'),
	# 			'view_mode': 'tree',
	# 			'res_model': 'gbr.group.1',
	# 			'view_id': False,
	# 			# 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox_footer').id,
	# 			'type': 'ir.actions.act_window',
	# 			'res_id': 1,
	# 			'context': context,
	# 			'target': 'new'
	# 		}

	# 	return action
			
	# def gbr_get_data_info(self, model, res_id, **kw):
		# print("kwkwkwdsdsdsdsdsdsdsd",kw)
		# return True
		# Env = request.env

		# action  = {}
		# rec = request.env[model].browse(res_id)
		# print("recrec",rec)
		# if rec:
		#     if rec.is_credit_to_cost:
		#         action = Env.ref('ihotel_custom.ihotel_action_stock_picking_cost_switch').read()[0]
		#     if rec.is_transfer:
		#         action = Env.ref('ihotel_custom.ihotel_stock_picking_action_picking_type').read()[0]
		#     if rec.is_issuing:
		#         action = Env.ref('ihotel_custom.ihotel_action_stock_picking_issuing').read()[0]
		#     if rec.is_inventory_cost_switch:
		#         action = Env.ref('ihotel_custom.ihotel_action_stock_picking_cost_switch').read()[0]

		# return action
