{
	"name": "GBR Custom",
	"version": "1.0",
	"depends": [
		"base",
		"stock",
		"account",
		"account_reports",
		"sale",
		"sale_management",
		"purchase",
		"gbr_ui_custom",
		# "vit_stock_card_pro"
	],
	"author": "sgeede.com",
	"category": "Sales",
	'website': 'http://www.sgeede.com',
	"description": """\

this module provide Custom Form View for GBR


            Find our other interesting modules that can make your life easier:
            https://apps.odoo.com/apps/modules/browse?author=SGEEDE
""",
	"data": [
		'security/ir.model.access.csv',
		"wizards/view_wizard_filter_po.xml",
		"wizards/wizard_statement_filter_view.xml",
		"wizards/wizard_grouping.xml",
		"views/res_config_settings_views.xml",
		"views/gbr_custom_menu.xml",
		"views/configuration_view.xml",
		"views/account_views.xml",
		"views/pembelian_views.xml",
		"views/hr_employee.xml",
		"views/res_company.xml",
		"views/res_partner.xml",
		"views/customer_view.xml",
		"views/purchase_view.xml",
		"views/product_template_views.xml",
		"views/payment_voucher.xml",
		"views/sales_view.xml",
		"views/penjualan_view.xml",
		"views/kas_view.xml",
		"views/gbr_custom.xml",
		"views/lainnya_view.xml",
		"wizards/wizard_pencairan_cek.xml",
		"wizards/wizard_kartu_hutang_piutang.xml",
		"wizards/wizard_journal_khusus.xml",
		"data/group_data.xml",
		'data/ir_sequence_data.xml',
		'report/purchase_order_templates.xml',		
		'report/penjualan_report_views.xml'
		# "views/kecamatan.xml",

		# "views/kelurahan.xml",
		# "views/kota.xml",
		# "views/partner.xml",

		# "view/kecamatan.xml",
		# "view/kota.xml",
		# "view/partner.xml",
		# "security/ir.model.access.csv",
	],
    'qweb': [
       "static/src/xml/*.xml",
    ],
	"installable": True,
	"auto_install": False,
    "application": True,
}