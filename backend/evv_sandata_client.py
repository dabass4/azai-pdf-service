"""
Sandata EVV Aggregator Client
Real implementation for submitting EVV data to Sandata
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

from evv_aggregator_base import EVVAggregatorBase, EVVSubmissionResult

logger = logging.getLogger(__name__)


class SandataEVVClient(EVVAggregatorBase):
    """
    Sandata EVV API client for Ohio Medicaid
    
    API Documentation: https://www.sandata.com/api-docs
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Sandata-specific configuration
        self.username = config.get('username')
        self.password = config.get('password')
        self.company_id = config.get('company_id')
        
        # API endpoints (adjust based on Sandata docs)
        self.base_url = self.api_url.rstrip('/')
        self.auth_endpoint = f"{self.base_url}/auth/token"
        self.individuals_endpoint = f"{self.base_url}/evv/individuals"
        self.dcw_endpoint = f"{self.base_url}/evv/direct-care-workers"
        self.visits_endpoint = f"{self.base_url}/evv/visits"
        self.status_endpoint = f"{self.base_url}/evv/status"
        
        self._access_token = None
        self._token_expires = None
    
    def _get_auth_token(self) -> str:
        """
        Authenticate with Sandata API and get access token
        
        Returns:
            Access token for API requests
        """
        # Check if token is still valid
        if self._access_token and self._token_expires:
            if datetime.now(timezone.utc) < self._token_expires:
                return self._access_token
        
        try:
            logger.info("Authenticating with Sandata API...")
            
            auth_payload = {
                "username": self.username,
                "password": self.password,
                "company_id": self.company_id,
                "grant_type": "password"
            }
            
            response = requests.post(
                self.auth_endpoint,
                json=auth_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)  # Default 1 hour
            
            # Set expiration (with 5 min buffer)
            from datetime import timedelta
            self._token_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)
            
            logger.info("Sandata authentication successful")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Sandata authentication failed: {e}")
            raise Exception(f"Failed to authenticate with Sandata: {str(e)}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Make authenticated request to Sandata API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint URL
            data: Request payload
            
        Returns:
            Response JSON
        """
        token = self._get_auth_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(endpoint, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(
                    endpoint,
                    json=data,
                    headers=headers,
                    timeout=30
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Sandata API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Error response: {error_data}")
                except:
                    logger.error(f"Error response text: {e.response.text}")
            raise
    
    def submit_individuals(self, individuals_data: List[Dict]) -> EVVSubmissionResult:
        """
        Submit individual/patient records to Sandata
        
        Args:
            individuals_data: List of patient records
            
        Returns:
            EVVSubmissionResult
        """
        try:
            logger.info(f"Submitting {len(individuals_data)} individuals to Sandata...")
            
            # Transform data to Sandata format
            sandata_payload = {
                "business_entity_id": self.business_entity_id,
                "submission_date": datetime.now(timezone.utc).isoformat(),
                "test_mode": self.test_mode,
                "individuals": []
            }
            
            for individual in individuals_data:
                sandata_individual = self._transform_individual(individual)
                sandata_payload["individuals"].append(sandata_individual)
            
            # Submit to Sandata
            response = self._make_request(
                'POST',
                self.individuals_endpoint,
                sandata_payload
            )
            
            # Parse response
            transaction_id = response.get('transaction_id') or response.get('id')
            status = response.get('status', 'unknown')
            
            success = status in ['accepted', 'success', 'completed']
            
            logger.info(f"Sandata individuals submission: {status} (TxID: {transaction_id})")
            
            return EVVSubmissionResult(
                success=success,
                transaction_id=transaction_id,
                message=f"Submitted {len(individuals_data)} individuals to Sandata",
                response_data=response
            )
            
        except Exception as e:
            logger.error(f"Failed to submit individuals to Sandata: {e}")
            return EVVSubmissionResult(
                success=False,
                message=f"Submission failed: {str(e)}",
                errors=[str(e)]
            )
    
    def submit_direct_care_workers(self, dcw_data: List[Dict]) -> EVVSubmissionResult:
        """
        Submit direct care worker records to Sandata
        
        Args:
            dcw_data: List of employee/DCW records
            
        Returns:
            EVVSubmissionResult
        """
        try:
            logger.info(f"Submitting {len(dcw_data)} DCWs to Sandata...")
            
            sandata_payload = {
                "business_entity_id": self.business_entity_id,
                "submission_date": datetime.now(timezone.utc).isoformat(),
                "test_mode": self.test_mode,
                "direct_care_workers": []
            }
            
            for dcw in dcw_data:
                sandata_dcw = self._transform_dcw(dcw)
                sandata_payload["direct_care_workers"].append(sandata_dcw)
            
            response = self._make_request(
                'POST',
                self.dcw_endpoint,
                sandata_payload
            )
            
            transaction_id = response.get('transaction_id') or response.get('id')
            status = response.get('status', 'unknown')
            success = status in ['accepted', 'success', 'completed']
            
            logger.info(f"Sandata DCW submission: {status} (TxID: {transaction_id})")
            
            return EVVSubmissionResult(
                success=success,
                transaction_id=transaction_id,
                message=f"Submitted {len(dcw_data)} DCWs to Sandata",
                response_data=response
            )
            
        except Exception as e:
            logger.error(f"Failed to submit DCWs to Sandata: {e}")
            return EVVSubmissionResult(
                success=False,
                message=f"Submission failed: {str(e)}",
                errors=[str(e)]
            )
    
    def submit_visits(self, visits_data: List[Dict]) -> EVVSubmissionResult:
        """
        Submit visit records (service events) to Sandata
        
        Args:
            visits_data: List of visit/service records
            
        Returns:
            EVVSubmissionResult
        """
        try:
            logger.info(f"Submitting {len(visits_data)} visits to Sandata...")
            
            sandata_payload = {
                "business_entity_id": self.business_entity_id,
                "submission_date": datetime.now(timezone.utc).isoformat(),
                "test_mode": self.test_mode,
                "visits": []
            }
            
            for visit in visits_data:
                sandata_visit = self._transform_visit(visit)
                sandata_payload["visits"].append(sandata_visit)
            
            response = self._make_request(
                'POST',
                self.visits_endpoint,
                sandata_payload
            )
            
            transaction_id = response.get('transaction_id') or response.get('id')
            status = response.get('status', 'unknown')
            success = status in ['accepted', 'success', 'completed']
            
            logger.info(f"Sandata visits submission: {status} (TxID: {transaction_id})")
            
            return EVVSubmissionResult(
                success=success,
                transaction_id=transaction_id,
                message=f"Submitted {len(visits_data)} visits to Sandata",
                response_data=response
            )
            
        except Exception as e:
            logger.error(f"Failed to submit visits to Sandata: {e}")
            return EVVSubmissionResult(
                success=False,
                message=f"Submission failed: {str(e)}",
                errors=[str(e)]
            )
    
    def get_submission_status(self, transaction_id: str) -> Dict:
        """
        Check status of previous submission
        
        Args:
            transaction_id: Transaction ID from Sandata
            
        Returns:
            Status information
        """
        try:
            endpoint = f"{self.status_endpoint}/{transaction_id}"
            response = self._make_request('GET', endpoint)
            return response
            
        except Exception as e:
            logger.error(f"Failed to get submission status: {e}")
            return {
                "error": str(e),
                "transaction_id": transaction_id
            }
    
    def test_connection(self) -> bool:
        """
        Test connection to Sandata API
        
        Returns:
            True if successful, False otherwise
        """
        try:
            token = self._get_auth_token()
            return bool(token)
        except Exception as e:
            logger.error(f"Sandata connection test failed: {e}")
            return False
    
    # Data transformation methods
    
    def _transform_individual(self, individual: Dict) -> Dict:
        """Transform our format to Sandata individual format"""
        return {
            "individual_id": individual.get('id'),
            "medicaid_id": individual.get('medicaid_number'),
            "first_name": individual.get('first_name'),
            "last_name": individual.get('last_name'),
            "date_of_birth": individual.get('date_of_birth'),
            "gender": individual.get('gender'),
            "phone": individual.get('phone'),
            "email": individual.get('email'),
            "address": {
                "street": individual.get('street_address'),
                "city": individual.get('city'),
                "state": individual.get('state', 'OH'),
                "zip": individual.get('zip_code')
            },
            "coordinates": {
                "latitude": individual.get('latitude'),
                "longitude": individual.get('longitude')
            },
            "responsible_party": individual.get('responsible_party', {}),
            "payer_info": individual.get('payer_info', [])
        }
    
    def _transform_dcw(self, dcw: Dict) -> Dict:
        """Transform our format to Sandata DCW format"""
        return {
            "dcw_id": dcw.get('id'),
            "employee_id": dcw.get('employee_id'),
            "npi": dcw.get('npi'),
            "first_name": dcw.get('first_name'),
            "last_name": dcw.get('last_name'),
            "date_of_birth": dcw.get('date_of_birth'),
            "ssn": dcw.get('ssn'),
            "phone": dcw.get('phone'),
            "email": dcw.get('email'),
            "staff_pin": dcw.get('staff_pin'),
            "position_code": dcw.get('staff_position_code'),
            "hire_date": dcw.get('hire_date'),
            "status": dcw.get('employment_status')
        }
    
    def _transform_visit(self, visit: Dict) -> Dict:
        """Transform our format to Sandata visit format"""
        return {
            "visit_id": visit.get('id'),
            "individual_id": visit.get('patient_id'),
            "dcw_id": visit.get('employee_id'),
            "service_date": visit.get('service_date'),
            "check_in_time": visit.get('time_in'),
            "check_out_time": visit.get('time_out'),
            "service_code": visit.get('service_code'),
            "units": visit.get('units'),
            "location": {
                "latitude": visit.get('latitude'),
                "longitude": visit.get('longitude')
            },
            "visit_type": visit.get('visit_type', 'Scheduled'),
            "payer_id": visit.get('payer_id'),
            "notes": visit.get('notes')
        }
