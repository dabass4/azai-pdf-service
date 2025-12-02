import { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, RefreshCw, Download, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminLogs = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [filter]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? `?level=${filter}` : '';
      const response = await axios.get(`${API}/admin/logs${params}`);
      setLogs(response.data);
    } catch (e) {
      console.error('Error fetching logs:', e);
      toast.error('Failed to load system logs');
    } finally {
      setLoading(false);
    }
  };

  const handleExportLogs = async () => {
    try {
      const response = await axios.get(`${API}/admin/logs/export`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `system-logs-${new Date().toISOString()}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Logs exported successfully');
    } catch (e) {
      console.error('Error exporting logs:', e);
      toast.error('Failed to export logs');
    }
  };

  const getLevelColor = (level) => {
    const colors = {
      INFO: 'bg-blue-100 text-blue-800',
      WARNING: 'bg-yellow-100 text-yellow-800',
      ERROR: 'bg-red-100 text-red-800',
      DEBUG: 'bg-gray-100 text-gray-800'
    };
    return colors[level] || colors.INFO;
  };

  const filteredLogs = logs.filter(log =>
    searchTerm === '' || 
    log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.module?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => navigate('/admin')}
            className="text-blue-600 hover:text-blue-800 mb-2"
          >
            ← Back to Admin Dashboard
          </button>
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">System Logs</h1>
              <p className="text-gray-600 mt-1">Monitor application activity and errors</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={fetchLogs}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button onClick={handleExportLogs}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search logs..."
                  className="w-full border border-gray-300 rounded-md p-2"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <select
                  className="border border-gray-300 rounded-md p-2"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="all">All Levels</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                  <option value="DEBUG">Debug</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Log Entries ({filteredLogs.length})</CardTitle>
            <CardDescription>Recent system activity</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center py-8">Loading logs...</p>
            ) : filteredLogs.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No logs found matching your criteria.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {filteredLogs.map((log, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex gap-2 items-center">
                        <Badge className={getLevelColor(log.level)}>
                          {log.level}
                        </Badge>
                        {log.module && (
                          <span className="text-sm text-gray-600">{log.module}</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800 font-mono break-all">{log.message}</p>
                    {log.details && (
                      <details className="mt-2">
                        <summary className="text-xs text-blue-600 cursor-pointer">View Details</summary>
                        <pre className="text-xs bg-gray-100 p-2 rounded mt-2 overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminLogs;