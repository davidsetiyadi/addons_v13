# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2004-2013 odoo S.A. (<http://odoo.com>).
#
#    Copyright (C) 2011-2015 Nevpro Business Solutions Pvt Ltd. (<http://www.nevpro.co.in>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import odoo
from odoo import api, fields, models, tools
from datetime import date,datetime,time,timedelta
from odoo import SUPERUSER_ID
from odoo.http import request
from odoo.tools.translate import _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo import http, tools
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.addons.portal.controllers.web import Home as HomePortal

_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# Odoo Web web Controllers
#----------------------------------------------------------

class Home(HomePortal):

	def _login_redirect(self, uid, redirect=None):
		return super()._login_redirect(uid, redirect)

	@http.route('/web/login', type='http', auth="none")
	def web_login(self, redirect=None, **kw):
		odoo.addons.web.controllers.main.ensure_db()

		request.params['login_success'] = False
		if request.httprequest.method == 'GET' and redirect and request.session.uid:
			return http.redirect_with_hash(redirect)

		if not request.uid:
			request.uid = odoo.SUPERUSER_ID

		values = request.params.copy()
		try:
			values['databases'] = http.db_list()
		except AccessDenied:
			values['databases'] = None

		if request.httprequest.method == 'POST':
			old_uid = request.uid
			try:
				uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
				request.params['login_success'] = True
				return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
			except AccessDenied as e:
				request.uid = old_uid
				if e.args == AccessDenied().args:
					values['error'] = "Login failed due to one of the following reasons"
					values['error2'] = "- Wrong login/password"
					values['error3'] = "- User already logged in from another system"
				else:
					values['error'] = e.args[0]
		else:
			if 'error' in request.params and request.params.get('error') == 'access':
				values['error'] = _('Only employee can access this database. Please contact the administrator.')

		if 'login' not in values and request.session.get('auth_login'):
			values['login'] = request.session.get('auth_login')

		if not odoo.tools.config['list_db']:
			values['disable_database_manager'] = True

		response = request.render('web.login', values)
		response.headers['X-Frame-Options'] = 'DENY'
		return response


# class Root_new(odoo.http.Root):
	
	
# 	def get_response(self, httprequest, result, explicit_session):
# 		if isinstance(result, Response) and result.is_qweb:
# 			try:
# 				result.flatten()
# 			except Exception as e:
# 				if request.db:
# 					result = request.registry['ir.http']._handle_exception(e)
# 				else:
# 					raise

# 		if isinstance(result, (bytes, str)):
# 			response = Response(result, mimetype='text/html')
# 		else:
# 			response = result

# 		save_session = (not request.endpoint) or request.endpoint.routing.get('save_session', True)
# 		if not save_session:
# 			return response

# 		if httprequest.session.should_save:
# 			if httprequest.session.rotate:
# 				self.session_store.delete(httprequest.session)
# 				httprequest.session.sid = self.session_store.generate_key()
# 				if httprequest.session.uid:
# 					httprequest.session.session_token = security.compute_session_token(httprequest.session, request.env)
# 				httprequest.session.modified = True
# 			self.session_store.save(httprequest.session)
	 
# 		if not explicit_session and hasattr(response, 'set_cookie'):
# 			response.set_cookie(
# 				'session_id', httprequest.session.sid, max_age=2* 60, httponly=True)

# 		return response

	

# root = Root_new()
# odoo.http.Root.get_response = root.get_response

class Users(models.Model):
	_inherit = "res.users"
		
	session_id = fields.Char(string='Session IDs', size=100)
	expiration_date = fields.Datetime('Expiration Dates')
	logged_in =  fields.Boolean('Logged ins')

	@classmethod
	def _login(cls, db, login, password):
		res = super(Users, cls)._login( db, login, password)
		if not password:
			raise AccessDenied()
		ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
		try:
			with cls.pool.cursor() as cr:
				self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
				session_id = request.httprequest.session.sid		
				temp_browse = self.browse(res)
				if isinstance(temp_browse, list): temp_browse = temp_browse[0]
				exp_date = temp_browse.expiration_date
				if exp_date and temp_browse.session_id:
					# real_date = time.strftime(exp_date)
					# exp_date = datetime.strptime(exp_date,"%Y-%m-%d %H:%M:%S")
					if exp_date < datetime.utcnow() or temp_browse.session_id != session_id:
						raise AccessDenied()
				temp_browse.save_session()
		except AccessDenied:
			user_id = False
			_logger.warn(	"User %s is already logged in into the system!", login)
			_logger.warn("Multiple sessions are not allowed for security reasons!")
			raise
		# finally:
		# 	cr.close()

		return res

		#clears session_id and session expiry from res.users
	def clear_session(self):
		# if isinstance(user_id, list): user_id = user_id[0]		
		self.sudo().write({'session_id':'','expiration_date':False,'logged_in':False})

	#insert session_id and session expiry into res.users
	def save_session(self):
		# if isinstance(user_id, list): user_id = user_id[0]
		
		exp_date = datetime.utcnow() + timedelta(minutes=2)
		sid = request.httprequest.session.sid
		self.sudo().write( {'session_id':sid,'expiration_date':exp_date,'logged_in':True})

	#schedular function to validate users session
	def validate_sessions(self):
		ids = self.env['res.users'].sudo().search([('expiration_date','!=',False)])
		# users = self.sudo().browse(cr, SUPERUSER_ID, ids)		
		for user_id in ids:			
			exp_date = user_id.expiration_date#datetime.strptime(user_id.expiration_date,"%Y-%m-%d %H:%M:%S")
			if exp_date < datetime.utcnow():
				user_id.clear_session()
