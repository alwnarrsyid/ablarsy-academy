"""
Custom Certificate PDF Generator with Landscape Support
"""

import frappe
from frappe import _
from frappe.utils import get_url
import subprocess
import tempfile
import os


@frappe.whitelist()
def download_certificate_pdf(certificate_name):
    """
    Generate and download certificate PDF in landscape orientation.
    Uses Chrome/Chromium headless for better CSS support.
    """
    if not certificate_name:
        frappe.throw(_("Certificate name is required"))

    # Check if certificate exists and user has access
    if not frappe.db.exists("LMS Certificate", certificate_name):
        frappe.throw(_("Certificate not found"))

    certificate = frappe.get_doc("LMS Certificate", certificate_name)

    # Check permission - either owner, admin, or the member
    if not (
        frappe.session.user == certificate.member
        or frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "LMS Manager" in frappe.get_roles()
    ):
        frappe.throw(_("You don't have permission to access this certificate"))

    # Generate HTML content
    html_content = render_certificate_html(certificate)

    # Generate PDF
    pdf_content = generate_landscape_pdf(html_content)

    if pdf_content:
        frappe.local.response.filename = f"Certificate-{certificate_name}.pdf"
        frappe.local.response.filecontent = pdf_content
        frappe.local.response.type = "pdf"
    else:
        frappe.throw(_("Failed to generate PDF"))


def render_certificate_html(certificate):
    """
    Render the certificate HTML template with data.
    """
    # Get related data
    member = frappe.db.get_value("User", certificate.member, ["full_name", "email"], as_dict=True)
    course = None
    if certificate.course:
        course = frappe.db.get_value("LMS Course", certificate.course, ["title", "name", "image"], as_dict=True)

    logo = frappe.db.get_single_value("Website Settings", "banner_image")

    # Get instructors
    instructors = []
    if certificate.course:
        instructor_names = frappe.get_all(
            "Course Instructor",
            filters={"parent": certificate.course},
            pluck="instructor",
            order_by="idx"
        )
        for instructor in instructor_names:
            full_name = frappe.db.get_value("User", instructor, "full_name")
            if full_name:
                instructors.append(full_name)

    # Render template
    html_template = get_certificate_template()

    from jinja2 import Template
    template = Template(html_template)

    html_content = template.render(
        doc=certificate,
        member=member,
        course=course,
        logo=logo,
        instructors=instructors,
        get_url=get_url
    )

    return html_content


