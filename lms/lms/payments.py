import frappe

def get_payment_gateway():
    return frappe.db.get_single_value("LMS Settings", "payment_gateway")

def get_controller(payment_gateway):
    if payment_gateway == "Midtrans":
        # DEBUG MODE: TRY-EXCEPT REMOVED
        # This will raise an error if imports fail, showing us the root cause
        from lms.lms.doctype.midtrans_settings.midtrans_settings import is_midtrans_enabled

        if is_midtrans_enabled():
            from lms.lms.gateways.midtrans_gateway import MidtransController
            return MidtransController()

    if "payments" in frappe.get_installed_apps():
        from payments.utils import get_payment_gateway_controller
        return get_payment_gateway_controller(payment_gateway)

def validate_currency(payment_gateway, currency):
    controller = get_controller(payment_gateway)
    controller().validate_transaction_currency(currency)

@frappe.whitelist()
def get_payment_link(doctype, docname, title, amount, discount_amount, gst_amount, currency, address, redirect_to, payment_for_certificate, coupon_code=None, coupon=None):
    payment_gateway = get_payment_gateway()
    address = frappe._dict(address)
    original_amount = amount
    amount -= discount_amount
    amount_with_gst = get_amount_with_gst(amount, gst_amount)

    payment = record_payment(address, doctype, docname, amount, original_amount, currency, amount_with_gst, discount_amount, payment_for_certificate, coupon_code, coupon)

    # Init controller
    controller = get_controller(payment_gateway)

    payment_details = {
        "amount": amount_with_gst if amount_with_gst else amount,
        "title": f"Payment for {doctype} {title} {docname}",
        "description": f"{address.billing_name}'s payment for {title}",
        "reference_doctype": doctype,
        "reference_docname": docname,
        "payer_email": frappe.session.user,
        "payer_name": address.billing_name,
        "currency": currency,
        "payment_gateway": payment_gateway,
        "redirect_to": redirect_to,
        "payment": payment.name,
    }

    create_order(payment_gateway, payment_details, controller)
    url = controller.get_payment_url(**payment_details)
    return url

def create_order(payment_gateway, payment_details, controller):
    if payment_gateway != "Razorpay":
        return
    order = controller.create_order(**payment_details)
    payment_details.update({"order_id": order.get("id")})

def get_amount_with_gst(amount, gst_amount):
    return amount + gst_amount if gst_amount else 0

def record_payment(address, doctype, docname, amount, original_amount, currency, amount_with_gst=0, discount_amount=0, payment_for_certificate=0, coupon_code=None, coupon=None):
    address = frappe._dict(address)
    address_name = save_address(address)
    payment_doc = frappe.new_doc("LMS Payment")
    payment_doc.update({
        "member": frappe.session.user,
        "billing_name": address.billing_name,
        "address": address_name,
        "amount": amount,
        "currency": currency,
        "discount_amount": discount_amount,
        "amount_with_gst": amount_with_gst,
        "gstin": address.gstin,
        "pan": address.pan,
        "source": address.source,
        "payment_for_document_type": doctype,
        "payment_for_document": docname,
        "payment_for_certificate": payment_for_certificate,
    })
    if coupon_code:
        payment_doc.update({
            "coupon": coupon,
            "coupon_code": coupon_code,
            "discount_amount": discount_amount,
            "original_amount": original_amount,
        })
    payment_doc.save(ignore_permissions=True)
    return payment_doc

def save_address(address):
    filters = {"email_id": frappe.session.user}
    if frappe.db.exists("Address", filters):
        address_doc = frappe.get_last_doc("Address", filters=filters)
    else:
        address_doc = frappe.new_doc("Address")
    address_doc.update(address)
    address_doc.update({
        "address_title": frappe.db.get_value("User", frappe.session.user, "full_name"),
        "address_type": "Billing",
        "is_primary_address": 1,
        "email_id": frappe.session.user,
    })
    address_doc.save(ignore_permissions=True)
    return address_doc.name
