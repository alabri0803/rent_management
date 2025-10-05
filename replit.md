# Overview

This is a comprehensive **Rent Management System** built with Django. The application helps property managers oversee buildings, units, tenants, lease contracts, payments, expenses, maintenance requests, and generate financial reports. It features a bilingual interface (Arabic/English) with separate portals for administrators and tenants.

The system manages the complete lifecycle of rental properties: from adding buildings and units, creating tenant profiles, drafting lease agreements, tracking payments and expenses, handling maintenance requests, to generating various financial and occupancy reports.

**Currency**: The system uses Omani Rial (ر.ع / OMR) as the default currency throughout the application.

# Recent Changes

## October 5, 2025
- **Custom Login Redirect**: Implemented custom login view that redirects users based on their role
  - Staff users (admin/employees) are redirected to dashboard home page
  - Tenant users are redirected to tenant portal dashboard
  - Created CustomLoginView that overrides Django's default login behavior

- **Check Payment Feature**: Added comprehensive check payment support to the payment system
  - Added payment_method field with choices: cash, check, bank_transfer, other
  - Added check-specific fields: check_number, check_date, bank_name
  - Updated payment form with dynamic showing/hiding of check fields based on payment method
  - Enhanced payment list to display payment method and check number
  - Updated payment receipt template to show complete check information when applicable
  - Created migration (0014) for new payment fields

## October 4, 2025
- **Currency Update**: Changed all currency references from Saudi Riyal (ر.س) to Omani Rial (ر.ع) in tenant_detail.html
- **Database Configuration**: Updated settings.py to use SQLite for local development instead of external MySQL database
- **CSRF Configuration**: Added CSRF_TRUSTED_ORIGINS for Replit domains (*.replit.dev, *.repl.co)
- **Project Setup**: Configured the project to run on Replit environment
- **Workflow**: Set up Django development server workflow on port 5000
- **Deployment**: Configured autoscale deployment with Gunicorn WSGI server

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Framework & Core Technology

**Django 5.2.7** - Full-stack Python web framework with:
- Django ORM for database abstraction
- Built-in admin interface for data management
- Class-based views (ListView, DetailView, CreateView, UpdateView, DeleteView)
- Template engine with internationalization support
- Signal-based event handling for notifications

**Database**: SQLite for local development (production can use MySQL/PostgreSQL)

## Application Structure

The system is organized into two main Django apps:

### 1. Dashboard App (Admin Portal)
- **Purpose**: Full administrative control for property managers
- **Key Models**:
  - `Company`: Stores company profile, logo, contact information
  - `Building`: Property/building information
  - `Unit`: Individual rental units with type (office/apartment/shop), floor, availability status
  - `Tenant`: Tenant profiles (individual or company) with rating system
  - `Lease`: Rental contracts with status tracking (active, expiring_soon, expired, cancelled)
  - `Payment`: Monthly payment records with year/month tracking
  - `Expense`: Operating expenses categorized by type
  - `MaintenanceRequest`: Maintenance tickets with priority and status
  - `Document`: File attachments for leases
  - `Notification`: System notifications for users
  - `ContractTemplate`: Reusable contract templates

- **Key Features**:
  - Dashboard with financial metrics and charts
  - CRUD operations for all entities
  - Lease renewal workflow
  - PDF report generation (tenant statements, P&L reports, occupancy reports, payment receipts)
  - Tenant rating system
  - Multi-language support (Arabic as default, English available)

### 2. Portal App (Tenant Portal)
- **Purpose**: Self-service portal for tenants
- **Features**:
  - View current lease details
  - Check payment history
  - Submit maintenance requests
  - Access lease documents
  - Limited to tenant's own data via user authentication

## Authentication & Authorization

- **Django's built-in authentication system**
- **Staff-required mixin**: Restricts dashboard access to staff users only
- **Tenant user accounts**: Automatically created via signals when new tenant is added
  - Username derived from email or phone
  - Initial password set to phone number
  - One-to-one relationship between Tenant and User models

## Database Design Patterns

**Key Relationships**:
- Building → Units (one-to-many)
- Tenant → Leases (one-to-many)
- Unit → Leases (one-to-many)
- Lease → Payments (one-to-many)
- Lease → MaintenanceRequests (one-to-many)
- Lease → Documents (one-to-many)
- Building → Expenses (one-to-many)

