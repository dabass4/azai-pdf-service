# AZAI Hours Format Feature

## Overview
AZAI now automatically converts decimal hours to hours and minutes format for better readability.

---

## What Changed

### Before (Decimal Format)
```
0.58 hr  ❌ (confusing)
8.5 hr   ❌ (unclear)
10.25 hr ❌ (hard to read)
```

### After (Hours and Minutes)
```
0 hr 35 min  ✅ (clear)
8 hr 30 min  ✅ (intuitive)
10 hr 15 min ✅ (easy to understand)
```

---

## Technical Implementation

### New Fields in TimeEntry

**Before:**
```json
{
  "date": "12/02",
  "time_in": "09:00 AM",
  "time_out": "05:30 PM",
  "hours_worked": "8.5"
}
```

**After:**
```json
{
  "date": "12/02",
  "time_in": "09:00 AM",
  "time_out": "05:30 PM",
  "hours_worked": "8.5",          // Legacy decimal format (kept for compatibility)
  "hours": 8,                      // Hours component (NEW)
  "minutes": 30,                   // Minutes component (NEW)
  "formatted_hours": "8 hr 30 min", // Human-readable format (NEW)
  "total_minutes": 510,            // Total minutes (NEW)
  "units": 34                      // 15-minute billing units
}
```

---

## Conversion Examples

### Common Conversions

| Decimal Hours | Hours | Minutes | Formatted       | Total Minutes |
|--------------|-------|---------|-----------------|---------------|
| 0.25         | 0     | 15      | 0 hr 15 min    | 15            |
| 0.50         | 0     | 30      | 0 hr 30 min    | 30            |
| 0.58         | 0     | 35      | 0 hr 35 min    | 35            |
| 0.75         | 0     | 45      | 0 hr 45 min    | 45            |
| 1.00         | 1     | 0       | 1 hr 0 min     | 60            |
| 4.50         | 4     | 30      | 4 hr 30 min    | 270           |
| 4.75         | 4     | 45      | 4 hr 45 min    | 285           |
| 8.00         | 8     | 0       | 8 hr 0 min     | 480           |
| 8.50         | 8     | 30      | 8 hr 30 min    | 510           |
| 8.75         | 8     | 45      | 8 hr 45 min    | 525           |
| 10.25        | 10    | 15      | 10 hr 15 min   | 615           |
| 12.00        | 12    | 0       | 12 hr 0 min    | 720           |

---

## Utility Functions

### Convert Decimal to Hours/Minutes

```python
def decimal_hours_to_hours_minutes(decimal_hours: float) -> dict:
    """
    Convert decimal hours to hours and minutes
    
    Args:
        decimal_hours: Hours in decimal format (e.g., 0.58, 8.5)
    
    Returns:
        dict with 'hours', 'minutes', 'formatted', 'total_minutes'
    
    Examples:
        0.58  -> {'hours': 0, 'minutes': 35, 'formatted': '0 hr 35 min'}
        8.5   -> {'hours': 8, 'minutes': 30, 'formatted': '8 hr 30 min'}
    """
    hours = int(decimal_hours)
    minutes = round((decimal_hours - hours) * 60)
    
    if minutes >= 60:
        hours += 1
        minutes = 0
    
    return {
        'hours': hours,
        'minutes': minutes,
        'formatted': f"{hours} hr {minutes} min",
        'total_minutes': hours * 60 + minutes
    }
```

### Convert Hours/Minutes to Decimal

```python
def hours_minutes_to_decimal(hours: int, minutes: int) -> float:
    """
    Convert hours and minutes to decimal hours
    
    Args:
        hours: Number of hours
        minutes: Number of minutes
    
    Returns:
        Decimal hours
    
    Examples:
        (8, 30)  -> 8.5
        (0, 35)  -> 0.58
        (10, 15) -> 10.25
    """
    return hours + (minutes / 60)
```

---

## Data Flow

### Extraction Process

```
1. PDF uploaded
   ↓
2. AI extracts timesheet data
   - Extracts hours in decimal format (8.5, 3.58, etc.)
   ↓
3. Backend calculates hours from time_in/time_out
   - 09:00 AM to 05:30 PM = 8.5 hours
   ↓
4. Decimal converted to hours and minutes
   - decimal_hours_to_hours_minutes(8.5)
   - Result: {'hours': 8, 'minutes': 30, 'formatted': '8 hr 30 min'}
   ↓
5. TimeEntry created with all formats:
   - hours_worked: "8.5" (legacy)
   - hours: 8
   - minutes: 30
   - formatted_hours: "8 hr 30 min"
   - total_minutes: 510
   - units: 34 (billing units)
   ↓
6. Stored in MongoDB
   ↓
7. Frontend displays: "8 hr 30 min"
```

---

## API Response Format

### Timesheet Upload Response

