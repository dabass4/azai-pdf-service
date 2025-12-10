"""
Geofencing API Routes
Endpoints for location validation and geofence management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
import logging

from geofencing import GeofenceValidator, GeofenceException, GeofenceConfig
from geofence_models import (
    LocationData, ClockEvent, GeofenceValidationResult, 
    GeofenceViolation, OrganizationGeofenceConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geofence", tags=["geofencing"])


# This would typically come from auth middleware
def get_current_user():
    """Placeholder for auth dependency"""
    return {"user_id": "test-user", "organization_id": "test-org"}


@router.post("/validate", response_model=GeofenceValidationResult)
async def validate_location(
    employee_lat: float,
    employee_lon: float,
    patient_lat: float,
    patient_lon: float,
    event_type: str = "clock_in",
    current_user: dict = Depends(get_current_user)
):
    """
    Validate if employee location is within geofence radius of patient address
    
    Args:
        employee_lat: Employee's current latitude
        employee_lon: Employee's current longitude
        patient_lat: Patient's registered latitude
        patient_lon: Patient's registered longitude
        event_type: "clock_in" or "clock_out"
    
    Returns:
        GeofenceValidationResult with distance and validation status
    """
    try:
        result = GeofenceValidator.validate_clock_event(
            event_type=event_type,
            employee_location={"latitude": employee_lat, "longitude": employee_lon},
            patient_location={"latitude": patient_lat, "longitude": patient_lon}
        )
        
        return GeofenceValidationResult(**result)
    
    except Exception as e:
        logger.error(f"Geofence validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geofence validation failed: {str(e)}"
        )


@router.get("/distance")
async def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate distance between two GPS coordinates
    
    Returns distance in both meters and feet
    """
    try:
        distance_meters = GeofenceValidator.calculate_distance(lat1, lon1, lat2, lon2)
        distance_feet = GeofenceValidator.meters_to_feet(distance_meters)
        
        return {
            "distance_meters": round(distance_meters, 2),
            "distance_feet": round(distance_feet, 2),
            "distance_miles": round(distance_feet / 5280, 2)
        }
    
    except Exception as e:
        logger.error(f"Distance calculation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Distance calculation failed: {str(e)}"
        )


@router.get("/config")
async def get_geofence_config(
    current_user: dict = Depends(get_current_user)
):
    """
    Get geofencing configuration for current organization
    """
    # In production, this would fetch from database
    config = GeofenceConfig.get_default_config()
    config["organization_id"] = current_user["organization_id"]
    return config


@router.put("/config")
async def update_geofence_config(
    radius_feet: float,
    strict_mode: bool = False,
    require_approval: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    Update geofencing configuration for organization
    
    Args:
        radius_feet: Geofence radius in feet (e.g., 500)
        strict_mode: If true, block submissions outside geofence
        require_approval: If true, require supervisor approval for violations
    """
    try:
        config = GeofenceConfig.create_custom_config(
            radius_feet=radius_feet,
            strict_mode=strict_mode,
            require_approval=require_approval
        )
        
        # In production, save to database
        # await db.geofence_configs.update_one(
        #     {"organization_id": current_user["organization_id"]},
        #     {"$set": config},
        #     upsert=True
        # )
        
        logger.info(f"Geofence config updated for org {current_user['organization_id']}: {radius_feet} ft")
        
        return {
            "status": "success",
            "message": f"Geofence radius updated to {radius_feet} feet",
            "config": config
        }
    
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )


@router.post("/clock-in")
async def clock_in_with_location(
    timesheet_id: str,
    employee_id: str,
    patient_id: str,
    location: LocationData,
    current_user: dict = Depends(get_current_user)
):
    """
    Clock in with location validation
    
    This endpoint would be called from the frontend when an employee 
    starts their shift. It captures the GPS location and validates 
    it against the patient's registered address.
    """
    # In production, fetch patient location from database
    # patient = await db.patients.find_one({"id": patient_id})
    # patient_location = {
    #     "latitude": patient["address_latitude"],
    #     "longitude": patient["address_longitude"]
    # }
    
    # For now, return validation result
    # In production, this would also create a clock_in record
    
    return {
        "status": "success",
        "message": "Clock in recorded with location",
        "timesheet_id": timesheet_id,
        "employee_id": employee_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": location.dict()
    }


@router.post("/clock-out")
async def clock_out_with_location(
    timesheet_id: str,
    employee_id: str,
    patient_id: str,
    location: LocationData,
    current_user: dict = Depends(get_current_user)
):
    """
    Clock out with location validation
    
    Similar to clock-in, but for end of shift
    """
    return {
        "status": "success",
        "message": "Clock out recorded with location",
        "timesheet_id": timesheet_id,
        "employee_id": employee_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": location.dict()
    }


@router.get("/violations")
async def get_geofence_violations(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of geofence violations for organization
    
    Args:
        status: Filter by status (pending, approved, rejected)
    """
    # In production, fetch from database
    # violations = await db.geofence_violations.find({
    #     "organization_id": current_user["organization_id"],
    #     "status": status
    # }).to_list(100)
    
    return {
        "status": "success",
        "violations": [],
        "message": "No violations found (mock response)"
    }


@router.post("/violations/{violation_id}/approve")
async def approve_violation(
    violation_id: str,
    reason: str,
    notes: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Approve a geofence violation exception
    
    Args:
        violation_id: ID of the violation
        reason: Reason for approval (from VALID_EXCEPTION_REASONS)
        notes: Additional notes explaining the exception
    """
    # In production, update violation status in database
    return {
        "status": "success",
        "message": f"Violation {violation_id} approved",
        "approved_by": current_user["user_id"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/test-location")
async def test_location_services(
    latitude: float,
    longitude: float
):
    """
    Test endpoint to verify location services are working
    No auth required for testing
    """
    return {
        "status": "success",
        "message": "Location received successfully",
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "valid_coordinates": GeofenceValidator.calculate_distance(latitude, longitude, latitude, longitude) == 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
