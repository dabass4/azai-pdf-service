from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
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
class TimeEntry(BaseModel):
    """Single time entry for a specific date"""
    date: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    hours_worked: Optional[str] = None

class ExtractedData(BaseModel):
    employee_name: Optional[str] = None
    client_name: Optional[str] = None
    service_code: Optional[str] = None
    signature: Optional[str] = None
    time_entries: List[TimeEntry] = []  # Multiple date/time entries

class Timesheet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str
    extracted_data: Optional[ExtractedData] = None
    status: str = "processing"  # processing, completed, failed, submitted
    sandata_status: Optional[str] = None  # pending, submitted, error
    error_message: Optional[str] = None
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
        
        extraction_prompt = """Analyze this timesheet document carefully and extract the following information. Return ONLY a valid JSON object with this exact structure:

{
  "employee_name": "full name of the employee",
  "date": "date in YYYY-MM-DD format",
  "time_in": "clock in time in HH:MM AM/PM format",
  "time_out": "clock out time in HH:MM AM/PM format",
  "hours_worked": "total hours worked as number or text",
  "client_name": "name of the client or patient",
  "service_code": "service or billing code",
  "signature": "Yes if signature is present, No if not"
}

If any field is not found or unclear, use "Not Found" as the value. Return ONLY the JSON object, no additional text or explanation."""
        
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
            
            # Create ExtractedData with validated fields
            return ExtractedData(
                employee_name=extracted_json.get("employee_name"),
                date=extracted_json.get("date"),
                time_in=extracted_json.get("time_in"),
                time_out=extracted_json.get("time_out"),
                hours_worked=extracted_json.get("hours_worked"),
                client_name=extracted_json.get("client_name"),
                service_code=extracted_json.get("service_code"),
                signature=extracted_json.get("signature")
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
        payload = {
            "employee_name": timesheet.extracted_data.employee_name,
            "date": timesheet.extracted_data.date,
            "time_in": timesheet.extracted_data.time_in,
            "time_out": timesheet.extracted_data.time_out,
            "hours_worked": timesheet.extracted_data.hours_worked,
            "client_name": timesheet.extracted_data.client_name,
            "service_code": timesheet.extracted_data.service_code,
            "signature_verified": timesheet.extracted_data.signature == "Yes"
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

@api_router.delete("/timesheets/{timesheet_id}")
async def delete_timesheet(timesheet_id: str):
    """Delete a timesheet"""
    result = await db.timesheets.delete_one({"id": timesheet_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    return {"message": "Timesheet deleted successfully"}

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