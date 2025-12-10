# Sandata Testing Requirements - Complete Checklist

**Last Updated:** December 10, 2025  
**Application:** AZAI Healthcare Timesheet System

---

## 🎯 Executive Summary

Your AZAI application has **mock Sandata integration** built-in. To complete full Sandata testing and move to production, you'll need real credentials and complete profile data. This document outlines everything needed.

---

## 📋 CURRENT STATUS

### What's Already Implemented ✅

1. **Mock Sandata API Integration**
   - Location: `/app/backend/evv_sandata_client.py`
   - Mock submission service: `/app/backend/evv_submission.py`
   - Full EVV (Electronic Visit Verification) data models

2. **Profile Management System**
   - Patient profile creation & management
   - Employee profile creation & management
   - Auto-creation from PDF timesheet uploads
   - `is_complete` flag to track profile completeness

3. **Submission Blocking Logic**
   - System blocks Sandata submissions if profiles are incomplete
   - Clear error messages guide users to complete profiles
   - Bulk operations to mark profiles as complete

4. **Frontend UI**
   - Patient management page
   - Employee management page
   - Profile completion status indicators
   - Bulk profile completion actions

### What's Currently Mocked 🟡

- **Sandata API calls** - Using mock endpoints
- **Credentials** - Using placeholder values in `.env`:
  ```
  SANDATA_API_URL=https://api.sandata.com/v1
  SANDATA_API_KEY=mock_api_key_replace_later
  SANDATA_AUTH_TOKEN=mock_auth_token_replace_later
  ```

---

## 🔑 REQUIREMENTS FOR REAL SANDATA TESTING

### 1. Sandata Account Credentials

**You Need:**

| Credential | Description | Where to Get It | Example Format |
|------------|-------------|-----------------|----------------|
| **Username** | Sandata portal username | Sandata account setup | `your-org@sandata.com` |
| **Password** | Sandata portal password | Sandata account setup | (secure password) |
| **Company ID** | Your organization's Sandata ID | Sandata onboarding | `OHIO-12345` |
| **API URL** | Sandata API endpoint | Sandata technical docs | `https://api.sandata.com/v1` or `https://sandbox.sandata.com/v1` |
| **Business Entity ID** | Your Medicaid business entity ID | Ohio Medicaid registration | `BE-OH-123456` |
| **Business Entity Medicaid ID** | Your Medicaid identifier | Ohio Medicaid registration | `1234567890` |

**How to Obtain:**

1. **Contact Sandata:**
   - Website: https://www.sandata.com/
   - Phone: Check their website for current contact
   - Request: "Ohio Medicaid EVV API Access"

2. **Complete Sandata Onboarding:**
   - Sign contract with Sandata
   - Complete technical integration questionnaire
   - Receive sandbox credentials for testing

3. **Get Ohio Medicaid Registration:**
   - Register with Ohio Department of Medicaid (ODM)
   - Obtain Business Entity ID and Medicaid Identifier
   - Link your Sandata account to ODM

**Estimated Timeline:** 2-4 weeks for full setup

---

### 2. Complete Patient Profiles

For Sandata submission, **each patient must have a complete profile** with the following fields:

#### ✅ Required Patient Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| **first_name** | String | Patient first name | `Jane` |
| **last_name** | String | Patient last name | `Smith` |
| **date_of_birth** | Date | DOB (YYYY-MM-DD) | `1985-03-15` |
| **medicaid_number** | String | Ohio Medicaid ID | `OH123456789` |
| **sex** | String | Male/Female/Other | `Female` |
| **phone** | String | Phone number | `(614) 555-1234` |
| **address_street** | String | Street address | `123 Main St` |
| **address_city** | String | City | `Columbus` |
| **address_state** | String | State (2 letters) | `OH` |
| **address_zip** | String | ZIP code | `43085` |
| **latitude** | Float | GPS latitude | `39.9612` |
| **longitude** | Float | GPS longitude | `-82.9988` |

#### 🔹 Optional But Recommended

- **email** - Patient email address
- **middle_name** - Patient middle name
- **ssn** - Social Security Number (encrypted)
- **responsible_party_name** - Guardian/responsible party
- **responsible_party_phone** - Guardian phone
- **primary_language** - Patient's primary language

#### How to Complete Patient Profiles:

**Option 1: Via Frontend (Recommended)**
1. Log in to AZAI at `/patients`
2. Find patients marked as "INCOMPLETE"
3. Click on a patient to edit
4. Fill in all required fields
5. Save - system will automatically set `is_complete: true`

**Option 2: Via API**
```bash
curl -X PUT "https://azai-claims.preview.emergentagent.com/api/patients/{patient_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1985-03-15",
    "medicaid_number": "OH123456789",
    "sex": "Female",
    "phone": "(614) 555-1234",
    "address_street": "123 Main St",
    "address_city": "Columbus",
    "address_state": "OH",
    "address_zip": "43085",
    "latitude": 39.9612,
    "longitude": -82.9988,
    "is_complete": true
  }'
```

**Option 3: Bulk Mark as Complete**
If you have the data elsewhere and just need to mark profiles complete:
```bash
POST /api/patients/bulk-update
{
  "ids": ["patient-id-1", "patient-id-2"],
  "updates": { "is_complete": true }
}
```

---

### 3. Complete Employee Profiles

For Sandata submission, **each employee (Direct Care Worker) must have a complete profile**:

#### ✅ Required Employee Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| **first_name** | String | Employee first name | `John` |
| **last_name** | String | Employee last name | `Doe` |
| **employee_id** | String | Internal employee ID | `EMP001` |
| **date_of_birth** | Date | DOB (YYYY-MM-DD) | `1990-05-20` |
| **ssn** | String | Social Security Number | `123-45-6789` |
| **phone** | String | Phone number | `(614) 555-5678` |
| **email** | String | Email address | `john.doe@provider.com` |
| **sex** | String | Male/Female/Other | `Male` |

#### 🔹 Optional But Recommended for EVV

- **npi** - National Provider Identifier
- **staff_pin** - PIN for EVV device/app
- **staff_position_code** - Position/role code
- **hire_date** - Employment start date
- **employment_status** - Active/Inactive/On Leave

#### How to Complete Employee Profiles:

**Option 1: Via Frontend (Recommended)**
1. Log in to AZAI at `/employees`
2. Find employees marked as "INCOMPLETE"
3. Click on an employee to edit
4. Fill in all required fields
5. Save - system will automatically set `is_complete: true`

**Option 2: Via API**
```bash
curl -X PUT "https://azai-claims.preview.emergentagent.com/api/employees/{employee_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "employee_id": "EMP001",
    "date_of_birth": "1990-05-20",
    "ssn": "123-45-6789",
    "phone": "(614) 555-5678",
    "email": "john.doe@provider.com",
    "sex": "Male",
    "is_complete": true
  }'
```

---

### 4. Service Code Configuration

Each timesheet must have a valid **service code** configured with Sandata/EVV requirements:

#### Service Code Components

**3-Part Combination Required:**

1. **Payer** - Who's paying
   - `ODM` - Ohio Department of Medicaid
   - `ODA` - Ohio Department of Aging

2. **Payer Program** - Which program
   - `SP` - State Plan
   - `OHCW` - Ohio Home Care Waiver
   - `MYCARE` - MyCare Ohio
   - `PASSPORT` - PASSPORT Program

3. **Procedure Code** - HCPCS code
   - `T1019` - Personal Care Services
   - `G0156` - Home Health Services
   - `S5150` - Respite Care
   - `S5165` - Homemaker Services

#### How to Configure Service Codes:

**Via Frontend:**
1. Go to `/service-codes` in AZAI
2. Create or edit service codes
3. Map internal codes to Sandata requirements
4. Set Payer + Program + Procedure Code

**Example Service Code:**
```json
{
  "service_name": "Personal Care - ODM State Plan",
  "service_code_internal": "PC-01",
  "payer": "ODM",
  "payer_program": "SP",
  "procedure_code": "T1019",
  "rate": 20.50,
  "units_per_hour": 4
}
```

---

## 🧪 TESTING WORKFLOW

### Phase 1: Profile Completion Testing (No Credentials Needed)

**Test the blocking logic:**

1. Upload a test PDF timesheet
2. System should auto-create incomplete patient/employee profiles
3. Try to submit to Sandata - should be **blocked** with message:
   - "Cannot submit: Patient profile incomplete"
   - OR "Cannot submit: Employee profile(s) incomplete"