def get_certificate_template():
    """
    Return the certificate HTML template.
    """
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate of Completion</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Playfair+Display:ital,wght@0,600;1,600&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        @page {
            size: 297mm 210mm;
            margin: 0;
        }

        html, body {
            width: 297mm;
            height: 210mm;
            margin: 0;
            padding: 0;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #ffffff;
            color: #1e293b;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }

        .certificate-container {
            width: 297mm;
            height: 210mm;
            background-color: #ffffff;
            position: relative;
            display: flex;
            flex-direction: column;
            padding: 40px;
            overflow: hidden;
        }

        .certificate-border {
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            bottom: 20px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            pointer-events: none;
            z-index: 10;
        }

        .header {
            text-align: center;
            margin-top: 40px;
        }

        .certificate-logo {
            width: 80px;
            height: 80px;
            margin-bottom: 24px;
            object-fit: contain;
        }

        .title {
            font-family: "Libre Baskerville", Georgia, serif;
            font-size: 3.5rem;
            font-weight: 700;
            color: #000000;
            margin: 0;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .subtitle {
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            color: #64748b;
            margin-top: 10px;
            font-weight: 500;
        }

        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 0 60px;
        }

        .recipient-name {
            font-family: "Libre Baskerville", Georgia, serif;
            font-size: 2.75rem;
            font-weight: 700;
            color: #000000;
            margin: 16px 0 24px 0;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            min-width: 500px;
        }

        .completion-text {
            font-size: 1.125rem;
            color: #64748b;
            margin: 20px 0;
            max-width: 600px;
            line-height: 1.6;
        }

        .course-name {
            font-size: 2rem;
            font-weight: 700;
            color: #2c2c2c;
            margin-bottom: 8px;
        }

        .batch-name {
            font-size: 1.125rem;
            color: #ffffff;
            font-weight: 600;
            background-color: #2c2c2c;
            padding: 8px 24px;
            border-radius: 9999px;
            display: inline-block;
            margin-top: 10px;
        }

        .footer {
            margin-top: auto;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding: 0 40px 40px;
        }

        .footer-column {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .footer-column-right {
            align-items: flex-end;
        }

        .signature-block {
            text-align: center;
            min-width: 200px;
        }

        .signature-name {
            font-family: "Playfair Display", Georgia, serif;
            font-style: italic;
            font-size: 24px;
            margin-bottom: 4px;
        }

        .signature-line {
            height: 1px;
            background-color: #1e293b;
            margin-bottom: 8px;
            width: 100%;
        }

        .signature-title {
            font-size: 0.875rem;
            font-weight: 500;
            color: #1e293b;
        }

        .meta-info {
            font-size: 0.75rem;
            color: #64748b;
            text-align: left;
            display: grid;
            grid-template-columns: auto auto;
            gap: 4px 16px;
        }

        .meta-label {
            font-weight: 600;
        }

        .badge-icon {
            width: 80px;
            height: 80px;
            border: 2px solid #e2e8f0;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.7em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transform: rotate(-15deg);
            position: absolute;
            bottom: 60px;
            right: 60px;
            opacity: 0.5;
        }

        .badge-text {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="certificate-container">
        <div class="certificate-border"></div>

        <div class="header">
            {% if logo %}
            <img src="{{ get_url() }}{{ logo }}" alt="Logo" class="certificate-logo">
            {% endif %}
            <h1 class="title">Certificate of Completion</h1>
            <div class="subtitle">Proudly Presented To</div>
        </div>

        <div class="content">
            <div class="recipient-name">{{ member.full_name if member else doc.member }}</div>

            <p class="completion-text">
                For successfully completing the course requirements and demonstrating
                proficiency in the curriculum prescribed for
            </p>

            <div class="course-name">{{ course.title if course else "" }}</div>
            {% if doc.batch_name %}
            <div class="batch-name">{{ doc.batch_name }}</div>
            {% endif %}
        </div>

        <div class="footer">
            <div class="footer-column">
                <div class="meta-info">
                    <span class="meta-label">Certificate ID:</span>
                    <span>{{ doc.name }}</span>

                    <span class="meta-label">Issued By:</span>
                    <span>Ablarsy Academy</span>

                    <span class="meta-label">Recipient:</span>
                    <span>{{ doc.member }}</span>

                    <span class="meta-label">Created On:</span>
                    <span>{{ doc.creation.strftime('%d-%m-%Y %H:%M:%S') if doc.creation else '' }}</span>
                </div>
            </div>

            <div class="footer-column footer-column-right">
                <div class="signature-block">
                    <div class="signature-name">
                        {% for instructor in instructors %}
                        {{ instructor }}{% if not loop.last %}, {% endif %}
                        {% endfor %}
                    </div>
                    <div class="signature-line"></div>
                    <div class="signature-title">Course Instructor</div>
                </div>
            </div>
        </div>

        <div class="badge-icon">
            <div class="badge-text">Official<br>Verified</div>
        </div>
    </div>
</body>
</html>'''


def generate_landscape_pdf(html_content):
    """
    Generate PDF using Chromium headless with landscape orientation.
    """
    chromium_path = frappe.conf.get("chromium_binary_path") or "/usr/bin/chromium"

    if not os.path.exists(chromium_path):
        # Try alternative paths
        for path in ["/usr/bin/chromium-browser", "/usr/bin/google-chrome", "/usr/bin/chrome"]:
            if os.path.exists(path):
                chromium_path = path
                break

    if not os.path.exists(chromium_path):
        frappe.throw(_("Chromium is not installed. Please install Chromium."))

    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
        html_file.write(html_content)
        html_path = html_file.name

    pdf_path = html_path.replace('.html', '.pdf')

    try:
        # Run Chromium headless to generate PDF
        cmd = [
            chromium_path,
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--print-to-pdf=' + pdf_path,
            '--print-to-pdf-no-header',
            '--no-pdf-header-footer',
            f'--run-all-compositor-stages-before-draw',
            f'file://{html_path}'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            return pdf_content
        else:
            frappe.log_error(f"Chromium error: {result.stderr}", "Certificate PDF Generation")
            return None

    except subprocess.TimeoutExpired:
        frappe.log_error("Chromium timeout", "Certificate PDF Generation")
        return None
    except Exception as e:
        frappe.log_error(str(e), "Certificate PDF Generation")
        return None
    finally:
        # Cleanup temp files
        if os.path.exists(html_path):
            os.remove(html_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@frappe.whitelist(allow_guest=True)
def get_certificate_html(certificate_name):
    """
    Get certificate HTML for preview (without PDF).
    Returns HTML that can be displayed in browser.
    """
    if not certificate_name:
        frappe.throw(_("Certificate name is required"))

    if not frappe.db.exists("LMS Certificate", certificate_name):
        frappe.throw(_("Certificate not found"))

    certificate = frappe.get_doc("LMS Certificate", certificate_name)
    html_content = render_certificate_html(certificate)

    return html_content
