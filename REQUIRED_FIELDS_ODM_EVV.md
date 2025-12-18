# Required Fields for ODM Claims & EVV Compliance

## Fields Required by BOTH ODM (837P Claims) and EVV (Sandata)

These fields are marked with asterisk (*) and are MANDATORY before saving.

---

## 👤 PATIENT/CLIENT FIELDS

### Required by BOTH ODM & EVV (*)

#### Basic Information:
```
* first_name             - Required for claims & EVV identification
* last_name              - Required for claims & EVV identification
* date_of_birth          - Required for claims (eligibility) & EVV (verification)
* sex                    - Required for claims & EVV demographics
* medicaid_number        - Required for claims billing & EVV member ID
```

#### Address Information:
```
* address_street         - Required for claims & EVV service location
* address_city           - Required for claims & EVV service location
* address_state          - Required for claims & EVV service location
* address_zip            - Required for claims & EVV service location
* address_latitude       - Required for EVV geofencing (must be populated)
* address_longitude      - Required for EVV geofencing (must be populated)
* timezone               - Required for EVV timestamp accuracy
```

#### Medical:
```
* icd10_code             - Required for claims diagnosis & EVV service justification
```

### Required by ODM ONLY (for complete claims):
```
- physician_name         - Rendering provider
- physician_npi          - Provider identification (10 digits)
- prior_auth_number      - Service authorization (if applicable to service type)
```

### Required by EVV ONLY:
```
- patient_other_id       - External system ID (optional but recommended)
- phone_numbers          - For visit confirmation calls
- responsible_party      - If patient is minor or has guardian
```

---

## 👷 STAFF/EMPLOYEE FIELDS

### Required by BOTH ODM & EVV (*)

#### Basic Information:
```
* first_name             - Required for claims rendering provider & EVV staff ID
* last_name              - Required for claims rendering provider & EVV staff ID
* date_of_birth          - Required for claims & EVV staff verification
* ssn                    - Required for claims (tax ID) & EVV staff authentication
* sex                    - Required for demographics
```

#### Contact Information:
```
* address_street         - Required for employee records & EVV registration
* address_city           - Required for employee records & EVV registration
* address_state          - Required for employee records & EVV registration
* address_zip            - Required for employee records & EVV registration
* phone                  - Required for contact & EVV telephony
```

#### Employment Information:
```
* hire_date              - Required for claims eligibility & EVV staff active dates
* job_title              - Required for claims service classification
* employment_status      - Must be "Active" for claims & EVV
* staff_pin              - Required for EVV telephony clock-in (9 digits)
```

### Required by ODM ONLY:
```
- license_number         - Professional license (if applicable)
- certifications         - Required certifications for service type
```

### Required by EVV ONLY:
```
- staff_other_id         - External system ID
- staff_position         - Position code (3 characters)
- sequence_id            - EVV sequence tracking
```

---

## 📋 VALIDATION RULES

### Patient Validation Rules:

1. **Name Fields:**
   - first_name: 1-50 characters, letters, spaces, hyphens only
   - last_name: 1-50 characters, letters, spaces, hyphens only

2. **Date of Birth:**
   - Format: YYYY-MM-DD
   - Must be valid date
   - Cannot be future date
   - For home health: Must be 18+ years (unless newborn services)

3. **Medicaid Number:**
   - Format: 12 digits (Ohio)
   - Leading zeros required
   - Example: 000123456789

4. **Address:**
   - street: Minimum 5 characters
   - city: Minimum 2 characters
   - state: 2-letter code (OH)
   - zip: 5 digits or 9 digits (XXXXX or XXXXX-XXXX)
   - latitude: -90 to 90
   - longitude: -180 to 180

5. **ICD-10 Code:**
   - Format: Letter + 2-7 alphanumeric (e.g., A00.0, M79.3)
   - Must be valid ICD-10 code

### Employee Validation Rules:

1. **Name Fields:**
   - first_name: 1-50 characters
   - last_name: 1-50 characters

2. **SSN:**
   - Format: XXX-XX-XXXX
   - Must be 9 digits with hyphens
   - Cannot be all zeros (000-00-0000)

3. **Date of Birth:**
   - Format: YYYY-MM-DD
   - Must be 18+ years old
   - Cannot be future date

4. **Phone:**
   - Format: (XXX) XXX-XXXX or XXX-XXX-XXXX
   - Must be 10 digits

5. **Hire Date:**
   - Format: YYYY-MM-DD
   - Cannot be before 1900-01-01
   - Cannot be future date

6. **Staff PIN (EVV):**
   - Exactly 9 digits
   - Numeric only
   - Unique per staff member

7. **Employment Status:**
   - Must be "Active" to submit claims
   - Options: Active, Inactive, Terminated

---

## 🔄 PROFILE COMPLETION WORKFLOW

### Patient Profile:
```
1. Basic info created (from timesheet or manual)
   └─ is_complete = False

2. User completes REQUIRED fields (marked with *)
   └─ All (*) fields validated

3. System validates:
   ✓ All required fields present
   ✓ All formats correct
   ✓ Geocoding address (lat/long)
   
4. Profile marked complete
   └─ is_complete = True
   └─ Can now submit claims & EVV visits
```

