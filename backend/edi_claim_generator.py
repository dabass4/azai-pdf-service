"""X12 837P Claim Generator for Ohio Medicaid

This module generates complete HIPAA 5010-compliant 837 Professional claims
from timesheet data for submission to Ohio Department of Medicaid.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import logging

from edi_x12_builder import (
    ISABuilder, NM1SegmentBuilder, CLMSegmentBuilder,
    SV1SegmentBuilder, HISegmentBuilder, X12Segment
)

logger = logging.getLogger(__name__)


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
