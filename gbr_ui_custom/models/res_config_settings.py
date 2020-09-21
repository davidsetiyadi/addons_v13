# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    top_menu_ids = fields.Many2many(related='company_id.top_menu_ids', readonly=False)