"""
Time calculation utilities for timesheet processing
Handles time parsing, unit conversion, and special rounding rules
"""
from datetime import datetime, time
from typing import Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


def normalize_am_pm(time_str: str) -> str:
    """
    Normalize any time format to consistent 12-hour format with AM/PM
    Handles military time, malformed times, and mixed formats
    
    Rules:
    - All times converted to "H:MM AM/PM" format (no leading zero for hour)
    - Military time (e.g., 1800, 321) converted to 12-hour
    - Times 7:00-11:59 without AM/PM are assumed AM
    - Times 1:00-6:59 without AM/PM are assumed PM
    - 12:xx defaults to PM (noon) unless explicitly marked
    
    Returns:
        Normalized time string in "H:MM AM" or "H:MM PM" format
    """
    if not time_str:
        return time_str
    
    # Clean input - remove extra spaces and common OCR errors
    time_str = time_str.strip().replace('O', '0').replace('o', '0')
    
    # Filter out completely invalid inputs
    if re.search(r'[^0-9:apmAPM\s]', time_str):
        logger.warning(f"Cannot normalize invalid time: '{time_str}'")
        return time_str
    
    # Check for 1-4 digit format without colon (e.g., "6am", "321", "1145", "830", "1800")
    match_digits = re.match(r'^(\d{1,4})\s*(a|p|am|pm|AM|PM)?$', time_str, re.IGNORECASE)
    if match_digits:
        digits = match_digits.group(1)
        am_pm = match_digits.group(2)
        
        # Parse based on digit count
        if len(digits) == 1 or len(digits) == 2:  # e.g., "6" -> 6:00, "11" -> 11:00
            hour = int(digits)
            minute = 0
        elif len(digits) == 3:  # e.g., "321" -> 3:21, "830" -> 8:30
            hour = int(digits[0])
            minute = int(digits[1:])
        elif len(digits) == 4:  # e.g., "1145" -> 11:45, "1800" -> 18:00
            hour = int(digits[:2])
            minute = int(digits[2:])
        else:
            return time_str
        
        # Validate minute
        if minute > 59:
            logger.warning(f"Invalid minute in time: '{time_str}'")
            return time_str
        
        # Convert to 12-hour format
        if am_pm:
            # Use provided AM/PM
            am_pm = am_pm.upper()
            if am_pm in ['A', 'AM']:
                am_pm_str = 'AM'
                if hour == 12:
                    hour = 12  # 12 AM is midnight
            else:  # P or PM
                am_pm_str = 'PM'
                if hour < 12 and hour != 0:
                    hour = hour  # Keep as-is for 12-hour
        else:
            # Smart AM/PM logic
            if hour >= 13:  # Definitely 24-hour PM
                hour = hour - 12
                am_pm_str = 'PM'
            elif hour == 0:  # Midnight
                hour = 12
                am_pm_str = 'AM'
            elif 7 <= hour <= 11:  # Morning
                am_pm_str = 'AM'
            elif hour == 12:  # Noon
                am_pm_str = 'PM'
            elif 1 <= hour <= 6:  # Afternoon/Evening
                am_pm_str = 'PM'
            else:
                am_pm_str = 'PM'
        
        return f"{hour:02d}:{minute:02d} {am_pm_str}"
    
    # Check for format with colon (e.g., "8:30", "18:00", "8:30 AM")
    match = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?$', time_str, re.IGNORECASE)
    
    if not match:
        return time_str
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm_from_scan = match.group(3)
    
    # Validate minute
    if minute > 59:
        logger.warning(f"Invalid minute in time: '{time_str}'")
        return time_str
    
    # If hour >= 13, it's definitely 24-hour format
    if hour >= 13:
        hour = hour - 12
        am_pm_str = 'PM'
    elif hour == 0:
        hour = 12
        am_pm_str = 'AM'
    elif am_pm_from_scan:
        # Use provided AM/PM
        am_pm_str = am_pm_from_scan.upper()
        # Ensure hour is in correct range for 12-hour format
        if hour > 12:
            hour = hour - 12
    else:
        # Apply smart AM/PM logic
        if 7 <= hour <= 11:
            am_pm_str = 'AM'
        elif hour == 12:
            am_pm_str = 'PM'  # Default to noon
        elif 1 <= hour <= 6:
            am_pm_str = 'PM'
        else:
            am_pm_str = 'PM'
    
    return f"{hour}:{minute:02d} {am_pm_str}"


