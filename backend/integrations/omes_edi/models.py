"""Pydantic models for OMES EDI transactions"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"


class EligibilityRequest(BaseModel):
    """270 Eligibility Inquiry Request"""
    member_id: str = Field(..., description="Patient Medicaid ID")
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[Gender] = None
    service_type_code: str = Field(default="30", description="30=Health Benefit Plan Coverage")
    provider_npi: str = Field(..., regex=r"^\d{10}$")
    

class CoveragePeriod(BaseModel):
    """Coverage period information"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class EligibilityResponse(BaseModel):
    """271 Eligibility Response"""
    member_id: str
    is_active: bool
    eligibility_start_date: Optional[date] = None
    eligibility_end_date: Optional[date] = None
    plan_name: Optional[str] = None
    copay_amount: Optional[float] = None
    deductible_amount: Optional[float] = None
    deductible_met: Optional[float] = None
    rejection_reason: Optional[str] = None
    response_raw: Optional[str] = None


class ClaimStatusRequest(BaseModel):
    """276 Claim Status Inquiry"""
    claim_number: str
    patient_member_id: str
    patient_last_name: str
    patient_first_name: str
    patient_dob: date
    provider_npi: str = Field(..., regex=r"^\d{10}$")
    service_date: Optional[date] = None


class ClaimStatus(str, Enum):
    """Claim processing status codes"""
    RECEIVED = "1"  # Received
    PENDING = "2"  # In process
    REJECTED = "3"  # Rejected
    PAID = "4"  # Paid
    DENIED = "20"  # Denied
    PARTIAL = "22"  # Partial payment


class ClaimStatusResponse(BaseModel):
    """277 Claim Status Response"""
    claim_number: str
    status_code: ClaimStatus
    status_description: str
    payer_claim_control_number: Optional[str] = None
    total_charge: Optional[float] = None
    payment_amount: Optional[float] = None
    patient_responsibility: Optional[float] = None
    adjudication_date: Optional[date] = None
    check_number: Optional[str] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    response_raw: Optional[str] = None


class ClaimSubmissionBatch(BaseModel):
    """Batch of claims for SFTP submission"""
    organization_id: str
    tpid: str = Field(..., description="7-digit Trading Partner ID")
    submission_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    claim_ids: List[str]
    filename: Optional[str] = None


class RemittanceAdvice(BaseModel):
    """835 Remittance Advice (Payment)"""
    transaction_id: str
    claim_number: str
    claim_status: str
    total_charge: float
    payment_amount: float
    patient_responsibility: float
    adjustments: List[dict] = Field(default_factory=list)
    service_lines: List[dict] = Field(default_factory=list)
    payment_date: date
    check_number: Optional[str] = None
    payer_name: str
    received_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


from datetime import timezone
