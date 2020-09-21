odoo.define('gbr_ui_custom.AbstractWebClient', function (require) {
    "use strict";
    var AbstractWebClient = require('web.AbstractWebClient');

    AbstractWebClient.include({
        init: function (parent) {
            var self = this;
            this._super(parent);
            var oldOnKeyDown = this._onKeyDown;
            this._onKeyDown = function(keyDownEvent) {
                if(keyDownEvent.ctrlKey && keyDownEvent.key == 'F7') {
                    var clearSearchAccessKey = document.querySelectorAll('[accesskey="CTRL+F7"]');
                    if (clearSearchAccessKey.length) {
                        clearSearchAccessKey[0].click();
                        if (keyDownEvent.preventDefault) keyDownEvent.preventDefault(); else keyDownEvent.returnValue = false;
                        if (keyDownEvent.stopPropagation) keyDownEvent.stopPropagation();
                        if (keyDownEvent.cancelBubble) keyDownEvent.cancelBubble = true;
                        return false;
                    }
                }
                oldOnKeyDown.call(self, keyDownEvent);
            }
        }
    });
});