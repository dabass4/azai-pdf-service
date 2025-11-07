from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import base64
import json
import csv
import io

from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import aiohttp
from pdf2image import convert_from_path
from PIL import Image
from time_utils import calculate_units_from_times, normalize_am_pm

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models

# Business Entity Configuration (EVV Required)
class BusinessEntityConfig(BaseModel):
    """Business entity configuration for EVV submissions"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_entity_id: str  # Max 10 characters
    business_entity_medicaid_id: str  # 7 digits for Ohio
    agency_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# EVV Call Record
class EVVCall(BaseModel):
    """EVV Call record - telephony or mobile check-in/check-out"""
    call_external_id: str  # Unique identifier
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

# EVV Exception Acknowledgement
class EVVException(BaseModel):
    """EVV Exception acknowledgement"""
    exception_id: str  # "15", "28", "39", "40" for Ohio
    exception_acknowledged: bool
    exception_description: Optional[str] = None

# EVV Visit Change Record
class EVVVisitChange(BaseModel):
    """EVV Visit change audit record"""
    sequence_id: str  # Unique sequence for this change
    change_made_by_email: str
    change_datetime: str  # UTC: YYYY-MM-DDTHH:MM:SSZ
    reason_code: str  # Change reason code (4 characters)
    change_reason_memo: str  # Description (max 256 chars)
    resolution_code: str = "A"  # Only "A" for ODM (Approved)

# Service Code Configuration Model
class ServiceCodeConfig(BaseModel):
    """Service code configuration for Sandata/EVV submission"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Multi-tenant isolation
    
    # Service identification
    service_name: str  # Display name: "Home Health Aide - State Plan"
    service_code_internal: str  # Internal code/abbreviation
    
    # Sandata/EVV required fields (3-part combination)
    payer: str  # "ODM" or "ODA"
    payer_program: str  # "SP", "OHCW", "MYCARE", "PASSPORT"
    procedure_code: str  # HCPCS code: "G0156", "T1019", etc.
    
    # Optional modifiers
    modifier1: Optional[str] = None
    modifier2: Optional[str] = None
    modifier3: Optional[str] = None
    modifier4: Optional[str] = None
    
    # Service details
    service_description: str
    service_category: str  # "Personal Care", "Nursing", "Therapy", etc.
    
    # Billing information
    billable_unit_type: str = "15_minutes"  # 1 unit = 15 minutes
    requires_evv: bool = True
    
    # Status and dates
    is_active: bool = True
    effective_start_date: str  # YYYY-MM-DD
    effective_end_date: Optional[str] = None  # YYYY-MM-DD
    
    # Metadata
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Multi-Tenant Organization Model
class Organization(BaseModel):
    """Organization/Company account for multi-tenancy"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Company/Organization name
    plan: str = "basic"  # "basic", "professional", "enterprise"
    subscription_status: str = "trial"  # "trial", "active", "suspended", "cancelled"
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Contact Information
    admin_email: str
    admin_name: str
    phone: Optional[str] = None
    
    # Address
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    
    # Plan limits
    max_timesheets: int = 100  # Per month, -1 for unlimited
    max_employees: int = 5
    max_patients: int = 10
    
    # Features enabled
    features: List[str] = ["sandata_submission"]  # ["sandata_submission", "evv_submission", "bulk_operations", "advanced_reporting", "api_access"]
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trial_ends_at: Optional[datetime] = None
    last_payment_at: Optional[datetime] = None

# User Model
class User(BaseModel):
    """User account with role-based access"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    firebase_uid: Optional[str] = None  # Firebase authentication UID
    organization_id: str  # Link to organization
    
    # Profile
    first_name: str
    last_name: str
    phone: Optional[str] = None
    
    # Role and permissions
    role: str = "staff"  # "owner", "admin", "staff"
    is_active: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None

# EVV Credentials Model
class EVVCredentials(BaseModel):
    """Secure storage for EVV API credentials per organization"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Link to organization
    
    # Environment selection
    environment: str = "sandbox"  # "sandbox" or "production"
    
    # Sandata API Credentials
    sandata_api_key: Optional[str] = None
    sandata_api_secret: Optional[str] = None
    sandata_organization_id: Optional[str] = None
    sandata_enabled: bool = False
    
    # Ohio EVV Aggregator Credentials
    ohio_evv_username: Optional[str] = None
    ohio_evv_password: Optional[str] = None
    ohio_evv_business_entity_id: Optional[str] = None
    ohio_evv_enabled: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# EVV Visit Record (Core)
class EVVVisit(BaseModel):
    """
    Complete EVV Visit record compliant with Ohio Medicaid specifications
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # External IDs (Required)
    visit_other_id: str  # External visit ID (max 50 chars)
    staff_other_id: str  # External staff/employee ID (max 64 chars)
    patient_other_id: str  # External patient ID (max 64 chars)
    
    # Sequence Management (EVV Required)
    sequence_id: Optional[str] = None  # Unique sequence ID for this visit record
    
    # Patient Information (EVV Required)
    patient_medicaid_id: str  # 12 digits for Ohio (with leading zeros)
    patient_alternate_id: Optional[str] = None
    client_payer_id: Optional[str] = None  # Required if Payer is ODA (7 digits)
    
    # Visit Status
    visit_cancelled_indicator: bool = False
    
    # Payer/Program/Service (EVV Required)
    payer: str  # "ODM" or "ODA"
    payer_program: str  # Program name from approved list
    procedure_code: str  # Service code from approved list
    
    # Visit Times (EVV Required - UTC)
    timezone: str = "America/New_York"
    adj_in_datetime: Optional[str] = None  # Adjusted check-in: YYYY-MM-DDTHH:MM:SSZ
    adj_out_datetime: Optional[str] = None  # Adjusted check-out: YYYY-MM-DDTHH:MM:SSZ
    
    # Geographic Location (EVV Required if GPS available)
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    
    # Billing Information
    bill_visit: bool = True
    hours_to_bill: Optional[float] = None
    units_to_bill: Optional[int] = None  # 15-minute units
    
    # Verification (EVV Required)
    member_verified_times: bool = False
    member_verified_service: bool = False
    member_signature_available: bool = False
    member_voice_recording: bool = False
    
    # Call Records (EVV Required)
    calls: List[EVVCall] = []
    
    # Exception Acknowledgements (EVV - if applicable)
    exceptions: List[EVVException] = []
    
    # Visit Change History (EVV - if applicable)
    visit_changes: List[EVVVisitChange] = []
    
    # Additional Information
    visit_memo: Optional[str] = None  # Max 1024 characters
    
    # Linked Records
    timesheet_id: Optional[str] = None  # Source timesheet
    claim_id: Optional[str] = None  # Associated claim
    
    # Submission Tracking
    evv_status: str = "draft"  # draft, ready, submitted, accepted, rejected
    transaction_id: Optional[str] = None
    submission_date: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# EVV Transmission Record
class EVVTransmission(BaseModel):
    """EVV Transmission tracking"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str  # Unique transaction ID
    record_type: str  # "Individual", "Staff", "Visit"
    record_count: int
    business_entity_id: str
    business_entity_medicaid_id: str
    transmission_datetime: str  # UTC
    status: str  # "pending", "accepted", "rejected", "partial"
    acknowledgement: Optional[str] = None
    rejection_details: Optional[List[Dict]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Define Models
class EmployeeProfile(BaseModel):
    """Employee profile with all required information including EVV DCW fields"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Multi-tenant isolation
    
    # Basic Information
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    ssn: str = "000-00-0000"  # Default for incomplete, must be updated
    date_of_birth: str = "1900-01-01"  # YYYY-MM-DD format, default for incomplete
    sex: str = "Unknown"  # Male, Female, Other, Unknown
    
    # Registration status
    is_complete: bool = False  # False if auto-created from timesheet
    auto_created_from_timesheet: bool = False  # Flag for auto-creation
    
    # Contact Information
    email: Optional[str] = None  # EVV: Must be unique if provided
    phone: str = ""
    address_street: str = ""
    address_city: str = ""
    address_state: str = "OH"  # Default to Ohio
    address_zip: str = ""
    
    # Employment Information
    employee_id: Optional[str] = None  # Internal employee ID
    hire_date: str = "1900-01-01"  # YYYY-MM-DD format, default for incomplete
    job_title: str = "Direct Care Worker"  # Default title
    department: Optional[str] = None
    hourly_rate: Optional[float] = None
    employment_status: str = "Active"  # Full-time, Part-time, Contract, Active
    
    # EVV DCW Fields
    staff_pin: Optional[str] = None  # EVV: Staff PIN for telephony (9 digits)
    staff_other_id: Optional[str] = None  # EVV: External system ID
    staff_position: Optional[str] = None  # EVV: Position code (3 characters)
    
    # Emergency Contact
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    emergency_contact_relation: str = ""
    
    # Certifications & Licenses
    certifications: Optional[str] = None  # Comma-separated or free text
    license_number: Optional[str] = None
    license_expiration: Optional[str] = None
    
    # Sequence Management (EVV)
    sequence_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatientPhone(BaseModel):
    """Patient phone number"""
    phone_type: str  # Mobile, Home, Work, Emergency
    phone_number: str  # 10 digits
    is_primary: bool = False

