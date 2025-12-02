import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminCredentials = () => {
  const navigate = useNavigate();
  const { organizationId } = useParams();
  const [credentials, setCredentials] = useState({});
  const [formData, setFormData] = useState({
    omes_tpid: '',
    omes_soap_username: '',
    omes_soap_password: '',
    omes_sftp_username: '',
    omes_sftp_password: '',
    availity_api_key: '',
    availity_client_secret: '',
    availity_scope: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    if (organizationId) {
      fetchCredentials();
    }
  }, [organizationId]);

  const fetchCredentials = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${BACKEND_URL}/api/admin/organizations/${organizationId}/credentials`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCredentials(response.data.credentials);
    } catch (err) {
      setError('Failed to load credentials');
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      
      // Filter out empty values
      const updateData = {};
      Object.keys(formData).forEach(key => {
        if (formData[key]) {
          updateData[key] = formData[key];
        }
      });

      await axios.put(
        `${BACKEND_URL}/api/admin/organizations/${organizationId}/credentials`,
        updateData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setSuccess('Credentials updated successfully!');
      fetchCredentials();
      
      // Clear form
      setFormData({
        omes_tpid: '',
        omes_soap_username: '',
        omes_soap_password: '',
        omes_sftp_username: '',
        omes_sftp_password: '',
        availity_api_key: '',
        availity_client_secret: '',
        availity_scope: ''
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update credentials');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (service) => {
    try {
      setTestResults({ ...testResults, [service]: 'testing' });
      const token = localStorage.getItem('token');
      
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/organizations/${organizationId}/test-credentials?service=${service}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setTestResults({ 
        ...testResults, 
        [service]: response.data.success ? 'success' : 'failed',
        [`${service}_message`]: response.data.message
      });
    } catch (err) {
      setTestResults({ 
        ...testResults, 
        [service]: 'failed',
        [`${service}_message`]: err.response?.data?.message || 'Test failed'
      });
    }
  };

  const getTestStatusColor = (status) => {
    if (status === 'success') return 'text-green-600 bg-green-50';
    if (status === 'failed') return 'text-red-600 bg-red-50';
    if (status === 'testing') return 'text-blue-600 bg-blue-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/admin/organizations')}
          className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
        >
          ← Back to Organizations
        </button>

        <h1 className="text-3xl font-bold mb-8">Manage Credentials</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800">{success}</p>
          </div>
        )}

        {/* Current Credentials (Masked) */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Current Credentials</h2>
          <div className="space-y-2">
            {Object.entries(credentials).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium">{key.replace(/_/g, ' ').toUpperCase()}</span>
                <span className="text-gray-600 font-mono">{value || 'Not set'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Update Credentials Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Update Credentials</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* OMES EDI Section */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center justify-between">
                OMES EDI (Ohio Medicaid)
                <button
                  type="button"
                  onClick={() => testConnection('omes_soap')}
                  className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
                >
                  Test SOAP
                </button>
              </h3>
              {testResults.omes_soap && (
                <div className={`mb-3 p-3 rounded ${getTestStatusColor(testResults.omes_soap)}`}>
                  {testResults.omes_soap_message || testResults.omes_soap}
                </div>
              )}
              <div className="space-y-3">
                <input
                  type="text"
                  name="omes_tpid"
                  placeholder="Trading Partner ID (7 digits)"
                  value={formData.omes_tpid}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
                <input
                  type="text"
                  name="omes_soap_username"
                  placeholder="SOAP Username"
                  value={formData.omes_soap_username}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
                <input
                  type="password"
                  name="omes_soap_password"
                  placeholder="SOAP Password"
                  value={formData.omes_soap_password}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
                <div className="flex items-center justify-between">
                  <input
                    type="text"
                    name="omes_sftp_username"
                    placeholder="SFTP Username"
                    value={formData.omes_sftp_username}
                    onChange={handleChange}
                    className="flex-1 mr-2 px-4 py-2 border rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={() => testConnection('omes_sftp')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                  >
                    Test SFTP
                  </button>
                </div>
                {testResults.omes_sftp && (
                  <div className={`p-3 rounded ${getTestStatusColor(testResults.omes_sftp)}`}>
                    {testResults.omes_sftp_message || testResults.omes_sftp}
                  </div>
                )}
                <input
                  type="password"
                  name="omes_sftp_password"
                  placeholder="SFTP Password (or use SSH key)"
                  value={formData.omes_sftp_password}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
            </div>

            <hr />

            {/* Availity Section */}
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center justify-between">
                Availity Clearinghouse
                <button
                  type="button"
                  onClick={() => testConnection('availity')}
                  className="text-sm bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded"
                >
                  Test Connection
                </button>
              </h3>
              {testResults.availity && (
                <div className={`mb-3 p-3 rounded ${getTestStatusColor(testResults.availity)}`}>
                  {testResults.availity_message || testResults.availity}
                </div>
              )}
              <div className="space-y-3">
                <input
                  type="text"
                  name="availity_api_key"
                  placeholder="API Key (Client ID)"
                  value={formData.availity_api_key}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
                <input
                  type="password"
                  name="availity_client_secret"
                  placeholder="Client Secret"
                  value={formData.availity_client_secret}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
                <input
                  type="text"
                  name="availity_scope"
                  placeholder="OAuth Scopes (space-separated)"
                  value={formData.availity_scope}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/admin/organizations')}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Credentials'}
              </button>
            </div>
          </form>
        </div>

        {/* Help Text */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold mb-2">💡 Help</h3>
          <ul className="text-sm space-y-1 text-gray-700">
            <li>• Only fill in fields you want to update</li>
            <li>• Empty fields will not be changed</li>
            <li>• Test connections after updating credentials</li>
            <li>• Credentials are encrypted in database</li>
            <li>• No system restart required</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminCredentials;
