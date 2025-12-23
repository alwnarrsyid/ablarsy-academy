"""API methods for the LMS."""

import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from xml.dom.minidom import parseString

import frappe
from frappe import _
from frappe.integrations.frappe_providers.frappecloud_billing import (
	current_site_info,
	is_fc_site,
)
from frappe.query_builder import DocType
from frappe.translate import get_all_translations
from frappe.utils import (
	add_days,
	cint,
	date_diff,
	flt,
	format_date,
	get_datetime,
	now,
)
from frappe.utils.response import Response

from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.utils import get_average_rating, get_lesson_count


@frappe.whitelist()
def autosave_section(section, code):
	"""Saves the code edited in one of the sections."""
	doc = frappe.get_doc(doctype="Code Revision", section=section, code=code, author=frappe.session.user)
	doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def submit_solution(exercise, code):
	"""Submits a solution.

	@exerecise: name of the exercise to submit
	@code: solution to the exercise
	"""
	ex = frappe.get_doc("LMS Exercise", exercise)
	if not ex:
		return
	doc = ex.submit(code)
	return {"name": doc.name, "creation": doc.creation}


@frappe.whitelist()
def save_current_lesson(course_name, lesson_name):
	"""Saves the current lesson for a student/mentor."""
	name = frappe.get_value(
		doctype="LMS Enrollment",
		filters={"course": course_name, "member": frappe.session.user},
		fieldname="name",
	)
	if not name:
		return
	frappe.db.set_value("LMS Enrollment", name, "current_lesson", lesson_name)


@frappe.whitelist()
def join_cohort(course, cohort, subgroup, invite_code):
	"""Creates a Cohort Join Request for given user."""
	course_doc = frappe.get_doc("LMS Course", course)
	cohort_doc = course_doc and course_doc.get_cohort(cohort)
	subgroup_doc = cohort_doc and cohort_doc.get_subgroup(subgroup)

	if not subgroup_doc or subgroup_doc.invite_code != invite_code:
		return {"ok": False, "error": "Invalid join link"}

	data = {
		"doctype": "Cohort Join Request",
		"cohort": cohort_doc.name,
		"subgroup": subgroup_doc.name,
		"email": frappe.session.user,
		"status": "Pending",
	}
	# Don't insert duplicate records
	if frappe.db.exists(data):
		return {"ok": True, "status": "record found"}
	else:
		doc = frappe.get_doc(data)
		doc.insert()
		return {"ok": True, "status": "record created"}


@frappe.whitelist()
def approve_cohort_join_request(join_request):
	r = frappe.get_doc("Cohort Join Request", join_request)
	sg = r and frappe.get_doc("Cohort Subgroup", r.subgroup)
	if not sg or r.status not in ["Pending", "Accepted"]:
		return {"ok": False, "error": "Invalid Join Request"}
	if not sg.is_manager(frappe.session.user) and "System Manager" not in frappe.get_roles():
		return {"ok": False, "error": "Permission Deined"}

	r.status = "Accepted"
	r.save()
	return {"ok": True}


@frappe.whitelist()
def reject_cohort_join_request(join_request):
	r = frappe.get_doc("Cohort Join Request", join_request)
	sg = r and frappe.get_doc("Cohort Subgroup", r.subgroup)
	if not sg or r.status not in ["Pending", "Rejected"]:
		return {"ok": False, "error": "Invalid Join Request"}
	if not sg.is_manager(frappe.session.user) and "System Manager" not in frappe.get_roles():
		return {"ok": False, "error": "Permission Deined"}

	r.status = "Rejected"
	r.save()
	return {"ok": True}


@frappe.whitelist()
def undo_reject_cohort_join_request(join_request):
	r = frappe.get_doc("Cohort Join Request", join_request)
	sg = r and frappe.get_doc("Cohort Subgroup", r.subgroup)
	# keeping Pending as well to consider the case of duplicate requests
	if not sg or r.status not in ["Pending", "Rejected"]:
		return {"ok": False, "error": "Invalid Join Request"}
	if not sg.is_manager(frappe.session.user) and "System Manager" not in frappe.get_roles():
		return {"ok": False, "error": "Permission Deined"}

	r.status = "Pending"
	r.save()
	return {"ok": True}


@frappe.whitelist(allow_guest=True)
def get_user_info():
	if frappe.session.user == "Guest":
		return None

	user = frappe.db.get_value(
		"User",
		frappe.session.user,
		["name", "email", "enabled", "user_image", "full_name", "user_type", "username"],
		as_dict=1,
	)
	user["roles"] = frappe.get_roles(user.name)
	user.is_instructor = "Course Creator" in user.roles
	user.is_moderator = "Moderator" in user.roles
	user.is_evaluator = "Batch Evaluator" in user.roles
	user.is_student = not user.is_instructor and not user.is_moderator and not user.is_evaluator
	user.is_fc_site = is_fc_site()
	user.is_system_manager = "System Manager" in user.roles
	user.is_admin = user.name == "Administrator" or "System Manager" in user.roles
	user.is_vip_student = "VIP Student" in user.roles
	user.sitename = frappe.local.site
	user.developer_mode = frappe.conf.developer_mode
	if user.is_fc_site and user.is_system_manager:
		user.site_info = current_site_info()
	return user


@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")
	return get_all_translations(language)


@frappe.whitelist()
def validate_billing_access(billing_type, name):
	access = True
	message = ""
	doctype = "LMS Batch" if billing_type == "batch" else "LMS Course"

	if frappe.session.user == "Guest":
		access = False
		message = _("Please login to continue with payment.")

	if access and billing_type not in ["course", "batch", "certificate"]:
		access = False
		message = _("Module is incorrect.")

	if access and not frappe.db.exists(doctype, name):
		access = False
		message = _("Module Name is incorrect or does not exist.")

	if access and billing_type == "course":
		membership = frappe.db.exists("LMS Enrollment", {"member": frappe.session.user, "course": name})
		if membership:
			access = False
			message = _("You are already enrolled for this course.")

	elif access and billing_type == "batch":
		membership = frappe.db.exists("LMS Batch Enrollment", {"member": frappe.session.user, "batch": name})
		if membership:
			access = False
			message = _("You are already enrolled for this batch.")

		seat_count = frappe.get_cached_value("LMS Batch", name, "seat_count")
		number_of_students = frappe.db.count("LMS Batch Enrollment", {"batch": name})
		if seat_count <= number_of_students:
			access = False
			message = _("Batch is sold out.")

		start_date = frappe.get_cached_value("LMS Batch", name, "start_date")
		if start_date and date_diff(start_date, now()) < 0:
			access = False
			message = _("Batch has already started.")

	elif access and billing_type == "certificate":
		purchased_certificate = frappe.db.exists(
			"LMS Enrollment",
			{
				"course": name,
				"member": frappe.session.user,
				"purchased_certificate": 1,
			},
		)
		if purchased_certificate:
			access = False
			message = _("You have already purchased the certificate for this course.")

	address = frappe.db.get_value(
		"Address",
		{"email_id": frappe.session.user},
		[
			"name",
			"address_title as billing_name",
			"address_line1",
			"address_line2",
			"village",
			"district",
			"city",
			"state",
			"country",
			"pincode",
			"phone",
		],
		as_dict=1,
	)

	return {"access": access, "message": message, "address": address}


@frappe.whitelist(allow_guest=True)
def get_job_details(job):
	return frappe.db.get_value(
		"Job Opportunity",
		job,
		[
			"job_title",
			"location",
			"country",
			"type",
			"work_mode",
			"company_name",
			"company_logo",
			"company_website",
			"name",
			"creation",
			"description",
			"owner",
		],
		as_dict=1,
	)


@frappe.whitelist(allow_guest=True)
def get_job_opportunities(filters=None, orFilters=None):
	if not filters:
		filters = {}

	jobs = frappe.get_all(
		"Job Opportunity",
		filters=filters,
		or_filters=orFilters,
		fields=[
			"job_title",
			"location",
			"country",
			"type",
			"work_mode",
			"company_name",
			"company_logo",
			"name",
			"creation",
			"description",
		],
		order_by="creation desc",
	)

	for job in jobs:
		job.description = frappe.utils.strip_html_tags(job.description)
		job.applicants = frappe.db.count("LMS Job Application", {"job": job.name})
	return jobs


@frappe.whitelist(allow_guest=True)
def get_chart_details():
	details = frappe._dict()
	details.enrollments = frappe.db.count("LMS Enrollment")
	details.courses = frappe.db.count(
		"LMS Course",
		{
			"published": 1,
			"upcoming": 0,
		},
	)
	details.users = frappe.db.count("User", {"enabled": 1, "name": ["not in", ("Administrator", "Guest")]})
	details.completions = frappe.db.count("LMS Enrollment", {"progress": ["like", "%100%"]})
	details.certifications = frappe.db.count("LMS Certificate", {"published": 1})
	return details


@frappe.whitelist()
def get_file_info(file_url):
	"""Get file info for the given file URL."""
	file_info = frappe.db.get_value(
		"File", {"file_url": file_url}, ["file_name", "file_size", "file_url"], as_dict=1
	)
	return file_info


@frappe.whitelist(allow_guest=True)
def get_branding():
	"""Get branding details."""
	website_settings = frappe.get_single("Website Settings")
	image_fields = ["banner_image", "footer_logo", "favicon"]

	for field in image_fields:
		if website_settings.get(field):
			file_info = get_file_info(website_settings.get(field))
			website_settings.update({field: json.loads(json.dumps(file_info))})
		else:
			website_settings.update({field: None})

	return website_settings


@frappe.whitelist()
def get_unsplash_photos(keyword=None):
	from lms.unsplash import get_by_keyword, get_list

	if keyword:
		return get_by_keyword(keyword)

	return frappe.cache().get_value("unsplash_photos", generator=get_list)


@frappe.whitelist()
def get_evaluator_details(evaluator):
	frappe.only_for("Batch Evaluator")

	if not frappe.db.exists("Google Calendar", {"user": evaluator}):
		calendar = frappe.new_doc("Google Calendar")
		calendar.update({"user": evaluator, "calendar_name": evaluator})
		calendar.insert()
	else:
		calendar = frappe.db.get_value(
			"Google Calendar", {"user": evaluator}, ["name", "authorization_code"], as_dict=1
		)

	if frappe.db.exists("Course Evaluator", {"evaluator": evaluator}):
		doc = frappe.get_doc("Course Evaluator", evaluator)
	else:
		doc = frappe.new_doc("Course Evaluator")
		doc.evaluator = evaluator
		doc.insert()

	return {
		"slots": doc.as_dict(),
		"calendar": calendar.name,
		"is_authorised": calendar.authorization_code,
	}


@frappe.whitelist(allow_guest=True)
def get_certified_participants(filters=None, start=0, page_length=100):
	or_filters = {}
	if not filters:
		filters = {}

	filters.update({"published": 1})

	category = filters.get("category")
	if category:
		del filters["category"]
		or_filters["course_title"] = ["like", f"%{category}%"]
		or_filters["batch_title"] = ["like", f"%{category}%"]

	participants = frappe.db.get_all(
		"LMS Certificate",
		filters=filters,
		or_filters=or_filters,
		fields=["member", "issue_date"],
		group_by="member",
		order_by="issue_date desc",
		start=start,
		page_length=page_length,
	)

	for participant in participants:
		count = frappe.db.count("LMS Certificate", {"member": participant.member})
		details = frappe.db.get_value(
			"User",
			participant.member,
			["full_name", "user_image", "username", "country", "headline"],
			as_dict=1,
		)
		details["certificate_count"] = count
		participant.update(details)

	return participants


@frappe.whitelist(allow_guest=True)
def get_count_of_certified_members(filters=None):
	Certificate = DocType("LMS Certificate")

	query = (
		frappe.qb.from_(Certificate).select(Certificate.member).distinct().where(Certificate.published == 1)
	)

	if filters:
		for field, value in filters.items():
			if field == "category":
				query = query.where(
					Certificate.course_title.like(f"%{value}%") | Certificate.batch_title.like(f"%{value}%")
				)
			elif field == "member_name":
				query = query.where(Certificate.member_name.like(value[1]))

	result = query.run(as_dict=True)
	return len(result) or 0


