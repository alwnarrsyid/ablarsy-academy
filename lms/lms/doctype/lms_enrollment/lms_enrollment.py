# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import ceil


class LMSEnrollment(Document):
	def validate(self):
		self.validate_membership_in_same_batch()
		self.validate_membership_in_different_batch_same_course()
		self.validate_payment_for_paid_course()

	def validate_payment_for_paid_course(self):
		"""Ensure payment is complete before enrolling in a paid course."""
		# Skip validation if enrollment is from batch enrollment
		if getattr(self.flags, 'from_batch_enrollment', False):
			return

		# Skip validation for moderators/admins
		if frappe.session.user == "Administrator":
			return
		user_roles = frappe.get_roles(frappe.session.user)
		if "System Manager" in user_roles or "Moderator" in user_roles or "VIP Student" in user_roles:
			return

		course_details = frappe.db.get_value(
			"LMS Course",
			self.course,
			["paid_course", "title"],
			as_dict=True,
		)

		if course_details and course_details.paid_course:
			# First check if user has paid for this course directly
			payment = frappe.db.exists(
				"LMS Payment",
				{
					"payment_for_document_type": "LMS Course",
					"payment_for_document": self.course,
					"member": self.member or frappe.session.user,
					"payment_received": 1,
				},
			)

			if payment:
				return  # User has paid for course directly

			# Check if user is enrolled in a batch that contains this course
			if self.is_enrolled_via_batch():
				return  # User has access through batch enrollment

			frappe.throw(
				_("You need to complete the payment for '{0}' before enrolling.").format(
					course_details.title
				)
			)

	def is_enrolled_via_batch(self):
		"""Check if user is enrolled in a batch that contains this course."""
		member = self.member or frappe.session.user

		# Get all batches that contain this course
		batches_with_course = frappe.get_all(
			"Batch Course",
			filters={"course": self.course},
			pluck="parent"
		)

		if not batches_with_course:
			return False

		# Check if user is enrolled in any of these batches with payment received
		for batch in batches_with_course:
			batch_enrollment = frappe.db.exists(
				"LMS Batch Enrollment",
				{"batch": batch, "member": member}
			)
			if batch_enrollment:
				# Verify the batch was paid for (if it's a paid batch)
				batch_info = frappe.db.get_value("LMS Batch", batch, ["paid_batch"], as_dict=True)
				if not batch_info or not batch_info.paid_batch:
					# Free batch, user has access
					return True

				# Paid batch, check if payment was received
				batch_payment = frappe.db.exists(
					"LMS Payment",
					{
						"payment_for_document_type": "LMS Batch",
						"payment_for_document": batch,
						"member": member,
						"payment_received": 1,
					}
				)
				if batch_payment:
					return True

		return False

	def on_update(self):
		update_program_progress(self.member)

	def validate_membership_in_same_batch(self):
		filters = {"member": self.member, "course": self.course, "name": ["!=", self.name]}
		if self.batch_old:
			filters["batch_old"] = self.batch_old
		previous_membership = frappe.db.get_value(
			"LMS Enrollment", filters, fieldname=["member_type", "member"], as_dict=1
		)

		if previous_membership:
			member_name = frappe.db.get_value("User", self.member, "full_name")
			course_title = frappe.db.get_value("LMS Course", self.course, "title")
			frappe.throw(
				_("{0} is already a {1} of the course {2}").format(
					member_name, previous_membership.member_type, course_title
				)
			)

	def validate_membership_in_different_batch_same_course(self):
		"""Ensures that a studnet is only part of one batch."""
		# nothing to worry if the member is not a student
		if self.member_type != "Student":
			return

		course = frappe.db.get_value("LMS Batch Old", self.batch_old, "course")
		memberships = frappe.get_all(
			"LMS Enrollment",
			filters={
				"member": self.member,
				"name": ["!=", self.name],
				"member_type": "Student",
				"course": self.course,
			},
			fields=["batch_old", "member_type", "name"],
		)

		if memberships:
			membership = memberships[0]
			member_name = frappe.db.get_value("User", self.member, "full_name")
			frappe.throw(
				_("{0} is already a Student of {1} course through {2} batch").format(
					member_name, course, membership.batch_old
				)
			)


