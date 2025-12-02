import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const ClaimTracking = () => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [checkingStatus, setCheckingStatus] = useState(false);

  useEffect(() => {
    fetchClaims();
  }, [statusFilter]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);

      const response = await axios.get(
        `${BACKEND_URL}/api/claims/list?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setClaims(response.data.claims || []);
    } catch (err) {
      setError('Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  const checkClaimStatus = async (claimId) => {
    setCheckingStatus(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${BACKEND_URL}/api/claims/status/check`,
        { claim_number: claimId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Refresh claims list
      fetchClaims();
      
      alert(`Status: ${response.data.status_description || 'Updated'}`);
    } catch (err) {
      alert('Failed to check status: ' + (err.response?.data?.detail || 'Error'));
    } finally {
      setCheckingStatus(false);
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      ready: 'bg-blue-100 text-blue-800',
      submitted: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
      denied: 'bg-red-100 text-red-800',
      pending: 'bg-orange-100 text-orange-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8\">
      <div className="max-w-7xl mx-auto\">
        <div className="flex justify-between items-center mb-8\">
          <h1 className="text-3xl font-bold\">Claim Tracking</h1>
          <button
            onClick={() => window.location.href = '/claims'}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg\"
          >
            Submit New Claims
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6\">
            <p className="text-red-800\">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6\">
          <div className="flex items-center space-x-4\">
            <label className="font-medium\">Filter by Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg\"
            >
              <option value=\"\">All Statuses</option>
              <option value=\"draft\">Draft</option>
              <option value=\"ready\">Ready</option>
              <option value=\"submitted\">Submitted</option>
              <option value=\"paid\">Paid</option>
              <option value=\"denied\">Denied</option>
            </select>
            <button
              onClick={fetchClaims}
              className="ml-auto bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg\"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Claims List */}
        {loading ? (
          <div className="text-center py-8\">Loading claims...</div>
        ) : claims.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center\">
            <p className="text-gray-500\">No claims found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden\">
            <table className="min-w-full divide-y divide-gray-200\">
              <thead className="bg-gray-50\">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase\">
                    Claim ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase\">
                    Service Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase\">
                    Total Charge
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase\">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase\">
                    Payment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase\">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200\">
                {claims.map((claim) => (
                  <tr key={claim.claim_id} className="hover:bg-gray-50\">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono\">
                      {claim.claim_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm\">
                      {claim.service_date ? new Date(claim.service_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm\">
                      ${claim.total_charge?.toFixed(2) || '0.00'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap\">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(claim.status)}`}>
                        {claim.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm\">
                      {claim.payment_amount ? `$${claim.payment_amount.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2\">
                      <button
                        onClick={() => setSelectedClaim(claim)}
                        className="text-blue-600 hover:text-blue-900\"
                      >
                        View
                      </button>
                      {claim.status === 'submitted' && (
                        <button
                          onClick={() => checkClaimStatus(claim.claim_id)}
                          disabled={checkingStatus}
                          className="text-green-600 hover:text-green-900 disabled:opacity-50\"
                        >
                          Check Status
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Claim Details Modal */}
        {selectedClaim && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50\">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full m-4\">
              <div className="p-6\">
                <div className="flex justify-between items-center mb-4\">
                  <h2 className="text-2xl font-bold\">Claim Details</h2>
                  <button
                    onClick={() => setSelectedClaim(null)}
                    className="text-gray-500 hover:text-gray-700 text-2xl\"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-3\">
                  <div className="flex justify-between p-3 bg-gray-50 rounded\">
                    <span className="font-medium\">Claim ID:</span>
                    <span className="font-mono\">{selectedClaim.claim_id}</span>
                  </div>
                  
                  <div className="flex justify-between p-3 bg-gray-50 rounded\">
                    <span className="font-medium\">Status:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusBadge(selectedClaim.status)}`}>
                      {selectedClaim.status}
                    </span>
                  </div>

                  <div className="flex justify-between p-3 bg-gray-50 rounded\">
                    <span className="font-medium\">Service Date:</span>
                    <span>{selectedClaim.service_date ? new Date(selectedClaim.service_date).toLocaleDateString() : 'N/A'}</span>
                  </div>

                  <div className="flex justify-between p-3 bg-gray-50 rounded\">
                    <span className="font-medium\">Total Charge:</span>
                    <span>${selectedClaim.total_charge?.toFixed(2) || '0.00'}</span>
                  </div>

                  {selectedClaim.payment_amount && (
                    <div className="flex justify-between p-3 bg-green-50 rounded\">
                      <span className="font-medium\">Payment Amount:</span>
                      <span className="text-green-700 font-bold\">${selectedClaim.payment_amount.toFixed(2)}</span>
                    </div>
                  )}

                  {selectedClaim.submission_date && (
                    <div className="flex justify-between p-3 bg-gray-50 rounded\">
                      <span className="font-medium\">Submitted:</span>
                      <span>{new Date(selectedClaim.submission_date).toLocaleString()}</span>
                    </div>
                  )}

                  {selectedClaim.submission_method && (
                    <div className="flex justify-between p-3 bg-gray-50 rounded\">
                      <span className="font-medium\">Method:</span>
                      <span>{selectedClaim.submission_method}</span>
                    </div>
                  )}

                  {selectedClaim.check_number && (
                    <div className="flex justify-between p-3 bg-gray-50 rounded\">
                      <span className="font-medium\">Check Number:</span>
                      <span>{selectedClaim.check_number}</span>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end\">
                  <button
                    onClick={() => setSelectedClaim(null)}
                    className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg\"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClaimTracking;
