"""
Ohio Medicaid EVV Utilities
Utilities for managing EVV data compliance with Ohio Department of Medicaid specifications
"""
from datetime import datetime, timezone
from typing import Optional, Dict, List
import uuid


# Ohio Medicaid Specific Lists (Phase 2 & 3)
# Based on Appendix G from the EVV specifications

OHIO_PAYERS = [
    "ODM",  # Ohio Department of Medicaid
    "ODA"   # Ohio Department of Aging
]

OHIO_PAYER_PROGRAMS = {
    "ODM": [
        "Medicaid Home Care Waiver",
        "Medicaid PASSPORT",
        "Medicaid Assisted Living",
        "Medicaid My Care Ohio",
        "Medicaid Fee-For-Service"
    ],
    "ODA": [
        "PASSPORT",
        "Assisted Living",
        "Home First"
    ]
}

# Common Ohio Medicaid Procedure Codes for Home and Community Based Services
OHIO_PROCEDURE_CODES = {
    "T1019": "Personal Care Services",
    "T1020": "Personal Care Services - Per Diem",
    "S5125": "Attendant Care Services",
    "S5126": "Homemaker Services",
    "G0156": "Home Health Services - Skilled Nursing",
    "T1002": "RN Services",
    "T1003": "LPN/LVN Services",
    "T2024": "Service Assessment/Plan of Care",
    "T2025": "Waiver Services",
    "S9122": "Home Health Aide",
    "G0299": "Direct Skilled Nursing by RN",
    "G0300": "Direct Skilled Nursing by LPN"
}

# Exception codes as per ODM specifications
OHIO_EXCEPTION_CODES = {
    "15": "Visit time adjusted - member request",
    "28": "Visit time adjusted - system/technical issue",
    "39": "Visit time adjusted - emergency situation",
    "40": "Visit time adjusted - other reason"
}

# Call Types
CALL_TYPES = ["Telephony", "Mobile", "Manual", "Other"]

# Call Assignments
CALL_ASSIGNMENTS = ["Call In", "Call Out", "Interim"]

# Resolution Codes (Only "A" for ODM)
RESOLUTION_CODES = {"A": "Approved"}

# Timezone for Ohio (Eastern)
OHIO_TIMEZONE = "America/New_York"


class SequenceManager:
    """Manages sequence IDs for EVV records"""
    
    @staticmethod
    def generate_sequence_id() -> str:
        """
        Generate a unique sequence ID
        Can use timestamp format YYYYMMDDHHMMSS or UUID
        """
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    
    @staticmethod
    def validate_sequence_id(sequence_id: str, previous_sequence: Optional[str] = None) -> bool:
        """
        Validate sequence ID
        - Must be unique
        - For updates, must be greater than previous sequence
        """
        if not sequence_id:
            return False
        
        if previous_sequence:
            try:
                # If both are numeric timestamps, compare them
                if sequence_id.isdigit() and previous_sequence.isdigit():
                    return int(sequence_id) > int(previous_sequence)
            except:
                pass
        
        return True


class DateTimeUtils:
    """Utilities for handling date/time in EVV format"""
    
    @staticmethod
    def to_utc_iso(dt: datetime) -> str:
        """
        Convert datetime to UTC ISO format: YYYY-MM-DDTHH:MM:SSZ
        """
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            dt = dt.astimezone(timezone.utc)
        
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    @staticmethod
    def to_date_only(dt: datetime) -> str:
        """
        Convert datetime to date format: YYYY-MM-DD
        """
        return dt.strftime("%Y-%m-%d")
    
    @staticmethod
    def from_iso_string(iso_string: str) -> datetime:
        """
        Parse ISO format string to datetime
        """
        try:
            # Handle Z suffix
            if iso_string.endswith('Z'):
                iso_string = iso_string[:-1] + '+00:00'
            return datetime.fromisoformat(iso_string)
        except:
            # Try basic format
            return datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S")


class CoordinateValidator:
    """Validates geographic coordinates"""
    
    @staticmethod
    def validate_latitude(lat: float) -> bool:
        """Validate latitude (-90 to 90)"""
        return -90.0 <= lat <= 90.0
    
    @staticmethod
    def validate_longitude(lon: float) -> bool:
        """Validate longitude (-180 to 180)"""
        return -180.0 <= lon <= 180.0
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """Validate both coordinates"""
        return CoordinateValidator.validate_latitude(lat) and CoordinateValidator.validate_longitude(lon)


class PayerProgramValidator:
    """Validates payer, program, and procedure code combinations"""
    
    @staticmethod
    def validate_payer(payer: str) -> bool:
        """Validate payer is in Ohio list"""
        return payer in OHIO_PAYERS
    
    @staticmethod
    def validate_program(payer: str, program: str) -> bool:
        """Validate program for given payer"""
        if payer not in OHIO_PAYER_PROGRAMS:
            return False
        return program in OHIO_PAYER_PROGRAMS[payer]
    
    @staticmethod
    def validate_procedure_code(code: str) -> bool:
        """Validate procedure code"""
        return code in OHIO_PROCEDURE_CODES
    
    @staticmethod
    def validate_combination(payer: str, program: str, procedure_code: str) -> Dict[str, bool]:
        """
        Validate payer/program/procedure code combination
        Returns dict with validation results
        """
        return {
            "payer_valid": PayerProgramValidator.validate_payer(payer),
            "program_valid": PayerProgramValidator.validate_program(payer, program),
            "procedure_code_valid": PayerProgramValidator.validate_procedure_code(procedure_code),
            "all_valid": (
                PayerProgramValidator.validate_payer(payer) and
                PayerProgramValidator.validate_program(payer, program) and
                PayerProgramValidator.validate_procedure_code(procedure_code)
            )
        }
    
    @staticmethod
    def get_procedure_description(code: str) -> Optional[str]:
        """Get procedure code description"""
        return OHIO_PROCEDURE_CODES.get(code)


class BusinessEntityManager:
    """Manages Business Entity identification"""
    
    @staticmethod
    def format_medicaid_id(medicaid_id: str) -> str:
        """
        Format Medicaid ID with leading zeros (7 digits for Ohio)
        """
        return medicaid_id.zfill(7)
    
    @staticmethod
    def validate_business_entity_id(entity_id: str) -> bool:
        """
        Validate Business Entity ID (max 10 characters)
        """
        return len(entity_id) <= 10 and len(entity_id) > 0


class TransactionIDGenerator:
    """Generates transaction IDs for EVV submissions"""
    
    @staticmethod
    def generate() -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        unique_part = str(uuid.uuid4().hex[:8].upper())
        return f"TXN-{timestamp}-{unique_part}"


def validate_ssn(ssn: str) -> bool:
    """Validate SSN format (9 digits)"""
    clean_ssn = ssn.replace('-', '').replace(' ', '')
    return len(clean_ssn) == 9 and clean_ssn.isdigit()


def validate_phone(phone: str) -> bool:
    """Validate phone number (10 digits)"""
    clean_phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    return len(clean_phone) == 10 and clean_phone.isdigit()


def validate_zip_code(zip_code: str) -> bool:
    """Validate zip code (5 or 10 characters with dash)"""
    clean_zip = zip_code.replace('-', '')
    return len(clean_zip) in [5, 9] and clean_zip.isdigit()
