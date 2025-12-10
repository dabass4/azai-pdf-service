# Patient-Employee-Service Code Connections

**Complete Authorization & Assignment System for AZAI**

---

## 🎯 Overview

This document explains the relationship structure between **Patients (Clients)**, **Employees (Direct Care Workers)**, and **Service Codes** in the AZAI healthcare timesheet system.

### Why These Connections Matter

In healthcare EVV systems, you can't just have any employee provide any service to any patient. You need:

1. **Service Authorizations** - Which services is each patient approved to receive?
2. **Employee Assignments** - Which employees are assigned to work with which patients?
3. **Employee Qualifications** - Which services is each employee certified to provide?

---

## 📊 Data Model Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    RELATIONSHIP STRUCTURE                        │
└─────────────────────────────────────────────────────────────────┘

    PATIENT                    SERVICE CODE               EMPLOYEE
    ┌─────────┐               ┌──────────────┐          ┌─────────┐
    │ Jane    │               │ Personal Care│          │ John    │
    │ Smith   │               │ (T1019)      │          │ Doe     │
    └────┬────┘               └──────┬───────┘          └────┬────┘
         │                            │                       │
         │                            │                       │
         │    ┌───────────────────────┴───────────────┐      │
         │    │                                        │      │
         │    ▼                                        ▼      │
         │  SERVICE AUTHORIZATION              EMPLOYEE       │
         │  ┌──────────────────────┐      QUALIFICATION      │
         │  │ Patient: Jane Smith  │      ┌──────────────┐   │
         │  │ Service: T1019       │      │Employee: John│   │
         │  │ Units: 160/month     │      │Service: T1019│   │
         │  │ Valid: 1/1-12/31     │      │Status: Active│   │
         │  └──────────────────────┘      └──────────────┘   │
         │                                                     │
         └───────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
                    EMPLOYEE-PATIENT ASSIGNMENT
                    ┌─────────────────────────────┐
                    │ Employee: John Doe          │
                    │ Patient: Jane Smith         │
                    │ Services: [T1019, G0156]    │
                    │ Type: Primary               │
                    │ Status: Active              │
                    └─────────────────────────────┘
