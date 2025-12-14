# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LMSGoogleMeetSettings(Document):
	def validate(self):
		if self.enabled and not self.google_calendar:
			frappe.throw(_("Please select a Google Calendar to enable Google Meet integration."))
