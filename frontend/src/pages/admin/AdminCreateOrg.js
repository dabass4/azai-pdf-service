import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminCreateOrg = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    admin_email: '',
    admin_password: '',
    admin_first_name: '',
    admin_last_name: '',
    plan: 'free'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/organizations`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setSuccess(response.data);
      
      // Reset form
      setFormData({
        name: '',
        admin_email: '',
        admin_password: '',
        admin_first_name: '',
        admin_last_name: '',
        plan: 'free'
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/admin/organizations')}
          className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
        >
          ← Back to Organizations
        </button>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold mb-6">Create New Organization</h1>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <h3 className="font-semibold text-green-800 mb-2">✅ Organization Created Successfully!</h3>
              <div className="space-y-2 text-sm">
                <p><strong>Organization ID:</strong> {success.organization_id}</p>
                <p><strong>Organization Name:</strong> {success.organization.name}</p>
                <p><strong>Admin User ID:</strong> {success.admin_user_id}</p>
                <p className="text-green-700 mt-4">
                  The organization admin can now login with the email and password you provided.
                </p>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => navigate(`/admin/organizations/${success.organization_id}/credentials`)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg mr-2"
                >
                  Configure Credentials
                </button>
                <button
                  onClick={() => navigate('/admin/organizations')}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
                >
                  View All Organizations
                </button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Organization Details */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Organization Details</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Organization Name *</label>
                  <input
                    type="text"
                    name="name"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="e.g., Sunrise Healthcare"
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Plan</label>
                  <select
                    name="plan"
                    value={formData.plan}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border rounded-lg"
                  >
                    <option value="free">Free</option>
                    <option value="starter">Starter</option>
                    <option value="professional">Professional</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </div>
              </div>
            </div>

            <hr />

            {/* Admin User Details */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Administrator Account</h2>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">First Name *</label>
                    <input
                      type="text"
                      name="admin_first_name"
                      required
                      value={formData.admin_first_name}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Last Name *</label>
                    <input
                      type="text"
                      name="admin_last_name"
                      required
                      value={formData.admin_last_name}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Email Address *</label>
                  <input
                    type="email"
                    name="admin_email"
                    required
                    value={formData.admin_email}
                    onChange={handleChange}
                    placeholder="admin@organization.com"
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Password *</label>
                  <input
                    type="password"
                    name="admin_password"
                    required
                    value={formData.admin_password}
                    onChange={handleChange}
                    placeholder="Minimum 8 characters"
                    minLength={8}
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    This will be the initial login password for the organization administrator.
                  </p>
                </div>
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-end space-x-3 pt-4">
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
                {loading ? 'Creating...' : 'Create Organization'}
              </button>
            </div>
          </form>

          {/* Help */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold mb-2">💡 What happens next?</h3>
            <ul className="text-sm space-y-1 text-gray-700">
              <li>1. Organization and admin user are created</li>
              <li>2. Admin can login with provided email/password</li>
              <li>3. Configure OMES/Availity credentials for the organization</li>
              <li>4. Organization can start using the system</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminCreateOrg;
