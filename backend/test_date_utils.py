"""
Test script for date_utils functions
Tests date parsing with various formats and week contexts
"""
import sys
sys.path.insert(0, '/app/backend')

from date_utils import parse_week_range, parse_date_with_context, normalize_dates_in_extracted_data
from datetime import datetime

def test_parse_week_range():
    """Test week range parsing"""
    print("\n" + "="*60)
    print("TEST: parse_week_range()")
    print("="*60)
    
    test_cases = [
        # (input, expected_start, expected_end)
        ("10/6/2024 - 10/12/2024", "2024-10-06", "2024-10-12"),
        ("10-6-2024 - 10-12-2024", "2024-10-06", "2024-10-12"),
        ("10/6 - 10/12", "2024-10-06", "2024-10-12"),  # Assumes 2024
        ("10-6 to 10-12", "2024-10-06", "2024-10-12"),
        ("Week of 10/6/2024", "2024-10-06", "2024-10-12"),
        ("Week of 10/6", "2024-10-06", "2024-10-12"),
        ("Week starting 10/6/2024", "2024-10-06", "2024-10-12"),
        ("Week ending 10/12/2024", "2024-10-06", "2024-10-12"),
        ("Week ending 10/12", "2024-10-06", "2024-10-12"),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, exp_start, exp_end in test_cases:
        result = parse_week_range(input_str)
        if result:
            start_str = result[0].strftime("%Y-%m-%d")
            end_str = result[1].strftime("%Y-%m-%d")
            status = "✅" if (start_str == exp_start and end_str == exp_end) else "❌"
            if status == "✅":
                passed += 1
            else:
                failed += 1
            print(f"{status} '{input_str}' → {start_str} to {end_str} (expected: {exp_start} to {exp_end})")
        else:
            failed += 1
            print(f"❌ '{input_str}' → None (expected: {exp_start} to {exp_end})")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_parse_date_with_context():
    """Test date parsing with week context"""
    print("\n" + "="*60)
    print("TEST: parse_date_with_context()")
    print("="*60)
    
    # Create a week range for context: Oct 6-12, 2024 (Sunday to Saturday)
    week_range = (datetime(2024, 10, 6), datetime(2024, 10, 12))
    
    test_cases = [
        # (input, week_range, expected_output)
        ("2024-10-06", week_range, "2024-10-06"),  # Already formatted
        ("10/6/2024", week_range, "2024-10-06"),    # Full date
        ("10/6", week_range, "2024-10-06"),         # MM/DD with context
        ("10-6", week_range, "2024-10-06"),         # MM-DD with context
        ("6", week_range, "2024-10-06"),            # Day number (6th is in range)
        ("7", week_range, "2024-10-07"),            # Day number (7th is in range)
        ("12", week_range, "2024-10-12"),           # Day number (12th is in range)
        ("Sunday", week_range, "2024-10-06"),       # Day name (Sunday = Oct 6)
        ("Monday", week_range, "2024-10-07"),       # Day name (Monday = Oct 7)
        ("Tuesday", week_range, "2024-10-08"),      # Day name
        ("Wednesday", week_range, "2024-10-09"),    # Day name
        ("Thursday", week_range, "2024-10-10"),     # Day name
        ("Friday", week_range, "2024-10-11"),       # Day name
        ("Saturday", week_range, "2024-10-12"),     # Day name
        ("Sun", week_range, "2024-10-06"),          # Short day name
        ("Mon", week_range, "2024-10-07"),          # Short day name
        ("Tue", week_range, "2024-10-08"),          # Short day name
        ("Wed", week_range, "2024-10-09"),          # Short day name
        ("Thu", week_range, "2024-10-10"),          # Short day name
        ("Fri", week_range, "2024-10-11"),          # Short day name
        ("Sat", week_range, "2024-10-12"),          # Short day name
    ]
    
    passed = 0
    failed = 0
    
    for input_str, ctx, expected in test_cases:
        result = parse_date_with_context(input_str, ctx)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} '{input_str}' → '{result}' (expected: '{expected}')")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_normalize_dates_in_extracted_data():
    """Test full date normalization in extracted data"""
    print("\n" + "="*60)
    print("TEST: normalize_dates_in_extracted_data()")
    print("="*60)
    
    test_data = {
        "client_name": "Test Patient",
        "week_of": "Week of 10/6/2024",
        "employee_entries": [
            {
                "employee_name": "John Doe",
                "service_code": "TEST",
                "time_entries": [
                    {"date": "Sunday", "time_in": "8:00 AM", "time_out": "4:00 PM"},
                    {"date": "Monday", "time_in": "8:00 AM", "time_out": "4:00 PM"},
                    {"date": "10/8", "time_in": "8:00 AM", "time_out": "4:00 PM"},
                    {"date": "9", "time_in": "8:00 AM", "time_out": "4:00 PM"},
                    {"date": "10-10", "time_in": "8:00 AM", "time_out": "4:00 PM"},
                ]
            }
        ]
    }
    
    expected_dates = ["2024-10-06", "2024-10-07", "2024-10-08", "2024-10-09", "2024-10-10"]
    
    result = normalize_dates_in_extracted_data(test_data)
    
    actual_dates = [
        entry["date"] 
        for emp in result["employee_entries"] 
        for entry in emp["time_entries"]
    ]
    
    print(f"Week context: {test_data['week_of']}")
    print(f"\nOriginal dates: Sunday, Monday, 10/8, 9, 10-10")
    print(f"Normalized dates: {actual_dates}")
    print(f"Expected dates:   {expected_dates}")
    
    all_match = actual_dates == expected_dates
    if all_match:
        print("\n✅ ALL DATES NORMALIZED CORRECTLY")
        return True
    else:
        print("\n❌ SOME DATES INCORRECT")
        for i, (actual, expected) in enumerate(zip(actual_dates, expected_dates)):
            status = "✅" if actual == expected else "❌"
            print(f"{status} Date {i+1}: {actual} (expected: {expected})")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COMPREHENSIVE DATE UTILS TESTING")
    print("="*60)
    
    all_passed = True
    
    all_passed &= test_parse_week_range()
    all_passed &= test_parse_date_with_context()
    all_passed &= test_normalize_dates_in_extracted_data()
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL DATE PARSING TESTS PASSED!")
    else:
        print("❌ SOME DATE PARSING TESTS FAILED")
    print("="*60)
