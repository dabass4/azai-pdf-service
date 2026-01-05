"""Mock ODM (Ohio Department of Medicaid) API Routes

Simulates OMES SOAP and SFTP endpoints for development and testing.
These endpoints allow testing the claims workflow without real ODM credentials.

Mock Endpoints:
- POST /api/mock/odm/soap/eligibility - Simulate 270/271 eligibility check
- POST /api/mock/odm/soap/claim-status - Simulate 276/277 claim status
- POST /api/mock/odm/sftp/upload - Simulate 837 file upload
- GET /api/mock/odm/sftp/list - List mock response files
- GET /api/mock/odm/sftp/download/{filename} - Download mock response file
- POST /api/mock/odm/sftp/generate-835 - Generate mock 835 remittance

All mock responses follow Ohio Medicaid X12 EDI specifications.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timezone, timedelta
import uuid
import random
import logging

from auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/mock/odm", tags=["mock-odm"])

# In-memory storage for mock files
mock_sftp_inbound: Dict[str, Dict] = {}  # Uploaded 837 files
mock_sftp_outbound: Dict[str, Dict] = {}  # Response files (835, 277, 999)


# ==================== PYDANTIC MODELS ====================

class MockEligibilityRequest(BaseModel):
    """Mock eligibility verification request"""
    member_id: str = Field(..., description="12-digit Medicaid ID")
    first_name: str
    last_name: str
    date_of_birth: str  # YYYY-MM-DD
    provider_npi: str = Field(..., description="10-digit NPI")
    service_date: Optional[str] = None  # YYYY-MM-DD

class MockEligibilityResponse(BaseModel):
    """Mock eligibility verification response"""
    transaction_id: str
    member_id: str
    is_active: bool
    eligibility_start_date: Optional[str] = None
    eligibility_end_date: Optional[str] = None
    plan_name: Optional[str] = None
    plan_code: Optional[str] = None
    copay_amount: Optional[float] = None
    deductible_remaining: Optional[float] = None
    rejection_reason: Optional[str] = None
    response_code: str  # AAA = Active, AAF = Inactive
    response_message: str

class MockClaimStatusRequest(BaseModel):
    """Mock claim status check request"""
    claim_number: str
    patient_member_id: str
    patient_last_name: str
    patient_first_name: str
    patient_dob: str  # YYYY-MM-DD
    provider_npi: str
    service_from_date: Optional[str] = None
    service_to_date: Optional[str] = None

class MockClaimStatusResponse(BaseModel):
    """Mock claim status response"""
    transaction_id: str
    claim_number: str
    payer_claim_control_number: Optional[str] = None
    status_code: str  # A0-A7, D0, P0-P5, R0-R16, E0-E4
    status_category: str  # Accepted, Denied, Pending, Rejected
    status_description: str
    total_charge: float
    payment_amount: Optional[float] = None
    patient_responsibility: Optional[float] = None
    adjudication_date: Optional[str] = None
    check_number: Optional[str] = None
    effective_date: Optional[str] = None
    rejection_reasons: List[str] = []

class MockFileUploadRequest(BaseModel):
    """Mock SFTP file upload request"""
    filename: str
    content: str  # X12 EDI content
    file_type: str = Field(default="837", description="837, 270, 276, 278")

class MockGenerate835Request(BaseModel):
    """Request to generate mock 835 remittance"""
    claim_numbers: List[str]
    payment_status: str = Field(default="paid", description="paid, partial, denied")
    payment_date: Optional[str] = None  # YYYY-MM-DD


# ==================== MOCK SOAP ENDPOINTS ====================

@router.post("/soap/eligibility", response_model=MockEligibilityResponse)
async def mock_eligibility_check(
    request: MockEligibilityRequest,
    current_user: dict = Depends(get_current_user)
) -> MockEligibilityResponse:
    """
    Mock OMES SOAP 270/271 Eligibility Verification
    
    Simulates real-time eligibility check against Ohio Medicaid.
    Returns predictable responses based on member_id patterns:
    - Member IDs ending in 1-5: Active eligibility
    - Member IDs ending in 6-8: Inactive/expired eligibility
    - Member IDs ending in 9-0: Various rejection scenarios
    """
    logger.info(f"Mock eligibility check for member: {request.member_id}")
    
    transaction_id = f"MOCK-270-{uuid.uuid4().hex[:12].upper()}"
    
    # Determine response based on member_id pattern
    last_digit = request.member_id[-1] if request.member_id else "0"
    
    if last_digit in ["1", "2", "3", "4", "5"]:
        # Active eligibility
        return MockEligibilityResponse(
            transaction_id=transaction_id,
            member_id=request.member_id,
            is_active=True,
            eligibility_start_date="2024-01-01",
            eligibility_end_date="2025-12-31",
            plan_name="Ohio Medicaid Fee-For-Service",
            plan_code="ODMFFS",
            copay_amount=0.00,
            deductible_remaining=0.00,
            rejection_reason=None,
            response_code="AAA",
            response_message="Member is active and eligible for services"
        )
    
    elif last_digit in ["6", "7"]:
        # Inactive - coverage expired
        return MockEligibilityResponse(
            transaction_id=transaction_id,
            member_id=request.member_id,
            is_active=False,
            eligibility_start_date="2023-01-01",
            eligibility_end_date="2023-12-31",
            plan_name="Ohio Medicaid Fee-For-Service",
            plan_code="ODMFFS",
            copay_amount=None,
            deductible_remaining=None,
            rejection_reason="Coverage terminated - eligibility period ended",
            response_code="AAF",
            response_message="Member coverage has expired"
        )
    
    elif last_digit == "8":
        # Inactive - different plan
        return MockEligibilityResponse(
            transaction_id=transaction_id,
            member_id=request.member_id,
            is_active=False,
            eligibility_start_date=None,
            eligibility_end_date=None,
            plan_name=None,
            plan_code=None,
            copay_amount=None,
            deductible_remaining=None,
            rejection_reason="Member enrolled in Managed Care plan - contact MCO",
            response_code="AAF",
            response_message="Not eligible for Fee-For-Service - enrolled in MCO"
        )
    
    else:
        # Not found / invalid
        return MockEligibilityResponse(
            transaction_id=transaction_id,
            member_id=request.member_id,
            is_active=False,
            eligibility_start_date=None,
            eligibility_end_date=None,
            plan_name=None,
            plan_code=None,
            copay_amount=None,
            deductible_remaining=None,
            rejection_reason="Member not found in Ohio Medicaid system",
            response_code="AAF",
            response_message="Unable to locate member - verify Medicaid ID"
        )


@router.post("/soap/claim-status", response_model=MockClaimStatusResponse)
async def mock_claim_status(
    request: MockClaimStatusRequest,
    current_user: dict = Depends(get_current_user)
) -> MockClaimStatusResponse:
    """
    Mock OMES SOAP 276/277 Claim Status Inquiry
    
    Simulates real-time claim status check.
    Returns predictable responses based on claim_number patterns:
    - Claims starting with 'P': Paid
    - Claims starting with 'D': Denied
    - Claims starting with 'R': Pending review
    - Others: Random status
    """
    logger.info(f"Mock claim status check for claim: {request.claim_number}")
    
    transaction_id = f"MOCK-277-{uuid.uuid4().hex[:12].upper()}"
    pccn = f"ODM{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}"
    
    # Determine status based on claim number pattern
    first_char = request.claim_number[0].upper() if request.claim_number else "X"
    
    if first_char == "P":
        # Paid claim
        payment_amount = round(random.uniform(50, 500), 2)
        return MockClaimStatusResponse(
            transaction_id=transaction_id,
            claim_number=request.claim_number,
            payer_claim_control_number=pccn,
            status_code="A1",
            status_category="Accepted",
            status_description="Claim has been paid",
            total_charge=payment_amount + round(random.uniform(0, 20), 2),
            payment_amount=payment_amount,
            patient_responsibility=0.00,
            adjudication_date=(datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            check_number=f"CHK{random.randint(100000, 999999)}",
            effective_date=datetime.now().strftime("%Y-%m-%d"),
            rejection_reasons=[]
        )
    
    elif first_char == "D":
        # Denied claim
        denial_reasons = [
            "Service not covered under patient's benefit plan",
            "Prior authorization required but not obtained",
            "Service exceeds benefit maximum",
            "Duplicate claim - previously processed",
            "Provider not enrolled for this service type"
        ]
        return MockClaimStatusResponse(
            transaction_id=transaction_id,
            claim_number=request.claim_number,
            payer_claim_control_number=pccn,
            status_code="D0",
            status_category="Denied",
            status_description="Claim has been denied",
            total_charge=round(random.uniform(100, 600), 2),
            payment_amount=0.00,
            patient_responsibility=0.00,
            adjudication_date=(datetime.now() - timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            check_number=None,
            effective_date=None,
            rejection_reasons=[random.choice(denial_reasons)]
        )
    
    elif first_char == "R":
        # Pending review
        return MockClaimStatusResponse(
            transaction_id=transaction_id,
            claim_number=request.claim_number,
            payer_claim_control_number=pccn,
            status_code="P3",
            status_category="Pending",
            status_description="Claim is pending - under review",
            total_charge=round(random.uniform(100, 600), 2),
            payment_amount=None,
            patient_responsibility=None,
            adjudication_date=None,
            check_number=None,
            effective_date=None,
            rejection_reasons=[]
        )
    
    else:
        # Random status for testing
        statuses = [
            ("A1", "Accepted", "Claim has been paid", True),
            ("P0", "Pending", "Claim received - processing", False),
            ("P2", "Pending", "Claim pending - waiting for information", False),
            ("R5", "Rejected", "Claim rejected - invalid procedure code", False),
        ]
        status = random.choice(statuses)
        
        return MockClaimStatusResponse(
            transaction_id=transaction_id,
            claim_number=request.claim_number,
            payer_claim_control_number=pccn,
            status_code=status[0],
            status_category=status[1],
            status_description=status[2],
            total_charge=round(random.uniform(100, 600), 2),
            payment_amount=round(random.uniform(50, 500), 2) if status[3] else None,
            patient_responsibility=0.00 if status[3] else None,
            adjudication_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d") if status[3] else None,
            check_number=f"CHK{random.randint(100000, 999999)}" if status[3] else None,
            effective_date=datetime.now().strftime("%Y-%m-%d") if status[3] else None,
            rejection_reasons=["Invalid procedure code"] if status[0] == "R5" else []
        )


# ==================== MOCK SFTP ENDPOINTS ====================

@router.post("/sftp/upload")
async def mock_sftp_upload(
    request: MockFileUploadRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Mock SFTP file upload
    
    Simulates uploading 837 claim files to OMES SFTP inbound folder.
    Files are stored in memory and can be processed to generate mock responses.
    """
    logger.info(f"Mock SFTP upload: {request.filename}")
    
    organization_id = current_user.get("organization_id", "default-org")
    
    # Store file in mock inbound
    file_id = str(uuid.uuid4())
    mock_sftp_inbound[file_id] = {
        "id": file_id,
        "filename": request.filename,
        "content": request.content,
        "file_type": request.file_type,
        "organization_id": organization_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(request.content),
        "status": "received"
    }
    
    # Simulate processing delay message
    response_eta = (datetime.now(timezone.utc) + timedelta(hours=random.randint(2, 24))).isoformat()
    
    return {
        "success": True,
        "message": "File uploaded successfully to mock OMES SFTP",
        "file_id": file_id,
        "filename": request.filename,
        "size_bytes": len(request.content),
        "uploaded_at": mock_sftp_inbound[file_id]["uploaded_at"],
        "expected_response_by": response_eta,
        "mock_note": "This is a mock upload. Use /mock/odm/sftp/generate-835 to create response files."
    }