```

---

## 🔗 Four Core Relationship Types

### 1. Service Authorization

**What:** Approval for a patient to receive specific services

**Example:** 
- Patient: Jane Smith
- Service: Personal Care (T1019)
- Authorized: 160 units per month
- Date Range: January 1 - December 31, 2025
- Payer: Ohio Department of Medicaid

```json
{
  "id": "auth-uuid",
  "patient_id": "patient-uuid",
  "patient_name": "Jane Smith",
  "authorization_number": "AUTH123456",
  "payer": "ODM",
  "payer_program": "SP",
  "service_code_id": "service-uuid",
  "service_name": "Personal Care",
  "procedure_code": "T1019",
  "units_authorized": 160,
  "units_per_month": 160,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "status": "active"
}
```

### 2. Employee-Patient Assignment

**What:** Assigns specific employees to work with specific patients

**Example:**
- Employee: John Doe
- Patient: Jane Smith
- Type: Primary caregiver
- Authorized Services: Personal Care, Respite Care
- Status: Active

```json
{
  "id": "assignment-uuid",
  "employee_id": "employee-uuid",
  "employee_name": "John Doe",
  "patient_id": "patient-uuid",
  "patient_name": "Jane Smith",
  "assignment_type": "primary",
  "authorized_service_codes": ["service-uuid-1", "service-uuid-2"],
  "start_date": "2025-01-01",
  "end_date": null,
  "status": "active"
}
```

### 3. Employee Service Qualification

**What:** Certifies which services an employee is qualified to provide

**Example:**
- Employee: John Doe
- Service: Personal Care (T1019)
- Certification: CNA-12345
- Expiration: December 31, 2026

```json
{
  "id": "qualification-uuid",
  "employee_id": "employee-uuid",
  "employee_name": "John Doe",
  "service_code_id": "service-uuid",
  "service_name": "Personal Care",
  "procedure_code": "T1019",
  "certification_number": "CNA-12345",
  "certification_date": "2024-01-15",
  "expiration_date": "2026-12-31",
  "training_completed": true,
  "status": "active"
}
```

### 4. Patient Care Team

**What:** Summary view of all caregivers and services for a patient

**Example:**

```json
{
  "patient_id": "patient-uuid",
  "patient_name": "Jane Smith",
  "primary_employee_id": "employee-uuid-1",
  "primary_employee_name": "John Doe",
  "assigned_employees": [
    {
      "id": "employee-uuid-1",
      "name": "John Doe",
      "assignment_type": "primary",
      "services": ["T1019", "S5150"]
    },
    {
      "id": "employee-uuid-2",
      "name": "Sarah Johnson",
      "assignment_type": "backup",
      "services": ["T1019"]
    }
  ],
  "authorized_services": [
    {
      "service_code": "Personal Care",
      "procedure_code": "T1019",
      "authorization_number": "AUTH123456",
      "units_remaining": 140
    }
  ],
  "total_employees": 2,
  "total_authorizations": 1
}
```

---

## 🔐 Validation Logic

### Before Allowing Service Delivery

When an employee tries to clock in or submit a timesheet, the system validates:

```python
# Pseudo-code validation flow
def can_provide_service(employee_id, patient_id, service_code_id):
    # 1. Is employee assigned to patient?
    assignment = check_assignment(employee_id, patient_id)
    if not assignment or assignment.status != "active":
        return False, "Employee not assigned to patient"
    
    # 2. Is employee qualified for this service?
    qualification = check_qualification(employee_id, service_code_id)
    if not qualification or qualification.status != "active":
        return False, "Employee not qualified for service"
    
    # 3. Is service in employee's authorized services for this patient?
    if service_code_id not in assignment.authorized_service_codes:
        return False, "Service not authorized in assignment"
    
    # 4. Does patient have valid authorization for this service?
    authorization = check_authorization(patient_id, service_code_id)
    if not authorization or authorization.status != "active":
        return False, "No valid authorization for patient"
    
    # 5. Are units still available?
    if authorization.units_remaining <= 0:
        return False, "No units remaining on authorization"
    
    return True, "Service validated"
```

---

## 🚀 API Endpoints

### Service Authorizations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/authorizations/service-authorizations` | POST | Create new authorization |
| `/api/authorizations/service-authorizations` | GET | List authorizations (filter by patient) |
| `/api/authorizations/service-authorizations/{id}` | GET | Get specific authorization |

**Create Authorization:**
```bash
POST /api/authorizations/service-authorizations
{
  "patient_id": "patient-uuid",
  "authorization_number": "AUTH123456",
  "payer": "ODM",
  "payer_program": "SP",
  "service_code_id": "service-uuid",
  "service_name": "Personal Care",
  "procedure_code": "T1019",
  "units_authorized": 160,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

### Employee-Patient Assignments

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/authorizations/employee-assignments` | POST | Assign employee to patient |
| `/api/authorizations/employee-assignments` | GET | List assignments |

**Create Assignment:**
```bash
POST /api/authorizations/employee-assignments
{
  "employee_id": "employee-uuid",
  "patient_id": "patient-uuid",
  "assignment_type": "primary",
  "authorized_service_codes": ["service-uuid-1", "service-uuid-2"],
  "start_date": "2025-01-01"
}
```

### Employee Qualifications

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/authorizations/employee-qualifications` | POST | Add qualification |
| `/api/authorizations/employee-qualifications` | GET | List qualifications |

**Create Qualification:**
```bash
POST /api/authorizations/employee-qualifications
{
  "employee_id": "employee-uuid",
  "service_code_id": "service-uuid",
  "service_name": "Personal Care",
  "procedure_code": "T1019",
  "certification_number": "CNA-12345",
  "certification_date": "2024-01-15",
  "expiration_date": "2026-12-31",
  "training_completed": true
}
```

### Care Team

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/authorizations/care-team/{patient_id}` | GET | Get complete care team |