@frappe.whitelist(allow_guest=True)
def get_certification_categories():
	categories = []
	docs = frappe.get_all(
		"LMS Certificate",
		filters={
			"published": 1,
		},
		fields=["course_title", "batch_title"],
	)

	for doc in docs:
		category = doc.course_title if doc.course_title else doc.batch_title
		if category not in categories:
			categories.append(category)

	return categories


@frappe.whitelist()
def get_assigned_badges(member):
	assigned_badges = frappe.get_all(
		"LMS Badge Assignment",
		{"member": member},
		["badge"],
		as_dict=1,
	)

	for badge in assigned_badges:
		badge.update(frappe.db.get_value("LMS Badge", badge.badge, ["name", "title", "image"]))
	return assigned_badges


@frappe.whitelist()
def get_all_users():
	frappe.only_for(["Moderator", "Course Creator", "Batch Evaluator"])
	users = frappe.get_all(
		"User",
		{
			"enabled": 1,
		},
		["name", "full_name", "user_image"],
	)

	return {user.name: user for user in users}


@frappe.whitelist()
def mark_as_read(name):
	doc = frappe.get_doc("Notification Log", name)
	doc.read = 1
	doc.save(ignore_permissions=True)


@frappe.whitelist()
def mark_all_as_read():
	notifications = frappe.get_all(
		"Notification Log", {"for_user": frappe.session.user, "read": 0}, pluck="name"
	)

	for notification in notifications:
		mark_as_read(notification)


@frappe.whitelist(allow_guest=True)
def get_sidebar_settings():
	lms_settings = frappe.get_single("LMS Settings")
	sidebar_items = frappe._dict()

	items = [
		"courses",
		"batches",
		"certifications",
		"jobs",
		"statistics",
		"notifications",
		"programming_exercises",
	]
	for item in items:
		sidebar_items[item] = lms_settings.get(item)

	if len(lms_settings.sidebar_items):
		web_pages = frappe.get_all(
			"LMS Sidebar Item",
			{"parenttype": "LMS Settings", "parentfield": "sidebar_items"},
			["web_page", "route", "title as label", "icon", "name"],
		)
		for page in web_pages:
			page.to = page.route

		sidebar_items.web_pages = web_pages

	return sidebar_items


@frappe.whitelist()
def update_sidebar_item(webpage, icon):
	filters = {
		"web_page": webpage,
		"parenttype": "LMS Settings",
		"parentfield": "sidebar_items",
		"parent": "LMS Settings",
	}

	if frappe.db.exists("LMS Sidebar Item", filters):
		frappe.db.set_value("LMS Sidebar Item", filters, "icon", icon)
	else:
		doc = frappe.new_doc("LMS Sidebar Item")
		doc.update(filters)
		doc.icon = icon
		doc.insert()


@frappe.whitelist()
def delete_sidebar_item(webpage):
	return frappe.db.delete(
		"LMS Sidebar Item",
		{
			"web_page": webpage,
			"parenttype": "LMS Settings",
			"parentfield": "sidebar_items",
			"parent": "LMS Settings",
		},
	)


@frappe.whitelist()
def delete_lesson(lesson, chapter):
	# Delete Reference
	chapter = frappe.get_doc("Course Chapter", chapter)
	chapter.lessons = [row for row in chapter.lessons if row.lesson != lesson]
	chapter.save()

	# Delete progress
	frappe.db.delete("LMS Course Progress", {"lesson": lesson})

	# Delete Lesson
	frappe.db.delete("Course Lesson", lesson)


@frappe.whitelist()
def update_lesson_index(lesson, sourceChapter, targetChapter, idx):
	hasMoved = sourceChapter == targetChapter

	update_source_chapter(lesson, sourceChapter, idx, hasMoved)
	if not hasMoved:
		update_target_chapter(lesson, targetChapter, idx)


def update_source_chapter(lesson, chapter, idx, hasMoved=False):
	lessons = frappe.get_all(
		"Lesson Reference",
		{
			"parent": chapter,
		},
		pluck="lesson",
		order_by="idx",
	)

	lessons.remove(lesson)
	if not hasMoved:
		frappe.db.delete("Lesson Reference", {"parent": chapter, "lesson": lesson})
	else:
		lessons.insert(idx, lesson)

	update_index(lessons, chapter)


def update_target_chapter(lesson, chapter, idx):
	lessons = frappe.get_all(
		"Lesson Reference",
		{
			"parent": chapter,
		},
		pluck="lesson",
		order_by="idx",
	)

	lessons.insert(idx, lesson)
	new_lesson_reference = frappe.new_doc("Lesson Reference")
	new_lesson_reference.update(
		{
			"lesson": lesson,
			"parent": chapter,
			"parenttype": "Course Chapter",
			"parentfield": "lessons",
		}
	)
	new_lesson_reference.insert()
	update_index(lessons, chapter)


def update_index(lessons, chapter):
	for row in lessons:
		frappe.db.set_value(
			"Lesson Reference", {"lesson": row, "parent": chapter}, "idx", lessons.index(row) + 1
		)


@frappe.whitelist()
def update_chapter_index(chapter, course, idx):
	"""Update the index of a chapter within a course"""
	chapters = frappe.get_all(
		"Chapter Reference",
		{"parent": course},
		pluck="chapter",
		order_by="idx",
	)

	if chapter in chapters:
		chapters.remove(chapter)

	chapters.insert(idx, chapter)

	for i, chapter_name in enumerate(chapters):
		frappe.db.set_value("Chapter Reference", {"chapter": chapter_name, "parent": course}, "idx", i + 1)


@frappe.whitelist(allow_guest=True)
def get_categories(doctype, filters):
	categoryOptions = []

	categories = frappe.get_all(
		doctype,
		filters,
		pluck="category",
	)
	categories = list(set(categories))

	for category in categories:
		if category:
			categoryOptions.append({"label": category, "value": category})

	return categoryOptions


@frappe.whitelist()
def get_members(start=0, search=""):
	filters = {"enabled": 1, "name": ["not in", ["Administrator", "Guest"]]}
	or_filters = {}

	if search:
		or_filters["full_name"] = ["like", f"%{search}%"]
		or_filters["email"] = ["like", f"%{search}%"]

	members = frappe.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image", "username", "last_active"],
		or_filters=or_filters,
		page_length=20,
		start=start,
	)

	for member in members:
		roles = frappe.get_all(
			"Has Role",
			{
				"parent": member.name,
				"parenttype": "User",
			},
			pluck="role",
		)
		if "Moderator" in roles:
			member.role = "Moderator"
		elif "Course Creator" in roles:
			member.role = "Course Creator"
		elif "Batch Evaluator" in roles:
			member.role = "Batch Evaluator"
		elif "LMS Student" in roles:
			member.role = "LMS Student"

	return members


def check_app_permission():
	"""Check if the user has permission to access the app."""
	if frappe.session.user == "Administrator":
		return True

	roles = frappe.get_roles()
	lms_roles = ["Moderator", "Course Creator", "Batch Evaluator", "LMS Student"]
	if any(role in roles for role in lms_roles):
		return True

	return False


@frappe.whitelist()
def save_evaluation_details(
	member,
	course,
	batch_name,
	evaluator,
	date,
	start_time,
	end_time,
	status,
	rating,
	summary,
):
	"""
	Save evaluation details for a member against a course.
	"""
	evaluation = frappe.db.exists("LMS Certificate Evaluation", {"member": member, "course": course})

	details = {
		"date": date,
		"start_time": start_time,
		"end_time": end_time,
		"status": status,
		"rating": rating / 5,
		"summary": summary,
		"batch_name": batch_name,
	}

	if evaluation:
		frappe.db.set_value("LMS Certificate Evaluation", evaluation, details)
		return evaluation
	else:
		doc = frappe.new_doc("LMS Certificate Evaluation")
		details.update(
			{
				"member": member,
				"course": course,
				"evaluator": evaluator,
			}
		)
		doc.update(details)
		doc.insert()
		return doc.name


@frappe.whitelist()
def save_certificate_details(
	member,
	course,
	batch_name,
	evaluator,
	issue_date,
	expiry_date,
	template,
	published=True,
):
	"""
	Save certificate details for a member against a course.
	"""
	certificate = frappe.db.exists("LMS Certificate", {"member": member, "course": course})

	details = {
		"published": published,
		"issue_date": issue_date,
		"expiry_date": expiry_date,
		"template": template,
		"batch_name": batch_name,
	}

	if certificate:
		frappe.db.set_value("LMS Certificate", certificate, details)
		return certificate
	else:
		doc = frappe.new_doc("LMS Certificate")
		details.update(
			{
				"member": member,
				"course": course,
				"evaluator": evaluator,
			}
		)
		doc.update(details)
		doc.insert()
		return doc.name


@frappe.whitelist()
def delete_documents(doctype, documents):
	frappe.only_for("Moderator")
	for doc in documents:
		frappe.delete_doc(doctype, doc)


@frappe.whitelist(allow_guest=True)
def get_count(doctype, filters):
	return frappe.db.count(
		doctype,
		filters=filters,
	)


@frappe.whitelist()
def get_payment_gateway_details(payment_gateway):
	gateway = frappe.get_doc("Payment Gateway", payment_gateway)

	if gateway.gateway_controller is None:
		try:
			data = frappe.get_doc(f"{payment_gateway} Settings").as_dict()
			meta = frappe.get_meta(f"{payment_gateway} Settings").fields
			doctype = f"{payment_gateway} Settings"
			docname = f"{payment_gateway} Settings"
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))
	else:
		try:
			data = frappe.get_doc(gateway.gateway_settings, gateway.gateway_controller).as_dict()
			meta = frappe.get_meta(gateway.gateway_settings).fields
			doctype = gateway.gateway_settings
			docname = gateway.gateway_controller
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))

	gateway_fields = get_transformed_fields(meta, data)

	return {
		"fields": gateway_fields,
		"data": data,
		"doctype": doctype,
		"docname": docname,
	}


def get_transformed_fields(meta, data=None):
	transformed_fields = []
	for row in meta:
		if row.fieldtype not in ["Column Break", "Section Break"]:
			if row.fieldtype in ["Attach", "Attach Image"]:
				fieldtype = "Upload"
				if data and data.get(row.fieldname):
					data[row.fieldname] = get_file_info(data.get(row.fieldname))
			elif row.fieldtype == "Check":
				fieldtype = "checkbox"
			else:
				fieldtype = row.fieldtype

			transformed_fields.append(
				{
					"label": row.label,
					"name": row.fieldname,
					"type": fieldtype,
				}
			)

	return transformed_fields


@frappe.whitelist()
def get_new_gateway_fields(doctype):
	try:
		meta = frappe.get_meta(doctype).fields
	except Exception:
		frappe.throw(_("{0} not found").format(doctype))

	transformed_fields = get_transformed_fields(meta)

	return transformed_fields


def update_course_statistics():
	courses = frappe.get_all("LMS Course", fields=["name"])

	for course in courses:
		lessons = get_lesson_count(course.name)

		enrollments = frappe.db.count("LMS Enrollment", {"course": course.name, "member_type": "Student"})

		avg_rating = get_average_rating(course.name) or 0
		avg_rating = flt(avg_rating, frappe.get_system_settings("float_precision") or 3)

		frappe.db.set_value(
			"LMS Course",
			course.name,
			{"lessons": lessons, "enrollments": enrollments, "rating": avg_rating},
		)


@frappe.whitelist()
def get_announcements(batch):
	communications = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": "LMS Batch",
			"reference_name": batch,
		},
		fields=[
			"subject",
			"content",
			"recipients",
			"cc",
			"communication_date",
			"sender",
			"sender_full_name",
		],
		order_by="communication_date desc",
	)

	for communication in communications:
		communication.image = frappe.get_cached_value("User", communication.sender, "user_image")

	return communications


