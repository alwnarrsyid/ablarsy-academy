// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("Midtrans Settings", {
    refresh: function(frm) {
        if (frm.doc.enabled) {
            frm.add_custom_button(__("Test Connection"), function() {
                frappe.call({
                    method: "lms.lms.gateways.midtrans_gateway.test_connection",
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({
                                title: __("Success"),
                                indicator: "green",
                                message: __("Successfully connected to Midtrans API.")
                            });
                        } else {
                            frappe.msgprint({
                                title: __("Error"),
                                indicator: "red",
                                message: r.message.error || __("Failed to connect to Midtrans API.")
                            });
                        }
                    }
                });
            });
        }
    }
});
