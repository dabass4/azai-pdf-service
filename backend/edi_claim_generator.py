"""X12 837P Claim Generator for Ohio Medicaid

This module generates complete HIPAA 5010-compliant 837 Professional claims
from timesheet data for submission to Ohio Department of Medicaid.

Supports:
- 837P (Professional) claims for home health/personal care services
- Ohio Medicaid HCPCS codes (T1019, T1020, S5125, etc.)
- Batch claim generation for SFTP submission
- Individual claim generation for testing

Ohio Medicaid Companion Guide Reference:
https://medicaid.ohio.gov/resources-for-providers/billing/companion-guides
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import logging
import uuid

from edi_x12_builder import (
    ISABuilder, NM1SegmentBuilder, CLMSegmentBuilder,
    SV1SegmentBuilder, HISegmentBuilder, X12Segment
)

logger = logging.getLogger(__name__)


# Ohio Medicaid specific constants
OHIO_MEDICAID_PAYER_ID = "ODMITS"
OHIO_MEDICAID_PAYER_NAME = "OHIO DEPARTMENT OF MEDICAID"

# Common HCPCS codes for Ohio Medicaid home care services
OHIO_HCPCS_CODES = {
    "T1019": {"description": "Personal Care Services", "unit_type": "UN", "typical_rate": 17.50},
    "T1020": {"description": "Personal Care Services - Live-In", "unit_type": "UN", "typical_rate": 15.00},
    "S5125": {"description": "Attendant Care Services", "unit_type": "UN", "typical_rate": 18.00},
    "S5126": {"description": "Attendant Care Services - Live-In", "unit_type": "UN", "typical_rate": 16.00},
    "T2025": {"description": "Waiver Services - NOS", "unit_type": "UN", "typical_rate": 20.00},
    "T2026": {"description": "Specialized Medical Equipment", "unit_type": "UN", "typical_rate": 25.00},
    "H0004": {"description": "Behavioral Health Counseling", "unit_type": "UN", "typical_rate": 75.00},
    "H2015": {"description": "Comprehensive Community Support", "unit_type": "UN", "typical_rate": 45.00},
    "H2016": {"description": "Comprehensive Community Support per diem", "unit_type": "UN", "typical_rate": 150.00},
    "99211": {"description": "Office Visit - Minimal", "unit_type": "UN", "typical_rate": 25.00},
    "99212": {"description": "Office Visit - Straightforward", "unit_type": "UN", "typical_rate": 45.00},
    "99213": {"description": "Office Visit - Low Complexity", "unit_type": "UN", "typical_rate": 75.00},
}

# Place of Service codes relevant to Ohio Medicaid
PLACE_OF_SERVICE = {
    "11": "Office",
    "12": "Home",
    "13": "Assisted Living Facility",
    "14": "Group Home",
    "31": "Skilled Nursing Facility",
    "32": "Nursing Facility",
    "33": "Custodial Care Facility",
    "99": "Other Place of Service",
}


class ClaimGenerator:
    """Generates complete X12 837P claims from timesheet data"""
    
    def __init__(self,
                 sender_id: str = "SENDER",
                 receiver_id: str = "ODMITS",
                 test_mode: bool = True):
        """
        Initialize claim generator with ODM connection parameters
        
        Args:
            sender_id: 7-digit ODM Trading Partner ID
            receiver_id: ODM system receiver ID
            test_mode: Whether to generate test or production claims
        """
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.test_mode = test_mode
        self.test_indicator = "T" if test_mode else "P"
        self.interchange_counter = 0
    
    def generate_claim(self, claim_data: Dict[str, Any]) -> str:
        """
        Generate complete X12 837P transaction from claim data
        
        Args:
            claim_data: Dictionary containing claim information
            
        Returns:
            Complete EDI file as string
        """
        segments = []
        self.interchange_counter += 1
        control_number = str(self.interchange_counter).zfill(9)
        
        # Build ISA (Interchange Control Header)
        isa = ISABuilder.build(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            interchange_control_number=control_number,
            test_indicator=self.test_indicator
        )
        segments.append(isa)
        
        # Build GS (Functional Group Header)
        gs = self._build_gs_segment(control_number)
        segments.append(gs)
        
        # Build ST (Transaction Set Header) and claim data
        st_and_claim = self._build_claim_transaction(claim_data, control_number)
        segments.extend(st_and_claim)
        
        # Build GE (Functional Group Trailer)
        ge = self._build_ge_segment(control_number)
        segments.append(ge)
        
        # Build IEA (Interchange Control Trailer)
        iea = self._build_iea_segment(control_number)
        segments.append(iea)
        
        # Combine all segments
        edi_output = "".join(segments)
        return edi_output
    
    def _build_gs_segment(self, control_number: str) -> str:
        """Build GS (Functional Group Header) segment"""
        gs_elements = [
            "GS",
            "HC",  # Functional Identifier Code (HC = Health Care)
            self.sender_id,
            self.receiver_id,
            datetime.now().strftime("%Y%m%d"),  # Date
            datetime.now().strftime("%H%M"),  # Time
            control_number,
            "X",  # Responsible Agency Code
            "005010X222A1",  # Version/Release/Industry Identifier (837P 5010)
        ]
        return "*".join(gs_elements) + "~"
    
    def _build_claim_transaction(self, claim_data: Dict[str, Any], control_number: str) -> List[str]:
        """Build ST segment and all claim detail segments"""
        segments = []
        
        # Build ST (Transaction Set Header)
        st_segments = [
            "ST",
            "837",  # Transaction Set Identifier Code
            "0001",  # Transaction Set Control Number
            "005010X222A1",  # Implementation Convention Reference
        ]
        segments.append("*".join(st_segments) + "~")
        
        # Build BHT (Beginning of Hierarchical Transaction)
        bht_segments = [
            "BHT",
            "0019",  # Hierarchical Structure Code
            "00",  # Transaction Set Purpose Code
            control_number,  # Reference Identifier
            datetime.now().strftime("%Y%m%d"),  # Date
            datetime.now().strftime("%H%M%S"),  # Time
            "CH",  # Claim or Encounter
        ]
        segments.append("*".join(bht_segments) + "~")
        
        # Loop 1000A: Submitter Name
        segments.append(self._build_submitter_name(claim_data))
        
        # Loop 1000B: Receiver Name
        segments.append(self._build_receiver_name())
        
        # Loop 2000A: Billing Provider Detail
        segments.extend(self._build_billing_provider(claim_data))
        
        # Loop 2000B: Subscriber (Patient) Detail
        segments.extend(self._build_subscriber_detail(claim_data))
        
        # Loop 2300: Claim Information
        segments.extend(self._build_claim_level_detail(claim_data))
        
        # Loop 2400: Service Line Information
        for idx, service_line in enumerate(claim_data.get('service_lines', []), start=1):
            segments.extend(self._build_service_line(service_line, idx, claim_data))
        
        # Build SE (Transaction Set Trailer)
        segment_count = len(segments) + 1  # +1 for SE itself
        se_segments = [
            "SE",
            str(segment_count),
            "0001",  # Must match ST02
        ]
        segments.append("*".join(se_segments) + "~")
        
        return segments
    
    def _build_submitter_name(self, claim_data: Dict[str, Any]) -> str:
        """Build Loop 1000A: Submitter Name"""
        submitter_name = claim_data.get('billing_provider_name', 'HEALTHCARE PROVIDER')
        submitter_id = claim_data.get('billing_provider_npi', '1234567890')
        
        submitter = NM1SegmentBuilder.build(
            entity_type_code="41",  # Submitter
            entity_id_type="2",  # Organization
            last_name_or_org=submitter_name,
            identification_code_qualifier="46",  # Electronic Transmitter ID
            identification_code=submitter_id,
        )
        
        # Build PER (Submitter EDI Contact Information)
        per_segments = [
            "PER",
            "IC",  # Contact Function Code
            "EDI DEPARTMENT",
            "TE",  # Telephone
            "6145551234",
        ]
        
        output = submitter.serialize()
        output += "*".join(per_segments) + "~"
        return output
    
    def _build_receiver_name(self) -> str:
        """Build Loop 1000B: Receiver Name (ODM)"""
        receiver = NM1SegmentBuilder.build(
            entity_type_code="40",  # Receiver
            entity_id_type="2",  # Organization
            last_name_or_org="OHIO MEDICAID",
            identification_code_qualifier="46",
            identification_code="ODMITS",
        )
        return receiver.serialize()
    
    def _build_billing_provider(self, claim_data: Dict[str, Any]) -> List[str]:
        """Build Loop 2000A: Billing Provider Detail"""
        segments = []
        
        # HL (Hierarchical Level) - Billing Provider
        hl_segments = [
            "HL",
            "1",  # Hierarchical ID number
            "",   # Hierarchical Parent ID (blank for first level)
            "20",  # Hierarchical Level Code (20 = billing provider)
            "1",   # Hierarchical Child Code (1 = has child)
        ]
        segments.append("*".join(hl_segments) + "~")
        
        # PRV (Provider Information)
        prv_segments = [
            "PRV",
            "BI",  # Provider Code (BI = Billing)
            "PXC",  # Reference Identification Qualifier
            "207Q00000X",  # Family Medicine taxonomy code (example)
        ]
        segments.append("*".join(prv_segments) + "~")
        
        # NM1 segment for billing provider
        billing_npi = claim_data.get('billing_provider_npi', '1234567890')
        billing_name = claim_data.get('billing_provider_name', 'HEALTHCARE PROVIDER')
        
        billing_provider = NM1SegmentBuilder.build(
            entity_type_code="85",  # Billing Provider
            entity_id_type="2",  # Organization
            last_name_or_org=billing_name,
            identification_code_qualifier="XX",  # NPI
            identification_code=billing_npi,
        )
        segments.append(billing_provider.serialize())
        
        return segments
    
    def _build_subscriber_detail(self, claim_data: Dict[str, Any]) -> List[str]:
        """Build Loop 2000B: Subscriber (Patient) Detail"""
        segments = []
        patient = claim_data.get('patient', {})
        
        # HL (Hierarchical Level) - Subscriber/Patient
        hl_segments = [
            "HL",
            "2",  # Hierarchical ID number
            "1",  # Hierarchical Parent ID
            "22",  # Hierarchical Level Code (22 = subscriber)
            "0",   # Hierarchical Child Code (0 = no child)
        ]
        segments.append("*".join(hl_segments) + "~")
        
        # SBR (Subscriber Information)
        sbr_segments = [
            "SBR",
            "P",   # Payer Responsibility (P = primary)
            "18",  # Individual Relationship Code (18 = self)
            "",    # Group or Policy Number
            "",    # Group Name
            "",    # Insurance Type Code
            "",    # Reserved
            "",    # Reserved
            "",    # Reserved
            "MB",  # Claim Filing Indicator (MB = Medicaid)
        ]
        segments.append("*".join(sbr_segments) + "~")
        
        # NM1 segment for patient/subscriber
        patient_first = patient.get('first_name', '')
        patient_last = patient.get('last_name', '')
        medicaid_id = patient.get('medicaid_id', '')
        
        patient_nm1 = NM1SegmentBuilder.build(
            entity_type_code="IL",  # Insured or Subscriber
            entity_id_type="1",  # Person
            last_name_or_org=patient_last,
            first_name=patient_first,
            identification_code_qualifier="MI",  # Member Identification Number
            identification_code=medicaid_id,
        )
        segments.append(patient_nm1.serialize())
        
        # DMG (Demographic Information)
        dob = patient.get('date_of_birth', '')
        gender = patient.get('gender', 'U')
        
        if dob:
            if isinstance(dob, str):
                # Assume YYYY-MM-DD format
                dob_formatted = dob.replace('-', '')
            else:
                dob_formatted = dob.strftime('%Y%m%d')
            
            dmg_segments = [
                "DMG",
                "D8",  # Date Format Qualifier
                dob_formatted,
                gender,
            ]
            segments.append("*".join(dmg_segments) + "~")
        
        return segments
    
    def _build_claim_level_detail(self, claim_data: Dict[str, Any]) -> List[str]:
        """Build Loop 2300: Claim Information"""
        segments = []
        
        # Generate unique claim ID
        claim_id = claim_data.get('claim_id', datetime.now().strftime("%Y%m%d%H%M%S"))
        
        # Calculate total charge
        total_charge = Decimal('0')
        for line in claim_data.get('service_lines', []):
            total_charge += Decimal(str(line.get('charge_amount', 0)))
        
        # CLM segment
        clm = CLMSegmentBuilder.build(
            claim_id=claim_id,
            total_charge_amount=total_charge,
            place_of_service=claim_data.get('place_of_service', '12'),  # 12 = Home
            frequency_code="1",
        )
        segments.append(clm.serialize())
        
        # DTP (Date) - Date of service
        service_lines = claim_data.get('service_lines', [])
        if service_lines:
            first_service_date = service_lines[0].get('service_date', '')
            if isinstance(first_service_date, str):
                service_date_formatted = first_service_date.replace('-', '')
            else:
                service_date_formatted = first_service_date.strftime('%Y%m%d')
            
            dtp_segments = [
                "DTP",
                "472",  # Service Date
                "D8",
                service_date_formatted,
            ]
            segments.append("*".join(dtp_segments) + "~")
        
        # HI (Diagnosis codes)
        diagnosis_codes = []
        if claim_data.get('diagnosis_code_1'):
            diagnosis_codes.append(claim_data['diagnosis_code_1'])
        if claim_data.get('diagnosis_code_2'):
            diagnosis_codes.append(claim_data['diagnosis_code_2'])
        
        if diagnosis_codes:
            hi = HISegmentBuilder.build(diagnosis_codes)
            segments.append(hi.serialize())
        
        # NM1 - Rendering provider (Loop 2310B)
        rendering_npi = claim_data.get('rendering_provider_npi', '')
        rendering_name = claim_data.get('rendering_provider_name', '')
        
        if rendering_npi:
            # Split name into first and last
            name_parts = rendering_name.split() if rendering_name else []
            last_name = name_parts[-1] if name_parts else ''
            first_name = name_parts[0] if len(name_parts) > 1 else ''
            
            rendering_provider = NM1SegmentBuilder.build(
                entity_type_code="82",  # Rendering Provider
                entity_id_type="1",  # Person
                last_name_or_org=last_name,
                first_name=first_name,
                identification_code_qualifier="XX",  # NPI
                identification_code=rendering_npi,
            )
            segments.append(rendering_provider.serialize())
        
        return segments
    
    def _build_service_line(self, service_line: Dict[str, Any], line_number: int, claim_data: Dict[str, Any]) -> List[str]:
        """Build Loop 2400: Service Line Information"""
        segments = []
        
        # LX (Service Line Number)
        lx_segments = [
            "LX",
            str(line_number),
        ]
        segments.append("*".join(lx_segments) + "~")
        
        # SV1 (Professional Service)
        cpt_code = service_line.get('service_code', service_line.get('cpt_code', ''))
        charge = Decimal(str(service_line.get('charge_amount', 0)))
        units = Decimal(str(service_line.get('units', 1)))
        
        sv1 = SV1SegmentBuilder.build(
            cpt_code=cpt_code,
            charge_amount=charge,
            units=units,
        )
        segments.append(sv1.serialize())
        
        # DTP (Date of Service)
        service_date = service_line.get('service_date', '')
        if isinstance(service_date, str):
            service_date_formatted = service_date.replace('-', '')
        else:
            service_date_formatted = service_date.strftime('%Y%m%d')
        
        dtp_segments = [
            "DTP",
            "472",  # Service Date
            "D8",
            service_date_formatted,
        ]
        segments.append("*".join(dtp_segments) + "~")
        
        return segments
    
    def _build_ge_segment(self, control_number: str) -> str:
        """Build GE (Functional Group Trailer) segment"""
        ge_segments = [
            "GE",
            "1",  # Number of transaction sets
            control_number,
        ]
        return "*".join(ge_segments) + "~"
    
    def _build_iea_segment(self, control_number: str) -> str:
        """Build IEA (Interchange Control Trailer) segment"""
        iea_segments = [
            "IEA",
            "1",  # Number of functional groups
            control_number.zfill(9),
        ]
        return "*".join(iea_segments) + "~"


# ==================== CONVENIENCE FUNCTIONS ====================

def generate_837p_claim(
    claims_data: List[Dict[str, Any]],
    sender_id: str,
    receiver_id: str = "ODMITS",
    provider_name: str = "HEALTHCARE PROVIDER",
    provider_npi: str = "1234567890",
    test_mode: bool = True
) -> str:
    """
    Generate complete 837P EDI file from claims data
    
    This is the main entry point for generating claims from timesheet data.
    
    Args:
        claims_data: List of claim dictionaries containing:
            - claim: Claim record from database
            - timesheet: Timesheet record
            - patient: Patient record
            - employee: Employee/DCW record
        sender_id: 7-digit ODM Trading Partner ID
        receiver_id: ODM system receiver ID (default: ODMITS)
        provider_name: Billing provider organization name
        provider_npi: Billing provider NPI (10 digits)
        test_mode: Whether to generate test (T) or production (P) claims
    
    Returns:
        Complete EDI file content as string
    """
    generator = ClaimGenerator(
        sender_id=sender_id,
        receiver_id=receiver_id,
        test_mode=test_mode
    )
    
    # If single claim, just generate it
    if len(claims_data) == 1:
        claim_dict = _transform_claim_data(claims_data[0], provider_name, provider_npi)
        return generator.generate_claim(claim_dict)
    
    # For multiple claims, generate batch file
    return generate_837p_batch(
        claims_data=claims_data,
        sender_id=sender_id,
        receiver_id=receiver_id,
        provider_name=provider_name,
        provider_npi=provider_npi,
        test_mode=test_mode
    )


def generate_837p_batch(
    claims_data: List[Dict[str, Any]],
    sender_id: str,
    receiver_id: str = "ODMITS",
    provider_name: str = "HEALTHCARE PROVIDER",
    provider_npi: str = "1234567890",
    test_mode: bool = True
) -> str:
    """
    Generate batch 837P EDI file with multiple claims
    
    Creates a single EDI file containing multiple claim transactions,
    suitable for SFTP batch submission to Ohio Medicaid.
    
    Args:
        claims_data: List of claim data dictionaries
        sender_id: Trading Partner ID
        receiver_id: ODM receiver ID
        provider_name: Billing provider name
        provider_npi: Billing provider NPI
        test_mode: Test or production mode
    
    Returns:
        Complete batch EDI file content
    """
    segments = []
    test_indicator = "T" if test_mode else "P"
    control_number = datetime.now().strftime("%Y%m%d%H%M%S")[:9]
    
    # ISA - Interchange Control Header
    isa = ISABuilder.build(
        sender_id=sender_id,
        receiver_id=receiver_id,
        interchange_control_number=control_number,
        test_indicator=test_indicator
    )
    segments.append(isa)
    
    # GS - Functional Group Header
    gs_elements = [
        "GS",
        "HC",  # Health Care Claim
        sender_id,
        receiver_id,
        datetime.now().strftime("%Y%m%d"),
        datetime.now().strftime("%H%M"),
        control_number,
        "X",
        "005010X222A1",
    ]
    segments.append("*".join(gs_elements) + "~")
    
    # Generate each claim as a separate ST-SE transaction
    transaction_count = 0
    for idx, claim_data in enumerate(claims_data, start=1):
        try:
            claim_dict = _transform_claim_data(claim_data, provider_name, provider_npi)
            claim_segments = _build_claim_transaction_set(claim_dict, str(idx).zfill(4))
            segments.extend(claim_segments)
            transaction_count += 1
        except Exception as e:
            logger.error(f"Failed to generate claim {idx}: {str(e)}")
            continue
    
    # GE - Functional Group Trailer
    ge_elements = ["GE", str(transaction_count), control_number]
    segments.append("*".join(ge_elements) + "~")
    
    # IEA - Interchange Control Trailer
    iea_elements = ["IEA", "1", control_number.zfill(9)]
    segments.append("*".join(iea_elements) + "~")
    
    return "".join(segments)


def _transform_claim_data(
    raw_data: Dict[str, Any],
    provider_name: str,
    provider_npi: str
) -> Dict[str, Any]:
    """
    Transform raw database records into claim generator format
    
    Extracts and formats data from timesheet, patient, and employee records
    into the structure expected by ClaimGenerator.
    """
    claim = raw_data.get('claim', {})
    timesheet = raw_data.get('timesheet', {})
    patient = raw_data.get('patient', {})
    employee = raw_data.get('employee', {})
    
    # Determine service code from timesheet
    service_code = timesheet.get('service_code') or timesheet.get('billing_code') or 'T1019'
    
    # Get rate information
    hourly_rate = Decimal(str(timesheet.get('hourly_rate', 0)))
    if hourly_rate == 0 and service_code in OHIO_HCPCS_CODES:
        hourly_rate = Decimal(str(OHIO_HCPCS_CODES[service_code]['typical_rate']))
    
    # Calculate units (typically hours for personal care)
    total_hours = Decimal(str(timesheet.get('total_hours', 0)))
    units = total_hours if total_hours > 0 else Decimal('1')
    
    # Calculate charge
    charge_amount = units * hourly_rate
    
    # Build service lines from timesheet entries
    service_lines = []
    
    # Check if timesheet has multiple entries
    timesheet_entries = timesheet.get('entries', [])
    if timesheet_entries:
        for entry in timesheet_entries:
            entry_hours = Decimal(str(entry.get('hours', 0)))
            entry_rate = Decimal(str(entry.get('rate', hourly_rate)))
            service_lines.append({
                'service_code': entry.get('service_code', service_code),
                'service_date': entry.get('date', timesheet.get('date')),
                'units': entry_hours,
                'charge_amount': entry_hours * entry_rate,
            })
    else:
        # Single service line from timesheet totals
        service_lines.append({
            'service_code': service_code,
            'service_date': timesheet.get('date', datetime.now().strftime('%Y-%m-%d')),
            'units': units,
            'charge_amount': charge_amount,
        })
    
    # Build patient info
    patient_info = {
        'first_name': patient.get('first_name', ''),
        'last_name': patient.get('last_name', ''),
        'medicaid_id': patient.get('medicaid_number') or patient.get('medicaid_id', ''),
        'date_of_birth': patient.get('dob') or patient.get('date_of_birth', ''),
        'gender': _normalize_gender(patient.get('gender', 'U')),
        'address_street': patient.get('address', ''),
        'address_city': patient.get('city', ''),
        'address_state': patient.get('state', 'OH'),
        'address_zip': patient.get('zip', ''),
    }
    
    # Build rendering provider info (the DCW/employee who provided service)
    rendering_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
    rendering_npi = employee.get('npi', '')
    
    # Diagnosis codes (default Z codes for routine encounters if none specified)
    diagnosis_1 = claim.get('diagnosis_code_1') or patient.get('primary_diagnosis') or 'Z0000'
    diagnosis_2 = claim.get('diagnosis_code_2') or patient.get('secondary_diagnosis')
    
    return {
        'claim_id': claim.get('claim_id') or str(uuid.uuid4()),
        'billing_provider_name': provider_name,
        'billing_provider_npi': provider_npi,
        'rendering_provider_name': rendering_name,
        'rendering_provider_npi': rendering_npi,
        'patient': patient_info,
        'place_of_service': timesheet.get('place_of_service', '12'),  # Default: Home
        'diagnosis_code_1': diagnosis_1,
        'diagnosis_code_2': diagnosis_2,
        'service_lines': service_lines,
        'authorization_number': claim.get('authorization_number') or timesheet.get('authorization_number'),
        'original_claim_number': claim.get('original_claim_number'),  # For replacements
    }


def _normalize_gender(gender: str) -> str:
    """Normalize gender value for X12 format"""
    if not gender:
        return 'U'
    gender_upper = gender.upper()
    if gender_upper in ['M', 'MALE']:
        return 'M'
    elif gender_upper in ['F', 'FEMALE']:
        return 'F'
    else:
        return 'U'


def _build_claim_transaction_set(
    claim_data: Dict[str, Any],
    transaction_control_number: str
) -> List[str]:
    """
    Build a complete ST-SE transaction set for a single claim
    
    Returns list of segment strings for one claim transaction.
    """
    segments = []
    
    # ST - Transaction Set Header
    st_elements = ["ST", "837", transaction_control_number, "005010X222A1"]
    segments.append("*".join(st_elements) + "~")
    
    # BHT - Beginning of Hierarchical Transaction
    bht_elements = [
        "BHT",
        "0019",  # Hierarchical Structure Code
        "00",    # Original
        claim_data.get('claim_id', '')[:30],  # Reference ID
        datetime.now().strftime("%Y%m%d"),
        datetime.now().strftime("%H%M%S"),
        "CH",    # Claim
    ]
    segments.append("*".join(bht_elements) + "~")
    
    # Loop 1000A - Submitter Name
    segments.append(_build_submitter_loop(claim_data))
    
    # Loop 1000B - Receiver Name
    segments.append(_build_receiver_loop())
    
    # Loop 2000A - Billing Provider Hierarchical Level
    segments.extend(_build_billing_provider_loop(claim_data))
    
    # Loop 2000B - Subscriber Hierarchical Level
    segments.extend(_build_subscriber_loop(claim_data))
    
    # Loop 2300 - Claim Information
    segments.extend(_build_claim_info_loop(claim_data))
    
    # Loop 2400 - Service Line Information
    for idx, service_line in enumerate(claim_data.get('service_lines', []), start=1):
        segments.extend(_build_service_line_loop(service_line, idx))
    
    # SE - Transaction Set Trailer
    segment_count = len(segments) + 1
    se_elements = ["SE", str(segment_count), transaction_control_number]
    segments.append("*".join(se_elements) + "~")
    
    return segments


def _build_submitter_loop(claim_data: Dict[str, Any]) -> str:
    """Build Loop 1000A - Submitter Name"""
    submitter_name = claim_data.get('billing_provider_name', 'PROVIDER')
    # NM1 - Submitter Name
    nm1 = f"NM1*41*2*{submitter_name}*****46*{claim_data.get('billing_provider_npi', '')}~"
    # PER - Submitter Contact
    per = "PER*IC*EDI DEPT*TE*6145551234~"
    return nm1 + per


def _build_receiver_loop() -> str:
    """Build Loop 1000B - Receiver Name"""
    return f"NM1*40*2*{OHIO_MEDICAID_PAYER_NAME}*****46*{OHIO_MEDICAID_PAYER_ID}~"


def _build_billing_provider_loop(claim_data: Dict[str, Any]) -> List[str]:
    """Build Loop 2000A - Billing Provider"""
    segments = []
    
    # HL - Hierarchical Level (Billing Provider)
    segments.append("HL*1**20*1~")
    
    # PRV - Provider Information
    segments.append("PRV*BI*PXC*251E00000X~")  # Home Health taxonomy
    
    # NM1 - Billing Provider Name
    provider_name = claim_data.get('billing_provider_name', 'PROVIDER')
    provider_npi = claim_data.get('billing_provider_npi', '1234567890')
    segments.append(f"NM1*85*2*{provider_name}*****XX*{provider_npi}~")
    
    # N3 - Provider Address (required by Ohio Medicaid)
    segments.append("N3*123 PROVIDER ST~")
    
    # N4 - Provider City/State/Zip
    segments.append("N4*COLUMBUS*OH*432150000~")
    
    # REF - Provider Tax ID
    segments.append("REF*EI*123456789~")
    
    return segments


def _build_subscriber_loop(claim_data: Dict[str, Any]) -> List[str]:
    """Build Loop 2000B - Subscriber/Patient"""
    segments = []
    patient = claim_data.get('patient', {})
    
    # HL - Hierarchical Level (Subscriber)
    segments.append("HL*2*1*22*0~")
    
    # SBR - Subscriber Information
    segments.append("SBR*P*18*******MB~")  # MB = Medicaid
    
    # NM1 - Subscriber Name
    last_name = patient.get('last_name', 'DOE')
    first_name = patient.get('first_name', 'JOHN')
    medicaid_id = patient.get('medicaid_id', '')
    segments.append(f"NM1*IL*1*{last_name}*{first_name}****MI*{medicaid_id}~")
    
    # N3 - Patient Address
    address = patient.get('address_street', '123 MAIN ST')
    segments.append(f"N3*{address}~")
    
    # N4 - Patient City/State/Zip
    city = patient.get('address_city', 'COLUMBUS')
    state = patient.get('address_state', 'OH')
    zip_code = patient.get('address_zip', '43215')
    segments.append(f"N4*{city}*{state}*{zip_code}~")
    
    # DMG - Demographic Information
    dob = patient.get('date_of_birth', '')
    if isinstance(dob, str):
        dob_formatted = dob.replace('-', '')
    elif hasattr(dob, 'strftime'):
        dob_formatted = dob.strftime('%Y%m%d')
    else:
        dob_formatted = '19900101'
    
    gender = patient.get('gender', 'U')
    segments.append(f"DMG*D8*{dob_formatted}*{gender}~")
    
    return segments


def _build_claim_info_loop(claim_data: Dict[str, Any]) -> List[str]:
    """Build Loop 2300 - Claim Information"""
    segments = []
    
    # Calculate total charge
    total_charge = sum(
        Decimal(str(line.get('charge_amount', 0)))
        for line in claim_data.get('service_lines', [])
    )
    
    claim_id = claim_data.get('claim_id', '')[:20]
    pos = claim_data.get('place_of_service', '12')
    
    # CLM - Claim Information
    segments.append(f"CLM*{claim_id}*{total_charge:.2f}***{pos}:B:1*Y*A*Y*Y~")
    
    # DTP - Service Date (statement dates)
    service_lines = claim_data.get('service_lines', [])
    if service_lines:
        first_date = service_lines[0].get('service_date', '')
        last_date = service_lines[-1].get('service_date', '')
        
        if isinstance(first_date, str):
            first_date_fmt = first_date.replace('-', '')
        else:
            first_date_fmt = first_date.strftime('%Y%m%d') if first_date else datetime.now().strftime('%Y%m%d')
        
        if isinstance(last_date, str):
            last_date_fmt = last_date.replace('-', '')
        else:
            last_date_fmt = last_date.strftime('%Y%m%d') if last_date else first_date_fmt
        
        segments.append(f"DTP*434*RD8*{first_date_fmt}-{last_date_fmt}~")
    
    # REF - Prior Authorization (if present)
    auth_num = claim_data.get('authorization_number')
    if auth_num:
        segments.append(f"REF*G1*{auth_num}~")
    
    # HI - Diagnosis Codes
    diag_1 = claim_data.get('diagnosis_code_1', 'Z0000').replace('.', '')
    hi_segment = f"HI*ABK:{diag_1}"
    
    diag_2 = claim_data.get('diagnosis_code_2')
    if diag_2:
        hi_segment += f"*ABF:{diag_2.replace('.', '')}"
    
    segments.append(hi_segment + "~")
    
    # NM1 - Rendering Provider (if different from billing)
    rendering_npi = claim_data.get('rendering_provider_npi')
    rendering_name = claim_data.get('rendering_provider_name', '')
    
    if rendering_npi and rendering_name:
        name_parts = rendering_name.split()
        last_name = name_parts[-1] if name_parts else ''
        first_name = name_parts[0] if len(name_parts) > 1 else ''
        segments.append(f"NM1*82*1*{last_name}*{first_name}****XX*{rendering_npi}~")
    
    return segments


def _build_service_line_loop(service_line: Dict[str, Any], line_number: int) -> List[str]:
    """Build Loop 2400 - Service Line Information"""
    segments = []
    
    # LX - Service Line Number
    segments.append(f"LX*{line_number}~")
    
    # SV1 - Professional Service
    service_code = service_line.get('service_code', 'T1019')
    charge = Decimal(str(service_line.get('charge_amount', 0)))
    units = Decimal(str(service_line.get('units', 1)))
    
    # Get unit type from HCPCS definition or default
    unit_type = "UN"
    if service_code in OHIO_HCPCS_CODES:
        unit_type = OHIO_HCPCS_CODES[service_code].get('unit_type', 'UN')
    
    # Build SV1 with procedure code composite
    sv1_elements = [
        "SV1",
        f"HC:{service_code}",  # Procedure code
        f"{charge:.2f}",       # Charge amount
        unit_type,             # Unit type
        str(units),            # Units
        "",                    # Place of service (blank - in CLM)
        "",                    # Service type code (blank)
        "1",                   # Diagnosis code pointer
    ]
    segments.append("*".join(sv1_elements) + "~")
    
    # DTP - Service Date
    service_date = service_line.get('service_date', '')
    if isinstance(service_date, str):
        date_formatted = service_date.replace('-', '')
    elif hasattr(service_date, 'strftime'):
        date_formatted = service_date.strftime('%Y%m%d')
    else:
        date_formatted = datetime.now().strftime('%Y%m%d')
    
    segments.append(f"DTP*472*D8*{date_formatted}~")
    
    return segments


# ==================== VALIDATION UTILITIES ====================

def validate_claim_data(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate claim data before generation
    
    Returns dict with 'valid' boolean and 'errors' list
    """
    errors = []
    
    # Check required fields
    if not claim_data.get('billing_provider_npi'):
        errors.append("Missing billing provider NPI")
    elif len(claim_data['billing_provider_npi']) != 10:
        errors.append("Billing provider NPI must be 10 digits")
    
    patient = claim_data.get('patient', {})
    if not patient.get('medicaid_id'):
        errors.append("Missing patient Medicaid ID")
    elif len(patient['medicaid_id']) != 12:
        errors.append("Medicaid ID must be 12 digits")
    
    if not patient.get('last_name'):
        errors.append("Missing patient last name")
    
    if not patient.get('first_name'):
        errors.append("Missing patient first name")
    
    service_lines = claim_data.get('service_lines', [])
    if not service_lines:
        errors.append("No service lines provided")
    
    for idx, line in enumerate(service_lines, start=1):
        if not line.get('service_code'):
            errors.append(f"Service line {idx}: Missing service code")
        if not line.get('charge_amount') or Decimal(str(line.get('charge_amount', 0))) <= 0:
            errors.append(f"Service line {idx}: Invalid charge amount")
        if not line.get('service_date'):
            errors.append(f"Service line {idx}: Missing service date")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def get_hcpcs_info(code: str) -> Optional[Dict[str, Any]]:
    """Get information about an Ohio Medicaid HCPCS code"""
    return OHIO_HCPCS_CODES.get(code)
