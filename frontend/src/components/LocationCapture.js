import React, { useState, useEffect } from 'react';
import { MapPin, AlertCircle, CheckCircle, Loader } from 'lucide-react';

/**
 * LocationCapture Component
 * 
 * Captures GPS location from browser and validates against patient address
 * Used for EVV compliance and geofencing
 */
const LocationCapture = ({ 
  patientLocation,  // { latitude, longitude, address }
  onLocationCaptured,  // Callback with captured location
  onValidationComplete,  // Callback with validation result
  autoCapture = false,  // Auto-capture on mount
  showValidation = true,  // Show validation UI
  allowedRadiusFeet = 500
}) => {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState(null);
  const [permissionStatus, setPermissionStatus] = useState('prompt'); // 'granted', 'denied', 'prompt'

  // Check geolocation support
  const isGeolocationSupported = 'geolocation' in navigator;

  useEffect(() => {
    if (autoCapture && isGeolocationSupported) {
      captureLocation();
    }
    
    // Check permission status
    if ('permissions' in navigator) {
      navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        setPermissionStatus(result.state);
        result.onchange = () => setPermissionStatus(result.state);
      });
    }
  }, [autoCapture]);

  const captureLocation = () => {
    if (!isGeolocationSupported) {
      setError('Geolocation is not supported by your browser');
      return;
    }

    setLoading(true);
    setError(null);

    const options = {
      enableHighAccuracy: true,  // Request GPS instead of network location
      timeout: 10000,  // 10 second timeout
      maximumAge: 0  // Don't use cached position
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const capturedLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude,
          timestamp: new Date(position.timestamp).toISOString(),
          provider: 'gps'
        };

        setLocation(capturedLocation);
        setLoading(false);

        // Notify parent
        if (onLocationCaptured) {
          onLocationCaptured(capturedLocation);
        }

        // Validate if patient location provided
        if (patientLocation && showValidation) {
          validateLocation(capturedLocation);
        }
      },
      (error) => {
        setLoading(false);
        
        let errorMessage;
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location permission denied. Please enable location access in your browser settings.';
            setPermissionStatus('denied');
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable. Please check your device settings.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out. Please try again.';
            break;
          default:
            errorMessage = 'An unknown error occurred while getting your location.';
        }
        
        setError(errorMessage);
      },
      options
    );
  };

  const validateLocation = async (employeeLocation) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/geofence/validate?` +
        `employee_lat=${employeeLocation.latitude}&` +
        `employee_lon=${employeeLocation.longitude}&` +
        `patient_lat=${patientLocation.latitude}&` +
        `patient_lon=${patientLocation.longitude}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Add auth token if required
            // 'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const validationResult = await response.json();
        setValidation(validationResult);
        
        if (onValidationComplete) {
          onValidationComplete(validationResult);
        }
      }
    } catch (err) {
      console.error('Location validation error:', err);
    }
  };

  const getAccuracyLevel = (accuracy) => {
    if (!accuracy) return 'Unknown';
    if (accuracy <= 10) return 'Excellent';
    if (accuracy <= 50) return 'Good';
    if (accuracy <= 100) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="location-capture space-y-4">
      {/* Geolocation Not Supported */}
      {!isGeolocationSupported && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900">Location Not Supported</p>
            <p className="text-sm text-red-700">Your browser doesn't support geolocation services.</p>
          </div>
        </div>
      )}

      {/* Permission Denied */}
      {permissionStatus === 'denied' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div>
            <p className="font-semibold text-yellow-900">Location Permission Denied</p>
            <p className="text-sm text-yellow-700">
              Please enable location access in your browser settings to use this feature.
            </p>
          </div>
        </div>
      )}

      {/* Capture Button */}
      {isGeolocationSupported && !loading && !location && (
        <button
          onClick={captureLocation}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          <MapPin className="w-5 h-5" />
          Capture My Location
        </button>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3">
          <Loader className="w-5 h-5 text-blue-600 animate-spin" />
          <div>
            <p className="font-semibold text-blue-900">Getting your location...</p>
            <p className="text-sm text-blue-700">Please wait while we determine your position.</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900">Location Error</p>
            <p className="text-sm text-red-700">{error}</p>
            <button
              onClick={captureLocation}
              className="mt-2 text-sm text-red-600 hover:text-red-800 font-semibold"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Location Captured */}
      {location && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-green-900">Location Captured</p>
              <div className="mt-2 space-y-1 text-sm text-green-800">
                <p>
                  <span className="font-medium">Coordinates:</span>{' '}
                  {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                </p>
                <p>
                  <span className="font-medium">Accuracy:</span>{' '}
                  {location.accuracy ? `±${location.accuracy.toFixed(0)}m (${getAccuracyLevel(location.accuracy)})` : 'Unknown'}
                </p>
                <p>
                  <span className="font-medium">Time:</span>{' '}
                  {new Date(location.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validation Result */}
      {validation && showValidation && (
        <div className={`border rounded-lg p-4 ${
          validation.valid 
            ? 'bg-green-50 border-green-200' 
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-start gap-3">
            {validation.valid ? (
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            )}
            <div className="flex-1">
              <p className={`font-semibold ${
                validation.valid ? 'text-green-900' : 'text-yellow-900'
              }`}>
                {validation.valid ? 'Location Verified ✓' : 'Location Outside Geofence'}
              </p>
              <div className={`mt-2 space-y-1 text-sm ${
                validation.valid ? 'text-green-800' : 'text-yellow-800'
              }`}>
                <p>
                  <span className="font-medium">Distance from patient:</span>{' '}
                  {validation.distance_feet.toFixed(0)} feet
                </p>
                <p>
                  <span className="font-medium">Allowed radius:</span>{' '}
                  {validation.allowed_radius_feet.toFixed(0)} feet
                </p>
                {!validation.valid && validation.variance_meters > 0 && (
                  <p className="text-yellow-900 font-medium mt-2">
                    ⚠️ You are {validation.variance_meters.toFixed(0)}m outside the allowed area
                  </p>
                )}
                <p className="text-xs mt-2 opacity-75">
                  Accuracy: {validation.accuracy_level}
                </p>
              </div>

              {patientLocation && patientLocation.address && (
                <div className="mt-3 pt-3 border-t border-green-200">
                  <p className="text-xs text-green-700">
                    <span className="font-medium">Patient Address:</span> {patientLocation.address}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recapture Button */}
      {location && (
        <button
          onClick={captureLocation}
          className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors text-sm"
        >
          <MapPin className="w-4 h-4" />
          Capture Location Again
        </button>
      )}
    </div>
  );
};

export default LocationCapture;
