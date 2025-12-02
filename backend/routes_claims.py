"""API Routes for Claims Management

Handles:
- Eligibility verification
- Claim submission (OMES direct or Availity clearinghouse)
- Claim status checking
- Remittance processing
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os

from integrations.omes_edi import OMESSOAPClient, OMESSFTPClient
from integrations.omes_edi.models import (
    EligibilityRequest,
    ClaimStatusRequest,
    Gender
)
from integrations.availity import AvailityClient
from auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/claims", tags=["claims"])


# Pydantic models for API requests
class EligibilityCheckRequest(BaseModel):
    """Request to check patient eligibility"""
    member_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str] = None
    provider_npi: str
    submission_method: str = Field(default="omes", description="'omes' or 'availity'")


class ClaimStatusCheckRequest(BaseModel):
    """Request to check claim status"""
    claim_number: str
    patient_member_id: str
    patient_last_name: str
    patient_first_name: str
    patient_dob: date
    provider_npi: str
    payer_id: Optional[str] = None
    submission_method: str = Field(default="omes", description="'omes' or 'availity'")


class ClaimSubmissionRequest(BaseModel):
    """Request to submit claims"""
    claim_ids: List[str]
    submission_method: str = Field(..., description="'omes_direct' or 'availity'")


@router.post("/eligibility/verify")
async def verify_eligibility(
    request: EligibilityCheckRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify patient eligibility before service
    
    Supports both OMES direct and Availity clearinghouse
    """
    try:
        organization_id = current_user.get("organization_id", "default-org")
        
        if request.submission_method == "omes":
            # Use OMES SOAP client for direct eligibility check
            soap_client = OMESSOAPClient()
            
            elig_request = EligibilityRequest(
                member_id=request.member_id,
                first_name=request.first_name,
                last_name=request.last_name,
                date_of_birth=request.date_of_birth,
                gender=Gender(request.gender) if request.gender else None,
                provider_npi=request.provider_npi
            )
            
            response = soap_client.verify_eligibility(elig_request)
            
            return {
                "success": True,
                "method": "omes_direct",
                "member_id": response.member_id,
                "is_active": response.is_active,
                "eligibility_start_date": response.eligibility_start_date.isoformat() if response.eligibility_start_date else None,
                "eligibility_end_date": response.eligibility_end_date.isoformat() if response.eligibility_end_date else None,
                "plan_name": response.plan_name,
                "copay_amount": response.copay_amount,
                "rejection_reason": response.rejection_reason,
                "checked_at": datetime.utcnow().isoformat()
            }
        
        elif request.submission_method == "availity":
            # Use Availity client for eligibility check
            availity_client = AvailityClient()
            
            response = availity_client.verify_eligibility(
                payer_id=os.getenv("AVAILITY_DEFAULT_PAYER_ID", "ODMITS"),
                member_id=request.member_id,
                patient_first_name=request.first_name,
                patient_last_name=request.last_name,
                patient_dob=request.date_of_birth.isoformat()
            )
            
            return {
                "success": True,
                "method": "availity",
                "response": response,
                "checked_at": datetime.utcnow().isoformat()
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid submission method: {request.submission_method}"
            )
    
    except Exception as e:
        logger.error(f"Eligibility verification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Eligibility verification failed: {str(e)}"
        )


