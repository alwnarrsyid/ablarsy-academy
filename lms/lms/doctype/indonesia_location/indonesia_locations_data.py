"""
Fixtures for Indonesia Location data.
Run with: bench --site [sitename] execute lms.lms.doctype.indonesia_location.indonesia_locations_data.import_locations
"""

import frappe

INDONESIA_LOCATIONS = [
    # DKI Jakarta
    {"province": "DKI Jakarta", "city": "Jakarta Pusat", "district": "Menteng", "postal_code": "10310"},
    {"province": "DKI Jakarta", "city": "Jakarta Pusat", "district": "Gambir", "postal_code": "10110"},
    {"province": "DKI Jakarta", "city": "Jakarta Pusat", "district": "Tanah Abang", "postal_code": "10210"},
    {"province": "DKI Jakarta", "city": "Jakarta Selatan", "district": "Kebayoran Baru", "postal_code": "12110"},
    {"province": "DKI Jakarta", "city": "Jakarta Selatan", "district": "Tebet", "postal_code": "12810"},
    {"province": "DKI Jakarta", "city": "Jakarta Selatan", "district": "Pancoran", "postal_code": "12780"},
    {"province": "DKI Jakarta", "city": "Jakarta Barat", "district": "Grogol Petamburan", "postal_code": "11470"},
    {"province": "DKI Jakarta", "city": "Jakarta Barat", "district": "Kebon Jeruk", "postal_code": "11530"},
    {"province": "DKI Jakarta", "city": "Jakarta Utara", "district": "Kelapa Gading", "postal_code": "14240"},
    {"province": "DKI Jakarta", "city": "Jakarta Utara", "district": "Tanjung Priok", "postal_code": "14310"},
    {"province": "DKI Jakarta", "city": "Jakarta Timur", "district": "Cakung", "postal_code": "13910"},
    {"province": "DKI Jakarta", "city": "Jakarta Timur", "district": "Duren Sawit", "postal_code": "13440"},

    # Jawa Barat
    {"province": "Jawa Barat", "city": "Bandung", "district": "Coblong", "postal_code": "40132"},
    {"province": "Jawa Barat", "city": "Bandung", "district": "Cicendo", "postal_code": "40171"},
    {"province": "Jawa Barat", "city": "Bandung", "district": "Sukasari", "postal_code": "40152"},
    {"province": "Jawa Barat", "city": "Bogor", "district": "Bogor Tengah", "postal_code": "16124"},
    {"province": "Jawa Barat", "city": "Bogor", "district": "Bogor Utara", "postal_code": "16152"},
    {"province": "Jawa Barat", "city": "Bogor", "district": "Bogor Selatan", "postal_code": "16310"},
    {"province": "Jawa Barat", "city": "Depok", "district": "Beji", "postal_code": "16421"},
    {"province": "Jawa Barat", "city": "Depok", "district": "Cimanggis", "postal_code": "16451"},
    {"province": "Jawa Barat", "city": "Bekasi", "district": "Bekasi Timur", "postal_code": "17111"},
    {"province": "Jawa Barat", "city": "Bekasi", "district": "Bekasi Barat", "postal_code": "17133"},
    {"province": "Jawa Barat", "city": "Cimahi", "district": "Cimahi Tengah", "postal_code": "40521"},
    {"province": "Jawa Barat", "city": "Tasikmalaya", "district": "Tawang", "postal_code": "46112"},
    {"province": "Jawa Barat", "city": "Sukabumi", "district": "Gunungpuyuh", "postal_code": "43121"},

    # Jawa Tengah
    {"province": "Jawa Tengah", "city": "Semarang", "district": "Semarang Tengah", "postal_code": "50134"},
    {"province": "Jawa Tengah", "city": "Semarang", "district": "Semarang Selatan", "postal_code": "50249"},
    {"province": "Jawa Tengah", "city": "Solo", "district": "Laweyan", "postal_code": "57142"},
    {"province": "Jawa Tengah", "city": "Solo", "district": "Jebres", "postal_code": "57126"},
    {"province": "Jawa Tengah", "city": "Yogyakarta", "district": "Gondokusuman", "postal_code": "55221"},
    {"province": "Jawa Tengah", "city": "Magelang", "district": "Magelang Tengah", "postal_code": "56117"},
    {"province": "Jawa Tengah", "city": "Salatiga", "district": "Sidorejo", "postal_code": "50714"},

    # Jawa Timur
    {"province": "Jawa Timur", "city": "Surabaya", "district": "Gubeng", "postal_code": "60281"},
    {"province": "Jawa Timur", "city": "Surabaya", "district": "Tegalsari", "postal_code": "60262"},
    {"province": "Jawa Timur", "city": "Surabaya", "district": "Wonokromo", "postal_code": "60243"},
    {"province": "Jawa Timur", "city": "Malang", "district": "Klojen", "postal_code": "65111"},
    {"province": "Jawa Timur", "city": "Malang", "district": "Lowokwaru", "postal_code": "65141"},
    {"province": "Jawa Timur", "city": "Sidoarjo", "district": "Sidoarjo", "postal_code": "61212"},
    {"province": "Jawa Timur", "city": "Gresik", "district": "Gresik", "postal_code": "61111"},
    {"province": "Jawa Timur", "city": "Kediri", "district": "Kota", "postal_code": "64125"},

    # Banten
    {"province": "Banten", "city": "Tangerang", "district": "Tangerang", "postal_code": "15111"},
    {"province": "Banten", "city": "Tangerang", "district": "Cipondoh", "postal_code": "15148"},
    {"province": "Banten", "city": "Tangerang Selatan", "district": "Pamulang", "postal_code": "15417"},
    {"province": "Banten", "city": "Tangerang Selatan", "district": "Serpong", "postal_code": "15310"},
    {"province": "Banten", "city": "Serang", "district": "Serang", "postal_code": "42111"},
    {"province": "Banten", "city": "Cilegon", "district": "Cilegon", "postal_code": "42411"},

    # Bali
    {"province": "Bali", "city": "Denpasar", "district": "Denpasar Selatan", "postal_code": "80223"},
    {"province": "Bali", "city": "Denpasar", "district": "Denpasar Utara", "postal_code": "80116"},
    {"province": "Bali", "city": "Badung", "district": "Kuta", "postal_code": "80361"},
    {"province": "Bali", "city": "Gianyar", "district": "Ubud", "postal_code": "80571"},

    # Sumatera Utara
    {"province": "Sumatera Utara", "city": "Medan", "district": "Medan Kota", "postal_code": "20212"},
    {"province": "Sumatera Utara", "city": "Medan", "district": "Medan Baru", "postal_code": "20153"},
    {"province": "Sumatera Utara", "city": "Binjai", "district": "Binjai Kota", "postal_code": "20714"},

    # Sumatera Selatan
    {"province": "Sumatera Selatan", "city": "Palembang", "district": "Ilir Barat I", "postal_code": "30128"},
    {"province": "Sumatera Selatan", "city": "Palembang", "district": "Ilir Timur I", "postal_code": "30111"},

    # Sulawesi Selatan
    {"province": "Sulawesi Selatan", "city": "Makassar", "district": "Ujung Pandang", "postal_code": "90111"},
    {"province": "Sulawesi Selatan", "city": "Makassar", "district": "Panakkukang", "postal_code": "90231"},

    # Kalimantan Timur
    {"province": "Kalimantan Timur", "city": "Balikpapan", "district": "Balikpapan Kota", "postal_code": "76111"},
    {"province": "Kalimantan Timur", "city": "Samarinda", "district": "Samarinda Kota", "postal_code": "75117"},

    # DI Yogyakarta
    {"province": "DI Yogyakarta", "city": "Yogyakarta", "district": "Gondokusuman", "postal_code": "55221"},
    {"province": "DI Yogyakarta", "city": "Yogyakarta", "district": "Gedongtengen", "postal_code": "55271"},
    {"province": "DI Yogyakarta", "city": "Sleman", "district": "Depok", "postal_code": "55281"},
    {"province": "DI Yogyakarta", "city": "Bantul", "district": "Bantul", "postal_code": "55711"},
]


def import_locations():
    """Import Indonesia location data."""
    count = 0
    for loc in INDONESIA_LOCATIONS:
        if not frappe.db.exists("Indonesia Location", {
            "province": loc["province"],
            "city": loc["city"],
            "postal_code": loc["postal_code"]
        }):
            doc = frappe.new_doc("Indonesia Location")
            doc.update(loc)
            doc.insert(ignore_permissions=True)
            count += 1

    frappe.db.commit()
    print(f"Imported {count} Indonesia locations")
    return count
