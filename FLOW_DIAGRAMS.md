# Healthcare Timesheet Scanner - Flow Diagrams

**Version:** 2.0  
**Last Updated:** November 2024

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [User Authentication Flow](#user-authentication-flow)
3. [Timesheet Processing Flow](#timesheet-processing-flow)
4. [Patient Management Flow](#patient-management-flow)
5. [Ohio Medicaid 837P Claims Flow](#ohio-medicaid-837p-claims-flow)
6. [EVV Submission Flow](#evv-submission-flow)
7. [Multi-Tenant Data Isolation](#multi-tenant-data-isolation)
8. [Payment & Subscription Flow](#payment--subscription-flow)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
│                      (React Frontend - Port 3000)                    │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Landing  │  │  Login   │  │Dashboard │  │ Settings │           │
│  │   Page   │  │  Signup  │  │          │  │          │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │Timesheets│  │ Patients │  │Employees │  │  Claims  │           │
│  │          │  │          │  │          │  │  (837P)  │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │  Payers  │  │   EVV    │  │ Service  │                         │
│  │          │  │Management│  │  Codes   │                         │
│  └──────────┘  └──────────┘  └──────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS/REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND API SERVER                             │
│                    (FastAPI - Python - Port 8001)                    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    API ENDPOINTS (/api)                     │    │
│  │                                                              │    │
│  │  /auth/*              - Authentication & JWT tokens         │    │
│  │  /timesheets/*        - Timesheet CRUD & processing         │    │
│  │  /patients/*          - Patient management                  │    │
│  │  /employees/*         - Employee management                 │    │
│  │  /claims/*            - 837P claim generation               │    │
│  │  /evv/*               - EVV exports & submission            │    │
│  │  /payments/*          - Stripe integration                  │    │
│  │                                                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    BUSINESS LOGIC                           │    │
│  │                                                              │    │
│  │  • JWT Authentication      • Multi-tenant Isolation         │    │
│  │  • PDF/Image Processing    • X12 EDI Generation             │    │
│  │  • OCR Data Extraction     • Time Unit Calculation          │    │
│  │  • EVV Data Formatting     • Claims Validation              │    │
│  │                                                              │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
            │                  │                    │
            │                  │                    │
            ▼                  ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   MongoDB       │  │  OpenAI Vision  │  │    Stripe       │
│   Database      │  │   API (OCR)     │  │   Payments      │
│                 │  │                 │  │                 │
│  Collections:   │  │  • Timesheet    │  │  • Checkout     │
│  • users        │  │    scanning     │  │  • Webhooks     │
│  • patients     │  │  • Data extract │  │  • Subscriptions│
│  • employees    │  │                 │  │                 │
│  • timesheets   │  └─────────────────┘  └─────────────────┘
│  • claims       │
│  • evv_visits   │  ┌─────────────────┐  ┌─────────────────┐
│  • organizations│  │ Ohio Medicaid   │  │   Sandata API   │
│                 │  │   EDI (SFTP)    │  │   (Mocked)      │
└─────────────────┘  │                 │  │                 │
                     │  • 837P Submit  │  │  • Payroll      │
                     │  • 999 Response │  │  • Billing      │
                     │  • 277CA Ack    │  │                 │
                     │  • 835 Remit    │  └─────────────────┘
                     │  (Phase 2)      │
                     └─────────────────┘
```

---

## User Authentication Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    NEW USER SIGNUP                            │
└──────────────────────────────────────────────────────────────┘

    User                Frontend              Backend              Database
     │                     │                     │                     │
     │  Visit Landing Page │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Click "Sign Up"    │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Fill Form:         │                     │                     │
     │  • Organization     │                     │                     │
     │  • Email            │                     │                     │
     │  • Password         │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Select Plan        │                     │                     │
     │  (Basic/Pro/Ent)    │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ POST /api/auth/signup                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Create Organization │
     │                     │                     ├────────────────────>│
     │                     │                     │ organization_id     │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │                     │ Hash Password       │
     │                     │                     │ (bcrypt)            │
     │                     │                     │                     │
     │                     │                     │ Create User         │
     │                     │                     ├────────────────────>│
     │                     │                     │ user_id             │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │ Stripe Checkout URL │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Redirect to Stripe │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
     
    ┌─────────────────────────────────────────────────────────┐
    │               Stripe Payment Portal                      │
    └─────────────────────────────────────────────────────────┘
     │                     │                     │                     │
     │  Complete Payment   │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │                Webhook Event               │
     │                     │                     │<────────────────────┤
     │                     │                     │ checkout.session    │
     │                     │                     │ .completed          │
     │                     │                     │                     │
     │                     │                     │ Update User         │
     │                     │                     │ subscription_plan   │
     │                     │                     ├────────────────────>│
     │                     │                     │                     │
     │  Redirect to App    │                     │                     │
     │<────────────────────┴─────────────────────┤                     │
     │                     │                     │                     │
     │  Login Automatically│                     │                     │
     │  with JWT Token     │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │


┌──────────────────────────────────────────────────────────────┐
│                    EXISTING USER LOGIN                        │
└──────────────────────────────────────────────────────────────┘

    User                Frontend              Backend              Database
     │                     │                     │                     │
     │  Visit App          │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Click "Sign In"    │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Enter Credentials  │                     │                     │
     │  • Email            │                     │                     │
     │  • Password         │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ POST /api/auth/login│                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Find User by Email  │
     │                     │                     ├────────────────────>│
     │                     │                     │ User record         │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │                     │ Verify Password     │
     │                     │                     │ (bcrypt compare)    │
     │                     │                     │                     │
     │                     │                     │ ✓ Valid             │
     │                     │                     │                     │
     │                     │                     │ Generate JWT Token  │
     │                     │                     │ Payload:            │
     │                     │                     │ • user_id           │
     │                     │                     │ • organization_id   │
     │                     │                     │ • email             │
     │                     │                     │ Expiry: 7 days      │
     │                     │                     │                     │
     │                     │ JWT Token           │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Store Token        │                     │                     │
     │  (localStorage)     │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
     │  Redirect to        │                     │                     │
     │  Dashboard          │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │


┌──────────────────────────────────────────────────────────────┐
│              AUTHENTICATED API REQUESTS                       │
└──────────────────────────────────────────────────────────────┘

    User                Frontend              Backend              Database
     │                     │                     │                     │
     │  Any Action         │                     │                     │
     │  (e.g., View        │                     │                     │
     │   Patients)         │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ GET /api/patients   │                     │
     │                     │ Header:             │                     │
     │                     │ Authorization:      │                     │
     │                     │ Bearer <JWT_TOKEN>  │                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Verify JWT Token    │
     │                     │                     │ • Signature valid?  │
     │                     │                     │ • Not expired?      │
     │                     │                     │                     │
     │                     │                     │ Extract Payload:    │
     │                     │                     │ • organization_id   │
     │                     │                     │                     │
     │                     │                     │ Query Database      │
     │                     │                     │ WHERE org_id =      │
     │                     │                     │ <from_token>        │
     │                     │                     ├────────────────────>│
     │                     │                     │ Patients (filtered) │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │ Patient Data        │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Display Patients   │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
```

---

## Timesheet Processing Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     TIMESHEET UPLOAD & PROCESSING                     │
└──────────────────────────────────────────────────────────────────────┘

    User                Frontend         Backend              OpenAI         Database
     │                     │                 │                   │              │
     │  Click "Upload      │                 │                   │              │
     │  Timesheet"         │                 │                   │              │
     ├────────────────────>│                 │                   │              │
     │                     │                 │                   │              │
     │  Select PDF/Image   │                 │                   │              │
     │  File               │                 │                   │              │
     ├────────────────────>│                 │                   │              │
     │                     │                 │                   │              │
     │                     │ POST            │                   │              │
     │                     │ /api/timesheets │                   │              │
     │                     │ (multipart)     │                   │              │
     │                     ├────────────────>│                   │              │
     │                     │                 │                   │              │
     │                     │                 │ Save File         │              │
     │                     │                 │ /tmp/upload.pdf   │              │
     │                     │                 │                   │              │
     │                     │                 │ Is PDF?           │              │
     │                     │                 │ ├─Yes─> Convert   │              │
     │                     │                 │ │       to Images │              │
     │                     │                 │ │       (poppler) │              │
     │                     │                 │ │                 │              │
     │                     │                 │ └─No──> Use Image │              │
     │                     │                 │         directly  │              │
     │                     │                 │                   │              │
     │                     │                 │ Vision API Call   │              │
     │                     │                 │ Prompt:           │              │
     │                     │                 │ "Extract timesheet│              │
     │                     │                 │  data..."         │              │
     │                     │                 ├──────────────────>│              │
     │                     │                 │                   │              │
     │                     │                 │                   │ Analyze Image│
     │                     │                 │                   │ OCR + NLP    │
     │                     │                 │                   │              │
     │                     │                 │ Extracted JSON    │              │
     │                     │                 │<──────────────────┤              │
     │                     │                 │ {                 │              │
     │                     │                 │   "week_of": "...",              │
     │                     │                 │   "entries": [    │              │
     │                     │                 │     {             │              │
     │                     │                 │       "date": "..." │            │
     │                     │                 │       "employee":".."            │
     │                     │                 │       "time_in": "..."           │
     │                     │                 │       "time_out": "..."          │
     │                     │                 │       "service_code":"..."       │
     │                     │                 │     }             │              │
     │                     │                 │   ]               │              │
     │                     │                 │ }                 │              │
     │                     │                 │                   │              │
     │                     │                 │ Process Data:     │              │
     │                     │                 │ • Normalize dates │              │
     │                     │                 │   (MM/DD/YYYY)    │              │
     │                     │                 │ • Normalize times │              │
     │                     │                 │   (00:00 AM/PM)   │              │
     │                     │                 │ • Calculate units │              │
     │                     │                 │   (15 min each)   │              │
     │                     │                 │ • Apply rounding  │              │
     │                     │                 │   (>=35min = 3u)  │              │
     │                     │                 │                   │              │
     │                     │                 │ Match Patient     │              │
     │                     │                 │ by name           │              │
     │                     │                 ├──────────────────────────────────>│
     │                     │                 │ Patient found?    │              │
     │                     │                 │<──────────────────────────────────┤
     │                     │                 │                   │              │
     │                     │                 │ ├─Yes─> Link     │              │
     │                     │                 │ │                 │              │
     │                     │                 │ └─No──> Create    │              │
     │                     │                 │         incomplete│              │
     │                     │                 │         profile   │              │
     │                     │                 │                   │              │
     │                     │                 │ Match Employee    │              │
     │                     │                 │ by name           │              │
     │                     │                 ├──────────────────────────────────>│
     │                     │                 │ Employee found?   │              │
     │                     │                 │<──────────────────────────────────┤
     │                     │                 │                   │              │
     │                     │                 │ ├─Yes─> Link     │              │
     │                     │                 │ │                 │              │
     │                     │                 │ └─No──> Create    │              │
     │                     │                 │         incomplete│              │
     │                     │                 │         profile   │              │
     │                     │                 │                   │              │
     │                     │                 │ Create Timesheet  │              │
     │                     │                 │ Record            │              │
     │                     │                 ├──────────────────────────────────>│
     │                     │                 │ timesheet_id      │              │
     │                     │                 │<──────────────────────────────────┤
     │                     │                 │                   │              │
     │                     │ Success         │                   │              │
     │                     │ + Extracted Data│                   │              │
     │                     │<────────────────┤                   │              │
     │                     │                 │                   │              │
     │  View Extracted     │                 │                   │              │
     │  Data               │                 │                   │              │
     │<────────────────────┤                 │                   │              │
     │                     │                 │                   │              │
     │  Review & Edit      │                 │                   │              │
     │  if needed          │                 │                   │              │
     │                     │                 │                   │              │
     │  Click "Save" or    │                 │                   │              │
     │  "Submit"           │                 │                   │              │
     ├────────────────────>│                 │                   │              │
     │                     │                 │                   │              │
     │                     │ PUT             │                   │              │
     │                     │ /api/timesheets │                   │              │
     │                     │ /{id}           │                   │              │
     │                     ├────────────────>│                   │              │
     │                     │                 │                   │              │
     │                     │                 │ Update Timesheet  │              │
     │                     │                 │ status="completed"│              │
     │                     │                 ├──────────────────────────────────>│
     │                     │                 │                   │              │
     │                     │ Success         │                   │              │
     │                     │<────────────────┤                   │              │
     │                     │                 │                   │              │
     │  Confirmation       │                 │                   │              │
     │<────────────────────┤                 │                   │              │
     │                     │                 │                   │              │
```

---

## Patient Management Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    ADD NEW PATIENT                            │
└──────────────────────────────────────────────────────────────┘

    User                Frontend              Backend              Database
     │                     │                     │                     │
     │  Click "Add Patient"│                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Multi-Step Wizard  │                     │                     │
     │  Opens              │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
     │  STEP 1: Basic Info │                     │                     │
     │  • First Name       │                     │                     │
     │  • Last Name        │                     │                     │
     │  • DOB              │                     │                     │
     │  • Gender           │                     │                     │
     │  • SSN (optional)   │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Click "Next"       │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  STEP 2: Contact    │                     │                     │
     │  • Phone Numbers    │                     │                     │
     │  • Email            │                     │                     │
     │  • Address          │                     │                     │
     │  • City/State/ZIP   │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Click "Next"       │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  STEP 3: Medical    │                     │                     │
     │  • Medicaid Number  │                     │                     │
     │  • Medicare Number  │                     │                     │
     │  • Insurance        │                     │                     │
     │  • Diagnosis Codes  │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Click "Next"       │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  STEP 4: EVV Info   │                     │                     │
     │  • Patient Other ID │                     │                     │
     │  • PIMS ID          │                     │                     │
     │  • Timezone         │                     │                     │
     │  • Coordinates      │                     │                     │
     │  • Responsible Party│                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │  Click "Save"       │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ POST /api/patients  │                     │
     │                     │ + JWT Token         │                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Extract org_id      │
     │                     │                     │ from JWT            │
     │                     │                     │                     │
     │                     │                     │ Validate Data       │
     │                     │                     │ • Required fields   │
     │                     │                     │ • Format checks     │
     │                     │                     │ • Medicaid ID valid │
     │                     │                     │                     │
     │                     │                     │ Generate patient_id │
     │                     │                     │ (UUID)              │
     │                     │                     │                     │
     │                     │                     │ Save Patient        │
     │                     │                     │ WITH org_id         │
     │                     │                     ├────────────────────>│
     │                     │                     │ patient record      │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │ Patient Created     │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Success Message    │                     │                     │
     │  "Patient Added"    │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
     │  View Patients List │                     │                     │
     │  (auto-refresh)     │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │


┌──────────────────────────────────────────────────────────────┐
│              SEARCH & FILTER PATIENTS                         │
└──────────────────────────────────────────────────────────────┘

    User                Frontend              Backend              Database
     │                     │                     │                     │
     │  Navigate to        │                     │                     │
     │  Patients Page      │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ GET /api/patients   │                     │
     │                     │ + JWT Token         │                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Query:              │
     │                     │                     │ WHERE org_id =      │
     │                     │                     │ <from_jwt>          │
     │                     │                     ├────────────────────>│
     │                     │                     │ All patients        │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │ Patient List        │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Display Patients   │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
     │  Type in Search:    │                     │                     │
     │  "John"             │                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ GET /api/patients   │                     │
     │                     │ ?search=John        │                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Query:              │
     │                     │                     │ WHERE org_id =      │
     │                     │                     │ <from_jwt>          │
     │                     │                     │ AND (first_name     │
     │                     │                     │ LIKE "%John%" OR    │
     │                     │                     │ last_name LIKE      │
     │                     │                     │ "%John%")           │
     │                     │                     ├────────────────────>│
     │                     │                     │ Filtered patients   │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │ Filtered List       │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Display Results    │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
     │  Apply Filter:      │                     │                     │
     │  Status="Incomplete"│                     │                     │
     ├────────────────────>│                     │                     │
     │                     │                     │                     │
     │                     │ GET /api/patients   │                     │
     │                     │ ?search=John        │                     │
     │                     │ &status=incomplete  │                     │
     │                     ├────────────────────>│                     │
     │                     │                     │                     │
     │                     │                     │ Query with filters  │
     │                     │                     ├────────────────────>│
     │                     │                     │ Results             │
     │                     │                     │<────────────────────┤
     │                     │                     │                     │
     │                     │ Refined List        │                     │
     │                     │<────────────────────┤                     │
     │                     │                     │                     │
     │  Display Refined    │                     │                     │
     │  Results            │                     │                     │
     │<────────────────────┤                     │                     │
     │                     │                     │                     │
```

---

## Ohio Medicaid 837P Claims Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│              GENERATE 837P CLAIM FROM TIMESHEETS                          │
└──────────────────────────────────────────────────────────────────────────┘

    User             Frontend           Backend           EDI Generator      Database
     │                  │                  │                    │                │
     │  Navigate to     │                  │                    │                │
     │  Claims Page     │                  │                    │                │
     ├─────────────────>│                  │                    │                │
     │                  │                  │                    │                │
     │  Tab: "Generate  │                  │                    │                │
     │  837P"           │                  │                    │                │
     ├─────────────────>│                  │                    │                │
     │                  │                  │                    │                │
     │                  │ GET /api/timesheets                   │                │
     │                  ├─────────────────>│                    │                │
     │                  │                  │                    │                │
     │                  │                  │ Query WHERE org_id │                │
     │                  │                  ├───────────────────────────────────>│
     │                  │                  │ Timesheets         │                │
     │                  │                  │<───────────────────────────────────┤
     │                  │                  │                    │                │
     │                  │ Timesheet List   │                    │                │
     │                  │<─────────────────┤                    │                │
     │                  │                  │                    │                │
     │  View Timesheets │                  │                    │                │
     │<─────────────────┤                  │                    │                │
     │                  │                  │                    │                │
     │  Select Multiple │                  │                    │                │
     │  Timesheets      │                  │                    │                │
     │  ☑ Timesheet 1   │                  │                    │                │
     │  ☑ Timesheet 2   │                  │                    │                │
     │  ☑ Timesheet 3   │                  │                    │                │
     ├─────────────────>│                  │                    │                │
     │                  │                  │                    │                │
     │  Click "Generate │                  │                    │                │
     │  837P File"      │                  │                    │                │
     ├─────────────────>│                  │                    │                │
     │                  │                  │                    │                │
     │                  │ POST /api/claims/generate-837         │                │
     │                  │ {timesheet_ids: [...]}                │                │
     │                  ├─────────────────>│                    │                │
     │                  │                  │                    │                │
     │                  │                  │ Fetch Timesheets   │                │
     │                  │                  ├───────────────────────────────────>│
     │                  │                  │ Timesheet data     │                │
     │                  │                  │<───────────────────────────────────┤
     │                  │                  │                    │                │
     │                  │                  │ Fetch Patient Info │                │
     │                  │                  ├───────────────────────────────────>│
     │                  │                  │ Patient data       │                │
     │                  │                  │<───────────────────────────────────┤
     │                  │                  │                    │                │
     │                  │                  │ Fetch Employee NPI │                │
     │                  │                  ├───────────────────────────────────>│
     │                  │                  │ Employee data      │                │
     │                  │                  │<───────────────────────────────────┤
     │                  │                  │                    │                │
     │                  │                  │ Build Claim Data   │                │
     │                  │                  │ Structure:         │                │
     │                  │                  │ • claim_id         │                │
     │                  │                  │ • patient info     │                │
     │                  │                  │ • provider info    │                │
     │                  │                  │ • service_lines[]  │                │
     │                  │                  │                    │                │
     │                  │                  │ Initialize Generator                │
     │                  │                  ├───────────────────>│                │
     │                  │                  │                    │                │
     │                  │                  │ Generate 837P File │                │
     │                  │                  │<───────────────────┤                │
     │                  │                  │                    │                │
     │                  │                  │ ISA Segment        │                │
     │                  │                  │ ISA*00*...*ZZ*     │                │
     │                  │                  │ SENDER*ZZ*ODMITS*  │                │
     │                  │                  │ ...*^*00501*...T:~ │                │
     │                  │                  │                    │                │
     │                  │                  │ GS Segment         │                │
     │                  │                  │ GS*HC*SENDER*      │                │
     │                  │                  │ ODMITS*...*X*      │                │
     │                  │                  │ 005010X222A1~      │                │
     │                  │                  │                    │                │
     │                  │                  │ ST Segment         │                │
     │                  │                  │ ST*837*0001*       │                │
     │                  │                  │ 005010X222A1~      │                │
     │                  │                  │                    │                │
     │                  │                  │ BHT Segment        │                │
     │                  │                  │ BHT*0019*00*...~   │                │
     │                  │                  │                    │                │
     │                  │                  │ NM1 Segments       │                │
     │                  │                  │ (Submitter,        │                │
     │                  │                  │  Receiver,         │                │
     │                  │                  │  Billing Provider, │                │
     │                  │                  │  Patient)          │                │
     │                  │                  │                    │                │
     │                  │                  │ CLM Segment        │                │
     │                  │                  │ (Claim Info)       │                │
     │                  │                  │                    │                │
     │                  │                  │ DTP Segments       │                │
     │                  │                  │ (Dates)            │                │
     │                  │                  │                    │                │
     │                  │                  │ HI Segment         │                │
     │                  │                  │ (Diagnosis Codes)  │                │
     │                  │                  │                    │                │
     │                  │                  │ SV1 Segments       │                │
     │                  │                  │ (Service Lines)    │                │
     │                  │                  │                    │                │
     │                  │                  │ SE, GE, IEA        │                │
     │                  │                  │ (Trailers)         │                │
     │                  │                  │                    │                │
     │                  │                  │ Complete EDI File  │                │
     │                  │                  │<───────────────────┤                │
     │                  │                  │                    │                │
     │                  │                  │ Save to Database   │                │
     │                  │                  ├───────────────────────────────────>│
     │                  │                  │ claim_id           │                │
     │                  │                  │<───────────────────────────────────┤
     │                  │                  │                    │                │
     │                  │ EDI File         │                    │                │
     │                  │ (download)       │                    │                │
     │                  │<─────────────────┤                    │                │
     │                  │                  │                    │                │
     │  File Downloaded │                  │                    │                │
     │  "837P_claim_... │                  │                    │                │
     │  .edi"           │                  │                    │                │
     │<─────────────────┤                  │                    │                │
     │                  │                  │                    │                │
     │  Success Toast:  │                  │                    │                │
     │  "837P claim     │                  │                    │                │
     │  generated!"     │                  │                    │                │
     │<─────────────────┤                  │                    │                │
     │                  │                  │                    │                │


┌──────────────────────────────────────────────────────────────────────────┐
│                   ODM ENROLLMENT TRACKING                                 │
└──────────────────────────────────────────────────────────────────────────┘

    User             Frontend           Backend                           Database
     │                  │                  │                                  │
     │  Tab: "ODM       │                  │                                  │
     │  Enrollment"     │                  │                                  │
     ├─────────────────>│                  │                                  │
     │                  │                  │                                  │
     │                  │ GET /api/enrollment/status                         │
     │                  ├─────────────────>│                                  │
     │                  │                  │                                  │
     │                  │                  │ Find enrollment record           │
     │                  │                  ├─────────────────────────────────>│
     │                  │                  │ Record exists?                   │
     │                  │                  │<─────────────────────────────────┤
     │                  │                  │                                  │
     │                  │                  │ ├─No──> Create default          │
     │                  │                  │ │        11-step checklist       │
     │                  │                  │ │                                │
     │                  │                  │ └─Yes─> Return existing          │
     │                  │                  │                                  │
     │                  │ Enrollment Data  │                                  │
     │                  │ • Status         │                                  │
     │                  │ • Trading ID     │                                  │
     │                  │ • Steps (11)     │                                  │
     │                  │ • Progress (X/11)│                                  │
     │                  │<─────────────────┤                                  │
     │                  │                  │                                  │
     │  View Checklist  │                  │                                  │
     │  Step 1: Review  │                  │                                  │
     │         Guide    │                  │                                  │
     │  Step 2: Review  │                  │                                  │
     │         TR3      │                  │                                  │
     │  ...             │                  │                                  │
     │  Step 11: Verify │                  │                                  │
     │          Receipts│                  │                                  │
     │<─────────────────┤                  │                                  │
     │                  │                  │                                  │
     │  Click "Mark     │                  │                                  │
     │  Complete" on    │                  │                                  │
     │  Step 1          │                  │                                  │
     ├─────────────────>│                  │                                  │
     │                  │                  │                                  │
     │                  │ PUT /api/enrollment/update-step                    │
     │                  │ {step_number: 1, completed: true}                  │
     │                  ├─────────────────>│                                  │
     │                  │                  │                                  │
     │                  │                  │ Update step in array             │
     │                  │                  │ steps[0].completed = true        │
     │                  │                  │ steps[0].completed_date = now    │
     │                  │                  ├─────────────────────────────────>│
     │                  │                  │ Updated                          │
     │                  │                  │<─────────────────────────────────┤
     │                  │                  │                                  │
     │                  │ Success          │                                  │
     │                  │<─────────────────┤                                  │
     │                  │                  │                                  │
     │  Update UI:      │                  │                                  │
     │  ☑ Step 1        │                  │                                  │
     │  Progress: 1/11  │                  │                                  │
     │<─────────────────┤                  │                                  │
     │                  │                  │                                  │
```

---

## EVV Submission Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    EVV DATA EXPORT & SUBMISSION                           │
└──────────────────────────────────────────────────────────────────────────┘

    User         Frontend        Backend         EVV Module      ODM Aggregator
     │              │                │                │                │
     │  Navigate to │                │                │                │
     │  EVV Mgmt    │                │                │                │
     ├─────────────>│                │                │                │
     │              │                │                │                │
     │  Click       │                │                │                │
     │  "Export     │                │                │                │
     │  Individuals"│                │                │                │
     ├─────────────>│                │                │                │
     │              │                │                │                │
     │              │ GET /api/evv/export/individuals  │                │
     │              ├───────────────>│                │                │
     │              │                │                │                │
     │              │                │ Fetch Patients │                │
     │              │                │ with EVV fields│                │
     │              │                ├───────────────>│                │
     │              │                │                │                │
     │              │                │ Build EVV JSON │                │
     │              │                │ per spec:      │                │
     │              │                │ • BusinessID   │                │
     │              │                │ • PatientID    │                │
     │              │                │ • Medicaid#    │                │
     │              │                │ • Address      │                │
     │              │                │ • Coordinates  │                │
     │              │                │ • Payer Info   │                │
     │              │                │<───────────────┤                │
     │              │                │                │                │
     │              │ JSON Data      │                │                │
     │              │<───────────────┤                │                │
     │              │                │                │                │
     │  View/Download                │                │                │
     │  JSON        │                │                │                │
     │<─────────────┤                │                │                │
     │              │                │                │                │
     │  Click       │                │                │                │
     │  "Submit to  │                │                │                │
     │  EVV"        │                │                │                │
     ├─────────────>│                │                │                │
     │              │                │                │                │
     │              │ POST /api/evv/submit/individuals │                │
     │              ├───────────────>│                │                │
     │              │                │                │                │
     │              │                │ Prepare Data   │                │
     │              │                │ for aggregator │                │
     │              │                │                │                │
     │              │                │ POST to EVV    │                │
     │              │                │ Aggregator     │                │
     │              │                ├───────────────────────────────>│
     │              │                │                │                │
     │              │                │                │ Validate Data  │
     │              │                │                │ • Required     │
     │              │                │                │   fields       │
     │              │                │                │ • Format check │
     │              │                │                │                │
     │              │                │                │ Store Visit    │
     │              │                │                │ Records        │
     │              │                │                │                │
     │              │                │ Transaction ID │                │
     │              │                │ & Acknowledgment               │
     │              │                │<───────────────────────────────┤
     │              │                │                │                │
     │              │                │ Save Transmission               │
     │              │                │ Record         │                │
     │              │                │                │                │
     │              │ Success        │                │                │
     │              │ {              │                │                │
     │              │   txn_id: "...",                │                │
     │              │   status: "accepted"            │                │
     │              │ }              │                │                │
     │              │<───────────────┤                │                │
     │              │                │                │                │
     │  Success     │                │                │                │
     │  Notification│                │                │                │
     │<─────────────┤                │                │                │
     │              │                │                │                │

Note: Currently using MOCK aggregator for testing.
      Real aggregator requires ODM EVV vendor certification.
```

---

## Multi-Tenant Data Isolation

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   MULTI-TENANT DATA ISOLATION                             │
└──────────────────────────────────────────────────────────────────────────┘

DATABASE STRUCTURE:

┌─────────────────────────────────────────────────────────────────────┐
│  ORGANIZATIONS                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  id: "org-1"                                                         │
│  name: "ABC Healthcare"                                              │
│  subscription_plan: "professional"                                   │
│  created_at: "2024-01-15"                                            │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ 1-to-many
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  USERS                                                               │
├─────────────────────────────────────────────────────────────────────┤
│  id: "user-1"                                                        │
│  organization_id: "org-1"  ◄── FOREIGN KEY                          │
│  email: "admin@abchealthcare.com"                                   │
│  password_hash: "..."                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  PATIENTS                                                            │
├─────────────────────────────────────────────────────────────────────┤
│  id: "patient-1"                                                     │
│  organization_id: "org-1"  ◄── ISOLATION KEY                        │
│  first_name: "John"                                                  │
│  last_name: "Doe"                                                    │
│  medicaid_number: "..."                                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  EMPLOYEES                                                           │
├─────────────────────────────────────────────────────────────────────┤
│  id: "employee-1"                                                    │
│  organization_id: "org-1"  ◄── ISOLATION KEY                        │
│  first_name: "Jane"                                                  │
│  last_name: "Smith"                                                  │
│  npi: "..."                                                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  TIMESHEETS                                                          │
├─────────────────────────────────────────────────────────────────────┤
│  id: "timesheet-1"                                                   │
│  organization_id: "org-1"  ◄── ISOLATION KEY                        │
│  patient_id: "patient-1"                                             │
│  employee_id: "employee-1"                                           │
│  extracted_data: {...}                                               │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  CLAIMS (837P)                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  id: "claim-1"                                                       │
│  organization_id: "org-1"  ◄── ISOLATION KEY                        │
│  patient_id: "patient-1"                                             │
│  edi_content: "ISA*..."                                              │
│  timesheet_ids: ["timesheet-1", ...]                                │
└─────────────────────────────────────────────────────────────────────┘


API REQUEST FLOW WITH ISOLATION:

┌─────────────────────────────────────────────────────────────────────┐
│  1. USER LOGIN                                                       │
│                                                                       │
│  POST /api/auth/login                                                │
│  {                                                                    │
│    "email": "admin@abchealthcare.com",                               │
│    "password": "..."                                                 │
│  }                                                                    │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Backend:                                                            │
│  • Find user by email                                                │
│  • Verify password                                                   │
│  • Get user.organization_id = "org-1"                                │
│  • Generate JWT with payload:                                        │
│    {                                                                  │
│      user_id: "user-1",                                              │
│      organization_id: "org-1",  ◄── EMBEDDED IN TOKEN                │
│      email: "admin@abchealthcare.com"                                │
│    }                                                                  │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Return: JWT Token                                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  2. PROTECTED API REQUEST                                            │
│                                                                       │
│  GET /api/patients                                                   │
│  Headers:                                                            │
│    Authorization: Bearer <JWT_TOKEN>                                 │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Backend Middleware:                                                 │
│  • Extract JWT from header                                           │
│  • Verify JWT signature                                              │
│  • Decode payload                                                    │
│  • Extract organization_id = "org-1"  ◄── FROM TOKEN                 │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Endpoint Handler:                                                   │
│  def get_patients(current_user):                                     │
│      org_id = current_user["organization_id"]                        │
│                                                                       │
│      # AUTOMATIC ISOLATION - NO ORG_ID LEAKAGE                       │
│      patients = db.patients.find({                                   │
│          "organization_id": org_id  ◄── FILTER BY ORG                │
│      })                                                               │
│                                                                       │
│      return patients                                                 │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  MongoDB Query:                                                      │
│  db.patients.find({                                                  │
│      "organization_id": "org-1"  ◄── ONLY THIS ORG'S DATA            │
│  })                                                                   │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Return: Patients for "org-1" ONLY                                   │
│  (Other orgs' patients are NEVER visible)                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  3. DATA CREATION WITH AUTOMATIC ORG ASSIGNMENT                      │
│                                                                       │
│  POST /api/patients                                                  │
│  Headers:                                                            │
│    Authorization: Bearer <JWT_TOKEN>                                 │
│  Body:                                                                │
│  {                                                                    │
│    "first_name": "John",                                             │
│    "last_name": "Doe",                                               │
│    "medicaid_number": "..."                                          │
│    // NO organization_id in request                                  │
│  }                                                                    │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Backend:                                                            │
│  def create_patient(data, current_user):                             │
│      org_id = current_user["organization_id"]                        │
│                                                                       │
│      # AUTOMATICALLY ASSIGN ORG_ID                                   │
│      patient = {                                                      │
│          "id": generate_uuid(),                                      │
│          "organization_id": org_id,  ◄── AUTO-ASSIGNED               │
│          "first_name": data.first_name,                              │
│          "last_name": data.last_name,                                │
│          ...                                                          │
│      }                                                                │
│                                                                       │
│      db.patients.insert_one(patient)                                 │
│      return patient                                                  │
│                                                                       │
│  ↓                                                                    │
│                                                                       │
│  Result: Patient created WITH organization_id                        │
│  User CANNOT create data for other organizations                     │
└─────────────────────────────────────────────────────────────────────┘

SECURITY GUARANTEES:

✓ Each JWT token contains organization_id
✓ All queries automatically filter by organization_id
✓ Users can ONLY see their organization's data
✓ Users can ONLY create data in their organization
✓ Cross-org access is IMPOSSIBLE
✓ No data leakage between organizations
```

---

## Payment & Subscription Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    STRIPE SUBSCRIPTION FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

    User          Frontend         Backend         Stripe         Database
     │               │                │               │                │
     │  Select Plan  │                │               │                │
     │  (Professional)                │               │                │
     ├──────────────>│                │               │                │
     │               │                │               │                │
     │               │ POST /api/payments/create-checkout                │
     │               │ {plan: "professional"}          │                │
     │               ├───────────────>│               │                │
     │               │                │               │                │
     │               │                │ Create Stripe │                │
     │               │                │ Checkout      │                │
     │               │                ├──────────────>│                │
     │               │                │               │                │
     │               │                │ Checkout URL  │                │
     │               │                │<──────────────┤                │
     │               │                │               │                │
     │               │ Redirect URL   │               │                │
     │               │<───────────────┤               │                │
     │               │                │               │                │
     │  Redirect to  │                │               │                │
     │  Stripe       │                │               │                │
     │<──────────────┤                │               │                │
     │               │                │               │                │
     
    ┌────────────────────────────────────────────────────────────┐
    │            Stripe Checkout Portal                           │
    │  • Enter payment details                                    │
    │  • Review subscription                                      │
    │  • Complete purchase                                        │
    └────────────────────────────────────────────────────────────┘
     │               │                │               │                │
     │  Payment      │                │               │                │
     │  Completed    │                │               │                │
     ├──────────────>│                │               │                │
     │               │                │               │                │
     │               │                │          Webhook Event          │
     │               │                │          (async)                │
     │               │                │<──────────────┤                │
     │               │                │               │                │
     │               │                │ POST /api/payments/webhook     │
     │               │                │ Event: checkout.session.completed
     │               │                │               │                │
     │               │                │ Verify        │                │
     │               │                │ Signature     │                │
     │               │                │               │                │
     │               │                │ Extract:      │                │
     │               │                │ • customer_id │                │
     │               │                │ • subscription_id               │
     │               │                │ • plan        │                │
     │               │                │               │                │
     │               │                │ Update User   │                │
     │               │                │ Record        │                │
     │               │                ├───────────────────────────────>│
     │               │                │ SET:          │                │
     │               │                │ subscription_plan="professional"│
     │               │                │ stripe_customer_id="..."        │
     │               │                │ subscription_status="active"    │
     │               │                │<───────────────────────────────┤
     │               │                │               │                │
     │               │                │ Return 200 OK │                │
     │               │                ├──────────────>│                │
     │               │                │               │                │
     │  Redirect     │                │               │                │
     │  to App       │                │               │                │
     │<──────────────┴────────────────┤               │                │
     │               │                │               │                │
     │  Access       │                │               │                │
     │  Professional │                │               │                │
     │  Features     │                │               │                │
     │<──────────────┤                │               │                │
     │               │                │               │                │


SUBSCRIPTION PLAN COMPARISON:

┌────────────────────────────────────────────────────────────────┐
│                       PLAN FEATURES                             │
├────────────────┬────────────────┬────────────────┬─────────────┤
│   Feature      │     Basic      │  Professional  │ Enterprise  │
├────────────────┼────────────────┼────────────────┼─────────────┤
│ Monthly Price  │     $49        │     $149       │   Custom    │
│ Timesheets/Mo  │      50        │      500       │  Unlimited  │
│ Users          │       1        │       5        │  Unlimited  │
│ 837P Claims    │       ✓        │       ✓        │      ✓      │
│ EVV Export     │       ✓        │       ✓        │      ✓      │
│ Priority       │       -        │       ✓        │      ✓      │
│ Support        │                │                │             │
│ Dedicated      │       -        │       -        │      ✓      │
│ Account Mgr    │                │                │             │
└────────────────┴────────────────┴────────────────┴─────────────┘
```

---

## Summary

This document provides comprehensive flow diagrams for:

1. **System Architecture** - Overview of all components
2. **Authentication** - Signup, login, and JWT handling
3. **Timesheet Processing** - Upload, OCR, data extraction
4. **Patient Management** - CRUD operations and search
5. **837P Claims** - EDI generation and ODM enrollment
6. **EVV Submission** - Export and aggregator submission
7. **Multi-Tenant Isolation** - Security and data separation
8. **Payments** - Stripe subscription workflow

All flows include:
- Step-by-step sequence
- Data flow between components
- Decision points and branching
- Error handling paths
- Multi-tenant security

---

**For More Information:**
- User Guide: `/app/USER_GUIDE.md`
- ODM Enrollment: `/app/ODM_ENROLLMENT_GUIDE.md`
- Pending Actions: `/app/PENDING_ACTIONS.md`

**Version:** 2.0  
**Last Updated:** November 2024
