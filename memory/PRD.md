# AZAI Healthcare Application - Product Requirements Document

## Original Problem Statement
Build a comprehensive healthcare application for Ohio Medicaid providers featuring:
- PDF timesheet scanning with OCR (Gemini Vision API)
- Electronic Visit Verification (EVV) compliance with Sandata
- Payer and Contract management for Medicaid billing
- Multi-tenant organization management
- Admin panel for system administration

## Core Requirements
1. **Timesheet Processing**: Scan and extract data from paper timesheets using AI/OCR
2. **EVV Compliance**: Meet Ohio Medicaid EVV requirements with Sandata integration
3. **Billing Management**: Track payers, contracts, and billing codes
4. **User Management**: Multi-tenant with organization isolation
5. **Admin Panel**: Super admin tools for managing organizations and credentials

## Current Architecture
```
/app/
├── backend/
│   ├── server.py             # Main FastAPI application
│   ├── routes_admin.py       # Admin panel APIs
│   ├── routes_notifications.py   # Notification system
│   ├── routes_notifications_extended.py  # Extended notification features
│   ├── validation_utils.py   # Data validation rules
│   ├── evv_export.py         # EVV data export
│   └── scan_config.py        # Centralized OCR configuration
├── frontend/
│   └── src/pages/
│       ├── NotificationCenter.js
│       ├── admin/AdminOrganizations.js
│       ├── admin/AdminCredentials.js
│       ├── Payers.js
│       ├── Employees.js
│       ├── Patients.js
│       └── EVVManagement.js
└── tests/
    └── test_admin_notifications_validation.py
```

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React
- **Database**: MongoDB
- **OCR**: Google Gemini Vision API (gemini-2.0-flash)
- **Payments**: Stripe
- **EVV**: Sandata API (JSON export implemented)

## What's Been Implemented

### January 5, 2026 - Bug Fixes Session
**Fixed 4 Critical Bugs:**
1. **Notification Routes Double Prefix** - Changed from `/api/notifications` to `/notifications` to prevent `/api/api/notifications/...`
2. **Admin Organization ObjectId Serialization** - Added `_id` removal after MongoDB insert
3. **Admin Organization Field Mismatch** - Fixed queries to support both `id` and `organization_id` fields
4. **Admin Organization Update** - Same field mismatch fix applied

**Test Results:** 18/18 tests passing

### Previous Sessions (Summary)
- PDF scanning workflow stabilized with `gemini-2.0-flash` model
- Payer/Contract management system re-architected
- Employee billing codes linked to timesheets
- EVV JSON export for Sandata manual submission
- Notification system implemented

## Pending Issues (Prioritized)

### P1 - Critical
- **poppler-utils Instability**: PDF dependency keeps getting uninstalled. Workaround script in place, but root cause unknown.

### P2 - Medium
- Test the Notification System end-to-end (UI verification)
- Build Mock ODM Integration endpoints

### P3 - Low
- Test Admin Panel CRUD from Frontend
- Implement X12 EDI Generation Logic
- Deploy external PDF service to Railway

## Upcoming Tasks
1. Build Mock ODM Integration (`/api/mock/odm/soap`, `/api/mock/odm/sftp`)
2. Implement X12 EDI Generation Logic in `edi_claim_generator.py`
3. Real backend claims logic for ODM/Availity
4. Implement 835 Remittance Parsing
5. Automated SFTP polling for 835 files

## Test Credentials
- **Super Admin**: admin@medicaidservices.com / Admin2024!
- **API URL**: https://medstaff-portal-27.preview.emergentagent.com

## Known Mocked Integrations
- ODM SOAP/SFTP (placeholder)
- Availity API (placeholder)
- Sandata API (JSON export works, direct API not connected)

## Database Collections
- `organizations` - Multi-tenant orgs
- `users` - User accounts
- `patients` - Patient profiles
- `employees` - Employee/DCW profiles
- `timesheets` - Scanned timesheets
- `payers` - Permanent payer entities (Ohio Medicaid pre-seeded)
- `payer_contracts` - Time-bound contracts under payers
- `notifications` - System notifications
- `evv_visits` - EVV visit records