class PatientResponsibleParty(BaseModel):
    """Responsible party information for patient"""
    first_name: str
    last_name: str
    relationship: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class PatientProfile(BaseModel):
    """Patient profile with all required information including EVV compliance"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    first_name: str
    last_name: str
    sex: str = "Unknown"  # Male, Female, Other, Unknown
    date_of_birth: str = "1900-01-01"  # YYYY-MM-DD format, default for incomplete
    is_newborn: bool = False  # EVV: Newborn indicator
    
    # Registration status
    is_complete: bool = False  # False if auto-created from timesheet
    auto_created_from_timesheet: bool = False  # Flag for auto-creation
    
    # Address with Geographic Coordinates (EVV Required)
    address_street: str = ""
    address_city: str = ""
    address_state: str = "OH"  # Default to Ohio
    address_zip: str = ""
    address_latitude: Optional[float] = None  # EVV: Required for primary address
    address_longitude: Optional[float] = None  # EVV: Required for primary address
    address_type: str = "Home"  # Home, Service, Billing
    
    # Timezone (EVV Required)
    timezone: str = "America/New_York"  # Default to Eastern for Ohio
    
    # Medical Information
    prior_auth_number: str = ""  # Alphanumeric with special characters
    icd10_code: str = ""
    icd10_description: Optional[str] = None
    physician_name: str = ""
    physician_npi: str = ""  # 10-digit NPI
    medicaid_number: str = ""  # 12 characters max (Ohio: 12 digits with leading zeros)
    
    # EVV: Alternate IDs
    patient_other_id: Optional[str] = None  # External system ID
    pims_id: Optional[str] = None  # For ODA services (7 digits)
    
    # Phone Numbers (EVV: Optional but recommended)
    phone_numbers: List[PatientPhone] = []
    
    # Responsible Party (EVV: Required if patient is minor or has guardian)
    responsible_party: Optional[PatientResponsibleParty] = None
    
    # Sequence Management (EVV)
    sequence_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BillableService(BaseModel):
    """Billable service with toggle status"""
    service_code: str
    service_name: str
    description: Optional[str] = None
    is_active: bool = True

class InsuranceContract(BaseModel):
    """Insurance/Payer contract information"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payer_name: str  # e.g., Ohio Department of Medicaid
    insurance_type: str  # Medicaid, Medicare, Private, etc.
    contract_number: Optional[str] = None
    start_date: str  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD or None for active
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    billable_services: List[BillableService] = []  # Services under this contract
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClaimLineItem(BaseModel):
    """Individual service line item in a claim"""
    date_of_service: str  # YYYY-MM-DD
    employee_name: str
    employee_id: Optional[str] = None
    service_code: str
    service_name: str
    units: int  # Billable units
    rate_per_unit: Optional[float] = None
    amount: Optional[float] = None  # Total amount (units * rate)

class MedicaidClaim(BaseModel):
    """Ohio Medicaid Claim"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Multi-tenant isolation
    claim_number: str  # Auto-generated claim number
    
    # Patient Information
    patient_id: str
    patient_name: str
    patient_medicaid_number: str
    
    # Payer Information
    payer_id: str
    payer_name: str
    contract_number: Optional[str] = None
    
    # Service Information
    service_period_start: str  # YYYY-MM-DD
    service_period_end: str  # YYYY-MM-DD
    line_items: List[ClaimLineItem] = []
    
    # Financial
    total_units: int = 0
    total_amount: float = 0.0
    
    # Status
    status: str = "draft"  # draft, submitted, pending, approved, denied, paid
    submission_date: Optional[str] = None
    approval_date: Optional[str] = None
    payment_date: Optional[str] = None
    
    # Additional Information
    notes: Optional[str] = None
    denial_reason: Optional[str] = None
    
    # Linked Records
    timesheet_ids: List[str] = []  # Source timesheets
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimeEntry(BaseModel):
    """Single time entry for a specific date"""
    date: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    hours_worked: Optional[str] = None
    units: Optional[int] = None  # Calculated 15-minute units
    

class EmployeeEntry(BaseModel):
    """Single employee's complete timesheet data"""
    employee_name: Optional[str] = None
    service_code: Optional[str] = None
    signature: Optional[str] = None
    time_entries: List[TimeEntry] = []

class ExtractedData(BaseModel):
    client_name: Optional[str] = None  # Single patient/client
    employee_entries: List[EmployeeEntry] = []  # Multiple employees

class Timesheet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Multi-tenant isolation
    filename: str
    file_type: str
    extracted_data: Optional[ExtractedData] = None
    status: str = "processing"  # processing, completed, failed, submitted
    sandata_status: Optional[str] = None  # pending, submitted, error, blocked
    error_message: Optional[str] = None
    
    # Linked patient
    patient_id: Optional[str] = None  # Link to patient profile
    
    # Auto-registration results
    registration_results: Optional[Dict] = None  # Patient and employee registration info
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimesheetCreate(BaseModel):
    filename: str
    file_type: str

# Initialize LLM Chat
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

async def get_pdf_page_count(file_path: str) -> int:
    """Get the number of pages in a PDF file"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Error getting PDF page count: {e}")
        # Fallback to pdf2image
        try:
            images = convert_from_path(file_path)
            return len(images)
        except:
            return 1

async def check_or_create_patient(client_name: str) -> Dict[str, Any]:
    """
    Check if patient exists by name, create if not found
    Returns patient info with is_complete flag
    """
    if not client_name or client_name.strip() == "":
        return None
    
    # Parse name (assume "FirstName LastName" format)
    name_parts = client_name.strip().split()
    if len(name_parts) < 2:
        # If only one name, use it as last name
        first_name = ""
        last_name = name_parts[0] if name_parts else "Unknown"
    else:
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])
    
    # Search for existing patient (case-insensitive)
    existing_patient = await db.patients.find_one({
        "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
        "last_name": {"$regex": f"^{last_name}$", "$options": "i"}
    }, {"_id": 0})
    
    if existing_patient:
        logger.info(f"Found existing patient: {first_name} {last_name}")
        return {
            "id": existing_patient["id"],
            "first_name": existing_patient["first_name"],
            "last_name": existing_patient["last_name"],
            "is_complete": existing_patient.get("is_complete", True),
            "exists": True
        }
    
    # Create new incomplete patient profile
    logger.info(f"Auto-creating patient: {first_name} {last_name}")
    new_patient = PatientProfile(
        first_name=first_name,
        last_name=last_name,
        is_complete=False,
        auto_created_from_timesheet=True
    )
    
    doc = new_patient.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.patients.insert_one(doc)
    
    return {
        "id": new_patient.id,
        "first_name": first_name,
        "last_name": last_name,
        "is_complete": False,
        "exists": False,
        "message": "Auto-created incomplete profile - please update"
    }

async def check_or_create_employee(employee_name: str) -> Dict[str, Any]:
    """
    Check if employee exists by name, create if not found
    Returns employee info with is_complete flag
    """
    if not employee_name or employee_name.strip() == "":
        return None
    
    # Parse name (assume "FirstName LastName" format)
    name_parts = employee_name.strip().split()
    if len(name_parts) < 2:
        # If only one name, use it as last name
        first_name = ""
        last_name = name_parts[0] if name_parts else "Unknown"
    else:
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])
    
    # Search for existing employee (case-insensitive)
    existing_employee = await db.employees.find_one({
        "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
        "last_name": {"$regex": f"^{last_name}$", "$options": "i"}
    }, {"_id": 0})
    
    if existing_employee:
        logger.info(f"Found existing employee: {first_name} {last_name}")
        return {
            "id": existing_employee["id"],
            "first_name": existing_employee["first_name"],
            "last_name": existing_employee["last_name"],
            "is_complete": existing_employee.get("is_complete", True),
            "exists": True
        }
    
    # Create new incomplete employee profile
    logger.info(f"Auto-creating employee: {first_name} {last_name}")
    new_employee = EmployeeProfile(
        first_name=first_name,
        last_name=last_name,
        is_complete=False,
        auto_created_from_timesheet=True
    )
    
    doc = new_employee.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.employees.insert_one(doc)
    
    return {
        "id": new_employee.id,
        "first_name": first_name,
        "last_name": last_name,
        "is_complete": False,
        "exists": False,
        "message": "Auto-created incomplete profile - please update"
    }

async def extract_timesheet_data(file_path: str, file_type: str, page_number: int = 1) -> ExtractedData:
    """Extract data from timesheet using Gemini Vision API
    
    Args:
        file_path: Path to the file
        file_type: Type of file (pdf, jpg, jpeg, png)
        page_number: Page number to extract (for multi-page PDFs)
    """
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"timesheet-{uuid.uuid4()}",
            system_message="You are an expert at extracting structured data from timesheets. Extract all fields accurately and return valid JSON."
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Convert PDF to image if needed (Gemini works better with images)
        processing_file_path = file_path
        mime_type = "image/jpeg"
        temp_image_created = False
        
        if file_type == 'pdf':
            try:
                logger.info(f"Converting PDF page {page_number} to image: {file_path}")
                # Convert specific PDF page to image
                images = convert_from_path(file_path, first_page=page_number, last_page=page_number, dpi=200)
                if images:
                    # Save as JPEG
                    image_path = file_path.replace('.pdf', f'_page{page_number}.jpg')
                    images[0].save(image_path, 'JPEG', quality=95)
                    processing_file_path = image_path
                    temp_image_created = True
                    logger.info(f"PDF page {page_number} converted to image: {image_path}")
                else:
                    raise Exception("No images returned from PDF conversion")
            except Exception as e:
                logger.error(f"PDF conversion error for page {page_number}: {e}")
                logger.warning(f"Cannot process individual pages - PDF conversion failed")
                # If conversion fails, we can't process individual pages properly
                # Return empty data with error
                return ExtractedData(
                    client_name="Error: PDF conversion failed",
                    employee_entries=[]
                )
        elif file_type in ['jpg', 'jpeg', 'png']:
            mime_type = f"image/{file_type if file_type != 'jpg' else 'jpeg'}"
        
        logger.info(f"Processing file: {processing_file_path}, type: {file_type}, mime: {mime_type}, page: {page_number}")
        
        file_content = FileContentWithMimeType(
            file_path=processing_file_path,
            mime_type=mime_type
        )
        
        extraction_prompt = """Analyze this timesheet document carefully. It may contain ONE patient/client with MULTIPLE employees who worked with that patient.