@frappe.whitelist()
def delete_course(course):
	chapters = frappe.get_all("Course Chapter", {"course": course}, pluck="name")

	chapter_references = frappe.get_all("Chapter Reference", {"parent": course}, pluck="name")

	for chapter in chapters:
		lessons = frappe.get_all("Course Lesson", {"chapter": chapter}, pluck="name")

		lesson_references = frappe.get_all("Lesson Reference", {"parent": chapter}, pluck="name")

		for lesson in lesson_references:
			frappe.delete_doc("Lesson Reference", lesson)

		for lesson in lessons:
			topics = frappe.get_all(
				"Discussion Topic",
				{"reference_doctype": "Course Lesson", "reference_docname": lesson},
				pluck="name",
			)

			for topic in topics:
				frappe.db.delete("Discussion Reply", {"topic": topic})

				frappe.db.delete("Discussion Topic", topic)

			frappe.delete_doc("Course Lesson", lesson)

	for chapter in chapter_references:
		frappe.delete_doc("Chapter Reference", chapter)

	for chapter in chapters:
		frappe.delete_doc("Course Chapter", chapter)

	frappe.db.delete("LMS Course Progress", {"course": course})
	frappe.db.delete("LMS Quiz", {"course": course})
	frappe.db.delete("LMS Quiz Submission", {"course": course})
	frappe.db.delete("LMS Enrollment", {"course": course})
	frappe.delete_doc("LMS Course", course)


@frappe.whitelist()
def delete_batch(batch):
	frappe.db.delete("LMS Batch Enrollment", {"batch": batch})
	frappe.db.delete("Batch Course", {"parent": batch, "parenttype": "LMS Batch"})
	frappe.db.delete("LMS Assessment", {"parent": batch, "parenttype": "LMS Batch"})
	frappe.db.delete("LMS Batch Timetable", {"parent": batch, "parenttype": "LMS Batch"})
	frappe.db.delete("LMS Batch Feedback", {"batch": batch})
	delete_batch_discussions(batch)
	frappe.db.delete("LMS Batch", batch)


def delete_batch_discussions(batch):
	topics = frappe.get_all(
		"Discussion Topic",
		{"reference_doctype": "LMS Batch", "reference_docname": batch},
		pluck="name",
	)

	for topic in topics:
		frappe.db.delete("Discussion Reply", {"topic": topic})
		frappe.db.delete("Discussion Topic", topic)


def give_discussions_permission():
	doctypes = ["Discussion Topic", "Discussion Reply"]
	roles = ["LMS Student", "Course Creator", "Moderator", "Batch Evaluator"]
	for doctype in doctypes:
		for role in roles:
			if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
				frappe.get_doc(
					{
						"doctype": "Custom DocPerm",
						"parent": doctype,
						"role": role,
						"read": 1,
						"write": 1,
						"create": 1,
						"delete": 1,
						"if_owner": 0 if role == "Moderator" else 1,
					}
				).save(ignore_permissions=True)


@frappe.whitelist()
def upsert_chapter(title, course, is_scorm_package, scorm_package, name=None):
	values = frappe._dict({"title": title, "course": course, "is_scorm_package": is_scorm_package})

	if is_scorm_package:
		scorm_package = frappe._dict(scorm_package)
		extract_path = extract_package(course, title, scorm_package)

		values.update(
			{
				"scorm_package": scorm_package.name,
				"scorm_package_path": extract_path.split("public")[1],
				"manifest_file": get_manifest_file(extract_path).split("public")[1],
				"launch_file": get_launch_file(extract_path).split("public")[1],
			}
		)

	if name:
		chapter = frappe.get_doc("Course Chapter", name)
	else:
		chapter = frappe.new_doc("Course Chapter")

	chapter.update(values)
	chapter.save()

	if is_scorm_package and not len(chapter.lessons):
		add_lesson(title, chapter.name, course, 1)

	return chapter


def extract_package(course, title, scorm_package):
	package = frappe.get_doc("File", scorm_package.name)
	zip_path = package.get_full_path()
	# check_for_malicious_code(zip_path)
	extract_path = frappe.get_site_path("public", "scorm", course, title)
	zipfile.ZipFile(zip_path).extractall(extract_path)
	return extract_path


def check_for_malicious_code(zip_path):
	suspicious_patterns = [
		# Unsafe inline JavaScript
		r'on(click|load|mouseover|error|submit|focus|blur|change|keyup|keydown|keypress|resize)=".*?"',  # Inline event handlers (e.g., onerror, onclick)
		r'<script.*?src=["\']http',  # External script tags
		r"eval\(",  # Usage of eval()
		r"Function\(",  # Usage of Function constructor
		r"(btoa|atob)\(",  # Base64 encoding/decoding
		# Dangerous XML patterns
		r"<!ENTITY",  # XXE-related
		r"<\?xml-stylesheet .*?>",  # External stylesheets in XML
	]

	with zipfile.ZipFile(zip_path, "r") as zf:
		for file_name in zf.namelist():
			if file_name.endswith((".html", ".js", ".xml")):
				with zf.open(file_name) as file:
					content = file.read().decode("utf-8", errors="ignore")
					for pattern in suspicious_patterns:
						if re.search(pattern, content):
							frappe.throw(_("Suspicious pattern found in {0}: {1}").format(file_name, pattern))


def get_manifest_file(extract_path):
	manifest_file = None
	for root, _dirs, files in os.walk(extract_path):
		for file in files:
			if file == "imsmanifest.xml":
				manifest_file = os.path.join(root, file)
				break
		if manifest_file:
			break
	return manifest_file


def get_launch_file(extract_path):
	launch_file = None
	manifest_file = get_manifest_file(extract_path)

	if manifest_file:
		with open(manifest_file) as file:
			data = file.read()
			dom = parseString(data)
			resource = dom.getElementsByTagName("resource")
			for res in resource:
				if (
					res.getAttribute("adlcp:scormtype") == "sco"
					or res.getAttribute("adlcp:scormType") == "sco"
				):
					launch_file = res.getAttribute("href")
					break

		if launch_file:
			launch_file = os.path.join(os.path.dirname(manifest_file), launch_file)

	return launch_file


def add_lesson(title, chapter, course, idx):
	lesson = frappe.new_doc("Course Lesson")
	lesson.update(
		{
			"title": title,
			"chapter": chapter,
			"course": course,
		}
	)
	lesson.insert()

	lesson_reference = frappe.new_doc("Lesson Reference")
	lesson_reference.update(
		{
			"lesson": lesson.name,
			"idx": idx,
			"parent": chapter,
			"parenttype": "Course Chapter",
			"parentfield": "lessons",
		}
	)
	lesson_reference.insert()


@frappe.whitelist()
def delete_chapter(chapter):
	chapterInfo = frappe.db.get_value(
		"Course Chapter", chapter, ["is_scorm_package", "scorm_package_path"], as_dict=True
	)

	if chapterInfo.is_scorm_package:
		delete_scorm_package(chapterInfo.scorm_package_path)

	frappe.db.delete("Chapter Reference", {"chapter": chapter})
	frappe.db.delete("Lesson Reference", {"parent": chapter})
	frappe.db.delete("Course Lesson", {"chapter": chapter})
	frappe.db.delete("Course Chapter", chapter)


def delete_scorm_package(scorm_package_path):
	scorm_package_path = frappe.get_site_path("public", scorm_package_path[1:])
	if os.path.exists(scorm_package_path):
		shutil.rmtree(scorm_package_path)


@frappe.whitelist()
def mark_lesson_progress(course, chapter_number, lesson_number):
	chapter_name = frappe.get_value("Chapter Reference", {"parent": course, "idx": chapter_number}, "chapter")
	lesson_name = frappe.get_value(
		"Lesson Reference", {"parent": chapter_name, "idx": lesson_number}, "lesson"
	)
	save_progress(lesson_name, course)


@frappe.whitelist()
def get_heatmap_data(member=None, base_days=200):
	if not member:
		member = frappe.session.user

	base_date, start_date, number_of_days, days = calculate_date_ranges(base_days)
	date_count = initialize_date_count(days)

	lesson_completions, quiz_submissions, assignment_submissions = fetch_activity_data(member, start_date)
	count_dates(lesson_completions, date_count)
	count_dates(quiz_submissions, date_count)
	count_dates(assignment_submissions, date_count)

	heatmap_data, labels, total_activities, weeks = prepare_heatmap_data(
		start_date, number_of_days, date_count
	)

	return {
		"heatmap_data": heatmap_data,
		"labels": labels,
		"total_activities": total_activities,
		"weeks": weeks,
	}


def calculate_date_ranges(base_days):
	today = format_date(now(), "YYYY-MM-dd")
	day_today = get_datetime(today).strftime("%w")
	padding_end = 6 - cint(day_today)

	base_date = add_days(today, -base_days)
	day_of_base_date = cint(get_datetime(base_date).strftime("%w"))
	start_date = add_days(base_date, -day_of_base_date)
	number_of_days = base_days + day_of_base_date + padding_end
	days = [add_days(start_date, i) for i in range(number_of_days + 1)]

	return base_date, start_date, number_of_days, days


def initialize_date_count(days):
	return {format_date(day, "YYYY-MM-dd"): 0 for day in days}


def fetch_activity_data(member, start_date):
	lesson_completions = frappe.get_all(
		"LMS Course Progress",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date], "status": "Complete"},
	)

	quiz_submissions = frappe.get_all(
		"LMS Quiz Submission",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	assignment_submissions = frappe.get_all(
		"LMS Assignment Submission",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	return lesson_completions, quiz_submissions, assignment_submissions


def count_dates(data, date_count):
	for entry in data:
		date = format_date(entry.creation, "YYYY-MM-dd")
		if date in date_count:
			date_count[date] += 1


def prepare_heatmap_data(start_date, number_of_days, date_count):
	days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
	heatmap_data = {day: [] for day in days_of_week}
	week_count = -(number_of_days // -7)
	labels = [None] * week_count
	last_seen_month = None
	sorted_dates = sorted(date_count.keys())

	for date in sorted_dates:
		activity_count = date_count[date]
		day_of_week = get_datetime(date).strftime("%a")
		current_month = get_datetime(date).strftime("%b")
		column_index = get_week_difference(start_date, date)

		if 0 <= column_index < week_count:
			heatmap_data[day_of_week].append(
				{
					"date": date,
					"count": activity_count,
					"label": f"{activity_count} activities on {format_date(date, 'dd MMM')}",
				}
			)

			if last_seen_month != current_month:
				labels[column_index] = current_month
				last_seen_month = current_month

	for index, label in enumerate(labels):
		if not label:
			labels[index] = ""

	formatted_heatmap_data = [{"name": day, "data": heatmap_data[day]} for day in days_of_week]

	total_activities = sum(date_count.values())
	return formatted_heatmap_data, labels, total_activities, week_count


def get_week_difference(start_date, current_date):
	diff_in_days = date_diff(current_date, start_date)
	return diff_in_days // 7


@frappe.whitelist()
def get_notifications(filters):
	notifications = frappe.get_all(
		"Notification Log",
		filters,
		["subject", "from_user", "link", "read", "name"],
		order_by="creation desc",
	)

	for notification in notifications:
		from_user_details = frappe.db.get_value(
			"User", notification.from_user, ["full_name", "user_image"], as_dict=1
		)
		notification.update(from_user_details)

	return notifications


@frappe.whitelist(allow_guest=True)
def get_lms_settings():
	allowed_fields = [
		"allow_guest_access",
		"prevent_skipping_videos",
		"contact_us_email",
		"contact_us_url",
		"livecode_url",
		"disable_pwa",
	]

	settings = frappe._dict()
	for field in allowed_fields:
		settings[field] = frappe.get_cached_value("LMS Settings", None, field)

	return settings


@frappe.whitelist()
def cancel_evaluation(evaluation):
	evaluation = frappe._dict(evaluation)

	if evaluation.member != frappe.session.user:
		return

	frappe.db.set_value("LMS Certificate Request", evaluation.name, "status", "Cancelled")
	events = frappe.get_all(
		"Event Participants",
		{
			"email": evaluation.member,
		},
		["parent", "name"],
	)

	for event in events:
		info = frappe.db.get_value("Event", event.parent, ["starts_on", "subject"], as_dict=1)
		date = str(info.starts_on).split(" ")[0]

		if date == str(evaluation.date.format("YYYY-MM-DD")) and evaluation.member_name in info.subject:
			communication = frappe.db.get_value(
				"Communication",
				{"reference_doctype": "Event", "reference_name": event.parent},
				"name",
			)
			if communication:
				frappe.delete_doc("Communication", communication, ignore_permissions=True)

			frappe.delete_doc("Event Participants", event.name, ignore_permissions=True)
			frappe.delete_doc("Event", event.parent, ignore_permissions=True)


@frappe.whitelist()
def get_certification_details(course):
	membership = None
	filters = {"course": course, "member": frappe.session.user}

	if frappe.db.exists("LMS Enrollment", filters):
		membership = frappe.db.get_value(
			"LMS Enrollment",
			filters,
			["name", "purchased_certificate"],
			as_dict=1,
		)

	paid_certificate = frappe.db.get_value("LMS Course", course, "paid_certificate")
	certificate = frappe.db.get_value(
		"LMS Certificate",
		{"member": frappe.session.user, "course": course},
		["name", "template"],
		as_dict=1,
	)

	return {
		"membership": membership,
		"paid_certificate": paid_certificate,
		"certificate": certificate,
	}


@frappe.whitelist()
def save_role(user, role, value):
	frappe.only_for("Moderator")
	if cint(value):
		doc = frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": user,
				"role": role,
				"parenttype": "User",
				"parentfield": "roles",
			}
		)
		doc.save(ignore_permissions=True)
	else:
		frappe.db.delete("Has Role", {"parent": user, "role": role})
	frappe.clear_cache(user=user)
	return True


@frappe.whitelist()
def add_an_evaluator(email):
	frappe.only_for("Moderator")
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": email.split("@")[0].capitalize(),
				"enabled": 1,
			}
		)
		user.insert()
		user.add_roles("Batch Evaluator")

	evaluator = frappe.new_doc("Course Evaluator")
	evaluator.evaluator = email
	evaluator.insert()

	return evaluator


