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


def format_date_mm_dd_yyyy(date_str: str) -> str:
    """
    Convert a date string to MM/DD/YYYY format
    
    Args:
        date_str: Date in various formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
    
    Returns:
        Date in MM/DD/YYYY format
    """
    if not date_str:
        return date_str
    
    try:
        # Try YYYY-MM-DD format first
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%m/%d/%Y')
        
        # Try MM/DD/YYYY format (already correct)
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            dt = datetime.strptime(date_str, '%m/%d/%Y')
            return dt.strftime('%m/%d/%Y')
        
        # Try MM-DD-YYYY format
        if re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
            dt = datetime.strptime(date_str, '%m-%d-%Y')
            return dt.strftime('%m/%d/%Y')
        
        return date_str
    except Exception as e:
        logger.warning(f"Could not format date '{date_str}': {e}")
        return date_str


def infer_week_from_timesheets(timesheets: list) -> Optional[Tuple[datetime, datetime]]:
    """
    Infer week range from multiple timesheets by finding one with a valid week_of field
    
    Args:
        timesheets: List of timesheet dictionaries
    
    Returns:
        Tuple of (start_date, end_date) or None
    """
    for ts in timesheets:
        extracted = ts.get('extracted_data', {})
        if isinstance(extracted, dict):
            week_of = extracted.get('week_of')
            if week_of:
                week_range = parse_week_range(week_of)
                if week_range:
                    logger.info(f"Inferred week range from timesheet: {week_range[0].strftime('%m/%d/%Y')} - {week_range[1].strftime('%m/%d/%Y')}")
                    return week_range
    
    # Try to infer from dates in time entries
    all_dates = []
    for ts in timesheets:
        extracted = ts.get('extracted_data', {})
        if isinstance(extracted, dict):
            for emp in extracted.get('employee_entries', []):
                if isinstance(emp, dict):
                    for entry in emp.get('time_entries', []):
                        if isinstance(entry, dict):
                            date_str = entry.get('date', '')
                            # Try to parse complete dates
                            parsed = None
                            try:
                                if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                                    parsed = datetime.strptime(date_str, '%Y-%m-%d')
                                elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                                    parsed = datetime.strptime(date_str, '%m/%d/%Y')
                                elif re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
                                    parsed = datetime.strptime(date_str, '%m-%d-%Y')
                            except:
                                pass
                            if parsed:
                                all_dates.append(parsed)
    
    if all_dates:
        # Calculate week range from dates
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # Expand to full week (Sunday to Saturday)
        # Find the Sunday before or on min_date
        days_since_sunday = (min_date.weekday() + 1) % 7
        week_start = min_date - timedelta(days=days_since_sunday)
        
        # Find the Saturday after or on max_date
        days_until_saturday = (5 - max_date.weekday()) % 7
        week_end = max_date + timedelta(days=days_until_saturday)
        
        logger.info(f"Inferred week range from dates: {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}")
        return (week_start, week_end)
    
    return None