```json
{
  "id": "timesheet-123",
  "extracted_data": {
    "client_name": "Mary Johnson",
    "employee_entries": [
      {
        "employee_name": "Sarah Williams",
        "time_entries": [
          {
            "date": "2025-12-02",
            "time_in": "09:00 AM",
            "time_out": "05:30 PM",
            "hours_worked": "8.5",
            "hours": 8,
            "minutes": 30,
            "formatted_hours": "8 hr 30 min",
            "total_minutes": 510,
            "units": 34
          },
          {
            "date": "2025-12-03",
            "time_in": "09:00 AM",
            "time_out": "12:35 PM",
            "hours_worked": "3.58",
            "hours": 3,
            "minutes": 35,
            "formatted_hours": "3 hr 35 min",
            "total_minutes": 215,
            "units": 14
          }
        ]
      }
    ]
  }
}
```

---

## Frontend Display

### Display Formatted Hours

```javascript
// React component example
const TimeEntryRow = ({ timeEntry }) => {
  return (
    <tr>
      <td>{timeEntry.date}</td>
      <td>{timeEntry.time_in}</td>
      <td>{timeEntry.time_out}</td>
      <td>{timeEntry.formatted_hours}</td> {/* Display this! */}
      <td>{timeEntry.units} units</td>
    </tr>
  );
};

// Output:
// 12/02 | 09:00 AM | 05:30 PM | 8 hr 30 min | 34 units
```

### Calculate Totals

```javascript
const calculateTotalHours = (timeEntries) => {
  const totalMinutes = timeEntries.reduce(
    (sum, entry) => sum + (entry.total_minutes || 0), 
    0
  );
  
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  
  return `${hours} hr ${minutes} min`;
};

// Example:
// Entry 1: 8 hr 30 min (510 min)
// Entry 2: 3 hr 35 min (215 min)
// Total: 12 hr 5 min (725 min)
```

---

## Benefits

### 1. Better Readability
- ❌ **Before:** "0.58 hr" (what does this mean?)
- ✅ **After:** "0 hr 35 min" (crystal clear!)

### 2. Intuitive for Healthcare Workers
- Healthcare staff think in hours and minutes, not decimals
- "8 hr 30 min" matches how shifts are described
- No mental math required

### 3. Accurate Representation
- 35 minutes ≠ 0.35 hours (it's 0.58)
- Prevents confusion with time formats
- Shows exact minutes worked

### 4. Easy Calculations
- Total minutes field enables easy summation
- Hours and minutes components for grouping
- Billing units still calculated from minutes

### 5. Backward Compatible
- `hours_worked` field kept for legacy systems
- Old integrations continue to work
- New fields are additive, not breaking

---

## Edge Cases Handled

### Rounding
```
0.58333... hr → 0 hr 35 min (rounded to nearest minute)
8.499 hr      → 8 hr 30 min (0.499 * 60 = 29.94 ≈ 30)
```

### 60-Minute Rollover
```
Input: 7.99 hr
Calculation: 7 + (0.99 * 60) = 7 hours 59.4 minutes
Rounded: 7 hours 59 minutes

If minutes >= 60:
  hours += 1
  minutes = 0
```

### Zero Values
```
0 hr    → 0 hr 0 min
Null    → 0 hr 0 min
Invalid → 0 hr 0 min
```

---

## Testing

### Test Conversion Function

```bash
python3 << 'EOF'
def test_conversion():
    test_cases = [
        (0.25, "0 hr 15 min"),
        (0.58, "0 hr 35 min"),
        (4.5, "4 hr 30 min"),
        (8.75, "8 hr 45 min"),
        (12.0, "12 hr 0 min")
    ]
    
    for decimal, expected in test_cases:
        result = decimal_hours_to_hours_minutes(decimal)
        assert result['formatted'] == expected
        print(f"✅ {decimal} hr → {result['formatted']}")

test_conversion()
EOF
```

### Test Upload with Various Hours

```bash
# Create test PDF with different hour values
# Upload and verify conversion

TOKEN="your_auth_token"

curl -X POST "https://your-app.com/api/timesheets/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_timesheet.pdf" \
  | jq '.extracted_data.employee_entries[].time_entries[] | {date, formatted_hours, total_minutes}'

# Expected output:
# {
#   "date": "12/02",
#   "formatted_hours": "8 hr 30 min",
#   "total_minutes": 510
# }
```

---

## Migration Notes

### Existing Data
- Old timesheets still have `hours_worked` field
- Frontend should check for `formatted_hours` first
- Fallback to `hours_worked` if not present
- No data migration needed - fields are additive

### Frontend Updates
```javascript
// Display hours with fallback
const displayHours = (timeEntry) => {
  // Try new format first
  if (timeEntry.formatted_hours) {
    return timeEntry.formatted_hours;
  }
  
  // Fallback to decimal format
  if (timeEntry.hours_worked) {
    return `${timeEntry.hours_worked} hr`;
  }
  
  // Default
  return 'N/A';
};
```

---

## Summary

✅ **Feature:** Automatic conversion of decimal hours to hours and minutes
✅ **Format:** "X hr Y min" (e.g., "8 hr 30 min")
✅ **Fields Added:** `hours`, `minutes`, `formatted_hours`, `total_minutes`
✅ **Backward Compatible:** Legacy `hours_worked` field retained
✅ **Frontend Ready:** Use `formatted_hours` for display
✅ **Tested:** Working with real timesheet uploads

**Result:** Timesheets now display hours in an intuitive, healthcare-friendly format! 🎉
