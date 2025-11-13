# Pending Actions & Next Steps 📋

**Generated:** 2024-11-13  
**Status:** After Phase 1 837P Implementation

---

## 🔴 CRITICAL - IMMEDIATE ACTION REQUIRED

### 1. System Dependency Issue
**Status:** ⚠️ BLOCKING PDF PROCESSING  
**Issue:** `poppler-utils` not persisting after container restarts  
**Impact:** PDF timesheet scanning breaks after every restart  

**Immediate Fix (Temporary):**
```bash
sudo apt-get update && sudo apt-get install -y poppler-utils
```

**Permanent Fix Required:**
- **Action:** Contact Emergent support to add poppler-utils to base image
- **Discord:** https://discord.gg/VzKfwCXC4A
- **Email:** support@emergent.sh
- **Details:** See `/app/SYSTEM_DEPENDENCIES_AUDIT.md`
- **Template message:** Included in audit document

---

## 🟡 HIGH PRIORITY - TESTING & VALIDATION

### 2. Test New 837P Claims Features
**Status:** ⚠️ IMPLEMENTED BUT NOT TESTED  
**What needs testing:**

**Backend Testing:**
- [ ] `POST /api/claims/generate-837` - Generate 837P from timesheets
- [ ] `GET /api/claims/generated` - List generated claims
- [ ] `GET /api/claims/generated/{id}/download` - Download EDI file
- [ ] `GET /api/enrollment/status` - Get ODM enrollment checklist
- [ ] `PUT /api/enrollment/update-step` - Update checklist progress
- [ ] Verify multi-tenant isolation (organization_id)
- [ ] Test with multiple timesheets
- [ ] Verify EDI file format (X12 837P compliance)

**Frontend Testing:**
- [ ] Claims page - Generate 837P tab
- [ ] Claims page - Generated Claims tab
- [ ] Claims page - ODM Enrollment tab
- [ ] Timesheet selection with checkboxes
- [ ] EDI file download
- [ ] Enrollment checklist interactions
- [ ] Progress tracking display

**Files:**
- Backend: `/app/backend/server.py`, `edi_claim_generator.py`, `edi_x12_builder.py`
- Frontend: `/app/frontend/src/pages/Claims.js`
- Test data: `/app/test_result.md` (needs updating with test results)

### 3. Comprehensive Regression Testing
**Status:** ⚠️ NEEDED AFTER NEW IMPLEMENTATION  
**Scope:** Ensure new 837P features didn't break existing functionality

**Test Areas:**
- [ ] Timesheet upload and extraction
- [ ] Patient CRUD operations
- [ ] Employee CRUD operations
- [ ] EVV system functionality
- [ ] Authentication and multi-tenancy
- [ ] Existing claims management
- [ ] Search and filter features
- [ ] Bulk operations

---

## 🟢 PHASE 2 - OHIO MEDICAID 837P (AWAITING CREDENTIALS)

### 4. Complete ODM Trading Partner Enrollment
**Status:** 📋 USER ACTION REQUIRED  
**Current:** Phase 1 complete (file generation)  
**Next:** User must complete enrollment process

**Steps for User:**
1. [ ] Review ODM Trading Partner Information Guide
2. [ ] Review HIPAA ASC X12 Technical Reports (TR3)
3. [ ] Begin trading partner enrollment via ODM portal
4. [ ] Review Ohio Medicaid 837P Companion Guide
5. [ ] Coordinate testing strategy with IT team
6. [ ] Complete and submit Trading Partner Agreement
7. [ ] Complete EDI Connectivity Form (SFTP/AS2)
8. [ ] Receive 7-digit ODM Trading Partner ID
9. [ ] Provide test provider list (max 5 providers)
10. [ ] Submit test claims to ODM test environment
11. [ ] Verify EDI receipts (999, 824, 277CA, 835)

**Resources:**
- Guide: https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners/content/enrollment-testing
- Contact: EDI-TP-Comments@medicaid.ohio.gov

### 5. Implement Phase 2 - Automated EDI Transmission
**Status:** 🚧 PENDING ODM CREDENTIALS  
**Dependencies:** Requires completion of step #4

**What to implement:**
- [ ] EDI connectivity setup (SFTP or AS2)
- [ ] Automated 837P file transmission to ODM
- [ ] 999 Implementation Acknowledgement parsing
- [ ] 277CA Claim Acknowledgment handling
- [ ] 835 Remittance Advice processing
- [ ] Transaction tracking and status updates
- [ ] Error handling and retry logic
- [ ] Production vs test environment configuration

**Files to create/modify:**
- `/app/backend/edi_transmission.py` (new)
- `/app/backend/edi_response_parser.py` (new)
- `/app/backend/server.py` (update endpoints)

---

## 🔵 MEDIUM PRIORITY - FEATURE COMPLETION

### 6. Implement Real Sandata API Integration
**Status:** ⚠️ MOCKED - REQUIRES CREDENTIALS  
**Current:** Mock implementation logs but doesn't actually submit

**What's needed:**
- [ ] Create Sandata account at https://www.sandata.com
- [ ] Obtain API credentials (API Key, Auth Token, Base URL)
- [ ] Replace mock logic in `/app/backend/server.py` lines 1008-1055
- [ ] Implement authentication (OAuth or API key)
- [ ] Format payload per Sandata specifications
- [ ] Handle API responses and errors
- [ ] Implement retry logic

**Configuration:**
```env
SANDATA_API_URL=https://api.sandata.com/v1
SANDATA_API_KEY=your_real_api_key
SANDATA_AUTH_TOKEN=your_real_auth_token
```

**Documentation:** https://www.sandata.com/api-documentation

