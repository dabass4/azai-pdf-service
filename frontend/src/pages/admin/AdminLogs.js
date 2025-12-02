import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminLogs = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    level: 'ERROR',
    limit: 100
  });

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.get(
        `${BACKEND_URL}/api/admin/system/logs?level=${filters.level}&limit=${filters.limit}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setLogs(response.data.logs);
    } catch (err) {
      setError('Failed to load system logs');
    } finally {
      setLoading(false);
    }
  };

  const downloadLogs = () => {
    const logText = logs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-logs-${new Date().toISOString()}.txt`;
    a.click();
  };

  const getLevelColor = (level) => {
    if (level === 'ERROR') return 'bg-red-50 border-red-200 text-red-800';
    if (level === 'WARNING') return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    if (level === 'INFO') return 'bg-blue-50 border-blue-200 text-blue-800';
    if (level === 'CRITICAL') return 'bg-purple-50 border-purple-200 text-purple-800';
    return 'bg-gray-50 border-gray-200 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <button
              onClick={() => navigate('/admin')}
              className="text-blue-600 hover:text-blue-800 mb-2 flex items-center"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold">System Logs</h1>
          </div>
          <button
            onClick={downloadLogs}
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg"
          >
            Download Logs
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Log Level</label>
              <select
                value={filters.level}
                onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg"
              >
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Limit</label>
              <select
                value={filters.limit}
                onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border rounded-lg"
              >
                <option value="50">50 lines</option>
                <option value="100">100 lines</option>
                <option value="200">200 lines</option>
                <option value="500">500 lines</option>
                <option value="1000">1000 lines</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={fetchLogs}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Logs Display */}
        {loading ? (
          <div className="text-center py-8">Loading logs...</div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-4 flex justify-between items-center">
              <h2 className="text-lg font-semibold">
                Showing {logs.length} log entries ({filters.level} level)
              </h2>
              <span className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>

            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {logs.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No logs found</p>
              ) : (
                logs.map((log, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded border font-mono text-sm ${getLevelColor(filters.level)}`}
                  >
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Info */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold mb-2">💡 About Logs</h3>
          <ul className="text-sm space-y-1 text-gray-700">
            <li>• ERROR logs show application errors and exceptions</li>
            <li>• WARNING logs show potential issues</li>
            <li>• INFO logs show general application events</li>
            <li>• CRITICAL logs show severe errors requiring immediate attention</li>
            <li>• Logs are pulled from /var/log/supervisor/backend.err.log</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminLogs;