### Employee Profile:
```
1. Basic info created (from timesheet or manual)
   └─ is_complete = False

2. User completes REQUIRED fields (marked with *)
   └─ All (*) fields validated

3. System validates:
   ✓ All required fields present
   ✓ All formats correct
   ✓ SSN unique
   ✓ Staff PIN unique
   
4. Profile marked complete
   └─ is_complete = True
   └─ Can now submit claims & EVV visits
```

---

## ⚠️ BLOCKING LOGIC

### Cannot Submit Claims Without:
```
Patient:
  ✗ Missing any (*) marked field
  ✗ is_complete = False
  ✗ Invalid medicaid_number
  ✗ Invalid address
  ⚠ Prior auth may be required for specific services (check per service type)

Employee:
  ✗ Missing any (*) marked field
  ✗ is_complete = False
  ✗ Invalid SSN
  ✗ Employment status not "Active"
  ✗ Missing staff_pin
```

### Cannot Submit EVV Without:
```
Patient:
  ✗ Missing latitude/longitude
  ✗ Missing timezone
  ✗ is_complete = False

Employee:
  ✗ Missing staff_pin
  ✗ is_complete = False
  ✗ Invalid staff_pin format
```

---

## 🎯 IMPLEMENTATION CHECKLIST

### Backend Changes:
```
☐ Update PatientProfile model with required field validation
☐ Update EmployeeProfile model with required field validation
☐ Add validation function: validate_patient_complete()
☐ Add validation function: validate_employee_complete()
☐ Block save if required fields missing
☐ Block claim submission if profile incomplete
☐ Add clear error messages for missing fields
```

### Frontend Changes:
```
☐ Add asterisk (*) to required field labels
☐ Make required fields unable to be blank
☐ Add real-time validation on form fields
☐ Show completion status indicator
☐ Prevent save unless all (*) fields completed
☐ Display helpful error messages
☐ Add field-level validation messages
```

### Database:
```
☐ Ensure default values don't satisfy validation
☐ Add indexes on required fields
☐ Add completion status tracking
```

---

## 📊 COMPLETION STATUS INDICATOR

### Patient Profile Status:
```
Incomplete (Red):
  - Missing any (*) required field
  - Cannot submit claims or EVV
  
Partial (Yellow):
  - All (*) fields present
  - Missing optional ODM/EVV fields
  - Can submit claims with warnings
  
Complete (Green):
  - All required fields present
  - All optional recommended fields present
  - Ready for claims & EVV
```

### Employee Profile Status:
```
Incomplete (Red):
  - Missing any (*) required field
  - Cannot render services or submit EVV
  
Complete (Green):
  - All (*) fields present and valid
  - Ready for service delivery
```

---

## 🔍 FIELD LOOKUP REFERENCE

### Quick Reference: What Requires What?

| Field | ODM Claims | EVV | Both |
|-------|------------|-----|------|
| **PATIENT** |
| first_name | ✓ | ✓ | * |
| last_name | ✓ | ✓ | * |
| date_of_birth | ✓ | ✓ | * |
| sex | ✓ | ✓ | * |
| medicaid_number | ✓ | ✓ | * |
| address_street | ✓ | ✓ | * |
| address_city | ✓ | ✓ | * |
| address_state | ✓ | ✓ | * |
| address_zip | ✓ | ✓ | * |
| address_latitude | | ✓ | * |
| address_longitude | | ✓ | * |
| timezone | | ✓ | * |
| icd10_code | ✓ | ✓ | * |
| prior_auth_number | ✓ | | (service-specific) |
| physician_name | ✓ | | |
| physician_npi | ✓ | | |
| **EMPLOYEE** |
| first_name | ✓ | ✓ | * |
| last_name | ✓ | ✓ | * |
| date_of_birth | ✓ | ✓ | * |
| ssn | ✓ | ✓ | * |
| sex | ✓ | ✓ | * |
| address_street | ✓ | ✓ | * |
| address_city | ✓ | ✓ | * |
| address_state | ✓ | ✓ | * |
| address_zip | ✓ | ✓ | * |
| phone | ✓ | ✓ | * |
| hire_date | ✓ | ✓ | * |
| job_title | ✓ | ✓ | * |
| employment_status | ✓ | ✓ | * |
| staff_pin | | ✓ | * |

---

## 💡 USER MESSAGING

### On Save Attempt with Missing Fields:
```
"⚠️ Required Information Missing

The following fields marked with (*) are required by 
Ohio Medicaid and Electronic Visit Verification:

Patient:
  - Date of Birth *
  - Medicaid Number *
  - Address Latitude/Longitude *

Please complete all required fields to enable:
  ✓ Claims submission to ODM
  ✓ Electronic Visit Verification
  ✓ Service authorization

[Complete Profile] [Save Draft]"
```

### On Profile Completion:
```
"✅ Profile Complete!

This patient/employee profile is now complete and 
ready for:
  ✓ Ohio Medicaid claims submission
  ✓ Electronic Visit Verification
  ✓ Service delivery and billing

All required information has been validated."
```

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Purpose:** Define mandatory fields for ODM claims and EVV compliance