### Validation

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/authorizations/validate-service` | GET | Validate employee-patient-service |

**Validate Service:**
```bash
GET /api/authorizations/validate-service?employee_id=X&patient_id=Y&service_code_id=Z

Response:
{
  "valid": true,
  "message": "Employee is authorized to provide this service",
  "employee_validation": {...},
  "authorization_validation": {...}
}
```

---

## 💾 Database Collections

### service_authorizations
```javascript
{
  "id": "auth-uuid",
  "organization_id": "org-uuid",
  "patient_id": "patient-uuid",
  "patient_name": "Jane Smith",
  "authorization_number": "AUTH123456",
  "payer": "ODM",
  "payer_program": "SP",
  "service_code_id": "service-uuid",
  "service_name": "Personal Care",
  "procedure_code": "T1019",
  "units_authorized": 160,
  "units_used": 20,
  "hours_authorized": 160.0,
  "hours_used": 20.0,
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "status": "active",
  "rate": 20.50,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### employee_patient_assignments
```javascript
{
  "id": "assignment-uuid",
  "organization_id": "org-uuid",
  "employee_id": "employee-uuid",
  "employee_name": "John Doe",
  "patient_id": "patient-uuid",
  "patient_name": "Jane Smith",
  "assignment_type": "primary",
  "authorized_service_codes": ["service-uuid-1"],
  "start_date": "2025-01-01",
  "end_date": null,
  "max_hours_per_week": 40.0,
  "status": "active",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### employee_service_qualifications
```javascript
{
  "id": "qualification-uuid",
  "organization_id": "org-uuid",
  "employee_id": "employee-uuid",
  "employee_name": "John Doe",
  "service_code_id": "service-uuid",
  "service_name": "Personal Care",
  "procedure_code": "T1019",
  "certification_number": "CNA-12345",
  "certification_date": "2024-01-15",
  "expiration_date": "2026-12-31",
  "training_completed": true,
  "training_date": "2024-01-10",
  "status": "active",
  "created_at": "2024-01-15T00:00:00Z"
}
```

---

## 🔄 Typical Workflow

### Setting Up a New Patient

1. **Create Patient Profile**
   ```
   POST /api/patients
   ```

2. **Create Service Authorization**
   ```
   POST /api/authorizations/service-authorizations
   {
     "patient_id": "new-patient-uuid",
     "service_code_id": "T1019-uuid",
     "units_authorized": 160,
     "start_date": "2025-01-01",
     "end_date": "2025-12-31"
   }
   ```

3. **Assign Employee to Patient**
   ```
   POST /api/authorizations/employee-assignments
   {
     "employee_id": "john-doe-uuid",
     "patient_id": "new-patient-uuid",
     "authorized_service_codes": ["T1019-uuid"]
   }
   ```

4. **Verify Employee is Qualified**
   ```
   GET /api/authorizations/employee-qualifications?employee_id=john-doe-uuid
   ```

5. **Validate Service Delivery**
   ```
   GET /api/authorizations/validate-service?employee_id=X&patient_id=Y&service_code_id=Z
   ```

6. **Employee Can Now Clock In/Provide Service**

---

## 📋 Use Cases

### Use Case 1: Check if Employee Can Work with Patient

**Scenario:** Employee John wants to clock in for Patient Jane

**Check:**
```bash
GET /api/authorizations/validate-service?employee_id=john&patient_id=jane&service_code_id=T1019
```

**Possible Results:**

✅ **Valid:**
```json
{
  "valid": true,
  "message": "Employee is authorized to provide this service"
}
```

❌ **Not Assigned:**
```json
{
  "valid": false,
  "reason": "Employee is not assigned to this patient"
}
```

❌ **Not Qualified:**
```json
{
  "valid": false,
  "reason": "Employee is not qualified for this service"
}
```

❌ **No Authorization:**
```json
{
  "valid": false,
  "reason": "No active authorization found for this service"
}
```

❌ **Units Exhausted:**
```json
{
  "valid": false,
  "reason": "No units remaining on authorization"
}
```

### Use Case 2: View Patient's Care Team

**Scenario:** View all employees assigned to Patient Jane

```bash
GET /api/authorizations/care-team/jane-patient-uuid

Response:
{
  "patient_name": "Jane Smith",
  "primary_employee_name": "John Doe",
  "assigned_employees": [
    {"name": "John Doe", "assignment_type": "primary"},
    {"name": "Sarah Johnson", "assignment_type": "backup"}
  ],
  "authorized_services": [
    {"service_code": "Personal Care", "units_remaining": 140}
  ]
}
```

### Use Case 3: Track Authorization Usage

**Scenario:** Patient has 160 units/month, how many are left?

```bash
GET /api/authorizations/service-authorizations?patient_id=jane

Response:
{
  "authorizations": [
    {
      "service_name": "Personal Care",
      "units_authorized": 160,
      "units_used": 20,
      "validation": {
        "valid": true,
        "units_remaining": 140
      }
    }
  ]
}
```

---

## 🎓 Key Concepts

### Assignment Types

- **Primary:** Main caregiver for the patient
- **Backup:** Substitute when primary is unavailable
- **Temporary:** Short-term assignment (e.g., vacation coverage)

### Authorization Status

- **active:** Currently valid
- **expired:** End date has passed
- **suspended:** Temporarily stopped
- **cancelled:** Permanently cancelled

### Qualification Status

- **active:** Currently certified
- **expired:** Certification expired
- **suspended:** Temporarily inactive

---

## ⚠️ Important Notes

### 1. Validation Before Service Delivery

**Always** validate before allowing an employee to:
- Clock in for a patient
- Submit a timesheet
- Record services provided

### 2. Track Usage

Update `units_used` and `hours_used` on authorizations after each service delivery to prevent overuse.

### 3. Expiration Checking

Regularly check for:
- Expired authorizations
- Expired qualifications/certifications
- Ended assignments

### 4. Multi-Tenancy

All relationships are scoped by `organization_id` for data isolation.

---

## 🔧 Next Steps

### Immediate (To Do)

1. **Restart Backend:**
   ```bash
   sudo supervisorctl restart backend
   ```

2. **Test Endpoints:**
   ```bash
   # Create a test authorization
   curl -X POST "${API_URL}/api/authorizations/service-authorizations" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ${TOKEN}" \
     -d '{...}'
   ```

3. **Create MongoDB Collections:**
   ```javascript
   db.createCollection("service_authorizations")
   db.createCollection("employee_patient_assignments")
   db.createCollection("employee_service_qualifications")
   
   // Indexes
   db.service_authorizations.createIndex({"patient_id": 1, "status": 1})
   db.employee_patient_assignments.createIndex({"employee_id": 1, "patient_id": 1})
   db.employee_service_qualifications.createIndex({"employee_id": 1, "service_code_id": 1})
   ```

### Future Enhancements

- **Frontend UI:** Create pages for managing authorizations, assignments, and qualifications
- **Auto-Alerts:** Notify when authorizations are close to expiration or units running low
- **Bulk Operations:** Import/export authorizations from Excel/CSV
- **Reporting:** Dashboard showing authorization usage, employee workload, etc.

---

## 📚 Summary

**The connection structure ensures:**

✅ Only authorized employees work with patients  
✅ Only qualified employees provide specific services  
✅ Services are only provided when authorized  
✅ Authorization units/hours are tracked  
✅ Complete audit trail for compliance  

**Three-Way Validation:**
```
Employee ←→ Patient ←→ Service Code
    ↓           ↓           ↓
Assignment + Authorization + Qualification = Valid Service
```

---

**Document Version:** 1.0  
**Last Updated:** December 10, 2025  
**Files Created:**
- `/app/backend/patient_authorizations.py` - Data models
- `/app/backend/routes_authorizations.py` - API endpoints
