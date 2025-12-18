from urllib.parse import quote

import frappe


def get_context(context):
	context.no_cache = 1
	certificate_id = frappe.form_dict.certificate_id

	# Use custom endpoint for proper landscape PDF generation
	frappe.local.flags.redirect_location = f"/api/method/lms.lms.custom_certificate.download_certificate_pdf?certificate_name={certificate_id}"
	raise frappe.Redirect

