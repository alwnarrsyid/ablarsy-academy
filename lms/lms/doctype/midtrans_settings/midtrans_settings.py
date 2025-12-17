# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url


class MidtransSettings(Document):
    def validate(self):
        if self.enabled:
            if not self.server_key:
                frappe.throw(_("Server Key is required when Midtrans is enabled."))
            if not self.client_key:
                frappe.throw(_("Client Key is required when Midtrans is enabled."))

    def on_update(self):
        self.update_webhook_url_html()

    def update_webhook_url_html(self):
        webhook_url = get_url("/api/method/lms.lms.gateways.midtrans_gateway.handle_webhook")
        html = f"""
        <div class="alert alert-info">
            <strong>Webhook URL:</strong><br>
            <code>{webhook_url}</code><br><br>
            <small>Configure this URL in your Midtrans Dashboard under Settings &gt; Configuration &gt; Payment Notification URL</small>
        </div>
        """
        frappe.db.set_value("Midtrans Settings", "Midtrans Settings", "webhook_url_html", html)


@frappe.whitelist()
def is_midtrans_enabled():
    """Check if Midtrans is enabled."""
    return frappe.db.get_single_value("Midtrans Settings", "enabled")


def get_midtrans_settings():
    """Get Midtrans settings as a dict."""
    settings = frappe.get_single("Midtrans Settings")
    return {
        "enabled": settings.enabled,
        "environment": settings.environment,
        "server_key": settings.get_password("server_key"),
        "client_key": settings.client_key,
    }
