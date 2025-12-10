"""
Manual Clock In/Out Routes
Handles manual time entries with geofencing validation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import logging
import uuid

from geofencing import GeofenceValidator
from auth import get_current_user, get_organization_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/timesheets", tags=["manual-clock"])


class LocationData(BaseModel):
    """Location data from frontend"""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: str
    provider: Optional[str] = "gps"


class ValidationData(BaseModel):
    """Validation result from frontend"""
    valid: bool
    distance_meters: float
    distance_feet: float
    allowed_radius_feet: float
    accuracy_level: str
    message: str


class ManualClockInRequest(BaseModel):
    """Request for manual clock in"""
    patient_id: str
    employee_id: str
    location: LocationData
    validation: Optional[ValidationData] = None
    timestamp: str


class ManualClockOutRequest(BaseModel):
    """Request for manual clock out"""
    timesheet_id: str
    location: LocationData
    validation: Optional[ValidationData] = None
    timestamp: str


# This will be injected by server.py
db = None

def set_db(database):
    global db
    db = database


@router.post("/manual-clock-in")
async def manual_clock_in(
    request: ManualClockInRequest,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Manual clock in with geofencing
    
    Creates a new timesheet entry with location data.
    If geofence is violated, flags for supervisor review.
    """
    try:
        # Get patient details
        patient = await db.patients.find_one(
            {"id": request.patient_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Check if patient has GPS coordinates
        if not patient.get('address_latitude') or not patient.get('address_longitude'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient address missing GPS coordinates. Please update patient profile."
            )
        
        # Get employee details
        employee = await db.employees.find_one(
            {"id": request.employee_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Validate location (server-side validation for security)
        server_validation = GeofenceValidator.validate_clock_event(
            event_type="clock_in",
            employee_location={
                "latitude": request.location.latitude,
                "longitude": request.location.longitude
            },
            patient_location={
                "latitude": patient['address_latitude'],
                "longitude": patient['address_longitude']
            }
        )
        
        # Create timesheet record
        timesheet_id = str(uuid.uuid4())
        clock_in_time = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
        
        created_now = datetime.now(timezone.utc)
        
        timesheet = {
            "id": timesheet_id,
            "organization_id": organization_id,
            "patient_id": request.patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "employee_id": request.employee_id,
            "employee_name": f"{employee['first_name']} {employee['last_name']}",
            "entry_method": "manual",
            "status": "active",  # Active shift
            "clock_in_time": clock_in_time.isoformat(),
            "clock_in_latitude": request.location.latitude,
            "clock_in_longitude": request.location.longitude,
            "clock_in_accuracy": request.location.accuracy,
            "clock_in_timestamp": clock_in_time.isoformat(),
            "clock_in_geofence_valid": server_validation["valid"],
            "clock_in_distance_feet": server_validation["distance_feet"],
            "clock_out_time": None,
            "requires_supervisor_approval": not server_validation["valid"],
            "created_at": created_now.isoformat(),
            "updated_at": created_now.isoformat()
        }
        
        # Insert timesheet
        await db.timesheets.insert_one(timesheet)
        
        # If geofence violated, create violation record
        if not server_validation["valid"]:
            violation = {
                "id": str(uuid.uuid4()),
                "timesheet_id": timesheet_id,
                "organization_id": organization_id,
                "employee_id": request.employee_id,
                "employee_name": f"{employee['first_name']} {employee['last_name']}",
                "patient_id": request.patient_id,
                "patient_name": f"{patient['first_name']} {patient['last_name']}",
                "event_type": "clock_in",
                "violation_time": clock_in_time.isoformat(),
                "distance_meters": server_validation["distance_meters"],
                "distance_feet": server_validation["distance_feet"],
                "allowed_radius_feet": server_validation["allowed_radius_feet"],
                "employee_location": request.location.dict(),
                "patient_location": {
                    "latitude": patient['address_latitude'],
                    "longitude": patient['address_longitude'],
                    "address": f"{patient.get('address_street', '')}, {patient.get('address_city', '')}"
                },
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.geofence_violations.insert_one(violation)
            
            logger.warning(
                f"Geofence violation on clock in: Timesheet {timesheet_id}, "
                f"Distance: {server_validation['distance_feet']:.0f} ft"
            )
        
        logger.info(
            f"Manual clock in: Employee {employee['first_name']} {employee['last_name']}, "
            f"Patient {patient['first_name']} {patient['last_name']}, "
            f"Geofence: {'VALID' if server_validation['valid'] else 'VIOLATED'}"
        )
        
        return {
            "status": "success",
            "message": "Clocked in successfully" + (
                " (requires supervisor approval)" if not server_validation["valid"] else ""
            ),
            "timesheet": {
                "id": timesheet_id,
                "clock_in_time": clock_in_time.isoformat(),
                "patient_name": timesheet["patient_name"],
                "employee_name": timesheet["employee_name"],
                "geofence_valid": server_validation["valid"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual clock in error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clock in failed: {str(e)}"
        )


@router.post("/manual-clock-out")
async def manual_clock_out(
    request: ManualClockOutRequest,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Manual clock out with geofencing
    
    Updates existing timesheet with clock out data and location.
    """
    try:
        # Get timesheet
        timesheet = await db.timesheets.find_one(
            {"id": request.timesheet_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not timesheet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timesheet not found"
            )
        
        if timesheet.get('clock_out_time'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already clocked out"
            )
        
        # Get patient details for geofence validation
        patient = await db.patients.find_one(
            {"id": timesheet["patient_id"], "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Validate location
        server_validation = GeofenceValidator.validate_clock_event(
            event_type="clock_out",
            employee_location={
                "latitude": request.location.latitude,
                "longitude": request.location.longitude
            },
            patient_location={
                "latitude": patient['address_latitude'],
                "longitude": patient['address_longitude']
            }
        )
        
        clock_out_time = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
        
        # Calculate hours worked
        clock_in_time = timesheet['clock_in_time']
        if isinstance(clock_in_time, str):
            clock_in_time = datetime.fromisoformat(clock_in_time)
        
        duration = clock_out_time - clock_in_time
        hours_decimal = duration.total_seconds() / 3600
        hours = int(hours_decimal)
        minutes = int((hours_decimal - hours) * 60)
        
        # Update timesheet
        update_data = {
            "clock_out_time": clock_out_time.isoformat(),
            "clock_out_latitude": request.location.latitude,
            "clock_out_longitude": request.location.longitude,
            "clock_out_accuracy": request.location.accuracy,
            "clock_out_timestamp": clock_out_time.isoformat(),
            "clock_out_geofence_valid": server_validation["valid"],
            "clock_out_distance_feet": server_validation["distance_feet"],
            "hours_worked": hours_decimal,
            "hours": hours,
            "minutes": minutes,
            "formatted_hours": f"{hours}:{minutes:02d}",
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If clock out violated geofence, flag for review
        if not server_validation["valid"]:
            update_data["requires_supervisor_approval"] = True
            
            # Create violation record
            employee = await db.employees.find_one(
                {"id": timesheet["employee_id"]},
                {"_id": 0}
            )
            
            violation = {
                "id": str(uuid.uuid4()),
                "timesheet_id": request.timesheet_id,
                "organization_id": organization_id,
                "employee_id": timesheet["employee_id"],
                "employee_name": timesheet["employee_name"],
                "patient_id": timesheet["patient_id"],
                "patient_name": timesheet["patient_name"],
                "event_type": "clock_out",
                "violation_time": clock_out_time.isoformat(),
                "distance_meters": server_validation["distance_meters"],
                "distance_feet": server_validation["distance_feet"],
                "allowed_radius_feet": server_validation["allowed_radius_feet"],
                "employee_location": request.location.dict(),
                "patient_location": {
                    "latitude": patient['address_latitude'],
                    "longitude": patient['address_longitude']
                },
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.geofence_violations.insert_one(violation)
        
        await db.timesheets.update_one(
            {"id": request.timesheet_id},
            {"$set": update_data}
        )
        
        logger.info(
            f"Manual clock out: Timesheet {request.timesheet_id}, "
            f"Hours: {hours}:{minutes:02d}, "
            f"Geofence: {'VALID' if server_validation['valid'] else 'VIOLATED'}"
        )
        
        return {
            "status": "success",
            "message": "Clocked out successfully" + (
                " (requires supervisor approval)" if not server_validation["valid"] else ""
            ),
            "hours_worked": f"{hours}:{minutes:02d}",
            "geofence_valid": server_validation["valid"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual clock out error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clock out failed: {str(e)}"
        )


@router.get("/active")
async def get_active_timesheet(
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get active timesheet (clocked in but not clocked out)
    """
    try:
        timesheet = await db.timesheets.find_one(
            {
                "organization_id": organization_id,
                "status": "active",
                "clock_out_time": None
            },
            {"_id": 0}
        )
        
        if timesheet:
            return {"status": "success", "timesheet": timesheet}
        else:
            return {"status": "success", "timesheet": None}
            
    except Exception as e:
        logger.error(f"Get active timesheet error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
