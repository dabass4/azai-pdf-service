"""
Patient Authorization & Service Assignment Module

Manages the relationships between:
- Patients/Clients
- Employees/Direct Care Workers
- Service Codes
- Authorizations (what services are approved for each patient)
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone, date
import uuid


class ServiceAuthorization(BaseModel):
    """
    Represents an authorization for specific services for a patient
    
    Example: Patient Jane Smith is authorized for 40 hours/month of Personal Care (T1019)
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Patient information
    patient_id: str
    patient_name: Optional[str] = None
    
    # Authorization details
    authorization_number: str  # Prior auth number from payer
    payer: str  # ODM, ODA, Insurance name
    payer_program: Optional[str] = None  # SP, OHCW, MYCARE, PASSPORT
    
    # Service details
    service_code_id: str  # Link to ServiceCodeConfig
    service_name: str
    procedure_code: str  # T1019, G0156, etc.
    
    # Authorization limits
    units_authorized: Optional[int] = None  # Total units approved
    units_per_week: Optional[int] = None
    units_per_month: Optional[int] = None
    hours_authorized: Optional[float] = None  # Alternative to units
    
    # Date range
    start_date: date
    end_date: date
    
    # Billing info
    rate: Optional[float] = None  # Rate per unit or hour
    
    # Status
    status: str = "active"  # active, expired, suspended, cancelled
    
    # Usage tracking
    units_used: int = 0
    hours_used: float = 0.0
    last_service_date: Optional[date] = None
    
    # Notes
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeePatientAssignment(BaseModel):
    """
    Assigns specific employees to work with specific patients
    
    Example: Employee John Doe is assigned to provide care for Patient Jane Smith
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Employee information
    employee_id: str
    employee_name: Optional[str] = None
    
    # Patient information
    patient_id: str
    patient_name: Optional[str] = None
    
    # Assignment details
    assignment_type: str = "primary"  # primary, backup, temporary
    
    # Services this employee can provide to this patient
    authorized_service_codes: List[str] = []  # List of service_code_ids
    
    # Schedule
    start_date: date
    end_date: Optional[date] = None  # None = ongoing
    
    # Restrictions
    max_hours_per_week: Optional[float] = None
    max_hours_per_month: Optional[float] = None
    
    # Status
    status: str = "active"  # active, inactive, suspended
    
    # Notes
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeServiceQualification(BaseModel):
    """
    Tracks which services an employee is qualified/certified to provide
    
    Example: Employee John Doe is certified to provide Personal Care and Respite Care
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Employee information
    employee_id: str
    employee_name: Optional[str] = None
    
    # Service qualification
    service_code_id: str
    service_name: str
    procedure_code: str
    
    # Certification details
    certification_number: Optional[str] = None
    certification_date: Optional[date] = None
    expiration_date: Optional[date] = None
    
    # Training
    training_completed: bool = False
    training_date: Optional[date] = None
    training_hours: Optional[float] = None
    
    # Status
    status: str = "active"  # active, expired, suspended
    
    # Notes
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatientCareTeam(BaseModel):
    """
    Complete care team for a patient including all assigned employees
    This is a summary/view model for easier querying
    """
    patient_id: str
    patient_name: str
    organization_id: str
    
    # Primary caregiver
    primary_employee_id: Optional[str] = None
    primary_employee_name: Optional[str] = None
    
    # All assigned employees
    assigned_employees: List[Dict] = []  # List of {id, name, assignment_type, services}
    
    # Authorized services for this patient
    authorized_services: List[Dict] = []  # List of {service_code, auth_number, units_remaining}
    
    # Quick stats
    total_employees: int = 0
    total_authorizations: int = 0
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceAuthorizationUsage(BaseModel):
    """
    Tracks usage against an authorization
    Updated each time a service is provided
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    authorization_id: str
    
    # Service details
    timesheet_id: str
    service_date: date
    
    # Who provided the service
    employee_id: str
    employee_name: str
    
    # Usage
    units_used: int
    hours_worked: float
    
    # Status
    status: str = "pending"  # pending, approved, billed, denied
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthorizationValidator:
    """
    Helper class to validate service authorizations
    """
    
    @staticmethod
    def is_authorization_valid(authorization: ServiceAuthorization) -> Dict:
        """
        Check if authorization is currently valid
        
        Returns:
            Dict with validation result and reason
        """
        today = date.today()
        
        # Check status
        if authorization.status != "active":
            return {
                "valid": False,
                "reason": f"Authorization status is {authorization.status}"
            }
        
        # Check date range
        if today < authorization.start_date:
            return {
                "valid": False,
                "reason": f"Authorization not yet active (starts {authorization.start_date})"
            }
        
        if today > authorization.end_date:
            return {
                "valid": False,
                "reason": f"Authorization expired on {authorization.end_date}"
            }
        
        # Check units remaining
        if authorization.units_authorized:
            remaining = authorization.units_authorized - authorization.units_used
            if remaining <= 0:
                return {
                    "valid": False,
                    "reason": "No units remaining on authorization"
                }
        
        return {
            "valid": True,
            "reason": "Authorization is valid",
            "units_remaining": authorization.units_authorized - authorization.units_used if authorization.units_authorized else None
        }
    
    @staticmethod
    def can_employee_serve_patient(
        employee_id: str,
        patient_id: str,
        service_code_id: str,
        assignments: List[EmployeePatientAssignment],
        qualifications: List[EmployeeServiceQualification]
    ) -> Dict:
        """
        Check if employee is authorized to provide service to patient
        
        Returns:
            Dict with validation result
        """
        # Check if employee is assigned to patient
        assignment = next(
            (a for a in assignments if a.employee_id == employee_id and a.patient_id == patient_id and a.status == "active"),
            None
        )
        
        if not assignment:
            return {
                "valid": False,
                "reason": f"Employee is not assigned to this patient"
            }
        
        # Check if employee is qualified for this service
        qualification = next(
            (q for q in qualifications if q.employee_id == employee_id and q.service_code_id == service_code_id and q.status == "active"),
            None
        )
        
        if not qualification:
            return {
                "valid": False,
                "reason": f"Employee is not qualified for this service"
            }
        
        # Check if service is in employee's authorized services for this patient
        if service_code_id not in assignment.authorized_service_codes:
            return {
                "valid": False,
                "reason": f"Employee is not authorized to provide this service to this patient"
            }
        
        # Check date range
        today = date.today()
        if today < assignment.start_date:
            return {
                "valid": False,
                "reason": f"Assignment not yet active (starts {assignment.start_date})"
            }
        
        if assignment.end_date and today > assignment.end_date:
            return {
                "valid": False,
                "reason": f"Assignment ended on {assignment.end_date}"
            }
        
        return {
            "valid": True,
            "reason": "Employee is authorized",
            "assignment": assignment.dict(),
            "qualification": qualification.dict()
        }