@router.get("/sftp/list")
async def mock_sftp_list_files(
    folder: str = Query(default="outbound", description="'inbound' or 'outbound'"),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Mock SFTP list files
    
    Lists files in mock SFTP folders.
    - inbound: Uploaded 837 files
    - outbound: Response files (835, 277, 999)
    """
    organization_id = current_user.get("organization_id", "default-org")
    
    if folder == "inbound":
        # Filter by organization
        files = [
            {
                "filename": f["filename"],
                "size_bytes": f["size_bytes"],
                "uploaded_at": f["uploaded_at"],
                "status": f["status"]
            }
            for f in mock_sftp_inbound.values()
            if f.get("organization_id") == organization_id
        ]
    else:  # outbound
        files = [
            {
                "filename": f["filename"],
                "size_bytes": f["size_bytes"],
                "created_at": f["created_at"],
                "file_type": f["file_type"]
            }
            for f in mock_sftp_outbound.values()
            if f.get("organization_id") == organization_id
        ]
    
    return {
        "success": True,
        "folder": folder,
        "file_count": len(files),
        "files": files
    }


@router.get("/sftp/download/{filename}")
async def mock_sftp_download(
    filename: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Mock SFTP download file
    
    Downloads a response file from mock SFTP outbound folder.
    """
    organization_id = current_user.get("organization_id", "default-org")
    
    # Find file
    for file_id, file_data in mock_sftp_outbound.items():
        if file_data["filename"] == filename and file_data.get("organization_id") == organization_id:
            return {
                "success": True,
                "filename": filename,
                "content": file_data["content"],
                "size_bytes": file_data["size_bytes"],
                "file_type": file_data["file_type"],
                "created_at": file_data["created_at"]
            }
    
    raise HTTPException(status_code=404, detail=f"File not found: {filename}")


@router.post("/sftp/generate-835")
async def mock_generate_835(
    request: MockGenerate835Request,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Generate mock 835 remittance advice
    
    Creates a mock 835 Electronic Remittance Advice file based on claim numbers.
    This simulates what OMES would send back after processing claims.
    """
    logger.info(f"Generating mock 835 for claims: {request.claim_numbers}")
    
    organization_id = current_user.get("organization_id", "default-org")
    payment_date = request.payment_date or datetime.now().strftime("%Y-%m-%d")
    
    # Generate mock 835 content
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    control_number = f"{random.randint(100000000, 999999999)}"
    
    # Build simplified 835 structure
    claims_detail = []
    total_payment = 0.0
    
    for claim_num in request.claim_numbers:
        if request.payment_status == "paid":
            charge = round(random.uniform(100, 500), 2)
            payment = charge
            adjustment = 0.00
            status = "1"  # Processed as primary
        elif request.payment_status == "partial":
            charge = round(random.uniform(100, 500), 2)
            adjustment = round(charge * 0.2, 2)
            payment = charge - adjustment
            status = "1"
        else:  # denied
            charge = round(random.uniform(100, 500), 2)
            payment = 0.00
            adjustment = charge
            status = "4"  # Denied
        
        total_payment += payment
        claims_detail.append({
            "claim_number": claim_num,
            "charge_amount": charge,
            "payment_amount": payment,
            "adjustment_amount": adjustment,
            "status_code": status,
            "service_date": (datetime.now() - timedelta(days=random.randint(7, 30))).strftime("%Y%m%d")
        })
    
    # Generate X12 835 format (simplified)
    x12_content = f"""ISA*00*          *00*          *ZZ*ODMITS         *ZZ*{organization_id[:15].ljust(15)}*{timestamp[:6]}*{timestamp[6:10]}*^*00501*{control_number}*0*P*:~
GS*HP*ODMITS*{organization_id[:15]}*{timestamp[:8]}*{timestamp[8:12]}*{control_number}*X*005010X221A1~
ST*835*0001*005010X221A1~
BPR*C*{total_payment:.2f}*C*ACH*CTX*01*031100649*DA*123456789*1234567890**01*031100649*DA*987654321*{payment_date.replace('-', '')}~
TRN*1*{control_number}*1234567890~
REF*EV*ODMFFS~
DTM*405*{payment_date.replace('-', '')}~
N1*PR*OHIO DEPARTMENT OF MEDICAID~
N3*50 WEST TOWN STREET~
N4*COLUMBUS*OH*432150000~
N1*PE*MOCK PROVIDER*XX*1234567890~"""
    
    for idx, claim in enumerate(claims_detail, 1):
        x12_content += f"""
CLP*{claim['claim_number']}*{claim['status_code']}*{claim['charge_amount']:.2f}*{claim['payment_amount']:.2f}**MC*ODM{timestamp}{idx:04d}~
NM1*QC*1*DOE*JOHN****MI*123456789012~
SVC*HC:T1019*{claim['charge_amount']:.2f}*{claim['payment_amount']:.2f}**4~
DTM*472*{claim['service_date']}~"""
        
        if claim['adjustment_amount'] > 0:
            x12_content += f"""
CAS*CO*45*{claim['adjustment_amount']:.2f}~"""
    
    x12_content += f"""
SE*{len(claims_detail) * 6 + 15}*0001~
GE*1*{control_number}~
IEA*1*{control_number}~"""
    
    # Store in mock outbound
    filename = f"835_{organization_id[:10]}_{timestamp}.txt"
    file_id = str(uuid.uuid4())
    
    mock_sftp_outbound[file_id] = {
        "id": file_id,
        "filename": filename,
        "content": x12_content,
        "file_type": "835",
        "organization_id": organization_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(x12_content),
        "claims_processed": len(claims_detail),
        "total_payment": total_payment,
        "payment_status": request.payment_status
    }
    
    return {
        "success": True,
        "message": "Mock 835 remittance generated",
        "filename": filename,
        "file_id": file_id,
        "claims_processed": len(claims_detail),
        "total_payment": round(total_payment, 2),
        "payment_status": request.payment_status,
        "payment_date": payment_date,
        "download_url": f"/api/mock/odm/sftp/download/{filename}"
    }


@router.post("/sftp/generate-999")
async def mock_generate_999(
    original_filename: str = Query(..., description="Filename of uploaded 837"),
    accept: bool = Query(default=True, description="Whether to accept or reject"),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Generate mock 999 functional acknowledgment
    
    Creates a mock 999 acknowledgment for an uploaded 837 file.
    """
    organization_id = current_user.get("organization_id", "default-org")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    control_number = f"{random.randint(100000000, 999999999)}"
    
    if accept:
        status_code = "A"
        status_text = "Accepted"
        error_codes = []
    else:
        status_code = "R"
        status_text = "Rejected"
        error_codes = ["IK502-1: Missing Required Data Element", "IK503-8: Data Element Too Long"]
    
    x12_content = f"""ISA*00*          *00*          *ZZ*ODMITS         *ZZ*{organization_id[:15].ljust(15)}*{timestamp[:6]}*{timestamp[6:10]}*^*00501*{control_number}*0*P*:~
GS*FA*ODMITS*{organization_id[:15]}*{timestamp[:8]}*{timestamp[8:12]}*{control_number}*X*005010~
ST*999*0001*005010~
AK1*HC*{control_number}*005010X223A2~
AK2*837*0001*005010X223A2~
IK5*{status_code}~
AK9*{status_code}*1*1*{"1" if accept else "0"}~
SE*6*0001~
GE*1*{control_number}~
IEA*1*{control_number}~"""
    
    filename = f"999_{organization_id[:10]}_{timestamp}.txt"
    file_id = str(uuid.uuid4())
    
    mock_sftp_outbound[file_id] = {
        "id": file_id,
        "filename": filename,
        "content": x12_content,
        "file_type": "999",
        "organization_id": organization_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(x12_content),
        "original_file": original_filename,
        "status": status_text
    }
    
    return {
        "success": True,
        "message": f"Mock 999 acknowledgment generated - {status_text}",
        "filename": filename,
        "status": status_text,
        "error_codes": error_codes,
        "download_url": f"/api/mock/odm/sftp/download/{filename}"
    }


# ==================== UTILITY ENDPOINTS ====================

@router.get("/status")
async def mock_odm_status() -> dict:
    """
    Get mock ODM system status
    
    Returns simulated status of OMES systems.
    """
    return {
        "success": True,
        "mock_mode": True,
        "message": "Mock ODM endpoints are active",
        "systems": {
            "soap_eligibility": {
                "status": "online",
                "endpoint": "/api/mock/odm/soap/eligibility",
                "description": "Mock 270/271 eligibility verification"
            },
            "soap_claim_status": {
                "status": "online", 
                "endpoint": "/api/mock/odm/soap/claim-status",
                "description": "Mock 276/277 claim status inquiry"
            },
            "sftp_upload": {
                "status": "online",
                "endpoint": "/api/mock/odm/sftp/upload",
                "description": "Mock 837 file upload"
            },
            "sftp_responses": {
                "status": "online",
                "endpoint": "/api/mock/odm/sftp/list",
                "description": "Mock response file listing (835, 999)"
            }
        },
        "inbound_files_count": len(mock_sftp_inbound),
        "outbound_files_count": len(mock_sftp_outbound),
        "note": "These are mock endpoints for testing. Real OMES integration requires valid credentials."
    }


@router.delete("/reset")
async def mock_reset_data(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Reset mock data
    
    Clears all mock SFTP files for the organization.
    """
    organization_id = current_user.get("organization_id", "default-org")
    
    # Clear inbound
    inbound_removed = 0
    keys_to_remove = [k for k, v in mock_sftp_inbound.items() if v.get("organization_id") == organization_id]
    for key in keys_to_remove:
        del mock_sftp_inbound[key]
        inbound_removed += 1
    
    # Clear outbound
    outbound_removed = 0
    keys_to_remove = [k for k, v in mock_sftp_outbound.items() if v.get("organization_id") == organization_id]
    for key in keys_to_remove:
        del mock_sftp_outbound[key]
        outbound_removed += 1
    
    return {
        "success": True,
        "message": "Mock data reset",
        "inbound_files_removed": inbound_removed,
        "outbound_files_removed": outbound_removed
    }
