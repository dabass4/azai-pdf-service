# Incomplete Features & Implementation Plan

## Current Status After Review

### ✅ COMPLETE & WORKING
1. **Authentication System** - JWT-based signup/login/logout
2. **Multi-Tenancy** - Complete data isolation between organizations
3. **Timesheet Scanning** - PDF/Image upload, OCR extraction, auto-registration
4. **Patient Management** - Full CRUD with EVV compliance fields
5. **Employee Management** - Full CRUD with DCW fields
6. **Payer Management** - Insurance contracts with multi-tenancy
7. **Service Codes** - Configuration management
8. **Claims Management** - CRUD operations (submission is mocked)
9. **Search & Filter** - Working across patients, employees, timesheets
10. **Bulk Operations** - Select all, bulk update, bulk delete
11. **CSV Export** - Working for timesheets
12. **Stripe Integration** - Checkout sessions, webhook handling, plan management
13. **EVV System** - Complete Ohio Medicaid EVV compliance
14. **EVV Export** - Individual, DCW, Visit records in Ohio format
15. **EVV Submission** - Mock aggregator for testing

### ⚠️ MOCKED/PLACEHOLDER (Need Real Implementation or Documentation)

#### 1. **Sandata API Submission** (Lines 1008-1055 in server.py)
- **Status**: MOCKED - Logs data but doesn't actually submit
- **Current**: Mock implementation that just logs payload
- **Needed**: Either implement real Sandata API integration OR document that it's intentionally mocked for testing
- **Decision**: Keep mocked with clear documentation (requires real Sandata credentials)

#### 2. **Medicaid Claims Submission** (Lines 2226-2265 in server.py)
- **Status**: MOCKED - Updates status but doesn't submit to real endpoint
- **Current**: Mock submission that logs claim data and sets status to "submitted"
- **Needed**: Real Ohio Medicaid claims submission endpoint integration
- **Decision**: Keep mocked with clear documentation (requires real Medicaid portal credentials)

### 🚧 MISSING FEATURES (Need Implementation)

#### 1. **ODM Export Format**
- **Status**: NOT IMPLEMENTED
- **Current**: Only CSV export exists
- **Needed**: Implement ODM (Ohio Department of Medicaid) export format
- **Priority**: MEDIUM (mentioned in requirements but not critical)
- **Files to Create**: Add ODM export functionality to backend

#### 2. **Landing Page UI**
- **Status**: EXISTS BUT BASIC
- **Current**: Login page shows instead of landing page for non-authenticated users
- **Needed**: Public landing page with pricing tiers, features, CTA buttons
- **Priority**: HIGH (important for SaaS marketing)
- **Files**: /app/frontend/src/pages/LandingPage.js exists but routing shows Login page

#### 3. **Bulk Medicaid Claims Submission**
- **Status**: BUTTON EXISTS, NO BACKEND
- **Current**: UI has bulk action toolbar but no "Submit Claims" action
- **Needed**: Bulk submit multiple claims at once
- **Priority**: MEDIUM (useful feature but claims submission is mocked anyway)

#### 4. **Stripe Webhook Testing in Production**
- **Status**: IMPLEMENTED BUT NOT TESTED IN PROD
- **Current**: Webhook endpoint exists and handles events
- **Needed**: Test with real Stripe webhooks in production environment
- **Priority**: HIGH (needed for subscription management)

#### 5. **Multi-Step Form for Employees**
- **Status**: IMPLEMENTED FOR PATIENTS ONLY
- **Current**: Patients have multi-step wizard, employees use standard form
- **Needed**: Apply same multi-step wizard to employee creation
- **Priority**: LOW (nice to have for consistency)

### 📋 IMPLEMENTATION PRIORITY

**HIGH PRIORITY (Do Today):**
1. Fix Landing Page routing - make it actually show for unauthenticated users
2. Document mocked APIs clearly in codebase
3. Add bulk claims submission UI and backend endpoint
4. Add ODM export format

**MEDIUM PRIORITY (Can do later):**
1. Refine landing page design with pricing tiers
2. Multi-step form for employees
3. Additional export formats

**LOW PRIORITY (Document only):**
1. Real Sandata API integration (requires credentials)
2. Real Medicaid portal integration (requires credentials)

## Implementation Plan for Today

### Task 1: Fix Landing Page Routing ✅
- Make landing page show for unauthenticated users
- Add proper routing logic in App.js

### Task 2: Add ODM Export Format
- Research ODM format specifications
- Implement backend endpoint for ODM export
- Add frontend button/option for ODM export

### Task 3: Add Bulk Claims Submission
- Add backend endpoint for bulk claims submission
- Add frontend bulk action button
- Connect to mocked submission endpoint

### Task 4: Document Mocked APIs
- Add clear comments in code about mocked functionality
- Document what's needed for real implementation
- Update README with integration requirements