def cross_compare_and_fill_dates(timesheets: list, organization_id: str = None) -> list:
    """
    Cross-compare timesheets and fill in missing dates.
    Uses week context from other timesheets to infer dates.
    
    Timesheets are scanned weekly, so if one timesheet has a week_of field,
    we can use it to fill in dates for other timesheets in the same batch.
    
    Args:
        timesheets: List of timesheet dictionaries (extracted_data format)
        organization_id: Optional organization ID for logging
    
    Returns:
        List of timesheets with filled-in dates in MM/DD/YYYY format
    """
    if not timesheets:
        return timesheets
    
    logger.info(f"Cross-comparing {len(timesheets)} timesheets to fill missing dates")
    
    # Step 1: Find the week range from available data
    week_range = infer_week_from_timesheets(timesheets)
    
    if not week_range:
        logger.warning("Could not infer week range from any timesheet")
        return timesheets
    
    week_start, week_end = week_range
    logger.info(f"Using week range: {week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}")
    
    # Step 2: Build a mapping of day names/numbers to actual dates
    day_to_date = {}
    current = week_start
    while current <= week_end:
        # Map day number (1-31)
        day_to_date[str(current.day)] = current
        # Map day names
        day_name_full = current.strftime('%A').lower()  # monday, tuesday, etc.
        day_name_short = current.strftime('%a').lower()  # mon, tue, etc.
        day_to_date[day_name_full] = current
        day_to_date[day_name_short] = current
        # Map MM/DD format
        day_to_date[f"{current.month}/{current.day}"] = current
        day_to_date[f"{current.month:02d}/{current.day:02d}"] = current
        day_to_date[f"{current.month}-{current.day}"] = current
        current += timedelta(days=1)
    
    # Step 3: Process each timesheet and fill missing dates
    filled_count = 0
    for ts in timesheets:
        extracted = ts.get('extracted_data', {})
        if not isinstance(extracted, dict):
            continue
        
        # Set week_of if missing
        if not extracted.get('week_of'):
            extracted['week_of'] = f"{week_start.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}"
            logger.info(f"Filled in week_of: {extracted['week_of']}")
        
        for emp in extracted.get('employee_entries', []):
            if not isinstance(emp, dict):
                continue
            
            for entry in emp.get('time_entries', []):
                if not isinstance(entry, dict):
                    continue
                
                original_date = entry.get('date', '').strip()
                
                # Check if date is already complete (MM/DD/YYYY)
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', original_date):
                    # Already in correct format, just ensure proper formatting
                    entry['date'] = format_date_mm_dd_yyyy(original_date)
                    continue
                
                # Check if date is in YYYY-MM-DD format
                if re.match(r'^\d{4}-\d{2}-\d{2}$', original_date):
                    entry['date'] = format_date_mm_dd_yyyy(original_date)
                    continue
                
                # Try to infer date from context
                date_lower = original_date.lower()
                inferred_date = None
                
                # Check if it's a day name
                if date_lower in day_to_date:
                    inferred_date = day_to_date[date_lower]
                
                # Check if it's a partial date (MM/DD or MM-DD)
                elif re.match(r'^\d{1,2}[/-]\d{1,2}$', original_date):
                    # Extract month and day
                    parts = re.split(r'[/-]', original_date)
                    if len(parts) == 2:
                        month, day = int(parts[0]), int(parts[1])
                        # Find matching date in week range
                        current = week_start
                        while current <= week_end:
                            if current.month == month and current.day == day:
                                inferred_date = current
                                break
                            current += timedelta(days=1)
                        
                        # If not found in week, use week's year
                        if not inferred_date:
                            try:
                                inferred_date = datetime(week_start.year, month, day)
                            except ValueError:
                                pass
                
                # Check if it's just a day number
                elif re.match(r'^\d{1,2}$', original_date):
                    day_num = int(original_date)
                    # Find matching date in week range
                    current = week_start
                    while current <= week_end:
                        if current.day == day_num:
                            inferred_date = current
                            break
                        current += timedelta(days=1)
                
                # Apply the inferred date
                if inferred_date:
                    new_date = inferred_date.strftime('%m/%d/%Y')
                    logger.info(f"Filled date: '{original_date}' → '{new_date}'")
                    entry['date'] = new_date
                    entry['date_inferred'] = True
                    entry['original_date'] = original_date
                    filled_count += 1
                else:
                    # Keep original but note it couldn't be inferred
                    logger.warning(f"Could not infer date for: '{original_date}'")
                    entry['date_inference_failed'] = True
    
    logger.info(f"Filled {filled_count} missing dates across timesheets")
    return timesheets


async def fill_missing_dates_for_timesheet(timesheet_data: dict, db, organization_id: str) -> dict:
    """
    Fill missing dates for a single timesheet by cross-comparing with other 
    recent timesheets in the same organization.
    
    Args:
        timesheet_data: The timesheet's extracted_data dictionary
        db: Database connection
        organization_id: Organization ID to filter timesheets
    
    Returns:
        Updated timesheet_data with filled dates
    """
    from datetime import datetime, timezone
    
    # Get recent timesheets from the same organization (last 7 days)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    
    try:
        recent_timesheets = await db.timesheets.find({
            "organization_id": organization_id,
            "created_at": {"$gte": cutoff_date.isoformat()}
        }, {"_id": 0, "extracted_data": 1, "week_of": 1}).to_list(100)
        
        # Add current timesheet to the list for processing
        all_timesheets = [{"extracted_data": timesheet_data}] + recent_timesheets
        
        # Cross-compare and fill dates
        filled = cross_compare_and_fill_dates(all_timesheets, organization_id)
        
        # Return the first timesheet (the one we're processing)
        if filled and filled[0].get('extracted_data'):
            return filled[0]['extracted_data']
        
        return timesheet_data
    except Exception as e:
        logger.error(f"Error filling missing dates: {e}")
        return timesheet_data
