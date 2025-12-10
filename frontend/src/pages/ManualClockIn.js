import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import LocationCapture from '../components/LocationCapture';
import { Clock, User, MapPin, Calendar, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Manual Clock In/Out Page
 * 
 * Allows employees to manually clock in/out with GPS geofencing
 * This is separate from PDF scanning - location capture only happens here
 */
const ManualClockIn = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [patients, setPatients] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [location, setLocation] = useState(null);
  const [validation, setValidation] = useState(null);
  const [activeTimesheet, setActiveTimesheet] = useState(null);
  const [clockType, setClockType] = useState('in'); // 'in' or 'out'

  useEffect(() => {
    fetchPatients();
    fetchEmployees();
    checkActiveTimesheet();
  }, []);

  const fetchPatients = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/patients?is_complete=true`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPatients(response.data);
    } catch (error) {
      console.error('Error fetching patients:', error);
      toast.error('Failed to load patients');
    }
  };

  const fetchEmployees = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/employees?is_complete=true`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
      toast.error('Failed to load employees');
    }
  };

  const checkActiveTimesheet = async () => {
    // Check if there's an active (clocked-in but not clocked-out) timesheet
    // This would query your database for timesheets with clock_in but no clock_out
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/timesheets/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data && response.data.timesheet) {
        setActiveTimesheet(response.data.timesheet);
        setClockType('out');
      }
    } catch (error) {
      // No active timesheet, that's ok
      console.log('No active timesheet');
    }
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    setLocation(null);
    setValidation(null);
  };

  const handleEmployeeSelect = (employee) => {
    setSelectedEmployee(employee);
  };

  const handleLocationCaptured = (capturedLocation) => {
    setLocation(capturedLocation);
  };

  const handleValidationComplete = (validationResult) => {
    setValidation(validationResult);
  };

  const handleClockIn = async () => {
    if (!selectedPatient || !selectedEmployee || !location) {
      toast.error('Please select patient, employee, and capture location');
      return;
    }

    if (validation && !validation.valid) {
      const confirm = window.confirm(
        `⚠️ You are ${validation.distance_feet.toFixed(0)} feet from the patient address.\n\n` +
        `This is outside the allowed ${validation.allowed_radius_feet.toFixed(0)} feet radius.\n\n` +
        `A supervisor will need to approve this exception.\n\nContinue?`
      );
      if (!confirm) return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/timesheets/manual-clock-in`,
        {
          patient_id: selectedPatient.id,
          employee_id: selectedEmployee.id,
          location: location,
          validation: validation,
          timestamp: new Date().toISOString()
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      toast.success('Clocked in successfully!');
      setActiveTimesheet(response.data.timesheet);
      setClockType('out');
      
      // Reset for next clock out
      setLocation(null);
      setValidation(null);
    } catch (error) {
      console.error('Clock in error:', error);
      toast.error(error.response?.data?.detail || 'Failed to clock in');
    } finally {
      setLoading(false);
    }
  };

  const handleClockOut = async () => {
    if (!location) {
      toast.error('Please capture your location before clocking out');
      return;
    }

    if (validation && !validation.valid) {
      const confirm = window.confirm(
        `⚠️ You are ${validation.distance_feet.toFixed(0)} feet from the patient address.\n\n` +
        `This is outside the allowed ${validation.allowed_radius_feet.toFixed(0)} feet radius.\n\n` +
        `A supervisor will need to approve this exception.\n\nContinue?`
      );
      if (!confirm) return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/timesheets/manual-clock-out`,
        {
          timesheet_id: activeTimesheet.id,
          location: location,
          validation: validation,
          timestamp: new Date().toISOString()
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      toast.success('Clocked out successfully!');
      navigate('/timesheets');
    } catch (error) {
      console.error('Clock out error:', error);
      toast.error(error.response?.data?.detail || 'Failed to clock out');
    } finally {
      setLoading(false);
    }
  };

  const patientLocation = selectedPatient ? {
    latitude: selectedPatient.address_latitude,
    longitude: selectedPatient.address_longitude,
    address: `${selectedPatient.address_street}, ${selectedPatient.address_city}, ${selectedPatient.address_state} ${selectedPatient.address_zip}`
  } : null;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Manual Clock {clockType === 'in' ? 'In' : 'Out'}
            </h1>
          </div>
          <p className="text-gray-600">
            {clockType === 'in' 
              ? 'Select patient and employee, then capture your location to clock in'
              : 'Capture your location to complete your shift'}
          </p>
        </div>

        {/* Active Timesheet Info */}
        {activeTimesheet && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <p className="font-semibold text-blue-900">Active Shift</p>
                <p className="text-sm text-blue-700">
                  Clocked in at {new Date(activeTimesheet.clock_in_time).toLocaleTimeString()}
                </p>
                <p className="text-sm text-blue-700">
                  Patient: {activeTimesheet.patient_name} | Employee: {activeTimesheet.employee_name}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Patient Selection (Clock In Only) */}
        {clockType === 'in' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <User className="w-5 h-5" />
              Select Patient
            </h2>
            
            {patients.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">
                  No patients with complete profiles found. Please complete patient profiles first.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {patients.map((patient) => (
                  <button
                    key={patient.id}
                    onClick={() => handlePatientSelect(patient)}
                    className={`text-left p-4 border-2 rounded-lg transition-all ${
                      selectedPatient?.id === patient.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-semibold text-gray-900">
                      {patient.first_name} {patient.last_name}
                    </p>
                    <p className="text-sm text-gray-600 flex items-center gap-1 mt-1">
                      <MapPin className="w-3 h-3" />
                      {patient.address_street}, {patient.address_city}
                    </p>
                    {(!patient.address_latitude || !patient.address_longitude) && (
                      <p className="text-xs text-red-600 mt-1">
                        ⚠️ Missing GPS coordinates
                      </p>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Employee Selection (Clock In Only) */}
        {clockType === 'in' && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <User className="w-5 h-5" />
              Select Employee
            </h2>
            
            {employees.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">
                  No employees with complete profiles found.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {employees.map((employee) => (
                  <button
                    key={employee.id}
                    onClick={() => handleEmployeeSelect(employee)}
                    className={`text-left p-4 border-2 rounded-lg transition-all ${
                      selectedEmployee?.id === employee.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-semibold text-gray-900">
                      {employee.first_name} {employee.last_name}
                    </p>
                    <p className="text-sm text-gray-600">{employee.employee_id}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Location Capture */}
        {((clockType === 'in' && selectedPatient && selectedEmployee) || clockType === 'out') && patientLocation && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Capture Your Location
            </h2>
            
            {!patientLocation.latitude || !patientLocation.longitude ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-red-900">Missing GPS Coordinates</p>
                    <p className="text-sm text-red-700">
                      The selected patient's address doesn't have GPS coordinates.
                      Please update the patient profile with latitude and longitude.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <LocationCapture
                patientLocation={patientLocation}
                onLocationCaptured={handleLocationCaptured}
                onValidationComplete={handleValidationComplete}
                showValidation={true}
                allowedRadiusFeet={500}
              />
            )}
          </div>
        )}

        {/* Clock In/Out Button */}
        {location && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <button
              onClick={clockType === 'in' ? handleClockIn : handleClockOut}
              disabled={loading}
              className={
                `w-full py-4 px-6 rounded-lg font-bold text-lg transition-colors ${
                  validation?.valid
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`
              }
            >
              {loading ? (
                'Processing...'
              ) : clockType === 'in' ? (
                validation?.valid ? '✓ Clock In (Location Verified)' : '⚠️ Clock In (Requires Approval)'
              ) : (
                validation?.valid ? '✓ Clock Out (Location Verified)' : '⚠️ Clock Out (Requires Approval)'
              )}
            </button>
            
            {validation && !validation.valid && (
              <p className="text-sm text-yellow-700 text-center mt-2">
                Your location is outside the geofence. A supervisor will need to review this.
              </p>
            )}
          </div>
        )}

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Manual clock in/out requires GPS location verification for EVV compliance.
            If you're uploading a scanned timesheet, location capture is not required.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ManualClockIn;