IMPORTANT: Extract entries in the EXACT ORDER they appear in the document, from top to bottom.

Return ONLY a valid JSON object with this exact structure:

{
  "client_name": "name of the patient or client",
  "employee_entries": [
    {
      "employee_name": "first employee's full name",
      "service_code": "service or billing code for this employee",
      "signature": "Yes if signature is present, No if not",
      "time_entries": [
        {
          "date": "YYYY-MM-DD",
          "time_in": "time format as shown",
          "time_out": "time format as shown",
          "hours_worked": "number of hours"
        }
      ]
    }
  ]
}

CRITICAL INSTRUCTIONS:
- Extract entries in SCAN ORDER (top to bottom as they appear)
- Do NOT group by employee - maintain document order
- Extract ALL employees and ALL their time entries
- Group time entries by employee, but keep employees in order they appear

TIME FORMAT RULES:
- Extract times EXACTLY as shown in the document
- Military time examples: "1800", "0830", "1345" (4 digits)
- 24-hour with colon: "18:00", "08:30", "13:45"
- 12-hour format: "8:30 AM", "5:45 PM", "8:30", "5:45"
- DO NOT convert - extract as-is, system will normalize
- Examples: "1800", "18:00", "6:00 PM", "8:30" all acceptable

ORDERING:
- Maintain the exact order entries appear in the document
- If John's entry appears before Mary's, list John first
- Within each employee, list time entries in document order

