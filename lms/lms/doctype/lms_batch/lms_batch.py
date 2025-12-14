# Copyright (c) 2022, Frappe and contributors
# For license information, please see license.txt

import base64
import json
from datetime import timedelta

import frappe
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, format_datetime, get_time, nowdate

from lms.lms.utils import (
	generate_slug,
	get_assignment_details,
	get_lesson_index,
	get_lesson_url,
	get_quiz_details,
	update_payment_record,
)


class LMSBatch(Document):
	def validate(self):
		self.validate_seats_left()
		self.validate_batch_end_date()
		self.validate_batch_time()
		self.validate_duplicate_courses()
		self.validate_payments_app()
		self.validate_amount_and_currency()
		self.validate_duplicate_assessments()
		self.validate_membership()
		self.validate_timetable()
		self.validate_evaluation_end_date()

	def autoname(self):
		if not self.name:
			self.name = generate_slug(self.title, "LMS Batch")

	def validate_batch_end_date(self):
		if self.end_date < self.start_date:
			frappe.throw(_("Batch end date cannot be before the batch start date"))

	def validate_batch_time(self):
		if self.start_time and self.end_time:
			if get_time(self.start_time) >= get_time(self.end_time):
				frappe.throw(_("Batch start time cannot be greater than or equal to end time."))

	def validate_duplicate_courses(self):
		courses = [row.course for row in self.courses]
		duplicates = {course for course in courses if courses.count(course) > 1}
		if len(duplicates):
			title = frappe.db.get_value("LMS Course", next(iter(duplicates)), "title")
			frappe.throw(_("Course {0} has already been added to this batch.").format(frappe.bold(title)))

	def validate_payments_app(self):
		if self.paid_batch:
			installed_apps = frappe.get_installed_apps()
			if "payments" not in installed_apps:
				documentation_link = "https://docs.frappe.io/learning/setting-up-payment-gateway"
				frappe.throw(
					_(
						"Please install the Payments App to create a paid batch. Refer to the documentation for more details. {0}"
					).format(documentation_link)
				)

	def validate_amount_and_currency(self):
		if self.paid_batch and (not self.amount or not self.currency):
			frappe.throw(_("Amount and currency are required for paid batches."))

	def validate_duplicate_assessments(self):
		assessments = [row.assessment_name for row in self.assessment]
		for assessment in self.assessment:
			if assessments.count(assessment.assessment_name) > 1:
				title = frappe.db.get_value(assessment.assessment_type, assessment.assessment_name, "title")
				frappe.throw(
					_("Assessment {0} has already been added to this batch.").format(frappe.bold(title))
				)

	def validate_evaluation_end_date(self):
		if self.evaluation_end_date and self.evaluation_end_date < self.end_date:
			frappe.throw(_("Evaluation end date cannot be less than the batch end date."))

	def validate_membership(self):
		members = frappe.get_all("LMS Batch Enrollment", {"batch": self.name}, pluck="member")
		for course in self.courses:
			for member in members:
				if not frappe.db.exists("LMS Enrollment", {"course": course.course, "member": member}):
					enrollment = frappe.new_doc("LMS Enrollment")
					enrollment.course = course.course
					enrollment.member = member
					enrollment.save()

	def validate_seats_left(self):
		if cint(self.seat_count) < 0:
			frappe.throw(_("Seat count cannot be negative."))

		students = frappe.db.count("LMS Batch Enrollment", {"batch": self.name})
		if cint(self.seat_count) and cint(self.seat_count) < students:
			frappe.throw(_("There are no seats available in this batch."))

	def validate_timetable(self):
		for schedule in self.timetable:
			if schedule.start_time and schedule.end_time:
				if get_time(schedule.start_time) > get_time(schedule.end_time) or get_time(
					schedule.start_time
				) == get_time(schedule.end_time):
					frappe.throw(
						_("Row #{0} Start time cannot be greater than or equal to end time.").format(
							schedule.idx
						)
					)

				if get_time(schedule.start_time) < get_time(self.start_time) or get_time(
					schedule.start_time
				) > get_time(self.end_time):
					frappe.throw(
						_("Row #{0} Start time cannot be outside the batch duration.").format(schedule.idx)
					)

				if get_time(schedule.end_time) < get_time(self.start_time) or get_time(
					schedule.end_time
				) > get_time(self.end_time):
					frappe.throw(
						_("Row #{0} End time cannot be outside the batch duration.").format(schedule.idx)
					)

			if schedule.date < self.start_date or schedule.date > self.end_date:
				frappe.throw(_("Row #{0} Date cannot be outside the batch duration.").format(schedule.idx))

	def on_payment_authorized(self, payment_status):
		if payment_status in ["Authorized", "Completed"]:
			update_payment_record("LMS Batch", self.name)