4. Complete the patient profile via UI
5. Complete the employee profile(s) via UI
6. Verify profiles now show as "COMPLETE" (no yellow badges)

**Test Commands:**
```bash
# Check current incomplete profiles
curl "https://azai-claims.preview.emergentagent.com/api/patients?is_complete=false" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl "https://azai-claims.preview.emergentagent.com/api/employees?is_complete=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Phase 2: Mock Sandata Testing (No Real Credentials Needed)

**Current State: Mock Mode**

The system is currently in mock mode. When profiles are complete, submissions will:
1. ✅ Pass validation checks
2. ✅ Format data correctly
3. ✅ Log submission details
4. ✅ Return mock success response
5. ⚠️ Not actually send to Sandata (mocked)

**What You'll See:**
```json
{
  "status": "success",
  "sandata_id": "SND-A3F8B2C1",
  "message": "Timesheet submitted successfully (MOCKED)"
}
```

**Check Backend Logs:**
```bash
tail -f /var/log/supervisor/backend.out.log | grep SANDATA
```

You'll see:
```
[MOCK] Submitting to Sandata API: {...}
[MOCK] API URL: https://api.sandata.com/v1
[MOCK] Using API Key: mock_api_ke... (masked)
```

---

### Phase 3: Real Sandata Testing (Requires Credentials)

**Prerequisites:**
- ✅ Sandata sandbox credentials obtained
- ✅ All patient profiles complete
- ✅ All employee profiles complete
- ✅ Service codes configured

**Steps to Enable Real Integration:**

1. **Update Environment Variables**
   
   Edit `/app/backend/.env`:
   ```bash
   # Replace mock values with real credentials
   SANDATA_API_URL=https://sandbox.sandata.com/v1
   SANDATA_API_KEY=your_real_api_key_here
   SANDATA_AUTH_TOKEN=your_real_auth_token_here
   ```

2. **Update Sandata Client Configuration**
   
   Edit `/app/backend/evv_sandata_client.py` if needed to match Sandata's actual API format.

3. **Restart Backend**
   ```bash
   sudo supervisorctl restart backend
   ```

4. **Test Connection**
   ```bash
   # Create a test endpoint to verify connection
   curl "https://azai-claims.preview.emergentagent.com/api/sandata/test-connection" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

5. **Submit Test Timesheet**
   - Upload a real timesheet PDF
   - Complete all profiles
   - Submit to Sandata
   - Check for real transaction ID from Sandata

6. **Verify in Sandata Portal**
   - Log in to Sandata portal
   - Check for your submission
   - Verify data accuracy

---

## 🔄 TRANSITION FROM MOCK TO PRODUCTION

### Checklist Before Going Live

- [ ] **Sandata production credentials** obtained (not sandbox)
- [ ] **All patient profiles** have complete, accurate data
- [ ] **All employee profiles** have complete, accurate data
- [ ] **Service codes** mapped correctly to Sandata codes
- [ ] **GPS coordinates** added for patient addresses
- [ ] **Tested in Sandata sandbox** successfully
- [ ] **Sandata validation** - No rejections in sandbox
- [ ] **ODM Business Entity ID** confirmed and configured
- [ ] **Production API URL** updated in `.env`
- [ ] **Error handling** tested (what happens if Sandata is down?)
- [ ] **Logging and monitoring** in place

### Update `.env` for Production

```bash
# Production Sandata Configuration
SANDATA_API_URL=https://api.sandata.com/v1
SANDATA_API_KEY=prod_api_key_here
SANDATA_AUTH_TOKEN=prod_auth_token_here

# Remove mock indicators
# (Update code to remove "[MOCK]" log prefixes)
```

---

## 📊 MONITORING & VALIDATION

### Key Metrics to Track

1. **Profile Completeness Rate**
   - % of patients with complete profiles
   - % of employees with complete profiles

2. **Submission Success Rate**
   - Total submissions attempted
   - Successful vs. blocked submissions
   - Sandata API errors

3. **Data Quality**
   - Missing required fields
   - Invalid data formats
   - GPS coordinate accuracy

### Monitoring Commands

```bash
# Check incomplete patients
GET /api/patients?is_complete=false

# Check incomplete employees
GET /api/employees?is_complete=false

# Check submission history
GET /api/timesheets?sandata_status=submitted

# Check blocked submissions
GET /api/timesheets?sandata_status=blocked
```

