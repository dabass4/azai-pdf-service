from pathlib import Path
import os
import asyncio
import subprocess
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import scan configuration - SINGLE SOURCE OF TRUTH
from scan_config import (
    OCR_MODEL_SETTINGS,
    PDF_SETTINGS,
    TIME_SETTINGS,
    DATE_SETTINGS,
    EXTRACTION_SETTINGS,
    UNIT_SETTINGS,
    CONFIDENCE_SETTINGS,
    get_all_settings,
    get_settings_summary
)

# Ensure PDF dependencies are installed on startup
def ensure_pdf_dependencies():
    """Check and install poppler-utils if not present, then display scan config from scan_config.py"""
    try:
        result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  poppler-utils not found. Installing...")
            subprocess.run(['apt-get', 'update', '-qq'], capture_output=True)
            subprocess.run(['apt-get', 'install', '-y', 'poppler-utils'], capture_output=True)
            print("✅ poppler-utils installed")
        else:
            print("✅ poppler-utils ready")
        
        # Display scan configuration summary FROM scan_config.py (single source of truth)
        print("\n" + "="*50)
        print("SCAN CONFIGURATION LOADED (from scan_config.py)")
        print("="*50)
        print(f"🤖 OCR Model: {OCR_MODEL_SETTINGS['model']} ({OCR_MODEL_SETTINGS['provider']})")
        print(f"🕐 Time Format: {TIME_SETTINGS['display_format']} ({TIME_SETTINGS.get('display_example', 'N/A')})")
        print(f"📅 Date Format: {DATE_SETTINGS['output_format']}")
        print(f"🔧 OCR Fixes: decimal→colon={TIME_SETTINGS['ocr_fixes']['decimal_to_colon']}, invalid_minutes={TIME_SETTINGS['ocr_fixes']['fix_invalid_minutes']}")
        print(f"📄 DPI: {PDF_SETTINGS['dpi']} | Quality: {PDF_SETTINGS['jpeg_quality']}")
        print(f"🔢 Unit Calculation: {UNIT_SETTINGS['minutes_per_unit']} min/unit")
        print("="*50 + "\n")
    except Exception as e:
        print(f"⚠️  Could not check/install poppler-utils: {e}")

# Run on module load
ensure_pdf_dependencies()

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Header, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime, timezone, timedelta
import base64
import json
import csv
import io

from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import aiohttp
from pdf2image import convert_from_path
from PIL import Image
from time_utils import calculate_units_from_times, normalize_am_pm, format_time_24h, format_time_12h
from date_utils import normalize_dates_in_extracted_data
from auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_current_user,
    get_organization_from_token
)
from payments import (
    create_checkout_session,
    create_billing_portal_session,
    verify_webhook_signature,
    get_plan_limits,
    get_plan_features,
    PLANS
)
from extraction_service import ConfidenceScorer, ExtractionProgress
from date_utils import (
    parse_week_range, 
    parse_date_with_context, 
    normalize_dates_in_extracted_data,
    cross_compare_and_fill_dates,
    fill_missing_dates_for_timesheet,
    format_date_mm_dd_yyyy
)


# Utility function to convert decimal hours to hours and minutes
def decimal_hours_to_hours_minutes(decimal_hours: float) -> dict:
    """
    Convert decimal hours to hours and minutes in H:MM format
    
    Args:
        decimal_hours: Hours in decimal format (e.g., 0.58, 8.5, 10.25)
    
    Returns:
        dict with 'hours', 'minutes', and 'formatted' string
        
    Examples:
        0.58 -> {'hours': 0, 'minutes': 35, 'formatted': '0:35'}
        8.5 -> {'hours': 8, 'minutes': 30, 'formatted': '8:30'}
        10.25 -> {'hours': 10, 'minutes': 15, 'formatted': '10:15'}
    """
    if decimal_hours is None:
        return {'hours': 0, 'minutes': 0, 'formatted': '0:00', 'total_minutes': 0}
    
    try:
        decimal_hours = float(decimal_hours)
    except (ValueError, TypeError):
        return {'hours': 0, 'minutes': 0, 'formatted': '0:00', 'total_minutes': 0}
    
    hours = int(decimal_hours)
    minutes = round((decimal_hours - hours) * 60)
    
    # Handle rounding edge case (59.5 minutes -> 60 minutes = 1 hour)
    if minutes >= 60:
        hours += 1
        minutes = 0
    
    # Format as H:MM (with leading zero for minutes if needed)
    formatted = f"{hours}:{minutes:02d}"
    
    return {
        'hours': hours,
        'minutes': minutes,
        'formatted': formatted,
        'total_minutes': hours * 60 + minutes
    }

def hours_minutes_to_decimal(hours: int, minutes: int) -> float:
    """
    Convert hours and minutes to decimal hours
    
    Args:
        hours: Number of hours
        minutes: Number of minutes
    
    Returns:
        Decimal hours (e.g., 8 hr 30 min -> 8.5)
    """
    return hours + (minutes / 60)



# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import WebSocket manager and Socket.IO
from websocket_manager import sio, ws_manager
import socketio

# Create ASGI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Multi-Tenant Data Isolation Middleware
async def get_organization_id(
    authorization: Optional[str] = Header(None),
    x_organization_id: Optional[str] = Header(None)
) -> str:
    """
    Extract organization_id from JWT token or fallback to header.
    Priority: JWT token > X-Organization-ID header > default-org
    """
    # Try to get from JWT token first
    if authorization:
        try:
            return await get_organization_from_token(authorization)
        except:
            pass
    
    # Fallback to X-Organization-ID header
    if x_organization_id:
        return x_organization_id
    
    # Fallback to default for backward compatibility
    return "default-org"

# Define Models

# Business Entity Configuration (EVV Required)
class BusinessEntityConfig(BaseModel):
    """Business entity configuration for EVV submissions"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
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
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
    
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
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
    
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
    
    # Employee Categories - Healthcare worker types (REQUIRED)
    # RN = Registered Nurse, LPN = Licensed Practical Nurse
    # HHA = Home Health Aide, DSP = Direct Support Professional
    categories: List[str] = []  # Array of category codes: ["RN", "LPN", "HHA", "DSP"]
    
    # Billing Codes - HCPCS codes this employee can bill
    # Populated from the payer's billable services
    billing_codes: List[str] = []  # Array of HCPCS codes: ["T1019", "G0156", "T1000"]
    
    # EVV DCW Fields
    staff_pin: Optional[str] = None  # EVV: Staff PIN for telephony (9 digits) - Auto-generated for Sandata
    staff_other_id: Optional[str] = None  # EVV: External system ID
    staff_position: Optional[str] = None  # EVV: Position code (3 characters)
    
    # Sequence Management (EVV)
    sequence_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeProfileUpdate(BaseModel):
    """Employee profile update with all optional fields"""
    model_config = ConfigDict(extra="ignore")
    
    # Basic Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    ssn: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    
    # Registration status
    is_complete: Optional[bool] = None
    
    # Contact Information
    email: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    
    # Employment Information
    employee_id: Optional[str] = None
    
    # Employee Categories (REQUIRED for validation)
    categories: Optional[List[str]] = None  # Array of category codes: ["RN", "LPN", "HHA", "DSP"]
    
    sequence_id: Optional[str] = None


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


class OtherInsurance(BaseModel):
    """Other insurance information for a patient (TPL - Third Party Liability)"""
    insurance_name: str = ""
    subscriber_type: str = "Person"  # Person or Non-Person Entity
    relationship_to_patient: str = ""  # Self, Spouse, Child, Other
    group_number: str = ""
    policy_number: str = ""
    policy_type: str = ""  # Primary, Secondary, Tertiary


class PatientProfile(BaseModel):
    """Patient profile with all required information including EVV compliance"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
    
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
    
    # Other Insurance (TPL - Third Party Liability for Medicaid audits)
    has_other_insurance: bool = False
    other_insurance: Optional[OtherInsurance] = None
    has_second_other_insurance: bool = False
    second_other_insurance: Optional[OtherInsurance] = None
    
    # Sequence Management (EVV)
    sequence_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatientProfileUpdate(BaseModel):
    """Patient profile update with all optional fields"""
    model_config = ConfigDict(extra="ignore")
    
    # Basic Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_newborn: Optional[bool] = None
    
    # Registration status
    is_complete: Optional[bool] = None
    
    # Address
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    address_latitude: Optional[float] = None
    address_longitude: Optional[float] = None
    address_type: Optional[str] = None
    timezone: Optional[str] = None
    
    # Medical Information
    prior_auth_number: Optional[str] = None
    icd10_code: Optional[str] = None
    icd10_description: Optional[str] = None
    physician_name: Optional[str] = None
    physician_npi: Optional[str] = None
    medicaid_number: Optional[str] = None
    patient_other_id: Optional[str] = None
    pims_id: Optional[str] = None
    
    # Phone Numbers
    phone_numbers: Optional[List[PatientPhone]] = None
    
    # Responsible Party
    responsible_party: Optional[PatientResponsibleParty] = None
    sequence_id: Optional[str] = None
    
    # Other Insurance (TPL)
    has_other_insurance: Optional[bool] = None
    other_insurance: Optional[OtherInsurance] = None
    has_second_other_insurance: Optional[bool] = None
    second_other_insurance: Optional[OtherInsurance] = None


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
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
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
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
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
    hours_worked: Optional[str] = None  # Decimal hours (legacy)
    hours: Optional[int] = None  # Hours component (e.g., 8)
    minutes: Optional[int] = None  # Minutes component (e.g., 30)
    formatted_hours: Optional[str] = None  # Human readable (e.g., "8 hr 30 min")
    total_minutes: Optional[int] = None  # Total minutes (e.g., 510)
    units: Optional[int] = None  # Calculated 15-minute units
    
    # Geofencing fields (only for manual clock in/out)
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
    
    # Entry method tracking
    entry_method: Optional[str] = None  # "manual" or "scanned"
    

class EmployeeEntry(BaseModel):
    """Single employee's complete timesheet data"""
    employee_name: Optional[str] = None
    service_code: Optional[str] = None
    signature: Optional[str] = None
    time_entries: List[TimeEntry] = []

class ExtractedData(BaseModel):
    client_name: Optional[str] = None  # Single patient/client
    week_of: Optional[str] = None  # Week date range from timesheet header
    employee_entries: List[EmployeeEntry] = []  # Multiple employees

class Timesheet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None  # Multi-tenant isolation (set by endpoint from JWT)
    filename: str
    file_type: str
    extracted_data: Optional[ExtractedData] = None
    status: str = "processing"  # processing, completed, failed, submitted
    sandata_status: Optional[str] = None  # pending, submitted, error, blocked
    error_message: Optional[str] = None
    entry_method: Optional[str] = "scanned"  # "manual" or "scanned" - determines if geofencing is required
    
    # Linked patient
    patient_id: Optional[str] = None  # Link to patient profile
    
    # Auto-registration results
    registration_results: Optional[Dict] = None  # Patient and employee registration info
    
    # Phase 1 enhancements: Confidence scoring
    metadata: Optional[Dict] = None  # Stores confidence_score, confidence_details, recommendation
    
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