@frappe.whitelist()
def delete_evaluator(evaluator):
	frappe.only_for("Moderator")
	if not frappe.db.exists("Course Evaluator", evaluator):
		frappe.throw(_("Evaluator does not exist."))

	frappe.db.delete("Has Role", {"parent": evaluator, "role": "Batch Evaluator"})
	frappe.db.delete("Course Evaluator", evaluator)


@frappe.whitelist()
def capture_user_persona(responses):
	frappe.only_for("System Manager")
	data = frappe.parse_json(responses)
	data = json.dumps(data)
	response = frappe.integrations.utils.make_post_request(
		"https://school.frappe.io/api/method/capture-persona",
		data={"response": data},
	)
	if response.get("message").get("name"):
		frappe.db.set_single_value("LMS Settings", "persona_captured", True)
	return response


@frappe.whitelist()
def get_meta_info(type, route):
	if frappe.db.exists("Website Meta Tag", {"parent": f"{type}/{route}"}):
		meta_tags = frappe.get_all(
			"Website Meta Tag",
			{
				"parent": f"{type}/{route}",
			},
			["name", "key", "value"],
		)

		return meta_tags

	return []


@frappe.whitelist()
def update_meta_info(meta_type, route, meta_tags):
	validate_meta_data_permissions(meta_type)
	validate_meta_tags(meta_tags)

	parent_name = f"{meta_type}/{route}"
	for tag in meta_tags:
		existing_tag = frappe.db.exists(
			"Website Meta Tag",
			{
				"parent": parent_name,
				"parenttype": "Website Route Meta",
				"parentfield": "meta_tags",
				"key": tag["key"],
			},
		)
		if existing_tag:
			if not tag.get("value"):
				frappe.db.delete("Website Meta Tag", existing_tag)
				continue
			frappe.db.set_value("Website Meta Tag", existing_tag, "value", tag["value"])
		elif tag.get("value"):
			tag_properties = {
				"parent": parent_name,
				"parenttype": "Website Route Meta",
				"parentfield": "meta_tags",
				"key": tag["key"],
				"value": tag["value"],
			}

			parent_exists = frappe.db.exists("Website Route Meta", parent_name)
			if not parent_exists:
				create_meta(parent_name, tag_properties)
			else:
				create_meta_tag(tag_properties)


def validate_meta_tags(meta_tags):
	if not isinstance(meta_tags, list):
		frappe.throw(_("Meta tags should be a list."))


def create_meta(parent_name, tag_properties):
	route_meta = frappe.new_doc("Website Route Meta")
	route_meta.update(
		{
			"__newname": parent_name,
		}
	)
	route_meta.append("meta_tags", tag_properties)
	route_meta.insert()


def create_meta_tag(tag_properties):
	new_tag = frappe.new_doc("Website Meta Tag")
	new_tag.update(tag_properties)
	new_tag.insert()


def validate_meta_data_permissions(meta_type):
	roles = frappe.get_roles()

	if meta_type == "courses":
		if not ("Course Creator" in roles or "Moderator" in roles):
			frappe.throw(_("You do not have permission to update meta tags."))

	elif meta_type == "batches":
		if not ("Batch Evaluator" in roles or "Moderator" in roles):
			frappe.throw(_("You do not have permission to update meta tags."))


@frappe.whitelist()
def create_programming_exercise_submission(exercise, submission, code, test_cases):
	if submission == "new":
		return make_new_exercise_submission(exercise, code, test_cases)
	else:
		update_exercise_submission(submission, code, test_cases)


def make_new_exercise_submission(exercise, code, test_cases):
	submission = frappe.new_doc("LMS Programming Exercise Submission")
	submission.exercise = exercise
	submission.member = frappe.session.user
	submission.code = code

	for test_case in test_cases:
		submission.append(
			"test_cases",
			{
				"input": test_case.get("input"),
				"output": test_case.get("output"),
				"expected_output": test_case.get("expected_output"),
				"status": test_case.get("status", test_case.get("status", "Failed")),
			},
		)

	submission.status = get_exercise_status(test_cases)
	submission.insert()
	return submission.name


def update_exercise_submission(submission, code, test_cases):
	update_test_cases(test_cases, submission)
	status = get_exercise_status(test_cases)
	frappe.db.set_value("LMS Programming Exercise Submission", submission, {"status": status, "code": code})


def get_exercise_status(test_cases):
	if not test_cases:
		return "Failed"

	if all(row.get("status", "Failed") == "Passed" for row in test_cases):
		return "Passed"
	else:
		return "Failed"


def update_test_cases(test_cases, submission):
	frappe.db.delete("LMS Test Case Submission", {"parent": submission})
	for row in test_cases:
		test_case = frappe.new_doc("LMS Test Case Submission")
		test_case.update(
			{
				"parent": submission,
				"parenttype": "LMS Programming Exercise Submission",
				"parentfield": "test_cases",
				"input": row.get("input"),
				"output": row.get("output"),
				"expected_output": row.get("expected_output"),
				"status": row.get("status", "Failed"),
			}
		)
		test_case.insert()


@frappe.whitelist()
def track_video_watch_duration(lesson, videos):
	"""
	Track the watch duration of videos in a lesson.
	"""
	if not isinstance(videos, list):
		videos = json.loads(videos)

	for video in videos:
		filters = {
			"lesson": lesson,
			"source": video.get("source"),
			"member": frappe.session.user,
		}
		existing_record = frappe.db.get_value(
			"LMS Video Watch Duration", filters, ["name", "watch_time"], as_dict=True
		)
		if existing_record and flt(existing_record.watch_time) < flt(video.get("watch_time")):
			frappe.db.set_value(
				"LMS Video Watch Duration",
				filters,
				"watch_time",
				video.get("watch_time"),
			)
		elif not existing_record:
			track_new_watch_time(lesson, video)


def track_new_watch_time(lesson, video):
	doc = frappe.new_doc("LMS Video Watch Duration")
	doc.lesson = lesson
	doc.source = video.get("source")
	doc.watch_time = video.get("watch_time")
	doc.member = frappe.session.user
	doc.save()


@frappe.whitelist()
def get_course_progress_distribution(course):
	all_progress = frappe.get_all(
		"LMS Enrollment",
		{
			"course": course,
		},
		pluck="progress",
	)

	average_progress = get_average_course_progress(all_progress)
	progress_distribution = get_progress_distribution(all_progress)

	return {
		"average_progress": average_progress,
		"progress_distribution": progress_distribution,
	}


def get_average_course_progress(progress_list):
	if not progress_list:
		return 0
	average_progress = sum(progress_list) / len(progress_list)
	return flt(average_progress, frappe.get_system_settings("float_precision") or 3)


def get_progress_distribution(progressList):
	distribution = [
		{
			"category": "0-20%",
			"count": len([p for p in progressList if 0 <= p < 20]),
		},
		{
			"category": "20-40%",
			"count": len([p for p in progressList if 20 <= p < 40]),
		},
		{
			"category": "40-60%",
			"count": len([p for p in progressList if 40 <= p < 60]),
		},
		{
			"category": "60-80%",
			"count": len([p for p in progressList if 60 <= p < 80]),
		},
		{
			"category": "80-100%",
			"count": len([p for p in progressList if 80 <= p <= 100]),
		},
	]

	return distribution


@frappe.whitelist(allow_guest=True)
def get_pwa_manifest():
	title = frappe.db.get_single_value("Website Settings", "app_name") or "Frappe Learning"
	banner_image = frappe.db.get_single_value("Website Settings", "banner_image")

	manifest = {
		"name": title,
		"short_name": title,
		"description": "Easy to use, 100% open source Learning Management System",
		"start_url": "/lms",
		"icons": [
			{
				"src": banner_image or "/assets/lms/frontend/manifest/manifest-icon-192.maskable.png",
				"sizes": "192x192",
				"type": "image/png",
				"purpose": "maskable any",
			}
		],
	}

	return Response(json.dumps(manifest), status=200, content_type="application/manifest+json")


@frappe.whitelist()
def get_profile_details(username):
	details = frappe.db.get_value(
		"User",
		{"username": username},
		[
			"first_name",
			"last_name",
			"full_name",
			"name",
			"username",
			"user_image",
			"bio",
			"headline",
			"language",
			"cover_image",
		],
		as_dict=True,
	)

	details.roles = frappe.get_roles(details.name)
	return details


# ============================================
# REFERRAL SYSTEM APIs
# ============================================

@frappe.whitelist()
def get_referral_stats(user=None):
	"""
	Get aggregated referral statistics for a user.
	Returns: total_referrals, total_earnings, pending_payout, paid_payout
	"""
	if not user:
		user = frappe.session.user

	# Count referred users
	total_referrals = frappe.db.count("User", {"referred_by": user})

	# Get commission stats
	commissions = frappe.get_all(
		"LMS Referral Commission",
		filters={"referrer": user},
		fields=["commission_amount", "payout_status"]
	)

	total_earnings = sum(c.commission_amount or 0 for c in commissions)
	pending_payout = sum(c.commission_amount or 0 for c in commissions if c.payout_status == "Unpaid")
	paid_payout = sum(c.commission_amount or 0 for c in commissions if c.payout_status == "Paid")

	# Get user's referral code
	referral_code = frappe.db.get_value("User", user, "referral_code") or ""

	return {
		"referral_code": referral_code,
		"total_referrals": total_referrals,
		"total_earnings": total_earnings,
		"pending_payout": pending_payout,
		"paid_payout": paid_payout,
	}


@frappe.whitelist()
def get_referral_commissions(user=None, status=None, start=0, limit=20):
	"""
	Get list of referral commission records for a user.
	For n8n integration and profile dashboard.
	"""
	if not user:
		user = frappe.session.user

	filters = {"referrer": user}
	if status:
		filters["payout_status"] = status

	commissions = frappe.get_all(
		"LMS Referral Commission",
		filters=filters,
		fields=[
			"name", "referred_student", "payment", "purchase_type",
			"purchase_document", "total_amount", "commission_amount",
			"payout_status", "payout_date", "creation"
		],
		order_by="creation desc",
		start=cint(start),
		limit_page_length=cint(limit)
	)

	# Enrich with student name
	for c in commissions:
		c.student_name = frappe.db.get_value("User", c.referred_student, "full_name")
		if c.purchase_document:
			c.purchase_title = frappe.db.get_value(c.purchase_type, c.purchase_document, "title")

	return commissions


