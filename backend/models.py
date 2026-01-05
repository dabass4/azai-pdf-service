"""
Pydantic Models for AZAI Healthcare Application

This module contains all data models used across the application.
Extracted from server.py to reduce file size and improve maintainability.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


# ==================== EVV MODELS ====================

class BusinessEntityConfig(BaseModel):
    """Business entity configuration for EVV submissions"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    business_entity_id: str  # Max 10 characters
    business_entity_medicaid_id: str  # 7 digits for Ohio
    agency_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EVVCall(BaseModel):
    """EVV Call record - telephony or mobile check-in/check-out"""
    call_external_id: str
    call_datetime: str  # UTC: YYYY-MM-DDTHH:MM:SSZ
    call_assignment: str  # "Call In", "Call Out", "Interim"
    call_type: str  # "Telephony", "Mobile", "Manual", "Other"
    procedure_code: Optional[str] = None
    patient_identifier_on_call: Optional[str] = None
    mobile_login: Optional[str] = None
    call_latitude: Optional[float] = None
    call_longitude: Optional[float] = None
    telephony_pin: Optional[str] = None  # 9 digits
    originating_phone_number: Optional[str] = None  # 10 digits
    timezone: str = "America/New_York"


class EVVException(BaseModel):
    """EVV Exception acknowledgement"""
    exception_id: str  # "15", "28", "39", "40" for Ohio
    exception_acknowledged: bool
    exception_description: Optional[str] = None


class EVVVisitChange(BaseModel):
    """EVV Visit change audit record"""
    sequence_id: str
    change_made_by_email: str
    change_datetime: str  # UTC: YYYY-MM-DDTHH:MM:SSZ
    reason_code: str  # 4 characters
    change_reason_memo: str  # Max 256 chars
    resolution_code: str = "A"