async def check_or_create_patient(client_name: str, organization_id: str) -> Dict[str, Any]:
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
    
    # Search for existing patient (case-insensitive) within organization
    existing_patient = await db.patients.find_one({
        "organization_id": organization_id,
        "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
        "last_name": {"$regex": f"^{last_name}$", "$options": "i"}
    }, {"_id": 0})
    
    if existing_patient:
        logger.info(f"Found existing patient: {first_name} {last_name} for org: {organization_id}")
        return {
            "id": existing_patient["id"],
            "first_name": existing_patient["first_name"],
            "last_name": existing_patient["last_name"],
            "is_complete": existing_patient.get("is_complete", True),
            "exists": True
        }
    
    # Create new incomplete patient profile
    logger.info(f"Auto-creating patient: {first_name} {last_name} for org: {organization_id}")
    new_patient = PatientProfile(
        first_name=first_name,
        last_name=last_name,
        organization_id=organization_id,
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

async def find_similar_employees(employee_name: str, organization_id: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
    """
    Find employees with similar names to the given name.
    Uses fuzzy matching to find potential matches.
    
    Args:
        employee_name: Name to search for
        organization_id: Organization ID for filtering
        threshold: Similarity threshold (0.0 to 1.0)
    
    Returns:
        List of similar employees with similarity scores
    """
    if not employee_name or employee_name.strip() == "":
        return []
    
    # Normalize the search name
    search_name = employee_name.strip().lower()
    search_parts = search_name.split()
    
    # Get all employees for this organization
    employees = await db.employees.find(
        {"organization_id": organization_id},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "categories": 1, "is_complete": 1}
    ).to_list(10000)
    
    similar_employees = []
    
    for emp in employees:
        emp_first = (emp.get('first_name') or '').lower()
        emp_last = (emp.get('last_name') or '').lower()
        emp_full = f"{emp_first} {emp_last}".strip()
        
        # Calculate similarity score
        similarity = calculate_name_similarity(search_name, emp_full)
        
        # Also check if first/last names match individually
        first_match = False
        last_match = False
        
        if len(search_parts) >= 1:
            # Check first name similarity
            if search_parts[0] and emp_first:
                first_sim = calculate_name_similarity(search_parts[0], emp_first)
                first_match = first_sim >= 0.8
        
        if len(search_parts) >= 2:
            # Check last name similarity
            search_last = ' '.join(search_parts[1:])
            if search_last and emp_last:
                last_sim = calculate_name_similarity(search_last, emp_last)
                last_match = last_sim >= 0.8
        
        # Boost similarity if first or last name matches
        if first_match and last_match:
            similarity = max(similarity, 0.95)
        elif first_match or last_match:
            similarity = max(similarity, 0.7)
        
        if similarity >= threshold:
            similar_employees.append({
                "id": emp.get('id'),
                "first_name": emp.get('first_name'),
                "last_name": emp.get('last_name'),
                "full_name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                "categories": emp.get('categories', []),
                "is_complete": emp.get('is_complete', False),
                "similarity_score": round(similarity, 2),
                "match_type": "exact" if similarity >= 0.95 else "similar"
            })
    
    # Sort by similarity score (highest first)
    similar_employees.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return similar_employees[:10]  # Return top 10 matches


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names using Levenshtein distance.
    Returns a score between 0.0 (completely different) and 1.0 (identical).
    """
    if not name1 or not name2:
        return 0.0
    
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    
    if name1 == name2:
        return 1.0
    
    # Calculate Levenshtein distance
    len1, len2 = len(name1), len(name2)
    
    if len1 == 0:
        return 0.0 if len2 > 0 else 1.0
    if len2 == 0:
        return 0.0
    
    # Create distance matrix
    distances = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        distances[i][0] = i
    for j in range(len2 + 1):
        distances[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if name1[i-1] == name2[j-1] else 1
            distances[i][j] = min(
                distances[i-1][j] + 1,      # deletion
                distances[i][j-1] + 1,      # insertion
                distances[i-1][j-1] + cost  # substitution
            )
    
    # Convert distance to similarity score
    max_len = max(len1, len2)
    distance = distances[len1][len2]
    similarity = 1.0 - (distance / max_len)
    
    return similarity


async def check_or_create_employee(employee_name: str, organization_id: str) -> Dict[str, Any]:
    """
    Check if employee exists by name, create if not found.
    Now includes similar employee suggestions when no exact match is found.
    Returns employee info with is_complete flag and similar_employees list.
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
    
    # Search for existing employee (case-insensitive) within organization
    existing_employee = await db.employees.find_one({
        "organization_id": organization_id,
        "first_name": {"$regex": f"^{first_name}$", "$options": "i"},
        "last_name": {"$regex": f"^{last_name}$", "$options": "i"}
    }, {"_id": 0})
    
    if existing_employee:
        logger.info(f"Found existing employee: {first_name} {last_name} for org: {organization_id}")
        return {
            "id": existing_employee["id"],
            "first_name": existing_employee["first_name"],
            "last_name": existing_employee["last_name"],
            "is_complete": existing_employee.get("is_complete", True),
            "exists": True,
            "similar_employees": []  # No suggestions needed for exact match
        }
    
    # No exact match found - look for similar employees
    similar_employees = await find_similar_employees(employee_name, organization_id, threshold=0.5)
    
    # If we found very similar employees (>= 0.85 similarity), suggest using them instead
    high_similarity_matches = [e for e in similar_employees if e['similarity_score'] >= 0.85]
    
    if high_similarity_matches:
        # Found very similar names - suggest them but still create the new profile
        logger.info(f"Found {len(high_similarity_matches)} similar employees for '{employee_name}' - suggesting matches")
    
    # Create new incomplete employee profile
    logger.info(f"Auto-creating employee: {first_name} {last_name} for org: {organization_id}")
    new_employee = EmployeeProfile(
        first_name=first_name,
        last_name=last_name,
        organization_id=organization_id,
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
        "message": "Auto-created incomplete profile - please update",
        "similar_employees": similar_employees,  # Include suggestions
        "has_similar_matches": len(high_similarity_matches) > 0
    }

async def extract_timesheet_data(file_path: str, file_type: str, page_number: int = 1, progress_tracker: ExtractionProgress = None) -> Tuple[ExtractedData, float, dict]:
    """Extract data from timesheet using Gemini Vision API with confidence scoring
    
    Args:
        file_path: Path to the file
        file_type: Type of file (pdf, jpg, jpeg, png)
        page_number: Page number to extract (for multi-page PDFs)
        progress_tracker: Optional progress tracker for real-time updates
    
    Returns:
        Tuple of (ExtractedData, confidence_score, confidence_details)
    """
    try:
        if progress_tracker:
            await progress_tracker.update(status="processing", progress_percent=10, 
                                         current_step="Initializing AI model")
        
        # Using OCR model from scan_config.py (SINGLE SOURCE OF TRUTH)
        # Change OCR_MODEL_SETTINGS in scan_config.py to switch models
        ocr_provider = OCR_MODEL_SETTINGS['provider']
        ocr_model = OCR_MODEL_SETTINGS['model']
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"timesheet-{uuid.uuid4()}",
            system_message="""You are an expert OCR system specialized in extracting structured data from timesheets. 
You have been trained on millions of timesheet documents and can accurately read:
- Handwritten text (names, times, dates)
- Printed text in various fonts
- Tables and structured layouts
- Signatures and initials
- Poor quality or faded scans

Always extract all fields accurately and return valid JSON. Pay special attention to:
- Time formats (convert all to consistent format)
- Date formats (extract full dates when possible)
- Employee names (preserve exact spelling for matching)
- Service codes and billing information"""
        ).with_model(ocr_provider, ocr_model)
        
        # Convert PDF to image if needed (Gemini works better with images)
        processing_file_path = file_path
        mime_type = "image/jpeg"
        temp_image_created = False
        
        if file_type == 'pdf':
            try:
                if progress_tracker:
                    await progress_tracker.update(progress_percent=20, current_step="Converting PDF to image")
                
                logger.info(f"Converting PDF page {page_number} to image: {file_path}")
                # Convert specific PDF page to image with optimized settings for OCR
                # DPI 300 provides better text clarity for handwritten entries
                # Using 'rgb' format for color preservation
                images = convert_from_path(
                    file_path, 
                    first_page=page_number, 
                    last_page=page_number, 
                    dpi=300,  # Higher DPI for better OCR accuracy
                    fmt='jpeg',
                    thread_count=2,  # Parallel processing
                    grayscale=False,  # Keep color for signature detection
                    transparent=False
                )
                if images:
                    # Save as JPEG with high quality for OCR
                    image_path = file_path.replace('.pdf', f'_page{page_number}.jpg')
                    # Quality 98 preserves text clarity while keeping file size reasonable
                    images[0].save(image_path, 'JPEG', quality=98, optimize=True)
                    processing_file_path = image_path
                    temp_image_created = True
                    logger.info(f"PDF page {page_number} converted to image at 300 DPI: {image_path}")
                else:
                    raise Exception("No images returned from PDF conversion")
            except Exception as e:
                logger.error(f"PDF conversion error for page {page_number}: {e}")
                logger.warning(f"Cannot process individual pages - PDF conversion failed")
                # If conversion fails, we can't process individual pages properly
                # Return empty data with error
                if progress_tracker:
                    await progress_tracker.error("PDF conversion failed")
                return ExtractedData(
                    client_name="Error: PDF conversion failed",
                    employee_entries=[]
                ), 0.0, {}
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
  "week_of": "week date range if shown (e.g., '10/6/2024 - 10/12/2024', '10-6 to 10-12', 'Week of 10/6')",
  "employee_entries": [
    {
      "employee_name": "first employee's full name",
      "service_code": "service or billing code for this employee",
      "signature": "Yes if signature is present, No if not",
      "time_entries": [
        {
          "date": "date as shown (e.g., '10/6', '10-6', 'Monday', 'Mon', '6')",
          "time_in": "time format as shown",
          "time_out": "time format as shown",
          "hours_worked": "hours in decimal format (e.g., 8.5, 0.58) - system will convert to hours and minutes"
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

DATE EXTRACTION RULES (CRITICAL):
- **ALWAYS LOOK FOR WEEK INFORMATION FIRST** at the top of the timesheet
- Week formats: "Week of 10/6/2024", "10/6/2024 - 10/12/2024", "Week ending 10/12/2024"
- If you see a week range, capture it EXACTLY in the "week_of" field
- For individual dates, extract in COMPLETE format when possible:
  * BEST: "10/6/2024" or "10-06-2024" (full date with year)
  * GOOD: "10/6" or "10-06" (month/day)
  * OKAY: "Monday", "Mon", "M" (day name)
  * LAST RESORT: "6" (day number only)
- If the document shows "Monday 10/6/2024", extract as "10/6/2024"
- If only day number is shown, check nearby dates for context
- ALWAYS try to find the year - check corners, headers, footers
- Common date separators: / - . (space)

NAME EXTRACTION RULES (CRITICAL - ENHANCED FOR SIMILAR MATCHING):
- Extract FULL names exactly as written - First Middle Last if present
- PRESERVE original spelling even if it looks like a typo (system will suggest corrections)
- Look for multiple name formats:
  * "Smith, John" → extract as "John Smith"
  * "John Smith" → extract as "John Smith"
  * "J. Smith" → extract as "J. Smith"
  * "SMITH JOHN" (all caps) → extract as "John Smith" (capitalize properly)
- For handwritten names:
  * Extract best readable interpretation
  * Include all characters you can identify
  * System will match against employee database for suggestions
- Check for common OCR errors but EXTRACT AS-IS:
  * "0" (zero) instead of "O" in names - extract as seen
  * "1" (one) instead of "I" or "l" - extract as seen
  * "5" instead of "S" - extract as seen
- Employee signatures may contain initials - extract full name from printed section
- If name is partially illegible, extract what you CAN read (e.g., "J??? Smith" → "J Smith")

SERVICE CODE EXTRACTION:
- Common Ohio Medicaid service codes: T1019, T1020, T1021, S5125, S5126, S5130, S5131
- Extract exactly as shown - preserve case and formatting
- If unclear, extract best interpretation

TIME FORMAT RULES:
- Extract times EXACTLY as shown in the document
- Military time examples: "1800", "0830", "1345" (4 digits)
- 24-hour with colon: "18:00", "08:30", "13:45"
- 12-hour format: "8:30 AM", "5:45 PM", "8:30", "5:45"
- DO NOT convert - extract as-is, system will normalize
- Examples: "1800", "18:00", "6:00 PM", "8:30" all acceptable
- Watch for handwritten times that might be unclear

HOURS WORKED FORMAT:
- Extract as DECIMAL hours (e.g., 8.5, 10.25, 0.58)
- System will automatically convert to "H:MM" format (e.g., 8:30, 0:36)
- If document shows "8:30" (hours:minutes), convert to 8.5 decimal
- If document shows "8 hr 30 min", convert to 8.5 decimal
- Examples:
  * 8 hours 30 minutes = 8.5 → displays as 8:30
  * 45 minutes = 0.75 → displays as 0:45
  * 35 minutes = 0.58 → displays as 0:35
  * 10 hours 15 minutes = 10.25 → displays as 10:15

SIGNATURE DETECTION:
- Look for: handwritten signatures, initials, "X" marks, stamps
- "Yes" if ANY signature mark is present in signature area
- "No" if signature area is blank or marked "N/A"

ORDERING:
- Maintain the exact order entries appear in the document
- If John's entry appears before Mary's, list John first
- Within each employee, list time entries in document order

Return ONLY the JSON object, no additional text or explanation."""
        
        user_message = UserMessage(
            text=extraction_prompt,
            file_contents=[file_content]
        )
        
        if progress_tracker:
            await progress_tracker.update(progress_percent=40, current_step="Analyzing timesheet with AI")
        
        response = await chat.send_message(user_message)
        logger.info(f"LLM Raw Response: {response}")
        
        if progress_tracker:
            await progress_tracker.update(progress_percent=70, current_step="Parsing extracted data")
        
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
            
            # Normalize dates using week context
            extracted_json = normalize_dates_in_extracted_data(extracted_json)
            
            # Get week range for date inference
            week_of = extracted_json.get("week_of")
            week_range = parse_week_range(week_of) if week_of else None
            
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
                                    # Get and infer date if needed
                                    raw_date = entry.get("date", "")
                                    inferred_date = parse_date_with_context(raw_date, week_range) if raw_date else ""
                                    entry['date'] = inferred_date if inferred_date else raw_date
                                    
                                    # Get original times
                                    time_in = entry.get("time_in", "")
                                    time_out = entry.get("time_out", "")
                                    
                                    # Normalize AM/PM first for calculation
                                    normalized_time_in = normalize_am_pm(time_in) if time_in else ""
                                    normalized_time_out = normalize_am_pm(time_out) if time_out else ""
                                    
                                    # Calculate units and hours from time difference
                                    units, calculated_hours = calculate_units_from_times(normalized_time_in, normalized_time_out)
                                    
                                    # Convert to 12-hour format (HH:MM AM/PM) for display
                                    # This preserves AM/PM information and is more readable
                                    formatted_time_in = format_time_12h(time_in) if time_in else ""
                                    formatted_time_out = format_time_12h(time_out) if time_out else ""
                                    
                                    # Use calculated hours if available, otherwise use extracted value
                                    hours_worked_decimal = calculated_hours if calculated_hours is not None else entry.get("hours_worked")
                                    
                                    # Convert decimal hours to hours and minutes
                                    hours_minutes = decimal_hours_to_hours_minutes(hours_worked_decimal)
                                    
                                    # Format date to MM/DD/YYYY
                                    entry_date = entry.get("date", "")
                                    if entry_date:
                                        entry_date = format_date_mm_dd_yyyy(entry_date)
                                    
                                    # Create TimeEntry with 12-hour times (HH:MM AM/PM), calculated units, and formatted hours
                                    time_entry = TimeEntry(
                                        date=entry_date,
                                        time_in=formatted_time_in,  # Now in HH:MM AM/PM format (e.g., "09:00 AM", "05:30 PM")
                                        time_out=formatted_time_out,  # Now in HH:MM AM/PM format
                                        hours_worked=str(hours_worked_decimal) if hours_worked_decimal else None,  # Keep for backward compatibility
                                        hours=hours_minutes['hours'],
                                        minutes=hours_minutes['minutes'],
                                        formatted_hours=hours_minutes['formatted'],
                                        total_minutes=hours_minutes['total_minutes'],
                                        units=units
                                    )
                                    
                                    time_entries.append(time_entry)
                        
                        # Create employee entry
                        employee_entries.append(EmployeeEntry(
                            employee_name=emp_entry.get("employee_name"),
                            service_code=emp_entry.get("service_code"),
                            signature=emp_entry.get("signature"),
                            time_entries=time_entries
                        ))
            
            # Create ExtractedData with validated fields
            extracted_data = ExtractedData(
                client_name=extracted_json.get("client_name"),
                week_of=extracted_json.get("week_of"),
                employee_entries=employee_entries
            )
            
            # Calculate confidence scores
            if progress_tracker:
                await progress_tracker.update(progress_percent=90, current_step="Calculating confidence scores")
            
            confidence_score, confidence_details = ConfidenceScorer.score_extraction(extracted_json)
            logger.info(f"Extraction confidence score: {confidence_score:.2f} ({confidence_details.get('recommendation')})")
            
            # Add similar employee suggestions to confidence details
            confidence_details['similar_employee_suggestions'] = []
            raw_employee_entries = extracted_json.get('employee_entries', [])
            for emp_entry in raw_employee_entries:
                if isinstance(emp_entry, dict) and emp_entry.get('employee_name'):
                    emp_name = emp_entry['employee_name']
                    # Note: Similar employees will be fetched when timesheet is loaded in editor
                    confidence_details['similar_employee_suggestions'].append({
                        'extracted_name': emp_name,
                        'suggestion': 'Click the 👥 icon next to employee name to find matching employees'
                    })
            
            if progress_tracker:
                await progress_tracker.complete(extracted_json, confidence_score, confidence_details)
            
            return extracted_data, confidence_score, confidence_details
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Failed to parse: {response_text}")
            if progress_tracker:
                await progress_tracker.error(f"JSON parsing error: {str(e)}")
            return ExtractedData(), 0.0, {}
        except TypeError as e:
            logger.error(f"Type error when creating ExtractedData: {e}")
            if progress_tracker:
                await progress_tracker.error(f"Type error: {str(e)}")
            return ExtractedData(), 0.0, {}
            
    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
        if progress_tracker:
            await progress_tracker.error(str(e))
        raise

async def submit_to_sandata(timesheet: Timesheet) -> dict:
    """
    Submit timesheet data to Sandata API
    IMPORTANT: Validates that patient and all employees have complete profiles before submission
    """
    try:
        # Check if patient profile is complete
        if timesheet.patient_id:
            patient = await db.patients.find_one({"id": timesheet.patient_id, "organization_id": timesheet.organization_id}, {"_id": 0})
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
                            "organization_id": timesheet.organization_id,
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

@api_router.post("/timesheets/upload-enhanced")
async def upload_timesheet_enhanced(file: UploadFile = File(...), organization_id: str = Depends(get_organization_id)):
    """
    Enhanced timesheet upload with real-time WebSocket updates, parallel processing, and confidence scoring
    Phase 1 improvements implemented
    """
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
        
        # Check if PDF has multiple pages
        page_count = 1
        if file_extension == 'pdf':
            page_count = await get_pdf_page_count(str(file_path))
            logger.info(f"PDF has {page_count} page(s)")
        
        # Create timesheet records first (so we have IDs for WebSocket tracking)
        timesheets_to_process = []
        for page_num in range(1, page_count + 1):
            page_suffix = f" (Page {page_num}/{page_count})" if page_count > 1 else ""
            timesheet = Timesheet(
                filename=f"{file.filename}{page_suffix}",
                file_type=file_extension,
                status="processing",
                organization_id=organization_id
            )
            
            # Save to database
            doc = timesheet.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.timesheets.insert_one(doc)
            
            timesheets_to_process.append((timesheet, page_num))
        
        # Process pages in parallel
        async def process_single_page(timesheet: Timesheet, page_num: int):
            """Process a single page with progress tracking"""
            try:
                # Create progress tracker with WebSocket manager
                progress_tracker = ExtractionProgress(timesheet.id, ws_manager)
                await progress_tracker.update(status="starting", progress_percent=5,
                                            current_step=f"Starting extraction for page {page_num}")
                
                # Extract data with progress tracking
                extracted_data, confidence_score, confidence_details = await extract_timesheet_data(
                    str(file_path), file_extension, page_num, progress_tracker
                )
                
                # Fill missing dates by cross-comparing with other timesheets
                if extracted_data:
                    try:
                        # Convert to dict for date processing
                        extracted_dict = extracted_data.model_dump() if hasattr(extracted_data, 'model_dump') else dict(extracted_data)
                        
                        # Fill missing dates using cross-comparison
                        filled_data = await fill_missing_dates_for_timesheet(extracted_dict, db, organization_id)
                        
                        # Convert dates to MM/DD/YYYY format
                        if filled_data.get('employee_entries'):
                            for emp in filled_data['employee_entries']:
                                if emp.get('time_entries'):
                                    for entry in emp['time_entries']:
                                        if entry.get('date'):
                                            entry['date'] = format_date_mm_dd_yyyy(entry['date'])
                        
                        # Update extracted_data with filled dates
                        extracted_data = ExtractedData(**filled_data) if filled_data else extracted_data
                        logger.info(f"Dates filled for timesheet page {page_num}")
                    except Exception as e:
                        logger.warning(f"Could not fill missing dates: {e}")
                
                timesheet.extracted_data = extracted_data
                timesheet.status = "completed"
                
                # Store confidence information
                if not hasattr(timesheet, 'metadata'):
                    timesheet.metadata = {}
                timesheet.metadata = {
                    "confidence_score": confidence_score,
                    "confidence_details": confidence_details,
                    "recommendation": confidence_details.get("recommendation", "review_recommended")
                }
                
                # Check and auto-register patient and employees
                registration_results = {
                    "patient": None,
                    "employees": [],
                    "incomplete_profiles": []
                }
                
                if extracted_data and extracted_data.client_name:
                    # Check/create patient
                    patient_info = await check_or_create_patient(extracted_data.client_name, organization_id)
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
                                employee_info = await check_or_create_employee(emp_entry.employee_name, organization_id)
                                if employee_info:
                                    registration_results["employees"].append(employee_info)
                                    if not employee_info.get("is_complete"):
                                        registration_results["incomplete_profiles"].append({
                                            "type": "employee",
                                            "name": f"{employee_info['first_name']} {employee_info['last_name']}",
                                            "id": employee_info["id"]
                                        })
                
                # Store registration results
                timesheet.registration_results = registration_results
                
                # Auto-submit based on confidence (only if confidence is high)
                if confidence_score >= 0.95:
                    submission_result = await submit_to_sandata(timesheet)
                    if submission_result["status"] == "success":
                        timesheet.sandata_status = "submitted"
                    elif submission_result["status"] == "blocked":
                        timesheet.sandata_status = "blocked"
                        timesheet.error_message = submission_result.get("message")
                    else:
                        timesheet.sandata_status = "error"
                        timesheet.error_message = submission_result.get("message")
                else:
                    timesheet.sandata_status = "pending"
                    timesheet.error_message = f"Manual review recommended (confidence: {confidence_score:.1%})"
                
            except Exception as e:
                logger.error(f"Processing error for page {page_num}: {e}")
                timesheet.status = "failed"
                timesheet.error_message = str(e)
                
                # Update progress tracker
                progress_tracker = ExtractionProgress(timesheet.id, ws_manager)
                await progress_tracker.error(str(e))
            
            # Update database
            timesheet.updated_at = datetime.now(timezone.utc)
            update_doc = timesheet.model_dump()
            update_doc['created_at'] = update_doc['created_at'].isoformat()
            update_doc['updated_at'] = update_doc['updated_at'].isoformat()
            
            await db.timesheets.update_one(
                {"id": timesheet.id},
                {"$set": update_doc}
            )
            
            # Clean up temp page image if created
            try:
                page_image_path = str(file_path).replace('.pdf', f'_page{page_num}.jpg')
                Path(page_image_path).unlink(missing_ok=True)
            except:
                pass
            
            return timesheet
        
        # Process all pages in parallel
        logger.info(f"Processing {len(timesheets_to_process)} pages in parallel")
        tasks = [process_single_page(ts, page_num) for ts, page_num in timesheets_to_process]
        created_timesheets = await asyncio.gather(*tasks)
        
        # Clean up original temp file
        try:
            file_path.unlink()
        except:
            pass
        
        # Return results
        if len(created_timesheets) == 1:
            return created_timesheets[0]
        else:
            return {
                "message": f"Batch processing complete: {len(created_timesheets)} timesheets created",
                "total_pages": page_count,
                "timesheets": created_timesheets,
                "average_confidence": sum(ts.metadata.get("confidence_score", 0) for ts in created_timesheets) / len(created_timesheets) if created_timesheets else 0
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/")
async def root():
    return {"message": "Timesheet Scanner API"}

@api_router.post("/timesheets/upload")
async def upload_timesheet(file: UploadFile = File(...), organization_id: str = Depends(get_organization_id)):
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
                status="processing",
                organization_id=organization_id,
                entry_method="scanned"  # Mark as scanned - no geofencing required
            )
            
            # Save to database
            doc = timesheet.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.timesheets.insert_one(doc)
            
            # Extract data for this specific page
            try:
                # extract_timesheet_data returns (ExtractedData, confidence_score, metadata)
                result = await extract_timesheet_data(str(file_path), file_extension, page_num)
                if isinstance(result, tuple):
                    extracted_data, confidence_score, metadata = result
                    # Store confidence and metadata
                    timesheet.metadata = {
                        "confidence_score": confidence_score,
                        "confidence_details": metadata
                    }
                else:
                    extracted_data = result
                
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
                    patient_info = await check_or_create_patient(extracted_data.client_name, organization_id)
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
                                employee_info = await check_or_create_employee(emp_entry.employee_name, organization_id)
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
        # Convert to dict for JSON serialization without validation
        result_timesheets = []
        for ts in created_timesheets:
            ts_dict = ts.model_dump()
            if isinstance(ts_dict.get('created_at'), datetime):
                ts_dict['created_at'] = ts_dict['created_at'].isoformat()
            if isinstance(ts_dict.get('updated_at'), datetime):
                ts_dict['updated_at'] = ts_dict['updated_at'].isoformat()
            result_timesheets.append(ts_dict)
        
        if len(result_timesheets) == 1:
            return result_timesheets[0]
        else:
            return {
                "message": f"Batch processing complete: {len(result_timesheets)} timesheets created",
                "total_pages": page_count,
                "timesheets": result_timesheets
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
    skip: int = 0,
    organization_id: str = Depends(get_organization_id)
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
    query = {"organization_id": organization_id}
    
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
    
    # Convert datetime objects to ISO strings for JSON serialization
    for ts in timesheets:
        if isinstance(ts.get('created_at'), datetime):
            ts['created_at'] = ts['created_at'].isoformat()
        if isinstance(ts.get('updated_at'), datetime):
            ts['updated_at'] = ts['updated_at'].isoformat()
    
    return timesheets

@api_router.get("/timesheets/{timesheet_id}")
async def get_timesheet(timesheet_id: str, organization_id: str = Depends(get_organization_id)):
    """Get specific timesheet by ID"""
    timesheet = await db.timesheets.find_one({"id": timesheet_id, "organization_id": organization_id}, {"_id": 0})
    
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Convert datetime fields to ISO strings for JSON serialization
    if isinstance(timesheet.get('created_at'), datetime):
        timesheet['created_at'] = timesheet['created_at'].isoformat()
    if isinstance(timesheet.get('updated_at'), datetime):
        timesheet['updated_at'] = timesheet['updated_at'].isoformat()
    
    # Return as dict for proper JSON serialization
    return timesheet

@api_router.put("/timesheets/{timesheet_id}", response_model=Timesheet)
async def update_timesheet(timesheet_id: str, timesheet_update: Timesheet, organization_id: str = Depends(get_organization_id)):
    """Update timesheet data (for manual corrections)"""
    timesheet_update.id = timesheet_id
    timesheet_update.organization_id = organization_id
    timesheet_update.updated_at = datetime.now(timezone.utc)
    
    doc = timesheet_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.timesheets.update_one(
        {"id": timesheet_id, "organization_id": organization_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    logger.info(f"Timesheet updated manually: {timesheet_id}")
    return timesheet_update

@api_router.delete("/timesheets/{timesheet_id}")
async def delete_timesheet(timesheet_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete a timesheet"""
    result = await db.timesheets.delete_one({"id": timesheet_id, "organization_id": organization_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    return {"message": "Timesheet deleted successfully"}


@api_router.post("/timesheets/{timesheet_id}/rescan")
async def rescan_timesheet(timesheet_id: str, organization_id: str = Depends(get_organization_id)):
    """
    Re-scan/re-process a timesheet to update extracted data
    This is useful when:
    - OCR initially extracted incorrect data
    - User wants to retry extraction with improved AI
    - File was processed with errors
    """
    try:
        # Get the timesheet
        timesheet_doc = await db.timesheets.find_one(
            {"id": timesheet_id, "organization_id": organization_id}, 
            {"_id": 0}
        )
        
        if not timesheet_doc:
            raise HTTPException(status_code=404, detail="Timesheet not found")
        
        # Check if original file still exists (stored files are temporary)
        filename = timesheet_doc.get('filename', '')
        file_type = timesheet_doc.get('file_type', 'pdf')
        
        # Note: This requires the original file - in production, you'd store files permanently
        # For now, return a message that re-scanning requires re-upload
        
        logger.info(f"Re-scan requested for timesheet {timesheet_id}")
        
        return {
            "message": "Re-scanning functionality requires file re-upload",
            "suggestion": "Please delete this timesheet and upload the file again for improved extraction",
            "timesheet_id": timesheet_id,
            "filename": filename
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Re-scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/timesheets/fill-dates")
async def fill_missing_dates_batch(
    timesheet_ids: List[str] = None,
    organization_id: str = Depends(get_organization_id)
):
    """
    Fill missing dates for timesheets by cross-comparing with other timesheets.
    
    Timesheets are scanned weekly, so if one timesheet has a week_of field or
    complete dates, we can infer dates for other timesheets in the same batch.
    
    Args:
        timesheet_ids: Optional list of specific timesheet IDs to process.
                      If not provided, processes all timesheets from the last 7 days.
    
    Returns:
        Summary of dates filled
    """
    try:
        # Get timesheets to process
        query = {"organization_id": organization_id}
        
        if timesheet_ids:
            query["id"] = {"$in": timesheet_ids}
        else:
            # Get timesheets from last 7 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            query["created_at"] = {"$gte": cutoff.isoformat()}
        
        timesheets = await db.timesheets.find(query, {"_id": 0}).to_list(500)
        
        if not timesheets:
            return {
                "status": "no_timesheets",
                "message": "No timesheets found to process"
            }
        
        logger.info(f"Processing {len(timesheets)} timesheets for date filling")
        
        # Convert to format expected by cross_compare_and_fill_dates
        timesheet_data = []
        for ts in timesheets:
            extracted = ts.get('extracted_data', {})
            if isinstance(extracted, dict):
                timesheet_data.append({
                    "id": ts.get('id'),
                    "extracted_data": extracted
                })
        
        # Cross-compare and fill dates
        filled_timesheets = cross_compare_and_fill_dates(timesheet_data, organization_id)
        
        # Update timesheets in database
        updated_count = 0
        filled_dates_count = 0
        
        for ts_data in filled_timesheets:
            ts_id = ts_data.get('id')
            if not ts_id:
                continue
            
            extracted = ts_data.get('extracted_data', {})
            
            # Count filled dates
            for emp in extracted.get('employee_entries', []):
                for entry in emp.get('time_entries', []):
                    if entry.get('date_inferred'):
                        filled_dates_count += 1
            
            # Update in database
            result = await db.timesheets.update_one(
                {"id": ts_id, "organization_id": organization_id},
                {
                    "$set": {
                        "extracted_data": extracted,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            if result.modified_count > 0:
                updated_count += 1
        
        return {
            "status": "success",
            "message": f"Processed {len(timesheets)} timesheets",
            "timesheets_updated": updated_count,
            "dates_filled": filled_dates_count,
            "date_format": "MM/DD/YYYY"
        }
    
    except Exception as e:
        logger.error(f"Error filling dates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/system/pdf-status")
async def get_pdf_status():
    """
    Check PDF processing status and scan parameters.
    Also reinstalls poppler-utils if missing.
    All scan parameters are permanently configured in code.
    """
    import shutil
    
    # Check if poppler-utils is installed
    pdftoppm_path = shutil.which('pdftoppm')
    poppler_installed = pdftoppm_path is not None
    
    # Try to install if missing
    if not poppler_installed:
        try:
            subprocess.run(['apt-get', 'update', '-qq'], capture_output=True, timeout=30)
            subprocess.run(['apt-get', 'install', '-y', 'poppler-utils'], capture_output=True, timeout=60)
            pdftoppm_path = shutil.which('pdftoppm')
            poppler_installed = pdftoppm_path is not None
            install_attempted = True
        except Exception as e:
            install_attempted = True
            logger.error(f"Failed to install poppler-utils: {e}")
    else:
        install_attempted = False
    
    # Get version if installed
    poppler_version = None
    if poppler_installed:
        try:
            result = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True, timeout=5)
            poppler_version = result.stderr.strip().split('\n')[0] if result.stderr else "Unknown"
        except:
            poppler_version = "Unknown"
    
    return {
        "status": "ready" if poppler_installed else "unavailable",
        "config_source": "scan_config.py (single source of truth)",
        "ocr_model": {
            "provider": OCR_MODEL_SETTINGS['provider'].title(),
            "model": OCR_MODEL_SETTINGS['model'],
            "description": OCR_MODEL_SETTINGS.get('description', 'OCR model for timesheet processing'),
            "capabilities": [cap.replace('_', ' ').title() for cap in OCR_MODEL_SETTINGS['capabilities']],
            "alternatives": OCR_MODEL_SETTINGS['alternatives'],
            "last_updated": OCR_MODEL_SETTINGS['last_updated']
        },
        "poppler_utils": {
            "installed": poppler_installed,
            "path": pdftoppm_path,
            "version": poppler_version,
            "install_attempted": install_attempted
        },
        "scan_parameters": {
            "dpi": PDF_SETTINGS['dpi'],
            "jpeg_quality": PDF_SETTINGS['jpeg_quality'],
            "color_mode": PDF_SETTINGS['color_mode'],
            "thread_count": PDF_SETTINGS['thread_count']
        },
        "time_format": {
            "display": f"{TIME_SETTINGS['display_format']} ({TIME_SETTINGS.get('display_example', 'N/A')})",
            "example": TIME_SETTINGS.get('display_example', '09:00 AM, 05:30 PM'),
            "supports_24h_input": True,
            "ocr_fixes": {
                "decimal_to_colon": TIME_SETTINGS['ocr_fixes'].get('decimal_to_colon_example', '6.70 → 06:10'),
                "invalid_minutes": "6:70 → 06:10 (70→10)",
                "enabled": TIME_SETTINGS['ocr_fixes']['decimal_to_colon']
            },
            "auto_applied": True
        },
        "date_format": {
            "output": DATE_SETTINGS['output_format'],
            "example": "12/30/2024",
            "week_inference": DATE_SETTINGS['week_inference'],
            "cross_timesheet_comparison": DATE_SETTINGS['cross_timesheet_comparison'],
            "auto_applied": True
        },
        "unit_calculation": {
            "minutes_per_unit": UNIT_SETTINGS['minutes_per_unit'],
            "rounding": UNIT_SETTINGS['rounding'],
            "auto_applied": True
        },
        "extraction_features": {
            "service_codes": EXTRACTION_SETTINGS['service_codes'],
            "signature_detection": EXTRACTION_SETTINGS['signature_detection'],
            "similar_employee_matching": EXTRACTION_SETTINGS['similar_employee_matching'],
            "name_correction": EXTRACTION_SETTINGS.get('preserve_ocr_names', True),
            "auto_applied": True
        },
        "message": "PDF processing ready. All settings loaded from scan_config.py." if poppler_installed else "PDF processing unavailable - poppler-utils installation failed"
    }


@api_router.post("/system/reinstall-pdf-deps")
async def reinstall_pdf_dependencies():
    """
    Force reinstall poppler-utils and verify scan parameters.
    Use this if PDF processing is failing.
    """
    import shutil
    
    try:
        # Force reinstall
        logger.info("Force reinstalling poppler-utils...")
        
        result1 = subprocess.run(['apt-get', 'update', '-qq'], capture_output=True, text=True, timeout=30)
        result2 = subprocess.run(['apt-get', 'install', '-y', '--reinstall', 'poppler-utils'], 
                                capture_output=True, text=True, timeout=60)
        
        # Verify installation
        pdftoppm_path = shutil.which('pdftoppm')
        poppler_installed = pdftoppm_path is not None
        
        # Get version
        poppler_version = None
        if poppler_installed:
            try:
                result = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True, timeout=5)
                poppler_version = result.stderr.strip().split('\n')[0] if result.stderr else "Unknown"
            except:
                poppler_version = "Unknown"
        
        return {
            "status": "success" if poppler_installed else "failed",
            "poppler_utils": {
                "installed": poppler_installed,
                "path": pdftoppm_path,
                "version": poppler_version
            },
            "scan_parameters_applied": {
                "dpi": 300,
                "jpeg_quality": 98,
                "color_mode": "RGB",
                "date_format": "MM/DD/YYYY",
                "date_inference": True,
                "service_codes": ["T1019", "T1020", "T1021", "S5125", "S5126", "S5130", "S5131"],
                "signature_detection": True,
                "similar_employee_matching": True
            },
            "message": "PDF dependencies reinstalled successfully" if poppler_installed else "Reinstallation failed"
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Installation timed out")
    except Exception as e:
        logger.error(f"Error reinstalling PDF dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

@api_router.post("/timesheets/{timesheet_id}/submit-sandata")
async def submit_timesheet_to_sandata(timesheet_id: str, organization_id: str = Depends(get_organization_id)):
    """
    Submit timesheet to Sandata API (for payroll and billing processing)
    Validates patient/employee completion before submission
    
    ⚠️ MOCKED IMPLEMENTATION
    This endpoint simulates Sandata API submission for testing purposes.
    Real implementation requires:
    - Valid Sandata API credentials (API key, auth token)
    - Sandata endpoint URL
    - Proper authentication setup
    - See: https://www.sandata.com/api-documentation
    """
    try:
        # Get timesheet
        timesheet = await db.timesheets.find_one({"id": timesheet_id, "organization_id": organization_id}, {"_id": 0})
        
        if not timesheet:
            raise HTTPException(status_code=404, detail="Timesheet not found")
        
        # MOCKED: Simulated Sandata API submission
        logger.info(f"[MOCK] Submitting timesheet {timesheet_id} to Sandata API")
        
        # Mock successful response
        return {
            "status": "success",
            "message": "Timesheet submitted to Sandata successfully (MOCKED)",
            "sandata_id": f"SND-{timesheet_id[:8].upper()}",
            "submission_date": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sandata submission error: {e}")
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
async def bulk_update_patients(request: BulkUpdateRequest, organization_id: str = Depends(get_organization_id)):
    """Bulk update multiple patient profiles
    
    Common use case: Mark multiple profiles as complete
    """
    try:
        # Validate IDs exist within organization
        count = await db.patients.count_documents({"id": {"$in": request.ids}, "organization_id": organization_id})
        
        if count == 0:
            raise HTTPException(status_code=404, detail="No patients found with provided IDs")
        
        # Add updated_at timestamp
        updates = request.updates.copy()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Perform bulk update within organization
        result = await db.patients.update_many(
            {"id": {"$in": request.ids}, "organization_id": organization_id},
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
async def bulk_update_employees(request: BulkUpdateRequest, organization_id: str = Depends(get_organization_id)):
    """Bulk update multiple employee profiles
    
    Common use case: Mark multiple profiles as complete
    """
    try:
        # Validate IDs exist within organization
        count = await db.employees.count_documents({"id": {"$in": request.ids}, "organization_id": organization_id})
        
        if count == 0:
            raise HTTPException(status_code=404, detail="No employees found with provided IDs")
        
        # Add updated_at timestamp
        updates = request.updates.copy()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Perform bulk update within organization
        result = await db.employees.update_many(
            {"id": {"$in": request.ids}, "organization_id": organization_id},
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
async def bulk_delete_patients(request: BulkDeleteRequest, organization_id: str = Depends(get_organization_id)):
    """Bulk delete multiple patient profiles"""
    try:
        result = await db.patients.delete_many({"id": {"$in": request.ids}, "organization_id": organization_id})
        
        logger.info(f"Bulk deleted {result.deleted_count} patients")
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/employees/bulk-delete")
async def bulk_delete_employees(request: BulkDeleteRequest, organization_id: str = Depends(get_organization_id)):
    """Bulk delete multiple employee profiles"""
    try:
        result = await db.employees.delete_many({"id": {"$in": request.ids}, "organization_id": organization_id})
        
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

# Organization Management Endpoints

@api_router.post("/organizations", response_model=Organization)
async def create_organization(org: Organization):
    """Create a new organization"""
    try:
        org_dict = org.dict()
        org_dict["created_at"] = org_dict["created_at"].isoformat()
        org_dict["updated_at"] = org_dict["updated_at"].isoformat()
        if org_dict.get("trial_ends_at"):
            org_dict["trial_ends_at"] = org_dict["trial_ends_at"].isoformat()
        if org_dict.get("last_payment_at"):
            org_dict["last_payment_at"] = org_dict["last_payment_at"].isoformat()
        
        await db.organizations.insert_one(org_dict)
        logger.info(f"Organization created: {org.id}")
        return org
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/organizations/{org_id}", response_model=Organization)
async def get_organization(org_id: str):
    """Get organization details"""
    try:
        org_doc = await db.organizations.find_one({"id": org_id}, {"_id": 0})
        if not org_doc:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Convert ISO strings back to datetime
        if isinstance(org_doc.get('created_at'), str):
            org_doc['created_at'] = datetime.fromisoformat(org_doc['created_at'])
        if isinstance(org_doc.get('updated_at'), str):
            org_doc['updated_at'] = datetime.fromisoformat(org_doc['updated_at'])
        if org_doc.get('trial_ends_at') and isinstance(org_doc['trial_ends_at'], str):
            org_doc['trial_ends_at'] = datetime.fromisoformat(org_doc['trial_ends_at'])
        if org_doc.get('last_payment_at') and isinstance(org_doc['last_payment_at'], str):
            org_doc['last_payment_at'] = datetime.fromisoformat(org_doc['last_payment_at'])
        
        return Organization(**org_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/organizations/{org_id}", response_model=Organization)
async def update_organization(org_id: str, updates: Dict[str, Any]):
    """Update organization details"""
    try:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.organizations.update_one(
            {"id": org_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Fetch and return updated organization
        org_doc = await db.organizations.find_one({"id": org_id}, {"_id": 0})
        
        # Convert ISO strings
        if isinstance(org_doc.get('created_at'), str):
            org_doc['created_at'] = datetime.fromisoformat(org_doc['created_at'])
        if isinstance(org_doc.get('updated_at'), str):
            org_doc['updated_at'] = datetime.fromisoformat(org_doc['updated_at'])
        if org_doc.get('trial_ends_at') and isinstance(org_doc['trial_ends_at'], str):
            org_doc['trial_ends_at'] = datetime.fromisoformat(org_doc['trial_ends_at'])
        if org_doc.get('last_payment_at') and isinstance(org_doc['last_payment_at'], str):
            org_doc['last_payment_at'] = datetime.fromisoformat(org_doc['last_payment_at'])
        
        return Organization(**org_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/organizations/{org_id}/users", response_model=List[User])
async def get_organization_users(org_id: str):
    """Get all users in an organization"""
    try:
        users = await db.users.find({"organization_id": org_id}, {"_id": 0}).to_list(1000)
        
        # Convert ISO strings
        for user in users:
            if isinstance(user.get('created_at'), str):
                user['created_at'] = datetime.fromisoformat(user['created_at'])
            if isinstance(user.get('updated_at'), str):
                user['updated_at'] = datetime.fromisoformat(user['updated_at'])
            if user.get('last_login_at') and isinstance(user['last_login_at'], str):
                user['last_login_at'] = datetime.fromisoformat(user['last_login_at'])
        
        return users
    except Exception as e:
        logger.error(f"Error fetching organization users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user"""
    try:
        user_dict = user.dict()
        user_dict["created_at"] = user_dict["created_at"].isoformat()
        user_dict["updated_at"] = user_dict["updated_at"].isoformat()
        if user_dict.get("last_login_at"):
            user_dict["last_login_at"] = user_dict["last_login_at"].isoformat()
        
        await db.users.insert_one(user_dict)
        logger.info(f"User created: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evv-credentials/{org_id}", response_model=EVVCredentials)
async def get_evv_credentials(org_id: str):
    """Get EVV credentials for an organization"""
    try:
        creds_doc = await db.evv_credentials.find_one({"organization_id": org_id}, {"_id": 0})
        if not creds_doc:
            raise HTTPException(status_code=404, detail="EVV credentials not found")
        
        # Convert ISO strings
        if isinstance(creds_doc.get('created_at'), str):
            creds_doc['created_at'] = datetime.fromisoformat(creds_doc['created_at'])
        if isinstance(creds_doc.get('updated_at'), str):
            creds_doc['updated_at'] = datetime.fromisoformat(creds_doc['updated_at'])
        
        return EVVCredentials(**creds_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching EVV credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/evv-credentials/{org_id}", response_model=EVVCredentials)
async def update_evv_credentials(org_id: str, creds: EVVCredentials):
    """Update EVV credentials for an organization"""
    try:
        creds_dict = creds.dict()
        creds_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        creds_dict["created_at"] = creds_dict["created_at"].isoformat()
        
        # Upsert (update or insert)
        result = await db.evv_credentials.update_one(
            {"organization_id": org_id},
            {"$set": creds_dict},
            upsert=True
        )
        
        logger.info(f"EVV credentials updated for org: {org_id}")
        return creds
    except Exception as e:
        logger.error(f"Error updating EVV credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Patient Profile Endpoints
@api_router.post("/patients", response_model=PatientProfile)
async def create_patient(patient: PatientProfile, organization_id: str = Depends(get_organization_id)):
    """Create a new patient profile"""
    try:
        # Ensure organization_id is set
        patient.organization_id = organization_id
        
        doc = patient.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.patients.insert_one(doc)
        logger.info(f"Patient created: {patient.id} for org: {organization_id}")
        
        return patient
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/patients", response_model=List[PatientProfile])
async def get_patients(
    search: Optional[str] = None,
    is_complete: Optional[bool] = None,
    limit: int = 1000,
    skip: int = 0,
    organization_id: str = Depends(get_organization_id)
):
    """Get all patient profiles with optional search and filters
    
    Args:
        search: Search by first name, last name, medicaid number, or date of birth (YYYY-MM-DD)
        is_complete: Filter by completion status (True/False)
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
    """
    query = {"organization_id": organization_id}  # Multi-tenant isolation
    
    # Add search filter
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"medicaid_number": {"$regex": search, "$options": "i"}},
            {"date_of_birth": {"$regex": search, "$options": "i"}}
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
async def get_patient(patient_id: str, organization_id: str = Depends(get_organization_id)):
    """Get specific patient by ID"""
    patient = await db.patients.find_one({"id": patient_id, "organization_id": organization_id}, {"_id": 0})
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Convert ISO string timestamps
    if isinstance(patient.get('created_at'), str):
        patient['created_at'] = datetime.fromisoformat(patient['created_at'])
    if isinstance(patient.get('updated_at'), str):
        patient['updated_at'] = datetime.fromisoformat(patient['updated_at'])
    
    return patient

@api_router.put("/patients/{patient_id}", response_model=PatientProfile)
async def update_patient(patient_id: str, patient_update: PatientProfileUpdate, organization_id: str = Depends(get_organization_id)):
    """Update patient profile and auto-sync with all related timesheets"""
    from validation_utils import validate_patient_required_fields
    
    # Get existing patient
    existing = await db.patients.find_one({"id": patient_id, "organization_id": organization_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Only update fields that are provided
    update_data = patient_update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Merge with existing data for validation
    merged_data = {**existing, **update_data}
    
    # Validate if is_complete is being set to True
    if update_data.get('is_complete') == True:
        is_valid, errors = validate_patient_required_fields(merged_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot mark profile complete. Required fields marked with (*) are missing.",
                    "missing_fields": errors,
                    "required_by": "Ohio Medicaid (ODM) and Electronic Visit Verification (EVV)"
                }
            )
    
    # Update in database
    result = await db.patients.update_one(
        {"id": patient_id, "organization_id": organization_id},
        {"$set": update_data}
    )
    
    # Get updated patient
    updated_patient = await db.patients.find_one({"id": patient_id, "organization_id": organization_id}, {"_id": 0})
    
    # AUTO-SYNC: Update all timesheets that reference this patient
    if update_data.get('first_name') or update_data.get('last_name') or update_data.get('medicaid_number'):
        full_name = f"{updated_patient.get('first_name', '')} {updated_patient.get('last_name', '')}".strip()
        
        # Find all timesheets with this patient
        timesheets_to_update = await db.timesheets.find({
            "organization_id": organization_id,
            "patient_id": patient_id
        }, {"_id": 0}).to_list(1000)
        
        # Update each timesheet's extracted_data with corrected patient info
        for timesheet in timesheets_to_update:
            if timesheet.get('extracted_data') and isinstance(timesheet['extracted_data'], dict):
                # Update client name
                if full_name:
                    timesheet['extracted_data']['client_name'] = full_name
                
                # Mark as auto-corrected
                if 'metadata' not in timesheet or not isinstance(timesheet.get('metadata'), dict):
                    timesheet['metadata'] = {}
                timesheet['metadata']['patient_auto_corrected'] = True
                timesheet['metadata']['patient_corrected_at'] = datetime.now(timezone.utc).isoformat()
                
                # Update the timesheet
                await db.timesheets.update_one(
                    {"id": timesheet['id']},
                    {"$set": {
                        "extracted_data": timesheet['extracted_data'],
                        "metadata": timesheet.get('metadata', {}),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        logger.info(f"Auto-synced {len(timesheets_to_update)} timesheets with updated patient info: {full_name}")
    
    return PatientProfile(**updated_patient)

@api_router.get("/patients/{patient_id}/completion-status")
async def get_patient_completion_status(patient_id: str, organization_id: str = Depends(get_organization_id)):
    """Get profile completion status for patient"""
    from validation_utils import get_profile_completion_status
    
    patient = await db.patients.find_one({"id": patient_id, "organization_id": organization_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    status = get_profile_completion_status('patient', patient)
    return status

@api_router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete a patient profile"""
    result = await db.patients.delete_one({"id": patient_id, "organization_id": organization_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {"message": "Patient deleted successfully"}

@api_router.get("/patients/{patient_id}/details")
async def get_patient_details(patient_id: str, organization_id: str = Depends(get_organization_id)):
    """Get patient details with timesheet history
    
    Returns:
        Patient profile with additional fields:
        - timesheets: List of all timesheets for this patient
        - total_visits: Total number of timesheets/visits
        - last_visit_date: Date of most recent visit
    """
    # Get patient
    patient = await db.patients.find_one({"id": patient_id, "organization_id": organization_id}, {"_id": 0})
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Convert ISO string timestamps for patient
    if isinstance(patient.get('created_at'), str):
        patient['created_at'] = datetime.fromisoformat(patient['created_at'])
    if isinstance(patient.get('updated_at'), str):
        patient['updated_at'] = datetime.fromisoformat(patient['updated_at'])
    
    # Get all timesheets for this patient
    timesheets = await db.timesheets.find(
        {"patient_id": patient_id, "organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Convert ISO string timestamps for timesheets
    for timesheet in timesheets:
        if isinstance(timesheet.get('created_at'), str):
            timesheet['created_at'] = datetime.fromisoformat(timesheet['created_at'])
        if isinstance(timesheet.get('updated_at'), str):
            timesheet['updated_at'] = datetime.fromisoformat(timesheet['updated_at'])
    
    # Calculate statistics
    total_visits = len(timesheets)
    last_visit_date = None
    if timesheets:
        # Get the most recent visit date from extracted_data
        for ts in timesheets:
            if ts.get('extracted_data') and ts['extracted_data'].get('date'):
                visit_date = ts['extracted_data']['date']
                if not last_visit_date or visit_date > last_visit_date:
                    last_visit_date = visit_date
    
    return {
        **patient,
        "timesheets": timesheets,
        "total_visits": total_visits,
        "last_visit_date": last_visit_date
    }


# Employee Profile Endpoints
@api_router.post("/employees", response_model=EmployeeProfile)
async def create_employee(employee: EmployeeProfile, organization_id: str = Depends(get_organization_id)):
    """Create a new employee profile"""
    try:
        # Ensure organization_id is set
        employee.organization_id = organization_id
        
        doc = employee.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.employees.insert_one(doc)
        logger.info(f"Employee created: {employee.id} for org: {organization_id}")
        
        return employee
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/employees", response_model=List[EmployeeProfile])
async def get_employees(
    search: Optional[str] = None,
    is_complete: Optional[bool] = None,
    limit: int = 1000,
    skip: int = 0,
    organization_id: str = Depends(get_organization_id)
):
    """Get all employee profiles with optional search and filters
    
    Args:
        search: Search by first name, last name, or employee ID
        is_complete: Filter by completion status (True/False)
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
    """
    query = {"organization_id": organization_id}
    
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


@api_router.get("/employees/similar/{name}")
async def get_similar_employees(name: str, organization_id: str = Depends(get_organization_id)):
    """
    Find employees with names similar to the given name.
    Useful for suggesting existing employees when scanning timesheets.
    
    Args:
        name: The name to search for (from timesheet scan)
    
    Returns:
        List of similar employees with similarity scores
    """
    similar = await find_similar_employees(name, organization_id, threshold=0.5)
    
    return {
        "search_name": name,
        "similar_employees": similar,
        "total_found": len(similar),
        "has_exact_match": any(e['similarity_score'] >= 0.95 for e in similar),
        "has_close_match": any(e['similarity_score'] >= 0.85 for e in similar)
    }


@api_router.post("/employees/link-to-existing")
async def link_scanned_employee_to_existing(
    scanned_employee_id: str,
    existing_employee_id: str,
    organization_id: str = Depends(get_organization_id)
):
    """
    Link a scanned/auto-created employee to an existing employee.
    This is used when a timesheet scan creates a new employee but
    there's actually an existing employee with a similar name.
    
    - Transfers any timesheet references from scanned to existing
    - Deletes the scanned (duplicate) employee
    
    Args:
        scanned_employee_id: ID of the auto-created employee to remove
        existing_employee_id: ID of the existing employee to link to
    """
    # Verify both employees exist
    scanned_emp = await db.employees.find_one(
        {"id": scanned_employee_id, "organization_id": organization_id},
        {"_id": 0}
    )
    if not scanned_emp:
        raise HTTPException(status_code=404, detail="Scanned employee not found")
    
    existing_emp = await db.employees.find_one(
        {"id": existing_employee_id, "organization_id": organization_id},
        {"_id": 0}
    )
    if not existing_emp:
        raise HTTPException(status_code=404, detail="Existing employee not found")
    
    # Update any timesheets that reference the scanned employee
    scanned_name = f"{scanned_emp.get('first_name', '')} {scanned_emp.get('last_name', '')}".strip()
    existing_name = f"{existing_emp.get('first_name', '')} {existing_emp.get('last_name', '')}".strip()
    
    # Find timesheets with the scanned employee in registration_results
    timesheets_updated = 0
    timesheets = await db.timesheets.find({
        "organization_id": organization_id,
        "registration_results.employees.id": scanned_employee_id
    }, {"_id": 0}).to_list(10000)
    
    for ts in timesheets:
        updated = False
        reg_results = ts.get('registration_results', {})
        
        # Update employee references
        if 'employees' in reg_results:
            for emp in reg_results['employees']:
                if emp.get('id') == scanned_employee_id:
                    emp['id'] = existing_employee_id
                    emp['first_name'] = existing_emp.get('first_name')
                    emp['last_name'] = existing_emp.get('last_name')
                    emp['linked_from'] = scanned_name
                    updated = True
        
        # Update extracted_data employee names
        if ts.get('extracted_data') and isinstance(ts['extracted_data'], dict):
            for entry in ts['extracted_data'].get('employee_entries', []):
                if isinstance(entry, dict):
                    emp_name = entry.get('employee_name', '').lower()
                    if scanned_name.lower() in emp_name or emp_name in scanned_name.lower():
                        entry['employee_name'] = existing_name
                        entry['linked_from_scanned'] = scanned_name
                        updated = True
        
        if updated:
            await db.timesheets.update_one(
                {"id": ts['id']},
                {"$set": {
                    "registration_results": reg_results,
                    "extracted_data": ts.get('extracted_data'),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            timesheets_updated += 1
    
    # Delete the scanned (duplicate) employee
    await db.employees.delete_one({"id": scanned_employee_id, "organization_id": organization_id})
    
    logger.info(f"Linked scanned employee '{scanned_name}' to existing '{existing_name}', updated {timesheets_updated} timesheets")
    
    return {
        "status": "success",
        "message": f"Linked '{scanned_name}' to existing employee '{existing_name}'",
        "scanned_employee_deleted": scanned_name,
        "linked_to": {
            "id": existing_employee_id,
            "name": existing_name
        },
        "timesheets_updated": timesheets_updated
    }


@api_router.post("/employees/name-corrections")
async def create_name_correction(
    incorrect_name: str,
    correct_name: str,
    apply_to_all: bool = True,
    organization_id: str = Depends(get_organization_id)
):
    """
    Create a name correction mapping and optionally apply it to all timesheets.
    
    This is useful when:
    - OCR consistently misreads a name
    - Names are written differently on various timesheets
    - You want to standardize name spelling across all records
    
    Args:
        incorrect_name: The misspelled/incorrect name to find
        correct_name: The correct name to replace it with
        apply_to_all: If True, immediately apply to all existing timesheets
    
    Returns:
        Summary of corrections applied
    """
    if not incorrect_name or not correct_name:
        raise HTTPException(status_code=400, detail="Both incorrect_name and correct_name are required")
    
    incorrect_name = incorrect_name.strip()
    correct_name = correct_name.strip()
    
    if incorrect_name.lower() == correct_name.lower():
        raise HTTPException(status_code=400, detail="Incorrect and correct names cannot be the same")
    
    # Store the correction mapping for future use
    correction_doc = {
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "incorrect_name": incorrect_name,
        "correct_name": correct_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "times_applied": 0
    }
    
    # Check if this correction already exists
    existing = await db.name_corrections.find_one({
        "organization_id": organization_id,
        "incorrect_name": {"$regex": f"^{incorrect_name}$", "$options": "i"}
    })
    
    if existing:
        # Update existing correction
        await db.name_corrections.update_one(
            {"id": existing["id"]},
            {"$set": {"correct_name": correct_name, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        correction_id = existing["id"]
    else:
        await db.name_corrections.insert_one(correction_doc)
        correction_id = correction_doc["id"]
    
    timesheets_updated = 0
    entries_corrected = 0
    
    if apply_to_all:
        # Apply correction to all timesheets
        timesheets_updated, entries_corrected = await apply_name_correction_to_timesheets(
            incorrect_name, correct_name, organization_id
        )
    
    logger.info(f"Name correction created: '{incorrect_name}' → '{correct_name}', applied to {timesheets_updated} timesheets")
    
    return {
        "status": "success",
        "correction_id": correction_id,
        "incorrect_name": incorrect_name,
        "correct_name": correct_name,
        "applied_to_all": apply_to_all,
        "timesheets_updated": timesheets_updated,
        "entries_corrected": entries_corrected,
        "message": f"Name correction saved. Updated {entries_corrected} entries across {timesheets_updated} timesheets."
    }


async def apply_name_correction_to_timesheets(
    incorrect_name: str, 
    correct_name: str, 
    organization_id: str
) -> Tuple[int, int]:
    """
    Apply a name correction to all timesheets in an organization.
    
    Returns:
        Tuple of (timesheets_updated, entries_corrected)
    """
    timesheets_updated = 0
    entries_corrected = 0
    
    # Find all timesheets for this organization
    timesheets = await db.timesheets.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).to_list(10000)
    
    incorrect_lower = incorrect_name.lower()
    
    for ts in timesheets:
        updated = False
        extracted = ts.get('extracted_data', {})
        
        if not isinstance(extracted, dict):
            continue
        
        # Check and update employee entries
        employee_entries = extracted.get('employee_entries', [])
        for emp in employee_entries:
            if isinstance(emp, dict):
                emp_name = emp.get('employee_name', '')
                if emp_name and emp_name.lower() == incorrect_lower:
                    emp['employee_name'] = correct_name
                    emp['name_corrected_from'] = emp_name
                    emp['name_corrected_at'] = datetime.now(timezone.utc).isoformat()
                    entries_corrected += 1
                    updated = True
        
        # Also check registration_results
        reg_results = ts.get('registration_results', {})
        if isinstance(reg_results, dict):
            for emp in reg_results.get('employees', []):
                if isinstance(emp, dict):
                    emp_first = emp.get('first_name', '')
                    emp_last = emp.get('last_name', '')
                    full_name = f"{emp_first} {emp_last}".strip()
                    if full_name.lower() == incorrect_lower:
                        # Parse correct name
                        parts = correct_name.split()
                        if len(parts) >= 2:
                            emp['first_name'] = parts[0]
                            emp['last_name'] = ' '.join(parts[1:])
                        else:
                            emp['last_name'] = correct_name
                        emp['name_corrected_from'] = full_name
                        updated = True
        
        if updated:
            await db.timesheets.update_one(
                {"id": ts['id']},
                {"$set": {
                    "extracted_data": extracted,
                    "registration_results": reg_results,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            timesheets_updated += 1
    
    # Update the correction count
    await db.name_corrections.update_one(
        {"organization_id": organization_id, "incorrect_name": {"$regex": f"^{incorrect_name}$", "$options": "i"}},
        {"$inc": {"times_applied": entries_corrected}}
    )
    
    return timesheets_updated, entries_corrected


@api_router.get("/employees/name-corrections")
async def get_name_corrections(organization_id: str = Depends(get_organization_id)):
    """
    Get all saved name corrections for the organization.
    """
    corrections = await db.name_corrections.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return {
        "corrections": corrections,
        "total": len(corrections)
    }


@api_router.post("/employees/name-corrections/apply-all")
async def apply_all_name_corrections(organization_id: str = Depends(get_organization_id)):
    """
    Apply all saved name corrections to all timesheets.
    Useful after bulk imports or when corrections were saved but not applied.
    """
    corrections = await db.name_corrections.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not corrections:
        return {
            "status": "no_corrections",
            "message": "No name corrections found"
        }
    
    total_timesheets = 0
    total_entries = 0
    
    for corr in corrections:
        ts_updated, entries_corrected = await apply_name_correction_to_timesheets(
            corr['incorrect_name'],
            corr['correct_name'],
            organization_id
        )
        total_timesheets += ts_updated
        total_entries += entries_corrected
    
    return {
        "status": "success",
        "corrections_applied": len(corrections),
        "timesheets_updated": total_timesheets,
        "entries_corrected": total_entries,
        "message": f"Applied {len(corrections)} corrections to {total_entries} entries across {total_timesheets} timesheets"
    }


@api_router.delete("/employees/name-corrections/{correction_id}")
async def delete_name_correction(correction_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete a name correction mapping"""
    result = await db.name_corrections.delete_one({
        "id": correction_id,
        "organization_id": organization_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Name correction not found")
    
    return {"message": "Name correction deleted"}


@api_router.get("/employees/duplicates/find")
async def find_duplicate_employees(organization_id: str = Depends(get_organization_id)):
    """
    Find employees with similar/duplicate names.
    Returns groups of potential duplicates with suggestions on which to keep.
    Suggests keeping the most recently updated record.
    """
    # Get all employees for this organization
    employees = await db.employees.find(
        {"organization_id": organization_id}, 
        {"_id": 0}
    ).to_list(10000)
    
    # Normalize name for comparison (lowercase, strip whitespace)
    def normalize_name(first_name, last_name):
        first = (first_name or "").strip().lower()
        last = (last_name or "").strip().lower()
        return f"{first} {last}"
    
    # Group employees by normalized name
    name_groups = {}
    for emp in employees:
        normalized = normalize_name(emp.get('first_name'), emp.get('last_name'))
        if normalized not in name_groups:
            name_groups[normalized] = []
        name_groups[normalized].append(emp)
    
    # Find groups with duplicates (more than one employee with same name)
    duplicate_groups = []
    for normalized_name, group in name_groups.items():
        if len(group) > 1:
            # Sort by updated_at descending (most recent first)
            sorted_group = sorted(
                group, 
                key=lambda x: x.get('updated_at', '1900-01-01') if isinstance(x.get('updated_at'), str) else x.get('updated_at', datetime.min).isoformat(),
                reverse=True
            )
            
            # The first one (most recently updated) is suggested to keep
            suggested_keep = sorted_group[0]
            suggested_delete = sorted_group[1:]
            
            duplicate_groups.append({
                "normalized_name": normalized_name,
                "display_name": f"{sorted_group[0].get('first_name', '')} {sorted_group[0].get('last_name', '')}",
                "total_duplicates": len(group),
                "suggested_keep": {
                    "id": suggested_keep.get('id'),
                    "first_name": suggested_keep.get('first_name'),
                    "last_name": suggested_keep.get('last_name'),
                    "email": suggested_keep.get('email'),
                    "phone": suggested_keep.get('phone'),
                    "categories": suggested_keep.get('categories', []),
                    "is_complete": suggested_keep.get('is_complete', False),
                    "updated_at": suggested_keep.get('updated_at'),
                    "reason": "Most recently updated"
                },
                "suggested_delete": [
                    {
                        "id": emp.get('id'),
                        "first_name": emp.get('first_name'),
                        "last_name": emp.get('last_name'),
                        "email": emp.get('email'),
                        "phone": emp.get('phone'),
                        "categories": emp.get('categories', []),
                        "is_complete": emp.get('is_complete', False),
                        "updated_at": emp.get('updated_at'),
                        "reason": "Older record"
                    }
                    for emp in suggested_delete
                ]
            })
    
    # Sort by number of duplicates (most duplicates first)
    duplicate_groups.sort(key=lambda x: x['total_duplicates'], reverse=True)
    
    return {
        "total_duplicate_groups": len(duplicate_groups),
        "total_duplicate_records": sum(g['total_duplicates'] - 1 for g in duplicate_groups),
        "duplicate_groups": duplicate_groups
    }


@api_router.post("/employees/duplicates/resolve")
async def resolve_duplicate_employees(
    keep_id: str,
    delete_ids: List[str],
    organization_id: str = Depends(get_organization_id)
):
    """
    Resolve duplicate employees by keeping one and deleting others.
    
    Args:
        keep_id: ID of the employee to keep
        delete_ids: List of employee IDs to delete
    """
    # Verify the employee to keep exists
    keep_employee = await db.employees.find_one(
        {"id": keep_id, "organization_id": organization_id},
        {"_id": 0}
    )
    if not keep_employee:
        raise HTTPException(status_code=404, detail="Employee to keep not found")
    
    # Verify all employees to delete exist and belong to organization
    deleted_count = 0
    deleted_names = []
    
    for delete_id in delete_ids:
        employee = await db.employees.find_one(
            {"id": delete_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if employee:
            # Delete the duplicate
            result = await db.employees.delete_one(
                {"id": delete_id, "organization_id": organization_id}
            )
            if result.deleted_count > 0:
                deleted_count += 1
                deleted_names.append(f"{employee.get('first_name', '')} {employee.get('last_name', '')}")
                logger.info(f"Deleted duplicate employee: {delete_id} ({employee.get('first_name')} {employee.get('last_name')})")
    
    return {
        "status": "success",
        "kept_employee": {
            "id": keep_employee.get('id'),
            "name": f"{keep_employee.get('first_name', '')} {keep_employee.get('last_name', '')}"
        },
        "deleted_count": deleted_count,
        "deleted_names": deleted_names,
        "message": f"Kept 1 employee, deleted {deleted_count} duplicate(s)"
    }


@api_router.get("/employees/{employee_id}", response_model=EmployeeProfile)
async def get_employee(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Get specific employee by ID"""
    employee = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Convert ISO string timestamps
    if isinstance(employee.get('created_at'), str):
        employee['created_at'] = datetime.fromisoformat(employee['created_at'])
    if isinstance(employee.get('updated_at'), str):
        employee['updated_at'] = datetime.fromisoformat(employee['updated_at'])
    
    return employee

@api_router.put("/employees/{employee_id}", response_model=EmployeeProfile)
async def update_employee(employee_id: str, employee_update: EmployeeProfileUpdate, organization_id: str = Depends(get_organization_id)):
    """Update employee profile and auto-sync with all related timesheets"""
    from validation_utils import validate_employee_required_fields
    
    # Get existing employee
    existing = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Only update fields that are provided
    update_data = employee_update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Merge with existing data for validation
    merged_data = {**existing, **update_data}
    
    # Validate if is_complete is being set to True
    if update_data.get('is_complete') == True:
        is_valid, errors = validate_employee_required_fields(merged_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot mark profile complete. Required fields marked with (*) are missing.",
                    "missing_fields": errors,
                    "required_by": "Ohio Medicaid (ODM) and Electronic Visit Verification (EVV)"
                }
            )
    
    # Update in database
    result = await db.employees.update_one(
        {"id": employee_id, "organization_id": organization_id},
        {"$set": update_data}
    )
    
    # Get updated employee
    updated_employee = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    
    # AUTO-SYNC: Update all timesheets that reference this employee
    if update_data.get('first_name') or update_data.get('last_name'):
        full_name = f"{updated_employee.get('first_name', '')} {updated_employee.get('last_name', '')}".strip()
        
        # Find all timesheets with this employee in extracted_data
        timesheets_to_update = await db.timesheets.find({
            "organization_id": organization_id,
            "registration_results.employees.id": employee_id
        }, {"_id": 0}).to_list(1000)
        
        # Update each timesheet's extracted_data with corrected employee name
        for timesheet in timesheets_to_update:
            if timesheet.get('extracted_data') and isinstance(timesheet['extracted_data'], dict):
                employee_entries = timesheet['extracted_data'].get('employee_entries', [])
                for entry in employee_entries:
                    # Match by employee ID stored in registration results
                    if isinstance(entry, dict):
                        entry['employee_name'] = full_name
                        # Mark as auto-corrected
                        entry['auto_corrected'] = True
                        entry['corrected_at'] = datetime.now(timezone.utc).isoformat()
                
                # Update the timesheet
                await db.timesheets.update_one(
                    {"id": timesheet['id']},
                    {"$set": {
                        "extracted_data": timesheet['extracted_data'],
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        logger.info(f"Auto-synced {len(timesheets_to_update)} timesheets with updated employee name: {full_name}")
    
    return EmployeeProfile(**updated_employee)

@api_router.get("/employees/{employee_id}/completion-status")
async def get_employee_completion_status(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Get profile completion status for employee"""
    from validation_utils import get_profile_completion_status
    
    employee = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    status = get_profile_completion_status('employee', employee)
    return status

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete an employee profile"""
    result = await db.employees.delete_one({"id": employee_id, "organization_id": organization_id})
    
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
async def create_contract(contract: InsuranceContract, organization_id: str = Depends(get_organization_id)):
    """Create a new insurance contract"""
    try:
        # Ensure organization_id is set from JWT token
        contract.organization_id = organization_id
        
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
async def get_contracts(organization_id: str = Depends(get_organization_id)):
    """Get all insurance contracts"""
    contracts = await db.insurance_contracts.find({"organization_id": organization_id}, {"_id": 0}).sort("payer_name", 1).to_list(1000)
    
    # Convert ISO string timestamps
    for contract in contracts:
        if isinstance(contract.get('created_at'), str):
            contract['created_at'] = datetime.fromisoformat(contract['created_at'])
        if isinstance(contract.get('updated_at'), str):
            contract['updated_at'] = datetime.fromisoformat(contract['updated_at'])
    
    return contracts

@api_router.get("/insurance-contracts/{contract_id}", response_model=InsuranceContract)
async def get_contract(contract_id: str, organization_id: str = Depends(get_organization_id)):
    """Get specific contract by ID"""
    contract = await db.insurance_contracts.find_one({"id": contract_id, "organization_id": organization_id}, {"_id": 0})
    
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
async def create_claim(claim: MedicaidClaim, organization_id: str = Depends(get_organization_id)):
    """Create a new Medicaid claim"""
    try:
        # Ensure organization_id is set
        claim.organization_id = organization_id
        
        # Auto-generate claim number if not provided
        if not claim.claim_number:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            claim.claim_number = f"ODM-{timestamp}"
        
        doc = claim.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.claims.insert_one(doc)
        logger.info(f"Claim created: {claim.id} for org: {organization_id}")
        
        return claim
    except Exception as e:
        logger.error(f"Error creating claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/claims", response_model=List[MedicaidClaim])
async def get_claims(organization_id: str = Depends(get_organization_id)):
    """Get all claims"""
    claims = await db.claims.find({"organization_id": organization_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Convert ISO string timestamps
    for claim in claims:
        if isinstance(claim.get('created_at'), str):
            claim['created_at'] = datetime.fromisoformat(claim['created_at'])
        if isinstance(claim.get('updated_at'), str):
            claim['updated_at'] = datetime.fromisoformat(claim['updated_at'])
    
    return claims

@api_router.get("/claims/medicaid/{claim_id}", response_model=MedicaidClaim)
async def get_claim(claim_id: str, organization_id: str = Depends(get_organization_id)):
    """Get specific claim by ID"""
    claim = await db.claims.find_one({"id": claim_id, "organization_id": organization_id}, {"_id": 0})
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Convert ISO string timestamps
    if isinstance(claim.get('created_at'), str):
        claim['created_at'] = datetime.fromisoformat(claim['created_at'])
    if isinstance(claim.get('updated_at'), str):
        claim['updated_at'] = datetime.fromisoformat(claim['updated_at'])
    
    return claim

@api_router.put("/claims/medicaid/{claim_id}", response_model=MedicaidClaim)
async def update_claim(claim_id: str, claim_update: MedicaidClaim, organization_id: str = Depends(get_organization_id)):
    """Update claim"""
    claim_update.id = claim_id
    claim_update.organization_id = organization_id
    claim_update.updated_at = datetime.now(timezone.utc)
    
    doc = claim_update.model_dump()
    doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    result = await db.claims.update_one(
        {"id": claim_id, "organization_id": organization_id},
        {"$set": doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return claim_update

@api_router.post("/claims/medicaid/{claim_id}/submit")
async def submit_claim(claim_id: str, organization_id: str = Depends(get_organization_id)):
    """
    Submit claim to Ohio Medicaid portal
    
    ⚠️ MOCKED IMPLEMENTATION
    This endpoint simulates Ohio Medicaid claim submission for testing purposes.
    Real implementation requires:
    - Ohio Medicaid portal credentials
    - MITS (Medicaid Information Technology System) access
    - EDI 837 format compliance
    - Trading partner agreement
    - See: https://medicaid.ohio.gov/providers-partners/providers/billing-and-claims
    """
    try:
        claim = await db.claims.find_one({"id": claim_id, "organization_id": organization_id}, {"_id": 0})
        
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

@api_router.delete("/claims/medicaid/{claim_id}")
async def delete_claim(claim_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete a claim"""
    result = await db.claims.delete_one({"id": claim_id, "organization_id": organization_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {"message": "Claim deleted successfully"}

@api_router.post("/claims/bulk-submit")
async def bulk_submit_claims(request: Dict, organization_id: str = Depends(get_organization_id)):
    """
    Submit multiple claims to Ohio Medicaid in bulk
    
    ⚠️ MOCKED IMPLEMENTATION
    This endpoint simulates bulk claim submission to Ohio Medicaid for testing.
    Real implementation requires same credentials as single submission.
    
    Request body: {"claim_ids": ["id1", "id2", "id3"]}
    """
    try:
        claim_ids = request.get("claim_ids", [])
        
        if not claim_ids:
            raise HTTPException(status_code=400, detail="No claim IDs provided")
        
        # Fetch all claims
        claims = await db.claims.find({
            "id": {"$in": claim_ids},
            "organization_id": organization_id
        }, {"_id": 0}).to_list(1000)
        
        if not claims:
            raise HTTPException(status_code=404, detail="No claims found")
        
        # Mock bulk submission
        submission_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        submitted_claims = []
        
        for claim in claims:
            # Skip already submitted claims
            if claim.get('status') == 'submitted':
                continue
            
            logger.info(f"[MOCK BULK] Submitting claim: {claim['claim_number']}")
            logger.info(f"  Patient: {claim['patient_name']} (Medicaid: {claim['patient_medicaid_number']})")
            logger.info(f"  Total: ${claim['total_amount']:.2f}, Units: {claim['total_units']}")
            
            # Update claim status
            await db.claims.update_one(
                {"id": claim['id']},
                {"$set": {
                    "status": "submitted",
                    "submission_date": submission_date,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            submitted_claims.append({
                "claim_id": claim['id'],
                "claim_number": claim['claim_number'],
                "reference_id": f"REF-{claim['id'][:8].upper()}"
            })
        
        return {
            "status": "success",
            "message": f"{len(submitted_claims)} claims submitted successfully (MOCKED)",
            "submission_date": submission_date,
            "submitted_claims": submitted_claims,
            "skipped_count": len(claims) - len(submitted_claims)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk claim submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# EVV (Electronic Visit Verification) Endpoints
# ========================================

from evv_export import EVVExportOrchestrator
from evv_submission import EVVSubmissionService
from evv_submission_coordinator import EVVSubmissionCoordinator
from evv_aggregator_factory import get_default_evv_client

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
async def submit_individuals(current_user: Dict = Depends(get_current_user)):
    """Submit Individual/Patient records to EVV Aggregator (REAL IMPLEMENTATION)"""
    try:
        organization_id = current_user["organization_id"]
        
        # Initialize coordinator with real EVV client
        coordinator = EVVSubmissionCoordinator(db)
        
        # Submit all patients for organization
        result = await coordinator.submit_patients_to_evv(organization_id)
        
        return {
            "success": result.success,
            "transaction_id": result.transaction_id,
            "message": result.message,
            "errors": result.errors,
            "vendor": coordinator.evv_client.get_vendor_name()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting individuals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/evv/submit/direct-care-workers")
async def submit_direct_care_workers(current_user: Dict = Depends(get_current_user)):
    """Submit DirectCareWorker/Employee records to EVV Aggregator (REAL IMPLEMENTATION)"""
    try:
        organization_id = current_user["organization_id"]
        
        # Initialize coordinator with real EVV client
        coordinator = EVVSubmissionCoordinator(db)
        
        # Submit all employees for organization
        result = await coordinator.submit_employees_to_evv(organization_id)
        
        return {
            "success": result.success,
            "transaction_id": result.transaction_id,
            "message": result.message,
            "errors": result.errors,
            "vendor": coordinator.evv_client.get_vendor_name()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting DCWs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/evv/submit/visits")
async def submit_visits(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Submit Visit records from timesheets to EVV Aggregator (REAL IMPLEMENTATION)"""
    try:
        organization_id = current_user["organization_id"]
        timesheet_ids = request.get('timesheet_ids', [])
        
        if not timesheet_ids:
            raise HTTPException(status_code=400, detail="timesheet_ids required")
        
        # Initialize coordinator with real EVV client
        coordinator = EVVSubmissionCoordinator(db)
        
        # Submit timesheets to EVV
        result = await coordinator.submit_batch_to_evv(timesheet_ids, organization_id)
        
        return {
            "success": result['success_count'] > 0,
            "total": result['total'],
            "successful": result['successful'],
            "failed": result['failed'],
            "success_count": result['success_count'],
            "failure_count": result['failure_count'],
            "message": f"Submitted {result['success_count']} of {result['total']} timesheets to EVV"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting visits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/evv/verify-before-claim")
async def verify_evv_before_claim(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Verify all timesheets have EVV records before generating 837P claim"""
    try:
        organization_id = current_user["organization_id"]
        timesheet_ids = request.get('timesheet_ids', [])
        
        if not timesheet_ids:
            raise HTTPException(status_code=400, detail="timesheet_ids required")
        
        coordinator = EVVSubmissionCoordinator(db)
        result = await coordinator.verify_evv_before_claim(timesheet_ids, organization_id)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying EVV: {e}")
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
async def create_service_code(service_code: ServiceCodeConfig, organization_id: str = Depends(get_organization_id)):
    """Create a new service code configuration"""
    try:
        # Ensure organization_id is set
        service_code.organization_id = organization_id
        
        doc = service_code.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await db.service_codes.insert_one(doc)
        logger.info(f"Service code created: {service_code.id} for org: {organization_id}")
        
        return service_code
    except Exception as e:
        logger.error(f"Error creating service code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/service-codes", response_model=List[ServiceCodeConfig])
async def get_service_codes(active_only: bool = False, organization_id: str = Depends(get_organization_id)):
    """Get all service code configurations"""
    query = {"organization_id": organization_id}
    if active_only:
        query["is_active"] = True
    
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


# =============================================================================
# BILLING CODES CONFIGURATION (Toggle-based like RhinoBill)
# =============================================================================

class BillingCodeItem(BaseModel):
    """Individual billing code with toggle state"""
    code: str  # HCPCS code (e.g., G0151, T1019)
    description: str  # Human-readable description
    category: str  # Category for grouping
    modifier: Optional[str] = None  # Optional modifier (LPN, RN, etc.)
    enabled: bool = True  # Toggle state

class BillingCodesConfig(BaseModel):
    """Complete billing codes configuration"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    codes: List[BillingCodeItem] = []
    era_enabled: bool = True  # Enable ERAs via RhinoBill
    using_other_service: bool = False  # Currently using another billing service
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@api_router.get("/billing-codes/config")
async def get_billing_codes_config(organization_id: str = Depends(get_organization_id)):
    """Get the organization's billing codes configuration"""
    config = await db.billing_codes_config.find_one(
        {"organization_id": organization_id}, 
        {"_id": 0}
    )
    
    if not config:
        # Return empty config if none exists
        return {
            "codes": [],
            "era_enabled": True,
            "using_other_service": False
        }
    
    return config


@api_router.post("/billing-codes/config")
async def save_billing_codes_config(
    config: BillingCodesConfig,
    organization_id: str = Depends(get_organization_id)
):
    """Save the organization's billing codes configuration"""
    config.organization_id = organization_id
    config.updated_at = datetime.now(timezone.utc)
    
    # Convert to dict for MongoDB
    doc = config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    # Upsert - update if exists, insert if not
    result = await db.billing_codes_config.update_one(
        {"organization_id": organization_id},
        {"$set": doc},
        upsert=True
    )
    
    logger.info(f"Billing codes config saved for org: {organization_id}, codes: {len(config.codes)}")
    
    return {
        "success": True,
        "message": "Billing codes configuration saved successfully",
        "codes_count": len(config.codes),
        "enabled_count": len([c for c in config.codes if c.enabled])
    }


@api_router.get("/billing-codes/enabled")
async def get_enabled_billing_codes(organization_id: str = Depends(get_organization_id)):
    """Get only the enabled billing codes for claims submission"""
    config = await db.billing_codes_config.find_one(
        {"organization_id": organization_id}, 
        {"_id": 0}
    )
    
    if not config or not config.get("codes"):
        # Return default enabled codes if no config
        return {
            "enabled_codes": [
                {"code": "T1019", "description": "Personal Care Aide"},
                {"code": "T1020", "description": "Personal Care Services"},
                {"code": "T1021", "description": "Home Health Aide per visit"},
                {"code": "G0151", "description": "Physical Therapy"},
                {"code": "G0152", "description": "Occupational Therapy"},
                {"code": "G0153", "description": "Speech Therapy"},
            ]
        }
    
    enabled_codes = [
        {"code": c["code"], "description": c["description"], "modifier": c.get("modifier")}
        for c in config["codes"] 
        if c.get("enabled", True)
    ]
    
    return {"enabled_codes": enabled_codes}


@api_router.post("/billing-codes/toggle/{code}")
async def toggle_billing_code(
    code: str,
    enabled: bool,
    organization_id: str = Depends(get_organization_id)
):
    """Quick toggle a single billing code on/off"""
    result = await db.billing_codes_config.update_one(
        {"organization_id": organization_id, "codes.code": code},
        {"$set": {"codes.$.enabled": enabled, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Billing code not found in configuration")
    
    return {"success": True, "code": code, "enabled": enabled}


# Payment & Subscription Endpoints

class CheckoutRequest(BaseModel):
    """Request to create checkout session"""
    plan: str  # "basic" or "professional"

@api_router.post("/payments/create-checkout")
async def create_checkout(
    request: CheckoutRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a Stripe checkout session for subscription upgrade
    """
    try:
        organization_id = current_user["organization_id"]
        
        # Get organization details
        org = await db.organizations.find_one({"id": organization_id}, {"_id": 0})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Create checkout session
        # Get app URL from environment (for payment redirects)
        app_url = os.environ.get("APP_URL", "https://healthcare-tracking.preview.emergentagent.com")
        
        session = create_checkout_session(
            organization_id=organization_id,
            plan=request.plan,
            success_url=f"{app_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{app_url}/payment/cancelled",
            customer_email=current_user["email"]
        )
        
        return session
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/payments/create-portal")
async def create_portal(current_user: Dict = Depends(get_current_user)):
    """
    Create a Stripe billing portal session
    """
    try:
        organization_id = current_user["organization_id"]
        
        # Get organization
        org = await db.organizations.find_one({"id": organization_id}, {"_id": 0})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if not org.get("stripe_customer_id"):
            raise HTTPException(status_code=400, detail="No active subscription")
        
        # Get app URL from environment (for billing portal return)
        app_url = os.environ.get("APP_URL", "https://healthcare-tracking.preview.emergentagent.com")
        
        # Create billing portal session
        session = create_billing_portal_session(
            customer_id=org["stripe_customer_id"],
            return_url=f"{app_url}/"
        )
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Billing portal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/payments/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks for subscription events
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        event = verify_webhook_signature(payload, sig_header)
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            organization_id = session['metadata']['organization_id']
            plan = session['metadata']['plan']
            customer_id = session['customer']
            subscription_id = session['subscription']
            
            # Update organization
            plan_limits = get_plan_limits(plan)
            plan_features = get_plan_features(plan)
            
            await db.organizations.update_one(
                {"id": organization_id},
                {"$set": {
                    "plan": plan,
                    "subscription_status": "active",
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                    "features": plan_features,
                    "max_timesheets": plan_limits["max_timesheets"],
                    "max_employees": plan_limits["max_employees"],
                    "max_patients": plan_limits["max_patients"],
                    "last_payment_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            logger.info(f"Subscription activated for org: {organization_id}, plan: {plan}")
        
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            customer_id = subscription['customer']
            status = subscription['status']
            
            # Update subscription status
            await db.organizations.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {
                    "subscription_status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            logger.info(f"Subscription updated for customer: {customer_id}, status: {status}")
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            customer_id = subscription['customer']
            
            # Downgrade to trial/basic
            await db.organizations.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {
                    "subscription_status": "cancelled",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            logger.info(f"Subscription cancelled for customer: {customer_id}")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/payments/plans")
async def get_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": "basic",
                "name": "Basic Plan",
                "price": 49,
                "interval": "month",
                "features": PLANS["basic"]["features"],
                "limits": PLANS["basic"]["limits"]
            },
            {
                "id": "professional",
                "name": "Professional Plan",
                "price": 149,
                "interval": "month",
                "features": PLANS["professional"]["features"],
                "limits": PLANS["professional"]["limits"]
            },
            {
                "id": "enterprise",
                "name": "Enterprise Plan",
                "price": "Custom",
                "interval": "month",
                "features": PLANS["enterprise"]["features"],
                "limits": PLANS["enterprise"]["limits"]
            }
        ]
    }

# Authentication Endpoints

class SignupRequest(BaseModel):
    """Signup request model"""
    email: str
    password: str
    first_name: str
    last_name: str
    organization_name: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str

class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    organization: Dict[str, Any]

@api_router.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Sign up a new user and create their organization.
    This creates:
    1. A new organization (on free trial)
    2. A new user as the owner
    3. Returns JWT token
    """
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": request.email}, {"_id": 0})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create organization
        org = Organization(
            name=request.organization_name,
            plan="basic",
            subscription_status="trial",
            admin_email=request.email,
            admin_name=f"{request.first_name} {request.last_name}",
            phone=request.phone,
            max_timesheets=100,
            max_employees=5,
            max_patients=10,
            features=["sandata_submission"],
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14)  # 14-day trial
        )
        
        org_dict = org.dict()
        org_dict["created_at"] = org_dict["created_at"].isoformat()
        org_dict["updated_at"] = org_dict["updated_at"].isoformat()
        if org_dict.get("trial_ends_at"):
            org_dict["trial_ends_at"] = org_dict["trial_ends_at"].isoformat()
        
        await db.organizations.insert_one(org_dict)
        logger.info(f"Organization created: {org.id} - {org.name}")
        
        # Create user
        user = User(
            email=request.email,
            organization_id=org.id,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            role="owner"
        )
        
        user_dict = user.dict()
        # Hash password and store separately
        user_dict["password_hash"] = hash_password(request.password)
        user_dict["created_at"] = user_dict["created_at"].isoformat()
        user_dict["updated_at"] = user_dict["updated_at"].isoformat()
        
        await db.users.insert_one(user_dict)
        logger.info(f"User created: {user.id} - {user.email}")
        
        # Create access token
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            organization_id=org.id,
            role=user.role,
            is_admin=False
        )
        
        # Return response
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "organization_id": org.id
            },
            organization={
                "id": org.id,
                "name": org.name,
                "plan": org.plan,
                "subscription_status": org.subscription_status,
                "features": org.features
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login with email and password.
    Returns JWT token.
    """
    try:
        # Find user
        user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(request.password, user_doc["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is disabled")
        
        # Get organization
        org_doc = await db.organizations.find_one({"id": user_doc["organization_id"]}, {"_id": 0})
        if not org_doc:
            raise HTTPException(status_code=500, detail="Organization not found")
        
        # Update last login
        await db.users.update_one(
            {"id": user_doc["id"]},
            {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create access token
        access_token = create_access_token(
            user_id=user_doc["id"],
            email=user_doc["email"],
            organization_id=user_doc["organization_id"],
            role=user_doc["role"],
            is_admin=user_doc.get("is_admin", False)
        )
        
        # Return response
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user_doc["id"],
                "email": user_doc["email"],
                "first_name": user_doc["first_name"],
                "last_name": user_doc["last_name"],
                "role": user_doc["role"],
                "organization_id": user_doc["organization_id"]
            },
            organization={
                "id": org_doc["id"],
                "name": org_doc["name"],
                "plan": org_doc["plan"],
                "subscription_status": org_doc["subscription_status"],
                "features": org_doc.get("features", [])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Requires valid JWT token.
    """
    try:
        # Get full user details
        user_doc = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get organization
        org_doc = await db.organizations.find_one({"id": current_user["organization_id"]}, {"_id": 0})
        
        return {
            "user": user_doc,
            "organization": org_doc
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Ohio Medicaid 837P Claims Endpoints
# ========================================

from edi_claim_generator import ClaimGenerator

# Models for 837P claim generation
class Generate837ClaimRequest(BaseModel):
    """Request to generate 837P claim from timesheets"""
    timesheet_ids: List[str] = Field(..., description="List of timesheet IDs to include in claim")
    
class Generate837BulkRequest(BaseModel):
    """Request to generate multiple 837P claims"""
    claims: List[Dict[str, Any]] = Field(..., description="List of claim data dictionaries")

class ODMEnrollmentStep(BaseModel):
    """ODM enrollment checklist step"""
    step_number: int
    step_name: str
    description: str
    completed: bool = False
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None

class ODMEnrollmentStatus(BaseModel):
    """Track ODM trading partner enrollment progress"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    trading_partner_id: Optional[str] = None  # 7-digit ODM ID when assigned
    enrollment_status: str = "not_started"  # not_started, in_progress, testing, approved
    steps: List[ODMEnrollmentStep] = []
    documents: List[Dict[str, str]] = []  # Document references
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@api_router.post("/claims/generate-837")
async def generate_837_claim(
    request: Generate837ClaimRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate X12 837P claim file from selected timesheets.
    
    This creates a HIPAA 5010-compliant 837 Professional claim file
    that can be submitted to Ohio Medicaid after trading partner enrollment.
    """
    try:
        organization_id = current_user["organization_id"]
        
        # Fetch timesheets
        timesheets = []
        for timesheet_id in request.timesheet_ids:
            ts = await db.timesheets.find_one({
                "id": timesheet_id,
                "organization_id": organization_id
            }, {"_id": 0})
            
            if not ts:
                raise HTTPException(status_code=404, detail=f"Timesheet {timesheet_id} not found")
            
            timesheets.append(ts)
        
        if not timesheets:
            raise HTTPException(status_code=400, detail="No timesheets found")
        
        # Group timesheets by patient for claim generation
        claims_by_patient = {}
        for ts in timesheets:
            patient_id = ts.get('patient_id')
            if not patient_id:
                continue
            
            if patient_id not in claims_by_patient:
                claims_by_patient[patient_id] = []
            
            claims_by_patient[patient_id].append(ts)
        
        # Generate 837P file for the first patient (for now)
        # In production, you might want to handle multiple patients differently
        if not claims_by_patient:
            raise HTTPException(status_code=400, detail="No valid timesheets with patient information")
        
        # Take first patient's timesheets
        patient_id = list(claims_by_patient.keys())[0]
        patient_timesheets = claims_by_patient[patient_id]
        
        # Fetch patient information
        patient = await db.patients.find_one({
            "id": patient_id,
            "organization_id": organization_id
        }, {"_id": 0})
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Fetch business entity configuration for sender ID
        business_entity = await db.business_entity.find_one({
            "organization_id": organization_id
        }, {"_id": 0})
        
        # Build claim data structure
        service_lines = []
        billing_provider_npi = None
        rendering_provider_npi = None
        rendering_provider_name = None
        
        for ts in patient_timesheets:
            extracted = ts.get('extracted_data', {})
            entries = extracted.get('entries', [])
            
            for entry in entries:
                service_date = entry.get('date', '')
                service_code = entry.get('service_code', 'T1019')  # Default to T1019 if missing
                hours = entry.get('hours', 0)
                units = entry.get('units', 0)
                
                # Calculate charge (example: $20 per unit)
                charge_per_unit = 20.00
                charge_amount = float(units) * charge_per_unit if units else 0
                
                # Get employee info for rendering provider
                employee_name = entry.get('employee_name', '')
                
                # Fetch employee to get NPI
                if employee_name and not rendering_provider_npi:
                    employee = await db.employees.find_one({
                        "organization_id": organization_id,
                        "$or": [
                            {"first_name": {"$regex": employee_name.split()[0] if employee_name else "", "$options": "i"}},
                            {"employee_id": {"$regex": employee_name, "$options": "i"}}
                        ]
                    }, {"_id": 0})
                    
                    if employee:
                        rendering_provider_npi = employee.get('npi', '1234567890')
                        rendering_provider_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
                
                service_lines.append({
                    "service_date": service_date,
                    "service_code": service_code,
                    "cpt_code": service_code,
                    "charge_amount": charge_amount,
                    "units": units if units else 1,
                })
        
        # Use business entity NPI as billing provider
        if business_entity:
            billing_provider_npi = business_entity.get('business_entity_medicaid_id', '1234567890')
            billing_provider_name = business_entity.get('agency_name', 'Healthcare Agency')
        else:
            billing_provider_npi = '1234567890'  # Placeholder
            billing_provider_name = 'Healthcare Agency'
        
        if not rendering_provider_npi:
            rendering_provider_npi = '1234567890'  # Placeholder
            rendering_provider_name = 'Direct Care Worker'
        
        # Build claim data
        claim_data = {
            "claim_id": f"CLM{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient": {
                "first_name": patient.get('first_name', ''),
                "last_name": patient.get('last_name', ''),
                "date_of_birth": patient.get('date_of_birth', ''),
                "medicaid_id": patient.get('medicaid_number', ''),
                "gender": patient.get('gender', 'U'),
            },
            "billing_provider_npi": billing_provider_npi,
            "billing_provider_name": billing_provider_name,
            "rendering_provider_npi": rendering_provider_npi,
            "rendering_provider_name": rendering_provider_name,
            "diagnosis_code_1": "Z7389",  # Example diagnosis code
            "place_of_service": "12",  # Home
            "service_lines": service_lines,
        }
        
        # Initialize claim generator
        sender_id = business_entity.get('business_entity_id', 'SENDER') if business_entity else 'SENDER'
        claim_generator = ClaimGenerator(
            sender_id=sender_id,
            receiver_id="ODMITS",
            test_mode=True
        )
        
        # Generate EDI file
        edi_content = claim_generator.generate_claim(claim_data)
        
        # Save generated claim to database
        generated_claim = {
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "claim_data": claim_data,
            "edi_content": edi_content,
            "timesheet_ids": request.timesheet_ids,
            "patient_id": patient_id,
            "status": "generated",
            "file_format": "837P",
            "created_at": datetime.now(timezone.utc),
        }
        
        await db.generated_claims.insert_one(generated_claim)
        
        # Return EDI file as downloadable
        filename = f"837P_claim_{datetime.now().strftime('%Y%m%d_%H%M%S')}.edi"
        
        return StreamingResponse(
            io.StringIO(edi_content),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate 837 claim error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Claim generation failed: {str(e)}")

@api_router.get("/claims/generated")
async def get_generated_claims(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get list of generated 837P claims for the organization.
    """
    try:
        organization_id = current_user["organization_id"]
        
        claims = await db.generated_claims.find({
            "organization_id": organization_id
        }, {"_id": 0, "edi_content": 0}).sort("created_at", -1).to_list(length=100)
        
        return {"claims": claims}
        
    except Exception as e:
        logger.error(f"Get generated claims error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/claims/generated/{claim_id}/download")
async def download_generated_claim(
    claim_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Download a previously generated 837P claim file.
    """
    try:
        organization_id = current_user["organization_id"]
        
        claim = await db.generated_claims.find_one({
            "id": claim_id,
            "organization_id": organization_id
        }, {"_id": 0})
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        edi_content = claim.get('edi_content', '')
        filename = f"837P_claim_{claim_id}.edi"
        
        return StreamingResponse(
            io.StringIO(edi_content),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download claim error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/claims/bulk-submit")
async def bulk_submit_claims(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Bulk submit multiple claims to Ohio Medicaid.
    
    NOTE: This is a placeholder for the actual submission functionality.
    Real submission requires ODM trading partner enrollment and EDI connectivity.
    """
    try:
        organization_id = current_user["organization_id"]
        claim_ids = request.get('claim_ids', [])
        
        if not claim_ids:
            raise HTTPException(status_code=400, detail="No claims selected for submission")
        
        # For now, just mark claims as "submitted" in database
        # Real implementation would transmit to ODM via SFTP/AS2
        result = await db.generated_claims.update_many(
            {
                "id": {"$in": claim_ids},
                "organization_id": organization_id
            },
            {
                "$set": {
                    "status": "submitted",
                    "submitted_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "status": "success",
            "message": f"Successfully marked {result.modified_count} claims as submitted",
            "modified_count": result.modified_count,
            "note": "This is a placeholder. Real submission requires ODM trading partner enrollment."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk submit claims error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/enrollment/status")
async def get_enrollment_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get ODM trading partner enrollment status and checklist.
    """
    try:
        organization_id = current_user["organization_id"]
        
        # Check if enrollment record exists
        enrollment = await db.odm_enrollment.find_one({
            "organization_id": organization_id
        }, {"_id": 0})
        
        if not enrollment:
            # Create default enrollment checklist
            steps = [
                {"step_number": 1, "step_name": "Review ODM Trading Partner Information Guide", "description": "Download and review the guide", "completed": False},
                {"step_number": 2, "step_name": "Review HIPAA ASC X12 Technical Reports", "description": "Review TR3 reports from X12 website", "completed": False},
                {"step_number": 3, "step_name": "Begin Trading Partner Enrollment", "description": "Use Trading Partner Management Application", "completed": False},
                {"step_number": 4, "step_name": "Review ODM Companion Guides", "description": "Review 837P companion guide", "completed": False},
                {"step_number": 5, "step_name": "Coordinate Testing Strategy", "description": "Plan testing with IT and business units", "completed": False},
                {"step_number": 6, "step_name": "Complete Trading Partner Agreement", "description": "Submit signed ODM Trading Partner Agreement", "completed": False},
                {"step_number": 7, "step_name": "Complete EDI Connectivity Form", "description": "Submit connectivity form for SFTP/AS2", "completed": False},
                {"step_number": 8, "step_name": "Verify Trading Partner Number", "description": "Receive 7-digit Sender/Receiver ID from ODM", "completed": False},
                {"step_number": 9, "step_name": "Provide Test Provider List", "description": "Submit list of up to 5 providers for testing", "completed": False},
                {"step_number": 10, "step_name": "Submit Test Claims", "description": "Generate and submit test EDI data", "completed": False},
                {"step_number": 11, "step_name": "Verify EDI Receipts", "description": "Receive 999, 824, 277CA, and 835 responses", "completed": False},
            ]
            
            enrollment_doc = {
                "id": str(uuid.uuid4()),
                "organization_id": organization_id,
                "enrollment_status": "not_started",
                "steps": steps,
                "documents": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await db.odm_enrollment.insert_one(enrollment_doc)
            enrollment = enrollment_doc
        
        # Ensure all datetime fields are strings for JSON serialization
        response_data = {
            "id": enrollment.get("id"),
            "organization_id": enrollment.get("organization_id"),
            "trading_partner_id": enrollment.get("trading_partner_id"),
            "enrollment_status": enrollment.get("enrollment_status", "not_started"),
            "steps": enrollment.get("steps", []),
            "documents": enrollment.get("documents", []),
            "created_at": enrollment.get("created_at") if isinstance(enrollment.get("created_at"), str) else enrollment.get("created_at").isoformat() if enrollment.get("created_at") else None,
            "updated_at": enrollment.get("updated_at") if isinstance(enrollment.get("updated_at"), str) else enrollment.get("updated_at").isoformat() if enrollment.get("updated_at") else None,
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Get enrollment status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/enrollment/update-step")
async def update_enrollment_step(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Update a specific enrollment checklist step.
    """
    try:
        organization_id = current_user["organization_id"]
        step_number = request.get('step_number')
        completed = request.get('completed', False)
        notes = request.get('notes', '')
        
        if step_number is None:
            raise HTTPException(status_code=400, detail="step_number is required")
        
        # Update the specific step
        result = await db.odm_enrollment.update_one(
            {
                "organization_id": organization_id,
                "steps.step_number": step_number
            },
            {
                "$set": {
                    "steps.$.completed": completed,
                    "steps.$.completed_date": datetime.now(timezone.utc) if completed else None,
                    "steps.$.notes": notes,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Enrollment record or step not found")
        
        return {"status": "success", "message": "Step updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update enrollment step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/enrollment/trading-partner-id")
async def update_trading_partner_id(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Update ODM trading partner ID once received from ODM.
    """
    try:
        organization_id = current_user["organization_id"]
        trading_partner_id = request.get('trading_partner_id', '')
        
        if not trading_partner_id:
            raise HTTPException(status_code=400, detail="trading_partner_id is required")
        
        result = await db.odm_enrollment.update_one(
            {"organization_id": organization_id},
            {
                "$set": {
                    "trading_partner_id": trading_partner_id,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Enrollment record not found")
        
        return {"status": "success", "message": "Trading partner ID updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update trading partner ID error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Import and include claims router
from routes_claims import router as claims_router
api_router.include_router(claims_router)

# Import and include admin router
from routes_admin import router as admin_router
api_router.include_router(admin_router)

# Import and include geofencing router
from routes_geofencing import router as geofencing_router
api_router.include_router(geofencing_router)

# Import and include manual clock router
from routes_manual_clock import router as manual_clock_router, set_db as set_manual_clock_db
api_router.include_router(manual_clock_router)
set_manual_clock_db(db)  # Inject database

# Import and include authorizations router
from routes_authorizations import router as authorizations_router, set_db as set_authorizations_db
api_router.include_router(authorizations_router)
set_authorizations_db(db)  # Inject database

# Import and include notifications router
from routes_notifications import router as notifications_router, set_db as set_notifications_db
api_router.include_router(notifications_router)
set_notifications_db(db)  # Inject database

# Import and include extended notifications router (read/unread tracking)
from routes_notifications_extended import router as notifications_ext_router, set_db as set_notifications_ext_db
api_router.include_router(notifications_ext_router)
set_notifications_ext_db(db)  # Inject database

# Import and include ICD-10 lookup router
from routes_icd10 import router as icd10_router
api_router.include_router(icd10_router)

# Import and include NPI lookup router
from routes_npi import router as npi_router
api_router.include_router(npi_router)

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