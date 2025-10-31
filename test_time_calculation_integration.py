#!/usr/bin/env python3
"""
Integration test for time calculation functionality
Tests the complete flow from time extraction to unit calculation
"""

import sys
import os
sys.path.append('/app/backend')

from time_utils import calculate_units_from_times, normalize_am_pm
from server import ExtractedData, EmployeeEntry, TimeEntry

def test_time_calculation_integration():
    """Test the complete time calculation integration"""
    print("🧪 Testing Time Calculation Integration")
    print("=" * 50)
    
    # Test cases with expected results
    test_cases = [
        {
            "name": "30 minutes (normal rounding)",
            "time_in": "8:00 AM",
            "time_out": "8:30 AM", 
            "expected_units": 2,
            "expected_hours": 0.5
        },
        {
            "name": "37 minutes (special rounding rule)",
            "time_in": "8:00 AM",
            "time_out": "8:37 AM",
            "expected_units": 3,
            "expected_hours": 0.62
        },
        {
            "name": "45 minutes (special rounding rule)",
            "time_in": "9:00 AM", 
            "time_out": "9:45 AM",
            "expected_units": 3,
            "expected_hours": 0.75
        },
        {
            "name": "60 minutes (normal rounding)",
            "time_in": "1:00 PM",
            "time_out": "2:00 PM",
            "expected_units": 4,
            "expected_hours": 1.0
        },
        {
            "name": "Time normalization test",
            "time_in": "8:30",  # Should be normalized to 8:30 AM
            "time_out": "5:45",  # Should be normalized to 5:45 PM
            "expected_units": 37,  # 9 hours 15 minutes = 555 minutes = 37 units (rounded)
            "expected_hours": 9.25
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"  Input: {test_case['time_in']} → {test_case['time_out']}")
        
        # Test time normalization
        normalized_in = normalize_am_pm(test_case['time_in'])
        normalized_out = normalize_am_pm(test_case['time_out'])
        print(f"  Normalized: {normalized_in} → {normalized_out}")
        
        # Test unit calculation
        units, hours = calculate_units_from_times(test_case['time_in'], test_case['time_out'])
        
        # Check results
        units_correct = units == test_case['expected_units']
        hours_correct = abs(hours - test_case['expected_hours']) < 0.01 if hours else False
        
        if units_correct and hours_correct:
            print(f"  ✅ PASSED: {units} units, {hours} hours")
        else:
            print(f"  ❌ FAILED: Got {units} units (expected {test_case['expected_units']}), {hours} hours (expected {test_case['expected_hours']})")
            all_passed = False
    
    # Test creating TimeEntry objects with calculated units
    print(f"\n🔧 Testing TimeEntry Creation with Unit Calculation")
    
    time_entry = TimeEntry(
        date="2024-01-15",
        time_in="8:00 AM",
        time_out="8:37 AM",
        hours_worked=None
    )
    
    # Simulate the unit calculation that happens in the extraction process
    normalized_time_in = normalize_am_pm(time_entry.time_in)
    normalized_time_out = normalize_am_pm(time_entry.time_out)
    units, calculated_hours = calculate_units_from_times(normalized_time_in, normalized_time_out)
    
    # Update the time entry (this is what happens in the server code)
    time_entry.time_in = normalized_time_in
    time_entry.time_out = normalized_time_out
    time_entry.hours_worked = str(calculated_hours) if calculated_hours is not None else None
    time_entry.units = units
    
    print(f"  TimeEntry created:")
    print(f"    Date: {time_entry.date}")
    print(f"    Time In: {time_entry.time_in}")
    print(f"    Time Out: {time_entry.time_out}")
    print(f"    Hours Worked: {time_entry.hours_worked}")
    print(f"    Units: {time_entry.units}")
    
    entry_correct = (time_entry.units == 3 and 
                    time_entry.time_in == "8:00 AM" and 
                    time_entry.time_out == "8:37 AM")
    
    if entry_correct:
        print(f"  ✅ TimeEntry creation PASSED")
    else:
        print(f"  ❌ TimeEntry creation FAILED")
        all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All time calculation integration tests PASSED!")
        return 0
    else:
        print("❌ Some time calculation integration tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(test_time_calculation_integration())