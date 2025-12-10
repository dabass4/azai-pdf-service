# Timesheet Serialization Error - Root Cause Fix

## Issue Summary
The `GET /api/timesheets` endpoint was previously using no response_model (instead of the proper `List[Timesheet]`) due to concerns about data serialization errors with the `extracted_data` field stored in MongoDB.

## Root Cause
The issue was in the **manual clock-in/out routes** (`/app/backend/routes_manual_clock.py`), not in the PDF upload logic:

1. **Manual clock-in endpoint** was saving datetime objects directly to MongoDB:
   - `clock_in_time`, `clock_in_timestamp`, `created_at`, `updated_at`
   - `violation_time` in geofence violations

2. **Manual clock-out endpoint** was saving datetime objects directly to MongoDB:
   - `clock_out_time`, `clock_out_timestamp`, `updated_at`
   - `violation_time` in geofence violations

3. When these datetime objects were retrieved from MongoDB and returned by the API, they couldn't be properly validated by Pydantic's response model.

## The Fix
**File**: `/app/backend/routes_manual_clock.py`

### Changes Made:
1. **Clock-in function** (line 125-145):
   - Convert `clock_in_time` to ISO string before saving: `clock_in_time.isoformat()`
   - Convert `clock_in_timestamp` to ISO string
   - Convert `created_at` and `updated_at` to ISO strings

2. **Clock-out function** (line 278-293):
   - Convert `clock_out_time` to ISO string before saving
   - Convert `clock_out_timestamp` to ISO string
   - Convert `updated_at` to ISO string

3. **Geofence violation records**:
   - Convert `violation_time` to ISO string
   - Convert `created_at` to ISO string

### Response Model Restored:
**File**: `/app/backend/server.py` (line 1696)

Changed from:
```python
@api_router.get("/timesheets")
async def get_timesheets(...):
```

To:
```python
@api_router.get("/timesheets", response_model=List[Timesheet])
async def get_timesheets(...):
```

## Why This Works
- **MongoDB Storage**: Datetime objects are now stored as ISO strings (e.g., "2024-12-09T17:28:20.216838+00:00")
- **Pydantic Validation**: The Timesheet model can properly validate ISO datetime strings
- **JSON Serialization**: ISO strings serialize correctly in JSON responses
- **Type Safety**: Proper response_model validation ensures data integrity

## Testing Results
✅ `GET /api/timesheets` endpoint works with `response_model=List[Timesheet]`
✅ `GET /api/timesheets/{id}` endpoint works correctly
✅ No serialization errors in backend logs
✅ All datetime fields are properly formatted as ISO strings

## Prevention
- **Always convert datetime objects to ISO strings before MongoDB insertion**
- **Use `.isoformat()` method on datetime objects**
- **Keep response_model validation enabled to catch serialization issues early**

## Impact
- ✅ Proper data validation on all timesheet endpoints
- ✅ Type safety restored
- ✅ No more workarounds needed
- ✅ Future datetime serialization issues will be caught immediately
