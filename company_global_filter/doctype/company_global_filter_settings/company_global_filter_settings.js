// Copyright (c) 2025, Company Global Filter and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Global Filter Settings", {
	refresh: function(frm) {
		// Add custom buttons
		frm.add_custom_button(__("Clear Cache"), function() {
			frappe.call({
				method: "company_global_filter.utils.clear_company_filter_cache",
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __("Cache cleared successfully"),
							indicator: "green",
						});
					}
				},
			});
		});

		frm.add_custom_button(__("View Filtered DocTypes"), function() {
			frappe.set_route("List", "DocType", {
				custom_company: ["!=", ""],
			});
		});
	},
});

