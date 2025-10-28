import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Upload, FileText, CheckCircle, XCircle, Clock, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(timesheet.id)}
                        data-testid={`delete-timesheet-${timesheet.id}`}
                      >
                        <Trash2 className="text-red-500" size={18} />
                      </Button>
                    </div>
                  </CardHeader>
                  
                  {timesheet.extracted_data && timesheet.status === "completed" && (
                    <CardContent>
                      <div className="bg-gray-50 rounded-lg p-6 grid grid-cols-1 md:grid-cols-2 gap-4" data-testid={`extracted-data-${timesheet.id}`}>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Employee Name</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.employee_name || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Date</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.date || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Time In</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.time_in || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Time Out</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.time_out || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Hours Worked</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.hours_worked || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Client Name</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.client_name || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Service Code</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.service_code || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Signature</p>
                          <p className="text-sm font-medium text-gray-900">{timesheet.extracted_data.signature || "N/A"}</p>
                        </div>
                      </div>
                      
                      {timesheet.sandata_status === "submitted" && (
                        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg" data-testid={`sandata-success-${timesheet.id}`}>
                          <p className="text-sm text-green-700 font-medium">✓ Successfully submitted to Sandata API</p>
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
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;