Return ONLY the JSON object, no additional text or explanation."""
        
        user_message = UserMessage(
            text=extraction_prompt,
            file_contents=[file_content]
        )
        
        response = await chat.send_message(user_message)
        logger.info(f"LLM Raw Response: {response}")
        
        # Parse JSON from response with better error handling
        try:
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            logger.info(f"Cleaned response text: {response_text}")
            
            # Parse JSON
            extracted_json = json.loads(response_text)
            
            # Validate that it's a dict/object, not a list
            if isinstance(extracted_json, list):
                logger.error(f"LLM returned a list instead of object: {extracted_json}")
                # If it's a list with one item, use that
                if len(extracted_json) > 0 and isinstance(extracted_json[0], dict):
                    extracted_json = extracted_json[0]
                else:
                    return ExtractedData()
            
            # Ensure all required keys exist
            if not isinstance(extracted_json, dict):
                logger.error(f"Invalid JSON structure: {extracted_json}")
                return ExtractedData()
            
            # Parse employee_entries array
            employee_entries = []
            employee_entries_data = extracted_json.get("employee_entries", [])
            
            if isinstance(employee_entries_data, list):
                for emp_entry in employee_entries_data:
                    if isinstance(emp_entry, dict):
                        # Parse time entries for this employee
                        time_entries = []
                        time_entries_data = emp_entry.get("time_entries", [])
                        
                        if isinstance(time_entries_data, list):
                            for entry in time_entries_data:
                                if isinstance(entry, dict):
                                    # Get original times
                                    time_in = entry.get("time_in", "")
                                    time_out = entry.get("time_out", "")
                                    
                                    # Normalize AM/PM using system logic
                                    normalized_time_in = normalize_am_pm(time_in) if time_in else ""
                                    normalized_time_out = normalize_am_pm(time_out) if time_out else ""
                                    
                                    # Calculate units and hours from time difference
                                    units, calculated_hours = calculate_units_from_times(normalized_time_in, normalized_time_out)
                                    
                                    # Use calculated hours if available, otherwise use extracted value
                                    hours_worked = str(calculated_hours) if calculated_hours is not None else entry.get("hours_worked")
                                    
                                    # Create TimeEntry with normalized times and calculated units
                                    time_entry = TimeEntry(
                                        date=entry.get("date"),
                                        time_in=normalized_time_in,
                                        time_out=normalized_time_out,
                                        hours_worked=hours_worked
                                    )
                                    
                                    # Add units as custom attribute (will be used for billing)
                                    if units is not None:
                                        time_entry.units = units
                                    
                                    time_entries.append(time_entry)
                        
                        # Create employee entry
                        employee_entries.append(EmployeeEntry(
                            employee_name=emp_entry.get("employee_name"),
                            service_code=emp_entry.get("service_code"),
                            signature=emp_entry.get("signature"),
                            time_entries=time_entries
                        ))
            
            # Create ExtractedData with validated fields
            return ExtractedData(
                client_name=extracted_json.get("client_name"),
                employee_entries=employee_entries
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Failed to parse: {response_text}")
            return ExtractedData()
        except TypeError as e:
            logger.error(f"Type error when creating ExtractedData: {e}")
            return ExtractedData()
            
    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
        raise

async def submit_to_sandata(timesheet: Timesheet) -> dict:
    """
    Submit timesheet data to Sandata API
    IMPORTANT: Validates that patient and all employees have complete profiles before submission
    """
    try:
        # Check if patient profile is complete
        if timesheet.patient_id:
            patient = await db.patients.find_one({"id": timesheet.patient_id}, {"_id": 0})
            if patient:
                if not patient.get("is_complete", True):
                    return {
                        "status": "blocked",
                        "message": f"Cannot submit: Patient profile incomplete. Please complete the patient profile before submitting to Sandata.",
                        "incomplete_profiles": [{"type": "patient", "name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}"}]
                    }
        
        # Check if all employees have complete profiles
        if timesheet.extracted_data and timesheet.extracted_data.employee_entries:
            incomplete_employees = []
            for emp_entry in timesheet.extracted_data.employee_entries:
                if emp_entry.employee_name:
                    # Find employee by name
                    name_parts = emp_entry.employee_name.strip().split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = " ".join(name_parts[1:])
                        
                        employee = await db.employees.find_one({
                            "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
                            "last_name": {"$regex": f"^{last_name}$", "$options": "i"}
                        }, {"_id": 0})
                        
                        if employee and not employee.get("is_complete", True):
                            incomplete_employees.append({
                                "type": "employee",
                                "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
                            })
            
            if incomplete_employees:
                employee_names = ", ".join([emp["name"] for emp in incomplete_employees])
                return {
                    "status": "blocked",
                    "message": f"Cannot submit: Employee profile(s) incomplete. Please complete profiles for: {employee_names}",
                    "incomplete_profiles": incomplete_employees
                }
        
        # All profiles are complete, proceed with submission
        if not timesheet.extracted_data:
            return {
                "status": "error",
                "message": "No data extracted from timesheet"
            }
        
        # Mock Sandata API submission
        sandata_url = os.environ.get('SANDATA_API_URL', '')
        api_key = os.environ.get('SANDATA_API_KEY', '')
        auth_token = os.environ.get('SANDATA_AUTH_TOKEN', '')
        
        # Mock submission - log the data that would be sent
        # Format employee entries for submission
        employee_submissions = []
        total_time_entries = 0
        
        if timesheet.extracted_data.employee_entries:
            for emp_entry in timesheet.extracted_data.employee_entries:
                # Format time entries for this employee
                time_entries_payload = []
                if emp_entry.time_entries:
                    for entry in emp_entry.time_entries:
                        time_entries_payload.append({
                            "date": entry.date,
                            "time_in": entry.time_in,
                            "time_out": entry.time_out,
                            "hours_worked": entry.hours_worked
                        })
                    total_time_entries += len(time_entries_payload)
                
                employee_submissions.append({
                    "employee_name": emp_entry.employee_name,
                    "service_code": emp_entry.service_code,
                    "signature_verified": emp_entry.signature == "Yes",
                    "time_entries": time_entries_payload
                })
        
        payload = {
            "client_name": timesheet.extracted_data.client_name,
            "employee_submissions": employee_submissions,
            "total_employees": len(employee_submissions),
            "total_time_entries": total_time_entries
        }
        
        logger.info(f"[MOCK] Submitting to Sandata API: {payload}")
        logger.info(f"[MOCK] API URL: {sandata_url}")
        logger.info(f"[MOCK] Using API Key: {api_key[:10]}... (masked)")
        
        # Simulate successful submission
        return {
            "status": "success",
            "sandata_id": f"SND-{uuid.uuid4().hex[:8].upper()}",
            "message": "Timesheet submitted successfully (MOCKED)"
        }
        
    except Exception as e:
        logger.error(f"Sandata submission error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@api_router.get("/")
async def root():
    return {"message": "Timesheet Scanner API"}

@api_router.post("/timesheets/upload")
async def upload_timesheet(file: UploadFile = File(...)):
    """Upload and process a timesheet file (handles multi-page PDFs as batch)"""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'jpg', 'jpeg', 'png']:
            raise HTTPException(status_code=400, detail="Only PDF and image files are supported")
        
        # Save file temporarily
        upload_dir = Path("/tmp/timesheets")
        upload_dir.mkdir(exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}.{file_extension}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File saved: {file_path}")
        
        # Check if PDF has multiple pages (batch processing)
        page_count = 1
        if file_extension == 'pdf':
            page_count = await get_pdf_page_count(str(file_path))
            logger.info(f"PDF has {page_count} page(s)")
        
        created_timesheets = []
        
        # Process each page as a separate timesheet entry
        for page_num in range(1, page_count + 1):
            # Create timesheet record for this page
            page_suffix = f" (Page {page_num}/{page_count})" if page_count > 1 else ""
            timesheet = Timesheet(
                filename=f"{file.filename}{page_suffix}",
                file_type=file_extension,
                status="processing"
            )
            
            # Save to database
            doc = timesheet.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.timesheets.insert_one(doc)
            
            # Extract data for this specific page
            try:
                extracted_data = await extract_timesheet_data(str(file_path), file_extension, page_num)
                timesheet.extracted_data = extracted_data
                timesheet.status = "completed"
                
                # Check and auto-register patient and employees
                registration_results = {
                    "patient": None,
                    "employees": [],
                    "incomplete_profiles": []
                }
                
                if extracted_data and extracted_data.client_name:
                    # Check/create patient
                    patient_info = await check_or_create_patient(extracted_data.client_name)
                    if patient_info:
                        registration_results["patient"] = patient_info
                        if not patient_info.get("is_complete"):
                            registration_results["incomplete_profiles"].append({
                                "type": "patient",
                                "name": f"{patient_info['first_name']} {patient_info['last_name']}",
                                "id": patient_info["id"]
                            })
                        timesheet.patient_id = patient_info["id"]
                    
                    # Check/create employees
                    if extracted_data.employee_entries:
                        for emp_entry in extracted_data.employee_entries:
                            if emp_entry.employee_name:
                                employee_info = await check_or_create_employee(emp_entry.employee_name)
                                if employee_info:
                                    registration_results["employees"].append(employee_info)
                                    if not employee_info.get("is_complete"):
                                        registration_results["incomplete_profiles"].append({
                                            "type": "employee",
                                            "name": f"{employee_info['first_name']} {employee_info['last_name']}",
                                            "id": employee_info["id"]
                                        })
                
                # Store registration results in timesheet
                timesheet.registration_results = registration_results
                
                # Auto-submit to Sandata
                submission_result = await submit_to_sandata(timesheet)
                if submission_result["status"] == "success":
                    timesheet.sandata_status = "submitted"
                elif submission_result["status"] == "blocked":
                    timesheet.sandata_status = "blocked"
                    timesheet.error_message = submission_result.get("message", "Submission blocked due to incomplete profiles")
                else:
                    timesheet.sandata_status = "error"
                    timesheet.error_message = submission_result.get("message", "Unknown error")
                
            except Exception as e:
                logger.error(f"Processing error for page {page_num}: {e}")
                timesheet.status = "failed"
                timesheet.error_message = str(e)
            
            # Update database
            timesheet.updated_at = datetime.now(timezone.utc)
            update_doc = timesheet.model_dump()
            update_doc['created_at'] = update_doc['created_at'].isoformat()
            update_doc['updated_at'] = update_doc['updated_at'].isoformat()
            
            await db.timesheets.update_one(
                {"id": timesheet.id},
                {"$set": update_doc}
            )
            
            created_timesheets.append(timesheet)
            
            # Clean up temp page image if created
            try:
                page_image_path = str(file_path).replace('.pdf', f'_page{page_num}.jpg')
                Path(page_image_path).unlink(missing_ok=True)
            except:
                pass
        
        # Clean up original temp file
        try:
            file_path.unlink()
        except:
            pass
        
        # Return result based on number of pages processed
        if len(created_timesheets) == 1:
            return created_timesheets[0]
        else:
            return {
                "message": f"Batch processing complete: {len(created_timesheets)} timesheets created",
                "total_pages": page_count,
                "timesheets": created_timesheets
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/timesheets", response_model=List[Timesheet])
async def get_timesheets(
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    submission_status: Optional[str] = None,
    limit: int = 1000,
    skip: int = 0
):
    """Get all timesheets with optional search and filters
    
    Args:
        search: Search by client name, patient ID, or employee name
        date_from: Filter timesheets from this date (YYYY-MM-DD)
        date_to: Filter timesheets to this date (YYYY-MM-DD)
        submission_status: Filter by submission status (pending/submitted/failed)
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
    """
    query = {}
    
    # Add search filter
    if search:
        query["$or"] = [
            {"client_name": {"$regex": search, "$options": "i"}},
            {"patient_id": {"$regex": search, "$options": "i"}},
            {"employee_entries.employee_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Add date range filter
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        
        # Search in time_entries for dates
        if date_query:
            query["employee_entries.time_entries.date"] = date_query
    
    # Add submission status filter
    if submission_status:
        query["submission_status"] = submission_status
    
    timesheets = await db.timesheets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convert ISO string timestamps back to datetime objects
    for ts in timesheets:
        if isinstance(ts.get('created_at'), str):
            ts['created_at'] = datetime.fromisoformat(ts['created_at'])
        if isinstance(ts.get('updated_at'), str):
            ts['updated_at'] = datetime.fromisoformat(ts['updated_at'])
    
    return timesheets

@api_router.get("/timesheets/{timesheet_id}", response_model=Timesheet)
async def get_timesheet(timesheet_id: str):
    """Get specific timesheet by ID"""
    timesheet = await db.timesheets.find_one({"id": timesheet_id}, {"_id": 0})
    
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Convert ISO string timestamps
    if isinstance(timesheet.get('created_at'), str):
        timesheet['created_at'] = datetime.fromisoformat(timesheet['created_at'])
    if isinstance(timesheet.get('updated_at'), str):
        timesheet['updated_at'] = datetime.fromisoformat(timesheet['updated_at'])
    
    return timesheet

@api_router.put("/timesheets/{timesheet_id}", response_model=Timesheet)
async def update_timesheet(timesheet_id: str, timesheet_update: Timesheet):
    """Update timesheet data (for manual corrections)"""
    timesheet_update.id = timesheet_id
    timesheet_update.updated_at = datetime.now(timezone.utc)
    
    doc = timesheet_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.timesheets.update_one(
        {"id": timesheet_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    logger.info(f"Timesheet updated manually: {timesheet_id}")
    return timesheet_update

@api_router.delete("/timesheets/{timesheet_id}")
async def delete_timesheet(timesheet_id: str):
    """Delete a timesheet"""
    result = await db.timesheets.delete_one({"id": timesheet_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    return {"message": "Timesheet deleted successfully"}

@api_router.post("/timesheets/{timesheet_id}/resubmit")
async def resubmit_timesheet(timesheet_id: str):
    """Manually resubmit timesheet to Sandata with validation"""
    try:
        # Get the timesheet
        timesheet_doc = await db.timesheets.find_one({"id": timesheet_id}, {"_id": 0})
        
        if not timesheet_doc:
            raise HTTPException(status_code=404, detail="Timesheet not found")
        
        # Convert to Timesheet object
        if isinstance(timesheet_doc.get('created_at'), str):
            timesheet_doc['created_at'] = datetime.fromisoformat(timesheet_doc['created_at'])
        if isinstance(timesheet_doc.get('updated_at'), str):
            timesheet_doc['updated_at'] = datetime.fromisoformat(timesheet_doc['updated_at'])
        
        timesheet = Timesheet(**timesheet_doc)
        
        # Attempt resubmission with validation
        submission_result = await submit_to_sandata(timesheet)
        
        # Update timesheet based on result
        if submission_result["status"] == "success":
            timesheet.sandata_status = "submitted"
            timesheet.error_message = None
        elif submission_result["status"] == "blocked":
            timesheet.sandata_status = "blocked"
            timesheet.error_message = submission_result.get("message", "Submission blocked due to incomplete profiles")
        else:
            timesheet.sandata_status = "error"
            timesheet.error_message = submission_result.get("message", "Unknown error")
        
        timesheet.updated_at = datetime.now(timezone.utc)
        
        # Update database
        update_doc = timesheet.model_dump()
        update_doc['created_at'] = update_doc['created_at'].isoformat()
        update_doc['updated_at'] = update_doc['updated_at'].isoformat()
        
        await db.timesheets.update_one(
            {"id": timesheet_id},
            {"$set": update_doc}
        )
        
        logger.info(f"Timesheet resubmitted: {timesheet_id}, result: {submission_result['status']}")
        
        return {
            "status": submission_result["status"],
            "message": submission_result.get("message", ""),
            "timesheet": timesheet
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resubmission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bulk Operations Endpoints

class BulkUpdateRequest(BaseModel):
    """Request model for bulk updates"""
    ids: List[str]
    updates: Dict[str, Any]

class BulkDeleteRequest(BaseModel):
    """Request model for bulk deletes"""
    ids: List[str]

@api_router.post("/timesheets/export")
async def export_timesheets(
    format: str = "csv",
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    submission_status: Optional[str] = None
):
    """Export timesheets to CSV/Excel format with all Sandata-required fields
    
    Args:
        format: Export format ('csv' or 'excel')
        search: Search filter
        date_from: Start date filter
        date_to: End date filter
        submission_status: Submission status filter
    """
    # Build query using same logic as get_timesheets
    query = {}
    
    if search:
        query["$or"] = [
            {"client_name": {"$regex": search, "$options": "i"}},
            {"patient_id": {"$regex": search, "$options": "i"}},
            {"employee_entries.employee_name": {"$regex": search, "$options": "i"}}
        ]
    
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        if date_query:
            query["employee_entries.time_entries.date"] = date_query
    
    if submission_status:
        query["submission_status"] = submission_status
    
    # Fetch timesheets
    timesheets = await db.timesheets.find(query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Prepare CSV data with all Sandata-required fields
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Headers - All Sandata required fields
    headers = [
        "Timesheet ID", "Patient Name", "Patient ID", "Medicaid Number",
        "Employee Name", "Employee ID", "Service Code", "Date",
        "Time In", "Time Out", "Hours Worked", "Units", "Signature",
        "Submission Status", "Created At", "Submitted At"
    ]
    writer.writerow(headers)
    
    # Write data rows
    for ts in timesheets:
        for emp_entry in ts.get("employee_entries", []):
            for time_entry in emp_entry.get("time_entries", []):
                row = [
                    ts.get("id", ""),
                    ts.get("client_name", ""),
                    ts.get("patient_id", ""),
                    ts.get("medicaid_number", ""),
                    emp_entry.get("employee_name", ""),
                    emp_entry.get("employee_id", ""),
                    emp_entry.get("service_code", ""),
                    time_entry.get("date", ""),
                    time_entry.get("time_in", ""),
                    time_entry.get("time_out", ""),
                    time_entry.get("hours_worked", ""),
                    time_entry.get("units", ""),
                    emp_entry.get("signature", ""),
                    ts.get("submission_status", "pending"),
                    ts.get("created_at", ""),
                    ts.get("submitted_at", "")
                ]
                writer.writerow(row)
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=timesheets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@api_router.post("/patients/bulk-update")
async def bulk_update_patients(request: BulkUpdateRequest):
    """Bulk update multiple patient profiles
    
    Common use case: Mark multiple profiles as complete
    """
    try:
        # Validate IDs exist
        count = await db.patients.count_documents({"id": {"$in": request.ids}})
        
        if count == 0:
            raise HTTPException(status_code=404, detail="No patients found with provided IDs")
        
        # Add updated_at timestamp
        updates = request.updates.copy()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Perform bulk update
        result = await db.patients.update_many(
            {"id": {"$in": request.ids}},
            {"$set": updates}
        )
        
        logger.info(f"Bulk updated {result.modified_count} patients")
        
        return {
            "status": "success",
            "modified_count": result.modified_count,
            "matched_count": result.matched_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/employees/bulk-update")
async def bulk_update_employees(request: BulkUpdateRequest):
    """Bulk update multiple employee profiles
    
    Common use case: Mark multiple profiles as complete
    """
    try:
        # Validate IDs exist
        count = await db.employees.count_documents({"id": {"$in": request.ids}})
        
        if count == 0:
            raise HTTPException(status_code=404, detail="No employees found with provided IDs")
        
        # Add updated_at timestamp
        updates = request.updates.copy()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Perform bulk update
        result = await db.employees.update_many(
            {"id": {"$in": request.ids}},
            {"$set": updates}
        )
        
        logger.info(f"Bulk updated {result.modified_count} employees")
        
        return {
            "status": "success",
            "modified_count": result.modified_count,
            "matched_count": result.matched_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/patients/bulk-delete")
async def bulk_delete_patients(request: BulkDeleteRequest):
    """Bulk delete multiple patient profiles"""
    try:
        result = await db.patients.delete_many({"id": {"$in": request.ids}})
        
        logger.info(f"Bulk deleted {result.deleted_count} patients")
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/employees/bulk-delete")
async def bulk_delete_employees(request: BulkDeleteRequest):
    """Bulk delete multiple employee profiles"""
    try:
        result = await db.employees.delete_many({"id": {"$in": request.ids}})
        
        logger.info(f"Bulk deleted {result.deleted_count} employees")
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/timesheets/bulk-delete")
async def bulk_delete_timesheets(request: BulkDeleteRequest):
    """Bulk delete multiple timesheets"""
    try:
        result = await db.timesheets.delete_many({"id": {"$in": request.ids}})
        
        logger.info(f"Bulk deleted {result.deleted_count} timesheets")
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/timesheets/bulk-submit-sandata")
async def bulk_submit_sandata(request: BulkDeleteRequest):
    """Bulk submit multiple timesheets to Sandata"""
    try:
        results = {
            "success": [],
            "failed": []
        }
        
        for timesheet_id in request.ids:
            try:
                # Get the timesheet
                timesheet_doc = await db.timesheets.find_one({"id": timesheet_id}, {"_id": 0})
                
                if not timesheet_doc:
                    results["failed"].append({
                        "id": timesheet_id,
                        "error": "Timesheet not found"
                    })
                    continue
                
                # Convert to Timesheet object
                if isinstance(timesheet_doc.get('created_at'), str):
                    timesheet_doc['created_at'] = datetime.fromisoformat(timesheet_doc['created_at'])
                if isinstance(timesheet_doc.get('updated_at'), str):
                    timesheet_doc['updated_at'] = datetime.fromisoformat(timesheet_doc['updated_at'])
                
                timesheet = Timesheet(**timesheet_doc)
                
                # Submit to Sandata
                submission_result = await submit_to_sandata(timesheet)
                
                # Update timesheet status
                if submission_result["status"] == "success":
                    await db.timesheets.update_one(
                        {"id": timesheet_id},
                        {"$set": {
                            "sandata_status": "submitted",
                            "submitted_at": datetime.now(timezone.utc).isoformat(),
                            "error_message": None
                        }}
                    )
                    results["success"].append(timesheet_id)
                else:
                    await db.timesheets.update_one(
                        {"id": timesheet_id},
                        {"$set": {
                            "sandata_status": "blocked" if "incomplete" in submission_result.get("message", "").lower() else "pending",
                            "error_message": submission_result.get("message", "Submission failed")
                        }}
                    )
                    results["failed"].append({
                        "id": timesheet_id,
                        "error": submission_result.get("message", "Submission failed")
                    })
                    
            except Exception as e:
                logger.error(f"Error submitting timesheet {timesheet_id}: {e}")
                results["failed"].append({
                    "id": timesheet_id,
                    "error": str(e)
                })
        
        logger.info(f"Bulk Sandata submission: {len(results['success'])} succeeded, {len(results['failed'])} failed")
        
        return {
            "status": "completed",
            "success_count": len(results["success"]),
            "failed_count": len(results["failed"]),
            "results": results
        }
    except Exception as e:
        logger.error(f"Bulk Sandata submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Patient Profile Endpoints
@api_router.post("/patients", response_model=PatientProfile)
async def create_patient(patient: PatientProfile):
    """Create a new patient profile"""
    try:
        doc = patient.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.patients.insert_one(doc)
        logger.info(f"Patient created: {patient.id}")
        
        return patient
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/patients", response_model=List[PatientProfile])
async def get_patients(
    search: Optional[str] = None,
    is_complete: Optional[bool] = None,
    limit: int = 1000,
    skip: int = 0
):
    """Get all patient profiles with optional search and filters
    
    Args:
        search: Search by first name, last name, or medicaid number
        is_complete: Filter by completion status (True/False)
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
    """
    query = {}
    
    # Add search filter
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"medicaid_number": {"$regex": search, "$options": "i"}}
        ]
    
    # Add completion status filter
    if is_complete is not None:
        query["is_complete"] = is_complete
    
    patients = await db.patients.find(query, {"_id": 0}).sort("last_name", 1).skip(skip).limit(limit).to_list(limit)
    
    # Convert ISO string timestamps
    for patient in patients:
        if isinstance(patient.get('created_at'), str):
            patient['created_at'] = datetime.fromisoformat(patient['created_at'])
        if isinstance(patient.get('updated_at'), str):
            patient['updated_at'] = datetime.fromisoformat(patient['updated_at'])
    
    return patients

@api_router.get("/patients/{patient_id}", response_model=PatientProfile)
async def get_patient(patient_id: str):
    """Get specific patient by ID"""
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Convert ISO string timestamps
    if isinstance(patient.get('created_at'), str):
        patient['created_at'] = datetime.fromisoformat(patient['created_at'])
    if isinstance(patient.get('updated_at'), str):
        patient['updated_at'] = datetime.fromisoformat(patient['updated_at'])
    
    return patient

@api_router.put("/patients/{patient_id}", response_model=PatientProfile)
async def update_patient(patient_id: str, patient_update: PatientProfile):
    """Update patient profile"""
    patient_update.id = patient_id
    patient_update.updated_at = datetime.now(timezone.utc)
    
    doc = patient_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.patients.update_one(
        {"id": patient_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient_update

@api_router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient profile"""
    result = await db.patients.delete_one({"id": patient_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {"message": "Patient deleted successfully"}

# Employee Profile Endpoints
@api_router.post("/employees", response_model=EmployeeProfile)
async def create_employee(employee: EmployeeProfile):
    """Create a new employee profile"""
    try:
        doc = employee.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.employees.insert_one(doc)
        logger.info(f"Employee created: {employee.id}")
        
        return employee
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/employees", response_model=List[EmployeeProfile])
async def get_employees(
    search: Optional[str] = None,
    is_complete: Optional[bool] = None,
    limit: int = 1000,
    skip: int = 0
):
    """Get all employee profiles with optional search and filters
    
    Args:
        search: Search by first name, last name, or employee ID
        is_complete: Filter by completion status (True/False)
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
    """
    query = {}
    
    # Add search filter
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}}
        ]
    
    # Add completion status filter
    if is_complete is not None:
        query["is_complete"] = is_complete
    
    employees = await db.employees.find(query, {"_id": 0}).sort("last_name", 1).skip(skip).limit(limit).to_list(limit)
    
    # Convert ISO string timestamps
    for employee in employees:
        if isinstance(employee.get('created_at'), str):
            employee['created_at'] = datetime.fromisoformat(employee['created_at'])
        if isinstance(employee.get('updated_at'), str):
            employee['updated_at'] = datetime.fromisoformat(employee['updated_at'])
    
    return employees