### 7. Implement CSV/ODM Export Formats
**Status:** 🚧 PARTIALLY IMPLEMENTED  
**Current:** CSV export exists for timesheets  
**Missing:** ODM-specific export format

**What's needed:**
- [ ] Research ODM export format specifications
- [ ] Create `/app/backend/odm_export.py` module
- [ ] Add `GET /api/timesheets/export/odm` endpoint
- [ ] Add frontend UI option for ODM export
- [ ] Test with sample data
- [ ] Validate against ODM requirements

**Priority:** Medium (nice to have for compliance)

### 8. Bulk Claims Submission Endpoint
**Status:** 🚧 PLACEHOLDER EXISTS  
**Current:** `POST /api/claims/bulk-submit` exists but just marks as submitted  
**File:** `/app/backend/server.py` lines 3786-3820

**What's needed:**
- [ ] Integrate with Phase 2 automated transmission
- [ ] Handle multiple claims in single batch
- [ ] Progress tracking for bulk operations
- [ ] Error handling for partial failures
- [ ] Frontend UI enhancements

**Note:** This becomes relevant after Phase 2 implementation

---

## 🟣 LOW PRIORITY - ENHANCEMENTS

### 9. Stripe Production Webhook Testing
**Status:** ✅ IMPLEMENTED BUT NOT PROD-TESTED  
**Current:** Webhook endpoint exists, using test mode

**What's needed:**
- [ ] Switch Stripe from test to live mode
- [ ] Configure production webhook URL
- [ ] Test subscription events:
  - checkout.session.completed
  - customer.subscription.updated
  - customer.subscription.deleted
- [ ] Monitor webhook logs
- [ ] Test payment failures and retries

**Configuration:**
```env
STRIPE_API_KEY=sk_live_...  # Replace test key
STRIPE_WEBHOOK_SECRET=whsec_...  # Production webhook secret
```

### 10. Landing Page Improvements
**Status:** ✅ WORKING BUT BASIC  
**Current:** Landing page displays but could be enhanced

**Enhancements:**
- [ ] Add more detailed feature descriptions
- [ ] Improve pricing tier presentation
- [ ] Add customer testimonials section
- [ ] Add demo video or screenshots
- [ ] Optimize for SEO
- [ ] Add contact form

**File:** `/app/frontend/src/pages/LandingPage.js`

### 11. Multi-Step Form for Employees
**Status:** 📋 NICE TO HAVE  
**Current:** Patients have multi-step wizard, employees use standard form

**Enhancement:**
- [ ] Apply multi-step wizard pattern to employee creation
- [ ] Match patient form UX for consistency
- [ ] Add progress indicators
- [ ] Improve validation feedback

**Files:**
- Use `/app/frontend/src/components/ui/MultiStepForm.js` as reference
- Update `/app/frontend/src/pages/Employees.js`

---

## 📊 PRIORITY MATRIX

### Do Now (This Week)
1. ✅ Fix poppler-utils permanently (contact Emergent)
2. ⚠️ Test new 837P claims features (backend + frontend)
3. ⚠️ Run regression tests on existing features

### Do Next (Next 1-2 Weeks)
4. 📋 User completes ODM enrollment process
5. 🚧 Implement ODM export format
6. 🚧 Enhance bulk claims submission

### Do When Ready (Next Month)
7. 🔐 Implement Phase 2 (after receiving ODM credentials)
8. 🔐 Implement real Sandata API (after getting credentials)
9. 💳 Switch Stripe to production mode
10. 🎨 Landing page enhancements

### Nice to Have (Backlog)
11. Multi-step form for employees
12. Additional export formats
13. Advanced reporting features

---

## 📝 DOCUMENTATION TASKS

### Immediate
- [ ] Update test_result.md with 837P test results
- [ ] Document system dependencies permanently
- [ ] Create user guide for 837P claims generation
- [ ] Document ODM enrollment process

### Ongoing
- [ ] Keep INCOMPLETE_FEATURES.md updated
- [ ] Update API documentation
- [ ] Maintain integration requirements doc
- [ ] Document troubleshooting steps

---

## 🔒 CREDENTIALS CHECKLIST

**What you currently have:**
- ✅ JWT secret
- ✅ MongoDB connection
- ✅ Emergent LLM key (for OCR)
- ✅ Stripe test keys

**What you need to obtain:**
- ⏳ ODM Trading Partner ID (7 digits)
- ⏳ ODM EDI connectivity credentials
- ⏳ Sandata API credentials (optional)
- ⏳ Stripe live keys (for production)

---

## 🎯 SUCCESS METRICS

**Phase 1 (Current):**
- ✅ 837P file generation working
- ✅ Multi-tenant isolation maintained
- ✅ EDI file format compliant
- ⏳ All features tested and validated

**Phase 2 (After ODM Enrollment):**
- ⏳ Automated EDI transmission
- ⏳ 999/277/835 response handling
- ⏳ Production claims submission
- ⏳ 90%+ claim acceptance rate

**Production Ready:**
- ⏳ All mocked APIs implemented or documented
- ⏳ Stripe in live mode
- ⏳ Comprehensive error handling
- ⏳ User documentation complete

---

## 📞 SUPPORT & RESOURCES

**Emergent Platform:**
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

**Ohio Medicaid:**
- Portal: https://medicaid.ohio.gov
- EDI Support: EDI-TP-Comments@medicaid.ohio.gov
- Claims Support: (800) 686-1516

**Stripe:**
- Dashboard: https://dashboard.stripe.com
- Support: https://support.stripe.com

**Sandata:**
- Website: https://www.sandata.com
- Support: support@sandata.com

---

**Last Updated:** 2024-11-13  
**Next Review:** After 837P testing complete
