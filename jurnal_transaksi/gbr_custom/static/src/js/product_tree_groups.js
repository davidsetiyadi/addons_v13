odoo.define('gbr_custom.upload.bill.mixin', function (require) {
"use strict";

    var core = require('web.core');
    var _t = core._t;

    var qweb = core.qweb;

    var UploadBillMixin = {

        start: function () {
            // define a unique uploadId and a callback method
            this.fileUploadID = _.uniqueId('account_bill_file_upload');
            $(window).on(this.fileUploadID, this._onFileUploaded.bind(this));
            return this._super.apply(this, arguments);
        },

        _onAddAttachment: function (ev) {
            // Auto submit form once we've selected an attachment
            var $input = $(ev.currentTarget).find('input.o_input_file');
            if ($input.val() !== '') {
                var $binaryForm = this.$('.o_vendor_bill_upload form.o_form_binary_form');
                $binaryForm.submit();
            }
        },

        _onFileUploaded: function () {
            // Callback once attachment have been created, create a bill with attachment ids
            var self = this;
            var attachments = Array.prototype.slice.call(arguments, 1);
            // Get id from result
            var attachent_ids = attachments.reduce(function(filtered, record) {
                if (record.id) {
                    filtered.push(record.id);
                }
                return filtered;
            }, []);
            return this._rpc({
                model: 'account.journal',
                method: 'create_invoice_from_attachment',
                args: ["", attachent_ids],
                context: this.initialState.context,
            }).then(function(result) {
                self.do_action(result);
            });
        },

        _onUpload: function (event) {
            var self = this;
            // If hidden upload form don't exists, create it
            var $formContainer = this.$('.o_content').find('.o_vendor_bill_upload');
            if (!$formContainer.length) {
                $formContainer = $(qweb.render('gbr_custom.BillsHiddenUploadForm', {widget: this}));
                $formContainer.appendTo(this.$('.o_content'));
            }
            // Trigger the input to select a file
            this.$('.o_vendor_bill_upload .o_input_file').click();
        },
    }
    return UploadBillMixin;
});


odoo.define('gbr_custom.product.tree', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    
    var UploadBillMixin = require('gbr_custom.upload.bill.mixin');
    var viewRegistry = require('web.view_registry');

    var ProductGroupController = ListController.extend(UploadBillMixin, {
        buttons_template: 'ProdukGroupsListView.buttons',
        events: _.extend({}, ListController.prototype.events, {
            // 'click .o_button_kelompok': '_onUpload',
            // 'change .o_vendor_bill_upload .o_form_binary_form': '_onAddAttachment',
        }),
    });

    var ProdukGroupsListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ProductGroupController,
        }),
    });
    viewRegistry.add('product_tree', ProdukGroupsListView);

    var VendortGroupController = ListController.extend(UploadBillMixin, {
        buttons_template: 'VendorGroupsListView.buttons',
        events: _.extend({}, ListController.prototype.events, {
            // 'click .o_button_kelompok': '_onUpload',
            // 'change .o_vendor_bill_upload .o_form_binary_form': '_onAddAttachment',
        }),
    });
    var VendorGroupsListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: VendortGroupController,
        }),
    });
    viewRegistry.add('vendor_tree', VendorGroupsListView);

    var PelangganGroupController = ListController.extend(UploadBillMixin, {
        buttons_template: 'PelangganGroupsListView.buttons',
        events: _.extend({}, ListController.prototype.events, {
            // 'click .o_button_kelompok': '_onUpload',
            // 'change .o_vendor_bill_upload .o_form_binary_form': '_onAddAttachment',
        }),
    });
    var PelangganGroupsListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: PelangganGroupController,
        }),
    });
    viewRegistry.add('pelanggan_tree', PelangganGroupsListView);

});



