"""
Validation utilities for ODM and EVV compliance
Enforces required fields marked with asterisk (*)
"""

from datetime import datetime
from typing import Dict, List, Tuple
import re
import random


def generate_staff_pin() -> str:
    """
    Generate a 9-digit Staff PIN for Sandata EVV transmission.
    This PIN is auto-generated when transmitting to Sandata.
    
    Returns:
        str: 9-digit PIN string
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(9)])


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
    
    # Latitude/Longitude - Only required for Sandata EVV submission, not profile completion
    # Validation moved to evv_submission.py
    
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
    
    # Employee Categories (*) - Required - must have at least one category
    categories = employee.get('categories', [])
    if not categories or len(categories) == 0:
        errors.append("Employee Category * is required - select at least one (RN, LPN, HHA, or DSP)")
    else:
        valid_categories = ['RN', 'LPN', 'HHA', 'DSP']
        invalid_cats = [c for c in categories if c not in valid_categories]
        if invalid_cats:
            errors.append(f"Invalid categories: {invalid_cats}. Must be one of: RN, LPN, HHA, DSP")
    
    # Staff PIN - Auto-generated when transmitting to Sandata, not required from user
    # (Removed from validation - will be auto-generated at transmission time)
    
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
        total_required = 10  # Total number of required fields for employee (updated: removed job_title, hire_date, employment_status)
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
