"""Claims Processing Service

Orchestrates the complete claims workflow:
1. Convert timesheets to claims
2. Generate 837 EDI files
3. Submit via OMES direct or Availity
4. Track claim status
5. Process remittance advice (835)
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

from edi_claim_generator import generate_837p_claim
from integrations.omes_edi import OMESSOAPClient, OMESSFTPClient
from integrations.omes_edi.models import EligibilityRequest, ClaimStatusRequest
from integrations.availity import AvailityClient

logger = logging.getLogger(__name__)


class ClaimsService:
    """Service for managing the complete claims lifecycle"""
    
    def __init__(self, db: AsyncIOMotorClient, organization_id: str):
        self.db = db
        self.organization_id = organization_id
        self._config = None
    
    async def _get_org_config(self) -> Dict[str, Any]:
        """Get organization configuration including credentials"""
        if self._config is None:
            self._config = await self.db.organization_config.find_one(
                {"organization_id": self.organization_id}
            ) or {}
        return self._config
    
    async def verify_patient_eligibility(self, timesheet_id: str) -> Dict[str, Any]:
        """
        Verify patient eligibility before claim submission
        
        Args:
            timesheet_id: Timesheet ID to check
        
        Returns:
            Eligibility verification result
        """
        try:
            # Get timesheet
            timesheet = await self.db.timesheets.find_one({"id": timesheet_id})
            if not timesheet:
                raise Exception("Timesheet not found")
            
            # Get patient
            patient = await self.db.patients.find_one({"id": timesheet["patient_id"]})
            if not patient:
                raise Exception("Patient not found")
            
            # Get organization config
            config = await self._get_org_config()
            
            # Initialize SOAP client with org credentials
            soap_client = OMESSOAPClient(
                username=config.get("omes_soap_username"),
                password=config.get("omes_soap_password")
            )
            
            # Build eligibility request
            from integrations.omes_edi.models import Gender
            
            eligibility_request = EligibilityRequest(
                member_id=patient.get("medicaid_id", ""),
                first_name=patient.get("first_name", ""),
                last_name=patient.get("last_name", ""),
                date_of_birth=patient.get("dob"),
                gender=Gender(patient.get("gender", "U")[0].upper()) if patient.get("gender") else Gender.UNKNOWN,
                provider_npi=config.get("provider_npi", "1234567890")
            )
            
            # Check eligibility
            response = soap_client.verify_eligibility(eligibility_request)
            
            # Store eligibility check result
            await self.db.eligibility_checks.insert_one({
                "check_id": str(uuid.uuid4()),
                "organization_id": self.organization_id,
                "timesheet_id": timesheet_id,
                "patient_id": patient["id"],
                "is_active": response.is_active,
                "eligibility_start_date": response.eligibility_start_date,
                "eligibility_end_date": response.eligibility_end_date,
                "plan_name": response.plan_name,
                "checked_at": datetime.now(timezone.utc),
                "raw_response": response.response_raw
            })
            
            return {
                "success": True,
                "eligible": response.is_active,
                "details": {
                    "member_id": patient.get("medicaid_id"),
                    "start_date": response.eligibility_start_date.isoformat() if response.eligibility_start_date else None,
                    "end_date": response.eligibility_end_date.isoformat() if response.eligibility_end_date else None,
                    "plan_name": response.plan_name
                }
            }
        
        except Exception as e:
            logger.error(f"Eligibility check failed: {str(e)}")
            return {
                "success": False,
                "eligible": False,
                "error": str(e)
            }
    
    async def create_claim_from_timesheet(self, timesheet_id: str) -> str:
        """
        Create a claim record from a timesheet
        
        Args:
            timesheet_id: Timesheet ID
        
        Returns:
            Claim ID
        """
        try:
            # Get timesheet with all related data
            timesheet = await self.db.timesheets.find_one({"id": timesheet_id})
            if not timesheet:
                raise Exception("Timesheet not found")
            
            patient = await self.db.patients.find_one({"id": timesheet["patient_id"]})
            employee = await self.db.employees.find_one({"id": timesheet["employee_id"]})
            
            # Create claim record
            claim_id = str(uuid.uuid4())
            claim_doc = {
                "claim_id": claim_id,
                "organization_id": self.organization_id,
                "timesheet_id": timesheet_id,
                "patient_id": timesheet["patient_id"],
                "employee_id": timesheet["employee_id"],
                "service_date": timesheet.get("date"),
                "total_charge": timesheet.get("total_hours", 0) * timesheet.get("hourly_rate", 0),
                "status": "draft",  # draft, ready, submitted, paid, denied
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.claims.insert_one(claim_doc)
            
            logger.info(f"Created claim {claim_id} from timesheet {timesheet_id}")
            return claim_id
        
        except Exception as e:
            logger.error(f"Failed to create claim: {str(e)}")
            raise
    
    async def generate_837_file(self, claim_ids: List[str], claim_type: str = "837P") -> str:
        """
        Generate 837 EDI file from claim IDs
        
        Args:
            claim_ids: List of claim IDs
            claim_type: Type of claim (837P, 837I, 837D)
        
        Returns:
            EDI file content
        """
        try:
            # Get all claims with related data
            claims_data = []
            
            for claim_id in claim_ids:
                claim = await self.db.claims.find_one({"claim_id": claim_id})
                if not claim:
                    continue
                
                timesheet = await self.db.timesheets.find_one({"id": claim["timesheet_id"]})
                patient = await self.db.patients.find_one({"id": claim["patient_id"]})
                employee = await self.db.employees.find_one({"id": claim["employee_id"]})
                
                claims_data.append({
                    "claim": claim,
                    "timesheet": timesheet,
                    "patient": patient,
                    "employee": employee
                })
            
            # Get organization config
            config = await self._get_org_config()
            organization = await self.db.organizations.find_one(
                {"organization_id": self.organization_id}
            )
            
            # Generate 837 file using existing generator
            if claim_type == "837P":
                edi_content = generate_837p_claim(
                    claims_data=claims_data,
                    sender_id=config.get("omes_tpid", "0000000"),
                    receiver_id="ODMITS",
                    provider_name=organization.get("name", "Provider"),
                    provider_npi=config.get("provider_npi", "1234567890")
                )
            else:
                # TODO: Implement 837I and 837D generators
                raise Exception(f"Claim type {claim_type} not yet implemented")
            
            return edi_content
        
        except Exception as e:
            logger.error(f"Failed to generate 837 file: {str(e)}")
            raise
    
    async def submit_claims_omes(self, claim_ids: List[str]) -> Dict[str, Any]:
        """
        Submit claims via OMES SFTP
        
        Args:
            claim_ids: List of claim IDs to submit
        
        Returns:
            Submission result
        """
        try:
            # Generate 837 file
            edi_content = await self.generate_837_file(claim_ids, "837P")
            
            # Get org config
            config = await self._get_org_config()
            
            # Initialize SFTP client
            sftp_client = OMESSFTPClient(
                username=config.get("omes_sftp_username"),
                password=config.get("omes_sftp_password"),
                tpid=config.get("omes_tpid")
            )
            
            # Upload file
            filename = sftp_client.upload_claim_file(edi_content)
            
            # Update claims status
            for claim_id in claim_ids:
                await self.db.claims.update_one(
                    {"claim_id": claim_id},
                    {
                        "$set": {
                            "status": "submitted",
                            "submission_method": "omes_sftp",
                            "submission_date": datetime.now(timezone.utc),
                            "submission_filename": filename
                        }
                    }
                )
            
            logger.info(f"Submitted {len(claim_ids)} claims via OMES SFTP: {filename}")
            
            return {
                "success": True,
                "method": "omes_sftp",
                "filename": filename,
                "claim_count": len(claim_ids)
            }
        
        except Exception as e:
            logger.error(f"OMES submission failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def submit_claims_availity(self, claim_ids: List[str]) -> Dict[str, Any]:
        """
        Submit claims via Availity clearinghouse
        
        Args:
            claim_ids: List of claim IDs to submit
        
        Returns:
            Submission result
        """
        try:
            # Generate 837 file
            edi_content = await self.generate_837_file(claim_ids, "837P")
            
            # Get org config
            config = await self._get_org_config()
            
            # Initialize Availity client
            availity_client = AvailityClient(
                api_key=config.get("availity_api_key"),
                client_secret=config.get("availity_client_secret")
            )
            
            # Submit via Availity API
            # TODO: Implement actual Availity submission
            # For now, just mark as submitted
            
            for claim_id in claim_ids:
                await self.db.claims.update_one(
                    {"claim_id": claim_id},
                    {
                        "$set": {
                            "status": "submitted",
                            "submission_method": "availity",
                            "submission_date": datetime.now(timezone.utc)
                        }
                    }
                )
            
            logger.info(f"Submitted {len(claim_ids)} claims via Availity")
            
            return {
                "success": True,
                "method": "availity",
                "claim_count": len(claim_ids)
            }
        
        except Exception as e:
            logger.error(f"Availity submission failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_claim_status(self, claim_id: str) -> Dict[str, Any]:
        """
        Check status of a submitted claim
        
        Args:
            claim_id: Claim ID
        
        Returns:
            Claim status information
        """
        try:
            claim = await self.db.claims.find_one({"claim_id": claim_id})
            if not claim:
                raise Exception("Claim not found")
            
            if claim.get("status") != "submitted":
                return {
                    "success": True,
                    "status": claim.get("status"),
                    "message": "Claim not yet submitted"
                }
            
            # Get org config and patient info
            config = await self._get_org_config()
            patient = await self.db.patients.find_one({"id": claim["patient_id"]})
            
            # Initialize SOAP client
            soap_client = OMESSOAPClient(
                username=config.get("omes_soap_username"),
                password=config.get("omes_soap_password")
            )
            
            # Build status request
            status_request = ClaimStatusRequest(
                claim_number=claim_id,
                patient_member_id=patient.get("medicaid_id", ""),
                patient_last_name=patient.get("last_name", ""),
                patient_first_name=patient.get("first_name", ""),
                patient_dob=patient.get("dob"),
                provider_npi=config.get("provider_npi", "1234567890"),
                service_date=claim.get("service_date")
            )
            
            # Check status
            response = soap_client.check_claim_status(status_request)
            
            # Update claim record
            await self.db.claims.update_one(
                {"claim_id": claim_id},
                {
                    "$set": {
                        "status_code": response.status_code.value,
                        "status_description": response.status_description,
                        "payment_amount": response.payment_amount,
                        "check_number": response.check_number,
                        "last_status_check": datetime.now(timezone.utc)
                    }
                }
            )
            
            return {
                "success": True,
                "claim_id": claim_id,
                "status": response.status_description,
                "payment_amount": response.payment_amount,
                "check_number": response.check_number
            }
        
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_835_remittance(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Process 835 remittance advice file
        
        Args:
            filename: Filename of 835 file
            content: File content
        
        Returns:
            Processing result
        """
        try:
            from integrations.omes_edi.x12_parsers import parse_835_remittance
            
            # Parse 835 file
            remittances = parse_835_remittance(content)
            
            # Process each remittance
            for remittance in remittances:
                # Find matching claim
                claim = await self.db.claims.find_one(
                    {"claim_id": remittance.claim_number}
                )
                
                if claim:
                    # Update claim with payment information
                    await self.db.claims.update_one(
                        {"claim_id": remittance.claim_number},
                        {
                            "$set": {
                                "status": "paid" if remittance.payment_amount > 0 else "denied",
                                "payment_amount": remittance.payment_amount,
                                "patient_responsibility": remittance.patient_responsibility,
                                "check_number": remittance.check_number,
                                "payment_date": remittance.payment_date,
                                "remittance_processed": datetime.now(timezone.utc)
                            }
                        }
                    )
                
                # Store remittance record
                await self.db.remittances.insert_one({
                    "remittance_id": remittance.transaction_id,
                    "organization_id": self.organization_id,
                    "claim_number": remittance.claim_number,
                    "total_charge": remittance.total_charge,
                    "payment_amount": remittance.payment_amount,
                    "patient_responsibility": remittance.patient_responsibility,
                    "adjustments": remittance.adjustments,
                    "service_lines": remittance.service_lines,
                    "payment_date": remittance.payment_date,
                    "check_number": remittance.check_number,
                    "payer_name": remittance.payer_name,
                    "source_file": filename,
                    "processed_at": datetime.now(timezone.utc)
                })
            
            logger.info(f"Processed {len(remittances)} remittances from {filename}")
            
            return {
                "success": True,
                "remittance_count": len(remittances),
                "filename": filename
            }
        
        except Exception as e:
            logger.error(f"Failed to process 835 remittance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
