import React from 'react';
import { useNavigate } from 'react-router-dom';

const AdminLogs = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/admin')}
          className="text-blue-600 hover:text-blue-800 mb-4"
        >
          ← Back to Admin Dashboard
        </button>
        <h1 className="text-3xl font-bold mb-8">Logs</h1>
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-lg">Feature under development</p>
        </div>
      </div>
    </div>
  );
};

export default AdminLogs;
