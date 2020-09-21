odoo.define('gbr_ui_custom.ListRenderer', function (require) {
"use strict";
    var ListRenderer = require('web.ListRenderer');
    var Dialog = require('web.Dialog');
    var view_dialogs = require('web.view_dialogs');
    var view_registry = require('web.view_registry');
    var dom = require('web.dom');
    var core = require('web.core');
    var _t = core._t;

    ListRenderer.include({
        _onRowClicked: function (ev) {
            // The special_click property explicitely allow events to bubble all
            // the way up to bootstrap's level rather than being stopped earlier.
            var self = this;
            if (!ev.target.closest('.o_list_record_selector') && !$(ev.target).prop('special_click')) {
                var id = $(ev.currentTarget).data('id');
                if (id) {
                    var parent = this.getParent(),
                        currentPopup = parent.currentPopup;
                    if(parent.isDetailPopup){
                        core.bus.trigger('close_dialogs');
                        var data = this._getRecord(id);
                        var fragment = document.createDocumentFragment();
                        var dialog = new Dialog(this, {
                            title: currentPopup.title,
                            size: 'medium',
                            buttons: [{text: 'Close', close: true}],
                            renderHeader: true,
                            renderFooter: false,
                            backdrop: false,
                            focus: false
                        });
                        self.loadViews(currentPopup.popup_model, self.state.context, [[currentPopup.view_id[0], 'list']], {}).then(function(fieldsViews){
                            var ViewClass = view_registry.get('list');
                            var view = new ViewClass(fieldsViews['list'], {
                                hasSelectors: false,
                                readonly: true,
                                action_buttons: false,
                                domain: [[currentPopup.related_field, '=', data.res_id]],
                                modelName: currentPopup.popup_model,
                                withBreadcrumbs: false,
                                withSearchPanel: false,
                                actionId: false,
                                actionViews: [],
                                activateDefaultFavorite: true,
                                noContentHelp: "<p>No records found!</p>",
                                withControlPanel: false,
                                withSearchBar: false,
                                hasSidebar: false
                            });
                            return view.getController(self).then(function(controller) {
                                self.currentPopupController = controller;
                                return self.currentPopupController.appendTo(fragment);
                            }).then(function(){
                                return fragment;
                            });
                        }).then(function(fragment){
                            dialog.open().opened(function(){
                                var $modal = dialog.$el.parents('.modal'),
                                    $content = dialog.$el.parents('.modal-content');
                                $('body').removeClass('modal-open');
                                $modal.removeClass('modal');
                                $modal.addClass('detail_popup');
                                $content.draggable({
                                    handle: '.modal-header'
                                });
                                $content.on('dragstop', function(event, ui){
                                    $modal.css({
                                        top:  ' calc( ' + $modal.css('top') + ' + ' +  $content.css('top') + ')',
                                        left: ' calc( ' + $modal.css('left') + ' + ' +  $content.css('left') + ')'
                                    });
                                    $content.css({
                                        top:  '0px',
                                        left: '0px'
                                    });
                                });
                                dom.append(dialog.$el, fragment, {
                                    callbacks: [{widget: self.currentPopupController}],
                                    in_DOM: true,
                                });
                            });
                        });
                    } else if(parent.$el.parents('.detail_popup').length <= 0) {
                        this.trigger_up('open_record', { id: id, target: ev.target });
                    }
                }
            }
        },
    });
});