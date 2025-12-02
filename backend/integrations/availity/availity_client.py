"""Availity Clearinghouse Client

Handles:
- REST API for real-time transactions
- SFTP for batch submissions (optional)
- Eligibility verification (270/271)
- Claim status (276/277)
- Claims submission (837)
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from .auth import AvailityAuthManager

logger = logging.getLogger(__name__)


class AvailityClient:
    """Client for Availity clearinghouse integration"""
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Initialize Availity client
        
        Args:
            api_key: Availity API key
            client_secret: Availity client secret
            base_url: Availity base URL
        """
        self.base_url = base_url or os.getenv(
            "AVAILITY_BASE_URL",
            "https://api.availity.com"
        )
        
        # Initialize auth manager
        self.auth_manager = AvailityAuthManager(
            api_key=api_key,
            client_secret=client_secret,
            base_url=self.base_url
        )
    
    def verify_eligibility(self,
                          payer_id: str,
                          member_id: str,
                          patient_first_name: str,
                          patient_last_name: str,
                          patient_dob: str,
                          service_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify patient eligibility (270/271 transaction)
        
        Args:
            payer_id: Payer identifier
            member_id: Patient member ID
            patient_first_name: Patient first name
            patient_last_name: Patient last name
            patient_dob: Patient date of birth (YYYY-MM-DD)
            service_type: Optional service type code
        
        Returns:
            Eligibility response data
        """
        try:
            headers = self.auth_manager.get_auth_headers()
            
            payload = {
                "payerId": payer_id,
                "memberId": member_id,
                "patientFirstName": patient_first_name,
                "patientLastName": patient_last_name,
                "patientBirthDate": patient_dob
            }
            
            if service_type:
                payload["serviceType"] = service_type
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/v1/coverages",
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Availity eligibility verified for member {member_id}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Availity eligibility check failed: {str(e)}")
            raise Exception(f"Availity eligibility verification failed: {str(e)}")
    
    def check_claim_status(self,
                          payer_id: str,
                          claim_number: str,
                          provider_npi: Optional[str] = None) -> Dict[str, Any]:
        """
        Check claim status (276/277 transaction)
        
        Args:
            payer_id: Payer identifier
            claim_number: Claim number
            provider_npi: Optional provider NPI
        
        Returns:
            Claim status response data
        """
        try:
            headers = self.auth_manager.get_auth_headers()
            
            payload = {
                "payerId": payer_id,
                "claimNumber": claim_number
            }
            
            if provider_npi:
                payload["providerNpi"] = provider_npi
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/v1/claim-status",
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Availity claim status checked for {claim_number}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Availity claim status check failed: {str(e)}")
            raise Exception(f"Availity claim status check failed: {str(e)}")
    
    def submit_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit claim via Availity API
        
        Args:
            claim_data: Claim data (format TBD based on Availity requirements)
        
        Returns:
            Submission response
        """
        try:
            headers = self.auth_manager.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/v1/claims",
                    headers=headers,
                    json=claim_data,
                    timeout=60
                )
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Claim submitted via Availity")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Availity claim submission failed: {str(e)}")
            raise Exception(f"Availity claim submission failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test Availity API connection
        
        Returns:
            True if connection successful
        """
        try:
            # Try to get a token
            token = self.auth_manager.get_access_token()
            logger.info("Availity connection test successful")
            return True
        except Exception as e:
            logger.error(f"Availity connection test failed: {str(e)}")
            return False