@frappe.whitelist()
def create_live_class(
	batch_name,
	zoom_account,
	title,
	duration,
	date,
	time,
	timezone,
	auto_recording,
	description=None,
):
	payload = {
		"topic": title,
		"start_time": format_datetime(f"{date} {time}", "yyyy-MM-ddTHH:mm:ssZ"),
		"duration": duration,
		"agenda": description,
		"private_meeting": True,
		"auto_recording": "none" if auto_recording == "No Recording" else auto_recording.lower(),
		"timezone": timezone,
	}
	headers = {
		"Authorization": "Bearer " + authenticate(zoom_account),
		"content-type": "application/json",
	}
	response = requests.post(
		"https://api.zoom.us/v2/users/me/meetings", headers=headers, data=json.dumps(payload)
	)

	if response.status_code == 201:
		data = json.loads(response.text)
		payload.update(
			{
				"doctype": "LMS Live Class",
				"start_url": data.get("start_url"),
				"join_url": data.get("join_url"),
				"meeting_id": data.get("id"),
				"uuid": data.get("uuid"),
				"title": title,
				"host": frappe.session.user,
				"date": date,
				"time": time,
				"batch_name": batch_name,
				"password": data.get("password"),
				"description": description,
				"auto_recording": auto_recording,
				"zoom_account": zoom_account,
			}
		)
		class_details = frappe.get_doc(payload)
		class_details.save()
		return class_details
	else:
		frappe.throw(_("Error creating live class. Please try again. {0}").format(response.text))


def authenticate(zoom_account):
	zoom = frappe.get_doc("LMS Zoom Settings", zoom_account)
	if not zoom.enabled:
		frappe.throw(_("Please enable the zoom account to use this feature."))

	authenticate_url = (
		f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={zoom.account_id}"
	)

	headers = {
		"Authorization": "Basic "
		+ base64.b64encode(
			bytes(
				zoom.client_id + ":" + zoom.get_password(fieldname="client_secret", raise_exception=False),
				encoding="utf8",
			)
		).decode()
	}
	response = requests.request("POST", authenticate_url, headers=headers)
	return response.json()["access_token"]


@frappe.whitelist()
def create_google_meet_live_class(
	batch_name,
	google_meet_account,
	title,
	duration,
	date,
	time,
	timezone,
	auto_recording=None,
	description=None,
):
	"""Create a live class using Google Meet via Google Calendar API"""
	from datetime import datetime, timedelta

	gmeet_settings = frappe.get_doc("LMS Google Meet Settings", google_meet_account)
	if not gmeet_settings.enabled:
		frappe.throw(_("Please enable the Google Meet account to use this feature."))

	if not gmeet_settings.google_calendar:
		frappe.throw(_("Please select a Google Calendar for this Google Meet account."))

	# Get the Google Calendar document
	google_calendar = frappe.get_doc("Google Calendar", gmeet_settings.google_calendar)

	# Check if calendar is authorized
	if not google_calendar.get("authorization_code") and not google_calendar.get("refresh_token"):
		frappe.throw(_("Google Calendar is not authorized. Please authorize Google Calendar first."))

	# Create event with Google Meet conferencing
	try:
		google_meet_link = create_google_calendar_event_with_meet(
			google_calendar=google_calendar,
			title=title,
			description=description or "",
			date=date,
			time=time,
			duration=int(duration),
			timezone=timezone,
		)
	except Exception as e:
		frappe.log_error(f"Google Meet creation error: {str(e)}")
		frappe.throw(_("Error creating Google Meet. Please try again. {0}").format(str(e)))

	# Create LMS Live Class document
	class_doc = frappe.get_doc({
		"doctype": "LMS Live Class",
		"title": title,
		"host": frappe.session.user,
		"meeting_platform": "Google Meet",
		"google_meet_account": google_meet_account,
		"google_meet_link": google_meet_link,
		"join_url": google_meet_link,
		"date": date,
		"time": time,
		"duration": duration,
		"timezone": timezone,
		"batch_name": batch_name,
		"description": description,
		"auto_recording": auto_recording or "No Recording",
	})
	class_doc.insert()

	return class_doc


def create_google_calendar_event_with_meet(google_calendar, title, description, date, time, duration, timezone):
	"""Create a Google Calendar event with Google Meet conferencing"""
	from datetime import datetime, timedelta
	import json

	# Get access token
	access_token = get_google_calendar_access_token(google_calendar)

	# Parse date and time
	start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
	end_datetime = start_datetime + timedelta(minutes=int(duration))

	# Format for Google Calendar API
	start_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
	end_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")

	# Create event payload with conferencing
	event_payload = {
		"summary": title,
		"description": description,
		"start": {
			"dateTime": start_iso,
			"timeZone": timezone or "UTC"
		},
		"end": {
			"dateTime": end_iso,
			"timeZone": timezone or "UTC"
		},
		"conferenceData": {
			"createRequest": {
				"requestId": frappe.generate_hash(length=16),
				"conferenceSolutionKey": {
					"type": "hangoutsMeet"
				}
			}
		}
	}

	# Make API request
	headers = {
		"Authorization": f"Bearer {access_token}",
		"Content-Type": "application/json"
	}

	calendar_id = google_calendar.google_calendar_id or "primary"
	url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?conferenceDataVersion=1"

	response = requests.post(url, headers=headers, data=json.dumps(event_payload))

	if response.status_code not in [200, 201]:
		frappe.throw(_("Failed to create Google Calendar event: {0}").format(response.text))

	data = response.json()

	# Extract Google Meet link
	conference_data = data.get("conferenceData", {})
	entry_points = conference_data.get("entryPoints", [])

	meet_link = None
	for entry_point in entry_points:
		if entry_point.get("entryPointType") == "video":
			meet_link = entry_point.get("uri")
			break

	if not meet_link:
		# Fallback to hangoutLink
		meet_link = data.get("hangoutLink")

	if not meet_link:
		frappe.throw(_("Failed to get Google Meet link from the created event."))

	return meet_link


