# Total Minutes KeyError Fix

## Issue
**Error**: `KeyError: 'total_minutes'` during PDF timesheet extraction

## Error Location
- **File**: `/app/backend/server.py`
- **Line**: 1174
- **Function**: `extract_timesheet_data()`

## Root Cause
The `decimal_hours_to_hours_minutes()` utility function was not consistently returning the `total_minutes` key in all code paths:

### Problem Code:
```python
def decimal_hours_to_hours_minutes(decimal_hours: float) -> dict:
    if decimal_hours is None:
        return {'hours': 0, 'minutes': 0, 'formatted': '0:00'}  # ❌ Missing total_minutes
    
    try:
        decimal_hours = float(decimal_hours)
    except (ValueError, TypeError):
        return {'hours': 0, 'minutes': 0, 'formatted': '0:00'}  # ❌ Missing total_minutes
    
    # ... rest of function returns total_minutes correctly
```

## When It Failed
The error occurred when:
1. PDF extraction returned `None` or invalid values for `hours_worked`
2. Time entries had missing or unparseable time data
3. Edge cases like blank entries or OCR errors

## The Fix
Added `'total_minutes': 0` to both error return paths:

### Fixed Code:
```python
def decimal_hours_to_hours_minutes(decimal_hours: float) -> dict:
    if decimal_hours is None:
        return {'hours': 0, 'minutes': 0, 'formatted': '0:00', 'total_minutes': 0}  # ✅ Fixed
    
    try:
        decimal_hours = float(decimal_hours)
    except (ValueError, TypeError):
        return {'hours': 0, 'minutes': 0, 'formatted': '0:00', 'total_minutes': 0}  # ✅ Fixed
    
    # Normal path unchanged - already returns total_minutes
    hours = int(decimal_hours)
    minutes = round((decimal_hours - hours) * 60)
    
    return {
        'hours': hours,
        'minutes': minutes,
        'formatted': formatted,
        'total_minutes': hours * 60 + minutes  # ✅ Already correct
    }
```

## Testing Results

### Test Case 1: Normal Timesheet
- ✅ PDF upload successful
- ✅ Status: completed
- ✅ total_minutes field present: 480 (8 hours)

### Test Case 2: Edge Cases
- ✅ Handles None values without error
- ✅ Handles invalid decimal hours
- ✅ Returns consistent dict structure

### Backend Logs:
- ✅ No KeyError exceptions
- ✅ No traceback for 'total_minutes'
- ✅ Hot reload successful

## Impact
- **Fixed**: PDF extraction no longer crashes on edge cases
- **Consistency**: Function always returns same dict structure
- **Data Integrity**: Zero values used for invalid/missing data instead of crashes

## Related Code
This function is called from:
- `extract_timesheet_data()` - Line 1163-1174
- Creates `TimeEntry` objects with total_minutes field

## Files Modified
- `/app/backend/server.py` - Lines 65, 70 (added 'total_minutes': 0)

## Prevention
- All utility functions returning dicts should document their return structure
- Consider using TypedDict or dataclasses for structured returns
- Add unit tests for edge cases (None, invalid values, etc.)

## Status
✅ **FIXED** - Tested and verified working
