"""
Ohio Medicaid EVV Export Module
Exports data in JSON format compliant with Ohio EVV specifications
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
import json
import logging

from evv_utils import (
    DateTimeUtils,
    SequenceManager,
    CoordinateValidator,
    PayerProgramValidator
)

logger = logging.getLogger(__name__)


class EVVIndividualExporter:
    """Export Individual (Patient) data in EVV format"""
    
    @staticmethod
    def export_individual(patient_data: Dict, business_entity_id: str, 
                         business_entity_medicaid_id: str) -> Dict:
        """
        Export single patient to EVV Individual format
        Maps PatientProfile fields to Ohio EVV Individual specification
        
        Args:
            patient_data: Patient profile dictionary from PatientProfile model
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Dict in EVV Individual JSON format
        """
        # Generate sequence ID if not present
        sequence_id = patient_data.get('sequence_id') or SequenceManager.generate_sequence_id()
        
        # Build Individual record - all required EVV fields
        individual = {
            "BusinessEntityID": business_entity_id,
            "BusinessEntityMedicaidIdentifier": business_entity_medicaid_id,
            "PatientOtherID": patient_data.get('patient_other_id') or patient_data.get('id', ''),
            "SequenceID": sequence_id,
            "PatientMedicaidID": patient_data.get('medicaid_number', '').zfill(12),  # Ensure 12 digits with leading zeros
            "IsPatientNewborn": patient_data.get('is_newborn', False),
            "PatientLastName": patient_data.get('last_name', ''),
            "PatientFirstName": patient_data.get('first_name', ''),
            "PatientTimeZone": patient_data.get('timezone', 'America/New_York')
        }
        
        # Add default payer information for Ohio Medicaid if not provided
        # In production, this would link to patient's insurance contracts
        payer_info_list = []
        default_payer = {
            "Payer": "ODM",  # Ohio Department of Medicaid
            "PayerProgram": "Medicaid Fee-For-Service",
            "ProcedureCode": "T1019"  # Personal Care Services
        }
        
        # Add PIMS ID for ODA payers if available
        if patient_data.get('pims_id'):
            default_payer["PayerClientIdentifier"] = patient_data['pims_id']
        
        payer_info_list.append(default_payer)
        individual["IndividualPayerInformation"] = payer_info_list
        
        # Build address with coordinates - REQUIRED for EVV
        address = {
            "PatientAddressType": patient_data.get('address_type', 'Home'),
            "PatientAddressIsPrimary": True,
            "PatientAddressLine1": patient_data.get('address_street', ''),
            "PatientCity": patient_data.get('address_city', ''),
            "PatientState": patient_data.get('address_state', ''),
            "PatientZip": patient_data.get('address_zip', ''),
            "PatientTimeZone": patient_data.get('timezone', 'America/New_York')
        }
        
        # Add coordinates if available (REQUIRED by Ohio EVV)
        if patient_data.get('address_latitude') is not None and patient_data.get('address_longitude') is not None:
            try:
                lat = float(patient_data['address_latitude'])
                lon = float(patient_data['address_longitude'])
                if CoordinateValidator.validate_coordinates(lat, lon):
                    address["PatientAddressLatitude"] = lat
                    address["PatientAddressLongitude"] = lon
            except (ValueError, TypeError):
                # Skip invalid coordinates
                pass
        
        individual["IndividualAddress"] = [address]
        
        # Add phone numbers if available (optional but recommended)
        if patient_data.get('phone_numbers') and len(patient_data['phone_numbers']) > 0:
            phone_list = []
            for phone in patient_data['phone_numbers']:
                phone_item = {
                    "PatientPhoneType": phone.get('phone_type', 'Mobile'),
                    "PatientPhoneNumber": phone.get('phone_number', '')
                }
                phone_list.append(phone_item)
            if phone_list:
                individual["IndividualPhone"] = phone_list
        
        # Add responsible party if available (required for minors/guardianship)
        if patient_data.get('responsible_party'):
            rp = patient_data['responsible_party']
            if isinstance(rp, dict):
                responsible_party = {
                    "PatientResponsiblePartyLastName": rp.get('last_name', ''),
                    "PatientResponsiblePartyFirstName": rp.get('first_name', '')
                }
                if rp.get('phone_number'):
                    responsible_party["PatientResponsiblePartyPhone"] = rp['phone_number']
                if rp.get('email'):
                    responsible_party["PatientResponsiblePartyEmail"] = rp['email']
                individual["ResponsibleParty"] = responsible_party
        
        return individual


class EVVDirectCareWorkerExporter:
    """Export Direct Care Worker (Employee) data in EVV format"""
    
    @staticmethod
    def export_dcw(employee_data: Dict, business_entity_id: str, 
                   business_entity_medicaid_id: str) -> Dict:
        """
        Export single employee to EVV DirectCareWorker format
        
        Args:
            employee_data: Employee profile dictionary
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Dict in EVV DirectCareWorker JSON format
        """
        # Generate sequence ID if not present
        sequence_id = employee_data.get('sequence_id') or SequenceManager.generate_sequence_id()
        
        # Build DirectCareWorker record
        dcw = {
            "BusinessEntityID": business_entity_id,
            "BusinessEntityMedicaidIdentifier": business_entity_medicaid_id,
            "StaffOtherID": employee_data.get('staff_other_id') or employee_data['id'],
            "SequenceID": sequence_id,
            "StaffID": employee_data.get('staff_pin') or employee_data.get('employee_id', ''),
            "StaffSSN": employee_data['ssn'].replace('-', '').replace(' ', ''),  # 9 digits
            "StaffLastName": employee_data['last_name'],
            "StaffFirstName": employee_data['first_name']
        }
        
        # Add optional fields
        if employee_data.get('email'):
            dcw["StaffEmail"] = employee_data['email']
        
        if employee_data.get('staff_position'):
            dcw["StaffPosition"] = employee_data['staff_position']
        
        return dcw


class EVVVisitExporter:
    """Export Visit data in EVV format"""
    
    @staticmethod
    def export_visit(visit_data: Dict, business_entity_id: str, 
                    business_entity_medicaid_id: str) -> Dict:
        """
        Export single visit to EVV Visit format
        
        Args:
            visit_data: EVV visit dictionary
            business_entity_id: Business entity ID
            business_entity_medicaid_id: Business entity Medicaid ID
            
        Returns:
            Dict in EVV Visit JSON format
        """
        # Generate sequence ID if not present
        sequence_id = visit_data.get('sequence_id') or SequenceManager.generate_sequence_id()
        
        # Build Visit record
        visit = {
            "BusinessEntityID": business_entity_id,
            "BusinessEntityMedicaidIdentifier": business_entity_medicaid_id,
            "VisitOtherID": visit_data['visit_other_id'],
            "SequenceID": sequence_id,
            "StaffOtherID": visit_data['staff_other_id'],
            "PatientOtherID": visit_data['patient_other_id'],
            "PatientMedicaidID": visit_data['patient_medicaid_id'],
            "VisitCancelledIndicator": visit_data.get('visit_cancelled_indicator', False),
            "Payer": visit_data['payer'],
            "PayerProgram": visit_data['payer_program'],
            "ProcedureCode": visit_data['procedure_code'],
            "TimeZone": visit_data.get('timezone', 'America/New_York'),
            "BillVisit": visit_data.get('bill_visit', True),
            "MemberVerifiedTimes": visit_data.get('member_verified_times', False),
            "MemberVerifiedService": visit_data.get('member_verified_service', False)
        }
        
        # Add optional fields
        if visit_data.get('patient_alternate_id'):
            visit["PatientAlternateID"] = visit_data['patient_alternate_id']
        
        if visit_data.get('client_payer_id'):
            visit["ClientPayerID"] = visit_data['client_payer_id']
        
        if visit_data.get('adj_in_datetime'):
            visit["AdjInDateTime"] = visit_data['adj_in_datetime']
        
        if visit_data.get('adj_out_datetime'):
            visit["AdjOutDateTime"] = visit_data['adj_out_datetime']
        
        if visit_data.get('hours_to_bill'):
            visit["HoursToBill"] = visit_data['hours_to_bill']
        
        if visit_data.get('visit_memo'):
            visit["VisitMemo"] = visit_data['visit_memo']
        
        if visit_data.get('member_signature_available'):
            visit["MemberSignatureAvailable"] = visit_data['member_signature_available']
        
        if visit_data.get('member_voice_recording'):
            visit["MemberVoiceRecording"] = visit_data['member_voice_recording']
        
        # Add call records
        if visit_data.get('calls'):
            call_list = []
            for call in visit_data['calls']:
                call_item = {
                    "CallExternalID": call['call_external_id'],
                    "CallDateTime": call['call_datetime'],
                    "CallAssignment": call['call_assignment'],
                    "CallType": call['call_type']
                }
                
                # Add optional call fields
                if call.get('procedure_code'):
                    call_item["ProcedureCode"] = call['procedure_code']
                if call.get('patient_identifier_on_call'):
                    call_item["PatientIdentifierOnCall"] = call['patient_identifier_on_call']
                if call.get('mobile_login'):
                    call_item["MobileLogin"] = call['mobile_login']
                if call.get('call_latitude'):
                    call_item["CallLatitude"] = call['call_latitude']
                if call.get('call_longitude'):
                    call_item["CallLongitude"] = call['call_longitude']
                if call.get('telephony_pin'):
                    call_item["TelephonyPIN"] = call['telephony_pin']
                if call.get('originating_phone_number'):
                    call_item["OriginatingPhoneNumber"] = call['originating_phone_number']
                
                call_list.append(call_item)
            
            if call_list:
                visit["Calls"] = call_list
        
        # Add exception acknowledgements
        if visit_data.get('exceptions'):
            exception_list = []
            for exception in visit_data['exceptions']:
                exception_item = {
                    "ExceptionID": exception['exception_id'],
                    "ExceptionAcknowledged": exception['exception_acknowledged']
                }
                exception_list.append(exception_item)
            
            if exception_list:
                visit["VisitExceptionAcknowledgement"] = exception_list
        
        # Add visit change records
        if visit_data.get('visit_changes'):
            change_list = []
            for change in visit_data['visit_changes']:
                change_item = {
                    "SequenceID": change['sequence_id'],
                    "ChangeMadeByEmail": change['change_made_by_email'],
                    "ChangeDateTime": change['change_datetime'],
                    "ReasonCode": change['reason_code'],
                    "ChangeReasonMemo": change['change_reason_memo'],
                    "ResolutionCode": change.get('resolution_code', 'A')
                }
                change_list.append(change_item)
            
            if change_list:
                visit["VisitChanges"] = change_list
        
        return visit


class EVVExportOrchestrator:
    """Main orchestrator for EVV exports"""
    
    @staticmethod
    def export_individuals(patients: List[Dict], business_entity_id: str,
                          business_entity_medicaid_id: str) -> str:
        """
        Export multiple patients to EVV JSON format
        
        Returns:
            JSON string with array of Individual records
        """
        individuals = []
        for patient in patients:
            try:
                individual = EVVIndividualExporter.export_individual(
                    patient, business_entity_id, business_entity_medicaid_id
                )
                individuals.append(individual)
            except Exception as e:
                logger.error(f"Error exporting patient {patient.get('id')}: {e}")
        
        return json.dumps(individuals, indent=2)
    
    @staticmethod
    def export_direct_care_workers(employees: List[Dict], business_entity_id: str,
                                   business_entity_medicaid_id: str) -> str:
        """
        Export multiple employees to EVV JSON format
        
        Returns:
            JSON string with array of DirectCareWorker records
        """
        dcws = []
        for employee in employees:
            try:
                dcw = EVVDirectCareWorkerExporter.export_dcw(
                    employee, business_entity_id, business_entity_medicaid_id
                )
                dcws.append(dcw)
            except Exception as e:
                logger.error(f"Error exporting employee {employee.get('id')}: {e}")
        
        return json.dumps(dcws, indent=2)
    
    @staticmethod
    def export_visits(visits: List[Dict], business_entity_id: str,
                     business_entity_medicaid_id: str) -> str:
        """
        Export multiple visits to EVV JSON format
        
        Returns:
            JSON string with array of Visit records
        """
        visit_list = []
        for visit_data in visits:
            try:
                visit = EVVVisitExporter.export_visit(
                    visit_data, business_entity_id, business_entity_medicaid_id
                )
                visit_list.append(visit)
            except Exception as e:
                logger.error(f"Error exporting visit {visit_data.get('id')}: {e}")
        
        return json.dumps(visit_list, indent=2)
    
    @staticmethod
    def validate_export_limits(record_count: int, record_type: str) -> Dict:
        """
        Validate export against EVV transmission limits
        
        Args:
            record_count: Number of records to export
            record_type: "Individual", "Staff", or "Visit"
            
        Returns:
            Validation result dictionary
        """
        # Transaction size limits
        max_records_per_transaction = 5000
        
        # Hourly transaction limits
        hourly_limits = {
            "Visit": 500,
            "Staff": 100,
            "Individual": 100
        }
        
        # Maximum records per hour
        max_records_per_hour = {
            "Visit": 2500000,
            "Staff": 500000,
            "Individual": 500000
        }
        
        issues = []
        
        if record_count > max_records_per_transaction:
            issues.append(f"Record count ({record_count}) exceeds max per transaction ({max_records_per_transaction})")
        
        if record_count > max_records_per_hour.get(record_type, 0):
            issues.append(f"Record count ({record_count}) exceeds max per hour for {record_type}")
        
        return {
            "valid": len(issues) == 0,
            "record_count": record_count,
            "record_type": record_type,
            "issues": issues
        }
