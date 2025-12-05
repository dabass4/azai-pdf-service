# AZAI Auto-Sync Feature Documentation

## Overview
AZAI now automatically syncs corrections between employee/patient profiles and all related timesheets.

---

## Feature 1: Employee Profile Auto-Sync

### How It Works
When you edit an employee profile, AZAI automatically:
1. Updates the employee's information in the database
2. Finds ALL timesheets that reference this employee
3. Updates the employee name in ALL those timesheets
4. Marks the timesheets as "auto-corrected"
5. Records the correction timestamp

### Example Workflow
```
1. Timesheet is scanned, extracts employee name as "J0hn Sm1th" (OCR error)
2. Employee profile auto-created with name "J0hn Sm1th"
3. You edit the employee profile, correct name to "John Smith"
4. AZAI automatically:
   ✅ Updates employee profile to "John Smith"
   ✅ Finds all timesheets with this employee
   ✅ Updates extracted_data.employee_entries[].employee_name to "John Smith"
   ✅ Adds auto_corrected: true flag
   ✅ Adds corrected_at timestamp
```

### API Endpoint
```bash
PUT /api/employees/{employee_id}
{
  "first_name": "John",
  "last_name": "Smith"
}
```

**Response:**
- Updates employee profile
- Returns: Number of timesheets auto-synced
- Log message: "Auto-synced X timesheets with updated employee name: John Smith"

---

## Feature 2: Patient Profile Auto-Sync

### How It Works
When you edit a patient profile, AZAI automatically:
1. Updates the patient's information in the database
2. Finds ALL timesheets linked to this patient
3. Updates the client name in ALL those timesheets
4. Marks the timesheets with auto-correction metadata
5. Records the correction timestamp

### Example Workflow
```
1. Timesheet is scanned, extracts client name as "Jane D0e" (OCR error)
2. Patient profile auto-created with name "Jane D0e"
3. You edit the patient profile, correct name to "Jane Doe"
4. AZAI automatically:
   ✅ Updates patient profile to "Jane Doe"
   ✅ Finds all timesheets for this patient (via patient_id)
   ✅ Updates extracted_data.client_name to "Jane Doe"
   ✅ Adds metadata.patient_auto_corrected: true
   ✅ Adds metadata.patient_corrected_at timestamp
```

### API Endpoint
```bash
PUT /api/patients/{patient_id}
{
  "first_name": "Jane",
  "last_name": "Doe",
  "medicaid_number": "123456789012"
}
```

**Response:**
- Updates patient profile
- Returns: Updated patient data
- Log message: "Auto-synced X timesheets with updated patient info: Jane Doe"

---

## Feature 3: Improved Date & Name Extraction

### Enhanced Date Recognition

**What's Improved:**
- ✅ Better week detection ("Week of 10/6/2024", "10/6 - 10/12")
- ✅ Full date extraction with year when available
- ✅ Context-aware date parsing (uses week info to fill in missing data)
- ✅ Multiple date format support

**Supported Date Formats:**
```
✅ Full dates: 10/6/2024, 10-06-2024, 10.06.2024
✅ Partial dates: 10/6, 10-06 (month/day)
✅ Day names: Monday, Mon, M
✅ Day numbers: 6, 06 (when week context is present)
```

**Extraction Priority:**
1. BEST: Full date with year (10/6/2024)
2. GOOD: Month and day (10/6)
3. OKAY: Day name (Monday)
4. FALLBACK: Day number (6) + week context

### Enhanced Name Recognition

**What's Improved:**
- ✅ Full name extraction (First Middle Last)
- ✅ Name format normalization ("SMITH, JOHN" → "John Smith")
- ✅ OCR error detection and patterns
- ✅ Multiple name format support

**Common OCR Errors Detected:**
```
❌ "J0hn" → ✅ "John" (0 → O)
❌ "Sm1th" → ✅ "Smith" (1 → i)
❌ "5arah" → ✅ "Sarah" (5 → S)
❌ "D0e" → ✅ "Doe" (0 → o)
```

**Supported Name Formats:**
```
✅ "John Smith" → "John Smith"
✅ "Smith, John" → "John Smith"
✅ "JOHN SMITH" → "John Smith"
✅ "J. Smith" → "J. Smith"
✅ "John M. Smith" → "John M. Smith"
```

---

## Feature 4: Re-Scan Endpoint

### Purpose
Allows users to request a re-scan of a timesheet if:
- Initial extraction had errors
- OCR quality was poor
- User wants to retry with improved AI

### API Endpoint
```bash
POST /api/timesheets/{timesheet_id}/rescan
```

**Note:** Currently returns message to re-upload file. In production, this would:
1. Retrieve stored original file
2. Re-run extraction with latest AI improvements
3. Update timesheet with new extracted data
4. Maintain audit trail of re-scans

---

## Technical Details

### Database Structure

**Timesheet Document (after auto-correction):**
```json
{
  "id": "timesheet-123",
  "patient_id": "patient-456",
  "extracted_data": {
    "client_name": "Jane Doe",  // Auto-corrected
    "employee_entries": [
      {
        "employee_name": "John Smith",  // Auto-corrected
        "auto_corrected": true,
        "corrected_at": "2024-12-05T20:00:00Z",
        "time_entries": [...]
      }
    ]
  },
  "metadata": {
    "patient_auto_corrected": true,
    "patient_corrected_at": "2024-12-05T19:55:00Z",
    "confidence_score": 0.87
  }
}
```

### Auto-Sync Logic

**Employee Update Flow:**
```python
1. User updates employee profile (PUT /employees/{id})
2. Backend saves employee changes
3. Backend queries: db.timesheets.find({"registration_results.employees.id": employee_id})
4. For each timesheet:
   - Update extracted_data.employee_entries where employee matches
   - Add auto_corrected flag
   - Add corrected_at timestamp
5. Log: "Auto-synced X timesheets"
6. Return updated employee profile
```

**Patient Update Flow:**
```python
1. User updates patient profile (PUT /patients/{id})
2. Backend saves patient changes
3. Backend queries: db.timesheets.find({"patient_id": patient_id})
4. For each timesheet:
   - Update extracted_data.client_name
   - Add metadata.patient_auto_corrected
   - Add metadata.patient_corrected_at
5. Log: "Auto-synced X timesheets"
6. Return updated patient profile
```

---

## Usage Examples

### Example 1: Correcting OCR Error in Employee Name

**Scenario:** Timesheet extracted "J0hn Sm1th" but actual name is "John Smith"

```bash
# Step 1: Get employee ID from timesheet
GET /api/timesheets/abc-123
# Response includes: registration_results.employees[0].id = "emp-456"

# Step 2: Update employee profile
PUT /api/employees/emp-456
{
  "first_name": "John",
  "last_name": "Smith"
}

# Result:
# ✅ Employee profile updated
# ✅ All 15 timesheets with this employee now show "John Smith"
# ✅ Timesheets marked as auto-corrected
```

### Example 2: Correcting Patient Information

**Scenario:** Patient name extracted as "Jane D0e" (OCR error)

```bash
# Step 1: Update patient profile
PUT /api/patients/patient-789
{
  "first_name": "Jane",
  "last_name": "Doe",
  "medicaid_number": "123456789012"
}

# Result:
# ✅ Patient profile updated
# ✅ All 23 timesheets for this patient now show "Jane Doe"
# ✅ Medicaid number updated across all records
```

---

## Benefits

### 1. Time Savings
- ❌ **Before:** Edit each timesheet individually (5 min × 20 timesheets = 100 min)
- ✅ **After:** Edit profile once (2 min), auto-sync handles rest

### 2. Data Consistency
- ✅ All historical data automatically corrected
- ✅ No missed timesheets
- ✅ Single source of truth

### 3. Audit Trail
- ✅ Track when corrections were made
- ✅ See which timesheets were auto-corrected
- ✅ Maintain data integrity

### 4. Improved Accuracy
- ✅ Enhanced OCR instructions
- ✅ Better date parsing
- ✅ Name normalization
- ✅ Context-aware extraction

---

## Future Enhancements

### Planned Features:
1. **Bulk Re-scan:** Re-process multiple timesheets at once
2. **Smart Suggestions:** AI suggests corrections based on patterns
3. **Confidence Scoring:** Show extraction confidence per field
4. **Manual Review Queue:** Flag low-confidence extractions for review
5. **File Persistence:** Store original files for re-scanning
6. **Version History:** Track all changes to timesheet data

---

## Testing Auto-Sync

### Test Scenario 1: Employee Name Correction
```bash
# 1. Upload timesheet (creates employee with OCR name)
POST /api/timesheets/upload

# 2. Get employee ID from response
# Note the employee_id from registration_results

# 3. Correct employee name
PUT /api/employees/{employee_id}
{"first_name": "CorrectName"}

# 4. Verify timesheet updated
GET /api/timesheets/{timesheet_id}
# Check: extracted_data.employee_entries[0].employee_name = "CorrectName"
```

### Test Scenario 2: Patient Name Correction
```bash
# 1. Upload timesheet (creates patient with OCR name)
POST /api/timesheets/upload

# 2. Correct patient name
PUT /api/patients/{patient_id}
{"first_name": "CorrectName"}

# 3. Verify timesheet updated
GET /api/timesheets/{timesheet_id}
# Check: extracted_data.client_name = "CorrectName"
```

---

## Configuration

No additional configuration needed. Auto-sync is enabled by default for all organizations.

---

## Support

For issues or questions about auto-sync functionality:
1. Check backend logs for auto-sync messages
2. Verify profile updates are saving correctly
3. Check timesheet metadata for auto_corrected flags
4. Review extraction confidence scores
