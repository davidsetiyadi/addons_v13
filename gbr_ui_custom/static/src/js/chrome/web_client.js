odoo.define('gbr_ui_custom.WebClient', function (require) {
"use strict";
    var WebClient = require('web.WebClient');
    var Menu = require('web_enterprise.Menu');
    var HomeMenu = require('web_enterprise.HomeMenu');

    WebClient.include({
        load_top_menus: function () {
            return (odoo.loadTopMenusPromise || odoo.reloadTopMenus()).then(function (menuData) {
                if(menuData.length) {
                    for (var i = 0; i < menuData.children.length; i++) {
                        var child = menuData.children[i];
                        if (child.action === false) {
                            while (child.children && child.children.length) {
                                child = child.children[0];
                                if (child.action) {
                                    menuData.children[i].action = child.action;
                                    break;
                                }
                            }
                        }
                    }
                }
                odoo.loadTopMenusPromise = null;
                return menuData;
            });
        },
        instanciate_menu_widgets: function() {
            var self = this;
            var defs = [];
            return this.load_menus().then(function(menu_data) {
                return self.load_top_menus().then(function(top_menu_data) {
                    self.menu_data = menu_data;

                    self.home_menu = new HomeMenu(self, menu_data);
                    self.menu = new Menu(self, menu_data, top_menu_data);

                    defs.push(self.home_menu.appendTo(document.createDocumentFragment()));
                    defs.push(self.menu.appendTo(document.createDocumentFragment()));
                    return Promise.all(defs);
                });
            });
        },
    });
});