# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LMSReferralCommission(Document):
    def before_save(self):
        """Calculate commission amount before saving."""
        if self.total_amount and self.commission_rate:
            self.commission_amount = (self.total_amount * self.commission_rate) / 100
