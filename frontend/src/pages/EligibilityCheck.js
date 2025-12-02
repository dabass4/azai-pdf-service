import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const EligibilityCheck = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [providerNPI, setProviderNPI] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/patients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPatients(response.data.patients || []);
    } catch (err) {
      console.error('Failed to load patients');
    }
  };

  const checkEligibility = async () => {
    if (!selectedPatient || !providerNPI) {
      setError('Please select a patient and enter Provider NPI');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const patient = patients.find(p => p.id === selectedPatient);

      const requestData = {
        member_id: patient.medicaid_id,
        first_name: patient.first_name,
        last_name: patient.last_name,
        date_of_birth: patient.dob,
        gender: patient.gender,
        provider_npi: providerNPI,
        submission_method: 'omes'
      };

      const response = await axios.post(
        `${BACKEND_URL}/api/claims/eligibility/verify`,
        requestData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Eligibility check failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8\">
      <div className="max-w-4xl mx-auto\">
        <h1 className="text-3xl font-bold mb-8\">Patient Eligibility Verification</h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6\">
          <h2 className="text-xl font-semibold mb-4\">Check Eligibility</h2>

          <div className="space-y-4\">
            <div>
              <label className="block text-sm font-medium mb-1\">Select Patient</label>
              <select
                value={selectedPatient}
                onChange={(e) => setSelectedPatient(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg\"
              >
                <option value=\"\">-- Select Patient --</option>
                {patients.map(patient => (
                  <option key={patient.id} value={patient.id}>
                    {patient.first_name} {patient.last_name} - {patient.medicaid_id}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1\">Provider NPI</label>
              <input
                type=\"text\"
                value={providerNPI}
                onChange={(e) => setProviderNPI(e.target.value)}
                placeholder=\"10-digit NPI\"
                maxLength={10}
                className="w-full px-4 py-2 border rounded-lg\"
              />
            </div>

            <button
              onClick={checkEligibility}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg disabled:opacity-50\"
            >
              {loading ? 'Checking Eligibility...' : 'Check Eligibility'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6\">
            <p className="text-red-800\">{error}</p>
          </div>
        )}

        {result && (
          <div className={`rounded-lg shadow-md p-6 ${result.is_active ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'}`}>
            <h2 className="text-2xl font-bold mb-4 ${result.is_active ? 'text-green-800' : 'text-red-800'}\">
              {result.is_active ? '✓ Patient is Eligible' : '✗ Patient is Not Eligible'}
            </h2>

            <div className="space-y-3\">
              <div className="flex justify-between p-3 bg-white rounded\">
                <span className="font-medium\">Member ID:</span>
                <span>{result.member_id}</span>
              </div>

              {result.eligibility_start_date && (
                <div className="flex justify-between p-3 bg-white rounded\">
                  <span className="font-medium\">Start Date:</span>
                  <span>{new Date(result.eligibility_start_date).toLocaleDateString()}</span>
                </div>
              )}

              {result.eligibility_end_date && (
                <div className="flex justify-between p-3 bg-white rounded\">
                  <span className="font-medium\">End Date:</span>
                  <span>{new Date(result.eligibility_end_date).toLocaleDateString()}</span>
                </div>
              )}

              {result.plan_name && (
                <div className="flex justify-between p-3 bg-white rounded\">
                  <span className="font-medium\">Plan Name:</span>
                  <span>{result.plan_name}</span>
                </div>
              )}

              {result.copay_amount && (
                <div className="flex justify-between p-3 bg-white rounded\">
                  <span className="font-medium\">Copay Amount:</span>
                  <span>${result.copay_amount.toFixed(2)}</span>
                </div>
              )}

              {result.rejection_reason && (
                <div className="p-3 bg-red-100 border border-red-200 rounded\">
                  <span className="font-medium\">Reason:</span> {result.rejection_reason}
                </div>
              )}

              <div className="text-sm text-gray-600 pt-3 border-t\">
                Checked at: {new Date(result.checked_at).toLocaleString()}
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4\">
          <h3 className="font-semibold mb-2\">💡 About Eligibility Checks</h3>
          <ul className="text-sm space-y-1 text-gray-700\">
            <li>• Check patient eligibility before providing services</li>
            <li>• Reduces claim denials due to ineligibility</li>
            <li>• Real-time verification with Ohio Medicaid</li>
            <li>• Results are stored for record-keeping</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default EligibilityCheck;
