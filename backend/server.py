from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import base64
import json

from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import aiohttp
from pdf2image import convert_from_path
from PIL import Image

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
    
    # Basic Information
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    ssn: str  # Social Security Number (9 digits) - EVV Required
    date_of_birth: str  # YYYY-MM-DD format
    sex: str  # Male, Female, Other
    
    # Contact Information
    email: Optional[str] = None  # EVV: Must be unique if provided
    phone: str
    address_street: str
    address_city: str
    address_state: str
    address_zip: str
    
    # Employment Information
    employee_id: Optional[str] = None  # Internal employee ID
    hire_date: str  # YYYY-MM-DD format
    job_title: str
    department: Optional[str] = None
    hourly_rate: Optional[float] = None
    employment_status: str  # Full-time, Part-time, Contract
    
    # EVV DCW Fields
    staff_pin: Optional[str] = None  # EVV: Staff PIN for telephony (9 digits)
    staff_other_id: Optional[str] = None  # EVV: External system ID
    staff_position: Optional[str] = None  # EVV: Position code (3 characters)
    
    # Emergency Contact
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relation: str
    
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
    sex: str  # Male, Female, Other
    date_of_birth: str  # YYYY-MM-DD format
    is_newborn: bool = False  # EVV: Newborn indicator
    
    # Address with Geographic Coordinates (EVV Required)
    address_street: str
    address_city: str
    address_state: str
    address_zip: str
    address_latitude: Optional[float] = None  # EVV: Required for primary address
    address_longitude: Optional[float] = None  # EVV: Required for primary address
    address_type: str = "Home"  # Home, Service, Billing
    
    # Timezone (EVV Required)
    timezone: str = "America/New_York"  # Default to Eastern for Ohio
    
    # Medical Information
    prior_auth_number: str  # Alphanumeric with special characters
    icd10_code: str
    icd10_description: Optional[str] = None
    physician_name: str
    physician_npi: str  # 10-digit NPI
    medicaid_number: str  # 12 characters max (Ohio: 12 digits with leading zeros)
    
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
    filename: str
    file_type: str
    extracted_data: Optional[ExtractedData] = None
    status: str = "processing"  # processing, completed, failed, submitted
    sandata_status: Optional[str] = None  # pending, submitted, error
    error_message: Optional[str] = None
    patient_id: Optional[str] = None  # Link to patient profile
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimesheetCreate(BaseModel):
    filename: str
    file_type: str

# Initialize LLM Chat
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

async def extract_timesheet_data(file_path: str, file_type: str) -> ExtractedData:
    """Extract data from timesheet using Gemini Vision API"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"timesheet-{uuid.uuid4()}",
            system_message="You are an expert at extracting structured data from timesheets. Extract all fields accurately and return valid JSON."
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Convert PDF to image if needed (Gemini works better with images)
        processing_file_path = file_path
        mime_type = "image/jpeg"
        
        if file_type == 'pdf':
            try:
                logger.info(f"Converting PDF to image: {file_path}")
                # Convert PDF first page to image
                images = convert_from_path(file_path, first_page=1, last_page=1)
                if images:
                    # Save as JPEG
                    image_path = file_path.replace('.pdf', '_page1.jpg')
                    images[0].save(image_path, 'JPEG')
                    processing_file_path = image_path
                    logger.info(f"PDF converted to image: {image_path}")
            except Exception as e:
                logger.error(f"PDF conversion error: {e}")
                # Try with original PDF anyway
                mime_type = "application/pdf"
        elif file_type in ['jpg', 'jpeg', 'png']:
            mime_type = f"image/{file_type if file_type != 'jpg' else 'jpeg'}"
        
        logger.info(f"Processing file: {processing_file_path}, type: {file_type}, mime: {mime_type}")
        
        file_content = FileContentWithMimeType(
            file_path=processing_file_path,
            mime_type=mime_type
        )
        
        extraction_prompt = """Analyze this timesheet document carefully. It may contain ONE patient/client with MULTIPLE employees who worked with that patient.

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
          "time_in": "HH:MM",
          "time_out": "HH:MM",
          "hours_worked": "number of hours"
        }
      ]
    }
  ]
}

IMPORTANT INSTRUCTIONS:
- Extract ALL employees from the timesheet
- If there's only one employee, the employee_entries array should have one object
- Extract ALL date/time entries for each employee
- Group time entries by employee
- If the timesheet has the same service code for all employees, repeat it for each

TIME FORMAT RULES (CRITICAL):
- Extract times in 24-hour format (HH:MM) OR 12-hour format without spaces
- If you see "8:30 AM", extract as "8:30" (we'll determine AM/PM automatically)
- If you see "5:45 PM", extract as "17:45" OR "5:45" (system will normalize)
- DO NOT include AM/PM in the extracted time - just the numbers
- Examples: "8:30", "17:45", "14:30", "9:00"

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
                                    time_entries.append(TimeEntry(
                                        date=entry.get("date"),
                                        time_in=entry.get("time_in"),
                                        time_out=entry.get("time_out"),
                                        hours_worked=entry.get("hours_worked")
                                    ))
                        
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
    """Submit timesheet data to Sandata API (mocked for now)"""
    try:
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
    """Upload and process a timesheet file"""
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
        
        # Create timesheet record
        timesheet = Timesheet(
            filename=file.filename,
            file_type=file_extension,
            status="processing"
        )
        
        # Save to database
        doc = timesheet.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        await db.timesheets.insert_one(doc)
        
        # Extract data in background (for now, doing it synchronously)
        try:
            extracted_data = await extract_timesheet_data(str(file_path), file_extension)
            timesheet.extracted_data = extracted_data
            timesheet.status = "completed"
            
            # Auto-submit to Sandata
            submission_result = await submit_to_sandata(timesheet)
            if submission_result["status"] == "success":
                timesheet.sandata_status = "submitted"
            else:
                timesheet.sandata_status = "error"
                timesheet.error_message = submission_result.get("message", "Unknown error")
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
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
        
        # Clean up temp file
        try:
            file_path.unlink()
        except:
            pass
        
        return timesheet
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/timesheets", response_model=List[Timesheet])
async def get_timesheets():
    """Get all timesheets"""
    timesheets = await db.timesheets.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
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
async def get_patients():
    """Get all patient profiles"""
    patients = await db.patients.find({}, {"_id": 0}).sort("last_name", 1).to_list(1000)
    
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
async def get_employees():
    """Get all employee profiles"""
    employees = await db.employees.find({}, {"_id": 0}).sort("last_name", 1).to_list(1000)
    
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