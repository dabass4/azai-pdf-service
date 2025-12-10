"""
Geofencing Module for EVV Compliance
Validates that employees are at the correct location when clocking in/out
"""
from typing import Dict, Optional, Tuple
import math
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class GeofenceValidator:
    """
    Validates employee location against patient's registered address
    Uses Haversine formula for accurate distance calculation
    """
    
    # Earth's radius in meters
    EARTH_RADIUS_METERS = 6371000
    
    # Default geofence radius in meters (configurable per organization)
    DEFAULT_RADIUS_METERS = 150  # ~500 feet
    
    # Tolerance levels
    STRICT_RADIUS = 100   # ~330 feet
    MODERATE_RADIUS = 150  # ~500 feet
    LENIENT_RADIUS = 300   # ~1000 feet
    
    @staticmethod
    def calculate_distance(
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula
        
        Args:
            lat1, lon1: First coordinate (employee location)
            lat2, lon2: Second coordinate (patient address)
            
        Returns:
            Distance in meters
        """
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        
        # Distance in meters
        distance = GeofenceValidator.EARTH_RADIUS_METERS * c
        
        return distance
    
    @staticmethod
    def meters_to_feet(meters: float) -> float:
        """Convert meters to feet"""
        return meters * 3.28084
    
    @staticmethod
    def feet_to_meters(feet: float) -> float:
        """Convert feet to meters"""
        return feet / 3.28084
    
    @staticmethod
    def validate_location(
        employee_lat: float,
        employee_lon: float,
        patient_lat: float,
        patient_lon: float,
        allowed_radius_meters: Optional[float] = None
    ) -> Dict:
        """
        Validate if employee is within allowed geofence radius
        
        Args:
            employee_lat: Employee's current latitude
            employee_lon: Employee's current longitude
            patient_lat: Patient's registered latitude
            patient_lon: Patient's registered longitude
            allowed_radius_meters: Custom radius, defaults to DEFAULT_RADIUS_METERS
            
        Returns:
            Dict with validation result:
            {
                "valid": bool,
                "distance_meters": float,
                "distance_feet": float,
                "allowed_radius_meters": float,
                "allowed_radius_feet": float,
                "variance_meters": float,  # How far outside (negative if inside)
                "accuracy_level": str,  # "excellent", "good", "acceptable", "poor"
                "message": str
            }
        """
        if allowed_radius_meters is None:
            allowed_radius_meters = GeofenceValidator.DEFAULT_RADIUS_METERS
        
        # Calculate distance
        distance = GeofenceValidator.calculate_distance(
            employee_lat, employee_lon,
            patient_lat, patient_lon
        )
        
        # Determine if within geofence
        is_valid = distance <= allowed_radius_meters
        variance = distance - allowed_radius_meters
        
        # Determine accuracy level
        if distance <= 50:  # Within 50m (~164 feet)
            accuracy_level = "excellent"
        elif distance <= 100:  # Within 100m (~330 feet)
            accuracy_level = "good"
        elif distance <= allowed_radius_meters:
            accuracy_level = "acceptable"
        else:
            accuracy_level = "poor"
        
        # Build message
        distance_feet = GeofenceValidator.meters_to_feet(distance)
        allowed_feet = GeofenceValidator.meters_to_feet(allowed_radius_meters)
        
        if is_valid:
            message = f"Location verified: {distance_feet:.0f} ft from patient address (within {allowed_feet:.0f} ft radius)"
        else:
            message = f"⚠️ Location outside geofence: {distance_feet:.0f} ft from patient address (allowed: {allowed_feet:.0f} ft)"
        
        return {
            "valid": is_valid,
            "distance_meters": round(distance, 2),
            "distance_feet": round(distance_feet, 2),
            "allowed_radius_meters": allowed_radius_meters,
            "allowed_radius_feet": round(allowed_feet, 2),
            "variance_meters": round(variance, 2) if not is_valid else 0,
            "accuracy_level": accuracy_level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def validate_clock_event(
        event_type: str,  # "clock_in" or "clock_out"
        employee_location: Dict[str, float],  # {"latitude": x, "longitude": y}
        patient_location: Dict[str, float],  # {"latitude": x, "longitude": y}
        allowed_radius_meters: Optional[float] = None
    ) -> Dict:
        """
        Validate a clock in/out event
        
        Args:
            event_type: "clock_in" or "clock_out"
            employee_location: Employee GPS coordinates
            patient_location: Patient address coordinates
            allowed_radius_meters: Custom radius
            
        Returns:
            Validation result with geofence status
        """
        validation = GeofenceValidator.validate_location(
            employee_location["latitude"],
            employee_location["longitude"],
            patient_location["latitude"],
            patient_location["longitude"],
            allowed_radius_meters
        )
        
        validation["event_type"] = event_type
        validation["employee_location"] = employee_location
        validation["patient_location"] = patient_location
        
        # Log the validation
        if validation["valid"]:
            logger.info(
                f"{event_type.upper()}: Location verified - "
                f"{validation['distance_feet']:.0f} ft from patient address"
            )
        else:
            logger.warning(
                f"{event_type.upper()}: GEOFENCE VIOLATION - "
                f"{validation['distance_feet']:.0f} ft from patient address "
                f"(allowed: {validation['allowed_radius_feet']:.0f} ft)"
            )
        
        return validation


class GeofenceException:
    """
    Manage geofence exceptions and override reasons
    For cases where employee is legitimately outside geofence
    """
    
    VALID_EXCEPTION_REASONS = [
        "emergency_situation",
        "patient_temporary_location",
        "rural_gps_inaccuracy",
        "pre_approved_alternate_location",
        "patient_transportation",
        "medical_appointment",
        "community_outing",
        "other_documented_reason"
    ]
    
    @staticmethod
    def create_exception(
        timesheet_id: str,
        employee_id: str,
        patient_id: str,
        reason: str,
        notes: str,
        approved_by: Optional[str] = None
    ) -> Dict:
        """
        Create a geofence exception record
        
        Args:
            timesheet_id: Associated timesheet
            employee_id: Employee who needs exception
            patient_id: Patient being served
            reason: Exception reason from VALID_EXCEPTION_REASONS
            notes: Detailed explanation
            approved_by: Admin/supervisor who approved
            
        Returns:
            Exception record
        """
        if reason not in GeofenceException.VALID_EXCEPTION_REASONS:
            raise ValueError(f"Invalid exception reason. Must be one of: {GeofenceException.VALID_EXCEPTION_REASONS}")
        
        return {
            "id": f"GFE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "timesheet_id": timesheet_id,
            "employee_id": employee_id,
            "patient_id": patient_id,
            "reason": reason,
            "notes": notes,
            "approved_by": approved_by,
            "status": "pending" if not approved_by else "approved",
            "created_at": datetime.now(timezone.utc).isoformat()
        }


class GeofenceConfig:
    """
    Organization-level geofencing configuration
    """
    
    @staticmethod
    def get_default_config() -> Dict:
        """
        Get default geofence configuration
        """
        return {
            "enabled": True,
            "radius_meters": GeofenceValidator.DEFAULT_RADIUS_METERS,
            "radius_feet": GeofenceValidator.meters_to_feet(GeofenceValidator.DEFAULT_RADIUS_METERS),
            "strict_mode": False,  # If True, reject submissions outside geofence
            "require_approval_for_violations": True,  # Require supervisor approval for violations
            "allow_exceptions": True,
            "log_all_locations": True,  # Log all location checks for audit
            "alert_on_violations": True  # Send alerts for geofence violations
        }
    
    @staticmethod
    def create_custom_config(
        radius_feet: float,
        strict_mode: bool = False,
        require_approval: bool = True
    ) -> Dict:
        """
        Create custom geofence configuration
        
        Args:
            radius_feet: Geofence radius in feet
            strict_mode: If True, block submissions outside geofence
            require_approval: If True, require supervisor approval for violations
        """
        radius_meters = GeofenceValidator.feet_to_meters(radius_feet)
        
        return {
            "enabled": True,
            "radius_meters": radius_meters,
            "radius_feet": radius_feet,
            "strict_mode": strict_mode,
            "require_approval_for_violations": require_approval,
            "allow_exceptions": True,
            "log_all_locations": True,
            "alert_on_violations": True
        }
