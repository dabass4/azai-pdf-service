"""
Date parsing utilities for timesheet processing
Handles various date formats with week context
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


def parse_week_range(week_str: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Parse week range string to get start and end dates
    
    Examples:
        "10/6/2024 - 10/12/2024" → (2024-10-06, 2024-10-12)
        "10-6 to 10-12" → (current_year-10-06, current_year-10-12)
        "Week of 10/6" → (2024-10-06, 2024-10-12) # Sunday to Saturday
        "Week ending 10/12" → (2024-10-06, 2024-10-12)
        "10/6 - 10/12" → (current_year-10-06, current_year-10-12)
    
    Returns:
        Tuple of (start_date, end_date) as datetime objects, or None if parsing fails
    """
    if not week_str:
        return None
    
    try:
        # Pattern 1: "10/6/2024 - 10/12/2024" or "10-6-2024 - 10-12-2024"
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*[-–to]+\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', week_str)
        if match:
            m1, d1, y1, m2, d2, y2 = match.groups()
            start = datetime(int(y1), int(m1), int(d1))
            end = datetime(int(y2), int(m2), int(d2))
            return (start, end)
        
        # Pattern 2: "10/6 - 10/12" or "10-6 to 10-12" (assume current or recent year)
        match = re.search(r'(\d{1,2})[/-](\d{1,2})\s*[-–to]+\s*(\d{1,2})[/-](\d{1,2})', week_str)
        if match:
            m1, d1, m2, d2 = match.groups()
            # Use current year, or previous year if date is in future
            now = datetime.now()
            year = now.year
            start = datetime(year, int(m1), int(d1))
            end = datetime(year, int(m2), int(d2))
            
            # If dates are in future by more than 1 month, assume previous year
            if start > now + timedelta(days=30):
                start = datetime(year - 1, int(m1), int(d1))
                end = datetime(year - 1, int(m2), int(d2))
            
            return (start, end)
        
        # Pattern 3: "Week of 10/6" or "Week of 10/6/2024"
        match = re.search(r'(?:week\s+of|week\s+starting)\s+(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?', week_str, re.IGNORECASE)
        if match:
            month, day, year = match.groups()
            year = int(year) if year else datetime.now().year
            start = datetime(year, int(month), int(day))
            
            # Check if date is in future, if so use previous year
            if start > datetime.now() + timedelta(days=30):
                start = datetime(year - 1, int(month), int(day))
            
            # Week is 7 days
            end = start + timedelta(days=6)
            return (start, end)
        
        # Pattern 4: "Week ending 10/12" or "Week ending 10/12/2024"
        match = re.search(r'(?:week\s+ending|ending)\s+(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?', week_str, re.IGNORECASE)
        if match:
            month, day, year = match.groups()
            year = int(year) if year else datetime.now().year
            end = datetime(year, int(month), int(day))
            
            # Check if date is in future, if so use previous year
            if end > datetime.now() + timedelta(days=30):
                end = datetime(year - 1, int(month), int(day))
            
            # Week is 7 days back
            start = end - timedelta(days=6)
            return (start, end)
        
        return None
    except Exception as e:
        logger.error(f"Error parsing week range '{week_str}': {e}")
        return None


