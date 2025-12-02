import React from 'react';
import { useNavigate } from 'react-router-dom';

const AdminDashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/admin/organizations')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            Manage Organizations
          </button>
          <button
            onClick={() => alert('Configure credentials for an organization from the Organizations page')}
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            Manage Credentials
          </button>
          <button
            onClick={() => alert('Support tickets feature coming soon')}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            Support Tickets
          </button>
          <button
            onClick={() => alert('Logs viewer feature coming soon')}
            className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md transition"
          >
            View Logs
          </button>
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Welcome to Admin Panel</h2>
          <ul className="space-y-2">
            <li>• Manage all client organizations</li>
            <li>• Configure OMES/Availity credentials per organization</li>
            <li>• Monitor system health</li>
            <li>• No restart needed to fix client issues</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
