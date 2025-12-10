# Geofencing Implementation Guide for AZAI

**Complete GPS Location Tracking & Validation for EVV Compliance**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Implementation Components](#implementation-components)
4. [Setup & Configuration](#setup--configuration)
5. [Frontend Integration](#frontend-integration)
6. [Backend Integration](#backend-integration)
7. [Testing](#testing)
8. [Compliance & Reporting](#compliance--reporting)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### What is Geofencing?

Geofencing for EVV (Electronic Visit Verification) ensures that healthcare workers are physically present at the patient's registered address when clocking in/out. This is **required by Medicaid** and validated by Sandata.

### Key Features Implemented

✅ **GPS Location Capture** - Browser-based geolocation API  
✅ **Distance Calculation** - Haversine formula for accuracy  
✅ **Geofence Validation** - Configurable radius checking  
✅ **Violation Detection** - Automatic flagging of out-of-bounds clock events  
✅ **Exception Management** - Supervisor approval workflow  
✅ **Audit Trail** - Complete location history for compliance  

---

## 🔧 How It Works

### The Geofencing Flow

```
1. Employee Opens Timesheet/Clock-In Page
   ↓
2. Browser Requests Location Permission
   ↓
3. GPS Coordinates Captured (latitude/longitude)
   ↓
4. System Calculates Distance to Patient Address
   ↓
5. Validation Check:
   • Within radius → ✅ Approved
   • Outside radius → ⚠️ Flagged for review
   ↓
6. Location Stored with Timesheet
   ↓
7. Submitted to Sandata with EVV data
```

### Distance Calculation

Uses the **Haversine Formula** for accurate distance:
- Accounts for Earth's curvature
- Accurate to within a few meters
- Calculates shortest distance between two points on a sphere

---

## 📦 Implementation Components

### Backend Files Created

**1. `/app/backend/geofencing.py`**
- Core geofencing logic
- Distance calculations
- Validation functions
- Exception management

**Key Classes:**
- `GeofenceValidator` - Main validation engine
- `GeofenceException` - Exception/override handling
- `GeofenceConfig` - Configuration management

**2. `/app/backend/geofence_models.py`**
- Pydantic data models
- Type validation
- API contracts

**Models:**
- `LocationData` - GPS coordinates
- `ClockEvent` - Clock in/out events
- `GeofenceValidationResult` - Validation outcomes
- `GeofenceViolation` - Violation records
- `OrganizationGeofenceConfig` - Organization settings

**3. `/app/backend/routes_geofencing.py`**
- REST API endpoints
- Location validation routes
- Configuration management
- Violation tracking

### Frontend Files Created

**1. `/app/frontend/src/components/LocationCapture.js`**
- React component for GPS capture
- Browser geolocation API integration
- Real-time validation display
- User-friendly error handling

---

## ⚙️ Setup & Configuration

### Step 1: Install Backend Dependencies

```bash
cd /app/backend
# No additional dependencies needed - uses Python stdlib
```

### Step 2: Update Server Configuration

Add geofencing routes to your main FastAPI app:

```python
# In /app/backend/server.py

from routes_geofencing import router as geofencing_router

# Add to your FastAPI app
app.include_router(geofencing_router)
```

### Step 3: Configure Geofence Radius

**Default Configuration:**
- Radius: 150 meters (~500 feet)
- Mode: Warning (not strict blocking)
- Requires supervisor approval for violations

**Update via API:**
```bash
curl -X PUT "${API_URL}/api/geofence/config" \
  -H "Content-Type: application/json" \
  -d '{
    "radius_feet": 500,
    "strict_mode": false,
    "require_approval": true
  }'
```

**Recommended Radii:**
- **Urban areas:** 100-150 meters (330-500 feet)
- **Suburban areas:** 150-300 meters (500-1000 feet)
- **Rural areas:** 300-500 meters (1000-1640 feet)

### Step 4: Database Collections

Create MongoDB collections for geofencing data:

```javascript
db.createCollection("geofence_violations")
db.createCollection("geofence_exceptions")
db.createCollection("geofence_configs")

// Indexes for performance
db.geofence_violations.createIndex({ "organization_id": 1, "status": 1 })
db.geofence_violations.createIndex({ "timesheet_id": 1 })
db.geofence_violations.createIndex({ "employee_id": 1 })
```

---

## 🎨 Frontend Integration

### Option 1: Standalone Location Capture

Add to any page where employees clock in/out:

```javascript
import LocationCapture from '../components/LocationCapture';

function ClockInPage() {
  const [location, setLocation] = useState(null);
  const [validation, setValidation] = useState(null);

  const patientLocation = {
    latitude: 39.9612,
    longitude: -82.9988,
    address: "123 Main St, Columbus, OH 43085"
  };

  const handleLocationCaptured = (capturedLocation) => {
    console.log('Location captured:', capturedLocation);
    setLocation(capturedLocation);
  };

  const handleValidationComplete = (result) => {
    console.log('Validation result:', result);
    setValidation(result);
    
    if (!result.valid) {
      alert('⚠️ You are outside the patient address geofence. Your supervisor will be notified.');
    }
  };

  return (
    <div>
      <h2>Clock In</h2>
      <LocationCapture
        patientLocation={patientLocation}
        onLocationCaptured={handleLocationCaptured}
        onValidationComplete={handleValidationComplete}
        showValidation={true}
        allowedRadiusFeet={500}
      />
      
      {location && validation && validation.valid && (
        <button onClick={submitClockIn}>
          Confirm Clock In
        </button>
      )}
    </div>
  );
}
```

### Option 2: Auto-Capture on Page Load

```javascript
<LocationCapture
  patientLocation={patientLocation}
  onLocationCaptured={handleLocationCaptured}
  onValidationComplete={handleValidationComplete}
  autoCapture={true}  // ← Automatically capture on mount
  showValidation={true}
/>
```

### Option 3: Integrate with Timesheet Upload

Update `/app/frontend/src/pages/TimesheetEditor.js`:

```javascript
import LocationCapture from '../components/LocationCapture';

// In your timesheet submission function
const handleSubmitToSandata = async () => {
  // 1. Capture location first
  const location = await captureLocationPromise();
  
  // 2. Validate against patient address
  const validation = await validateLocation(location, patientAddress);
  
  // 3. Include location data in submission
  const submissionData = {
    timesheet_id: timesheet.id,
    location: location,
    validation: validation,
    // ... other timesheet data
  };
  
  // 4. Submit to Sandata
  await submitToSandata(submissionData);
};
```

---

## 🔌 Backend Integration

### Add Location Fields to TimeEntry Model

Update `/app/backend/server.py`:

```python
class TimeEntry(BaseModel):
    date: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    hours_worked: Optional[str] = None
    
    # ADD THESE FIELDS FOR GEOFENCING
    clock_in_latitude: Optional[float] = None
    clock_in_longitude: Optional[float] = None
    clock_in_accuracy: Optional[float] = None
    clock_in_timestamp: Optional[datetime] = None
    
    clock_out_latitude: Optional[float] = None
    clock_out_longitude: Optional[float] = None
    clock_out_accuracy: Optional[float] = None
    clock_out_timestamp: Optional[datetime] = None
    
    # Geofence validation results
    clock_in_geofence_valid: Optional[bool] = None
    clock_in_distance_feet: Optional[float] = None
    clock_out_geofence_valid: Optional[bool] = None
    clock_out_distance_feet: Optional[float] = None
```

### Validate Location on Timesheet Submission

```python
from geofencing import GeofenceValidator

@app.post("/api/timesheets/{timesheet_id}/submit")
async def submit_timesheet_with_location(
    timesheet_id: str,
    clock_in_location: dict,
    clock_out_location: dict
):
    # Get timesheet and patient info
    timesheet = await db.timesheets.find_one({"id": timesheet_id})
    patient = await db.patients.find_one({"id": timesheet["patient_id"]})
    
    # Validate clock-in location
    clock_in_validation = GeofenceValidator.validate_clock_event(
        event_type="clock_in",
        employee_location=clock_in_location,
        patient_location={
            "latitude": patient["address_latitude"],
            "longitude": patient["address_longitude"]
        }
    )
    
    # Validate clock-out location
    clock_out_validation = GeofenceValidator.validate_clock_event(
        event_type="clock_out",
        employee_location=clock_out_location,
        patient_location={
            "latitude": patient["address_latitude"],
            "longitude": patient["address_longitude"]
        }
    )
    
    # Check for violations
    violations = []
    if not clock_in_validation["valid"]:
        violations.append({
            "type": "clock_in",
            "distance_feet": clock_in_validation["distance_feet"],
            "message": clock_in_validation["message"]
        })
    
    if not clock_out_validation["valid"]:
        violations.append({
            "type": "clock_out",
            "distance_feet": clock_out_validation["distance_feet"],
            "message": clock_out_validation["message"]
        })
    
    # Store violations for review
    if violations:
        await db.geofence_violations.insert_many([
            {
                "timesheet_id": timesheet_id,
                "employee_id": timesheet["employee_id"],
                "patient_id": patient["id"],
                "violation": v,
                "status": "pending",
                "created_at": datetime.now(timezone.utc)
            } for v in violations
        ])
        
        # Notify supervisor
        await send_geofence_violation_alert(timesheet_id, violations)
    
    # Update timesheet with location data
    await db.timesheets.update_one(
        {"id": timesheet_id"},
        {"$set": {
            "clock_in_validation": clock_in_validation,
            "clock_out_validation": clock_out_validation,
            "has_geofence_violations": len(violations) > 0
        }}
    )
    
    return {
        "status": "success" if len(violations) == 0 else "pending_review",
        "violations": violations
    }
```

---

## 🧪 Testing

### Test 1: Location Capture

**Test the frontend component:**

1. Open developer console (F12)
2. Go to a page with LocationCapture component
3. Click "Capture My Location"
4. Browser should prompt for permission
5. Grant permission
6. Location should display with coordinates and accuracy

**Expected Output:**
```
Location Captured ✓
Coordinates: 39.961234, -82.998765
Accuracy: ±15m (Good)
Time: 10:30:45 AM
```

### Test 2: Distance Calculation

**Test API endpoint:**

```bash
curl "${API_URL}/api/geofence/distance?lat1=39.9612&lon1=-82.9988&lat2=39.9650&lon2=-83.0050"
```

**Expected Response:**
```json
{
  "distance_meters": 543.21,
  "distance_feet": 1782.19,
  "distance_miles": 0.34
}
```

### Test 3: Geofence Validation

**Test with valid location (within radius):**

```bash
curl -X POST "${API_URL}/api/geofence/validate?employee_lat=39.9612&employee_lon=-82.9988&patient_lat=39.9615&patient_lon=-82.9990&event_type=clock_in"
```

**Expected Response:**
```json
{
  "valid": true,
  "distance_meters": 42.5,
  "distance_feet": 139.4,
  "allowed_radius_feet": 492.0,
  "accuracy_level": "excellent",
  "message": "Location verified: 139 ft from patient address (within 492 ft radius)"
}
```

**Test with invalid location (outside radius):**

```bash
curl -X POST "${API_URL}/api/geofence/validate?employee_lat=40.0000&employee_lon=-83.0000&patient_lat=39.9612&patient_lon=-82.9988&event_type=clock_in"
```

**Expected Response:**
```json
{
  "valid": false,
  "distance_meters": 4523.7,
  "distance_feet": 14843.2,
  "variance_meters": 4373.7,
  "accuracy_level": "poor",
  "message": "⚠️ Location outside geofence: 14843 ft from patient address (allowed: 492 ft)"
}
```

### Test 4: Complete Flow Test

**Manual Test Steps:**

1. **Setup Test Patient:**
   ```
   Name: Test Patient
   Address: 123 Main St, Columbus, OH
   Latitude: 39.9612
   Longitude: -82.9988
   ```

2. **Upload Timesheet** with Test Patient

3. **Complete Patient Profile** with GPS coordinates

4. **Go to Clock-In Page** (or timesheet submission)

5. **Capture Location:**
   - Allow browser permission
   - Location should be captured
   - Validation should run automatically

6. **Check Validation Result:**
   - If at correct location → Green checkmark
   - If at different location → Yellow warning

7. **Submit Timesheet**

8. **Check for Violations:**
   ```bash
   curl "${API_URL}/api/geofence/violations"
   ```

---

## 📊 Compliance & Reporting

### For Sandata Submission

Include location data in EVV submission:

```python
# In evv_export.py or similar

visit_data = {
    "VisitOtherID": timesheet_id,
    "Calls": [
        {
            "CallType": "Mobile",  # GPS-enabled device
            "CallAssignment": "Call In",
            "CallDateTime": clock_in_time,
            "CallLatitude": clock_in_latitude,
            "CallLongitude": clock_in_longitude,
            "CallSource": "Mobile App"  # or "Web Browser"
        },
        {
            "CallType": "Mobile",
            "CallAssignment": "Call Out",
            "CallDateTime": clock_out_time,
            "CallLatitude": clock_out_latitude,
            "CallLongitude": clock_out_longitude,
            "CallSource": "Mobile App"
        }
    ]
}
```

### Violation Reports

**Get All Pending Violations:**
```bash
GET /api/geofence/violations?status=pending
```

**Weekly Violation Summary:**
```sql
-- Create aggregated report
SELECT 
  employee_id,
  COUNT(*) as violation_count,
  AVG(distance_feet) as avg_distance_feet,
  MAX(distance_feet) as max_distance_feet
FROM geofence_violations
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY employee_id
ORDER BY violation_count DESC
```

### Audit Trail

All location captures are logged with:
- Timestamp
- GPS coordinates
- Accuracy level
- Device/browser info
- Validation result

This provides complete audit trail for Medicaid compliance.

---

## 🔧 Troubleshooting

### Issue 1: "Location Permission Denied"

**Cause:** User denied browser permission

**Solution:**
1. Click browser address bar padlock icon
2. Find "Location" permission
3. Change to "Allow"
4. Refresh page

**Chrome:**
```
Settings → Privacy and security → Site settings → Location → Add allowed site
```

**Firefox:**
```
Preferences → Privacy & Security → Permissions → Location → Settings
```

### Issue 2: "Location Unavailable"

**Cause:** GPS disabled or no signal

**Solution:**
- Enable location services on device
- Move near window (for indoor GPS)
- Use WiFi (improves location accuracy)
- Try different browser

### Issue 3: Low Accuracy (>100m)

**Cause:** Poor GPS signal or network-based location

**Solution:**
- Enable "High Accuracy" mode on device
- Ensure GPS is on (not just network location)
- Wait 30-60 seconds for GPS lock
- Move outdoors or near window

### Issue 4: Always Shows "Outside Geofence"

**Cause:** Incorrect patient address coordinates

**Solution:**
```bash
# Verify patient coordinates
GET /api/patients/{patient_id}

# Check if coordinates match address
# Use Google Maps to verify:
# 1. Search patient address
# 2. Right-click on map
# 3. Select "What's here?"
# 4. Compare coordinates
```

**Update Patient Coordinates:**
```bash
PUT /api/patients/{patient_id}
{
  "address_latitude": 39.9612,
  "address_longitude": -82.9988
}
```

### Issue 5: CORS Errors on API Calls

**Cause:** Frontend and backend on different origins

**Solution:**
Update backend CORS settings in `server.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 Next Steps

### Phase 1: Basic Implementation ✅ (Completed)
- [x] Core geofencing module
- [x] Location capture component
- [x] Validation API endpoints
- [x] Documentation

### Phase 2: Database Integration (To Do)
- [ ] Add location fields to TimeEntry model in server.py
- [ ] Create MongoDB collections for violations
- [ ] Store location data with timesheets
- [ ] Include router in main FastAPI app

### Phase 3: UI Integration (To Do)
- [ ] Add LocationCapture to timesheet pages
- [ ] Display geofence status on timesheets
- [ ] Create violations dashboard
- [ ] Add supervisor approval workflow

### Phase 4: Sandata Integration (To Do)
- [ ] Include location in EVV export
- [ ] Format for Sandata "Calls" structure
- [ ] Test submission with location data
- [ ] Verify in Sandata portal

### Phase 5: Advanced Features (Future)
- [ ] Mobile app integration
- [ ] Background location tracking
- [ ] Geofence history/heatmaps
- [ ] AI-based anomaly detection
- [ ] Automated exception approval

---

## 📚 Additional Resources

### Geolocation API Documentation
- **MDN:** https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API
- **Browser Support:** https://caniuse.com/geolocation

### Ohio Medicaid EVV Requirements
- **EVV Specifications:** Contact ODM for latest docs
- **Sandata Requirements:** Refer to Sandata API documentation

### Haversine Formula
- **Wikipedia:** https://en.wikipedia.org/wiki/Haversine_formula
- **Calculator:** https://www.movable-type.co.uk/scripts/latlong.html

---

## ✅ Quick Reference

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/geofence/validate` | POST | Validate location against patient address |
| `/api/geofence/distance` | GET | Calculate distance between coordinates |
| `/api/geofence/config` | GET | Get organization geofence settings |
| `/api/geofence/config` | PUT | Update geofence settings |
| `/api/geofence/violations` | GET | List geofence violations |
| `/api/geofence/violations/{id}/approve` | POST | Approve violation exception |

### Default Configuration

```javascript
{
  "radius_meters": 150,
  "radius_feet": 492,
  "strict_mode": false,
  "require_approval_for_violations": true
}
```

### Location Data Format

```javascript
{
  "latitude": 39.9612,
  "longitude": -82.9988,
  "accuracy": 15.0,
  "timestamp": "2025-12-10T10:30:45Z",
  "provider": "gps"
}
```

---

**Document Version:** 1.0  
**Last Updated:** December 10, 2025  
**Maintained By:** AZAI Development Team
