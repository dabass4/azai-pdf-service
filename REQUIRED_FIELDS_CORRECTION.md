# Required Fields Correction - Prior Authorization

## ✅ Correction Applied

**Issue:** Prior Authorization Number was incorrectly marked as required field

**Correction:** Prior Authorization is **NOT** a universally required field

---

## 📋 Updated Patient Required Fields

### Total: 12 Required Fields (marked with *)

#### Basic Information (5 fields):
```
* First Name          - Required by ODM & EVV
* Last Name           - Required by ODM & EVV
* Date of Birth       - Required by ODM & EVV
* Sex                 - Required by ODM & EVV
* Medicaid Number     - Required by ODM & EVV
```

#### Address Information (7 fields):
```
* Street Address      - Required by ODM & EVV
* City                - Required by ODM & EVV
* State               - Required by ODM & EVV
* ZIP Code            - Required by ODM & EVV
* Latitude            - Required by EVV (geofencing)
* Longitude           - Required by EVV (geofencing)
* Timezone            - Required by EVV (timestamps)
```

#### Medical Information (1 field):
```
* ICD-10 Code         - Required by ODM & EVV (diagnosis)
```

---

## 📌 Prior Authorization Status

### When IS Prior Auth Required?

Prior authorization is **service-specific** and depends on:

1. **Service Type**: Some Medicaid services require prior auth, others don't
2. **State Rules**: Ohio Medicaid may require prior auth for specific HCPCS codes
3. **MCE Requirements**: Managed Care Entities may have their own prior auth rules
4. **Service Setting**: Home health vs facility services have different requirements

### Examples:

**Typically Requires Prior Auth:**
- Complex medical procedures
- DME (Durable Medical Equipment)
- Specialized therapies
- Some skilled nursing services

**Typically Does NOT Require Prior Auth:**
- Basic home health aide services
- Personal care services
- Standard homemaker services
- Routine skilled nursing visits (within authorized hours)

### Recommendation:

- ✅ **Include prior_auth_number field in patient profile** (optional)
- ✅ **Validate at claim submission time** based on service code
- ✅ **Check if service type requires prior auth** before submission
- ❌ **Do NOT block profile completion** if prior auth is missing
- ⚠️ **May block claim submission** if required for specific service

---

## 🔄 What Changed

### In Code (validation_utils.py):
```python
# REMOVED this validation:
prior_auth = patient.get('prior_auth_number', '').strip()
if not prior_auth:
    errors.append("Prior Authorization Number * is required (ODM & EVV)")

# Prior auth is now optional - not validated at profile level
```

### In Documentation (REQUIRED_FIELDS_ODM_EVV.md):
```
BEFORE: 13 required fields for patient (including prior_auth_number)
AFTER:  12 required fields for patient (prior_auth_number moved to optional)

Category Changed:
  Required by BOTH (*) → Required by ODM ONLY (service-specific)
```

---

## 💡 Implementation Guidance

### At Profile Completion:
- ✅ Allow saving without prior auth number
- ✅ Profile can be marked "complete" without prior auth
- ℹ️ Show optional field for prior auth in UI

### At Claim Submission:
```python
def validate_claim_for_submission(claim):
    """Validate claim based on service-specific rules"""
    
    service_code = claim.service_code
    
    # Check if this service requires prior auth
    if service_requires_prior_auth(service_code):
        if not claim.patient.prior_auth_number:
            raise ValidationError(
                f"Prior authorization required for service {service_code}. "
                f"Please obtain and enter prior auth number before submitting."
            )
```

### Service-Specific Validation:
```python
# Example: Home Health HCPCS codes that typically need prior auth
PRIOR_AUTH_REQUIRED_CODES = {
    'T1019',  # Personal Care Services - may need auth
    'T1020',  # Personal Care Services - Waiver
    # ... add codes as per Ohio Medicaid rules
}

def service_requires_prior_auth(hcpcs_code: str) -> bool:
    """Check if service code requires prior authorization"""
    return hcpcs_code in PRIOR_AUTH_REQUIRED_CODES
```

---

## 📊 Validation Summary

### Profile-Level Validation (Always Required):
**12 fields** must be complete before profile can be marked complete

### Claim-Level Validation (Conditional):
- Prior auth checked at submission time
- Based on service code
- Based on state/MCE rules
- Clear error if missing when needed

---

## ✅ Benefits of This Approach

1. **Flexible**: Doesn't force prior auth for services that don't need it
2. **Compliant**: Still validates prior auth when required
3. **User-Friendly**: Users can complete profiles faster
4. **Accurate**: Validation happens at the right time (claim submission)
5. **Scalable**: Easy to add service-specific rules

---

## 🎯 Updated Field Count

**Patient Profile:**
- Required Fields (*): 12 (was 13)
- Optional ODM Fields: 3 (including prior_auth_number)
- Optional EVV Fields: 3

**Employee Profile:**
- Required Fields (*): 13 (unchanged)
- Optional Fields: Various

---

## 📝 User Messaging Update

### Profile Form:
```
Prior Authorization Number
[________________________]
(Optional - required for certain services)
```

### Claim Submission:
```
⚠️ Prior Authorization Required

Service code T1019 requires prior authorization.

Please enter prior authorization number for this patient:
[________________________]

[ Cancel ]  [ Add Prior Auth & Submit ]
```

---

## 🔍 Where to Check Prior Auth Requirements

1. **Ohio Medicaid Provider Manual**
   - Chapter on Home Health Services
   - Prior Authorization section

2. **HCPCS Code Lookup**
   - Check specific code requirements
   - Ohio Medicaid fee schedule

3. **MCE Guidelines**
   - Each MCE may have different rules
   - Check contracts and provider guides

4. **Sandata EVV**
   - May flag if prior auth needed
   - Authorization module

---

**Correction Applied:** December 2024  
**Updated Files:**
- `/app/backend/validation_utils.py`
- `/app/REQUIRED_FIELDS_ODM_EVV.md`

**Status:** ✅ Prior auth no longer blocks profile completion
