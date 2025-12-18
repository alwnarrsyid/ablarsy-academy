# Ablarsy Academy LMS

Customized Learning Management System based on [Frappe LMS](https://github.com/frappe/lms).

## 🎯 Overview

Ablarsy Academy LMS is a comprehensive learning management system with Indonesian payment gateway integration (Midtrans), mobile-optimized UI, PWA support, and custom landscape certificate PDF generation.

---

## ✨ Key Customizations

### 1. 💳 Midtrans Payment Gateway Integration

**Location:** `lms/lms/gateways/midtrans_gateway.py`

Indonesian payment gateway integration supporting:

-   Credit/Debit Cards
-   Bank Transfer (BCA, BNI, BRI, Mandiri, Permata)
-   E-Wallets (GoPay, ShopeePay, QRIS)
-   Convenience Store (Indomaret, Alfamart)

**Configuration:**

```
Frappe Desk → LMS Settings → Midtrans Settings
- Server Key: Your Midtrans Server Key
- Client Key: Your Midtrans Client Key
- Environment: Sandbox / Production
```

### 2. 📜 Custom Certificate PDF (Landscape)

**Location:** `lms/lms/custom_certificate.py`

Custom certificate PDF generator that:

-   Generates **A4 Landscape** PDF using Chromium headless
-   Bypasses Frappe's default PDF generator (which has orientation issues)
-   Beautiful design with custom fonts (Inter, Libre Baskerville, Playfair Display)
-   Includes logo, instructor signatures, and certificate details

**Endpoint:** `/api/method/lms.lms.custom_certificate.download_certificate_pdf`

**Updated Files:**

-   `frontend/src/components/CertificationLinks.vue`
-   `frontend/src/pages/ProfileCertificates.vue`
-   `frontend/src/pages/CourseCertification.vue`
-   `frontend/src/components/CourseCardOverlay.vue`
-   `frontend/src/components/Modals/Event.vue`
-   `lms/www/certificate.py`
-   `lms/lms/doctype/lms_certificate/lms_certificate.js`
-   `lms/templates/emails/certification.html`

### 3. 📱 Mobile Layout Optimization

**Location:** `frontend/src/components/MobileLayout.vue`

-   Fixed mobile sidebar navigation
-   Flattened nested sidebar links for mobile display
-   Improved touch interactions
-   PWA-optimized bottom navigation

### 4. 🔧 Utility Functions Enhancement

**Location:** `frontend/src/utils/index.js`

-   `getSidebarLinks()` - Returns grouped sidebar links for role-based navigation
-   `formatRupiah()` - Indonesian Rupiah currency formatting

---

## 🖥️ Server Requirements

### Chromium Installation (Required for Certificate PDF)

```bash
# For Docker environment
docker exec -u root -it lms-frappe-1 bash -c "apt-get update && apt-get install -y chromium chromium-driver"
```

### Chromium Path Configuration

Add to `site_config.json` or `common_site_config.json`:

```json
{
	"chromium_binary_path": "/usr/bin/chromium"
}
```

---

## 🚀 Deployment

### Docker Deployment

1. **Clone repository:**

```bash
git clone https://github.com/alwnarrsyid/ablarsy-academy.git lms
cd lms
```

2. **Build frontend:**

```bash
docker exec lms-frappe-1 bash -c "cd /home/frappe/frappe-bench/apps/lms/frontend && yarn build"
```

3. **Copy build files:**

```bash
docker exec lms-frappe-1 bash -c "cp /home/frappe/frappe-bench/apps/lms/frontend/dist/index.html /home/frappe/frappe-bench/apps/lms/lms/public/frontend/"
docker exec lms-frappe-1 bash -c "cp -r /home/frappe/frappe-bench/apps/lms/frontend/dist/assets /home/frappe/frappe-bench/apps/lms/lms/public/frontend/"
docker exec lms-frappe-1 bash -c "cp /home/frappe/frappe-bench/apps/lms/lms/public/frontend/index.html /home/frappe/frappe-bench/apps/lms/lms/www/lms.html"
```

4. **Bench build:**

```bash
docker exec lms-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench build --force"
```

5. **Clear cache:**

```bash
docker ps --format "{{.Names}}" | grep redis | xargs -I {} docker exec {} redis-cli flushall
docker exec lms-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench --site lms.localhost clear-cache"
```

6. **Restart:**

```bash
docker restart lms-frappe-1
```

---

## 📁 Project Structure

```
lms/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MobileLayout.vue          # Mobile navigation
│   │   │   ├── CertificationLinks.vue    # Certificate download button
│   │   │   ├── CourseCardOverlay.vue     # Course card actions
│   │   │   └── Modals/
│   │   │       └── Event.vue             # Evaluation modal
│   │   ├── pages/
│   │   │   ├── ProfileCertificates.vue   # User certificates list
│   │   │   └── CourseCertification.vue   # Course certification page
│   │   └── utils/
│   │       └── index.js                  # Utility functions
│   └── ...
├── lms/
│   ├── lms/
│   │   ├── custom_certificate.py         # Custom PDF generator
│   │   ├── gateways/
│   │   │   └── midtrans_gateway.py       # Midtrans integration
│   │   └── doctype/
│   │       └── lms_certificate/
│   │           └── lms_certificate.js    # Desk UI integration
│   ├── www/
│   │   └── certificate.py                # Certificate redirect handler
│   └── templates/
│       └── emails/
│           └── certification.html        # Certificate email template
└── ...
```

---

## 🔐 Environment Variables

| Variable                 | Description          | Required |
| ------------------------ | -------------------- | -------- |
| `MIDTRANS_SERVER_KEY`    | Midtrans Server Key  | Yes      |
| `MIDTRANS_CLIENT_KEY`    | Midtrans Client Key  | Yes      |
| `MIDTRANS_IS_PRODUCTION` | Production mode flag | Yes      |

---

## 📝 Changelog

### v2.43.0 (2024-12-18)

-   ✅ Added custom landscape certificate PDF generator
-   ✅ Integrated Midtrans payment gateway
-   ✅ Optimized mobile layout navigation
-   ✅ Enhanced sidebar links for role-based access
-   ✅ PWA improvements

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

-   [Frappe LMS](https://github.com/frappe/lms) - Base LMS framework
-   [Midtrans](https://midtrans.com) - Indonesian payment gateway
-   [Frappe Framework](https://frappeframework.com) - Backend framework

---

## 📞 Support

For support, email alwanforjobs@gmail.com or create an issue in this repository.