---

## 🚨 COMMON ISSUES & SOLUTIONS

### Issue 1: "Patient profile incomplete"

**Cause:** Missing required fields in patient profile

**Solution:**
1. Go to `/patients` page
2. Find patient with "INCOMPLETE" badge
3. Click to edit
4. Fill in ALL required fields (see section 2 above)
5. Save

### Issue 2: "Employee profile(s) incomplete"

**Cause:** One or more employees on timesheet have incomplete profiles

**Solution:**
1. Go to `/employees` page
2. Filter by "Incomplete" status
3. Complete each employee profile
4. Return to timesheet and resubmit

### Issue 3: "Cannot connect to Sandata API"

**Cause:** Invalid credentials or API URL

**Solution:**
1. Verify credentials in `/app/backend/.env`
2. Check Sandata API documentation for correct URL
3. Test credentials in Sandata portal first
4. Check firewall/network settings

### Issue 4: "Missing GPS coordinates"

**Cause:** Patient address lacks latitude/longitude

**Solution:**
1. Use a geocoding service to get coordinates
2. Update patient profile with lat/long
3. Or use Google Maps to find coordinates manually

---

## 📞 SUPPORT CONTACTS

### Sandata Support
- **Website:** https://www.sandata.com/support
- **Documentation:** Request API docs during onboarding
- **Technical Support:** Available through your account manager

### Ohio Medicaid EVV Support
- **Website:** https://medicaid.ohio.gov/
- **EVV Program:** Contact ODM EVV team for registration
- **Provider Support:** Check ODM provider portal

---

## 📈 NEXT STEPS

### Immediate Actions (This Week):

1. **Complete Existing Profiles**
   - Review all patients marked "incomplete"
   - Review all employees marked "incomplete"
   - Fill in missing data

2. **Test Mock Workflow**
   - Upload test timesheet
   - Complete profiles
   - Verify submission (mock mode)

### Short Term (1-4 Weeks):

3. **Contact Sandata**
   - Request sandbox account
   - Schedule onboarding call
   - Get technical documentation

4. **Ohio Medicaid Registration**
   - Verify ODM registration status
   - Obtain Business Entity ID
   - Link to Sandata

### Medium Term (1-3 Months):

5. **Sandbox Testing**
   - Implement real API calls
   - Test with sandbox credentials
   - Validate data formats

6. **Production Go-Live**
   - Switch to production credentials
   - Monitor initial submissions
   - Handle any rejections

---

## 💡 TIPS FOR SUCCESS

1. **Start with Complete Data** - Don't upload timesheets until profiles are ready
2. **Use Bulk Operations** - Mark multiple profiles complete at once
3. **Validate Before Submit** - Check profile completeness before attempting Sandata submission
4. **Monitor Logs** - Watch backend logs for detailed error messages
5. **Keep Credentials Secure** - Never commit real API keys to git
6. **Test Incrementally** - Start with 1-2 timesheets, not hundreds
7. **Document Everything** - Track what works and what doesn't

---

## ✅ QUICK CHECKLIST

Use this checklist to track your progress:

**Setup:**
- [ ] Sandata account created
- [ ] Sandbox credentials received
- [ ] Production credentials received (when ready)
- [ ] Ohio Medicaid Business Entity ID obtained
- [ ] API documentation reviewed

**Data Preparation:**
- [ ] All patient profiles completed
- [ ] All employee profiles completed
- [ ] Service codes configured
- [ ] GPS coordinates added to addresses
- [ ] Medicaid numbers validated

**Technical Setup:**
- [ ] `.env` file updated with credentials
- [ ] Backend restarted after config changes
- [ ] Connection test passed
- [ ] Mock submission tested
- [ ] Real API submission tested (sandbox)

**Go-Live:**
- [ ] Production credentials configured
- [ ] Full end-to-end test passed
- [ ] Error monitoring in place
- [ ] Backup/rollback plan ready
- [ ] Team trained on new workflow

---

**Document Version:** 1.0  
**Last Updated:** December 10, 2025  
**Maintained By:** AZAI Development Team

**Questions?** Review the detailed sections above or contact your Sandata account manager.
