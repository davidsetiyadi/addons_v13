# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = 'res.company'
    
    top_menu_ids = fields.Many2many(comodel_name='ir.ui.menu', 
        relation='company_top_menu_rel',
        column1='company_id',
        column2='menu_id',
        string='Top Menus')