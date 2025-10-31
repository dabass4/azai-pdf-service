"""
Ohio Medicaid EVV Submission Module
Mock implementation of Ohio EVV Aggregator API for testing
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
import json
import logging
import uuid

from evv_utils import TransactionIDGenerator, SequenceManager

logger = logging.getLogger(__name__)


class OhioEVVAggregator:
    """
    Mock Ohio Department of Medicaid EVV Aggregator
    Simulates the Sandata Aggregator API for EVV submissions
    """
    
    def __init__(self):
        # In-memory storage for mock submissions
        self.submissions = {}
        self.rejections = {}
    
    def submit_records(self, record_type: str, records: List[Dict], 
                      business_entity_id: str, business_entity_medicaid_id: str) -> Dict:
        """
        Submit records to EVV Aggregator (MOCKED)
        
        Args:
            record_type: "Individual", "Staff", or "Visit"
            records: List of record dictionaries
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Response with transaction ID and acknowledgment
        """
        # Generate transaction ID
        transaction_id = TransactionIDGenerator.generate()
        
        # Validate record count
        if len(records) < 1 or len(records) > 5000:
            return {
                "status": "rejected",
                "reason": f"Invalid record count: {len(records)}. Must be between 1 and 5000.",
                "transaction_id": None
            }
        
        # Simulate validation of records
        rejected_records = []
        accepted_records = []
        
        for record in records:
            # Simulate validation
            validation_result = self._validate_record(record, record_type)
            
            if validation_result["valid"]:
                accepted_records.append(record)
            else:
                rejected_records.append({
                    "record_other_id": record.get(f"{record_type.lower()}_other_id", 
                                                 record.get("VisitOtherID", 
                                                 record.get("PatientOtherID",
                                                 record.get("StaffOtherID", "unknown")))),
                    "reasons": validation_result["errors"]
                })
        
        # Store submission
        submission_data = {
            "transaction_id": transaction_id,
            "record_type": record_type,
            "record_count": len(records),
            "accepted_count": len(accepted_records),
            "rejected_count": len(rejected_records),
            "business_entity_id": business_entity_id,
            "business_entity_medicaid_id": business_entity_medicaid_id,
            "submission_datetime": datetime.now(timezone.utc).isoformat(),
            "status": "partial" if rejected_records else "accepted"
        }
        
        self.submissions[transaction_id] = submission_data
        
        if rejected_records:
            self.rejections[transaction_id] = rejected_records
        
        # Build acknowledgment response
        ack_response = {
            "BusinessEntityID": business_entity_id,
            "BusinessEntityMedicaidIdentifier": business_entity_medicaid_id,
            "TransactionID": transaction_id,
            "Reason": f"Transaction received. {len(accepted_records)} accepted, {len(rejected_records)} rejected."
        }
        
        logger.info(f"[MOCK EVV] Transaction {transaction_id}: {ack_response['Reason']}")
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "acknowledgment": ack_response,
            "accepted_count": len(accepted_records),
            "rejected_count": len(rejected_records),
            "has_rejections": len(rejected_records) > 0
        }
    
    def query_transaction_status(self, transaction_id: str, 
                                business_entity_id: str,
                                business_entity_medicaid_id: str) -> Dict:
        """
        Query status of a transaction (MOCKED)
        
        Args:
            transaction_id: Transaction ID to query
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Status response with rejection details if any
        """
        if transaction_id not in self.submissions:
            return {
                "status": "not_found",
                "message": f"Transaction {transaction_id} not found"
            }
        
        submission = self.submissions[transaction_id]
        
        # Check if there are rejections
        rejected_records = self.rejections.get(transaction_id, [])
        
        response = {
            "status": "success",
            "transaction_id": transaction_id,
            "record_type": submission["record_type"],
            "total_records": submission["record_count"],
            "accepted_records": submission["accepted_count"],
            "rejected_records": submission["rejected_count"],
            "submission_datetime": submission["submission_datetime"],
            "overall_status": submission["status"]
        }
        
        if rejected_records:
            # Build rejection details in EVV format
            rejection_list = []
            for rejection in rejected_records:
                rejection_item = {
                    "BusinessEntityID": business_entity_id,
                    "BusinessEntityMedicaidIdentifier": business_entity_medicaid_id,
                    "RecordType": submission["record_type"],
                    "RecordOtherID": rejection["record_other_id"],
                    "Reason": "; ".join(rejection["reasons"])
                }
                rejection_list.append(rejection_item)
            
            response["rejections"] = rejection_list
        
        return response
    
    def _validate_record(self, record: Dict, record_type: str) -> Dict:
        """
        Validate a single record (MOCK validation)
        
        Returns:
            Dict with validation result
        """
        errors = []
        
        # Common required fields
        if not record.get("BusinessEntityID"):
            errors.append("Missing BusinessEntityID")
        
        if not record.get("BusinessEntityMedicaidIdentifier"):
            errors.append("Missing BusinessEntityMedicaidIdentifier")
        
        if not record.get("SequenceID"):
            errors.append("Missing SequenceID")
        
        # Record-specific validation
        if record_type == "Individual":
            if not record.get("PatientOtherID"):
                errors.append("Missing PatientOtherID")
            if not record.get("PatientLastName"):
                errors.append("Missing PatientLastName")
            if not record.get("PatientFirstName"):
                errors.append("Missing PatientFirstName")
            if not record.get("IndividualAddress"):
                errors.append("Missing IndividualAddress")
            else:
                # Check for coordinates in at least one address
                has_coords = False
                for addr in record["IndividualAddress"]:
                    if addr.get("PatientAddressLatitude") and addr.get("PatientAddressLongitude"):
                        has_coords = True
                        break
                if not has_coords:
                    errors.append("At least one address must have latitude and longitude")
        
        elif record_type == "Staff":
            if not record.get("StaffOtherID"):
                errors.append("Missing StaffOtherID")
            if not record.get("StaffID"):
                errors.append("Missing StaffID")
            if not record.get("StaffSSN"):
                errors.append("Missing StaffSSN")
            if not record.get("StaffLastName"):
                errors.append("Missing StaffLastName")
            if not record.get("StaffFirstName"):
                errors.append("Missing StaffFirstName")
        
        elif record_type == "Visit":
            if not record.get("VisitOtherID"):
                errors.append("Missing VisitOtherID")
            if not record.get("StaffOtherID"):
                errors.append("Missing StaffOtherID")
            if not record.get("PatientOtherID"):
                errors.append("Missing PatientOtherID")
            if not record.get("PatientMedicaidID"):
                errors.append("Missing PatientMedicaidID")
            if not record.get("Payer"):
                errors.append("Missing Payer")
            if not record.get("PayerProgram"):
                errors.append("Missing PayerProgram")
            if not record.get("ProcedureCode"):
                errors.append("Missing ProcedureCode")
            
            # Check for at least one call with coordinates if GPS type
            if record.get("Calls"):
                for call in record["Calls"]:
                    if call.get("CallType") in ["Mobile", "Telephony"]:
                        if call.get("CallAssignment") == "Call In":
                            if not (call.get("CallLatitude") and call.get("CallLongitude")):
                                errors.append(f"Call In must have latitude and longitude for {call.get('CallType')}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_all_transactions(self) -> List[Dict]:
        """Get all transactions (for admin/testing)"""
        return list(self.submissions.values())


# Singleton instance
_aggregator_instance = None

def get_evv_aggregator() -> OhioEVVAggregator:
    """Get singleton EVV aggregator instance"""
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = OhioEVVAggregator()
    return _aggregator_instance


class EVVSubmissionService:
    """Service for managing EVV submissions"""
    
    def __init__(self):
        self.aggregator = get_evv_aggregator()
    
    def submit_individuals(self, individuals_json: str, business_entity_id: str,
                          business_entity_medicaid_id: str) -> Dict:
        """
        Submit Individual records
        
        Args:
            individuals_json: JSON string with Individual records
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Submission result
        """
        try:
            individuals = json.loads(individuals_json)
            if not isinstance(individuals, list):
                individuals = [individuals]
            
            result = self.aggregator.submit_records(
                "Individual", individuals, 
                business_entity_id, business_entity_medicaid_id
            )
            
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error submitting individuals: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def submit_direct_care_workers(self, dcws_json: str, business_entity_id: str,
                                   business_entity_medicaid_id: str) -> Dict:
        """
        Submit DirectCareWorker records
        
        Args:
            dcws_json: JSON string with DCW records
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Submission result
        """
        try:
            dcws = json.loads(dcws_json)
            if not isinstance(dcws, list):
                dcws = [dcws]
            
            result = self.aggregator.submit_records(
                "Staff", dcws,
                business_entity_id, business_entity_medicaid_id
            )
            
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error submitting DCWs: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def submit_visits(self, visits_json: str, business_entity_id: str,
                     business_entity_medicaid_id: str) -> Dict:
        """
        Submit Visit records
        
        Args:
            visits_json: JSON string with Visit records
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Submission result
        """
        try:
            visits = json.loads(visits_json)
            if not isinstance(visits, list):
                visits = [visits]
            
            result = self.aggregator.submit_records(
                "Visit", visits,
                business_entity_id, business_entity_medicaid_id
            )
            
            return result
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error submitting visits: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def query_status(self, transaction_id: str, business_entity_id: str,
                    business_entity_medicaid_id: str) -> Dict:
        """Query submission status"""
        return self.aggregator.query_transaction_status(
            transaction_id, business_entity_id, business_entity_medicaid_id
        )