def get_google_calendar_access_token(google_calendar):
	"""Get access token for Google Calendar API"""
	from frappe.integrations.doctype.google_settings.google_settings import get_auth_url

	# Check if we have a refresh token
	if not google_calendar.get("refresh_token"):
		frappe.throw(_("Google Calendar is not authorized. Please re-authorize."))

	# Get Google Settings
	google_settings = frappe.get_single("Google Settings")

	if not google_settings.client_id or not google_settings.get_password("client_secret"):
		frappe.throw(_("Please configure Google Settings with Client ID and Client Secret."))

	# Refresh the access token
	token_url = "https://oauth2.googleapis.com/token"

	payload = {
		"client_id": google_settings.client_id,
		"client_secret": google_settings.get_password("client_secret"),
		"refresh_token": google_calendar.get_password("refresh_token"),
		"grant_type": "refresh_token"
	}

	response = requests.post(token_url, data=payload)

	if response.status_code != 200:
		frappe.throw(_("Failed to refresh Google access token: {0}").format(response.text))

	data = response.json()
	return data.get("access_token")




@frappe.whitelist()
def get_batch_timetable(batch):
	timetable = frappe.get_all(
		"LMS Batch Timetable",
		filters={"parent": batch},
		fields=[
			"reference_doctype",
			"reference_docname",
			"date",
			"start_time",
			"end_time",
			"milestone",
			"name",
			"idx",
			"parent",
		],
		order_by="date",
	)

	show_live_class = frappe.db.get_value("LMS Batch", batch, "show_live_class")
	if show_live_class:
		live_classes = get_live_classes(batch)
		timetable.extend(live_classes)

	timetable = get_timetable_details(timetable)
	return timetable


def get_live_classes(batch):
	live_classes = frappe.get_all(
		"LMS Live Class",
		{"batch_name": batch},
		["name", "title", "date", "time as start_time", "duration", "join_url as url"],
		order_by="date",
	)
	for class_ in live_classes:
		class_.end_time = class_.start_time + timedelta(minutes=class_.duration)
		class_.reference_doctype = "LMS Live Class"
		class_.reference_docname = class_.name
		class_.icon = "icon-call"

	return live_classes


def get_timetable_details(timetable):
	for entry in timetable:
		entry.title = frappe.db.get_value(entry.reference_doctype, entry.reference_docname, "title")
		assessment = frappe._dict({"assessment_name": entry.reference_docname})

		if entry.reference_doctype == "Course Lesson":
			course = frappe.db.get_value(entry.reference_doctype, entry.reference_docname, "course")
			entry.url = get_lesson_url(course, get_lesson_index(entry.reference_docname))

			entry.completed = (
				True
				if frappe.db.exists(
					"LMS Course Progress",
					{
						"lesson": entry.reference_docname,
						"member": frappe.session.user,
						"status": "Complete",
					},
				)
				else False
			)

		elif entry.reference_doctype == "LMS Quiz":
			entry.url = "/quizzes"
			details = get_quiz_details(assessment, frappe.session.user)
			entry.update(details)

		elif entry.reference_doctype == "LMS Assignment":
			details = get_assignment_details(assessment, frappe.session.user)
			entry.update(details)

	timetable = sorted(timetable, key=lambda k: k["date"])
	return timetable


def send_batch_start_reminder():
	batches = frappe.get_all(
		"LMS Batch",
		{"start_date": add_days(nowdate(), 1), "published": 1},
		["name", "title", "start_date", "start_time", "medium"],
	)

	for batch in batches:
		students = frappe.get_all("LMS Batch Enrollment", {"batch": batch.name}, ["member", "member_name"])
		for student in students:
			send_mail(batch, student)


def send_mail(batch, student):
	subject = _("Your batch {0} is starting tomorrow").format(batch.title)
	template = "batch_start_reminder"

	args = {
		"student_name": student.member_name,
		"title": batch.title,
		"start_date": batch.start_date,
		"start_time": batch.start_time,
		"medium": batch.medium,
		"name": batch.name,
	}

	frappe.sendmail(
		recipients=student.member,
		subject=subject,
		template=template,
		args=args,
		header=[_(f"Batch Start Reminder: {batch.title}"), "orange"],
	)