@frappe.whitelist()
def create_referral_commission(data):
	"""Create a new referral commission record. Admin only."""
	frappe.only_for("System Manager")

	if isinstance(data, str):
		data = json.loads(data)

	doc = frappe.get_doc({
		"doctype": "LMS Referral Commission",
		**data
	})
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def update_referral_commission(name, data):
	"""Update a referral commission record. Admin only."""
	frappe.only_for("System Manager")

	if isinstance(data, str):
		data = json.loads(data)

	doc = frappe.get_doc("LMS Referral Commission", name)
	doc.update(data)
	doc.save(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def delete_referral_commission(name):
	"""Delete a referral commission record. Admin only."""
	frappe.only_for("System Manager")

	frappe.delete_doc("LMS Referral Commission", name)
	return True


@frappe.whitelist()
def get_all_users_data(filters=None, start=0, limit=50):
	"""
	Get all users with referral information for n8n sync.
	Requires System Manager role.
	"""
	frappe.only_for("System Manager")

	user_filters = {"enabled": 1, "name": ["not in", ["Administrator", "Guest"]]}
	if filters:
		user_filters.update(filters if isinstance(filters, dict) else json.loads(filters))

	users = frappe.get_all(
		"User",
		filters=user_filters,
		fields=[
			"name", "email", "full_name", "username", "user_image",
			"referral_code", "referred_by", "creation", "last_active"
		],
		order_by="creation desc",
		start=cint(start),
		limit_page_length=cint(limit)
	)

	# Enrich with referral stats
	for user in users:
		user.referral_count = frappe.db.count("User", {"referred_by": user.name})
		if user.referred_by:
			user.referred_by_name = frappe.db.get_value("User", user.referred_by, "full_name")

	return users


@frappe.whitelist()
def get_payment_enrollments(filters=None, start=0, limit=50):
	"""
	Get payment and enrollment data for n8n integration.
	Requires System Manager role.
	"""
	frappe.only_for("System Manager")

	payment_filters = {}
	if filters:
		payment_filters.update(filters if isinstance(filters, dict) else json.loads(filters))

	payments = frappe.get_all(
		"LMS Payment",
		filters=payment_filters,
		fields=[
			"name", "member", "billing_name", "amount", "currency",
			"payment_for_document_type", "payment_for_document",
			"status", "payment_received", "creation"
		],
		order_by="creation desc",
		start=cint(start),
		limit_page_length=cint(limit)
	)

	# Enrich with document title and member info
	for p in payments:
		p.member_name = frappe.db.get_value("User", p.member, "full_name")
		if p.payment_for_document:
			p.document_title = frappe.db.get_value(
				p.payment_for_document_type,
				p.payment_for_document,
				"title"
			)

	return payments


def generate_referral_code(user_email):
	"""
	Generate a unique referral code for a user.
	Format: ABL-XXXX (4 random alphanumeric characters)
	"""
	import random
	import string

	prefix = "ABL"
	chars = string.ascii_uppercase + string.digits

	while True:
		code = f"{prefix}-{''.join(random.choices(chars, k=4))}"
		if not frappe.db.exists("User", {"referral_code": code}):
			return code


def create_referral_commission(payment_doc):
	"""
	Create a referral commission record when a referred user makes a purchase.
	Called from payment gateway after successful payment.
	"""
	member = payment_doc.member

	# Check if this user was referred
	referred_by = frappe.db.get_value("User", member, "referred_by")
	if not referred_by:
		return None

	# Check if commission already exists for this payment
	if frappe.db.exists("LMS Referral Commission", {"payment": payment_doc.name}):
		return None

	# Calculate commission (10%)
	commission_rate = 10
	commission_amount = (payment_doc.amount * commission_rate) / 100

	# Create commission record
	commission = frappe.new_doc("LMS Referral Commission")
	commission.update({
		"referrer": referred_by,
		"referred_student": member,
		"payment": payment_doc.name,
		"purchase_type": payment_doc.payment_for_document_type,
		"purchase_document": payment_doc.payment_for_document,
		"total_amount": payment_doc.amount,
		"commission_rate": commission_rate,
		"commission_amount": commission_amount,
		"payout_status": "Unpaid"
	})
	commission.insert(ignore_permissions=True)

	return commission.name


# ============================================
# N8N Integration APIs
# ============================================

@frappe.whitelist(allow_guest=True)
def generate_verification_link(email, api_key=None):
	"""
	Generate a fresh reset password key for email verification.
	Called by n8n after user signup webhook.

	Args:
		email: User email address
		api_key: Secret API key for authentication

	Returns:
		dict with verification_link and user info
	"""
	# Validate API key (set this in site_config.json as n8n_api_key)
	expected_key = frappe.conf.get("n8n_api_key", "")
	if not expected_key or api_key != expected_key:
		frappe.throw(_("Invalid API key"), frappe.AuthenticationError)

	# Check if user exists
	if not frappe.db.exists("User", email):
		frappe.throw(_("User not found"), frappe.DoesNotExistError)

	# Generate new reset key
	import hashlib
	from frappe.utils import random_string
	plain_key = random_string(32)

	# Hash the key (Frappe validates against hashed key)
	hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()

	# Update user with HASHED key
	frappe.db.set_value("User", email, "reset_password_key", hashed_key)
	frappe.db.commit()

	# Get user details
	user = frappe.db.get_value(
		"User",
		email,
		["full_name", "name", "referred_by", "referral_code"],
		as_dict=True
	)

	# Return plain key for email link
	return {
		"success": True,
		"email": email,
		"full_name": user.full_name,
		"referred_by": user.referred_by or "",
		"referral_code": user.referral_code or "",
		"reset_key": plain_key,
		"verification_link": f"https://lms.ablarsy.com/update-password?key={plain_key}"
	}


@frappe.whitelist(allow_guest=True)
def generate_otp(email, api_key=None):
	"""
	Generate a 6-digit OTP for email verification.
	Called by n8n after user signup webhook.

	Args:
		email: User email address
		api_key: Secret API key for authentication

	Returns:
		dict with OTP and user info for email
	"""
	import random

	# Validate API key
	expected_key = frappe.conf.get("n8n_api_key", "")
	if not expected_key or api_key != expected_key:
		frappe.throw(_("Invalid API key"), frappe.AuthenticationError)

	# Check if user exists
	if not frappe.db.exists("User", email):
		frappe.throw(_("User not found"), frappe.DoesNotExistError)

	# Generate 6-digit OTP
	otp = str(random.randint(100000, 999999))

	# Store OTP in cache with 10 minute expiry
	cache_key = f"signup_otp:{email}"
	frappe.cache.set_value(cache_key, otp, expires_in_sec=600)

	# Get user details
	user = frappe.db.get_value(
		"User",
		email,
		["full_name", "name"],
		as_dict=True
	)

	return {
		"success": True,
		"email": email,
		"full_name": user.full_name,
		"otp": otp
	}


@frappe.whitelist(allow_guest=True)
def verify_otp(email, otp):
	"""
	Verify OTP and return reset password key if valid.
	Called from frontend verify-otp page.

	Args:
		email: User email address
		otp: 6-digit OTP entered by user

	Returns:
		dict with reset_password_key if OTP is valid
	"""
	import hashlib
	from frappe.utils import random_string

	# Check if user exists
	if not frappe.db.exists("User", email):
		return {"success": False, "message": _("User not found")}

	# Get stored OTP from cache
	cache_key = f"signup_otp:{email}"
	stored_otp = frappe.cache.get_value(cache_key)

	if not stored_otp:
		return {"success": False, "message": _("OTP expired. Please request a new one.")}

	if stored_otp != otp:
		return {"success": False, "message": _("Invalid OTP. Please try again.")}

	# OTP is valid - delete it from cache
	frappe.cache.delete_value(cache_key)

	# Generate reset password key
	plain_key = random_string(32)
	hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()

	# Update user with hashed key
	frappe.db.set_value("User", email, "reset_password_key", hashed_key)
	frappe.db.commit()

	return {
		"success": True,
		"message": _("OTP verified successfully"),
		"reset_key": plain_key
	}


@frappe.whitelist(allow_guest=True)
def resend_otp(email):
	"""
	Resend OTP for email verification.
	Triggers n8n webhook to send new OTP.

	Args:
		email: User email address

	Returns:
		dict with success status
	"""
	# Check if user exists
	if not frappe.db.exists("User", email):
		return {"success": False, "message": _("User not found")}

	# Just return success - n8n will handle the actual sending
	# Frontend should call n8n webhook to trigger new OTP
	return {
		"success": True,
		"message": _("Please wait for new OTP")
	}


@frappe.whitelist(allow_guest=True)
def global_search(query):
	"""
	Global search for courses and batches.

	Args:
		query: Search query string

	Returns:
		dict with courses and batches lists
	"""
	from lms.lms.utils import get_course_details, get_batch_card_details

	if not query or len(query) < 2:
		return {"courses": [], "batches": []}

	# Search Courses
	courses = frappe.get_all(
		"LMS Course",
		filters={
			"published": 1,
			"title": ["like", f"%{query}%"]
		},
		fields=["name", "title", "short_introduction", "image", "paid_course", "course_price", "currency"],
		limit=10,
		order_by="title asc"
	)

	# Get course details
	course_results = []
	for course in courses:
		try:
			details = get_course_details(course.name)
			course_results.append(details)
		except Exception:
			continue

	# Search Batches
	batches = frappe.get_all(
		"LMS Batch",
		filters={
			"published": 1,
			"title": ["like", f"%{query}%"]
		},
		fields=[
			"name", "title", "description", "seat_count", "paid_batch",
			"amount", "amount_usd", "currency", "start_date", "end_date",
			"start_time", "end_time", "timezone", "category"
		],
		limit=10,
		order_by="start_date asc"
	)

	# Get batch card details
	batch_results = get_batch_card_details(batches)

	return {
		"courses": course_results,
		"batches": batch_results
	}


@frappe.whitelist()
def get_payout_info():
	"""Get user's payout information for receiving referral commissions."""
	user = frappe.session.user

	if user == "Guest":
		frappe.throw(_("Please login to view payout information"))

	payout_info = frappe.db.get_value(
		"User",
		user,
		["payout_method", "payout_phone", "payout_bank", "payout_account_number", "payout_account_name"],
		as_dict=True
	)

	return {
		"payout_method": payout_info.payout_method or "",
		"payout_phone": payout_info.payout_phone or "",
		"payout_bank": payout_info.payout_bank or "",
		"payout_account_number": payout_info.payout_account_number or "",
		"payout_account_name": payout_info.payout_account_name or "",
	}


@frappe.whitelist()
def update_payout_info(payout_method=None, payout_phone=None, payout_bank=None,
                       payout_account_number=None, payout_account_name=None):
	"""Update user's payout information for receiving referral commissions."""
	user = frappe.session.user

	if user == "Guest":
		frappe.throw(_("Please login to update payout information"))

	# Validate payout method
	valid_methods = ["", "GoPay", "Dana", "ShopeePay", "OVO", "Bank Transfer"]
	if payout_method and payout_method not in valid_methods:
		frappe.throw(_("Invalid payout method"))

	# Validate bank if bank transfer selected
	valid_banks = ["", "BCA", "Mandiri", "BRI", "BNI", "Aladin"]
	if payout_method == "Bank Transfer":
		if payout_bank and payout_bank not in valid_banks:
			frappe.throw(_("Invalid bank selection"))

	# Update user record
	user_doc = frappe.get_doc("User", user)
	user_doc.payout_method = payout_method or ""
	user_doc.payout_phone = payout_phone or ""
	user_doc.payout_bank = payout_bank or ""
	user_doc.payout_account_number = payout_account_number or ""
	user_doc.payout_account_name = payout_account_name or ""
	user_doc.save(ignore_permissions=True)

	return {
		"success": True,
		"message": _("Payout information updated successfully")
	}


# =============================================================================
# COMPREHENSIVE API SUITE - Professional LMS Integration APIs
# =============================================================================

# -----------------------------------------------------------------------------
# COURSE MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def api_get_courses(published=None, paid_course=None, category=None, featured=None,
                    upcoming=None, start=0, limit=20):
	"""
	Get list of courses with optional filters.

	Parameters:
	- published (int): 0 or 1 to filter by published status
	- paid_course (int): 0 or 1 to filter by paid status
	- category (str): Category name to filter
	- featured (int): 0 or 1 to filter featured courses
	- upcoming (int): 0 or 1 to filter upcoming courses
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	base_filters = {}

	if published is not None:
		base_filters["published"] = cint(published)
	if paid_course is not None:
		base_filters["paid_course"] = cint(paid_course)
	if category:
		base_filters["category"] = category
	if featured is not None:
		base_filters["featured"] = cint(featured)
	if upcoming is not None:
		base_filters["upcoming"] = cint(upcoming)

	courses = frappe.get_all(
		"LMS Course",
		filters=base_filters,
		fields=[
			"name", "title", "short_introduction", "image", "published",
			"paid_course", "course_price", "currency", "category",
			"rating", "enrollments", "lessons", "featured", "upcoming"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="creation desc"
	)

	for course in courses:
		course["instructors"] = frappe.get_all(
			"Course Instructor",
			filters={"parent": course.name},
			fields=["instructor"],
			pluck="instructor"
		)

	total = frappe.db.count("LMS Course", filters=base_filters)
	return {"data": courses, "total": total}


@frappe.whitelist(allow_guest=True)
def api_get_course(name):
	"""Get single course detail by name/ID."""
	if not frappe.db.exists("LMS Course", name):
		frappe.throw(_("Course not found"), frappe.DoesNotExistError)

	course = frappe.get_doc("LMS Course", name)

	# Get chapters with lessons
	chapters = []
	for ch_ref in course.chapters:
		chapter = frappe.get_doc("Course Chapter", ch_ref.chapter)
		lessons = frappe.get_all(
			"Course Lesson",
			filters={"chapter": chapter.name},
			fields=["name", "title", "include_in_preview", "youtube", "quiz_id"],
			order_by="creation asc"
		)
		chapters.append({
			"name": chapter.name,
			"title": chapter.title,
			"lessons": lessons
		})

	instructors = [{"email": i.instructor, "name": frappe.db.get_value("User", i.instructor, "full_name")}
				   for i in course.instructors]

	return {
		"name": course.name,
		"title": course.title,
		"description": course.description,
		"short_introduction": course.short_introduction,
		"image": course.image,
		"video_link": course.video_link,
		"published": course.published,
		"paid_course": course.paid_course,
		"course_price": course.course_price,
		"currency": course.currency,
		"category": course.category,
		"rating": course.rating,
		"enrollments": course.enrollments,
		"lessons": course.lessons,
		"instructors": instructors,
		"chapters": chapters,
		"enable_certification": course.enable_certification,
		"creation": course.creation,
		"modified": course.modified
	}


@frappe.whitelist()
def api_update_course(name, title=None, description=None, short_introduction=None,
                      image=None, video_link=None, published=None, paid_course=None,
                      course_price=None, currency=None, category=None, featured=None,
                      upcoming=None, enable_certification=None, tags=None):
	"""
	Update course by ID/name. Admin/Moderator/Course Creator only.

	Parameters:
	- name (str): Course ID/name - REQUIRED for identifying which course to update
	- title (str): Course title
	- description (str): Full course description (HTML)
	- short_introduction (str): Short course description
	- image (str): Course image URL
	- video_link (str): Intro video URL
	- published (int): 0 or 1
	- paid_course (int): 0 or 1
	- course_price (float): Course price
	- currency (str): Currency code (IDR, USD, etc)
	- category (str): Category name
	- featured (int): 0 or 1
	- upcoming (int): 0 or 1
	- enable_certification (int): 0 or 1
	- tags (str): Comma-separated tags
	"""
	frappe.only_for(["System Manager", "Moderator", "Course Creator"])

	if not frappe.db.exists("LMS Course", name):
		frappe.throw(_("Course not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("LMS Course", name)

	# Update fields if provided
	if title is not None:
		doc.title = title
	if description is not None:
		doc.description = description
	if short_introduction is not None:
		doc.short_introduction = short_introduction
	if image is not None:
		doc.image = image
	if video_link is not None:
		doc.video_link = video_link
	if published is not None:
		doc.published = cint(published)
	if paid_course is not None:
		doc.paid_course = cint(paid_course)
	if course_price is not None:
		doc.course_price = flt(course_price)
	if currency is not None:
		doc.currency = currency
	if category is not None:
		doc.category = category
	if featured is not None:
		doc.featured = cint(featured)
	if upcoming is not None:
		doc.upcoming = cint(upcoming)
	if enable_certification is not None:
		doc.enable_certification = cint(enable_certification)
	if tags is not None:
		doc.tags = tags

	doc.save(ignore_permissions=True)
	return {"success": True, "name": doc.name, "message": "Course updated successfully"}


# -----------------------------------------------------------------------------
# BATCH MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def api_get_batches(published=None, paid_batch=None, category=None, medium=None,
                    start_date_from=None, start_date_to=None, start=0, limit=20):
	"""
	Get list of batches with optional filters.

	Parameters:
	- published (int): 0 or 1 to filter by published status
	- paid_batch (int): 0 or 1 to filter by paid status
	- category (str): Category name to filter
	- medium (str): Medium (Online/Offline)
	- start_date_from (str): Filter batches starting from this date (YYYY-MM-DD)
	- start_date_to (str): Filter batches starting until this date (YYYY-MM-DD)
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	base_filters = {}

	if published is not None:
		base_filters["published"] = cint(published)
	if paid_batch is not None:
		base_filters["paid_batch"] = cint(paid_batch)
	if category:
		base_filters["category"] = category
	if medium:
		base_filters["medium"] = medium
	if start_date_from:
		base_filters["start_date"] = [">=", start_date_from]
	if start_date_to:
		if "start_date" in base_filters:
			# Already has from filter, need to use between
			base_filters["start_date"] = ["between", [start_date_from, start_date_to]]
		else:
			base_filters["start_date"] = ["<=", start_date_to]

	batches = frappe.get_all(
		"LMS Batch",
		filters=base_filters,
		fields=[
			"name", "title", "description", "meta_image", "published",
			"paid_batch", "amount", "currency", "start_date", "end_date",
			"start_time", "end_time", "timezone", "seat_count", "category",
			"medium", "certification"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="start_date desc"
	)

	for batch in batches:
		batch["enrolled_count"] = frappe.db.count("LMS Batch Enrollment", {"batch": batch.name})
		batch["courses"] = frappe.get_all(
			"Batch Course",
			filters={"parent": batch.name},
			fields=["course"],
			pluck="course"
		)

	total = frappe.db.count("LMS Batch", filters=base_filters)
	return {"data": batches, "total": total}


@frappe.whitelist(allow_guest=True)
def api_get_batch(name):
	"""Get single batch detail by name/ID."""
	if not frappe.db.exists("LMS Batch", name):
		frappe.throw(_("Batch not found"), frappe.DoesNotExistError)

	batch = frappe.get_doc("LMS Batch", name)

	courses = []
	for bc in batch.courses:
		course_title = frappe.db.get_value("LMS Course", bc.course, "title")
		courses.append({"name": bc.course, "title": course_title})

	instructors = [{"email": i.instructor, "name": frappe.db.get_value("User", i.instructor, "full_name")}
				   for i in batch.instructors]

	enrolled_count = frappe.db.count("LMS Batch Enrollment", {"batch": batch.name})

	return {
		"name": batch.name,
		"title": batch.title,
		"description": batch.description,
		"batch_details": batch.batch_details,
		"meta_image": batch.meta_image,
		"published": batch.published,
		"paid_batch": batch.paid_batch,
		"amount": batch.amount,
		"currency": batch.currency,
		"start_date": str(batch.start_date) if batch.start_date else None,
		"end_date": str(batch.end_date) if batch.end_date else None,
		"start_time": str(batch.start_time) if batch.start_time else None,
		"end_time": str(batch.end_time) if batch.end_time else None,
		"timezone": batch.timezone,
		"seat_count": batch.seat_count,
		"enrolled_count": enrolled_count,
		"seats_available": batch.seat_count - enrolled_count if batch.seat_count else None,
		"category": batch.category,
		"medium": batch.medium,
		"certification": batch.certification,
		"courses": courses,
		"instructors": instructors,
		"creation": batch.creation,
		"modified": batch.modified
	}


@frappe.whitelist()
def api_update_batch(name, title=None, description=None, batch_details=None,
                    meta_image=None, published=None, paid_batch=None, amount=None,
                    currency=None, start_date=None, end_date=None, start_time=None,
                    end_time=None, timezone=None, seat_count=None, category=None,
                    medium=None, certification=None):
	"""
	Update batch by ID/name. Admin/Moderator only.

	Parameters:
	- name (str): Batch ID/name - REQUIRED for identifying which batch to update
	- title (str): Batch title
	- description (str): Short description
	- batch_details (str): Full batch details (HTML)
	- meta_image (str): Batch image URL
	- published (int): 0 or 1
	- paid_batch (int): 0 or 1
	- amount (float): Batch price
	- currency (str): Currency code
	- start_date (str): Start date (YYYY-MM-DD)
	- end_date (str): End date (YYYY-MM-DD)
	- start_time (str): Start time (HH:MM:SS)
	- end_time (str): End time (HH:MM:SS)
	- timezone (str): Timezone
	- seat_count (int): Maximum seats
	- category (str): Category name
	- medium (str): Online/Offline
	- certification (int): 0 or 1
	"""
	frappe.only_for(["System Manager", "Moderator"])

	if not frappe.db.exists("LMS Batch", name):
		frappe.throw(_("Batch not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("LMS Batch", name)

	# Update fields if provided
	if title is not None:
		doc.title = title
	if description is not None:
		doc.description = description
	if batch_details is not None:
		doc.batch_details = batch_details
	if meta_image is not None:
		doc.meta_image = meta_image
	if published is not None:
		doc.published = cint(published)
	if paid_batch is not None:
		doc.paid_batch = cint(paid_batch)
	if amount is not None:
		doc.amount = flt(amount)
	if currency is not None:
		doc.currency = currency
	if start_date is not None:
		doc.start_date = start_date
	if end_date is not None:
		doc.end_date = end_date
	if start_time is not None:
		doc.start_time = start_time
	if end_time is not None:
		doc.end_time = end_time
	if timezone is not None:
		doc.timezone = timezone
	if seat_count is not None:
		doc.seat_count = cint(seat_count)
	if category is not None:
		doc.category = category
	if medium is not None:
		doc.medium = medium
	if certification is not None:
		doc.certification = cint(certification)

	doc.save(ignore_permissions=True)
	return {"success": True, "name": doc.name, "message": "Batch updated successfully"}


# -----------------------------------------------------------------------------
# ENROLLMENT MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_enrollments(course=None, member=None, progress_min=None, progress_max=None,
                        start=0, limit=50):
	"""
	Get list of course enrollments. Admin can see all, users see their own.

	Parameters:
	- course (str): Filter by course ID/name
	- member (str): Filter by member email (Admin only)
	- progress_min (int): Filter enrollments with progress >= this value
	- progress_max (int): Filter enrollments with progress <= this value
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	base_filters = {}

	if course:
		base_filters["course"] = course
	if progress_min is not None:
		base_filters["progress"] = [">=", cint(progress_min)]
	if progress_max is not None:
		if "progress" in base_filters:
			base_filters["progress"] = ["between", [cint(progress_min), cint(progress_max)]]
		else:
			base_filters["progress"] = ["<=", cint(progress_max)]

	# Non-admin can only see their own enrollments
	if "System Manager" not in roles and "Moderator" not in roles:
		base_filters["member"] = user
	elif member:
		base_filters["member"] = member

	enrollments = frappe.get_all(
		"LMS Enrollment",
		filters=base_filters,
		fields=[
			"name", "course", "member", "member_name", "progress",
			"current_lesson", "payment", "purchased_certificate", "creation"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="creation desc"
	)

	for e in enrollments:
		e["course_title"] = frappe.db.get_value("LMS Course", e.course, "title")

	total = frappe.db.count("LMS Enrollment", filters=base_filters)
	return {"data": enrollments, "total": total}


@frappe.whitelist()
def api_create_enrollment(course, member, payment=None):
	"""Create course enrollment. Admin only."""
	frappe.only_for(["System Manager", "Moderator"])

	if not frappe.db.exists("LMS Course", course):
		frappe.throw(_("Course not found"))
	if not frappe.db.exists("User", member):
		frappe.throw(_("User not found"))

	# Check if already enrolled
	if frappe.db.exists("LMS Enrollment", {"course": course, "member": member}):
		frappe.throw(_("User is already enrolled in this course"))

	doc = frappe.get_doc({
		"doctype": "LMS Enrollment",
		"course": course,
		"member": member,
		"payment": payment
	})
	doc.flags.from_batch_enrollment = True  # Skip payment validation
	doc.insert(ignore_permissions=True)

	return {"success": True, "name": doc.name}


@frappe.whitelist()
def api_update_enrollment(name, progress=None, current_lesson=None, purchased_certificate=None):
	"""
	Update enrollment by ID/name. Admin/Moderator only.

	Parameters:
	- name (str): Enrollment ID - REQUIRED for identifying which enrollment to update
	- progress (int): Progress percentage (0-100)
	- current_lesson (str): Current lesson ID/name
	- purchased_certificate (int): 0 or 1
	"""
	frappe.only_for(["System Manager", "Moderator"])

	if not frappe.db.exists("LMS Enrollment", name):
		frappe.throw(_("Enrollment not found"))

	doc = frappe.get_doc("LMS Enrollment", name)

	if progress is not None:
		doc.progress = cint(progress)
	if current_lesson is not None:
		doc.current_lesson = current_lesson
	if purchased_certificate is not None:
		doc.purchased_certificate = cint(purchased_certificate)

	doc.save(ignore_permissions=True)
	return {"success": True, "name": doc.name, "message": "Enrollment updated successfully"}


# -----------------------------------------------------------------------------
# BATCH ENROLLMENT MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_batch_enrollments(batch=None, member=None, start=0, limit=50):
	"""
	Get list of batch enrollments. Admin can see all, users see their own.

	Parameters:
	- batch (str): Filter by batch ID/name
	- member (str): Filter by member email (Admin only)
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	base_filters = {}

	if batch:
		base_filters["batch"] = batch

	if "System Manager" not in roles and "Moderator" not in roles:
		base_filters["member"] = user
	elif member:
		base_filters["member"] = member

	enrollments = frappe.get_all(
		"LMS Batch Enrollment",
		filters=base_filters,
		fields=[
			"name", "batch", "member", "member_name", "payment",
			"source", "confirmation_email_sent", "creation"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="creation desc"
	)

	for e in enrollments:
		e["batch_title"] = frappe.db.get_value("LMS Batch", e.batch, "title")

	total = frappe.db.count("LMS Batch Enrollment", filters=base_filters)
	return {"data": enrollments, "total": total}


@frappe.whitelist()
def api_create_batch_enrollment(batch, member, payment=None):
	"""Create batch enrollment. Admin only."""
	frappe.only_for(["System Manager", "Moderator"])

	if not frappe.db.exists("LMS Batch", batch):
		frappe.throw(_("Batch not found"))
	if not frappe.db.exists("User", member):
		frappe.throw(_("User not found"))

	if frappe.db.exists("LMS Batch Enrollment", {"batch": batch, "member": member}):
		frappe.throw(_("User is already enrolled in this batch"))

	doc = frappe.get_doc({
		"doctype": "LMS Batch Enrollment",
		"batch": batch,
		"member": member,
		"payment": payment
	})
	doc.insert(ignore_permissions=True)

	return {"success": True, "name": doc.name}


# -----------------------------------------------------------------------------
# PAYMENT MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_payments(member=None, status=None, payment_for_document=None,
                    date_from=None, date_to=None, start=0, limit=50):
	"""
	Get list of payments. Admin only.

	Parameters:
	- member (str): Filter by member email
	- status (str): Filter by status (Pending/Paid/Expired/Cancelled)
	- payment_for_document (str): Filter by batch/course name
	- date_from (str): Filter payments from this date (YYYY-MM-DD)
	- date_to (str): Filter payments until this date (YYYY-MM-DD)
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	frappe.only_for("System Manager")

	base_filters = {}

	if member:
		base_filters["member"] = member
	if status:
		base_filters["status"] = status
	if payment_for_document:
		base_filters["payment_for_document"] = payment_for_document
	if date_from:
		base_filters["creation"] = [">=", date_from]
	if date_to:
		if "creation" in base_filters:
			base_filters["creation"] = ["between", [date_from, date_to]]
		else:
			base_filters["creation"] = ["<=", date_to]

	payments = frappe.get_all(
		"LMS Payment",
		filters=base_filters,
		fields=[
			"name", "member", "billing_name", "amount", "currency", "status",
			"payment_for_document_type", "payment_for_document", "payment_received",
			"coupon_code", "discount_amount", "original_amount",
			"midtrans_order_id", "midtrans_payment_type", "creation"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="creation desc"
	)

	total = frappe.db.count("LMS Payment", filters=base_filters)
	return {"data": payments, "total": total}


@frappe.whitelist()
def api_get_payment(name):
	"""Get single payment detail. Admin only."""
	frappe.only_for("System Manager")

	if not frappe.db.exists("LMS Payment", name):
		frappe.throw(_("Payment not found"))

	payment = frappe.get_doc("LMS Payment", name)

	return {
		"name": payment.name,
		"member": payment.member,
		"billing_name": payment.billing_name,
		"amount": payment.amount,
		"original_amount": payment.original_amount,
		"discount_amount": payment.discount_amount,
		"currency": payment.currency,
		"status": payment.status,
		"payment_received": payment.payment_received,
		"payment_for_document_type": payment.payment_for_document_type,
		"payment_for_document": payment.payment_for_document,
		"coupon": payment.coupon,
		"coupon_code": payment.coupon_code,
		"address": payment.address,
		"midtrans_order_id": payment.midtrans_order_id,
		"midtrans_transaction_id": payment.midtrans_transaction_id,
		"midtrans_payment_type": payment.midtrans_payment_type,
		"midtrans_bank": payment.midtrans_bank,
		"midtrans_issuer": payment.midtrans_issuer,
		"midtrans_va_number": payment.midtrans_va_number,
		"creation": payment.creation,
		"modified": payment.modified
	}


@frappe.whitelist()
def api_update_payment(name, status=None, payment_received=None):
	"""
	Update payment by ID/name. Admin only. Useful for marking manual payments.

	Parameters:
	- name (str): Payment ID - REQUIRED for identifying which payment to update
	- status (str): Payment status (Pending/Paid/Expired/Cancelled)
	- payment_received (int): 0 or 1 to mark if payment has been received
	"""
	frappe.only_for("System Manager")

	if not frappe.db.exists("LMS Payment", name):
		frappe.throw(_("Payment not found"))

	doc = frappe.get_doc("LMS Payment", name)

	if status is not None:
		doc.status = status
	if payment_received is not None:
		doc.payment_received = cint(payment_received)

	doc.save(ignore_permissions=True)
	return {"success": True, "name": doc.name, "message": "Payment updated successfully"}


# -----------------------------------------------------------------------------
# CERTIFICATE MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_certificates(member=None, course=None, batch_name=None, start=0, limit=50):
	"""
	Get list of certificates. Admin can see all, users see their own.

	Parameters:
	- member (str): Filter by member email (Admin only)
	- course (str): Filter by course ID/name
	- batch_name (str): Filter by batch ID/name
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	base_filters = {}

	if course:
		base_filters["course"] = course
	if batch_name:
		base_filters["batch_name"] = batch_name

	if "System Manager" not in roles and "Moderator" not in roles:
		base_filters["member"] = user
	elif member:
		base_filters["member"] = member

	certificates = frappe.get_all(
		"LMS Certificate",
		filters=base_filters,
		fields=[
			"name", "member", "member_name", "course", "course_title",
			"batch_name", "batch_title", "issue_date", "expiry_date",
			"template", "published", "evaluator_name", "creation"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="issue_date desc"
	)

	total = frappe.db.count("LMS Certificate", filters=base_filters)
	return {"data": certificates, "total": total}


@frappe.whitelist(allow_guest=True)
def api_verify_certificate(certificate_id):
	"""Public API to verify certificate authenticity."""
	if not frappe.db.exists("LMS Certificate", certificate_id):
		return {"valid": False, "message": "Certificate not found"}

	cert = frappe.get_doc("LMS Certificate", certificate_id)

	return {
		"valid": True,
		"certificate_id": cert.name,
		"member_name": cert.member_name,
		"course_title": cert.course_title or cert.batch_title,
		"issue_date": str(cert.issue_date) if cert.issue_date else None,
		"expiry_date": str(cert.expiry_date) if cert.expiry_date else None,
		"published": cert.published
	}


@frappe.whitelist()
def api_issue_certificate(member, course=None, batch_name=None, template=None, issue_date=None):
	"""Issue a new certificate. Admin only."""
	frappe.only_for(["System Manager", "Moderator"])

	if not course and not batch_name:
		frappe.throw(_("Either course or batch must be specified"))

	if not frappe.db.exists("User", member):
		frappe.throw(_("User not found"))

	doc = frappe.get_doc({
		"doctype": "LMS Certificate",
		"member": member,
		"course": course,
		"batch_name": batch_name,
		"template": template or "LMS Certificate",
		"issue_date": issue_date or frappe.utils.today(),
		"published": 1
	})
	doc.insert(ignore_permissions=True)

	return {"success": True, "name": doc.name}


# -----------------------------------------------------------------------------
# QUIZ MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def api_get_quizzes(course=None, lesson=None, start=0, limit=20):
	"""
	Get list of quizzes.

	Parameters:
	- course (str): Filter by course ID/name
	- lesson (str): Filter by lesson ID/name
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	base_filters = {}

	if course:
		base_filters["course"] = course
	if lesson:
		base_filters["lesson"] = lesson

	quizzes = frappe.get_all(
		"LMS Quiz",
		filters=base_filters,
		fields=[
			"name", "title", "lesson", "course", "max_attempts",
			"passing_percentage", "total_marks", "duration",
			"shuffle_questions", "show_answers"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="creation desc"
	)

	for q in quizzes:
		q["question_count"] = frappe.db.count("LMS Quiz Question", {"parent": q.name})

	total = frappe.db.count("LMS Quiz", filters=base_filters)
	return {"data": quizzes, "total": total}


@frappe.whitelist(allow_guest=True)
def api_get_quiz(name):
	"""Get single quiz detail."""
	if not frappe.db.exists("LMS Quiz", name):
		frappe.throw(_("Quiz not found"))

	quiz = frappe.get_doc("LMS Quiz", name)

	questions = []
	for q in quiz.questions:
		question_doc = frappe.get_doc("LMS Question", q.question)
		options = [{"option": o.option, "is_correct": o.is_correct} for o in question_doc.options]
		questions.append({
			"name": question_doc.name,
			"question": question_doc.question,
			"type": question_doc.type,
			"marks": q.marks,
			"options": options
		})

	return {
		"name": quiz.name,
		"title": quiz.title,
		"max_attempts": quiz.max_attempts,
		"passing_percentage": quiz.passing_percentage,
		"total_marks": quiz.total_marks,
		"duration": quiz.duration,
		"shuffle_questions": quiz.shuffle_questions,
		"show_answers": quiz.show_answers,
		"questions": questions
	}


# -----------------------------------------------------------------------------
# LIVE CLASS MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_live_classes(batch_name=None, host=None, date_from=None, date_to=None,
                         start=0, limit=20):
	"""
	Get list of live classes.

	Parameters:
	- batch_name (str): Filter by batch ID/name
	- host (str): Filter by host email
	- date_from (str): Filter classes from this date (YYYY-MM-DD)
	- date_to (str): Filter classes until this date (YYYY-MM-DD)
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	base_filters = {}

	if batch_name:
		base_filters["batch_name"] = batch_name
	if host:
		base_filters["host"] = host
	if date_from:
		base_filters["date"] = [">=", date_from]
	if date_to:
		if "date" in base_filters:
			base_filters["date"] = ["between", [date_from, date_to]]
		else:
			base_filters["date"] = ["<=", date_to]

	classes = frappe.get_all(
		"LMS Live Class",
		filters=base_filters,
		fields=[
			"name", "title", "host", "batch_name", "date", "time",
			"duration", "timezone", "meeting_platform", "join_url",
			"attendees", "creation"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="date desc, time desc"
	)

	for c in classes:
		c["host_name"] = frappe.db.get_value("User", c.host, "full_name")
		c["batch_title"] = frappe.db.get_value("LMS Batch", c.batch_name, "title") if c.batch_name else None

	total = frappe.db.count("LMS Live Class", filters=base_filters)
	return {"data": classes, "total": total}


@frappe.whitelist()
def api_create_live_class(title, host, date, time, duration, timezone,
                          meeting_platform="Google Meet", batch_name=None,
                          google_meet_link=None, description=None):
	"""Create a new live class. Admin only."""
	frappe.only_for(["System Manager", "Moderator"])

	doc = frappe.get_doc({
		"doctype": "LMS Live Class",
		"title": title,
		"host": host,
		"date": date,
		"time": time,
		"duration": cint(duration),
		"timezone": timezone,
		"meeting_platform": meeting_platform,
		"batch_name": batch_name,
		"google_meet_link": google_meet_link,
		"description": description
	})
	doc.insert(ignore_permissions=True)

	return {"success": True, "name": doc.name, "join_url": doc.join_url or doc.google_meet_link}


@frappe.whitelist()
def api_update_live_class(name, title=None, date=None, time=None, duration=None,
                          timezone=None, description=None, meeting_platform=None,
                          google_meet_link=None):
	"""
	Update live class by ID/name. Admin/Moderator only.

	Parameters:
	- name (str): Live Class ID - REQUIRED for identifying which class to update
	- title (str): Class title
	- date (str): Date (YYYY-MM-DD)
	- time (str): Time (HH:MM:SS)
	- duration (int): Duration in minutes
	- timezone (str): Timezone
	- description (str): Class description
	- meeting_platform (str): Google Meet/Zoom/etc
	- google_meet_link (str): Google Meet link
	"""
	frappe.only_for(["System Manager", "Moderator"])

	if not frappe.db.exists("LMS Live Class", name):
		frappe.throw(_("Live class not found"))

	doc = frappe.get_doc("LMS Live Class", name)

	if title is not None:
		doc.title = title
	if date is not None:
		doc.date = date
	if time is not None:
		doc.time = time
	if duration is not None:
		doc.duration = cint(duration)
	if timezone is not None:
		doc.timezone = timezone
	if description is not None:
		doc.description = description
	if meeting_platform is not None:
		doc.meeting_platform = meeting_platform
	if google_meet_link is not None:
		doc.google_meet_link = google_meet_link

	doc.save(ignore_permissions=True)
	return {"success": True, "name": doc.name, "message": "Live class updated successfully"}


# -----------------------------------------------------------------------------
# BULK OPERATIONS APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_bulk_update_commissions(commission_ids, payout_status=None, payout_date=None, payout_notes=None):
	"""
	Bulk update multiple commission records. Admin only. Great for n8n.

	Parameters:
	- commission_ids (array/str): Array of commission IDs to update, or JSON string
	- payout_status (str): New payout status (Pending/Processing/Paid)
	- payout_date (str): Payout date (YYYY-MM-DD)
	- payout_notes (str): Notes about the payout
	"""
	frappe.only_for("System Manager")

	if isinstance(commission_ids, str):
		commission_ids = json.loads(commission_ids)

	updated = []
	errors = []

	for cid in commission_ids:
		try:
			if not frappe.db.exists("LMS Referral Commission", cid):
				errors.append({"id": cid, "error": "Not found"})
				continue

			doc = frappe.get_doc("LMS Referral Commission", cid)

			if payout_status is not None:
				doc.payout_status = payout_status
			if payout_date is not None:
				doc.payout_date = payout_date
			if payout_notes is not None and hasattr(doc, 'payout_notes'):
				doc.payout_notes = payout_notes

			doc.save(ignore_permissions=True)
			updated.append(cid)
		except Exception as e:
			errors.append({"id": cid, "error": str(e)})

	frappe.db.commit()
	return {"updated": updated, "errors": errors, "total_updated": len(updated)}


@frappe.whitelist()
def api_get_user_profile(user_email=None):
	"""Get user profile with payout info. Admin or self."""
	if not user_email:
		user_email = frappe.session.user

	if user_email != frappe.session.user:
		frappe.only_for("System Manager")

	if not frappe.db.exists("User", user_email):
		frappe.throw(_("User not found"))

	user = frappe.get_doc("User", user_email)

	return {
		"email": user.email,
		"full_name": user.full_name,
		"username": user.username,
		"user_image": user.user_image,
		"enabled": user.enabled,
		"referral_code": user.get("referral_code"),
		"referred_by": user.get("referred_by"),
		"payout_method": user.get("payout_method"),
		"payout_phone": user.get("payout_phone"),
		"payout_bank": user.get("payout_bank"),
		"payout_account_number": user.get("payout_account_number"),
		"payout_account_name": user.get("payout_account_name"),
		"creation": user.creation
	}


# -----------------------------------------------------------------------------
# COMMISSION MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_commissions(referrer=None, payout_status=None, date_from=None, date_to=None,
                        start=0, limit=50):
	"""
	Get list of referral commissions. Admin only.

	Parameters:
	- referrer (str): Filter by referrer email
	- payout_status (str): Filter by status (Pending/Processing/Paid)
	- date_from (str): Filter from this date (YYYY-MM-DD)
	- date_to (str): Filter until this date (YYYY-MM-DD)
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	frappe.only_for("System Manager")

	base_filters = {}

	if referrer:
		base_filters["referrer"] = referrer
	if payout_status:
		base_filters["payout_status"] = payout_status
	if date_from:
		base_filters["creation"] = [">=", date_from]
	if date_to:
		if "creation" in base_filters:
			base_filters["creation"] = ["between", [date_from, date_to]]
		else:
			base_filters["creation"] = ["<=", date_to]

	commissions = frappe.get_all(
		"LMS Referral Commission",
		filters=base_filters,
		fields=[
			"name", "referrer", "referred_student", "payment", "purchase_type",
			"commission_amount", "commission_rate", "payout_status", "payout_date",
			"creation"
		],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="creation desc"
	)

	for c in commissions:
		c["referrer_name"] = frappe.db.get_value("User", c.referrer, "full_name")
		c["student_name"] = frappe.db.get_value("User", c.referred_student, "full_name")

	total = frappe.db.count("LMS Referral Commission", filters=base_filters)
	return {"data": commissions, "total": total}


@frappe.whitelist()
def api_get_commission(name):
	"""
	Get single commission detail by ID. Admin only.

	Parameters:
	- name (str): Commission ID
	"""
	frappe.only_for("System Manager")

	if not frappe.db.exists("LMS Referral Commission", name):
		frappe.throw(_("Commission not found"))

	doc = frappe.get_doc("LMS Referral Commission", name)

	return {
		"name": doc.name,
		"referrer": doc.referrer,
		"referrer_name": frappe.db.get_value("User", doc.referrer, "full_name"),
		"referred_student": doc.referred_student,
		"student_name": frappe.db.get_value("User", doc.referred_student, "full_name"),
		"payment": doc.payment,
		"purchase_type": doc.purchase_type,
		"commission_amount": doc.commission_amount,
		"commission_rate": doc.commission_rate,
		"payout_status": doc.payout_status,
		"payout_date": str(doc.payout_date) if doc.payout_date else None,
		"creation": doc.creation,
		"modified": doc.modified
	}


@frappe.whitelist()
def api_update_commission(name, payout_status=None, payout_date=None):
	"""
	Update single commission by ID. Admin only.

	Parameters:
	- name (str): Commission ID - REQUIRED
	- payout_status (str): Payout status (Pending/Processing/Paid)
	- payout_date (str): Payout date (YYYY-MM-DD)
	"""
	frappe.only_for("System Manager")

	if not frappe.db.exists("LMS Referral Commission", name):
		frappe.throw(_("Commission not found"))

	doc = frappe.get_doc("LMS Referral Commission", name)

	if payout_status is not None:
		doc.payout_status = payout_status
	if payout_date is not None:
		doc.payout_date = payout_date

	doc.save(ignore_permissions=True)
	return {"success": True, "name": doc.name, "message": "Commission updated successfully"}


# -----------------------------------------------------------------------------
# CATEGORY MANAGEMENT APIs
# -----------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def api_get_categories(start=0, limit=100):
	"""
	Get list of all categories.

	Parameters:
	- start (int): Pagination offset
	- limit (int): Number of records to return
	"""
	categories = frappe.get_all(
		"LMS Category",
		fields=["name", "category_name", "image"],
		start=cint(start),
		limit_page_length=cint(limit),
		order_by="category_name asc"
	)

	for cat in categories:
		cat["course_count"] = frappe.db.count("LMS Course", {"category": cat.name, "published": 1})
		cat["batch_count"] = frappe.db.count("LMS Batch", {"category": cat.name, "published": 1})

	total = frappe.db.count("LMS Category")
	return {"data": categories, "total": total}


@frappe.whitelist()
def api_create_category(category_name, image=None):
	"""
	Create a new category. Admin/Moderator only.

	Parameters:
	- category_name (str): Category name - REQUIRED
	- image (str): Category image URL
	"""
	frappe.only_for(["System Manager", "Moderator"])

	if frappe.db.exists("LMS Category", {"category_name": category_name}):
		frappe.throw(_("Category already exists"))

	doc = frappe.get_doc({
		"doctype": "LMS Category",
		"category_name": category_name,
		"image": image
	})
	doc.insert(ignore_permissions=True)

	return {"success": True, "name": doc.name, "message": "Category created successfully"}


# -----------------------------------------------------------------------------
# DASHBOARD & STATISTICS APIs
# -----------------------------------------------------------------------------

@frappe.whitelist()
def api_get_dashboard_stats():
	"""
	Get dashboard statistics. Admin/Moderator only.
	Returns counts for courses, batches, enrollments, revenue, etc.
	"""
	frappe.only_for(["System Manager", "Moderator"])

	stats = {
		"courses": {
			"total": frappe.db.count("LMS Course"),
			"published": frappe.db.count("LMS Course", {"published": 1}),
			"paid": frappe.db.count("LMS Course", {"paid_course": 1})
		},
		"batches": {
			"total": frappe.db.count("LMS Batch"),
			"published": frappe.db.count("LMS Batch", {"published": 1}),
			"paid": frappe.db.count("LMS Batch", {"paid_batch": 1})
		},
		"enrollments": {
			"course_enrollments": frappe.db.count("LMS Enrollment"),
			"batch_enrollments": frappe.db.count("LMS Batch Enrollment")
		},
		"users": {
			"total": frappe.db.count("User", {"enabled": 1}),
		},
		"payments": {
			"total": frappe.db.count("LMS Payment"),
			"paid": frappe.db.count("LMS Payment", {"status": "Paid"}),
			"pending": frappe.db.count("LMS Payment", {"status": "Pending"})
		},
		"certificates": {
			"total": frappe.db.count("LMS Certificate"),
			"published": frappe.db.count("LMS Certificate", {"published": 1})
		},
		"commissions": {
			"total": frappe.db.count("LMS Referral Commission"),
			"pending": frappe.db.count("LMS Referral Commission", {"payout_status": "Pending"}),
			"paid": frappe.db.count("LMS Referral Commission", {"payout_status": "Paid"})
		}
	}

	# Calculate total revenue
	total_revenue = frappe.db.sql("""
		SELECT SUM(amount) as total FROM `tabLMS Payment` WHERE status = 'Paid'
	""", as_dict=True)
	stats["revenue"] = {
		"total_paid": flt(total_revenue[0].total) if total_revenue else 0
	}

	# Calculate pending commission amount
	pending_commission = frappe.db.sql("""
		SELECT SUM(commission_amount) as total FROM `tabLMS Referral Commission`
		WHERE payout_status = 'Pending'
	""", as_dict=True)
	stats["commissions"]["pending_amount"] = flt(pending_commission[0].total) if pending_commission else 0

	return stats


@frappe.whitelist()
def api_get_revenue_stats(date_from=None, date_to=None, group_by="day"):
	"""
	Get revenue statistics with date range. Admin only.

	Parameters:
	- date_from (str): Start date (YYYY-MM-DD)
	- date_to (str): End date (YYYY-MM-DD)
	- group_by (str): Group by 'day', 'week', or 'month'
	"""
	frappe.only_for("System Manager")

	date_format = {
		"day": "%Y-%m-%d",
		"week": "%Y-%u",
		"month": "%Y-%m"
	}.get(group_by, "%Y-%m-%d")

	filters = ["status = 'Paid'"]
	if date_from:
		filters.append(f"creation >= '{date_from}'")
	if date_to:
		filters.append(f"creation <= '{date_to} 23:59:59'")

	where_clause = " AND ".join(filters)

	revenue_data = frappe.db.sql(f"""
		SELECT
			DATE_FORMAT(creation, '{date_format}') as period,
			COUNT(*) as transaction_count,
			SUM(amount) as total_amount,
			currency
		FROM `tabLMS Payment`
		WHERE {where_clause}
		GROUP BY period, currency
		ORDER BY period DESC
	""", as_dict=True)

	return {"data": revenue_data}