def parse_time_string(time_str: str) -> Optional[time]:
    """
    Parse time string to time object
    Handles various formats:
    - "8:30 AM", "08:30AM", "8:30"
    - Military time: "1800", "0830", "1345"
    - "18:00", "08:30" (24-hour with colon)
    - Malformed: "830am", "540pm", "6am", "321", "1145" (missing colons)
    """
    if not time_str:
        return None
    
    try:
        # Clean the input - remove extra spaces and common OCR errors
        time_str = time_str.strip().replace('O', '0').replace('o', '0')
        
        # Filter out completely invalid inputs (letters, special chars except : and AM/PM)
        if re.search(r'[^0-9:apmAPM\s]', time_str):
            logger.warning(f"Invalid time string with unexpected characters: '{time_str}'")
            return None
        
        # Handle malformed times without colons
        # Examples: "830am", "540pm", "6am", "1645", "321", "1145"
        
        # Check for formats like "540pm", "830am", "6pm", "705p", "321", "1145"
        match_no_colon = re.match(r'^(\d{1,4})\s*(a|p|am|pm|AM|PM)?$', time_str, re.IGNORECASE)
        if match_no_colon:
            digits = match_no_colon.group(1)
            am_pm = match_no_colon.group(2)
            
            # Normalize am_pm (handle 'a' and 'p' without 'm')
            if am_pm:
                am_pm = am_pm.upper()
                if am_pm == 'A':
                    am_pm = 'AM'
                elif am_pm == 'P':
                    am_pm = 'PM'
            
            # Parse based on digit count
            if len(digits) == 3:  # e.g., "540" -> 5:40, "830" -> 8:30, "321" -> 3:21
                hour = int(digits[0])
                minute = int(digits[1:])
            elif len(digits) == 4:  # e.g., "1645" -> 16:45, "0830" -> 08:30, "1145" -> 11:45
                hour = int(digits[:2])
                minute = int(digits[2:])
            elif len(digits) == 1 or len(digits) == 2:  # e.g., "6" -> 6:00, "11" -> 11:00
                hour = int(digits)
                minute = 0
            else:
                return None
            
            # Validate minute range
            if minute > 59:
                logger.warning(f"Invalid minute value: {minute} from '{time_str}'")
                return None
            
            # Apply AM/PM if provided, otherwise use smart logic
            if am_pm:
                if am_pm == 'PM' and hour < 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0
            else:
                # Smart AM/PM logic for times without indicator
                # For 3 or 4 digit times without AM/PM
                if hour >= 13:  # Definitely PM (military time)
                    pass  # Already in 24-hour format
                elif 7 <= hour <= 11:
                    pass  # Morning (AM)
                elif 1 <= hour <= 6:
                    hour += 12  # Afternoon/evening (PM)
                # hour 12 stays as-is (noon)
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour=hour, minute=minute)
        
        # Check for military time format (4 digits without colon)
        # Examples: "1800", "0830", "1345"
        if re.match(r'^\d{4}$', time_str):
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour=hour, minute=minute)
        
        # Normalize the time string first (adds AM/PM if needed)
        normalized = normalize_am_pm(time_str)
        
        # Try parsing with various formats
        for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S"]:
            try:
                dt = datetime.strptime(normalized, fmt)
                return dt.time()
            except ValueError:
                continue
        
        # Try 24-hour format without normalization
        for fmt in ["%H:%M", "%H:%M:%S"]:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.time()
            except ValueError:
                continue
        
        # If all formats fail, try extracting hour and minute
        match = re.match(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour=hour, minute=minute)
        
        return None
    except Exception as e:
        logger.error(f"Error parsing time string '{time_str}': {e}")
        return None


