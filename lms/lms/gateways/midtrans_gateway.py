# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

"""
Midtrans Payment Gateway Integration for Frappe LMS.

This module provides integration with Midtrans Snap API for processing payments
in Indonesian Rupiah (IDR) using various payment methods like GoPay, QRIS,
Virtual Accounts, Credit Cards, etc.
"""

import base64
import hashlib
import json

import frappe
import requests
from frappe import _
from frappe.utils import cint, get_url, now_datetime, random_string


# Midtrans API Endpoints
MIDTRANS_SANDBOX_URL = "https://app.sandbox.midtrans.com/snap/v1/transactions"
MIDTRANS_PRODUCTION_URL = "https://app.midtrans.com/snap/v1/transactions"

SANDBOX_SNAP_URL = "https://app.sandbox.midtrans.com/snap/snap.js"
PRODUCTION_SNAP_URL = "https://app.midtrans.com/snap/snap.js"


class MidtransController:
    """Payment gateway controller for Midtrans."""

    def __init__(self):
        self.settings = self._get_settings()

    def _get_settings(self):
        """Get Midtrans settings from database."""
        settings = frappe.get_single("Midtrans Settings")
        return {
            "enabled": settings.enabled,
            "environment": settings.environment,
            "server_key": settings.get_password("server_key"),
            "client_key": settings.client_key,
        }

    def _get_api_url(self):
        """Get the appropriate API URL based on environment."""
        if self.settings.get("environment") == "Production":
            return MIDTRANS_PRODUCTION_URL
        return MIDTRANS_SANDBOX_URL

    def _get_snap_url(self):
        """Get the appropriate Snap JS URL based on environment."""
        if self.settings.get("environment") == "Production":
            return PRODUCTION_SNAP_URL
        return SANDBOX_SNAP_URL

    def _get_auth_header(self):
        """Generate Base64 encoded authorization header."""
        server_key = self.settings.get("server_key", "")
        auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
        return {"Authorization": f"Basic {auth_string}", "Content-Type": "application/json"}

    def _get_valid_email(self, email):
        """Get a valid email address, fallback to user's actual email if needed."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if email and re.match(email_pattern, email):
            return email

        # Try to get actual email from User document
        user = frappe.session.user
        if user and user != "Guest":
            user_email = frappe.db.get_value("User", user, "email")
            if user_email and re.match(email_pattern, user_email):
                return user_email

        # Fallback email
        return "customer@example.com"

    def validate_transaction_currency(self, currency):
        """Validate that the currency is supported by Midtrans."""
        if currency != "IDR":
            frappe.throw(
                _("Midtrans only supports IDR (Indonesian Rupiah) currency. Current currency: {0}").format(
                    currency
                )
            )

    def create_order(self, **kwargs):
        """
        Create a Midtrans Snap transaction and return the token.

        Args:
            amount: Transaction amount in IDR
            title: Transaction title
            description: Transaction description
            payer_email: Customer email
            payer_name: Customer name
            reference_doctype: Reference document type (e.g., LMS Course)
            reference_docname: Reference document name
            payment: LMS Payment document name

        Returns:
            dict: Contains 'token' and 'redirect_url' from Midtrans
        """
        if not self.settings.get("enabled"):
            frappe.throw(_("Midtrans is not enabled. Please configure Midtrans Settings."))

        amount = cint(kwargs.get("amount", 0))
        if amount <= 0:
            frappe.throw(_("Invalid transaction amount."))

        # Generate unique order ID
        order_id = f"LMS-{kwargs.get('payment', random_string(10))}-{now_datetime().strftime('%Y%m%d%H%M%S')}"

        # Prepare transaction data
        # Inline email validation (handle non-email usernames like 'Administrator')
        import re
        payer_email = kwargs.get("payer_email", "")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not payer_email or not re.match(email_pattern, payer_email):
            # Try to get actual email from User document
            user = frappe.session.user
            if user and user != "Guest":
                user_email = frappe.db.get_value("User", user, "email")
                if user_email and re.match(email_pattern, user_email):
                    payer_email = user_email
                else:
                    payer_email = "customer@example.com"
            else:
                payer_email = "customer@example.com"

        # Get item details based on reference_doctype (Course, Batch, etc.)
        reference_doctype = kwargs.get("reference_doctype", "LMS Course")
        reference_docname = kwargs.get("reference_docname", "")
        item_name = kwargs.get("title", "Course Purchase")[:50]  # Midtrans name limit 50 chars
        item_category = "Course"
        item_url = get_url(kwargs.get("redirect_to", "/lms/courses"))

        # Try to get more details from the actual document
        if reference_doctype == "LMS Course" and reference_docname:
            try:
                course = frappe.get_doc("LMS Course", reference_docname)
                item_name = (course.title or reference_docname)[:50]
                item_category = course.category or "Course"
            except Exception:
                pass
        elif reference_doctype == "LMS Batch" and reference_docname:
            try:
                batch = frappe.get_doc("LMS Batch", reference_docname)
                item_name = (batch.title or reference_docname)[:50]
                item_category = "Batch"
            except Exception:
                pass

        # Build transaction data per Midtrans API Reference
        transaction_data = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": amount
            },
            "customer_details": {
                "first_name": kwargs.get("payer_name", "Customer"),
                "email": payer_email,
            },
            "item_details": [
                {
                    "id": reference_docname or "ITEM",
                    "price": amount,
                    "quantity": 1,
                    "name": item_name,
                    "category": item_category,
                    "merchant_name": "LMS",
                    "url": item_url
                }
            ],
            "callbacks": {
                # Use localhost for callback URLs (user's browser is on localhost)
                "finish": f"http://localhost:8000{kwargs.get('redirect_to', '/lms/courses')}",
                "error": "http://localhost:8000/lms/payment-error",
                "pending": "http://localhost:8000/lms/payment-pending",
            },
            # Custom fields for webhook verification
            "custom_field1": kwargs.get("payment", ""),
            "custom_field2": reference_doctype,
            "custom_field3": reference_docname,
        }

        try:
            response = requests.post(
                self._get_api_url(),
                headers=self._get_auth_header(),
                json=transaction_data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if "token" in result:
                # Note: Skipping database save for midtrans_order_id/midtrans_token
                # as those columns don't exist yet. Token is stored in redirect_url.
                return {
                    "token": result.get("token"),
                    "redirect_url": result.get("redirect_url"),
                    "order_id": order_id,
                }
            else:
                frappe.throw(_("Failed to get payment token from Midtrans: {0}").format(result))

        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Midtrans API Error: {str(e)}", "Midtrans Payment Error")
            frappe.throw(_("Failed to connect to Midtrans. Please try again later."))

    def get_payment_url(self, **kwargs):
        """
        Get the Midtrans Snap payment URL/token.

        This method creates an order and returns the redirect URL.
        """
        result = self.create_order(**kwargs)
        return result.get("redirect_url")


def get_controller():
    """Factory function to get the Midtrans controller instance."""
    return MidtransController()


@frappe.whitelist()
def get_midtrans_payment_token(
    doctype,
    docname,
    title,
    amount,
    discount_amount,
    gst_amount,
    currency,
    address,
    redirect_to,
    payment_for_certificate,
    coupon_code=None,
    coupon=None,
):
    """
    API endpoint to get Midtrans payment token.

    This is called from the frontend when the user clicks "Pay".
    """
    from lms.lms.payments import get_amount_with_gst, record_payment

    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to continue with payment."))

    controller = get_controller()
    controller.validate_transaction_currency(currency)

    address = frappe._dict(address if isinstance(address, dict) else json.loads(address))
    original_amount = float(amount)
    discount_amount = float(discount_amount) if discount_amount else 0
    gst_amount = float(gst_amount) if gst_amount else 0

    amount_after_discount = original_amount - discount_amount
    amount_with_gst = get_amount_with_gst(amount_after_discount, gst_amount)
    final_amount = amount_with_gst if amount_with_gst else amount_after_discount

    # Record the payment
    payment = record_payment(
        address,
        doctype,
        docname,
        amount_after_discount,
        original_amount,
        currency,
        amount_with_gst,
        discount_amount,
        payment_for_certificate,
        coupon_code,
        coupon,
    )

    # Create Midtrans transaction
    result = controller.create_order(
        amount=cint(final_amount),
        title=f"Payment for {doctype} {title}",
        description=f"{address.billing_name}'s payment for {title}",
        reference_doctype=doctype,
        reference_docname=docname,
        payer_email=frappe.session.user,
        payer_name=address.billing_name,
        currency=currency,
        redirect_to=redirect_to,
        payment=payment.name,
    )

    return {
        "token": result.get("token"),
        "redirect_url": result.get("redirect_url"),
        "client_key": controller.settings.get("client_key"),
        "snap_url": controller._get_snap_url(),
    }


@frappe.whitelist(allow_guest=True)
def handle_webhook():
    """
    Handle Midtrans payment notification webhook.

    This is called by Midtrans when the payment status changes.
    """
    try:
        data = frappe.request.get_json() if frappe.request else {}

        if not data:
            frappe.throw(_("Invalid webhook data"))

        order_id = data.get("order_id", "")
        transaction_status = data.get("transaction_status", "")
        fraud_status = data.get("fraud_status", "")
        signature_key = data.get("signature_key", "")

        # Verify signature
        if not verify_signature(data):
            frappe.log_error("Invalid Midtrans signature", "Midtrans Webhook Error")
            return {"status": "error", "message": "Invalid signature"}

        # Find the payment record using custom_field1 (which contains payment name)
        # Fallback: try parsing order_id format "LMS-{payment_name}-{timestamp}"
        payment_name = data.get("custom_field1", "")

        if not payment_name and order_id:
            # Try to extract payment name from order_id
            # Format: LMS-{payment_name}-{timestamp}
            parts = order_id.split("-")
            if len(parts) >= 2:
                payment_name = parts[1]

        if not payment_name or not frappe.db.exists("LMS Payment", payment_name):
            frappe.log_error(f"Payment not found for order_id: {order_id}, custom_field1: {data.get('custom_field1')}", "Midtrans Webhook Error")
            return {"status": "error", "message": "Payment not found"}

        # Update payment status based on transaction status
        if transaction_status in ["capture", "settlement"]:
            if fraud_status == "accept" or not fraud_status:
                # Payment successful
                process_successful_payment(payment_name, data)
        elif transaction_status in ["deny", "cancel", "expire"]:
            # Payment failed
            frappe.db.set_value("LMS Payment", payment_name, "status", "Failed")
        elif transaction_status == "pending":
            # Payment pending
            frappe.db.set_value("LMS Payment", payment_name, "status", "Pending")

        frappe.db.commit()
        return {"status": "ok"}

    except Exception as e:
        frappe.log_error(f"Midtrans Webhook Error: {str(e)}", "Midtrans Webhook Error")
        return {"status": "error", "message": str(e)}


def verify_signature(data):
    """Verify the Midtrans webhook signature."""
    settings = frappe.get_single("Midtrans Settings")
    server_key = settings.get_password("server_key")

    order_id = data.get("order_id", "")
    status_code = data.get("status_code", "")
    gross_amount = data.get("gross_amount", "")
    signature_key = data.get("signature_key", "")

    # Calculate expected signature
    raw_string = f"{order_id}{status_code}{gross_amount}{server_key}"
    expected_signature = hashlib.sha512(raw_string.encode()).hexdigest()

    return signature_key == expected_signature


def process_successful_payment(payment_name, data):
    """Process a successful payment and enroll the user."""
    payment = frappe.get_doc("LMS Payment", payment_name)
    payment.status = "Paid"
    payment.payment_received = 1
    payment.midtrans_transaction_id = data.get("transaction_id", "")
    payment.midtrans_payment_type = data.get("payment_type", "")
    payment.save(ignore_permissions=True)

    # Update coupon redemption if applicable
    if payment.coupon:
        redemption_count = frappe.db.get_value("LMS Coupon", payment.coupon, "redemption_count") or 0
        frappe.db.set_value("LMS Coupon", payment.coupon, "redemption_count", redemption_count + 1)

    # Trigger enrollment based on document type
    doctype = payment.payment_for_document_type
    docname = payment.payment_for_document

    if payment.payment_for_certificate:
        # Handle certificate purchase
        update_certificate_purchase(docname, payment.name, payment.member)
    elif doctype == "LMS Course":
        # Enroll in course
        enroll_in_course_midtrans(docname, payment.name, payment.member)
    elif doctype == "LMS Batch":
        # Enroll in batch
        enroll_in_batch_midtrans(docname, payment.name, payment.member)


def update_certificate_purchase(course, payment_name, member):
    """Update certificate purchase status for a course enrollment."""
    enrollment = frappe.db.get_value(
        "LMS Enrollment", {"course": course, "member": member}, "name"
    )
    if enrollment:
        frappe.db.set_value("LMS Enrollment", enrollment, "purchased_certificate", 1)


def enroll_in_course_midtrans(course, payment_name, member):
    """Enroll user in a course after successful Midtrans payment."""
    if not frappe.db.exists("LMS Enrollment", {"member": member, "course": course}):
        enrollment = frappe.new_doc("LMS Enrollment")
        enrollment.update(
            {
                "member": member,
                "course": course,
                "payment": payment_name,
            }
        )
        enrollment.save(ignore_permissions=True)


def enroll_in_batch_midtrans(batch, payment_name, member):
    """Enroll user in a batch after successful Midtrans payment."""
    if not frappe.db.exists("LMS Batch Enrollment", {"member": member, "batch": batch}):
        # Run as the member user to bypass permission checks
        original_user = frappe.session.user
        frappe.set_user(member)

        try:
            enrollment = frappe.new_doc("LMS Batch Enrollment")
            payment = frappe.db.get_value("LMS Payment", payment_name, ["name", "source"], as_dict=True)
            enrollment.update(
                {
                    "member": member,
                    "batch": batch,
                    "payment": payment.name,
                    "source": payment.source if payment else None,
                }
            )
            enrollment.flags.ignore_permissions = True
            enrollment.save(ignore_permissions=True)
        finally:
            # Restore original user
            frappe.set_user(original_user)


@frappe.whitelist()
def test_connection():
    """Test the connection to Midtrans API."""
    try:
        controller = get_controller()

        if not controller.settings.get("enabled"):
            return {"success": False, "error": "Midtrans is not enabled."}

        # Make a simple request to verify credentials
        # We'll use a minimal transaction request that will fail but verify auth
        response = requests.post(
            controller._get_api_url(),
            headers=controller._get_auth_header(),
            json={"transaction_details": {"order_id": "test", "gross_amount": 1}},
            timeout=10,
        )

        # If we get 400/401, the credentials are wrong
        # If we get 200 or other validation errors, credentials are correct
        if response.status_code == 401:
            return {"success": False, "error": "Invalid Server Key. Please check your credentials."}

        return {"success": True}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
