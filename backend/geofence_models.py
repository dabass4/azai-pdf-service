"""
Geofencing Data Models
Pydantic models for geofence validation and tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class LocationData(BaseModel):
    """GPS location data"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")
    accuracy: Optional[float] = Field(None, description="GPS accuracy in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider: Optional[str] = Field(None, description="Location provider: gps, network, manual")


class ClockEvent(BaseModel):
    """Clock in/out event with location"""
    event_id: str
    timesheet_id: str
    employee_id: str
    patient_id: str
    event_type: str = Field(..., pattern="^(clock_in|clock_out)$")
    event_time: datetime
    location: LocationData
    device_info: Optional[dict] = None  # Browser/device that captured location


class GeofenceValidationResult(BaseModel):
    """Result of geofence validation"""
    valid: bool
    distance_meters: float
    distance_feet: float
    allowed_radius_meters: float
    allowed_radius_feet: float
    variance_meters: float = 0
    accuracy_level: str = Field(..., pattern="^(excellent|good|acceptable|poor)$")
    message: str
    timestamp: datetime
    event_type: Optional[str] = None
    employee_location: Optional[dict] = None
    patient_location: Optional[dict] = None


class GeofenceViolation(BaseModel):
    """Record of a geofence violation"""
    id: str
    timesheet_id: str
    employee_id: str
    employee_name: str
    patient_id: str
    patient_name: str
    event_type: str  # clock_in or clock_out
    violation_time: datetime
    distance_meters: float
    distance_feet: float
    allowed_radius_feet: float
    employee_location: LocationData
    patient_location: dict
    status: str = "pending"  # pending, approved, rejected
    exception_reason: Optional[str] = None
    exception_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GeofenceException(BaseModel):
    """Exception/override for geofence violation"""
    id: str
    violation_id: str
    timesheet_id: str
    employee_id: str
    patient_id: str
    reason: str
    notes: str
    approved_by: str
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class OrganizationGeofenceConfig(BaseModel):
    """Organization-level geofencing configuration"""
    organization_id: str
    enabled: bool = True
    radius_meters: float = 150
    radius_feet: float = 492
    strict_mode: bool = False
    require_approval_for_violations: bool = True
    allow_exceptions: bool = True
    log_all_locations: bool = True
    alert_on_violations: bool = True
    notification_emails: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
