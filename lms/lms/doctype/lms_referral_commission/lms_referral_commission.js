// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("LMS Referral Commission", {
    refresh(frm) {
        // Add button to mark as paid
        if (frm.doc.payout_status === "Unpaid" && !frm.is_new()) {
            frm.add_custom_button(__("Mark as Paid"), function() {
                frm.set_value("payout_status", "Paid");
                frm.set_value("payout_date", frappe.datetime.get_today());
                frm.save();
            }, __("Actions"));
        }
    }
});