**Unique Constraints**:
- Payment records are unique per lease/month/year combination (prevents duplicate payments)

**Computed Fields**:
- Lease status calculated based on dates (active, expiring_soon, expired)
- Payment summaries aggregated from payment records
- Building occupancy rates calculated from unit availability

## Signal-Based Event System

Located in `dashboard/signals.py`:
1. **Auto-create tenant user accounts** when new tenant is created
2. **Maintenance request notifications** sent to staff when requests are submitted or updated
3. **Lease expiration notifications** sent to tenants when contracts are expiring soon

## Frontend Architecture

- **Tailwind CSS** for styling with custom color scheme (primary: #993333, secondary: #D4AF37)
- **Chart.js** for financial trend visualization and occupancy charts
- **FullCalendar** for lease renewal calendar (referenced but implementation not visible)
- **Responsive design** with mobile-friendly layouts
- **RTL support** for Arabic language
- **Template inheritance** using base.html templates for consistent layouts

## PDF Generation

Uses multiple libraries with fallback strategy:
- **WeasyPrint** (preferred for Arabic text support)
- **xhtml2pdf** (fallback option)
- **ReportLab** (available in requirements)

Generates:
- Payment receipts (with bilingual Arabic/English format)
- Tenant account statements
- Monthly/Annual profit & loss reports
- Occupancy reports

All generated reports use Omani Rial (ر.ع / OMR) as the currency.

## Internationalization (i18n)

- **django-modeltranslation** for model field translations
- **Language middleware** for dynamic language switching
- **URL prefixing** with language codes (e.g., /ar/dashboard/, /en/dashboard/)
- **Default language**: Arabic (ar)
- **Translated content**: UI labels, model verbose names, messages
- **Timezone**: Asia/Muscat (Oman Standard Time)

## File Handling

Organized upload directories:
- `company_logos/` - Company branding
- `lease_documents/` - Contract attachments
- `maintenance_requests/` - Issue photos
- `expense_receipts/` - Expense documentation

## Deployment Configuration

- **Development**: Django development server on 0.0.0.0:5000
- **Production**: Gunicorn WSGI server with autoscale deployment
- **Whitenoise middleware** for static file serving
- **Static files** configuration for production
- **ALLOWED_HOSTS** set to accept all (should be restricted in production)
- **CSRF_TRUSTED_ORIGINS** configured for Replit domains

## Form Handling

Custom ModelForms with:
- Tailwind CSS styling applied to all form fields
- Validation at model and form level
- Specific forms for lease cancellation, tenant rating, document upload

## URL Structure

- `/admin/` - Django admin interface
- `/dashboard/` - Admin portal (staff only)
  - Buildings, units, tenants, leases, payments, expenses, maintenance, reports
- `/` - Tenant portal (public homepage)
  - Dashboard, maintenance requests
- `/accounts/` - Django auth URLs (login, logout, password management)

# External Dependencies

**Core Framework**:
- Django 5.2.7
- PyMySQL (MySQL database adapter - optional for production)

**PDF Generation**:
- WeasyPrint (preferred)
- xhtml2pdf (fallback)
- ReportLab

**Internationalization**:
- django-modeltranslation

**Frontend Libraries (CDN)**:
- Tailwind CSS
- Chart.js
- FullCalendar (referenced)

**Date Handling**:
- python-dateutil (relativedelta for date calculations)

**Web Server**:
- Gunicorn (production WSGI server)
- Whitenoise (static file serving)

**Other Utilities**:
- Pillow (image processing)
- requests, urllib3 (HTTP clients)
- cryptography libraries (certifi, cffi, pyHanko for digital signatures)
- Arabic text support (arabic-reshaper, python-bidi)

**Database**:
- SQLite (local development)
- MySQL support available via PyMySQL (for production if needed)
- PostgreSQL support can be configured

# Development Setup

1. Python 3.11 is required
2. All dependencies are installed via requirements.txt
3. Database migrations are already applied
4. Server runs on port 5000 (0.0.0.0:5000)
5. To create a superuser: `python manage.py createsuperuser`
6. Access admin at: `/admin/`
7. Access tenant portal at: `/`
