# -*- coding: utf-8 -*-
import json
import odoo
from odoo import http
from odoo.tools import ustr
from odoo.http import request
from odoo.addons.web.controllers.main import Home

CONTENT_MAXAGE = http.STATIC_CACHE_LONG

class Home(Home):
    @http.route('/web/webclient/load_top_menus/<string:unique>', type='http', auth='user', methods=['GET'])
    def web_load_top_menus(self, unique):
        menus = request.env["ir.ui.menu"].load_top_menus(request.session.debug)
        body = json.dumps(menus, default=ustr)
        response = request.make_response(body, [
            ('Content-Type', 'application/json'),
            ('Cache-Control', 'public, max-age=' + str(CONTENT_MAXAGE)),
        ])
        return response