"""
Test script for time_utils functions
Tests all edge cases and formats
"""
import sys
sys.path.insert(0, '/app/backend')

from time_utils import (
    normalize_am_pm,
    parse_time_string,
    calculate_time_difference_minutes,
    calculate_units_from_times,
    format_time_12hr
)

def test_normalize_am_pm():
    """Test time normalization to 12-hour format"""
    print("\n" + "="*60)
    print("TEST: normalize_am_pm()")
    print("="*60)
    
    test_cases = [
        # (input, expected_output)
        ("321", "3:21 PM"),
        ("357", "3:57 PM"),
        ("830", "8:30 AM"),
        ("1145", "11:45 AM"),
        ("1800", "6:00 PM"),
        ("0830", "8:30 AM"),
        ("8:30", "8:30 AM"),
        ("8:30 AM", "8:30 AM"),
        ("18:00", "6:00 PM"),
        ("11:32 AM", "11:32 AM"),
        ("12:05 PM", "12:05 PM"),
        ("540pm", "5:40 PM"),
        ("6am", "6:00 AM"),
        ("12:00", "12:00 PM"),  # Assume noon
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected in test_cases:
        result = normalize_am_pm(input_str)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} '{input_str}' -> '{result}' (expected: '{expected}')")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_parse_time_string():
    """Test time string parsing"""
    print("\n" + "="*60)
    print("TEST: parse_time_string()")
    print("="*60)
    
    test_cases = [
        # (input, expected_hour, expected_minute)
        ("321", 15, 21),   # 3:21 PM
        ("357", 15, 57),   # 3:57 PM
        ("830", 8, 30),    # 8:30 AM
        ("1145", 11, 45),  # 11:45 AM
        ("1800", 18, 0),   # 6:00 PM (24-hour)
        ("8:30 AM", 8, 30),
        ("3:21 PM", 15, 21),
        ("11:32 AM", 11, 32),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, exp_hour, exp_minute in test_cases:
        result = parse_time_string(input_str)
        if result and result.hour == exp_hour and result.minute == exp_minute:
            passed += 1
            print(f"✅ '{input_str}' -> {result.hour:02d}:{result.minute:02d}")
        else:
            failed += 1
            actual = f"{result.hour:02d}:{result.minute:02d}" if result else "None"
            print(f"❌ '{input_str}' -> {actual} (expected: {exp_hour:02d}:{exp_minute:02d})")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_calculate_time_difference():
    """Test time difference calculation"""
    print("\n" + "="*60)
    print("TEST: calculate_time_difference_minutes()")
    print("="*60)
    
    test_cases = [
        # (time_in, time_out, expected_minutes)
        ("321", "357", 36),          # 3:21 PM to 3:57 PM = 36 minutes
        ("830", "1145", 195),        # 8:30 AM to 11:45 AM = 195 minutes (3.25 hours)
        ("8:30 AM", "5:30 PM", 540), # 8:30 AM to 5:30 PM = 9 hours = 540 minutes
        ("11:32 AM", "12:05 PM", 33), # 11:32 AM to 12:05 PM = 33 minutes
        ("9:00 AM", "5:00 PM", 480),  # 9:00 AM to 5:00 PM = 8 hours = 480 minutes
    ]
    
    passed = 0
    failed = 0
    
    for time_in, time_out, expected in test_cases:
        result = calculate_time_difference_minutes(time_in, time_out)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} '{time_in}' to '{time_out}' = {result} min (expected: {expected} min)")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_calculate_units():
    """Test units calculation with special rounding"""
    print("\n" + "="*60)
    print("TEST: calculate_units_from_times()")
    print("="*60)
    
    test_cases = [
        # (time_in, time_out, expected_units, expected_hours)
        ("321", "357", 3, 0.6),           # 36 minutes -> 3 units (special rule)
        ("8:30 AM", "11:45 AM", 13, 3.25), # 195 minutes -> 13 units
        ("11:32 AM", "12:05 PM", 2, 0.55), # 33 minutes -> 2 units
        ("9:00 AM", "5:00 PM", 32, 8.0),   # 480 minutes -> 32 units (8 hours)
        ("9:00 AM", "9:34 AM", 2, 0.57),   # 34 minutes -> 2 units (standard)
        ("9:00 AM", "9:35 AM", 3, 0.58),   # 35 minutes -> 3 units (special rule - CHANGED)
        ("9:00 AM", "9:36 AM", 3, 0.6),    # 36 minutes -> 3 units (special rule)
        ("9:00 AM", "9:45 AM", 3, 0.75),   # 45 minutes -> 3 units (exact)
        ("9:00 AM", "9:50 AM", 3, 0.83),   # 50 minutes -> 3 units (special rule)
        ("9:00 AM", "10:00 AM", 4, 1.0),   # 60 minutes -> 4 units (exact hour)
    ]
    
    passed = 0
    failed = 0
    
    for time_in, time_out, exp_units, exp_hours in test_cases:
        units, hours = calculate_units_from_times(time_in, time_out)
        units_ok = units == exp_units
        hours_ok = hours == exp_hours
        status = "✅" if (units_ok and hours_ok) else "❌"
        
        if units_ok and hours_ok:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{time_in}' to '{time_out}' = {units} units, {hours} hrs (expected: {exp_units} units, {exp_hours} hrs)")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COMPREHENSIVE TIME UTILS TESTING")
    print("="*60)
    
    all_passed = True
    
    all_passed &= test_normalize_am_pm()
    all_passed &= test_parse_time_string()
    all_passed &= test_calculate_time_difference()
    all_passed &= test_calculate_units()
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60)
