"""X12 Response Parsers for OMES EDI

Parses X12 response transactions:
- 271 Eligibility Response
- 277 Claim Status Response
- 835 Remittance Advice
- 999 Functional Acknowledgment
"""

import logging
import re
from datetime import datetime, date
from typing import Optional, List

from .models import (
    EligibilityRequest,
    EligibilityResponse,
    ClaimStatusRequest,
    ClaimStatusResponse,
    ClaimStatus,
    RemittanceAdvice
)

logger = logging.getLogger(__name__)


def parse_271_response(x12_content: str, request: EligibilityRequest) -> EligibilityResponse:
    """
    Parse 271 Eligibility Response
    
    Args:
        x12_content: Raw X12 271 response
        request: Original eligibility request
    
    Returns:
        Parsed eligibility response
    """
    try:
        # Extract CDATA if wrapped in SOAP
        if "<![CDATA[" in x12_content:
            cdata_match = re.search(r'<!\[CDATA\[(.+?)\]\]>', x12_content, re.DOTALL)
            if cdata_match:
                x12_content = cdata_match.group(1)
        
        # Split into segments
        segments = [s.strip() for s in x12_content.split('~') if s.strip()]
        
        # Initialize response
        response = EligibilityResponse(
            member_id=request.member_id,
            is_active=False,
            response_raw=x12_content
        )
        
        # Parse segments
        for segment in segments:
            elements = segment.split('*')
            segment_id = elements[0]
            
            # EB segment contains eligibility information
            if segment_id == 'EB':
                # EB01: Eligibility or Benefit Information Code
                # '1' = Active Coverage, '6' = Inactive
                if len(elements) > 1:
                    eligibility_code = elements[1]
                    response.is_active = (eligibility_code == '1')
                
                # EB03: Service Type Code
                # EB04: Insurance Type Code
                
                # EB09: Copayment amount
                if len(elements) > 9 and elements[9]:
                    try:
                        response.copay_amount = float(elements[9])
                    except ValueError:
                        pass
            
            # DTP segment contains dates
            elif segment_id == 'DTP':
                # DTP01: Date/Time Qualifier
                # DTP02: Date/Time Period Format Qualifier
                # DTP03: Date/Time Period
                if len(elements) >= 4:
                    qualifier = elements[1]
                    date_str = elements[3]
                    
                    # 307 = Eligibility Begin Date
                    if qualifier == '307':
                        response.eligibility_start_date = parse_date(date_str)
                    # 308 = Eligibility End Date
                    elif qualifier == '308':
                        response.eligibility_end_date = parse_date(date_str)
            
            # NM1 segment for payer/plan name
            elif segment_id == 'NM1':
                # NM101: Entity Identifier Code (PR = Payer)
                if len(elements) > 3 and elements[1] == 'PR':
                    response.plan_name = elements[3]
            
            # AAA segment contains rejection/error codes
            elif segment_id == 'AAA':
                # AAA01: Valid
                # AAA03: Reject Reason Code
                # AAA04: Follow-up Action Code
                if len(elements) > 3:
                    response.rejection_reason = elements[3]
        
        logger.info(f"Parsed 271 response: Active={response.is_active}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to parse 271 response: {str(e)}")
        return EligibilityResponse(
            member_id=request.member_id,
            is_active=False,
            rejection_reason=f"Parse error: {str(e)}",
            response_raw=x12_content
        )


