"""
Validation utilities for ODM and EVV compliance
Enforces required fields marked with asterisk (*)
"""

from datetime import datetime
from typing import Dict, List, Tuple
import re


def validate_patient_required_fields(patient: dict) -> Tuple[bool, List[str]]:
    """
    Validate that all required fields for ODM Claims and EVV are present and valid.
    
    Required fields: 12 total
    - Basic info: first_name, last_name, dob, sex, medicaid_number
    - Address: street, city, state, zip, latitude, longitude, timezone
    - Medical: icd10_code
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Basic Information (*)
    if not patient.get('first_name') or patient.get('first_name', '').strip() == '':
        errors.append("First Name * is required (ODM & EVV)")
    
    if not patient.get('last_name') or patient.get('last_name', '').strip() == '':
        errors.append("Last Name * is required (ODM & EVV)")
    
    # Date of Birth (*)
    dob = patient.get('date_of_birth', '1900-01-01')
    if dob == '1900-01-01' or not dob:
        errors.append("Date of Birth * is required (ODM & EVV)")
    else:
        # Validate date format and that it's not in the future
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            if dob_date > datetime.now():
                errors.append("Date of Birth cannot be in the future")
        except ValueError:
            errors.append("Date of Birth must be in YYYY-MM-DD format")
    
    # Sex (*)
    sex = patient.get('sex', 'Unknown')
    if sex == 'Unknown' or not sex:
        errors.append("Sex * is required (ODM & EVV)")
    
    # Medicaid Number (*) - Exactly 12 digits for Ohio
    medicaid = patient.get('medicaid_number', '').strip()
    if not medicaid or medicaid == '':
        errors.append("Medicaid Number * is required (ODM & EVV)")
    elif not re.match(r'^\d{12}$', medicaid):
        errors.append("Medicaid Number must be exactly 12 digits (no letters or special characters)")
    
    # Address (*) - Required by both
    if not patient.get('address_street') or patient.get('address_street', '').strip() == '':
        errors.append("Street Address * is required (ODM & EVV)")
    elif len(patient.get('address_street', '')) < 5:
        errors.append("Street Address must be at least 5 characters")
    
    if not patient.get('address_city') or patient.get('address_city', '').strip() == '':
        errors.append("City * is required (ODM & EVV)")
    
    if not patient.get('address_state') or patient.get('address_state', '') == '':
        errors.append("State * is required (ODM & EVV)")
    
    zip_code = patient.get('address_zip', '').strip()
    if not zip_code:
        errors.append("ZIP Code * is required (ODM & EVV)")
    elif not re.match(r'^\d{5}(-\d{4})?$', zip_code):
        errors.append("ZIP Code must be 5 digits or 9 digits (XXXXX or XXXXX-XXXX)")
    
    # Latitude/Longitude (*) - Required by EVV
    lat = patient.get('address_latitude')
    lon = patient.get('address_longitude')
    if lat is None or lon is None:
        errors.append("Address Latitude/Longitude * is required (EVV geofencing)")
    else:
        if not (-90 <= lat <= 90):
            errors.append("Latitude must be between -90 and 90")
        if not (-180 <= lon <= 180):
            errors.append("Longitude must be between -180 and 180")
    
    # Timezone (*) - Required by EVV
    timezone = patient.get('timezone', '')
    if not timezone or timezone == '':
        errors.append("Timezone * is required (EVV)")
    
    # ICD-10 Code (*) - Required by both
    icd10 = patient.get('icd10_code', '').strip()
    if not icd10:
        errors.append("ICD-10 Diagnosis Code * is required (ODM & EVV)")
    elif not re.match(r'^[A-Z][0-9]{2}\.?[0-9A-Z]{0,4}$', icd10):
        errors.append("ICD-10 Code must be valid format (e.g., A00.0, M79.3)")
    
    return (len(errors) == 0, errors)


def validate_employee_required_fields(employee: dict) -> Tuple[bool, List[str]]:
    """
    Validate that all required fields for ODM Claims and EVV are present and valid.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Basic Information (*)
    if not employee.get('first_name') or employee.get('first_name', '').strip() == '':
        errors.append("First Name * is required (ODM & EVV)")
    
    if not employee.get('last_name') or employee.get('last_name', '').strip() == '':
        errors.append("Last Name * is required (ODM & EVV)")
    
    # Date of Birth (*) - Must be 18+
    dob = employee.get('date_of_birth', '1900-01-01')
    if dob == '1900-01-01' or not dob:
        errors.append("Date of Birth * is required (ODM & EVV)")
    else:
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            if dob_date > datetime.now():
                errors.append("Date of Birth cannot be in the future")
            
            # Check if 18+ years old
            age = (datetime.now() - dob_date).days / 365.25
            if age < 18:
                errors.append("Employee must be at least 18 years old")
        except ValueError:
            errors.append("Date of Birth must be in YYYY-MM-DD format")
    
    # SSN (*) - Required by both
    ssn = employee.get('ssn', '000-00-0000')
    if ssn == '000-00-0000' or not ssn:
        errors.append("Social Security Number * is required (ODM & EVV)")
    elif not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        errors.append("SSN must be in XXX-XX-XXXX format")
    
    # Sex (*)
    sex = employee.get('sex', 'Unknown')
    if sex == 'Unknown' or not sex:
        errors.append("Sex * is required (ODM & EVV)")
    
    # Address (*) - Required by both
    if not employee.get('address_street') or employee.get('address_street', '').strip() == '':
        errors.append("Street Address * is required (ODM & EVV)")
    
    if not employee.get('address_city') or employee.get('address_city', '').strip() == '':
        errors.append("City * is required (ODM & EVV)")
    
    if not employee.get('address_state') or employee.get('address_state', '') == '':
        errors.append("State * is required (ODM & EVV)")
    
    zip_code = employee.get('address_zip', '').strip()
    if not zip_code:
        errors.append("ZIP Code * is required (ODM & EVV)")
    elif not re.match(r'^\d{5}(-\d{4})?$', zip_code):
        errors.append("ZIP Code must be 5 digits (XXXXX or XXXXX-XXXX)")
    
    # Phone (*) - Required by both
    phone = employee.get('phone', '').strip()
    if not phone:
        errors.append("Phone Number * is required (ODM & EVV)")
    elif len(phone) < 10:
        errors.append("Phone Number must be at least 10 digits")
    
    # Hire Date (*) - Required by both
    hire_date = employee.get('hire_date', '1900-01-01')
    if hire_date == '1900-01-01' or not hire_date:
        errors.append("Hire Date * is required (ODM & EVV)")
    else:
        try:
            hire = datetime.strptime(hire_date, '%Y-%m-%d')
            if hire > datetime.now():
                errors.append("Hire Date cannot be in the future")
        except ValueError:
            errors.append("Hire Date must be in YYYY-MM-DD format")
    
    # Job Title (*) - Required by both
    if not employee.get('job_title') or employee.get('job_title', '').strip() == '':
        errors.append("Job Title * is required (ODM & EVV)")
    
    # Employment Status (*) - Must be Active
    status = employee.get('employment_status', 'Active')
    if not status or status == '':
        errors.append("Employment Status * is required (ODM & EVV)")
    elif status != 'Active':
        errors.append("Employment Status must be 'Active' to submit claims/EVV")
    
    # Staff PIN (*) - Required by EVV (9 digits)
    staff_pin = employee.get('staff_pin', '').strip()
    if not staff_pin:
        errors.append("Staff PIN * is required (EVV telephony)")
    elif not re.match(r'^\d{9}$', staff_pin):
        errors.append("Staff PIN must be exactly 9 digits")
    
    return (len(errors) == 0, errors)