def parse_date_with_context(date_str: str, week_range: Optional[Tuple[datetime, datetime]] = None) -> Optional[str]:
    """
    Parse date string with week context to get full YYYY-MM-DD date
    
    Args:
        date_str: Date string from timesheet (e.g., "10/6", "Monday", "Mon", "6", "10-6")
        week_range: Tuple of (start_date, end_date) from parse_week_range
    
    Returns:
        Date string in YYYY-MM-DD format, or None if parsing fails
    
    Examples:
        parse_date_with_context("10/6", week_range) → "2024-10-06"
        parse_date_with_context("Monday", week_range) → "2024-10-06" (if Monday is 10/6)
        parse_date_with_context("6", week_range) → "2024-10-06" (if 6th is in week range)
    """
    if not date_str:
        return None
    
    try:
        date_str = date_str.strip()
        
        # Pattern 1: Already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # Pattern 2: MM/DD/YYYY or MM-DD-YYYY
        match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', date_str)
        if match:
            month, day, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # Pattern 3: MM/DD or MM-DD (use week context or current year)
        match = re.match(r'^(\d{1,2})[/-](\d{1,2})$', date_str)
        if match:
            month, day = match.groups()
            year = datetime.now().year
            
            # If week_range provided, use its year
            if week_range:
                year = week_range[0].year
            
            # Check if date is in future by more than 1 month
            parsed_date = datetime(year, int(month), int(day))
            if parsed_date > datetime.now() + timedelta(days=30):
                year -= 1
                parsed_date = datetime(year, int(month), int(day))
            
            return parsed_date.strftime("%Y-%m-%d")
        
        # Pattern 4: Day name (Monday, Mon, M) - use week context
        if week_range:
            # Map day names to weekday numbers (0=Monday, 6=Sunday in Python)
            day_names_full = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day_names_short = {
                'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
                'fri': 4, 'sat': 5, 'sun': 6
            }
            
            date_lower = date_str.lower()
            target_weekday = None
            
            # Check full name
            if date_lower in day_names_full:
                target_weekday = day_names_full[date_lower]
            # Check short name
            elif date_lower in day_names_short:
                target_weekday = day_names_short[date_lower]
            
            if target_weekday is not None:
                # Find the date in the week range that matches this weekday
                current_date = week_range[0]
                while current_date <= week_range[1]:
                    if current_date.weekday() == target_weekday:
                        return current_date.strftime("%Y-%m-%d")
                    current_date += timedelta(days=1)
        
        # Pattern 5: Just a day number (1-31) - use week context
        match = re.match(r'^(\d{1,2})$', date_str)
        if match and week_range:
            day_num = int(match.group(1))
            
            # Find the date in the week range that matches this day
            current_date = week_range[0]
            while current_date <= week_range[1]:
                if current_date.day == day_num:
                    return current_date.strftime("%Y-%m-%d")
                current_date += timedelta(days=1)
            
            # If not found in range, use the month from week start
            year = week_range[0].year
            month = week_range[0].month
            try:
                date_obj = datetime(year, month, day_num)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                # Invalid day for month
                pass
        
        # If we have week context but no match, try to extract any number as day
        if week_range:
            numbers = re.findall(r'\d+', date_str)
            if numbers:
                day_num = int(numbers[0])
                current_date = week_range[0]
                while current_date <= week_range[1]:
                    if current_date.day == day_num:
                        return current_date.strftime("%Y-%m-%d")
                    current_date += timedelta(days=1)
        
        logger.warning(f"Could not parse date string: '{date_str}'")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        return None


def normalize_dates_in_extracted_data(extracted_data: dict) -> dict:
    """
    Normalize all dates in extracted data using week context
    
    Args:
        extracted_data: Dictionary with extracted timesheet data
    
    Returns:
        Modified extracted_data with normalized dates
    """
    # Parse week range if available
    week_range = None
    if extracted_data.get('week_of'):
        week_range = parse_week_range(extracted_data['week_of'])
        if week_range:
            logger.info(f"Parsed week range: {week_range[0].strftime('%Y-%m-%d')} to {week_range[1].strftime('%Y-%m-%d')}")
    
    # Process each employee's time entries
    if extracted_data.get('employee_entries'):
        for employee in extracted_data['employee_entries']:
            if employee.get('time_entries'):
                for entry in employee['time_entries']:
                    original_date = entry.get('date')
                    if original_date:
                        normalized_date = parse_date_with_context(original_date, week_range)
                        if normalized_date:
                            logger.debug(f"Normalized date: '{original_date}' → '{normalized_date}'")
                            entry['date'] = normalized_date
                        else:
                            logger.warning(f"Could not normalize date: '{original_date}'")
    
    return extracted_data