class EVVVisit(BaseModel):
    """Complete EVV Visit record compliant with Ohio Medicaid specifications"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    visit_other_id: str
    staff_other_id: str
    patient_other_id: str
    sequence_id: Optional[str] = None
    patient_medicaid_id: str
    patient_alternate_id: Optional[str] = None
    client_payer_id: Optional[str] = None
    visit_cancelled_indicator: bool = False
    payer: str  # "ODM" or "ODA"
    payer_program: str
    procedure_code: str
    timezone: str = "America/New_York"
    adj_in_datetime: Optional[str] = None
    adj_out_datetime: Optional[str] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    bill_visit: bool = True
    hours_to_bill: Optional[float] = None
    units_to_bill: Optional[int] = None
    member_verified_times: bool = False
    member_verified_service: bool = False
    member_signature_available: bool = False
    member_voice_recording: bool = False
    calls: List[EVVCall] = []
    exceptions: List[EVVException] = []
    visit_changes: List[EVVVisitChange] = []
    visit_memo: Optional[str] = None
    timesheet_id: Optional[str] = None
    claim_id: Optional[str] = None
    evv_status: str = "draft"
    transaction_id: Optional[str] = None
    submission_date: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EVVTransmission(BaseModel):
    """EVV Transmission tracking"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    record_type: str  # "Individual", "Staff", "Visit"
    record_count: int
    business_entity_id: str
    business_entity_medicaid_id: str
    transmission_datetime: str
    status: str  # "pending", "accepted", "rejected", "partial"
    acknowledgement: Optional[str] = None
    rejection_details: Optional[List[Dict]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EVVCredentials(BaseModel):
    """Secure storage for EVV API credentials per organization"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    environment: str = "sandbox"
    sandata_api_key: Optional[str] = None
    sandata_api_secret: Optional[str] = None
    sandata_organization_id: Optional[str] = None
    sandata_enabled: bool = False
    ohio_evv_username: Optional[str] = None
    ohio_evv_password: Optional[str] = None
    ohio_evv_business_entity_id: Optional[str] = None
    ohio_evv_enabled: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== ORGANIZATION & USER MODELS ====================

class Organization(BaseModel):
    """Organization/Company account for multi-tenancy"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    plan: str = "basic"
    subscription_status: str = "trial"
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    admin_email: str
    admin_name: str
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    max_timesheets: int = 100
    max_employees: int = 5
    max_patients: int = 10
    features: List[str] = ["sandata_submission"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trial_ends_at: Optional[datetime] = None
    last_payment_at: Optional[datetime] = None


class User(BaseModel):
    """User account with role-based access"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    firebase_uid: Optional[str] = None
    organization_id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str = "staff"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None


# ==================== SERVICE CODE MODELS ====================

class ServiceCodeConfig(BaseModel):
    """Service code configuration for Sandata/EVV submission"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    service_name: str
    service_code_internal: str
    payer: str
    payer_program: str
    procedure_code: str
    modifier1: Optional[str] = None
    modifier2: Optional[str] = None
    modifier3: Optional[str] = None
    modifier4: Optional[str] = None
    service_description: str
    service_category: str
    billable_unit_type: str = "15_minutes"
    requires_evv: bool = True
    is_active: bool = True
    effective_start_date: str
    effective_end_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== EMPLOYEE MODELS ====================

class EmployeeProfile(BaseModel):
    """Employee profile with all required information including EVV DCW fields"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    ssn: str = "000-00-0000"
    date_of_birth: str = "1900-01-01"
    sex: str = "Unknown"
    is_complete: bool = False
    auto_created_from_timesheet: bool = False
    email: Optional[str] = None
    phone: str = ""
    address_street: str = ""
    address_city: str = ""
    address_state: str = "OH"
    address_zip: str = ""
    employee_id: Optional[str] = None
    categories: List[str] = []
    billing_codes: List[str] = []
    staff_pin: Optional[str] = None
    staff_other_id: Optional[str] = None
    staff_position: Optional[str] = None
    sequence_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeProfileUpdate(BaseModel):
    """Employee profile update with all optional fields"""
    model_config = ConfigDict(extra="ignore")
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    ssn: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    is_complete: Optional[bool] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    employee_id: Optional[str] = None
    categories: Optional[List[str]] = None
    billing_codes: Optional[List[str]] = None
    sequence_id: Optional[str] = None


# ==================== PATIENT MODELS ====================

class PatientPhone(BaseModel):
    """Patient phone number"""
    phone_type: str
    phone_number: str
    is_primary: bool = False


class PatientResponsibleParty(BaseModel):
    """Responsible party information for patient"""
    first_name: str
    last_name: str
    relationship: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None


class OtherInsurance(BaseModel):
    """Other insurance information for a patient (TPL)"""
    insurance_name: str = ""
    subscriber_type: str = "Person"
    relationship_to_patient: str = ""
    group_number: str = ""
    policy_number: str = ""
    policy_type: str = ""


class PatientProfile(BaseModel):
    """Patient profile with all required information including EVV compliance"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    first_name: str
    last_name: str
    sex: str = "Unknown"
    date_of_birth: str = "1900-01-01"
    is_newborn: bool = False
    is_complete: bool = False
    auto_created_from_timesheet: bool = False
    address_street: str = ""
    address_city: str = ""
    address_state: str = "OH"
    address_zip: str = ""
    address_latitude: Optional[float] = None
    address_longitude: Optional[float] = None
    address_type: str = "Home"
    timezone: str = "America/New_York"
    prior_auth_number: str = ""
    icd10_code: str = ""
    icd10_description: Optional[str] = None
    physician_name: str = ""
    physician_npi: str = ""
    medicaid_number: str = ""
    patient_other_id: Optional[str] = None
    pims_id: Optional[str] = None
    phone_numbers: List[PatientPhone] = []
    responsible_party: Optional[PatientResponsibleParty] = None
    has_other_insurance: bool = False
    other_insurance: Optional[OtherInsurance] = None
    has_second_other_insurance: bool = False
    second_other_insurance: Optional[OtherInsurance] = None
    sequence_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatientProfileUpdate(BaseModel):
    """Patient profile update with all optional fields"""
    model_config = ConfigDict(extra="ignore")
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_newborn: Optional[bool] = None
    is_complete: Optional[bool] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    address_latitude: Optional[float] = None
    address_longitude: Optional[float] = None
    address_type: Optional[str] = None
    timezone: Optional[str] = None
    prior_auth_number: Optional[str] = None
    icd10_code: Optional[str] = None
    icd10_description: Optional[str] = None
    physician_name: Optional[str] = None
    physician_npi: Optional[str] = None
    medicaid_number: Optional[str] = None
    patient_other_id: Optional[str] = None
    pims_id: Optional[str] = None
    phone_numbers: Optional[List[PatientPhone]] = None
    responsible_party: Optional[PatientResponsibleParty] = None
    sequence_id: Optional[str] = None
    has_other_insurance: Optional[bool] = None
    other_insurance: Optional[OtherInsurance] = None
    has_second_other_insurance: Optional[bool] = None
    second_other_insurance: Optional[OtherInsurance] = None


# ==================== PAYER & CONTRACT MODELS ====================

class BillableService(BaseModel):
    """Billable service with toggle status"""
    service_code: str
    service_name: str
    description: Optional[str] = None
    is_active: bool = True


class Payer(BaseModel):
    """Payer/Insurance company - permanent entity"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    name: str
    short_name: Optional[str] = None
    payer_type: str
    insurance_type: str
    edi_payer_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PayerContract(BaseModel):
    """Contract with a payer - time-bound agreement"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    payer_id: Optional[str] = None
    contract_number: Optional[str] = None
    contract_name: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    billable_services: List[dict] = []
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InsuranceContract(BaseModel):
    """DEPRECATED: Use Payer + PayerContract instead"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    payer_name: str
    insurance_type: str
    contract_number: Optional[str] = None
    payer_id: Optional[str] = None
    payer_address: Optional[str] = None
    payer_city: Optional[str] = None
    payer_state: Optional[str] = None
    payer_zip: Optional[str] = None
    payer_phone: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    billable_services: List[BillableService] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== CLAIM MODELS ====================

class ClaimLineItem(BaseModel):
    """Individual service line item in a claim"""
    date_of_service: str
    employee_name: str
    employee_id: Optional[str] = None
    service_code: str
    service_name: str
    units: int
    rate_per_unit: Optional[float] = None
    amount: Optional[float] = None


class MedicaidClaim(BaseModel):
    """Ohio Medicaid Claim"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    claim_number: str
    patient_id: str
    patient_name: str
    patient_medicaid_number: str
    payer_id: str
    payer_name: str
    contract_number: Optional[str] = None
    service_period_start: str
    service_period_end: str
    line_items: List[ClaimLineItem] = []
    total_units: int = 0
    total_amount: float = 0.0
    status: str = "draft"
    submission_date: Optional[str] = None
    approval_date: Optional[str] = None
    payment_date: Optional[str] = None
    notes: Optional[str] = None
    denial_reason: Optional[str] = None
    timesheet_ids: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== TIMESHEET MODELS ====================

class TimeEntry(BaseModel):
    """Single time entry for a specific date"""
    date: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    hours_worked: Optional[str] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    formatted_hours: Optional[str] = None
    total_minutes: Optional[int] = None
    units: Optional[int] = None
    clock_in_latitude: Optional[float] = None
    clock_in_longitude: Optional[float] = None
    clock_in_accuracy: Optional[float] = None
    clock_in_timestamp: Optional[datetime] = None
    clock_in_geofence_valid: Optional[bool] = None
    clock_in_distance_feet: Optional[float] = None
    clock_out_latitude: Optional[float] = None
    clock_out_longitude: Optional[float] = None
    clock_out_accuracy: Optional[float] = None
    clock_out_timestamp: Optional[datetime] = None
    clock_out_geofence_valid: Optional[bool] = None
    clock_out_distance_feet: Optional[float] = None
    entry_method: Optional[str] = None


class EmployeeEntry(BaseModel):
    """Single employee's complete timesheet data"""
    employee_name: Optional[str] = None
    service_code: Optional[str] = None
    signature: Optional[str] = None
    time_entries: List[TimeEntry] = []


class ExtractedData(BaseModel):
    """Extracted data from timesheet"""
    client_name: Optional[str] = None
    week_of: Optional[str] = None
    employee_entries: List[EmployeeEntry] = []


class Timesheet(BaseModel):
    """Timesheet record"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    filename: str
    file_type: str
    extracted_data: Optional[ExtractedData] = None
    status: str = "processing"
    sandata_status: Optional[str] = None
    error_message: Optional[str] = None
    entry_method: Optional[str] = "scanned"
    patient_id: Optional[str] = None
    registration_results: Optional[Dict] = None
    metadata: Optional[Dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimesheetCreate(BaseModel):
    """Timesheet creation request"""
    filename: str
    file_type: str


# ==================== REQUEST/RESPONSE MODELS ====================

class BulkUpdateRequest(BaseModel):
    """Bulk update request"""
    ids: List[str]
    updates: Dict[str, Any]


class BulkDeleteRequest(BaseModel):
    """Bulk delete request"""
    ids: List[str]


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    organization: Dict[str, Any]
