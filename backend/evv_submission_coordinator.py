"""
EVV Submission Coordinator
Orchestrates the complete workflow: EVV submission → Claim generation → ODM submission
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import asyncio

from evv_aggregator_factory import get_default_evv_client
from evv_aggregator_base import EVVSubmissionResult

logger = logging.getLogger(__name__)


class EVVSubmissionCoordinator:
    """
    Coordinates EVV submissions and subsequent claim generation
    Ensures proper sequencing: EVV MUST be submitted BEFORE 837P claims
    """
    
    def __init__(self, db, evv_client=None):
        """
        Initialize coordinator
        
        Args:
            db: Database connection
            evv_client: EVV client (if None, creates default)
        """
        self.db = db
        self.evv_client = evv_client or get_default_evv_client()
    
    async def submit_timesheet_to_evv(
        self,
        timesheet_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Submit a single timesheet's data to EVV aggregator
        
        Args:
            timesheet_id: Timesheet ID
            organization_id: Organization ID (for isolation)
            
        Returns:
            Dict with submission results
        """
        try:
            # Fetch timesheet
            timesheet = await self.db.timesheets.find_one({
                "id": timesheet_id,
                "organization_id": organization_id
            }, {"_id": 0})
            
            if not timesheet:
                return {
                    "success": False,
                    "error": f"Timesheet {timesheet_id} not found"
                }
            
            # Extract visit data from timesheet
            visits_data = await self._extract_visits_from_timesheet(
                timesheet,
                organization_id
            )
            
            if not visits_data:
                return {
                    "success": False,
                    "error": "No valid visit data in timesheet"
                }
            
            # Submit to EVV aggregator
            logger.info(f"Submitting {len(visits_data)} visits to EVV for timesheet {timesheet_id}")
            result = self.evv_client.submit_visits(visits_data)
            
            # Save EVV submission record
            await self._save_evv_submission_record(
                timesheet_id=timesheet_id,
                organization_id=organization_id,
                submission_type="visits",
                result=result,
                data_count=len(visits_data)
            )
            
            # Update timesheet with EVV transaction ID
            if result.success:
                await self.db.timesheets.update_one(
                    {"id": timesheet_id},
                    {
                        "$set": {
                            "evv_submitted": True,
                            "evv_transaction_id": result.transaction_id,
                            "evv_submitted_at": datetime.now(timezone.utc)
                        }
                    }
                )
            
            return {
                "success": result.success,
                "transaction_id": result.transaction_id,
                "message": result.message,
                "errors": result.errors,
                "visits_count": len(visits_data)
            }
            
        except Exception as e:
            logger.error(f"Error submitting timesheet to EVV: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def submit_batch_to_evv(
        self,
        timesheet_ids: List[str],
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Submit multiple timesheets to EVV in batch
        
        Args:
            timesheet_ids: List of timesheet IDs
            organization_id: Organization ID
            
        Returns:
            Dict with batch submission results
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(timesheet_ids)
        }
        
        for timesheet_id in timesheet_ids:
            result = await self.submit_timesheet_to_evv(timesheet_id, organization_id)
            
            if result.get('success'):
                results['successful'].append({
                    "timesheet_id": timesheet_id,
                    "transaction_id": result.get('transaction_id')
                })
            else:
                results['failed'].append({
                    "timesheet_id": timesheet_id,
                    "error": result.get('error')
                })
        
        results['success_count'] = len(results['successful'])
        results['failure_count'] = len(results['failed'])
        
        return results
    
    async def submit_patients_to_evv(
        self,
        organization_id: str,
        patient_ids: Optional[List[str]] = None
    ) -> EVVSubmissionResult:
        """
        Submit patient/individual records to EVV
        
        Args:
            organization_id: Organization ID
            patient_ids: Specific patient IDs (if None, submits all)
            
        Returns:
            EVVSubmissionResult
        """
        try:
            # Build query
            query = {"organization_id": organization_id}
            if patient_ids:
                query["id"] = {"$in": patient_ids}
            
            # Fetch patients
            patients = await self.db.patients.find(query, {"_id": 0}).to_list(length=None)
            
            if not patients:
                return EVVSubmissionResult(
                    success=False,
                    message="No patients found to submit"
                )
            
            logger.info(f"Submitting {len(patients)} patients to EVV")
            result = self.evv_client.submit_individuals(patients)
            
            # Save submission record
            await self._save_evv_submission_record(
                timesheet_id=None,
                organization_id=organization_id,
                submission_type="individuals",
                result=result,
                data_count=len(patients)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting patients to EVV: {e}")
            return EVVSubmissionResult(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
    
    async def submit_employees_to_evv(
        self,
        organization_id: str,
        employee_ids: Optional[List[str]] = None
    ) -> EVVSubmissionResult:
        """
        Submit employee/DCW records to EVV
        
        Args:
            organization_id: Organization ID
            employee_ids: Specific employee IDs (if None, submits all)
            
        Returns:
            EVVSubmissionResult
        """
        try:
            query = {"organization_id": organization_id}
            if employee_ids:
                query["id"] = {"$in": employee_ids}
            
            employees = await self.db.employees.find(query, {"_id": 0}).to_list(length=None)
            
            if not employees:
                return EVVSubmissionResult(
                    success=False,
                    message="No employees found to submit"
                )
            
            logger.info(f"Submitting {len(employees)} employees to EVV")
            result = self.evv_client.submit_direct_care_workers(employees)
            
            await self._save_evv_submission_record(
                timesheet_id=None,
                organization_id=organization_id,
                submission_type="direct_care_workers",
                result=result,
                data_count=len(employees)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting employees to EVV: {e}")
            return EVVSubmissionResult(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
    
    async def verify_evv_before_claim(
        self,
        timesheet_ids: List[str],
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Verify that all timesheets have been submitted to EVV before generating claim
        
        Args:
            timesheet_ids: List of timesheet IDs for claim
            organization_id: Organization ID
            
        Returns:
            Dict with verification results
        """
        unsubmitted = []
        submitted = []
        
        for timesheet_id in timesheet_ids:
            timesheet = await self.db.timesheets.find_one({
                "id": timesheet_id,
                "organization_id": organization_id
            }, {"_id": 0, "evv_submitted": 1, "evv_transaction_id": 1})
            
            if not timesheet:
                continue
            
            if timesheet.get('evv_submitted') and timesheet.get('evv_transaction_id'):
                submitted.append({
                    "timesheet_id": timesheet_id,
                    "transaction_id": timesheet.get('evv_transaction_id')
                })
            else:
                unsubmitted.append(timesheet_id)
        
        can_generate_claim = len(unsubmitted) == 0
        
        return {
            "can_generate_claim": can_generate_claim,
            "submitted_count": len(submitted),
            "unsubmitted_count": len(unsubmitted),
            "unsubmitted_timesheets": unsubmitted,
            "submitted_timesheets": submitted,
            "message": "All timesheets have EVV records" if can_generate_claim else "Some timesheets missing EVV submission"
        }
    
    async def _extract_visits_from_timesheet(
        self,
        timesheet: Dict,
        organization_id: str
    ) -> List[Dict]:
        """
        Extract visit records from timesheet data
        
        Args:
            timesheet: Timesheet document
            organization_id: Organization ID
            
        Returns:
            List of visit records in EVV format
        """
        visits = []
        
        extracted = timesheet.get('extracted_data', {})
        entries = extracted.get('entries', [])
        patient_id = timesheet.get('patient_id')
        
        # Fetch patient for additional details
        patient = await self.db.patients.find_one({
            "id": patient_id,
            "organization_id": organization_id
        }, {"_id": 0}) if patient_id else None
        
        for entry in entries:
            # Get employee ID
            employee_name = entry.get('employee_name', '')
            employee = await self.db.employees.find_one({
                "organization_id": organization_id,
                "$or": [
                    {"first_name": {"$regex": employee_name.split()[0] if employee_name else "", "$options": "i"}},
                    {"employee_id": {"$regex": employee_name, "$options": "i"}}
                ]
            }, {"_id": 0}) if employee_name else None
            
            visit = {
                "id": f"{timesheet['id']}_{entry.get('date', '')}",
                "patient_id": patient_id,
                "employee_id": employee.get('id') if employee else None,
                "service_date": entry.get('date'),
                "time_in": entry.get('time_in'),
                "time_out": entry.get('time_out'),
                "service_code": entry.get('service_code', 'T1019'),
                "units": entry.get('units'),
                "latitude": patient.get('latitude') if patient else None,
                "longitude": patient.get('longitude') if patient else None,
                "visit_type": "Scheduled",
                "payer_id": patient.get('medicaid_number') if patient else None,
                "notes": entry.get('notes', '')
            }
            
            visits.append(visit)
        
        return visits
    
    async def _save_evv_submission_record(
        self,
        organization_id: str,
        submission_type: str,
        result: EVVSubmissionResult,
        data_count: int,
        timesheet_id: Optional[str] = None
    ):
        """Save EVV submission record to database"""
        import uuid
        
        record = {
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "timesheet_id": timesheet_id,
            "submission_type": submission_type,
            "success": result.success,
            "transaction_id": result.transaction_id,
            "message": result.message,
            "errors": result.errors,
            "data_count": data_count,
            "vendor": self.evv_client.get_vendor_name(),
            "submitted_at": datetime.now(timezone.utc),
            "response_data": result.response_data
        }
        
        await self.db.evv_submissions.insert_one(record)
        logger.info(f"Saved EVV submission record: {record['id']}")
