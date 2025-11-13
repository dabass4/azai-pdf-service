"""X12 EDI Segment Builder for 837P Claims

This module provides classes for building individual X12 segments that make up
HIPAA 5010-compliant 837 Professional claims for Ohio Medicaid.
"""

from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class X12Segment:
    """Base class for X12 segments with validation and serialization"""
    
    def __init__(self, segment_id: str):
        self.segment_id = segment_id
        self.elements: List[str] = [segment_id]
        self.element_separator = "*"
        self.segment_terminator = "~"
        self.composite_separator = ":"
    
    def add_element(self, value: Any, required: bool = False) -> 'X12Segment':
        """Add element to segment with validation"""
        if value is None:
            if required:
                raise ValueError(f"Required element missing for segment {self.segment_id}")
            self.elements.append("")
        else:
            # Convert value to string
            str_value = str(value)
            self.elements.append(str_value)
        return self
    
    def add_composite(self, components: List[str], required: bool = False) -> 'X12Segment':
        """Add composite element (multiple sub-elements separated by colon)"""
        if not components or all(c is None for c in components):
            if required:
                raise ValueError(f"Required composite element missing for segment {self.segment_id}")
            self.elements.append("")
        else:
            composite_value = self.composite_separator.join(str(c) if c else "" for c in components)
            self.elements.append(composite_value)
        return self
    
    def serialize(self) -> str:
        """Convert segment to X12 format string"""
        return self.element_separator.join(self.elements) + self.segment_terminator
    
    def __repr__(self) -> str:
        return self.serialize().rstrip(self.segment_terminator)


class ISABuilder:
    """Builds Interchange Control Header (ISA) segment"""
    
    @staticmethod
    def build(
        sender_id: str,
        receiver_id: str,
        interchange_control_number: str,
        test_indicator: str = "T"
    ) -> str:
        """
        Build ISA segment for ODM transmission
        
        ISA is fixed-format (106 chars) with specific positions for elements
        """
        isa = "ISA"
        isa += "*"  # Element separator
        isa += "00"  # Authorization Qualifier
        isa += " " * 10  # Authorization Information (10 spaces)
        isa += "00"  # Security Qualifier
        isa += " " * 10  # Security Information (10 spaces)
        isa += "ZZ"  # Interchange ID Qualifier
        isa += sender_id.ljust(15)  # Sender ID (15 chars)
        isa += "ZZ"  # Interchange ID Qualifier for receiver
        isa += receiver_id.ljust(15)  # Receiver ID (15 chars)
        isa += datetime.now().strftime("%y%m%d")  # Interchange date (YYMMDD)
        isa += datetime.now().strftime("%H%M")  # Interchange time (HHMM)
        isa += "^"  # Repetition separator
        isa += "00501"  # Interchange Control Version
        isa += interchange_control_number.zfill(9)  # Control number (9 chars)
        isa += "0"  # Acknowledgment requested flag
        isa += test_indicator  # Usage indicator T=test, P=production
        isa += ":"  # Component element separator
        
        return isa + "~"


class NM1SegmentBuilder:
    """Builds NM1 (Name) segments for providers, patients, payers"""
    
    @staticmethod
    def build(
        entity_type_code: str,
        entity_id_type: str,
        last_name_or_org: str,
        first_name: Optional[str] = None,
        middle_initial: Optional[str] = None,
        name_prefix: Optional[str] = None,
        name_suffix: Optional[str] = None,
        identification_code_qualifier: str = "XX",
        identification_code: Optional[str] = None,
    ) -> X12Segment:
        """Build NM1 segment following Ohio Medicaid companion guide requirements"""
        
        segment = X12Segment("NM1")
        segment.add_element(entity_type_code, required=True)  # NM101
        segment.add_element(entity_id_type, required=True)  # NM102
        segment.add_element(last_name_or_org, required=True)  # NM103
        segment.add_element(first_name)  # NM104
        segment.add_element(middle_initial)  # NM105
        segment.add_element(name_prefix)  # NM106
        segment.add_element(name_suffix)  # NM107
        segment.add_element(identification_code_qualifier, required=True)  # NM108
        segment.add_element(identification_code, required=True)  # NM109
        
        return segment


class CLMSegmentBuilder:
    """Builds CLM (Claim) segment containing claim-level information"""
    
    @staticmethod
    def build(
        claim_id: str,
        total_charge_amount: Decimal,
        place_of_service: str,
        frequency_code: str = "1",
        provider_signature_on_file: str = "Y",
        assignment_of_benefits: str = "Y",
        release_of_information: str = "Y",
    ) -> X12Segment:
        """
        Build CLM segment
        
        Place of Service codes:
        11 = Office
        12 = Patient home
        13 = Assisted living facility
        """
        segment = X12Segment("CLM")
        segment.add_element(claim_id, required=True)  # CLM01
        segment.add_element(f"{total_charge_amount:.2f}", required=True)  # CLM02
        segment.add_element("")  # CLM03 - Blank
        segment.add_element("")  # CLM04 - Blank
        segment.add_composite([place_of_service, "B", frequency_code], required=True)  # CLM05
        segment.add_element(provider_signature_on_file, required=True)  # CLM06
        segment.add_element(assignment_of_benefits, required=True)  # CLM07
        segment.add_element(release_of_information, required=True)  # CLM08
        segment.add_element(provider_signature_on_file, required=True)  # CLM09
        
        return segment


class SV1SegmentBuilder:
    """Builds SV1 (Professional Service) segment for service line items"""
    
    @staticmethod
    def build(
        cpt_code: str,
        modifier_1: Optional[str] = None,
        modifier_2: Optional[str] = None,
        charge_amount: Decimal = Decimal("0.00"),
        units: Decimal = Decimal("1"),
        unit_type: str = "UN",
    ) -> X12Segment:
        """
        Build SV1 segment for professional services
        
        Unit types: UN=Units, MJ=Minutes
        """
        segment = X12Segment("SV1")
        
        # Build procedure code composite
        proc_composite = ["HC", cpt_code]
        if modifier_1:
            proc_composite.append(modifier_1)
        if modifier_2:
            proc_composite.append(modifier_2)
        
        segment.add_composite(proc_composite, required=True)  # SV101
        segment.add_element(f"{charge_amount:.2f}", required=True)  # SV102
        segment.add_element(unit_type, required=True)  # SV103
        segment.add_element(str(units), required=True)  # SV104
        
        return segment


class HISegmentBuilder:
    """Builds HI (Health Care Diagnosis Code) segment for diagnosis codes"""
    
    @staticmethod
    def build(diagnosis_codes: List[str]) -> X12Segment:
        """
        Build HI segment for diagnosis codes
        
        Qualifiers: ABK=Principal diagnosis, ABF=Other diagnosis
        """
        segment = X12Segment("HI")
        
        # Principal diagnosis (first code)
        if len(diagnosis_codes) > 0:
            segment.add_composite(["ABK", diagnosis_codes[0]], required=True)  # HI01
        
        # Secondary diagnoses
        for diagnosis_code in diagnosis_codes[1:]:
            segment.add_composite(["ABF", diagnosis_code])
        
        return segment
