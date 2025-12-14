# Ablarsy Academy LMS

A specialized Learning Management System (LMS) built on [Frappe LMS](https://github.com/frappe/lms) for **Ablarsy Academy**. This repository contains custom integrations and enhancements tailored for the Indonesian market and seamless virtual classroom experiences.

## 🚀 Key Features

### 1. Google Meet Integration (New)

-   **Automated Meeting Creation**: Automatically generates Google Meet links when creating Live Classes.
-   **Seamless Calendar Sync**: Integrates directly with Google Calendar API to schedule sessions.
-   **Dual Platform Support**: Flexible choice between Zoom and Google Meet for each batch or class session.

### 2. Midtrans Payment Gateway (New)

-   **Indonesian Payment Support**: Full integration with Midtrans for accepting payments via GoPay, Bank Transfer, ShopeePay, etc.
-   **Automated Enrollment**: Students are automatically enrolled in batches upon successful payment verification.
-   **Rupiah Formatting**: UI enhanced to properly display currency in IDR (Rp).

### 3. Enhanced UI/UX

-   **Dark/Light Mode**: Fully supported theme switching.
-   **Responsive Design**: Optimized for mobile and desktop experiences.
-   **Custom Batch Management**: Improved tools for instructors to manage student batches.

## 🛠️ Tech Stack & Requirements

-   **Framework**: [Frappe Framework](https://frappe.io/framework)
-   **Frontend**: Vue.js 3
-   **Database**: MariaDB
-   **Cache**: Redis
-   **Deployment**: Docker

## ⚙️ Setup Guide (Local Development)

This project is configured to run easily with Docker and supports ngrok for testing external integrations (Google OAuth, Midtrans Webhooks).

### Prerequisites

-   Docker & Docker Compose
-   Ngrok (optional, for exposing localhost)

### Quick Start

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/alwnarrsyid/ablarsy-academy.git
    cd ablarsy-academy/docker
    ```

2.  **Start Services:**
    ```bash
    docker compose up -d
    ```
    -   This will start MariaDB, Redis, and the Frappe backend/frontend services.
    -   Access the site at `http://localhost:8000`.

### 🔑 Configuration

#### Google Meet Integration

1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable **Google Calendar API**.
3.  Create **OAuth 2.0 Credentials** (Web Application).
4.  Add Redirect URI: `http://localhost:8000/api/method/frappe.integrations.doctype.google_calendar.google_calendar.google_callback`.
    -   _Note: If using ngrok, use your ngrok URL instead._
5.  In LMS, go to **Google Settings** and enter Client ID & Secret.
6.  Create a **Google Calendar** record in LMS and authorize it.
7.  Create **LMS Google Meet Settings** and link it to the calendar.

#### Midtrans Payment

1.  Get Server Key & Client Key from [Midtrans Dashboard](https://dashboard.midtrans.com/).
2.  In LMS, go to **Midtrans Settings**.
3.  Enter credentials and enable the gateway.

## 📦 Docker Commands

-   **Migrate Database**: `docker compose exec backend bench --site lms.localhost migrate`
-   **View Logs**: `docker compose logs -f`
-   **Restart Services**: `docker compose restart`

## 🤝 Contribution

Developed by **Antigravity** for **Ablarsy Academy**.
For issues, please open a ticket in the repository.