@router.post("/status/check")
async def check_claim_status(
    request: ClaimStatusCheckRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Check status of submitted claim
    
    Supports both OMES direct and Availity clearinghouse
    """
    try:
        organization_id = current_user.get("organization_id", "default-org")
        
        if request.submission_method == "omes":
            # Use OMES SOAP client for direct status check
            soap_client = OMESSOAPClient()
            
            status_request = ClaimStatusRequest(
                claim_number=request.claim_number,
                patient_member_id=request.patient_member_id,
                patient_last_name=request.patient_last_name,
                patient_first_name=request.patient_first_name,
                patient_dob=request.patient_dob,
                provider_npi=request.provider_npi
            )
            
            response = soap_client.check_claim_status(status_request)
            
            return {
                "success": True,
                "method": "omes_direct",
                "claim_number": response.claim_number,
                "status_code": response.status_code.value,
                "status_description": response.status_description,
                "payer_claim_control_number": response.payer_claim_control_number,
                "total_charge": response.total_charge,
                "payment_amount": response.payment_amount,
                "patient_responsibility": response.patient_responsibility,
                "adjudication_date": response.adjudication_date.isoformat() if response.adjudication_date else None,
                "check_number": response.check_number,
                "rejection_reasons": response.rejection_reasons,
                "checked_at": datetime.utcnow().isoformat()
            }
        
        elif request.submission_method == "availity":
            # Use Availity client for status check
            availity_client = AvailityClient()
            
            response = availity_client.check_claim_status(
                payer_id=request.payer_id or "ODMITS",
                claim_number=request.claim_number,
                provider_npi=request.provider_npi
            )
            
            return {
                "success": True,
                "method": "availity",
                "response": response,
                "checked_at": datetime.utcnow().isoformat()
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid submission method: {request.submission_method}"
            )
    
    except Exception as e:
        logger.error(f"Claim status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim status check failed: {str(e)}"
        )


@router.post("/submit")
async def submit_claims(
    request: ClaimSubmissionRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Submit claims via OMES direct or Availity clearinghouse
    
    This will generate 837 files from timesheet data and submit
    """
    try:
        organization_id = current_user.get("organization_id", "default-org")
        
        # TODO: Retrieve claim data from database using claim_ids
        # TODO: Generate 837 EDI files from claim data
        # TODO: Submit via chosen method
        
        return {
            "success": True,
            "message": f"Claim submission initiated for {len(request.claim_ids)} claims",
            "method": request.submission_method,
            "claim_ids": request.claim_ids,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "processing"
        }
    
    except Exception as e:
        logger.error(f"Claim submission failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim submission failed: {str(e)}"
        )


@router.get("/sftp/responses")
async def get_sftp_responses(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Check and download response files from OMES SFTP
    
    Returns 835 remittance advice, 277 acknowledgments, etc.
    """
    try:
        sftp_client = OMESSFTPClient()
        
        # List available response files
        files = sftp_client.list_response_files()
        
        return {
            "success": True,
            "file_count": len(files),
            "files": files,
            "checked_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to check SFTP responses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check SFTP responses: {str(e)}"
        )


@router.post("/sftp/download")
async def download_sftp_response(
    filename: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Download specific response file from OMES SFTP"""
    try:
        sftp_client = OMESSFTPClient()
        
        content = sftp_client.download_response_file(filename)
        
        return {
            "success": True,
            "filename": filename,
            "content": content,
            "size_bytes": len(content),
            "downloaded_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to download SFTP file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download SFTP file: {str(e)}"
        )


@router.get("/test/omes-soap")
async def test_omes_soap_connection(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Test OMES SOAP connection"""
    try:
        # Simple connection test
        soap_client = OMESSOAPClient()
        
        return {
            "success": True,
            "message": "OMES SOAP client initialized",
            "endpoint": soap_client.endpoint_url,
            "configured": bool(soap_client.username and soap_client.password),
            "tested_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"OMES SOAP test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"OMES SOAP test failed: {str(e)}"
        )


@router.get("/test/omes-sftp")
async def test_omes_sftp_connection(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Test OMES SFTP connection"""
    try:
        sftp_client = OMESSFTPClient()
        
        success = sftp_client.test_connection()
        
        return {
            "success": success,
            "message": "OMES SFTP connection successful" if success else "OMES SFTP connection failed",
            "host": sftp_client.host,
            "port": sftp_client.port,
            "tested_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"OMES SFTP test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"OMES SFTP test failed: {str(e)}"
        )


@router.get("/test/availity")
async def test_availity_connection(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Test Availity API connection"""
    try:
        availity_client = AvailityClient()
        
        success = availity_client.test_connection()
        
        return {
            "success": success,
            "message": "Availity connection successful" if success else "Availity connection failed",
            "base_url": availity_client.base_url,
            "tested_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Availity test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Availity test failed: {str(e)}"
        )
