odoo.define('gbr_ui_custom.Menu', function (require) {
"use strict";
    var Menu = require('web_enterprise.Menu');
    var config = require('web.config');
    var core = require('web.core');
    var QWeb = core.qweb;

    Menu.include({
        events: _.extend(Menu.prototype.events, {
            'mouseover .gbr_menu_sections > li:not(.show)': '_onMouseOverGbrMenu',
        }),
        init: function (parent, menu_data, top_menu_data) {
            var self = this;
            this._super.apply(this, arguments);
            this.home_menu_displayed = true;
            this.backbutton_displayed = false;

            this.$menu_sections = {};
            this.menu_data = menu_data;
            this.top_menu_data = top_menu_data;

            // Prepare navbar's menus
            var $menu_sections = $(QWeb.render(this.menusTemplate, {
                menu_data: this.menu_data,
                top_menu_data: this.top_menu_data
            }));
            $menu_sections.filter('section').each(function () {
                self.$menu_sections[parseInt(this.className, 10)] = $(this).children('li');
            });

            // Bus event
            core.bus.on('change_menu_section', this, this.change_menu_section);
            core.bus.on('toggle_mode', this, this.toggle_mode);
        },
        start: function () {
            this._super();
            var self = this;
            var on_secondary_menu_click = function (ev) {
                ev.preventDefault();
                var menu_id = $(ev.currentTarget).data('menu');
                var action_id = $(ev.currentTarget).data('action-id');
                self._on_secondary_menu_click(menu_id, action_id);
            };
            this.$('.gbr_top_menu').on('click', 'a[data-menu]', self, on_secondary_menu_click.bind(this))
        },
        _onMouseOverGbrMenu: function(ev) {
            if (config.device.isMobile) {
                return;
            }
            var $target = $(ev.currentTarget);
            var $opened = $target.siblings('.show');
            if ($opened.length) {
                $opened.find('[data-toggle="dropdown"]').dropdown('toggle');
                $opened.removeClass('show');
                $target.find('[data-toggle="dropdown"]:first').dropdown('toggle');
                $target.addClass('show');
            }
        }
    });
});