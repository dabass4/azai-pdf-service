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
│   ├── routes_mock_odm.py    # Mock ODM SOAP/SFTP simulation
│   ├── routes_claims.py      # Claims management APIs
│   ├── edi_claim_generator.py    # ENHANCED: X12 837P EDI generation
│   ├── edi_x12_builder.py    # X12 segment builders
│   ├── claims_service.py     # Claims processing orchestration
│   ├── validation_utils.py   # Data validation rules
│   ├── evv_export.py         # EVV data export
│   └── scan_config.py        # Centralized OCR configuration
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── NotificationCenter.js
│       │   ├── NotificationPreferences.js
│       │   └── admin/
│       ├── components/
│       │   ├── NotificationBell.js
│       │   └── NotificationPopup.js
│       └── contexts/
│           └── NotificationContext.js
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
- **EDI**: X12 837P 5010 compliant claim generation

## What's Been Implemented

### January 5, 2026 - X12 EDI Generation & Notification UI Testing
**X12 837P EDI Generation Logic:**
- Enhanced `edi_claim_generator.py` with full Ohio Medicaid support
- Added `generate_837p_claim()` function for claims service integration
- Added `generate_837p_batch()` for multi-claim SFTP batch submission
- Ohio HCPCS codes library (T1019, T1020, S5125, etc.) with rates
- Claim data transformation from timesheet/patient/employee records
- Validation utilities for claim data

**Notification System UI Fixes (6 bugs fixed):**
- Fixed missing `/api` prefix in 5 frontend files
- Fixed backend route ordering (extended routes before main routes)
- 100% of notification UI tests passing

### January 5, 2026 - Mock ODM Integration
**Mock ODM SOAP/SFTP Endpoints:**
- `POST /api/mock/odm/soap/eligibility` - Simulates 270/271 eligibility verification
- `POST /api/mock/odm/soap/claim-status` - Simulates 276/277 claim status inquiry
- `POST /api/mock/odm/sftp/upload` - Mock 837 file upload
- `POST /api/mock/odm/sftp/generate-835` - Generate mock 835 remittance advice
- `POST /api/mock/odm/sftp/generate-999` - Generate mock 999 acknowledgment

### January 5, 2026 - Bug Fixes Session
**Fixed 4 Critical Backend Bugs:**
1. Notification Routes Double Prefix
2. Admin Organization ObjectId Serialization
3. Admin Organization Field Mismatch
4. Admin Organization Update

**Test Results:** 18/18 backend tests passing

### Previous Sessions (Summary)
- PDF scanning workflow stabilized with `gemini-2.0-flash` model
- Payer/Contract management system re-architected
- Employee billing codes linked to timesheets
- EVV JSON export for Sandata manual submission

## Pending Issues (Prioritized)

### P1 - Critical
- **poppler-utils Instability**: PDF dependency workaround in place

### P2 - Medium
- ~~**Timesheets API Corrupted Data**~~: ✅ FIXED - Backend data normalization + 31 records repaired
- ~~**Frontend NaN Error**~~: ✅ FIXED - Added NaN guards in units calculation (App.js)

### P3 - Low
- Deploy external PDF service to Railway

## Upcoming Tasks
1. ~~Implement X12 EDI Generation Logic~~ ✅ COMPLETED
2. ~~Test Notification System from UI~~ ✅ COMPLETED
3. Build real ODM/Availity connection (when credentials available)
4. Implement 835 Remittance Parsing (parser exists, needs integration)
5. Automated SFTP polling for 835 files

## Test Credentials
- **Super Admin**: admin@medicaidservices.com / Admin2024!
- **API URL**: https://medstaff-portal-27.preview.emergentagent.com

## EDI Claim Generation Guide
```python
from edi_claim_generator import generate_837p_claim, OHIO_HCPCS_CODES

# Generate single claim
edi_content = generate_837p_claim(
    claims_data=[{
        'claim': {'claim_id': 'CLM001'},
        'timesheet': {'date': '2024-01-15', 'service_code': 'T1019', 'total_hours': 4},
        'patient': {'first_name': 'JOHN', 'last_name': 'DOE', 'medicaid_number': '123456789012'},
        'employee': {'first_name': 'JANE', 'last_name': 'SMITH', 'npi': '1234567890'}
    }],
    sender_id='1234567',
    provider_name='HEALTHCARE PROVIDER',
    provider_npi='9876543210'
)
```

## Known Mocked Integrations
- **Mock ODM SOAP/SFTP**: For testing claims workflow
- **Real ODM/Availity**: Not yet connected (requires trading partner enrollment)
- **Sandata**: JSON export works, direct API not connected

## Database Collections
- `organizations` - Multi-tenant orgs
- `users` - User accounts
- `patients` - Patient profiles
- `employees` - Employee/DCW profiles
- `timesheets` - Scanned timesheets
- `payers` - Permanent payer entities
- `payer_contracts` - Time-bound contracts
- `notifications` - System notifications
- `evv_visits` - EVV visit records
- `claims` - Claim records
- `generated_claims` - Generated 837P files
