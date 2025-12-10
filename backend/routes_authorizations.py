"""
Patient Authorization API Routes

Endpoints for managing:
- Service authorizations for patients
- Employee-patient assignments
- Employee service qualifications
- Care team management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone, date
import logging

from patient_authorizations import (
    ServiceAuthorization,
    EmployeePatientAssignment,
    EmployeeServiceQualification,
    PatientCareTeam,
    AuthorizationValidator
)
from auth import get_current_user, get_organization_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/authorizations", tags=["authorizations"])

# Database will be injected
db = None

def set_db(database):
    global db
    db = database


# ========================================
# SERVICE AUTHORIZATIONS
# ========================================

@router.post("/service-authorizations")
async def create_service_authorization(
    authorization: ServiceAuthorization,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Create a new service authorization for a patient
    
    Example: Authorize Patient X for 160 units/month of Personal Care (T1019)
    """
    try:
        authorization.organization_id = organization_id
        
        # Verify patient exists
        patient = await db.patients.find_one(
            {"id": authorization.patient_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        authorization.patient_name = f"{patient['first_name']} {patient['last_name']}"
        
        # Verify service code exists
        service = await db.service_codes.find_one(
            {"id": authorization.service_code_id},
            {"_id": 0}
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service code not found")
        
        # Insert authorization
        doc = authorization.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        doc['start_date'] = doc['start_date'].isoformat()
        doc['end_date'] = doc['end_date'].isoformat()
        if doc.get('last_service_date'):
            doc['last_service_date'] = doc['last_service_date'].isoformat()
        
        await db.service_authorizations.insert_one(doc)
        
        logger.info(
            f"Service authorization created: {authorization.id} - "
            f"Patient: {authorization.patient_name}, "
            f"Service: {authorization.service_name}"
        )
        
        return {
            "status": "success",
            "message": "Service authorization created",
            "authorization": authorization
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create service authorization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service-authorizations")
async def get_service_authorizations(
    patient_id: Optional[str] = None,
    status: Optional[str] = "active",
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get service authorizations
    Filter by patient_id and/or status
    """
    try:
        query = {"organization_id": organization_id}
        if patient_id:
            query["patient_id"] = patient_id
        if status:
            query["status"] = status
        
        authorizations = await db.service_authorizations.find(query, {"_id": 0}).to_list(1000)
        
        # Validate each authorization
        for auth_doc in authorizations:
            auth = ServiceAuthorization(**auth_doc)
            validation = AuthorizationValidator.is_authorization_valid(auth)
            auth_doc["validation"] = validation
        
        return {
            "status": "success",
            "count": len(authorizations),
            "authorizations": authorizations
        }
    
    except Exception as e:
        logger.error(f"Get service authorizations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service-authorizations/{auth_id}")
async def get_service_authorization(
    auth_id: str,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get a specific service authorization
    """
    try:
        authorization = await db.service_authorizations.find_one(
            {"id": auth_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not authorization:
            raise HTTPException(status_code=404, detail="Authorization not found")
        
        # Validate
        auth = ServiceAuthorization(**authorization)
        validation = AuthorizationValidator.is_authorization_valid(auth)
        authorization["validation"] = validation
        
        return {"status": "success", "authorization": authorization}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get service authorization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# EMPLOYEE-PATIENT ASSIGNMENTS
# ========================================

@router.post("/employee-assignments")
async def create_employee_assignment(
    assignment: EmployeePatientAssignment,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Assign an employee to work with a patient
    
    Example: Assign John Doe to provide care for Jane Smith
    """
    try:
        assignment.organization_id = organization_id
        
        # Verify employee exists
        employee = await db.employees.find_one(
            {"id": assignment.employee_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        assignment.employee_name = f"{employee['first_name']} {employee['last_name']}"
        
        # Verify patient exists
        patient = await db.patients.find_one(
            {"id": assignment.patient_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        assignment.patient_name = f"{patient['first_name']} {patient['last_name']}"
        
        # Insert assignment
        doc = assignment.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        doc['start_date'] = doc['start_date'].isoformat()
        if doc.get('end_date'):
            doc['end_date'] = doc['end_date'].isoformat()
        
        await db.employee_patient_assignments.insert_one(doc)
        
        logger.info(
            f"Employee assignment created: {assignment.id} - "
            f"Employee: {assignment.employee_name}, "
            f"Patient: {assignment.patient_name}"
        )
        
        return {
            "status": "success",
            "message": "Employee assigned to patient",
            "assignment": assignment
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create employee assignment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee-assignments")
async def get_employee_assignments(
    employee_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    status: Optional[str] = "active",
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get employee-patient assignments
    Filter by employee_id, patient_id, and/or status
    """
    try:
        query = {"organization_id": organization_id}
        if employee_id:
            query["employee_id"] = employee_id
        if patient_id:
            query["patient_id"] = patient_id
        if status:
            query["status"] = status
        
        assignments = await db.employee_patient_assignments.find(query, {"_id": 0}).to_list(1000)
        
        return {
            "status": "success",
            "count": len(assignments),
            "assignments": assignments
        }
    
    except Exception as e:
        logger.error(f"Get employee assignments error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# EMPLOYEE SERVICE QUALIFICATIONS
# ========================================

@router.post("/employee-qualifications")
async def create_employee_qualification(
    qualification: EmployeeServiceQualification,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Add service qualification for an employee
    
    Example: Certify John Doe for Personal Care services
    """
    try:
        qualification.organization_id = organization_id
        
        # Verify employee exists
        employee = await db.employees.find_one(
            {"id": qualification.employee_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        qualification.employee_name = f"{employee['first_name']} {employee['last_name']}"
        
        # Verify service code exists
        service = await db.service_codes.find_one(
            {"id": qualification.service_code_id},
            {"_id": 0}
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service code not found")
        
        # Insert qualification
        doc = qualification.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        if doc.get('certification_date'):
            doc['certification_date'] = doc['certification_date'].isoformat()
        if doc.get('expiration_date'):
            doc['expiration_date'] = doc['expiration_date'].isoformat()
        if doc.get('training_date'):
            doc['training_date'] = doc['training_date'].isoformat()
        
        await db.employee_service_qualifications.insert_one(doc)
        
        logger.info(
            f"Employee qualification created: {qualification.id} - "
            f"Employee: {qualification.employee_name}, "
            f"Service: {qualification.service_name}"
        )
        
        return {
            "status": "success",
            "message": "Employee qualification added",
            "qualification": qualification
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create employee qualification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee-qualifications")
async def get_employee_qualifications(
    employee_id: Optional[str] = None,
    service_code_id: Optional[str] = None,
    status: Optional[str] = "active",
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get employee service qualifications
    """
    try:
        query = {"organization_id": organization_id}
        if employee_id:
            query["employee_id"] = employee_id
        if service_code_id:
            query["service_code_id"] = service_code_id
        if status:
            query["status"] = status
        
        qualifications = await db.employee_service_qualifications.find(query, {"_id": 0}).to_list(1000)
        
        return {
            "status": "success",
            "count": len(qualifications),
            "qualifications": qualifications
        }
    
    except Exception as e:
        logger.error(f"Get employee qualifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# CARE TEAM MANAGEMENT
# ========================================

@router.get("/care-team/{patient_id}")
async def get_patient_care_team(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get complete care team for a patient
    
    Returns:
    - All assigned employees
    - All service authorizations
    - Primary caregiver
    - Quick stats
    """
    try:
        # Get patient
        patient = await db.patients.find_one(
            {"id": patient_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get all assignments
        assignments = await db.employee_patient_assignments.find(
            {"patient_id": patient_id, "status": "active"},
            {"_id": 0}
        ).to_list(100)
        
        # Get all authorizations
        authorizations = await db.service_authorizations.find(
            {"patient_id": patient_id, "status": "active"},
            {"_id": 0}
        ).to_list(100)
        
        # Build care team
        care_team = PatientCareTeam(
            patient_id=patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            organization_id=organization_id
        )
        
        # Find primary employee
        primary = next((a for a in assignments if a.get('assignment_type') == 'primary'), None)
        if primary:
            care_team.primary_employee_id = primary['employee_id']
            care_team.primary_employee_name = primary['employee_name']
        
        # Add all employees
        for assignment in assignments:
            care_team.assigned_employees.append({
                "id": assignment['employee_id'],
                "name": assignment['employee_name'],
                "assignment_type": assignment['assignment_type'],
                "services": assignment.get('authorized_service_codes', [])
            })
        
        # Add authorizations
        for auth in authorizations:
            units_remaining = None
            if auth.get('units_authorized'):
                units_remaining = auth['units_authorized'] - auth.get('units_used', 0)
            
            care_team.authorized_services.append({
                "service_code": auth['service_name'],
                "procedure_code": auth['procedure_code'],
                "authorization_number": auth['authorization_number'],
                "units_remaining": units_remaining,
                "end_date": auth['end_date']
            })
        
        care_team.total_employees = len(assignments)
        care_team.total_authorizations = len(authorizations)
        
        return {
            "status": "success",
            "care_team": care_team.model_dump()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get care team error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# VALIDATION
# ========================================

@router.get("/validate-service")
async def validate_service(
    employee_id: str,
    patient_id: str,
    service_code_id: str,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Validate if an employee can provide a service to a patient
    
    Checks:
    1. Is employee assigned to patient?
    2. Is employee qualified for this service?
    3. Is service authorized in employee-patient assignment?
    4. Is there a valid authorization for the patient?
    """
    try:
        # Get assignments
        assignments = await db.employee_patient_assignments.find(
            {"organization_id": organization_id, "status": "active"},
            {"_id": 0}
        ).to_list(1000)
        
        # Get qualifications
        qualifications = await db.employee_service_qualifications.find(
            {"organization_id": organization_id, "status": "active"},
            {"_id": 0}
        ).to_list(1000)
        
        # Validate employee-patient-service
        employee_validation = AuthorizationValidator.can_employee_serve_patient(
            employee_id=employee_id,
            patient_id=patient_id,
            service_code_id=service_code_id,
            assignments=[EmployeePatientAssignment(**a) for a in assignments],
            qualifications=[EmployeeServiceQualification(**q) for q in qualifications]
        )
        
        if not employee_validation["valid"]:
            return {
                "valid": False,
                "reason": employee_validation["reason"],
                "employee_validation": employee_validation
            }
        
        # Get patient authorizations
        auth_doc = await db.service_authorizations.find_one(
            {
                "patient_id": patient_id,
                "service_code_id": service_code_id,
                "status": "active",
                "organization_id": organization_id
            },
            {"_id": 0}
        )
        
        if not auth_doc:
            return {
                "valid": False,
                "reason": "No active authorization found for this service",
                "employee_validation": employee_validation
            }
        
        # Validate authorization
        authorization = ServiceAuthorization(**auth_doc)
        auth_validation = AuthorizationValidator.is_authorization_valid(authorization)
        
        if not auth_validation["valid"]:
            return {
                "valid": False,
                "reason": auth_validation["reason"],
                "employee_validation": employee_validation,
                "authorization_validation": auth_validation
            }
        
        return {
            "valid": True,
            "message": "Employee is authorized to provide this service to the patient",
            "employee_validation": employee_validation,
            "authorization_validation": auth_validation,
            "authorization": authorization.model_dump()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