@api_router.get("/employees/{employee_id}", response_model=EmployeeProfile)
async def get_employee(employee_id: str):
    """Get specific employee by ID"""
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Convert ISO string timestamps
    if isinstance(employee.get('created_at'), str):
        employee['created_at'] = datetime.fromisoformat(employee['created_at'])
    if isinstance(employee.get('updated_at'), str):
        employee['updated_at'] = datetime.fromisoformat(employee['updated_at'])
    
    return employee

@api_router.put("/employees/{employee_id}", response_model=EmployeeProfile)
async def update_employee(employee_id: str, employee_update: EmployeeProfile):
    """Update employee profile"""
    employee_update.id = employee_id
    employee_update.updated_at = datetime.now(timezone.utc)
    
    doc = employee_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.employees.update_one(
        {"id": employee_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee_update

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """Delete an employee profile"""
    result = await db.employees.delete_one({"id": employee_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {"message": "Employee deleted successfully"}

# Get incomplete profiles endpoint
@api_router.get("/profiles/incomplete")
async def get_incomplete_profiles():
    """Get all incomplete patient and employee profiles"""
    incomplete_patients = await db.patients.find(
        {"is_complete": False},
        {"_id": 0}
    ).to_list(1000)
    
    incomplete_employees = await db.employees.find(
        {"is_complete": False},
        {"_id": 0}
    ).to_list(1000)
    
    return {
        "patients": incomplete_patients,
        "employees": incomplete_employees,
        "total_incomplete": len(incomplete_patients) + len(incomplete_employees)
    }

# Insurance Contract / Payer Endpoints
@api_router.post("/insurance-contracts", response_model=InsuranceContract)
async def create_contract(contract: InsuranceContract):
    """Create a new insurance contract"""
    try:
        doc = contract.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.insurance_contracts.insert_one(doc)
        logger.info(f"Insurance contract created: {contract.id}")
        
        return contract
    except Exception as e:
        logger.error(f"Error creating contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/insurance-contracts", response_model=List[InsuranceContract])
async def get_contracts():
    """Get all insurance contracts"""
    contracts = await db.insurance_contracts.find({}, {"_id": 0}).sort("payer_name", 1).to_list(1000)
    
    # Convert ISO string timestamps
    for contract in contracts:
        if isinstance(contract.get('created_at'), str):
            contract['created_at'] = datetime.fromisoformat(contract['created_at'])
        if isinstance(contract.get('updated_at'), str):
            contract['updated_at'] = datetime.fromisoformat(contract['updated_at'])
    
    return contracts

@api_router.get("/insurance-contracts/{contract_id}", response_model=InsuranceContract)
async def get_contract(contract_id: str):
    """Get specific contract by ID"""
    contract = await db.insurance_contracts.find_one({"id": contract_id}, {"_id": 0})
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Convert ISO string timestamps
    if isinstance(contract.get('created_at'), str):
        contract['created_at'] = datetime.fromisoformat(contract['created_at'])
    if isinstance(contract.get('updated_at'), str):
        contract['updated_at'] = datetime.fromisoformat(contract['updated_at'])
    
    return contract

@api_router.put("/insurance-contracts/{contract_id}", response_model=InsuranceContract)
async def update_contract(contract_id: str, contract_update: InsuranceContract):
    """Update insurance contract"""
    contract_update.id = contract_id
    contract_update.updated_at = datetime.now(timezone.utc)
    
    doc = contract_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.insurance_contracts.update_one(
        {"id": contract_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return contract_update

@api_router.delete("/insurance-contracts/{contract_id}")
async def delete_contract(contract_id: str):
    """Delete an insurance contract"""
    result = await db.insurance_contracts.delete_one({"id": contract_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {"message": "Contract deleted successfully"}

# Medicaid Claims Endpoints
@api_router.post("/claims", response_model=MedicaidClaim)
async def create_claim(claim: MedicaidClaim):
    """Create a new Medicaid claim"""
    try:
        # Auto-generate claim number if not provided
        if not claim.claim_number:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            claim.claim_number = f"ODM-{timestamp}"
        
        doc = claim.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.claims.insert_one(doc)
        logger.info(f"Claim created: {claim.id}")
        
        return claim
    except Exception as e:
        logger.error(f"Error creating claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/claims", response_model=List[MedicaidClaim])
async def get_claims():
    """Get all claims"""
    claims = await db.claims.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Convert ISO string timestamps
    for claim in claims:
        if isinstance(claim.get('created_at'), str):
            claim['created_at'] = datetime.fromisoformat(claim['created_at'])
        if isinstance(claim.get('updated_at'), str):
            claim['updated_at'] = datetime.fromisoformat(claim['updated_at'])
    
    return claims

@api_router.get("/claims/{claim_id}", response_model=MedicaidClaim)
async def get_claim(claim_id: str):
    """Get specific claim by ID"""
    claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Convert ISO string timestamps
    if isinstance(claim.get('created_at'), str):
        claim['created_at'] = datetime.fromisoformat(claim['created_at'])
    if isinstance(claim.get('updated_at'), str):
        claim['updated_at'] = datetime.fromisoformat(claim['updated_at'])
    
    return claim

@api_router.put("/claims/{claim_id}", response_model=MedicaidClaim)
async def update_claim(claim_id: str, claim_update: MedicaidClaim):
    """Update claim"""
    claim_update.id = claim_id
    claim_update.updated_at = datetime.now(timezone.utc)
    
    doc = claim_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.claims.update_one(
        {"id": claim_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return claim_update

@api_router.post("/claims/{claim_id}/submit")
async def submit_claim(claim_id: str):
    """Submit claim to Ohio Medicaid (mocked)"""
    try:
        claim = await db.claims.find_one({"id": claim_id}, {"_id": 0})
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Mock submission
        submission_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        logger.info(f"[MOCK] Submitting claim to Ohio Medicaid:")
        logger.info(f"  Claim Number: {claim['claim_number']}")
        logger.info(f"  Patient: {claim['patient_name']} (Medicaid: {claim['patient_medicaid_number']})")
        logger.info(f"  Total Amount: ${claim['total_amount']:.2f}")
        logger.info(f"  Total Units: {claim['total_units']}")
        logger.info(f"  Line Items: {len(claim['line_items'])}")
        
        # Update claim status
        await db.claims.update_one(
            {"id": claim_id},
            {"$set": {
                "status": "submitted",
                "submission_date": submission_date,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "status": "success",
            "message": "Claim submitted successfully (MOCKED)",
            "claim_number": claim['claim_number'],
            "submission_date": submission_date,
            "reference_id": f"REF-{claim_id[:8].upper()}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Claim submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/claims/{claim_id}")
async def delete_claim(claim_id: str):
    """Delete a claim"""
    result = await db.claims.delete_one({"id": claim_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {"message": "Claim deleted successfully"}

# ========================================
# EVV (Electronic Visit Verification) Endpoints
# ========================================

from evv_utils import (
    SequenceManager, PayerProgramValidator, CoordinateValidator,
    OHIO_PAYERS, OHIO_PAYER_PROGRAMS, OHIO_PROCEDURE_CODES, OHIO_EXCEPTION_CODES
)
from evv_export import EVVExportOrchestrator
from evv_submission import EVVSubmissionService

# Business Entity Configuration Endpoints
@api_router.post("/evv/business-entity", response_model=BusinessEntityConfig)
async def create_business_entity(entity: BusinessEntityConfig):
    """Create business entity configuration for EVV"""
    try:
        doc = entity.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.business_entities.insert_one(doc)
        logger.info(f"Business entity created: {entity.id}")
        
        return entity
    except Exception as e:
        logger.error(f"Error creating business entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv/business-entity", response_model=List[BusinessEntityConfig])
async def get_business_entities():
    """Get all business entity configurations"""
    entities = await db.business_entities.find({}, {"_id": 0}).to_list(100)
    
    for entity in entities:
        if isinstance(entity.get('created_at'), str):
            entity['created_at'] = datetime.fromisoformat(entity['created_at'])
        if isinstance(entity.get('updated_at'), str):
            entity['updated_at'] = datetime.fromisoformat(entity['updated_at'])
    
    return entities

@api_router.get("/evv/business-entity/active", response_model=BusinessEntityConfig)
async def get_active_business_entity():
    """Get active business entity for EVV submissions"""
    entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
    
    if not entity:
        raise HTTPException(status_code=404, detail="No active business entity found")
    
    if isinstance(entity.get('created_at'), str):
        entity['created_at'] = datetime.fromisoformat(entity['created_at'])
    if isinstance(entity.get('updated_at'), str):
        entity['updated_at'] = datetime.fromisoformat(entity['updated_at'])
    
    return entity

# EVV Visit Endpoints
@api_router.post("/evv/visits", response_model=EVVVisit)
async def create_evv_visit(visit: EVVVisit):
    """Create a new EVV visit record"""
    try:
        # Generate sequence ID if not provided
        if not visit.sequence_id:
            visit.sequence_id = SequenceManager.generate_sequence_id()
        
        # Validate payer/program/procedure combination
        validation = PayerProgramValidator.validate_combination(
            visit.payer, visit.payer_program, visit.procedure_code
        )
        
        if not validation["all_valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid payer/program/procedure combination: {validation}"
            )
        
        # Validate coordinates if provided
        if visit.start_latitude and visit.start_longitude:
            if not CoordinateValidator.validate_coordinates(visit.start_latitude, visit.start_longitude):
                raise HTTPException(status_code=400, detail="Invalid start coordinates")
        
        if visit.end_latitude and visit.end_longitude:
            if not CoordinateValidator.validate_coordinates(visit.end_latitude, visit.end_longitude):
                raise HTTPException(status_code=400, detail="Invalid end coordinates")
        
        doc = visit.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.evv_visits.insert_one(doc)
        logger.info(f"EVV visit created: {visit.id}")
        
        return visit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating EVV visit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv/visits", response_model=List[EVVVisit])
async def get_evv_visits():
    """Get all EVV visit records"""
    visits = await db.evv_visits.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for visit in visits:
        if isinstance(visit.get('created_at'), str):
            visit['created_at'] = datetime.fromisoformat(visit['created_at'])
        if isinstance(visit.get('updated_at'), str):
            visit['updated_at'] = datetime.fromisoformat(visit['updated_at'])
    
    return visits

@api_router.get("/evv/visits/{visit_id}", response_model=EVVVisit)
async def get_evv_visit(visit_id: str):
    """Get specific EVV visit by ID"""
    visit = await db.evv_visits.find_one({"id": visit_id}, {"_id": 0})
    
    if not visit:
        raise HTTPException(status_code=404, detail="EVV visit not found")
    
    if isinstance(visit.get('created_at'), str):
        visit['created_at'] = datetime.fromisoformat(visit['created_at'])
    if isinstance(visit.get('updated_at'), str):
        visit['updated_at'] = datetime.fromisoformat(visit['updated_at'])
    
    return visit

@api_router.put("/evv/visits/{visit_id}", response_model=EVVVisit)
async def update_evv_visit(visit_id: str, visit_update: EVVVisit):
    """Update EVV visit record"""
    # Increment sequence ID for update
    if visit_update.sequence_id:
        visit_update.sequence_id = SequenceManager.generate_sequence_id()
    
    visit_update.id = visit_id
    visit_update.updated_at = datetime.now(timezone.utc)
    
    doc = visit_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.evv_visits.update_one(
        {"id": visit_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="EVV visit not found")
    
    return visit_update

@api_router.delete("/evv/visits/{visit_id}")
async def delete_evv_visit(visit_id: str):
    """Delete an EVV visit"""
    result = await db.evv_visits.delete_one({"id": visit_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="EVV visit not found")
    
    return {"message": "EVV visit deleted successfully"}

# EVV Export Endpoints
@api_router.get("/evv/export/individuals")
async def export_individuals():
    """Export patients as EVV Individual records"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Get all patients
        patients = await db.patients.find({}, {"_id": 0}).to_list(1000)
        
        # Export to EVV format
        exporter = EVVExportOrchestrator()
        json_export = exporter.export_individuals(
            patients,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        return {
            "status": "success",
            "record_type": "Individual",
            "record_count": len(patients),
            "data": json.loads(json_export)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting individuals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv/export/direct-care-workers")
async def export_direct_care_workers():
    """Export employees as EVV DirectCareWorker records"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Get all employees
        employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
        
        # Export to EVV format
        exporter = EVVExportOrchestrator()
        json_export = exporter.export_direct_care_workers(
            employees,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        return {
            "status": "success",
            "record_type": "DirectCareWorker",
            "record_count": len(employees),
            "data": json.loads(json_export)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting DCWs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv/export/visits")
async def export_visits():
    """Export EVV visit records"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Get all ready/draft visits
        visits = await db.evv_visits.find(
            {"evv_status": {"$in": ["draft", "ready"]}},
            {"_id": 0}
        ).to_list(1000)
        
        # Export to EVV format
        exporter = EVVExportOrchestrator()
        json_export = exporter.export_visits(
            visits,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        return {
            "status": "success",
            "record_type": "Visit",
            "record_count": len(visits),
            "data": json.loads(json_export)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting visits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# EVV Submission Endpoints
@api_router.post("/evv/submit/individuals")
async def submit_individuals():
    """Submit Individual records to Ohio EVV Aggregator"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Get all patients
        patients = await db.patients.find({}, {"_id": 0}).to_list(1000)
        
        # Export to EVV format
        exporter = EVVExportOrchestrator()
        json_export = exporter.export_individuals(
            patients,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        # Submit to aggregator
        submission_service = EVVSubmissionService()
        result = submission_service.submit_individuals(
            json_export,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        # Save transmission record
        if result.get("status") == "success":
            transmission = EVVTransmission(
                transaction_id=result['transaction_id'],
                record_type="Individual",
                record_count=len(patients),
                business_entity_id=entity['business_entity_id'],
                business_entity_medicaid_id=entity['business_entity_medicaid_id'],
                transmission_datetime=datetime.now(timezone.utc).isoformat(),
                status="accepted" if not result.get('has_rejections') else "partial",
                acknowledgement=json.dumps(result.get('acknowledgment', {}))
            )
            
            doc = transmission.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.evv_transmissions.insert_one(doc)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting individuals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/evv/submit/direct-care-workers")
async def submit_direct_care_workers():
    """Submit DirectCareWorker records to Ohio EVV Aggregator"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Get all employees
        employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
        
        # Export to EVV format
        exporter = EVVExportOrchestrator()
        json_export = exporter.export_direct_care_workers(
            employees,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        # Submit to aggregator
        submission_service = EVVSubmissionService()
        result = submission_service.submit_direct_care_workers(
            json_export,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        # Save transmission record
        if result.get("status") == "success":
            transmission = EVVTransmission(
                transaction_id=result['transaction_id'],
                record_type="Staff",
                record_count=len(employees),
                business_entity_id=entity['business_entity_id'],
                business_entity_medicaid_id=entity['business_entity_medicaid_id'],
                transmission_datetime=datetime.now(timezone.utc).isoformat(),
                status="accepted" if not result.get('has_rejections') else "partial",
                acknowledgement=json.dumps(result.get('acknowledgment', {}))
            )
            
            doc = transmission.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.evv_transmissions.insert_one(doc)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting DCWs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/evv/submit/visits")
async def submit_visits():
    """Submit Visit records to Ohio EVV Aggregator"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Get ready visits
        visits = await db.evv_visits.find(
            {"evv_status": {"$in": ["draft", "ready"]}},
            {"_id": 0}
        ).to_list(1000)
        
        if not visits:
            return {
                "status": "success",
                "message": "No visits ready for submission",
                "record_count": 0
            }
        
        # Export to EVV format
        exporter = EVVExportOrchestrator()
        json_export = exporter.export_visits(
            visits,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        # Submit to aggregator
        submission_service = EVVSubmissionService()
        result = submission_service.submit_visits(
            json_export,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        # Save transmission record and update visit statuses
        if result.get("status") == "success":
            transmission = EVVTransmission(
                transaction_id=result['transaction_id'],
                record_type="Visit",
                record_count=len(visits),
                business_entity_id=entity['business_entity_id'],
                business_entity_medicaid_id=entity['business_entity_medicaid_id'],
                transmission_datetime=datetime.now(timezone.utc).isoformat(),
                status="accepted" if not result.get('has_rejections') else "partial",
                acknowledgement=json.dumps(result.get('acknowledgment', {}))
            )
            
            doc = transmission.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.evv_transmissions.insert_one(doc)
            
            # Update visit statuses
            visit_ids = [v['id'] for v in visits]
            await db.evv_visits.update_many(
                {"id": {"$in": visit_ids}},
                {"$set": {
                    "evv_status": "submitted",
                    "transaction_id": result['transaction_id'],
                    "submission_date": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting visits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv/status/{transaction_id}")
async def query_evv_status(transaction_id: str):
    """Query status of EVV submission"""
    try:
        # Get active business entity
        entity = await db.business_entities.find_one({"is_active": True}, {"_id": 0})
        if not entity:
            raise HTTPException(status_code=404, detail="No active business entity configured")
        
        # Query aggregator
        submission_service = EVVSubmissionService()
        result = submission_service.query_status(
            transaction_id,
            entity['business_entity_id'],
            entity['business_entity_medicaid_id']
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying EVV status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv/transmissions", response_model=List[EVVTransmission])
async def get_evv_transmissions():
    """Get all EVV transmission records"""
    transmissions = await db.evv_transmissions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for trans in transmissions:
        if isinstance(trans.get('created_at'), str):
            trans['created_at'] = datetime.fromisoformat(trans['created_at'])
    
    return transmissions

# EVV Reference Data Endpoints
@api_router.get("/evv/reference/payers")
async def get_evv_payers():
    """Get list of valid Ohio EVV payers"""
    return {"payers": OHIO_PAYERS}

@api_router.get("/evv/reference/programs")
async def get_evv_programs():
    """Get list of valid Ohio EVV payer programs"""
    return {"programs": OHIO_PAYER_PROGRAMS}

@api_router.get("/evv/reference/procedure-codes")
async def get_evv_procedure_codes():
    """Get list of valid Ohio EVV procedure codes"""
    return {"procedure_codes": OHIO_PROCEDURE_CODES}

@api_router.get("/evv/reference/exception-codes")
async def get_evv_exception_codes():
    """Get list of valid Ohio EVV exception codes"""
    return {"exception_codes": OHIO_EXCEPTION_CODES}

# ========================================
# Service Code Configuration Endpoints
# ========================================

@api_router.post("/service-codes", response_model=ServiceCodeConfig)
async def create_service_code(service_code: ServiceCodeConfig):
    """Create a new service code configuration"""
    try:
        doc = service_code.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.service_codes.insert_one(doc)
        logger.info(f"Service code created: {service_code.id}")
        
        return service_code
    except Exception as e:
        logger.error(f"Error creating service code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/service-codes", response_model=List[ServiceCodeConfig])
async def get_service_codes(active_only: bool = False):
    """Get all service code configurations"""
    query = {"is_active": True} if active_only else {}
    service_codes = await db.service_codes.find(query, {"_id": 0}).to_list(1000)
    
    for sc in service_codes:
        if isinstance(sc.get('created_at'), str):
            sc['created_at'] = datetime.fromisoformat(sc['created_at'])
        if isinstance(sc.get('updated_at'), str):
            sc['updated_at'] = datetime.fromisoformat(sc['updated_at'])
    
    return service_codes

@api_router.get("/service-codes/{service_code_id}", response_model=ServiceCodeConfig)
async def get_service_code(service_code_id: str):
    """Get specific service code by ID"""
    service_code = await db.service_codes.find_one({"id": service_code_id}, {"_id": 0})
    
    if not service_code:
        raise HTTPException(status_code=404, detail="Service code not found")
    
    if isinstance(service_code.get('created_at'), str):
        service_code['created_at'] = datetime.fromisoformat(service_code['created_at'])
    if isinstance(service_code.get('updated_at'), str):
        service_code['updated_at'] = datetime.fromisoformat(service_code['updated_at'])
    
    return service_code

@api_router.put("/service-codes/{service_code_id}", response_model=ServiceCodeConfig)
async def update_service_code(service_code_id: str, service_code_update: ServiceCodeConfig):
    """Update a service code configuration"""
    service_code_update.id = service_code_id
    service_code_update.updated_at = datetime.now(timezone.utc)
    
    doc = service_code_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.service_codes.update_one(
        {"id": service_code_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service code not found")
    
    return service_code_update

@api_router.delete("/service-codes/{service_code_id}")
async def delete_service_code(service_code_id: str):
    """Delete a service code configuration"""
    result = await db.service_codes.delete_one({"id": service_code_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service code not found")
    
    return {"message": "Service code deleted successfully"}

@api_router.post("/service-codes/validate")
async def validate_service_code_combination(
    payer: str,
    payer_program: str,
    procedure_code: str
):
    """Validate that payer/program/procedure code combination is valid"""
    service_code = await db.service_codes.find_one({
        "payer": payer,
        "payer_program": payer_program,
        "procedure_code": procedure_code,
        "is_active": True
    }, {"_id": 0})
    
    if not service_code:
        return {
            "valid": False,
            "error": f"Invalid combination: {payer}/{payer_program}/{procedure_code}",
            "message": "This service code combination is not configured or is inactive"
        }
    
    return {
        "valid": True,
        "service_name": service_code.get("service_name"),
        "service_code_id": service_code.get("id"),
        "service_description": service_code.get("service_description")
    }

@api_router.get("/service-codes/by-payer/{payer}")
async def get_service_codes_by_payer(payer: str):
    """Get all active service codes for a specific payer"""
    service_codes = await db.service_codes.find({
        "payer": payer,
        "is_active": True
    }, {"_id": 0}).to_list(1000)
    
    return {"payer": payer, "service_codes": service_codes}

@api_router.post("/service-codes/initialize-ohio")
async def initialize_ohio_service_codes():
    """Initialize Ohio Medicaid service codes (for setup)"""
    ohio_codes = [
        # State Plan Home Health
        {
            "service_name": "Home Health Aide - State Plan",
            "service_code_internal": "HHA_SP",
            "payer": "ODM",
            "payer_program": "SP",
            "procedure_code": "G0156",
            "service_description": "Home Health Aide services under State Plan Home Health",
            "service_category": "Personal Care",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "Physical Therapy - State Plan",
            "service_code_internal": "PT_SP",
            "payer": "ODM",
            "payer_program": "SP",
            "procedure_code": "G0151",
            "service_description": "Physical Therapy services under State Plan",
            "service_category": "Therapy",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "Occupational Therapy - State Plan",
            "service_code_internal": "OT_SP",
            "payer": "ODM",
            "payer_program": "SP",
            "procedure_code": "G0152",
            "service_description": "Occupational Therapy services under State Plan",
            "service_category": "Therapy",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "Speech Therapy - State Plan",
            "service_code_internal": "ST_SP",
            "payer": "ODM",
            "payer_program": "SP",
            "procedure_code": "G0153",
            "service_description": "Speech Language Pathology services under State Plan",
            "service_category": "Therapy",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "RN Services - State Plan",
            "service_code_internal": "RN_SP",
            "payer": "ODM",
            "payer_program": "SP",
            "procedure_code": "G0299",
            "service_description": "Registered Nurse services under State Plan",
            "service_category": "Nursing",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "LPN Services - State Plan",
            "service_code_internal": "LPN_SP",
            "payer": "ODM",
            "payer_program": "SP",
            "procedure_code": "G0300",
            "service_description": "Licensed Practical Nurse services under State Plan",
            "service_category": "Nursing",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        # Ohio Home Care Waiver
        {
            "service_name": "Personal Care Aide - OHCW",
            "service_code_internal": "PCA_OHCW",
            "payer": "ODM",
            "payer_program": "OHCW",
            "procedure_code": "T1019",
            "service_description": "Personal Care Aide services under Ohio Home Care Waiver",
            "service_category": "Personal Care",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "RN Waiver Services - OHCW",
            "service_code_internal": "RN_OHCW",
            "payer": "ODM",
            "payer_program": "OHCW",
            "procedure_code": "T1002",
            "service_description": "Registered Nurse waiver services under OHCW",
            "service_category": "Nursing",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "LPN Waiver Services - OHCW",
            "service_code_internal": "LPN_OHCW",
            "payer": "ODM",
            "payer_program": "OHCW",
            "procedure_code": "T1003",
            "service_description": "Licensed Practical Nurse waiver services under OHCW",
            "service_category": "Nursing",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        {
            "service_name": "Home Care Attendant - OHCW",
            "service_code_internal": "HCA_OHCW",
            "payer": "ODM",
            "payer_program": "OHCW",
            "procedure_code": "S5125",
            "service_description": "Home Care Attendant services under OHCW",
            "service_category": "Personal Care",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        # MyCare Waiver
        {
            "service_name": "Personal Care Aide - MyCare",
            "service_code_internal": "PCA_MYCARE",
            "payer": "ODM",
            "payer_program": "MYCARE",
            "procedure_code": "T1019",
            "service_description": "Personal Care Aide services under MyCare Waiver",
            "service_category": "Personal Care",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
        # PASSPORT Waiver
        {
            "service_name": "Personal Care Aide - PASSPORT",
            "service_code_internal": "PCA_PASSPORT",
            "payer": "ODA",
            "payer_program": "PASSPORT",
            "procedure_code": "T1019",
            "service_description": "Personal Care Aide services under PASSPORT Waiver",
            "service_category": "Personal Care",
            "effective_start_date": "2024-01-01",
            "is_active": True
        },
    ]
    
    # Check if already initialized
    existing_count = await db.service_codes.count_documents({})
    if existing_count > 0:
        return {
            "message": "Service codes already initialized",
            "existing_count": existing_count
        }
    
    # Insert all service codes
    for code_data in ohio_codes:
        service_code = ServiceCodeConfig(**code_data)
        doc = service_code.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.service_codes.insert_one(doc)
    
    logger.info(f"Initialized {len(ohio_codes)} Ohio Medicaid service codes")
    
    return {
        "message": f"Successfully initialized {len(ohio_codes)} Ohio Medicaid service codes",
        "codes_added": len(ohio_codes)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()