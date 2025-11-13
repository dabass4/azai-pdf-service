import { useState, useEffect } from "react";
import axios from "axios";
import { FileText, Plus, Edit, Trash2, Send, CheckCircle, Clock, X, AlertCircle, Download, FileCode, List, Settings, Square, CheckSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { formatDateForDisplay } from "../utils/dateUtils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Claims = () => {
  const [activeTab, setActiveTab] = useState("generate837");
  const [generated837Claims, setGenerated837Claims] = useState([]);
  const [timesheets, setTimesheets] = useState([]);
  const [selectedTimesheets, setSelectedTimesheets] = useState([]);
  const [enrollmentStatus, setEnrollmentStatus] = useState(null);

  useEffect(() => {
    fetchGenerated837Claims();
    fetchTimesheets();
    fetchEnrollmentStatus();
  }, []);

  const fetchGenerated837Claims = async () => {
    try {
      const response = await axios.get(`${API}/claims/generated`);
      setGenerated837Claims(response.data.claims || []);
    } catch (e) {
      console.error("Error fetching 837P claims:", e);
    }
  };

  const fetchTimesheets = async () => {
    try {
      const response = await axios.get(`${API}/timesheets`);
      setTimesheets(response.data || []);
    } catch (e) {
      console.error("Error fetching timesheets:", e);
    }
  };

  const fetchEnrollmentStatus = async () => {
    try {
      const response = await axios.get(`${API}/enrollment/status`);
      setEnrollmentStatus(response.data);
    } catch (e) {
      console.error("Error fetching enrollment status:", e);
    }
  };

  const handleGenerate837 = async () => {
    if (selectedTimesheets.length === 0) {
      toast.error("Please select at least one timesheet");
      return;
    }

    try {
      const response = await axios.post(`${API}/claims/generate-837`, {
        timesheet_ids: selectedTimesheets
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `837P_claim_${new Date().getTime()}.edi`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success("837P claim generated successfully!");
      setSelectedTimesheets([]);
      await fetchGenerated837Claims();
    } catch (e) {
      console.error("Generate 837 error:", e);
      toast.error(e.response?.data?.detail || "Failed to generate 837P claim");
    }
  };

  const handleDownload837 = async (claimId) => {
    try {
      const response = await axios.get(`${API}/claims/generated/${claimId}/download`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `837P_claim_${claimId}.edi`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success("Claim downloaded successfully");
    } catch (e) {
      console.error("Download error:", e);
      toast.error("Failed to download claim");
    }
  };

  const handleToggleTimesheetSelection = (timesheetId) => {
    setSelectedTimesheets(prev => {
      if (prev.includes(timesheetId)) {
        return prev.filter(id => id !== timesheetId);
      } else {
        return [...prev, timesheetId];
      }
    });
  };

  const handleUpdateEnrollmentStep = async (stepNumber, completed, notes = '') => {
    try {
      await axios.put(`${API}/enrollment/update-step`, {
        step_number: stepNumber,
        completed: completed,
        notes: notes
      });
      toast.success("Enrollment step updated");
      await fetchEnrollmentStatus();
    } catch (e) {
      console.error("Update step error:", e);
      toast.error("Failed to update enrollment step");
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      generated: "bg-blue-100 text-blue-700",
      submitted: "bg-green-100 text-green-700",
      pending: "bg-yellow-100 text-yellow-700",
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${styles[status] || styles.generated}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Ohio Medicaid Claims (837P)
            </h1>
            <p className="text-gray-600">Generate and submit HIPAA 5010-compliant 837 Professional claims</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={activeTab === "generate837" ? "default" : "ghost"}
              onClick={() => setActiveTab("generate837")}
              className={activeTab === "generate837" ? "border-b-2 border-blue-600 rounded-none" : "rounded-none"}
            >
              <FileCode className="mr-2" size={16} />
              Generate 837P
            </Button>
            <Button
              variant={activeTab === "generated" ? "default" : "ghost"}
              onClick={() => setActiveTab("generated")}
              className={activeTab === "generated" ? "border-b-2 border-blue-600 rounded-none" : "rounded-none"}
            >
              <List className="mr-2" size={16} />
              Generated Claims
            </Button>
            <Button
              variant={activeTab === "enrollment" ? "default" : "ghost"}
              onClick={() => setActiveTab("enrollment")}
              className={activeTab === "enrollment" ? "border-b-2 border-blue-600 rounded-none" : "rounded-none"}
            >
              <Settings className="mr-2" size={16} />
              ODM Enrollment
            </Button>
          </div>
        </div>

        {/* Generate 837P Tab */}
        {activeTab === "generate837" && (
          <div>
            <Card className="mb-6">
              <CardHeader className="bg-blue-50">
                <CardTitle>Generate 837P Claim from Timesheets</CardTitle>
                <CardDescription>
                  Select timesheets to generate a HIPAA 5010-compliant 837 Professional claim file for Ohio Medicaid
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {timesheets.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="mx-auto mb-4" size={48} />
                    <p>No timesheets available</p>
                    <p className="text-sm mt-2">Upload and process timesheets first</p>
                  </div>
                ) : (
                  <>
                    <div className="mb-4 flex justify-between items-center">
                      <p className="text-sm text-gray-600">
                        {selectedTimesheets.length} of {timesheets.length} timesheets selected
                      </p>
                      <Button
                        onClick={handleGenerate837}
                        disabled={selectedTimesheets.length === 0}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <FileCode className="mr-2" size={16} />
                        Generate 837P File
                      </Button>
                    </div>

                    <div className="border rounded-lg overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left">
                                <input
                                  type="checkbox"
                                  checked={selectedTimesheets.length === timesheets.length && timesheets.length > 0}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedTimesheets(timesheets.map(t => t.id));
                                    } else {
                                      setSelectedTimesheets([]);
                                    }
                                  }}
                                  className="rounded"
                                />
                              </th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Filename</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Patient</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {timesheets.map((ts) => (
                              <tr key={ts.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3">
                                  <input
                                    type="checkbox"
                                    checked={selectedTimesheets.includes(ts.id)}
                                    onChange={() => handleToggleTimesheetSelection(ts.id)}
                                    className="rounded"
                                  />
                                </td>
                                <td className="px-4 py-3 text-sm">{ts.filename}</td>
                                <td className="px-4 py-3 text-sm">
                                  {ts.extracted_data?.entries?.[0]?.client_name || 'N/A'}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {ts.extracted_data?.week_of ? formatDateForDisplay(ts.extracted_data.week_of) : 'N/A'}
                                </td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                    ts.status === 'completed' ? 'bg-green-100 text-green-700' :
                                    ts.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                                    'bg-gray-100 text-gray-700'
                                  }`}>
                                    {ts.status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-blue-600 flex-shrink-0" size={20} />
                  <div className="text-sm text-blue-900">
                    <p className="font-semibold mb-1">Important Note</p>
                    <p>Generated 837P files are for testing and preparation. To submit claims to Ohio Medicaid in production, you must:</p>
                    <ol className="list-decimal ml-5 mt-2 space-y-1">
                      <li>Complete ODM Trading Partner enrollment</li>
                      <li>Receive your 7-digit Sender/Receiver ID</li>
                      <li>Set up EDI connectivity (SFTP/AS2)</li>
                      <li>Complete end-to-end testing in ODM test environment</li>
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Generated Claims Tab */}
        {activeTab === "generated" && (
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Generated 837P Claims</CardTitle>
                <CardDescription>View and download previously generated claim files</CardDescription>
              </CardHeader>
              <CardContent>
                {generated837Claims.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileCode className="mx-auto mb-4" size={48} />
                    <p>No claims generated yet</p>
                    <p className="text-sm mt-2">Generate your first 837P claim from the Generate tab</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {generated837Claims.map((claim) => (
                      <Card key={claim.id} className="border-l-4 border-blue-500">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="font-semibold text-lg">{claim.claim_data?.claim_id || claim.id.substring(0, 12)}</h3>
                                {getStatusBadge(claim.status)}
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                                <div>
                                  <p className="text-gray-600">Patient</p>
                                  <p className="font-medium">
                                    {claim.claim_data?.patient?.first_name} {claim.claim_data?.patient?.last_name}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-gray-600">Service Lines</p>
                                  <p className="font-medium">{claim.claim_data?.service_lines?.length || 0} services</p>
                                </div>
                                <div>
                                  <p className="text-gray-600">Created</p>
                                  <p className="font-medium">
                                    {new Date(claim.created_at).toLocaleDateString()}
                                  </p>
                                </div>
                              </div>
                            </div>
                            <Button
                              onClick={() => handleDownload837(claim.id)}
                              size="sm"
                              className="bg-blue-600 hover:bg-blue-700"
                            >
                              <Download className="mr-2" size={16} />
                              Download EDI
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* ODM Enrollment Tab */}
        {activeTab === "enrollment" && (
          <div>
            <Card>
              <CardHeader className="bg-purple-50">
                <CardTitle>Ohio Medicaid Trading Partner Enrollment</CardTitle>
                <CardDescription>
                  Complete these steps to become an authorized trading partner with Ohio Department of Medicaid
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {enrollmentStatus && (
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <p className="text-sm text-gray-600">Enrollment Status</p>
                          <p className="text-xl font-bold text-blue-900 capitalize">
                            {enrollmentStatus.enrollment_status.replace('_', ' ')}
                          </p>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-600">Trading Partner ID</p>
                          <p className="text-xl font-bold text-blue-900">
                            {enrollmentStatus.trading_partner_id || 'Not Assigned'}
                          </p>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-600">Progress</p>
                          <p className="text-xl font-bold text-blue-900">
                            {enrollmentStatus.steps?.filter(s => s.completed).length || 0} / {enrollmentStatus.steps?.length || 11}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {enrollmentStatus.steps?.map((step) => (
                        <Card key={step.step_number} className={step.completed ? "border-green-300 bg-green-50" : "border-gray-200"}>
                          <CardContent className="p-4">
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 mt-1">
                                {step.completed ? (
                                  <CheckSquare className="text-green-600" size={20} />
                                ) : (
                                  <Square className="text-gray-400" size={20} />
                                )}
                              </div>
                              <div className="flex-1">
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <h4 className="font-semibold text-gray-900">
                                      Step {step.step_number}: {step.step_name}
                                    </h4>
                                    <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                                  </div>
                                  <Button
                                    size="sm"
                                    variant={step.completed ? "outline" : "default"}
                                    onClick={() => handleUpdateEnrollmentStep(step.step_number, !step.completed)}
                                    className="ml-4"
                                  >
                                    {step.completed ? "Mark Incomplete" : "Mark Complete"}
                                  </Button>
                                </div>
                                {step.completed && step.completed_date && (
                                  <p className="text-xs text-gray-500">
                                    Completed on {new Date(step.completed_date).toLocaleDateString()}
                                  </p>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>

                    <Card className="bg-yellow-50 border-yellow-200 mt-6">
                      <CardContent className="pt-6">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="text-yellow-600 flex-shrink-0" size={20} />
                          <div className="text-sm text-yellow-900">
                            <p className="font-semibold mb-2">Important Resources</p>
                            <ul className="list-disc ml-5 space-y-1">
                              <li>
                                <a href="https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners/content/enrollment-testing" 
                                   target="_blank" rel="noopener noreferrer" 
                                   className="text-blue-600 hover:underline">
                                  ODM Trading Partner Enrollment Guide
                                </a>
                              </li>
                              <li>
                                <a href="https://medicaid.ohio.gov/resources-for-providers/billing/hipaa-5010-implementation/companion-guides/guides" 
                                   target="_blank" rel="noopener noreferrer" 
                                   className="text-blue-600 hover:underline">
                                  Ohio Medicaid Companion Guides (837P)
                                </a>
                              </li>
                              <li>Contact: EDI-TP-Comments@medicaid.ohio.gov for enrollment support</li>
                            </ul>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Claims;
