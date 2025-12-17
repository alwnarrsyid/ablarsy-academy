"""
Script to import Indonesia wilayah data from SQL file.

Usage:
1. Place wilayah_2020.sql in the same directory as this script
2. Run: bench --site [sitename] execute lms.lms.doctype.indonesia_location.import_wilayah.import_from_sql

Or run with file path:
bench --site [sitename] execute lms.lms.doctype.indonesia_location.import_wilayah.import_from_sql --kwargs '{"sql_file": "/path/to/wilayah_2020.sql"}'
"""

import re
import frappe


def parse_sql_file(sql_file):
	"""Parse the SQL file and extract wilayah data."""
	with open(sql_file, 'r', encoding='utf-8') as f:
		content = f.read()

	# Find all INSERT values
	# Pattern: ('kode', 'nama')
	pattern = r"\('([^']+)',\s*'([^']+)'\)"
	matches = re.findall(pattern, content)

	return matches


def categorize_by_code(data):
	"""Categorize data by hierarchy level based on code format."""
	provinces = {}  # XX
	cities = {}     # XX.XX
	districts = {}  # XX.XX.XX
	villages = {}   # XX.XX.XX.XXXX

	for kode, nama in data:
		parts = kode.split('.')

		if len(parts) == 1 and len(kode) == 2:
			# Province: XX
			provinces[kode] = nama
		elif len(parts) == 2:
			# City: XX.XX
			cities[kode] = nama
		elif len(parts) == 3:
			# District: XX.XX.XX
			districts[kode] = nama
		elif len(parts) == 4:
			# Village: XX.XX.XX.XXXX
			villages[kode] = nama

	return provinces, cities, districts, villages


def import_from_sql(sql_file=None):
	"""Import wilayah data from SQL file into Indonesia Location DocType."""
	import os

	if not sql_file:
		# Try to find the file in common locations
		possible_paths = [
			'/home/frappe/frappe-bench/apps/lms/wilayah_2020.sql',
			'/home/frappe/frappe-bench/apps/lms/lms/lms/doctype/indonesia_location/wilayah_2020.sql',
			'/tmp/wilayah_2020.sql',
		]
		for path in possible_paths:
			if os.path.exists(path):
				sql_file = path
				break

	if not sql_file or not os.path.exists(sql_file):
		print(f"SQL file not found. Please provide the correct path.")
		print(f"Tried: {possible_paths if not sql_file else sql_file}")
		return 0

	print(f"Parsing SQL file: {sql_file}")
	data = parse_sql_file(sql_file)
	print(f"Found {len(data)} total records")

	# Categorize by level
	provinces, cities, districts, villages = categorize_by_code(data)
	print(f"Provinces: {len(provinces)}, Cities: {len(cities)}, Districts: {len(districts)}, Villages: {len(villages)}")

	# Import villages with full hierarchy
	count = 0
	batch_size = 500
	batch = []

	for village_code, village_name in villages.items():
		parts = village_code.split('.')
		province_code = parts[0]
		city_code = f"{parts[0]}.{parts[1]}"
		district_code = f"{parts[0]}.{parts[1]}.{parts[2]}"

		province_name = provinces.get(province_code, "")
		city_name = cities.get(city_code, "")
		district_name = districts.get(district_code, "")

		if not province_name or not city_name or not district_name:
			continue

		# Clean up names (remove KAB./KOTA prefix for cleaner display)
		city_display = city_name.replace("KAB. ", "").replace("KOTA ", "")

		batch.append({
			"doctype": "Indonesia Location",
			"province": province_name.title(),
			"city": city_display.title(),
			"district": district_name.title(),
			"village": village_name.title(),
		})

		if len(batch) >= batch_size:
			insert_batch(batch)
			count += len(batch)
			print(f"Imported {count} records...")
			batch = []

	# Insert remaining
	if batch:
		insert_batch(batch)
		count += len(batch)

	frappe.db.commit()
	print(f"Successfully imported {count} Indonesia locations")
	return count


def insert_batch(batch):
	"""Insert a batch of records."""
	for doc_data in batch:
		try:
			# Check if exists
			existing = frappe.db.exists("Indonesia Location", {
				"province": doc_data["province"],
				"city": doc_data["city"],
				"district": doc_data["district"],
				"village": doc_data["village"],
			})

			if not existing:
				doc = frappe.new_doc("Indonesia Location")
				doc.update(doc_data)
				doc.flags.ignore_permissions = True
				doc.insert()
		except Exception as e:
			# Skip duplicates or errors
			pass


def import_sample():
	"""Import a sample of locations for testing."""
	sample_data = [
		# DKI Jakarta
		{"province": "Dki Jakarta", "city": "Jakarta Pusat", "district": "Menteng", "village": "Menteng"},
		{"province": "Dki Jakarta", "city": "Jakarta Pusat", "district": "Gambir", "village": "Gambir"},
		{"province": "Dki Jakarta", "city": "Jakarta Selatan", "district": "Kebayoran Baru", "village": "Senayan"},
		{"province": "Dki Jakarta", "city": "Jakarta Selatan", "district": "Tebet", "village": "Tebet Barat"},

		# Jawa Barat
		{"province": "Jawa Barat", "city": "Bandung", "district": "Coblong", "village": "Dago"},
		{"province": "Jawa Barat", "city": "Bogor", "district": "Bogor Tengah", "village": "Babakan"},
		{"province": "Jawa Barat", "city": "Depok", "district": "Beji", "village": "Beji"},

		# Jawa Tengah
		{"province": "Jawa Tengah", "city": "Semarang", "district": "Semarang Tengah", "village": "Sekayu"},
		{"province": "Jawa Tengah", "city": "Solo", "district": "Laweyan", "village": "Laweyan"},

		# Jawa Timur
		{"province": "Jawa Timur", "city": "Surabaya", "district": "Gubeng", "village": "Gubeng"},
		{"province": "Jawa Timur", "city": "Malang", "district": "Klojen", "village": "Klojen"},

		# Bali
		{"province": "Bali", "city": "Denpasar", "district": "Denpasar Selatan", "village": "Sanur"},
		{"province": "Bali", "city": "Badung", "district": "Kuta", "village": "Kuta"},
	]

	count = 0
	for data in sample_data:
		try:
			if not frappe.db.exists("Indonesia Location", {
				"province": data["province"],
				"city": data["city"],
				"district": data["district"],
				"village": data["village"],
			}):
				doc = frappe.new_doc("Indonesia Location")
				doc.update(data)
				doc.flags.ignore_permissions = True
				doc.insert()
				count += 1
		except Exception as e:
			pass

	frappe.db.commit()
	print(f"Imported {count} sample locations")
	return count
