"""
Scan Configuration - Centralized settings for timesheet scanning
All parameters are automatically applied when processing timesheets.
These settings persist across poppler-utils reinstalls.
"""

# =============================================================================
# PDF CONVERSION SETTINGS
# =============================================================================
PDF_SETTINGS = {
    "dpi": 300,                    # Higher DPI for better OCR accuracy
    "jpeg_quality": 98,            # High quality for text clarity
    "color_mode": "RGB",           # Preserve color for signature detection
    "thread_count": 2,             # Parallel processing
    "grayscale": False,            # Keep color
    "transparent": False
}

# =============================================================================
# TIME FORMAT SETTINGS
# =============================================================================
TIME_SETTINGS = {
    "display_format": "24h",       # "24h" for HH:MM (e.g., 17:30) or "12h" for H:MM AM/PM
    "input_formats": [
        "H:MM AM/PM",              # 9:00 AM, 5:30 PM
        "HH:MM",                   # 09:00, 17:30
        "HHMM",                    # 0900, 1730 (military)
        "H.MM",                    # 9.00, 5.30 (OCR decimal error)
    ],
    "ocr_fixes": {
        "decimal_to_colon": True,  # 6.70 -> 6:10
        "fix_invalid_minutes": True,  # 70 -> 10 (OCR misread)
        "minute_corrections": {
            # minute >= 60: subtract 60
            # 70-79 -> 10-19 (7 looks like 1)
            # 60-69 -> 00-09
        }
    },
    "am_pm_inference": {
        # Times without AM/PM are inferred:
        "7:00-11:59": "AM",        # Morning
        "12:00-12:59": "PM",       # Noon
        "1:00-6:59": "PM",         # Afternoon/Evening
    }
}

# =============================================================================
# DATE FORMAT SETTINGS
# =============================================================================
DATE_SETTINGS = {
    "output_format": "MM/DD/YYYY",  # Always output in this format
    "input_formats": [
        "MM/DD/YYYY",              # 12/30/2024
        "MM-DD-YYYY",              # 12-30-2024
        "YYYY-MM-DD",              # 2024-12-30
        "MM/DD",                   # 12/30 (year inferred from week)
        "Day Name",                # Monday, Tuesday, etc.
        "Day Number",              # 30, 31 (inferred from week)
    ],
    "week_inference": True,        # Infer dates from week_of field
    "cross_timesheet_comparison": True  # Compare with other timesheets to fill dates
}

# =============================================================================
# OCR EXTRACTION SETTINGS
# =============================================================================
EXTRACTION_SETTINGS = {
    "service_codes": ["T1019", "T1020", "T1021", "S5125", "S5126", "S5130", "S5131"],
    "signature_detection": True,
    "similar_employee_matching": True,
    "name_format": "First Last",   # Extract names in this format
    "preserve_ocr_names": True,    # Keep original spelling for similarity matching
}

# =============================================================================
# UNIT CALCULATION SETTINGS
# =============================================================================
UNIT_SETTINGS = {
    "minutes_per_unit": 15,        # 1 unit = 15 minutes
    "rounding": "nearest",         # Round to nearest unit
    "special_rules": {
        "35-59_minutes": 3,        # 35-59 min = 3 units (45 min minimum)
    }
}

# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================
CONFIDENCE_SETTINGS = {
    "auto_submit_threshold": 0.95,  # Auto-submit if confidence >= 95%
    "review_recommended": 0.80,     # Recommend review if < 80%
}


def get_all_settings():
    """Return all scan settings as a dictionary"""
    return {
        "pdf": PDF_SETTINGS,
        "time": TIME_SETTINGS,
        "date": DATE_SETTINGS,
        "extraction": EXTRACTION_SETTINGS,
        "units": UNIT_SETTINGS,
        "confidence": CONFIDENCE_SETTINGS
    }


def get_settings_summary():
    """Return a human-readable summary of settings"""
    return f"""
AZAI Scan Configuration
========================
PDF Conversion:
  - DPI: {PDF_SETTINGS['dpi']}
  - JPEG Quality: {PDF_SETTINGS['jpeg_quality']}
  - Color Mode: {PDF_SETTINGS['color_mode']}

Time Format:
  - Display: {TIME_SETTINGS['display_format']} ({"HH:MM" if TIME_SETTINGS['display_format'] == "24h" else "H:MM AM/PM"})
  - OCR Decimal Fix: {TIME_SETTINGS['ocr_fixes']['decimal_to_colon']}
  - Invalid Minute Fix: {TIME_SETTINGS['ocr_fixes']['fix_invalid_minutes']}

Date Format:
  - Output: {DATE_SETTINGS['output_format']}
  - Week Inference: {DATE_SETTINGS['week_inference']}
  - Cross-Timesheet: {DATE_SETTINGS['cross_timesheet_comparison']}

Units:
  - {UNIT_SETTINGS['minutes_per_unit']} minutes per unit
  - Rounding: {UNIT_SETTINGS['rounding']}

Extraction:
  - Service Codes: {', '.join(EXTRACTION_SETTINGS['service_codes'])}
  - Signature Detection: {EXTRACTION_SETTINGS['signature_detection']}
  - Similar Employee Matching: {EXTRACTION_SETTINGS['similar_employee_matching']}
"""
