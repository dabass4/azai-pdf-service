import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import { Upload, FileText, CheckCircle, XCircle, Clock, Trash2, Users, Home as HomeIcon, UserCheck, Edit2, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import Patients from "@/pages/Patients";
import Employees from "@/pages/Employees";
import TimesheetEditor from "@/pages/TimesheetEditor";
import Payers from "@/pages/Payers";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Navigation = () => {
  const location = useLocation();
  
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex space-x-8">
            <Link
              to="/"
              className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium ${
                location.pathname === "/" 
                  ? "border-blue-500 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
              data-testid="nav-home"
            >
              <HomeIcon className="mr-2" size={18} />
              Timesheets
            </Link>
            <Link
              to="/patients"
              className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium ${
                location.pathname === "/patients" 
                  ? "border-blue-500 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
              data-testid="nav-patients"
            >
              <Users className="mr-2" size={18} />
              Patients
            </Link>
            <Link
              to="/employees"
              className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium ${
                location.pathname === "/employees" 
                  ? "border-blue-500 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
              data-testid="nav-employees"
            >
              <UserCheck className="mr-2" size={18} />
              Employees
            </Link>
            <Link
              to="/payers"
              className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium ${
                location.pathname === "/payers" 
                  ? "border-blue-500 text-blue-600" 
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
              data-testid="nav-payers"
            >
              <DollarSign className="mr-2" size={18} />
              Payers
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

const Home = () => {
  const [timesheets, setTimesheets] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fetchTimesheets = async () => {
    try {
      const response = await axios.get(`${API}/timesheets`);
      setTimesheets(response.data);
    } catch (e) {
      console.error("Error fetching timesheets:", e);
      toast.error("Failed to load timesheets");
    }
  };

  useEffect(() => {
    fetchTimesheets();
    const interval = setInterval(fetchTimesheets, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (file) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      const response = await axios.post(`${API}/timesheets/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Timesheet uploaded and processing!");
      await fetchTimesheets();
    } catch (e) {
      console.error("Upload error:", e);
      toast.error(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/timesheets/${id}`);
      toast.success("Timesheet deleted");
      await fetchTimesheets();
    } catch (e) {
      console.error("Delete error:", e);
      toast.error("Failed to delete timesheet");
    }
  };

  const getStatusIcon = (status, sandataStatus) => {
    if (status === "failed") return <XCircle className="text-red-500" size={20} />;
    if (status === "processing") return <Clock className="text-blue-500 animate-pulse" size={20} />;
    if (sandataStatus === "submitted") return <CheckCircle className="text-green-500" size={20} />;
    return <CheckCircle className="text-yellow-500" size={20} />;
  };

  const getStatusText = (status, sandataStatus) => {
    if (status === "failed") return "Failed";
    if (status === "processing") return "Processing...";
    if (sandataStatus === "submitted") return "Submitted to Sandata";
    return "Extracted";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Timesheet Scanner
          </h1>
          <p className="text-lg text-gray-600">Upload timesheets and automatically submit to Sandata</p>
        </div>

        {/* Upload Section */}
        <Card className="mb-12 border-2 border-dashed border-blue-200 bg-white/70 backdrop-blur-sm shadow-lg" data-testid="upload-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="text-blue-600" />
              Upload Timesheet
            </CardTitle>
            <CardDescription>Drag and drop or click to upload PDF or image files</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              data-testid="upload-dropzone"
              className={`relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-all ${
                dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-input").click()}
            >
              <input
                id="file-input"
                data-testid="file-input"
                type="file"
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
                disabled={uploading}
              />
              {uploading ? (
                <div className="flex flex-col items-center gap-3">
                  <Clock className="text-blue-600 animate-spin" size={48} />
                  <p className="text-lg font-medium text-gray-700">Uploading and processing...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <FileText className="text-blue-600" size={48} />
                  <p className="text-lg font-medium text-gray-700">Drop your timesheet here</p>
                  <p className="text-sm text-gray-500">or click to browse</p>
                  <p className="text-xs text-gray-400 mt-2">Supports PDF, JPG, PNG</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Timesheets List */}
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Recent Timesheets
          </h2>
          
          {timesheets.length === 0 ? (
            <Card className="bg-white/70 backdrop-blur-sm shadow-lg">
              <CardContent className="py-12 text-center">
                <FileText className="mx-auto text-gray-400 mb-4" size={64} />
                <p className="text-gray-500 text-lg">No timesheets uploaded yet</p>
                <p className="text-gray-400 text-sm mt-2">Upload your first timesheet to get started</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6" data-testid="timesheets-list">
              {timesheets.map((timesheet) => (
                <Card key={timesheet.id} className="bg-white/70 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow" data-testid={`timesheet-${timesheet.id}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(timesheet.status, timesheet.sandata_status)}
                        <div>
                          <CardTitle className="text-lg">{timesheet.filename}</CardTitle>
                          <CardDescription>
                            {getStatusText(timesheet.status, timesheet.sandata_status)} •{" "}
                            {new Date(timesheet.created_at).toLocaleString()}
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Link to={`/timesheet/edit/${timesheet.id}`}>
                          <Button
                            variant="ghost"
                            size="icon"
                            data-testid={`edit-timesheet-${timesheet.id}`}
                            title="Edit timesheet"
                          >
                            <Edit2 className="text-blue-600" size={18} />
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(timesheet.id)}
                          data-testid={`delete-timesheet-${timesheet.id}`}
                          title="Delete timesheet"
                        >
                          <Trash2 className="text-red-500" size={18} />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  
                  {timesheet.extracted_data && timesheet.status === "completed" && (
                    <CardContent>
                      <div className="space-y-6">
                        {/* Client Information */}
                        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                          <p className="text-xs text-blue-700 uppercase font-semibold mb-1">Patient/Client</p>
                          <p className="text-lg font-bold text-blue-900">{timesheet.extracted_data.client_name || "N/A"}</p>
                        </div>

                        {/* Chronological Time Entries */}
                        {timesheet.extracted_data.employee_entries && timesheet.extracted_data.employee_entries.length > 0 && (() => {
                          // Flatten all time entries from all employees and add employee info
                          const allEntries = [];
                          let totalUnits = 0;
                          
                          // Helper function to calculate units from time in and time out
                          const calculateUnits = (timeIn, timeOut, date) => {
                            try {
                              // Parse time strings (e.g., "08:00 AM")
                              const dateStr = date || '2025-01-01'; // Use date or default
                              const timeInDate = new Date(`${dateStr} ${timeIn}`);
                              const timeOutDate = new Date(`${dateStr} ${timeOut}`);
                              
                              // Calculate difference in minutes
                              let diffMinutes = (timeOutDate - timeInDate) / (1000 * 60);
                              
                              // Handle overnight shifts (time out is next day)
                              if (diffMinutes < 0) {
                                diffMinutes += 24 * 60; // Add 24 hours
                              }
                              
                              // Special rounding rule: if > 35 minutes and < 45 minutes, round to 3 units (45 min)
                              if (diffMinutes > 35 && diffMinutes < 45) {
                                return 3;
                              }
                              
                              // Convert minutes to units (1 unit = 15 minutes)
                              const units = Math.round(diffMinutes / 15);
                              return units;
                            } catch (e) {
                              console.error('Error calculating units:', e);
                              return 0;
                            }
                          };
                          
                          timesheet.extracted_data.employee_entries.forEach(employee => {
                            if (employee.time_entries) {
                              employee.time_entries.forEach(entry => {
                                // Calculate units from time in/out
                                const units = calculateUnits(entry.time_in, entry.time_out, entry.date);
                                totalUnits += units;
                                
                                allEntries.push({
                                  ...entry,
                                  employee_name: employee.employee_name,
                                  service_code: employee.service_code,
                                  signature: employee.signature,
                                  units: units
                                });
                              });
                            }
                          });
                          
                          // Sort by date and time
                          allEntries.sort((a, b) => {
                            const dateA = new Date(a.date + ' ' + a.time_in);
                            const dateB = new Date(b.date + ' ' + b.time_in);
                            return dateA - dateB;
                          });

                          return allEntries.length > 0 && (
                            <div data-testid={`chronological-entries-${timesheet.id}`}>
                              <h3 className="text-sm font-semibold text-gray-700 uppercase flex items-center gap-2 mb-3">
                                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                                  {allEntries.length} Total Time Entr{allEntries.length === 1 ? 'y' : 'ies'}
                                </span>
                                <span className="text-gray-500 text-xs">
                                  • {timesheet.extracted_data.employee_entries.length} Employee{timesheet.extracted_data.employee_entries.length !== 1 ? 's' : ''}
                                </span>
                                <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-semibold">
                                  {totalUnits} Total Units
                                </span>
                              </h3>
                              
                              <div className="border border-gray-200 rounded-lg overflow-hidden">
                                <table className="w-full">
                                  <thead className="bg-blue-50">
                                    <tr>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Date</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Employee</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Service Code</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Time In</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Time Out</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Hours</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Units</th>
                                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Signed</th>
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white divide-y divide-gray-200">
                                    {allEntries.map((entry, index) => (
                                      <tr key={index} className="hover:bg-gray-50" data-testid={`chronological-entry-${timesheet.id}-${index}`}>
                                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{entry.date || "N/A"}</td>
                                        <td className="px-4 py-3 text-sm text-gray-900">{entry.employee_name || "N/A"}</td>
                                        <td className="px-4 py-3 text-sm text-gray-700">{entry.service_code || "N/A"}</td>
                                        <td className="px-4 py-3 text-sm text-gray-900">{entry.time_in || "N/A"}</td>
                                        <td className="px-4 py-3 text-sm text-gray-900">{entry.time_out || "N/A"}</td>
                                        <td className="px-4 py-3 text-sm text-gray-700">{entry.hours_worked || "N/A"}</td>
                                        <td className="px-4 py-3 text-sm font-bold text-blue-900">{entry.units}</td>
                                        <td className="px-4 py-3 text-sm text-gray-700">
                                          {entry.signature === "Yes" ? "✓" : "✗"}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                                <div className="bg-gray-50 px-4 py-2 text-xs text-gray-600 border-t border-gray-200">
                                  <span className="font-semibold">Note:</span> 1 unit = 15 minutes (4 units per hour). Time periods greater than 35 minutes are rounded up to 3 units (45 min).
                                </div>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                      
                      {timesheet.sandata_status === "submitted" && (
                        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg" data-testid={`sandata-success-${timesheet.id}`}>
                          <p className="text-sm text-green-700 font-medium">
                            ✓ Successfully submitted timesheet with {timesheet.extracted_data.employee_entries?.length || 0} employee{timesheet.extracted_data.employee_entries?.length === 1 ? '' : 's'} to Sandata API
                          </p>
                        </div>
                      )}
                    </CardContent>
                  )}
                  
                  {timesheet.error_message && (
                    <CardContent>
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg" data-testid={`error-message-${timesheet.id}`}>
                        <p className="text-sm text-red-700">{timesheet.error_message}</p>
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/payers" element={<Payers />} />
          <Route path="/timesheet/edit/:id" element={<TimesheetEditor />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;