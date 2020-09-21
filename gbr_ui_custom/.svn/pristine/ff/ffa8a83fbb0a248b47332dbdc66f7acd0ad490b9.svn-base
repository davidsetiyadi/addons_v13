odoo.define('gbr_ui_custom.AbstractController', function (require) {
"use strict";
    var AbstractController = require('web.AbstractController');
    var time = require('web.time');
    var Domain = require('web.Domain');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    AbstractController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.isDetailPopup = false;
            this.detailPopups = false;
            this.currentPopup = false;
            this.currentPopupController = false;
        },
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if(self.viewType == 'list'){
                    self._rpc({
                        model: 'gbr.detail.popup',
                        method: 'search_read',
                        domain: [['src_model_id.model', '=', self.modelName]],
                    }).then(function(detailPopups){
                        self.detailPopups = detailPopups;
                        var fieldColumns = []
                        if(self._controlPanel){
                            var searchBar = self._controlPanel.renderer.searchBar,
                                filtersMenu = self._controlPanel.renderer.subMenus.filter,
                                filterFields = searchBar.filterFields;
                            var oddFilterFields = searchBar.autoCompleteSources.filter(function(field, index){
                                return !(index % 2);
                            });
                            var evenFilterFields = searchBar.autoCompleteSources.filter(function(field, index){
                                return index % 2;
                            });
                            fieldColumns.push(oddFilterFields, evenFilterFields);
                            self.$el.append(QWeb.render('SearchViewBottom', {fieldColumns: fieldColumns, detailPopups: detailPopups, isDetailPopup: (detailPopups.length ? true : false)}));
                            self.$('.gbr_search_form').on('keyup', '.gbr_search_field', function(event){
                                var keycode = (event.keyCode ? event.keyCode : event.which);
                                if(keycode == '13'){
                                    self.$('.gbr_search_submit').click();
                                }
                            });
                            self.$('.gbr_search_submit').click(function(){
                                searchBar = self._controlPanel.renderer.searchBar;

                                self.$('.gbr_search_field').each(function(){
                                    var input = $(':input.gbr_field', this);
                                    if(input.length > 1) {
                                        if($(this).hasClass('gbr_date')) {
                                            var $input_from = $(input[0]),
                                                $input_to = $(input[1]),
                                                val_from = $input_from.val(),
                                                val_to = $input_to.val();

                                            if(val_from && val_to) {
                                                var domain = Domain.prototype.arrayToString([[$input_from.data('name'), '>=', val_from], [$input_to.data('name'), '<=', val_to]]);
                                                var filters = [{
                                                    type: 'filter',
                                                    description: _.str.sprintf('%(field)s %(operator)s "%(value1)s and %(value2)s"', {
                                                        field: $input_from.data('string'),
                                                        operator: 'is between',
                                                        value1: val_from,
                                                        value2: val_to
                                                    }),
                                                    domain: domain,
                                                }];
                                                filtersMenu.trigger_up('new_filters', {filters: filters});
                                            }
                                        }

                                        if($(this).hasClass('gbr_radio')){
                                            var input = $('input[data-name=' + $(input[0]).attr('name') + ']:checked'),
                                                val = input.val(),
                                                filterId = input.data('filter-id');
                                            if(val){
                                                var val_bool = (val === 'true');
                                                var values = {label: input.data('label'), value: val_bool};
                                                var results = $.grep(searchBar.autoCompleteSources, function(a) {
                                                    return a.filter.id == filterId;
                                                });
                                                $.each(results, function(){
                                                    searchBar.trigger_up('autocompletion_filter', {
                                                        filterId: filterId,
                                                        autoCompleteValues: [values],
                                                    });
                                                });
                                            }
                                        }
                                    } else {
                                        var val = input.val(),
                                            filterId = input.data('filter-id');
                                        if(val){
                                            var values = {label: val, value: val};
                                            var results = $.grep(searchBar.autoCompleteSources, function(a) {
                                                return a.filter.id == filterId;
                                            });
                                            $.each(results, function(){
                                                if(this.attrs.type == 'selection'){
                                                    values['label'] = $('option:selected', input).data('label');
                                                }
                                                if(!this.attrs.filter_domain){
                                                    if(!this.attrs.operator){
                                                        if(this.attrs.type == 'many2one'){
                                                            values['operator'] = 'ilike';
                                                        } else if(this.attrs.type != 'selection') {
                                                            values['operator'] = this.__proto__.default_operator;
                                                        }
                                                    } else {
                                                        values['operator'] = this.attrs.operator;
                                                    }
                                                }
                                                searchBar.trigger_up('autocompletion_filter', {
                                                    filterId: filterId,
                                                    autoCompleteValues: [values],
                                                });
                                            });
                                        }
                                    }
                                });
                                self.$('.gbr_search_form :input.gbr_field:not([type=radio])').val(null);
                                self.$('.gbr_search_form :input.gbr_field[type=radio]').prop('checked', false);
                            });
                            self.$('.gbr_date_from[data-type="date"], .gbr_date_to[data-type="date"]').datetimepicker({
                                locale: moment.locale(),
                                format : time.getLangDateFormat(),
                                minDate: moment({ y: 1900 }),
                                maxDate: moment({ y: 9999, M: 11, d: 31 }),
                                useCurrent: false,
                                icons: {
                                    time: 'fa fa-clock-o',
                                    date: 'fa fa-calendar',
                                    up: 'fa fa-chevron-up',
                                    down: 'fa fa-chevron-down',
                                    previous: 'fa fa-chevron-left',
                                    next: 'fa fa-chevron-right',
                                    today: 'fa fa-calendar-check-o',
                                    clear: 'fa fa-delete',
                                    close: 'fa fa-check primary',
                                },
                                calendarWeeks: true,
                                buttons: {
                                    showToday: false,
                                    showClear: false,
                                    showClose: false,
                                },
                                widgetParent: 'body',
                                keyBinds: null,
                                allowInputToggle: true
                            });
                            self.$('.gbr_date_from[data-type="datetime"], .gbr_date_to[data-type="datetime"]').datetimepicker({
                                locale: moment.locale(),
                                format : time.getLangDatetimeFormat(),
                                minDate: moment({ y: 1900 }),
                                maxDate: moment({ y: 9999, M: 11, d: 31 }),
                                useCurrent: false,
                                icons: {
                                    time: 'fa fa-clock-o',
                                    date: 'fa fa-calendar',
                                    up: 'fa fa-chevron-up',
                                    down: 'fa fa-chevron-down',
                                    previous: 'fa fa-chevron-left',
                                    next: 'fa fa-chevron-right',
                                    today: 'fa fa-calendar-check-o',
                                    clear: 'fa fa-delete',
                                    close: 'fa fa-check primary',
                                },
                                calendarWeeks: true,
                                buttons: {
                                    showToday: false,
                                    showClear: false,
                                    showClose: false,
                                },
                                widgetParent: 'body',
                                keyBinds: null,
                                allowInputToggle: true
                            });
                            self.$('#gbr_search_content').on('show.bs.collapse', function(){
                                $(this).siblings('h3').find('i').attr('class', 'fa fa-arrow-circle-down');
                            });
                            self.$('#gbr_search_content').on('hide.bs.collapse', function(){
                                $(this).siblings('h3').find('i').attr('class', 'fa fa-arrow-circle-up');
                            });
                            self.$('.gbr_search_reset').click(function(){
                                self.$('.gbr_search_form').trigger('reset');
                            });
                            self.$('.gbr_search_clear').click(function(){
                                var model = self._controlPanel.model,
                                    state = model.get();
                                var groups = model.query;
                                $(groups).each(function(){
                                    model.deactivateGroup(this);
                                });
                                self._controlPanel._reportNewQueryAndRender();
                            });
                            self.$('.gbr_search_popup').click(function(){
                                $(this).toggleClass('active');
                                if($(this).hasClass('active')){
                                    self.isDetailPopup = true;
                                    self.currentPopup = self.detailPopups[$(this).data('index')]
                                    $(this).find('.detailState').text('ENABLED');
                                    self.$('.gbr_search_popup').not(this).removeClass('active');
                                    self.$('.gbr_search_popup').not(this).find('.detailState').text('DISABLED');
                                } else {
                                    self.isDetailPopup = false;
                                    self.currentPopup = false;
                                    $(this).find('.detailState').text('DISABLED');
                                }
                            });
                        }
                    });
                }
            });
        },
    });
});