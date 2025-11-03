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
    Normalize AM/PM in time string using system logic
    Handles military time format (e.g., 1800 → 6:00 PM)
    
    Rules:
    - Times 7:00-11:59 without AM/PM are assumed AM
    - Times 12:00-6:59 without clear indicator use context
    - Times 1:00-6:59 are typically PM for end times
    - Military time (e.g., 1800) converted to 12-hour with AM/PM
    """
    if not time_str:
        return time_str
    
    # Remove extra spaces
    time_str = time_str.strip()
    
    # Check for military time format (4 digits without colon)
    if re.match(r'^\d{4}$', time_str):
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        
        # Convert 24-hour to 12-hour with AM/PM
        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        else:
            return f"{hour-12}:{minute:02d} PM"
    
    # Check for 24-hour format with colon (e.g., "18:00")
    match_24hr = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if match_24hr:
        hour = int(match_24hr.group(1))
        minute = int(match_24hr.group(2))
        
        if hour >= 13 or hour == 0:  # Definitely 24-hour format
            if hour == 0:
                return f"12:{minute:02d} AM"
            elif hour < 12:
                return f"{hour}:{minute:02d} AM"
            elif hour == 12:
                return f"12:{minute:02d} PM"
            else:
                return f"{hour-12}:{minute:02d} PM"
    
    # Extract hour and minute from 12-hour format
    # Match patterns like "8:30", "08:30", "8:30AM", "8:30 AM", etc.
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', time_str, re.IGNORECASE)
    
    if not match:
        return time_str
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm_from_scan = match.group(3)
    
    # Apply system logic for AM/PM determination
    # Times 12-6 could be AM or PM, but we'll use smart defaults
    
    if hour >= 7 and hour <= 11:
        # Morning times: 7 AM - 11 AM
        am_pm = "AM"
    elif hour == 12:
        # Noon or Midnight - use scanned value if available, otherwise assume PM (noon)
        am_pm = "PM" if not am_pm_from_scan else am_pm_from_scan.upper()
    elif hour >= 1 and hour <= 6:
        # Afternoon/Evening: 1 PM - 6 PM (typical work hours)
        am_pm = "PM"
    else:
        # Use scanned AM/PM if available
        am_pm = am_pm_from_scan.upper() if am_pm_from_scan else "PM"
    
    return f"{hour}:{minute:02d} {am_pm}"


def parse_time_string(time_str: str) -> Optional[time]:
    """
    Parse time string to time object
    Handles various formats:
    - "8:30 AM", "08:30AM", "8:30"
    - Military time: "1800", "0830", "1345"
    - "18:00", "08:30" (24-hour with colon)
    - Malformed: "830am", "540pm", "6am" (missing colons)
    """
    if not time_str:
        return None
    
    try:
        # Clean the input
        time_str = time_str.strip()
        
        # Handle malformed times without colons
        # Examples: "830am", "540pm", "6am", "1645"
        
        # Check for formats like "540pm", "830am", "6pm"
        match_no_colon = re.match(r'^(\d{1,4})\s*(am|pm|AM|PM)?$', time_str, re.IGNORECASE)
        if match_no_colon:
            digits = match_no_colon.group(1)
            am_pm = match_no_colon.group(2)
            
            # Parse based on digit count
            if len(digits) == 3:  # e.g., "540" or "830"
                hour = int(digits[0])
                minute = int(digits[1:])
            elif len(digits) == 4:  # e.g., "1645" or "0830"
                hour = int(digits[:2])
                minute = int(digits[2:])
            elif len(digits) == 1 or len(digits) == 2:  # e.g., "6" or "11"
                hour = int(digits)
                minute = 0
            else:
                return None
            
            # Apply AM/PM if provided, otherwise use smart logic
            if am_pm:
                if am_pm.upper() == 'PM' and hour < 12:
                    hour += 12
                elif am_pm.upper() == 'AM' and hour == 12:
                    hour = 0
            else:
                # Smart AM/PM logic for times without indicator
                if 7 <= hour <= 11:
                    pass  # Morning
                elif 1 <= hour <= 6:
                    hour += 12  # Afternoon/evening
            
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
        time_in: Check-in time string (e.g., "8:30 AM")
        time_out: Check-out time string (e.g., "5:45 PM")
    
    Returns:
        Time difference in minutes, or None if parsing fails
    """
    try:
        # Parse both times
        t_in = parse_time_string(time_in)
        t_out = parse_time_string(time_out)
        
        if not t_in or not t_out:
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
        
        return diff
    except Exception as e:
        logger.error(f"Error calculating time difference: {e}")
        return None


def minutes_to_units_with_rounding(minutes: int) -> int:
    """
    Convert minutes to 15-minute units with special rounding rule
    
    Rules:
    - 1 unit = 15 minutes
    - Standard rounding: 0-7 mins = 0 units, 8-22 = 1 unit, 23-37 = 2 units, etc.
    - SPECIAL RULE: If time worked is > 35 minutes but < 60 minutes (2.33-3.99 units),
      round UP to 3 units (45 minutes)
    
    Args:
        minutes: Total minutes worked
    
    Returns:
        Number of 15-minute units
    """
    if minutes is None or minutes < 0:
        return 0
    
    # Special rounding rule: > 35 minutes and < 60 minutes rounds to 3 units
    if 35 < minutes < 60:
        return 3
    
    # Standard rounding for other cases
    # Round to nearest 15-minute unit
    units = round(minutes / 15.0)
    
    return units


def calculate_units_from_times(time_in: str, time_out: str) -> Tuple[Optional[int], Optional[float]]:
    """
    Calculate billable units and hours from check-in and check-out times
    
    Args:
        time_in: Check-in time string
        time_out: Check-out time string
    
    Returns:
        Tuple of (units, hours) or (None, None) if calculation fails
    """
    try:
        # Calculate time difference in minutes
        minutes = calculate_time_difference_minutes(time_in, time_out)
        
        if minutes is None:
            return None, None
        
        # Convert to units with special rounding
        units = minutes_to_units_with_rounding(minutes)
        
        # Calculate hours (for display purposes)
        hours = round(minutes / 60.0, 2)
        
        return units, hours
    except Exception as e:
        logger.error(f"Error calculating units from times: {e}")
        return None, None


def format_time_12hr(time_obj: time) -> str:
    """
    Format time object to 12-hour format with AM/PM
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
    
    return f"{hour}:{minute:02d} {am_pm}"
