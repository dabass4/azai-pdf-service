"""X12 Transaction Builders for OMES EDI

Builds X12 transactions:
- 270 Eligibility Inquiry
- 276 Claim Status Inquiry
"""

import logging
from datetime import datetime
from typing import Optional

from .models import EligibilityRequest, ClaimStatusRequest

logger = logging.getLogger(__name__)


class X12Builder270:
    """Builder for 270 Eligibility Inquiry transactions"""
    
    ELEMENT_SEP = "*"
    COMPONENT_SEP = ":"
    SEGMENT_SEP = "~"
    
    def __init__(self, sender_id: str, receiver_id: str):
        self.sender_id = sender_id.ljust(15)
        self.receiver_id = receiver_id.ljust(15)
    
    def build_270(self, request: EligibilityRequest) -> str:
        """Build complete 270 transaction"""
        segments = []
        
        # ISA - Interchange Control Header
        timestamp = datetime.utcnow()
        segments.append(
            f"ISA*00*          *00*          *28*{self.sender_id}*28*{self.receiver_id}*"
            f"{timestamp.strftime('%y%m%d')}*{timestamp.strftime('%H%M')}*|*00501*000000001*0*T*{self.COMPONENT_SEP}"
        )
        
        # GS - Functional Group Header
        segments.append(
            f"GS*HS*{self.sender_id.strip()}*{self.receiver_id.strip()}*"
            f"{timestamp.strftime('%Y%m%d')}*{timestamp.strftime('%H%M')}*1*X*005010X279A1"
        )
        
        # ST - Transaction Set Header
        segments.append("ST*270*0001*005010X279A1")
        
        # BHT - Beginning of Hierarchical Transaction
        segments.append(
            f"BHT*0022*13*{request.member_id[:20]}*{timestamp.strftime('%Y%m%d')}*{timestamp.strftime('%H%M')}"
        )
        
        # HL - Information Source Level
        segments.append("HL*1**20*1")
        
        # NM1 - Information Source Name (Payer)
        segments.append(f"NM1*PR*2*OHIO MEDICAID*****PI*ODMITS")
        
        # HL - Information Receiver Level
        segments.append("HL*2*1*21*1")
        
        # NM1 - Information Receiver (Provider)
        segments.append(f"NM1*1P*2*PROVIDER*****XX*{request.provider_npi}")
        
        # HL - Subscriber Level
        segments.append("HL*3*2*22*0")
        
        # TRN - Patient Trace Number
        segments.append(f"TRN*1*{request.member_id}*{self.sender_id.strip()}")
        
        # NM1 - Subscriber Name
        segments.append(
            f"NM1*IL*1*{request.last_name}*{request.first_name}****MI*{request.member_id}"
        )
        
        # DMG - Subscriber Demographics
        gender_code = request.gender.value if request.gender else "U"
        dob_str = request.date_of_birth.strftime("%Y%m%d")
        segments.append(f"DMG*D8*{dob_str}*{gender_code}")
        
        # DTP - Service Date
        service_date = datetime.utcnow().strftime("%Y%m%d")
        segments.append(f"DTP*291*D8*{service_date}")
        
        # EQ - Eligibility/Benefit Inquiry
        segments.append(f"EQ*{request.service_type_code}")
        
        # SE - Transaction Set Trailer
        segment_count = len(segments) + 1
        segments.append(f"SE*{segment_count}*0001")
        
        # GE - Functional Group Trailer
        segments.append("GE*1*1")
        
        # IEA - Interchange Control Trailer
        segments.append("IEA*1*000000001")
        
        return self.SEGMENT_SEP.join(segments) + self.SEGMENT_SEP


class X12Builder276:
    """Builder for 276 Claim Status Inquiry transactions"""
    
    ELEMENT_SEP = "*"
    COMPONENT_SEP = ":"
    SEGMENT_SEP = "~"
    
    def __init__(self, sender_id: str, receiver_id: str):
        self.sender_id = sender_id.ljust(15)
        self.receiver_id = receiver_id.ljust(15)
    
    def build_276(self, request: ClaimStatusRequest) -> str:
        """Build complete 276 transaction"""
        segments = []
        
        # ISA - Interchange Control Header
        timestamp = datetime.utcnow()
        segments.append(
            f"ISA*00*          *00*          *28*{self.sender_id}*28*{self.receiver_id}*"
            f"{timestamp.strftime('%y%m%d')}*{timestamp.strftime('%H%M')}*|*00501*000000001*0*T*{self.COMPONENT_SEP}"
        )
        
        # GS - Functional Group Header
        segments.append(
            f"GS*HR*{self.sender_id.strip()}*{self.receiver_id.strip()}*"
            f"{timestamp.strftime('%Y%m%d')}*{timestamp.strftime('%H%M')}*1*X*005010X212"
        )
        
        # ST - Transaction Set Header
        segments.append("ST*276*0001*005010X212")
        
        # BHT - Beginning of Hierarchical Transaction
        segments.append(
            f"BHT*0010*13*{request.claim_number[:20]}*{timestamp.strftime('%Y%m%d')}*{timestamp.strftime('%H%M')}"
        )
        
        # HL - Information Source Level
        segments.append("HL*1**20*1")
        
        # NM1 - Information Source (Payer)
        segments.append(f"NM1*PR*2*OHIO MEDICAID*****PI*ODMITS")
        
        # HL - Information Receiver Level
        segments.append("HL*2*1*21*1")
        
        # NM1 - Information Receiver (Provider)
        segments.append(f"NM1*1P*2*PROVIDER*****XX*{request.provider_npi}")
        
        # HL - Provider of Service Level
        segments.append("HL*3*2*19*1")
        
        # NM1 - Provider
        segments.append(f"NM1*1P*2*PROVIDER*****XX*{request.provider_npi}")
        
        # HL - Subscriber Level
        segments.append("HL*4*3*22*0")
        
        # TRN - Patient Trace Number
        segments.append(f"TRN*1*{request.claim_number}*{self.sender_id.strip()}")
        
        # NM1 - Subscriber
        segments.append(
            f"NM1*IL*1*{request.patient_last_name}*{request.patient_first_name}****MI*{request.patient_member_id}"
        )
        
        # DMG - Demographics
        dob_str = request.patient_dob.strftime("%Y%m%d")
        segments.append(f"DMG*D8*{dob_str}")
        
        # TRN - Claim Tracking Number
        segments.append(f"TRN*2*{request.claim_number}*{self.sender_id.strip()}")
        
        # REF - Claim Identifier
        segments.append(f"REF*D9*{request.claim_number}")
        
        # DTP - Service Date
        if request.service_date:
            service_date_str = request.service_date.strftime("%Y%m%d")
            segments.append(f"DTP*472*D8*{service_date_str}")
        
        # SE - Transaction Set Trailer
        segment_count = len(segments) + 1
        segments.append(f"SE*{segment_count}*0001")
        
        # GE - Functional Group Trailer
        segments.append("GE*1*1")
        
        # IEA - Interchange Control Trailer
        segments.append("IEA*1*000000001")
        
        return self.SEGMENT_SEP.join(segments) + self.SEGMENT_SEP
