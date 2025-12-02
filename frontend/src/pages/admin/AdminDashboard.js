import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const [healthRes, analyticsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/admin/system/health`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/admin/analytics/overview?days=30`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setHealth(healthRes.data);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
      if (err.response?.status === 403) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    return status === 'healthy' ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-xl">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* System Health */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">System Health</h2>
          {health && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{service}</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
                      {status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {health?.statistics && Object.entries(health.statistics).map(([key, value]) => (
            <div key={key} className="bg-white rounded-lg shadow-md p-6">
              <p className="text-gray-600 text-sm mb-1">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
              <p className="text-3xl font-bold text-blue-600">{value}</p>
            </div>
          ))}
        </div>

        {/* Analytics */}
        {analytics && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Last 30 Days</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border-l-4 border-green-500 pl-4">
                <p className="text-gray-600 text-sm">New Organizations</p>
                <p className="text-2xl font-bold">{analytics.metrics.new_organizations}</p>
              </div>
              <div className="border-l-4 border-blue-500 pl-4">
                <p className="text-gray-600 text-sm">New Users</p>
                <p className="text-2xl font-bold">{analytics.metrics.new_users}</p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <p className="text-gray-600 text-sm">New Timesheets</p>
                <p className="text-2xl font-bold">{analytics.metrics.new_timesheets}</p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/admin/organizations')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            Manage Organizations
          </button>
          <button
            onClick={() => navigate('/admin/credentials')}
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            Manage Credentials
          </button>
          <button
            onClick={() => navigate('/admin/support')}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            Support Tickets
          </button>
          <button
            onClick={() => navigate('/admin/logs')}
            className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            View Logs
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