def parse_277_response(x12_content: str, request: ClaimStatusRequest) -> ClaimStatusResponse:
    """
    Parse 277 Claim Status Response
    
    Args:
        x12_content: Raw X12 277 response
        request: Original claim status request
    
    Returns:
        Parsed claim status response
    """
    try:
        # Extract CDATA if wrapped in SOAP
        if "<![CDATA[" in x12_content:
            cdata_match = re.search(r'<!\[CDATA\[(.+?)\]\]>', x12_content, re.DOTALL)
            if cdata_match:
                x12_content = cdata_match.group(1)
        
        # Split into segments
        segments = [s.strip() for s in x12_content.split('~') if s.strip()]
        
        # Initialize response
        response = ClaimStatusResponse(
            claim_number=request.claim_number,
            status_code=ClaimStatus.RECEIVED,
            status_description="Received",
            response_raw=x12_content
        )
        
        # Parse segments
        for segment in segments:
            elements = segment.split('*')
            segment_id = elements[0]
            
            # STC segment contains status information
            if segment_id == 'STC':
                # STC01: Claim Status Category Code
                # STC02: Claim Status Code
                if len(elements) > 2:
                    status_parts = elements[1].split(':')
                    if status_parts:
                        status_code = status_parts[0]
                        # Map to ClaimStatus enum
                        response.status_code = map_status_code(status_code)
                    
                    # STC02: Status code and description
                    if len(elements[2].split(':')) > 1:
                        response.status_description = elements[2].split(':')[1]
                    else:
                        response.status_description = elements[2]
                
                # STC10: Total Claim Charge Amount
                if len(elements) > 10 and elements[10]:
                    try:
                        response.total_charge = float(elements[10])
                    except ValueError:
                        pass
            
            # REF segment contains reference numbers
            elif segment_id == 'REF':
                # REF01: Reference Identification Qualifier
                # REF02: Reference Identification
                if len(elements) >= 3:
                    qualifier = elements[1]
                    value = elements[2]
                    
                    # 1K = Payer Claim Control Number
                    if qualifier == '1K':
                        response.payer_claim_control_number = value
                    # EV = Check Number
                    elif qualifier == 'EV':
                        response.check_number = value
            
            # AMT segment contains amount information
            elif segment_id == 'AMT':
                # AMT01: Amount Qualifier Code
                # AMT02: Monetary Amount
                if len(elements) >= 3:
                    qualifier = elements[1]
                    amount_str = elements[2]
                    
                    try:
                        amount = float(amount_str)
                        
                        # T = Payment Amount
                        if qualifier == 'T':
                            response.payment_amount = amount
                        # R = Patient Responsibility
                        elif qualifier == 'R':
                            response.patient_responsibility = amount
                    except ValueError:
                        pass
            
            # DTP segment for dates
            elif segment_id == 'DTP':
                # DTP01: Date/Time Qualifier
                # DTP03: Date
                if len(elements) >= 4:
                    qualifier = elements[1]
                    date_str = elements[3]
                    
                    # 573 = Claim Adjudication Date
                    if qualifier == '573':
                        response.adjudication_date = parse_date(date_str)
        
        logger.info(f"Parsed 277 response: Status={response.status_description}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to parse 277 response: {str(e)}")
        raise Exception(f"Failed to parse 277 response: {str(e)}")


def parse_835_remittance(x12_content: str) -> List[RemittanceAdvice]:
    """
    Parse 835 Remittance Advice (payment information)
    
    Args:
        x12_content: Raw X12 835 response
    
    Returns:
        List of remittance advice records
    """
    remittances = []
    
    try:
        # Extract CDATA if wrapped
        if "<![CDATA[" in x12_content:
            cdata_match = re.search(r'<!\[CDATA\[(.+?)\]\]>', x12_content, re.DOTALL)
            if cdata_match:
                x12_content = cdata_match.group(1)
        
        # Split into segments
        segments = [s.strip() for s in x12_content.split('~') if s.strip()]
        
        current_remittance = None
        payer_name = "Unknown Payer"
        payment_date = None
        check_number = None
        
        for segment in segments:
            elements = segment.split('*')
            segment_id = elements[0]
            
            # N1 segment for payer name
            if segment_id == 'N1' and len(elements) > 2:
                if elements[1] == 'PR':  # Payer
                    payer_name = elements[2]
            
            # DTM segment for payment date
            elif segment_id == 'DTM' and len(elements) >= 3:
                if elements[1] == '405':  # Production Date
                    payment_date = parse_date(elements[2])
            
            # TRN segment for check number
            elif segment_id == 'TRN' and len(elements) >= 3:
                check_number = elements[2]
            
            # CLP segment starts a new claim
            elif segment_id == 'CLP' and len(elements) >= 6:
                if current_remittance:
                    remittances.append(current_remittance)
                
                current_remittance = RemittanceAdvice(
                    transaction_id=str(uuid.uuid4()),
                    claim_number=elements[1],
                    claim_status=elements[2],
                    total_charge=float(elements[3]),
                    payment_amount=float(elements[4]),
                    patient_responsibility=float(elements[5]) if len(elements) > 5 else 0.0,
                    payment_date=payment_date or date.today(),
                    check_number=check_number,
                    payer_name=payer_name
                )
        
        # Add last remittance
        if current_remittance:
            remittances.append(current_remittance)
        
        logger.info(f"Parsed {len(remittances)} remittance records from 835")
        return remittances
        
    except Exception as e:
        logger.error(f"Failed to parse 835 remittance: {str(e)}")
        return []


def parse_date(date_str: str) -> Optional[date]:
    """Parse date from X12 format (YYYYMMDD or CCYYMMDD)"""
    try:
        if len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d").date()
        elif len(date_str) == 6:
            # YYMMDD format
            return datetime.strptime(date_str, "%y%m%d").date()
    except ValueError:
        pass
    return None


def map_status_code(code: str) -> ClaimStatus:
    """Map X12 status code to ClaimStatus enum"""
    status_map = {
        '1': ClaimStatus.RECEIVED,
        '2': ClaimStatus.PENDING,
        '3': ClaimStatus.REJECTED,
        '4': ClaimStatus.PAID,
        '20': ClaimStatus.DENIED,
        '22': ClaimStatus.PARTIAL
    }
    return status_map.get(code, ClaimStatus.RECEIVED)


import uuid