def update_program_progress(member):
	programs = frappe.get_all("LMS Program Member", {"member": member}, ["parent", "name"])

	for program in programs:
		total_progress = 0
		courses = frappe.get_all("LMS Program Course", {"parent": program.parent}, pluck="course")
		for course in courses:
			progress = frappe.db.get_value("LMS Enrollment", {"course": course, "member": member}, "progress")
			progress = progress or 0
			total_progress += progress

		average_progress = ceil(total_progress / len(courses))
		frappe.db.set_value("LMS Program Member", program.name, "progress", average_progress)


@frappe.whitelist()
def create_membership(course, batch=None, member=None, member_type="Student", role="Member"):
	validate_course_enrollment_eligibility(course, member)

	enrollment = frappe.new_doc("LMS Enrollment")
	enrollment.update(
		{
			"doctype": "LMS Enrollment",
			"batch_old": batch,
			"course": course,
			"role": role,
			"member_type": member_type,
			"member": member or frappe.session.user,
		}
	)
	enrollment.insert()
	return enrollment


def validate_course_enrollment_eligibility(course, member):
	if not member:
		member = frappe.session.user

	# Skip validation for admins and VIP students
	if member == "Administrator":
		return
	user_roles = frappe.get_roles(member)
	if "System Manager" in user_roles or "Moderator" in user_roles or "VIP Student" in user_roles:
		return

	course_details = frappe.db.get_value(
		"LMS Course",
		course,
		["published", "disable_self_learning", "paid_course", "paid_certificate"],
		as_dict=True,
	)

	if course_details.disable_self_learning:
		frappe.throw(
			_(
				"You cannot enroll in this course as self-learning is disabled. Please contact the Administrator."
			)
		)

	if not course_details.published:
		frappe.throw(_("You cannot enroll in an unpublished course."))

	if course_details.paid_course:
		# Check if user has paid for this course directly
		payment = frappe.db.exists(
			"LMS Payment",
			{
				"payment_for_document_type": "LMS Course",
				"payment_for_document": course,
				"member": member,
				"payment_received": 1,
			},
		)

		if payment:
			return  # User has paid for course directly

		# Check if user is enrolled in a batch that contains this course
		if is_enrolled_via_batch_standalone(course, member):
			return  # User has access through batch enrollment

		frappe.throw(_("You need to complete the payment for this course before enrolling."))


def is_enrolled_via_batch_standalone(course, member):
	"""Check if user is enrolled in a batch that contains this course (standalone function)."""
	# Get all batches that contain this course
	batches_with_course = frappe.get_all(
		"Batch Course",
		filters={"course": course},
		pluck="parent"
	)

	if not batches_with_course:
		return False

	# Check if user is enrolled in any of these batches with payment received
	for batch in batches_with_course:
		batch_enrollment = frappe.db.exists(
			"LMS Batch Enrollment",
			{"batch": batch, "member": member}
		)
		if batch_enrollment:
			# Verify the batch was paid for (if it's a paid batch)
			batch_info = frappe.db.get_value("LMS Batch", batch, ["paid_batch"], as_dict=True)
			if not batch_info or not batch_info.paid_batch:
				# Free batch, user has access
				return True

			# Paid batch, check if payment was received
			batch_payment = frappe.db.exists(
				"LMS Payment",
				{
					"payment_for_document_type": "LMS Batch",
					"payment_for_document": batch,
					"member": member,
					"payment_received": 1,
				}
			)
			if batch_payment:
				return True

	return False


@frappe.whitelist()
def update_current_membership(batch, course, member):
	all_memberships = frappe.get_all("LMS Enrollment", {"member": member, "course": course})
	for membership in all_memberships:
		frappe.db.set_value("LMS Enrollment", membership.name, "is_current", 0)

	current_membership = frappe.get_all("LMS Enrollment", {"batch_old": batch, "member": member})
	if len(current_membership):
		frappe.db.set_value("LMS Enrollment", current_membership[0].name, "is_current", 1)