def calculate_time_difference_minutes(time_in: str, time_out: str) -> Optional[int]:
    """
    Calculate time difference in minutes between check-in and check-out
    
    Args:
        time_in: Check-in time string (e.g., "8:30 AM", "321", "0830")
        time_out: Check-out time string (e.g., "5:45 PM", "545", "1745")
    
    Returns:
        Time difference in minutes, or None if parsing fails
    """
    try:
        # Parse both times
        t_in = parse_time_string(time_in)
        t_out = parse_time_string(time_out)
        
        if not t_in or not t_out:
            logger.warning(f"Failed to parse times - In: '{time_in}' -> {t_in}, Out: '{time_out}' -> {t_out}")
            return None
        
        # Convert to minutes since midnight
        minutes_in = t_in.hour * 60 + t_in.minute
        minutes_out = t_out.hour * 60 + t_out.minute
        
        # Calculate difference
        # If check-out is "earlier" than check-in, assume it crosses midnight
        if minutes_out < minutes_in:
            # Crossed midnight
            diff = (24 * 60 - minutes_in) + minutes_out
        else:
            diff = minutes_out - minutes_in
        
        # Log calculation for debugging
        logger.debug(f"Time calc: {time_in} ({t_in.strftime('%H:%M')}) to {time_out} ({t_out.strftime('%H:%M')}) = {diff} minutes")
        
        return diff
    except Exception as e:
        logger.error(f"Error calculating time difference from '{time_in}' to '{time_out}': {e}")
        return None


def minutes_to_units_with_rounding(minutes: int) -> int:
    """
    Convert minutes to 15-minute units with special rounding rule
    
    Rules:
    - 1 unit = 15 minutes
    - Standard rounding: 0-7 mins = 0 units, 8-22 = 1 unit, 23-37 = 2 units, 38-52 = 3 units
    - SPECIAL RULE: If time worked is >= 35 minutes but < 60 minutes,
      round UP to 3 units (45 minutes) to ensure minimum billing
    - Examples:
      * 35 minutes = 3 units (special rule)
      * 36 minutes = 3 units (special rule)
      * 37 minutes = 3 units (special rule)
      * 45 minutes = 3 units (exact)
      * 50 minutes = 3 units (special rule)
      * 60 minutes = 4 units (exact hour)
    
    Args:
        minutes: Total minutes worked
    
    Returns:
        Number of 15-minute units
    """
    if minutes is None or minutes < 0:
        return 0
    
    # Special rounding rule: >= 35 minutes and < 60 minutes rounds UP to 3 units
    if 35 <= minutes < 60:
        logger.debug(f"Special rounding: {minutes} minutes -> 3 units (rule: >=35 and <60)")
        return 3
    
    # Standard rounding for other cases
    # Round to nearest 15-minute unit
    units = round(minutes / 15.0)
    
    logger.debug(f"Standard rounding: {minutes} minutes -> {units} units")
    
    return units


def calculate_units_from_times(time_in: str, time_out: str) -> Tuple[Optional[int], Optional[float]]:
    """
    Calculate billable units and hours from check-in and check-out times
    
    Args:
        time_in: Check-in time string (any format)
        time_out: Check-out time string (any format)
    
    Returns:
        Tuple of (units, hours) or (None, None) if calculation fails
    
    Example:
        calculate_units_from_times("321", "357") 
        -> (3, 0.6)  # 3:21 PM to 3:57 PM = 36 minutes = 3 units, 0.6 hours
    """
    try:
        # Calculate time difference in minutes
        minutes = calculate_time_difference_minutes(time_in, time_out)
        
        if minutes is None:
            logger.warning(f"Cannot calculate units - time parsing failed for: '{time_in}' to '{time_out}'")
            return None, None
        
        # Convert to units with special rounding
        units = minutes_to_units_with_rounding(minutes)
        
        # Calculate hours (for display purposes)
        hours = round(minutes / 60.0, 2)
        
        logger.info(f"Calculated: '{time_in}' to '{time_out}' = {minutes} min = {units} units = {hours} hrs")
        
        return units, hours
    except Exception as e:
        logger.error(f"Error calculating units from '{time_in}' to '{time_out}': {e}")
        return None, None


def format_time_12hr(time_obj: time) -> str:
    """
    Format time object to 12-hour format with AM/PM with leading zeros
    Examples: 08:30 AM, 12:00 PM, 05:45 PM
    """
    if not time_obj:
        return ""
    
    hour = time_obj.hour
    minute = time_obj.minute
    
    am_pm = "AM" if hour < 12 else "PM"
    
    # Convert to 12-hour format
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour = hour - 12
    
    # Format with leading zero for hours
    return f"{hour:02d}:{minute:02d} {am_pm}"
