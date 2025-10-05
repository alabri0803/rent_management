# Overview

This **Rent Management System** is a comprehensive Django-based application designed to streamline property management. It handles buildings, units, tenants, lease contracts, payments, expenses, and maintenance requests, culminating in robust financial reporting. The system supports a bilingual interface (Arabic/English) and provides distinct portals for administrators and tenants. Its core purpose is to manage the entire rental property lifecycle efficiently, from initial setup to lease expiration and financial reconciliation, using Omani Rial (ر.ع / OMR) as the default currency. The project aims to provide a robust, scalable solution for property managers, enhancing operational efficiency and tenant satisfaction.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Framework & Core Technology

The system is built on **Django 5.2.7**, leveraging its ORM, admin interface, class-based views, template engine, and signal-based event handling. SQLite is used for local development, with options for MySQL/PostgreSQL in production.

## Application Structure

The application is structured into two main Django apps:

### 1. Dashboard App (Admin Portal)
Provides full administrative control for property managers, managing `Company`, `Building`, `Unit`, `Tenant`, `Lease`, `Payment`, `Expense`, `MaintenanceRequest`, `Document`, `Notification`, and `ContractTemplate` models. Key features include CRUD operations, lease renewal workflows, PDF report generation (tenant statements, P&L, occupancy), tenant rating, and multi-language support.

### 2. Portal App (Tenant Portal)
Offers a self-service portal for tenants to view lease details, payment history, submit maintenance requests, and access documents, restricted to their own data.

## Authentication & Authorization

Utilizes Django's built-in authentication. Access to the dashboard is restricted to staff users via a staff-required mixin. Tenant user accounts are automatically created and linked to `Tenant` models upon tenant creation.

## Database Design Patterns

Key relationships include one-to-many between Building-Units, Tenant-Leases, Unit-Leases, Lease-Payments, Lease-MaintenanceRequests, Lease-Documents, and Building-Expenses. Unique constraints prevent duplicate payment records, and computed fields derive lease status, payment summaries, and occupancy rates.

## Signal-Based Event System

Signals handle automatic tenant user creation, maintenance request notifications to staff, and lease expiration notifications to tenants.

## Frontend Architecture

**Tailwind CSS** provides styling with a custom color scheme. **Chart.js** is used for financial and occupancy charts. **FullCalendar** is referenced for lease calendars. The design is responsive, supports RTL for Arabic, and uses Django's template inheritance.

## PDF Generation

PDF generation uses **WeasyPrint** (preferred for Arabic), with **xhtml2pdf** and **ReportLab** as fallbacks. It generates payment receipts, tenant statements, P&L reports, and occupancy reports in Omani Rial.

## Internationalization (i18n)

**django-modeltranslation** supports model field translations. Django's language middleware enables dynamic language switching and URL prefixing. Arabic is the default language, and the system supports translated UI labels, verbose names, and messages. Timezone is set to Asia/Muscat. Automatic translation of Arabic to English is implemented for key database fields (Building name/address, Tenant name/authorized signatory, Expense description) via pre-save signals and the `deep-translator` library.

## File Handling

Organized upload directories for `company_logos/`, `lease_documents/`, `maintenance_requests/`, and `expense_receipts/`.

## Deployment Configuration

Development uses Django's server on 0.0.0.0:5000. Production deploys with **Gunicorn** and **Whitenoise** for static files. `CSRF_TRUSTED_ORIGINS` are configured for Replit domains.

## Feature Specifications

*   **Lease Management**: Tracks lease status (active, expiring_soon, expired, cancelled), generates PDF documents, and includes a lease renewal workflow.
*   **Payment & Expense Tracking**: Records monthly payments, handles partial payments, tracks various expenses, and includes a comprehensive check payment system with status tracking (pending, cashed, returned) and a dedicated check management section.
*   **Reporting**: Generates detailed financial reports (P&L, occupancy) and tenant statements. Profit/Loss reports visually indicate profit (green) or loss (red).
*   **Maintenance Requests**: Manages maintenance tickets with priority and status.
*   **Notifications**: Automated system for late payment warnings and lease renewal reminders, along with signal-based notifications for maintenance requests.
*   **User Management**: Full CRUD operations for user accounts, with staff-only access and custom login redirection based on user role.
*   **Currency**: All financial operations and reports are in Omani Rial (ر.ع / OMR).
*   **Lease Expiry Tracking**: Displays days until lease expiry with color-coded alerts on the dashboard.
*   **Enhanced Financial Display**: Detailed breakdown of annual rent, registration fees (with/without office fees) on lease detail pages.
*   **Enhanced Payment Summary**: Clear status badges, payment methods, dates, and next payment dates.

# External Dependencies

**Core Framework**:
- Django 5.2.7

**Database**:
- PyMySQL (for MySQL, if used)

**PDF Generation**:
- WeasyPrint
- xhtml2pdf
- ReportLab

**Internationalization**:
- django-modeltranslation
- deep-translator (for automatic translation)

**Frontend Libraries (CDN)**:
- Tailwind CSS
- Chart.js
- FullCalendar

**Date Handling**:
- python-dateutil

**Web Server**:
- Gunicorn
- Whitenoise

**Other Utilities**:
- Pillow
- requests, urllib3
- cryptography libraries (certifi, cffi, pyHanko)
- Arabic text support (arabic-reshaper, python-bidi)