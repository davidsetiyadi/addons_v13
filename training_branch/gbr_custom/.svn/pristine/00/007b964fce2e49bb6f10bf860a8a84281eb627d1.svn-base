# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import get_lang


class PricelistItem(models.Model):
	_inherit = "product.pricelist.item"
	_description = "Pricelist Rule"

	base = fields.Selection(selection_add=[
		('list_price', 'Sales Price'),
		('standard_price', 'Cost'),
		('buying_price', 'Buying Price'),
		('sale_price', 'Harga Jual *1'),
		('sale_price_2', 'Harga Jual *2'),
		('sale_price_3', 'Harga Jual *3'),
		('sale_price_4', 'Harga Jual *4'),
		('sale_price_5', 'Harga Jual *5'),
		('pricelist', 'Other Pricelist')])
	