import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminOrganizations = () => {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrg, setSelectedOrg] = useState(null);

  useEffect(() => {
    fetchOrganizations();
  }, [searchQuery]);

  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = {};
      if (searchQuery) {
        params.search = searchQuery;
      }

      const response = await axios.get(`${BACKEND_URL}/api/admin/organizations`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });

      setOrganizations(response.data.organizations);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  const viewOrganizationDetails = async (organizationId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${BACKEND_URL}/api/admin/organizations/${organizationId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSelectedOrg(response.data);
    } catch (err) {
      setError('Failed to load organization details');
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      suspended: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8"
      <div className="max-w-7xl mx-auto"
        {/* Header */}
        <div className="flex justify-between items-center mb-8"
          <div>
            <button
              onClick={() => navigate('/admin')}
              className="text-blue-600 hover:text-blue-800 mb-2 flex items-center\"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold"Organizations</h1>
          </div>
          <button
            onClick={() => navigate('/admin/organizations/create')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg\"
          >
            + Create Organization
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6"
            <p className="text-red-800"{error}</p>
          </div>
        )}

        {/* Search */}
        <div className="mb-6"
          <input
            type=\"text\"
            placeholder=\"Search organizations...\"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500\"
          />
        </div>

        {/* Organizations List */}
        {loading ? (
          <div className="text-center py-8"Loading organizations...</div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden"
            <table className="min-w-full divide-y divide-gray-200"
              <thead className="bg-gray-50"
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    Organization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    Users
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    Timesheets
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200"
                {organizations.map((org) => (
                  <tr key={org.organization_id} className="hover:bg-gray-50"
                    <td className="px-6 py-4 whitespace-nowrap"
                      <div>
                        <div className="text-sm font-medium text-gray-900"{org.name}</div>
                        <div className="text-sm text-gray-500"{org.organization_id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap"
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(org.status)}`}>
                        {org.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                      {org.plan || 'free'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                      {org.user_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                      {org.timesheet_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium"
                      <button
                        onClick={() => viewOrganizationDetails(org.organization_id)}
                        className="text-blue-600 hover:text-blue-900 mr-3\"
                      >
                        View
                      </button>
                      <button
                        onClick={() => navigate(`/admin/organizations/${org.organization_id}/credentials`)}
                        className="text-green-600 hover:text-green-900\"
                      >
                        Credentials
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Organization Details Modal */}
        {selectedOrg && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto m-4"
              <div className="p-6"
                <div className="flex justify-between items-center mb-4"
                  <h2 className="text-2xl font-bold"{selectedOrg.organization.name}</h2>
                  <button
                    onClick={() => setSelectedOrg(null)}
                    className="text-gray-500 hover:text-gray-700\"
                  >
                    ✕
                  </button>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
                  <div className="bg-blue-50 p-4 rounded-lg"
                    <p className="text-sm text-gray-600"Users</p>
                    <p className="text-2xl font-bold"{selectedOrg.statistics.users}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg"
                    <p className="text-sm text-gray-600"Patients</p>
                    <p className="text-2xl font-bold"{selectedOrg.statistics.patients}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg"
                    <p className="text-sm text-gray-600"Employees</p>
                    <p className="text-2xl font-bold"{selectedOrg.statistics.employees}</p>
                  </div>
                  <div className="bg-yellow-50 p-4 rounded-lg"
                    <p className="text-sm text-gray-600"Timesheets</p>
                    <p className="text-2xl font-bold"{selectedOrg.statistics.timesheets}</p>
                  </div>
                </div>

                {/* Credentials Status */}
                <div className="mb-6"
                  <h3 className="font-semibold mb-2"Integration Status</h3>
                  <div className="space-y-2"
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded"
                      <span>OMES EDI</span>
                      <span className={`px-3 py-1 rounded-full text-sm ${selectedOrg.credentials_status.omes_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {selectedOrg.credentials_status.omes_configured ? 'Configured' : 'Not Configured'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded"
                      <span>Availity</span>
                      <span className={`px-3 py-1 rounded-full text-sm ${selectedOrg.credentials_status.availity_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {selectedOrg.credentials_status.availity_configured ? 'Configured' : 'Not Configured'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded"
                      <span>Sandata EVV</span>
                      <span className={`px-3 py-1 rounded-full text-sm ${selectedOrg.credentials_status.sandata_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {selectedOrg.credentials_status.sandata_configured ? 'Configured' : 'Not Configured'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Users */}
                <div className="mb-6"
                  <h3 className="font-semibold mb-2"Users</h3>
                  <div className="space-y-2"
                    {selectedOrg.users.map((user) => (
                      <div key={user.id} className="flex items-center justify-between p-3 bg-gray-50 rounded"
                        <div>
                          <p className="font-medium"{user.first_name} {user.last_name}</p>
                          <p className="text-sm text-gray-600"{user.email}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end space-x-3"
                  <button
                    onClick={() => navigate(`/admin/organizations/${selectedOrg.organization.organization_id}/credentials`)}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg\"
                  >
                    Manage Credentials
                  </button>
                  <button
                    onClick={() => setSelectedOrg(null)}
                    className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg\"
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

export default AdminOrganizations;
