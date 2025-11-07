"""
Critical Regression Tests
These tests MUST pass before any deployment
Run with: pytest tests/test_critical_regression.py -v
"""
import pytest
import sys
sys.path.insert(0, '/app/backend')

from time_utils import normalize_am_pm, parse_time_string, calculate_units_from_times
from date_utils import parse_week_range, parse_date_with_context
from datetime import datetime, time

@pytest.mark.critical
@pytest.mark.time
class TestTimeParsingStability:
    """Ensure time parsing never breaks"""
    
    def test_all_time_formats_supported(self):
        """Test that ALL supported time formats still work"""
        test_cases = [
            # (input, expected_output with leading zeros)
            ("321", "03:21 PM"),
            ("357", "03:57 PM"),
            ("830", "08:30 AM"),
            ("1145", "11:45 AM"),
            ("1800", "06:00 PM"),
            ("0830", "08:30 AM"),
            ("8:30", "08:30 AM"),
            ("8:30 AM", "08:30 AM"),
            ("18:00", "06:00 PM"),
            ("11:32 AM", "11:32 AM"),
            ("12:05 PM", "12:05 PM"),
            ("540pm", "05:40 PM"),
            ("6am", "06:00 AM"),
        ]
        
        for input_time, expected in test_cases:
            result = normalize_am_pm(input_time)
            assert result == expected, \
                f"REGRESSION: Time parsing broke for '{input_time}' - got '{result}' expected '{expected}'"
    
    def test_special_rounding_rule(self):
        """Ensure >=35 min rounding to 3 units never breaks"""
        test_cases = [
            ("9:00 AM", "9:35 AM", 3),  # 35 min = 3 units (special rule - CHANGED)
            ("9:00 AM", "9:36 AM", 3),  # 36 min = 3 units (special rule)
            ("9:00 AM", "9:50 AM", 3),  # 50 min = 3 units (special rule)
            ("9:00 AM", "9:34 AM", 2),  # 34 min = 2 units (standard)
            ("9:00 AM", "10:00 AM", 4), # 60 min = 4 units (standard)
        ]
        
        for time_in, time_out, expected_units in test_cases:
            units, hours = calculate_units_from_times(time_in, time_out)
            assert units == expected_units, \
                f"REGRESSION: Unit calculation broke for {time_in} to {time_out} - got {units} expected {expected_units}"

@pytest.mark.critical
@pytest.mark.date
class TestDateParsingStability:
    """Ensure date parsing with week context never breaks"""
    
    def test_all_date_formats_supported(self):
        """Test that ALL supported date formats still work"""
        week_range = (datetime(2024, 10, 6), datetime(2024, 10, 12))
        
        test_cases = [
            ("10/6", "2024-10-06"),
            ("10-6", "2024-10-06"),
            ("6", "2024-10-06"),
            ("Sunday", "2024-10-06"),
            ("Monday", "2024-10-07"),
            ("Mon", "2024-10-07"),
            ("10/6/2024", "2024-10-06"),
        ]
        
        for input_date, expected in test_cases:
            result = parse_date_with_context(input_date, week_range)
            assert result == expected, \
                f"REGRESSION: Date parsing broke for '{input_date}' - got '{result}' expected '{expected}'"
    
    def test_week_range_parsing(self):
        """Ensure week range parsing still works"""
        test_cases = [
            ("10/6/2024 - 10/12/2024", "2024-10-06", "2024-10-12"),
            ("Week of 10/6/2024", "2024-10-06", "2024-10-12"),
        ]
        
        for week_str, exp_start, exp_end in test_cases:
            result = parse_week_range(week_str)
            assert result is not None, f"REGRESSION: Failed to parse week '{week_str}'"
            start_str = result[0].strftime("%Y-%m-%d")
            end_str = result[1].strftime("%Y-%m-%d")
            assert start_str == exp_start and end_str == exp_end, \
                f"REGRESSION: Week parsing broke for '{week_str}'"

@pytest.mark.critical
class TestCriticalCalculations:
    """Test critical business logic calculations"""
    
    def test_units_calculation_accuracy(self):
        """Ensure billing unit calculations are always accurate"""
        test_cases = [
            (15, 1),   # 15 minutes = 1 unit
            (30, 2),   # 30 minutes = 2 units
            (34, 2),   # 34 minutes = 2 units (standard rounding)
            (35, 3),   # 35 minutes = 3 units (special rule - CHANGED)
            (36, 3),   # 36 minutes = 3 units (special rule)
            (45, 3),   # 45 minutes = 3 units (exact)
            (59, 3),   # 59 minutes = 3 units (special rule)
            (60, 4),   # 60 minutes = 4 units
            (480, 32), # 8 hours = 32 units
        ]
        
        from time_utils import minutes_to_units_with_rounding
        
        for minutes, expected_units in test_cases:
            result = minutes_to_units_with_rounding(minutes)
            assert result == expected_units, \
                f"CRITICAL: Units calculation broke - {minutes} min should be {expected_units} units, got {result}"
    
    def test_hours_calculation_accuracy(self):
        """Ensure hours calculations are accurate"""
        from time_utils import calculate_time_difference_minutes
        
        test_cases = [
            ("8:00 AM", "4:00 PM", 480),   # 8 hours
            ("9:00 AM", "5:00 PM", 480),   # 8 hours
            ("8:30 AM", "5:30 PM", 540),   # 9 hours
            ("11:32 AM", "12:05 PM", 33),  # 33 minutes
        ]
        
        for time_in, time_out, expected_minutes in test_cases:
            result = calculate_time_difference_minutes(time_in, time_out)
            assert result == expected_minutes, \
                f"CRITICAL: Time difference broke - {time_in} to {time_out} should be {expected_minutes} min, got {result}"

@pytest.mark.critical
def test_time_utils_module_stability():
    """Ensure time_utils module exports all required functions"""
    from time_utils import (
        normalize_am_pm,
        parse_time_string,
        calculate_time_difference_minutes,
        calculate_units_from_times,
        minutes_to_units_with_rounding,
        format_time_12hr
    )
    
    # If this test fails, critical functions were removed or renamed
    assert callable(normalize_am_pm)
    assert callable(parse_time_string)
    assert callable(calculate_time_difference_minutes)
    assert callable(calculate_units_from_times)
    assert callable(minutes_to_units_with_rounding)
    assert callable(format_time_12hr)

@pytest.mark.critical
def test_date_utils_module_stability():
    """Ensure date_utils module exports all required functions"""
    from date_utils import (
        parse_week_range,
        parse_date_with_context,
        normalize_dates_in_extracted_data
    )
    
    # If this test fails, critical functions were removed or renamed
    assert callable(parse_week_range)
    assert callable(parse_date_with_context)
    assert callable(normalize_dates_in_extracted_data)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "critical"])