def get_profile_completion_status(profile_type: str, profile: dict) -> Dict:
    """
    Get completion status of patient or employee profile.
    
    Returns:
        {
            'is_complete': bool,
            'completion_percentage': int,
            'missing_required_fields': list,
            'status': 'incomplete' | 'complete',
            'status_color': 'red' | 'green',
            'can_submit_claims': bool,
            'can_submit_evv': bool
        }
    """
    if profile_type == 'patient':
        is_valid, errors = validate_patient_required_fields(profile)
        total_required = 12  # Total number of required fields for patient
    elif profile_type == 'employee':
        is_valid, errors = validate_employee_required_fields(profile)
        total_required = 13  # Total number of required fields for employee
    else:
        return {
            'is_complete': False,
            'completion_percentage': 0,
            'missing_required_fields': ['Invalid profile type'],
            'status': 'incomplete',
            'status_color': 'red',
            'can_submit_claims': False,
            'can_submit_evv': False
        }
    
    missing_count = len(errors)
    completed_count = total_required - missing_count
    completion_percentage = int((completed_count / total_required) * 100)
    
    return {
        'is_complete': is_valid,
        'completion_percentage': completion_percentage,
        'missing_required_fields': errors,
        'status': 'complete' if is_valid else 'incomplete',
        'status_color': 'green' if is_valid else 'red',
        'can_submit_claims': is_valid,
        'can_submit_evv': is_valid
    }
