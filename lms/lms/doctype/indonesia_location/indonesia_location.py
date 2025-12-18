# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IndonesiaLocation(Document):
	pass


@frappe.whitelist(allow_guest=True)
def search_location(query):
	"""Search Indonesia locations by province, city, district, or village."""
	if not query or len(query) < 2:
		return []
	
	query = query.strip()
	
	# Search in village, district, city, or province
	locations = frappe.db.sql("""
		SELECT name, province, city, district, village
		FROM `tabIndonesia Location`
		WHERE village LIKE %(query)s
		   OR district LIKE %(query)s
		   OR city LIKE %(query)s
		   OR province LIKE %(query)s
		ORDER BY province, city, district, village
		LIMIT 20
	""", {"query": f"%{query}%"}, as_dict=True)
	
	return locations
