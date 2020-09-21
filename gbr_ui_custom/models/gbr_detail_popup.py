# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class GbrDetailPopup(models.Model):
    _name = 'gbr.detail.popup'

    @api.model
    def create(self, vals):
        model_id = vals.get('popup_model_id', False)
        related_field = vals.get('related_field', False)
        if model_id and related_field:
            field_exist = self.env['ir.model.fields'].search_count([('model_id', '=', model_id), ('name', '=', related_field)])
            if not field_exist:
                raise UserError(_('Related field does not exist, please recheck.'))

        return super(GbrDetailPopup, self).create(vals)

    def write(self, vals):
        model_id = vals.get('popup_model_id', self.popup_model_id.id)
        related_field = vals.get('related_field', self.related_field)
        if model_id and related_field:
            field_exist = self.env['ir.model.fields'].search_count([('model_id', '=', model_id), ('name', '=', related_field)])
            if not field_exist:
                raise UserError(_('Related field does not exist, please recheck.'))

        return super(GbrDetailPopup, self).write(vals)

    @api.onchange('name')
    def _onchange_name(self):
        for detail in self:
            if not detail.title:
                detail.title = detail.name

    @api.onchange('popup_model_id')
    def _onchange_view_id(self):
        view_obj = self.env['ir.ui.view']
        for detail in self:
            detail.view_id = False
            if detail.popup_model_id:
                view = view_obj.search([('type', '=', 'tree'), ('model', '=', detail.popup_model_id.model), ('inherit_id', '=', False)], limit=1)
                detail.view_id = view and view.id or False

    name = fields.Char('Button Name')
    title = fields.Char('Popup Title')
    src_model_id = fields.Many2one('ir.model', 'Source Model')
    src_model = fields.Char(related='src_model_id.model', string='Source Model ID')
    popup_model_id = fields.Many2one('ir.model', 'Popup Model')
    popup_model = fields.Char(related='popup_model_id.model', string='Popup Model ID')
    view_id = fields.Many2one('ir.ui.view', string='View')
    related_field = fields.Char('Related Field')