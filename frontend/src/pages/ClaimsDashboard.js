import { useState, useEffect } from "react";
import axios from "axios";
import { 
  FileText, Plus, Edit, Trash2, Send, CheckCircle, Clock, X, AlertCircle, 
  Download, FileCode, List, Settings, Square, CheckSquare, Search, 
  UserCheck, FileSearch, Upload, FolderOpen, RefreshCw, DollarSign,
  Activity, TrendingUp, AlertTriangle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { formatDateForDisplay } from "../utils/dateUtils";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClaimsDashboard = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [claims, setClaims] = useState([]);
  const [generated837Claims, setGenerated837Claims] = useState([]);
  const [timesheets, setTimesheets] = useState([]);
  const [selectedTimesheets, setSelectedTimesheets] = useState([]);
  const [enrollmentStatus, setEnrollmentStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Eligibility state
  const [eligibilityForm, setEligibilityForm] = useState({
    member_id: "",
    first_name: "",
    last_name: "",
    date_of_birth: "",
    provider_npi: ""
  });
  const [eligibilityResult, setEligibilityResult] = useState(null);
  
  // Claim status state
  const [claimStatusForm, setClaimStatusForm] = useState({
    claim_number: "",
    patient_member_id: "",
    patient_last_name: "",
    patient_first_name: "",
    patient_dob: "",
    provider_npi: ""
  });
  const [claimStatusResult, setClaimStatusResult] = useState(null);
  
  // SFTP state
  const [sftpFiles, setSftpFiles] = useState({ inbound: [], outbound: [] });
  const [sftpFolder, setSftpFolder] = useState("outbound");

  // Dashboard stats
  const [stats, setStats] = useState({
    totalClaims: 0,
    pendingClaims: 0,
    paidClaims: 0,
    deniedClaims: 0,
    totalAmount: 0
  });

  useEffect(() => {
    fetchClaims();
    fetchGenerated837Claims();
    fetchTimesheets();
    fetchEnrollmentStatus();
    fetchSftpFiles();
  }, []);

  useEffect(() => {
    // Calculate stats from claims
    const total = claims.length;
    const pending = claims.filter(c => c.status === 'pending' || c.status === 'submitted').length;
    const paid = claims.filter(c => c.status === 'paid' || c.status === 'approved').length;
    const denied = claims.filter(c => c.status === 'denied').length;
    const amount = claims.reduce((sum, c) => sum + (c.total_amount || 0), 0);
    
    setStats({
      totalClaims: total,
      pendingClaims: pending,
      paidClaims: paid,
      deniedClaims: denied,
      totalAmount: amount
    });
  }, [claims]);

  const fetchClaims = async () => {
    try {
      const response = await axios.get(`${API}/claims`);
      setClaims(response.data || []);
    } catch (e) {
      console.error("Error fetching claims:", e);
    }
  };

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

  const fetchSftpFiles = async () => {
    try {
      const [inboundRes, outboundRes] = await Promise.all([
        axios.get(`${API}/mock/odm/sftp/list?folder=inbound`),
        axios.get(`${API}/mock/odm/sftp/list?folder=outbound`)
      ]);
      setSftpFiles({
        inbound: inboundRes.data.files || [],
        outbound: outboundRes.data.files || []
      });
    } catch (e) {
      console.error("Error fetching SFTP files:", e);
    }
  };

  // Eligibility Check
  const handleCheckEligibility = async () => {
    if (!eligibilityForm.member_id || !eligibilityForm.first_name || !eligibilityForm.last_name) {
      toast.error("Please fill in required fields (Member ID, First Name, Last Name)");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/mock/odm/soap/eligibility`, {
        ...eligibilityForm,
        provider_npi: eligibilityForm.provider_npi || "1234567890"
      });
      setEligibilityResult(response.data);
      toast.success("Eligibility check completed");
    } catch (e) {
      console.error("Eligibility check error:", e);
      toast.error("Failed to check eligibility");
    } finally {
      setLoading(false);
    }
  };

  // Claim Status Check
  const handleCheckClaimStatus = async () => {
    if (!claimStatusForm.claim_number) {
      toast.error("Please enter a claim number");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/mock/odm/soap/claim-status`, {
        ...claimStatusForm,
        provider_npi: claimStatusForm.provider_npi || "1234567890"
      });
      setClaimStatusResult(response.data);
      toast.success("Claim status retrieved");
    } catch (e) {
      console.error("Claim status error:", e);
      toast.error("Failed to check claim status");
    } finally {
      setLoading(false);
    }
  };

  // Generate 835 Remittance
  const handleGenerate835 = async (claimNumbers, paymentStatus = "paid") => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/mock/odm/sftp/generate-835`, {
        claim_numbers: claimNumbers,
        payment_status: paymentStatus
      });
      toast.success(`835 Remittance generated: ${response.data.filename}`);
      await fetchSftpFiles();
    } catch (e) {
      console.error("Generate 835 error:", e);
      toast.error("Failed to generate 835 remittance");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate837 = async () => {
    if (selectedTimesheets.length === 0) {
      toast.error("Please select at least one timesheet");
      return;
    }

    setLoading(true);
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
    } finally {
      setLoading(false);
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

  const handleDownloadSftpFile = async (filename) => {
    try {
      const response = await axios.get(`${API}/mock/odm/sftp/download/${filename}`);
      
      const blob = new Blob([response.data.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success("File downloaded successfully");
    } catch (e) {
      console.error("Download error:", e);
      toast.error("Failed to download file");
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

  const getStatusBadge = (status) => {
    const styles = {
      draft: "bg-gray-100 text-gray-700",
      generated: "bg-blue-100 text-blue-700",
      submitted: "bg-yellow-100 text-yellow-700",
      pending: "bg-yellow-100 text-yellow-700",
      approved: "bg-green-100 text-green-700",
      paid: "bg-green-100 text-green-700",
      denied: "bg-red-100 text-red-700",
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${styles[status] || styles.draft}`}>
        {status?.charAt(0).toUpperCase() + status?.slice(1)}
      </span>
    );
  };

  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "eligibility", label: "Eligibility Check", icon: UserCheck },
    { id: "generate837", label: "Generate 837P", icon: FileCode },
    { id: "claimStatus", label: "Claim Status", icon: FileSearch },
    { id: "generated", label: "Generated Claims", icon: List },
    { id: "sftp", label: "EDI Files", icon: FolderOpen },
    { id: "enrollment", label: "ODM Enrollment", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50" data-testid="claims-dashboard">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Claims Dashboard
            </h1>
            <p className="text-gray-600 text-sm">Ohio Medicaid 837P Claims Management & EDI Processing</p>
          </div>
          <Button onClick={() => { fetchClaims(); fetchSftpFiles(); }} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200 overflow-x-auto">
          <div className="flex gap-1 min-w-max">
            {tabs.map(tab => (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? "default" : "ghost"}
                onClick={() => setActiveTab(tab.id)}
                size="sm"
                className={`rounded-none ${activeTab === tab.id ? "border-b-2 border-blue-600" : ""}`}
                data-testid={`tab-${tab.id}`}
              >
                <tab.icon className="mr-1.5 h-4 w-4" />
                {tab.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-6" data-testid="dashboard-content">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Total Claims</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.totalClaims}</p>
                    </div>
                    <FileText className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Pending</p>
                      <p className="text-2xl font-bold text-yellow-600">{stats.pendingClaims}</p>
                    </div>
                    <Clock className="h-8 w-8 text-yellow-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Paid</p>
                      <p className="text-2xl font-bold text-green-600">{stats.paidClaims}</p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Total Amount</p>
                      <p className="text-2xl font-bold text-gray-900">${stats.totalAmount.toFixed(2)}</p>
                    </div>
                    <DollarSign className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Claims */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Recent Claims</CardTitle>
              </CardHeader>
              <CardContent>
                {claims.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                    <p>No claims yet. Generate your first 837P claim from timesheets.</p>
                    <Button 
                      className="mt-4" 
                      onClick={() => setActiveTab("generate837")}
                      data-testid="create-first-claim-btn"
                    >
                      Create First Claim
                    </Button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Claim #</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Patient</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Amount</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Status</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {claims.slice(0, 5).map(claim => (
                          <tr key={claim.id} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm font-medium">{claim.claim_number}</td>
                            <td className="px-4 py-3 text-sm">{claim.patient_name}</td>
                            <td className="px-4 py-3 text-sm">${claim.total_amount?.toFixed(2)}</td>
                            <td className="px-4 py-3">{getStatusBadge(claim.status)}</td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {claim.created_at ? new Date(claim.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab("eligibility")}>
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <UserCheck className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold">Check Eligibility</p>
                    <p className="text-sm text-gray-500">Verify patient coverage</p>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab("claimStatus")}>
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <FileSearch className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-semibold">Claim Status</p>
                    <p className="text-sm text-gray-500">Track claim progress</p>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab("generate837")}>
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <FileCode className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p className="font-semibold">Generate 837P</p>
                    <p className="text-sm text-gray-500">Create EDI claims</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Eligibility Check Tab */}
        {activeTab === "eligibility" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="eligibility-content">
            <Card>
              <CardHeader className="bg-blue-50">
                <CardTitle className="flex items-center gap-2">
                  <UserCheck className="h-5 w-5" />
                  Patient Eligibility Check (270/271)
                </CardTitle>
                <CardDescription>
                  Verify patient Medicaid eligibility in real-time
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Medicaid ID *</Label>
                    <Input
                      placeholder="123456789012"
                      value={eligibilityForm.member_id}
                      onChange={(e) => setEligibilityForm(prev => ({ ...prev, member_id: e.target.value }))}
                      data-testid="eligibility-member-id"
                    />
                  </div>
                  <div>
                    <Label>Date of Birth</Label>
                    <Input
                      type="date"
                      value={eligibilityForm.date_of_birth}
                      onChange={(e) => setEligibilityForm(prev => ({ ...prev, date_of_birth: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>First Name *</Label>
                    <Input
                      placeholder="John"
                      value={eligibilityForm.first_name}
                      onChange={(e) => setEligibilityForm(prev => ({ ...prev, first_name: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label>Last Name *</Label>
                    <Input
                      placeholder="Doe"
                      value={eligibilityForm.last_name}
                      onChange={(e) => setEligibilityForm(prev => ({ ...prev, last_name: e.target.value }))}
                    />
                  </div>
                </div>
                <div>
                  <Label>Provider NPI</Label>
                  <Input
                    placeholder="1234567890"
                    value={eligibilityForm.provider_npi}
                    onChange={(e) => setEligibilityForm(prev => ({ ...prev, provider_npi: e.target.value }))}
                  />
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleCheckEligibility}
                  disabled={loading}
                  data-testid="check-eligibility-btn"
                >
                  {loading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                  Check Eligibility
                </Button>
                
                <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded">
                  <strong>Mock Test Patterns:</strong><br/>
                  • IDs ending in 1-5: Active eligibility<br/>
                  • IDs ending in 6-7: Expired coverage<br/>
                  • IDs ending in 8: Managed Care (MCO)<br/>
                  • IDs ending in 9-0: Not found
                </div>
              </CardContent>
            </Card>

            {/* Results Card */}
            <Card>
              <CardHeader>
                <CardTitle>Eligibility Result</CardTitle>
              </CardHeader>
              <CardContent>
                {eligibilityResult ? (
                  <div className="space-y-4">
                    <div className={`p-4 rounded-lg ${eligibilityResult.is_active ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                      <div className="flex items-center gap-2 mb-2">
                        {eligibilityResult.is_active ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : (
                          <AlertCircle className="h-5 w-5 text-red-600" />
                        )}
                        <span className={`font-semibold ${eligibilityResult.is_active ? 'text-green-700' : 'text-red-700'}`}>
                          {eligibilityResult.is_active ? 'ELIGIBLE' : 'NOT ELIGIBLE'}
                        </span>
                      </div>
                      <p className="text-sm">{eligibilityResult.response_message}</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Member ID</p>
                        <p className="font-medium">{eligibilityResult.member_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Plan</p>
                        <p className="font-medium">{eligibilityResult.plan_name || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Start Date</p>
                        <p className="font-medium">{eligibilityResult.eligibility_start_date || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">End Date</p>
                        <p className="font-medium">{eligibilityResult.eligibility_end_date || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Transaction ID</p>
                        <p className="font-medium text-xs">{eligibilityResult.transaction_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Response Code</p>
                        <p className="font-medium">{eligibilityResult.response_code}</p>
                      </div>
                    </div>
                    
                    {eligibilityResult.rejection_reason && (
                      <div className="bg-red-50 p-3 rounded text-sm text-red-700">
                        <strong>Rejection Reason:</strong> {eligibilityResult.rejection_reason}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <UserCheck className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                    <p>Enter patient information and click &quot;Check Eligibility&quot;</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Claim Status Tab */}
        {activeTab === "claimStatus" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="claim-status-content">
            <Card>
              <CardHeader className="bg-purple-50">
                <CardTitle className="flex items-center gap-2">
                  <FileSearch className="h-5 w-5" />
                  Claim Status Inquiry (276/277)
                </CardTitle>
                <CardDescription>
                  Check the status of submitted claims
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                <div>
                  <Label>Claim Number *</Label>
                  <Input
                    placeholder="CLM12345"
                    value={claimStatusForm.claim_number}
                    onChange={(e) => setClaimStatusForm(prev => ({ ...prev, claim_number: e.target.value }))}
                    data-testid="claim-number-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Patient Medicaid ID</Label>
                    <Input
                      placeholder="123456789012"
                      value={claimStatusForm.patient_member_id}
                      onChange={(e) => setClaimStatusForm(prev => ({ ...prev, patient_member_id: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label>Patient DOB</Label>
                    <Input
                      type="date"
                      value={claimStatusForm.patient_dob}
                      onChange={(e) => setClaimStatusForm(prev => ({ ...prev, patient_dob: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Patient First Name</Label>
                    <Input
                      placeholder="John"
                      value={claimStatusForm.patient_first_name}
                      onChange={(e) => setClaimStatusForm(prev => ({ ...prev, patient_first_name: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label>Patient Last Name</Label>
                    <Input
                      placeholder="Doe"
                      value={claimStatusForm.patient_last_name}
                      onChange={(e) => setClaimStatusForm(prev => ({ ...prev, patient_last_name: e.target.value }))}
                    />
                  </div>
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleCheckClaimStatus}
                  disabled={loading}
                  data-testid="check-claim-status-btn"
                >
                  {loading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                  Check Claim Status
                </Button>
                
                <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded">
                  <strong>Mock Test Patterns:</strong><br/>
                  • Claims starting with P: Paid<br/>
                  • Claims starting with D: Denied<br/>
                  • Claims starting with R: Pending review<br/>
                  • Other: Random status
                </div>
              </CardContent>
            </Card>

            {/* Results Card */}
            <Card>
              <CardHeader>
                <CardTitle>Claim Status Result</CardTitle>
              </CardHeader>
              <CardContent>
                {claimStatusResult ? (
                  <div className="space-y-4">
                    <div className={`p-4 rounded-lg ${
                      claimStatusResult.status_category === 'Accepted' ? 'bg-green-50 border border-green-200' :
                      claimStatusResult.status_category === 'Denied' ? 'bg-red-50 border border-red-200' :
                      claimStatusResult.status_category === 'Rejected' ? 'bg-red-50 border border-red-200' :
                      'bg-yellow-50 border border-yellow-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        {claimStatusResult.status_category === 'Accepted' && <CheckCircle className="h-5 w-5 text-green-600" />}
                        {claimStatusResult.status_category === 'Denied' && <X className="h-5 w-5 text-red-600" />}
                        {claimStatusResult.status_category === 'Rejected' && <AlertTriangle className="h-5 w-5 text-red-600" />}
                        {claimStatusResult.status_category === 'Pending' && <Clock className="h-5 w-5 text-yellow-600" />}
                        <span className="font-semibold">
                          {claimStatusResult.status_category} ({claimStatusResult.status_code})
                        </span>
                      </div>
                      <p className="text-sm">{claimStatusResult.status_description}</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Claim Number</p>
                        <p className="font-medium">{claimStatusResult.claim_number}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Payer Control #</p>
                        <p className="font-medium">{claimStatusResult.payer_claim_control_number || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Total Charge</p>
                        <p className="font-medium">${claimStatusResult.total_charge?.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Payment Amount</p>
                        <p className="font-medium text-green-600">
                          ${claimStatusResult.payment_amount?.toFixed(2) || '0.00'}
                        </p>
                      </div>
                      {claimStatusResult.check_number && (
                        <div>
                          <p className="text-gray-500">Check Number</p>
                          <p className="font-medium">{claimStatusResult.check_number}</p>
                        </div>
                      )}
                      {claimStatusResult.adjudication_date && (
                        <div>
                          <p className="text-gray-500">Adjudication Date</p>
                          <p className="font-medium">{claimStatusResult.adjudication_date}</p>
                        </div>
                      )}
                    </div>
                    
                    {claimStatusResult.rejection_reasons?.length > 0 && (
                      <div className="bg-red-50 p-3 rounded text-sm text-red-700">
                        <strong>Rejection Reasons:</strong>
                        <ul className="list-disc ml-4 mt-1">
                          {claimStatusResult.rejection_reasons.map((reason, i) => (
                            <li key={i}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <FileSearch className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                    <p>Enter a claim number and click "Check Claim Status"</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Generate 837P Tab */}
        {activeTab === "generate837" && (
          <div data-testid="generate837-content">
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
                    <FileText className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                    <p>No timesheets available. Upload timesheets first to generate claims.</p>
                  </div>
                ) : (
                  <>
                    <div className="mb-4 flex items-center justify-between">
                      <p className="text-sm text-gray-600">
                        {selectedTimesheets.length} of {timesheets.length} timesheets selected
                      </p>
                      <Button 
                        onClick={handleGenerate837}
                        disabled={selectedTimesheets.length === 0 || loading}
                        data-testid="generate-837-btn"
                      >
                        {loading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <FileCode className="mr-2 h-4 w-4" />}
                        Generate 837P
                      </Button>
                    </div>
                    <div className="max-h-96 overflow-y-auto border rounded">
                      <table className="w-full">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="px-4 py-2 text-left w-12">
                              <input
                                type="checkbox"
                                checked={selectedTimesheets.length === timesheets.length}
                                onChange={() => {
                                  if (selectedTimesheets.length === timesheets.length) {
                                    setSelectedTimesheets([]);
                                  } else {
                                    setSelectedTimesheets(timesheets.map(t => t.id));
                                  }
                                }}
                              />
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Patient</th>
                            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Date</th>
                            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {timesheets.slice(0, 50).map(ts => (
                            <tr key={ts.id} className="border-b hover:bg-gray-50">
                              <td className="px-4 py-2">
                                <input
                                  type="checkbox"
                                  checked={selectedTimesheets.includes(ts.id)}
                                  onChange={() => handleToggleTimesheetSelection(ts.id)}
                                />
                              </td>
                              <td className="px-4 py-2 text-sm">
                                {ts.extracted_data?.client_name || ts.filename}
                              </td>
                              <td className="px-4 py-2 text-sm text-gray-500">
                                {ts.created_at ? new Date(ts.created_at).toLocaleDateString() : 'N/A'}
                              </td>
                              <td className="px-4 py-2">
                                {getStatusBadge(ts.sandata_status || ts.status)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Generated Claims Tab */}
        {activeTab === "generated" && (
          <Card data-testid="generated-claims-content">
            <CardHeader>
              <CardTitle>Generated 837P Claims</CardTitle>
              <CardDescription>View and download previously generated EDI claim files</CardDescription>
            </CardHeader>
            <CardContent>
              {generated837Claims.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <List className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                  <p>No 837P claims generated yet</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Filename</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Created</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Status</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {generated837Claims.map(claim => (
                        <tr key={claim.id} className="border-b hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium">{claim.filename}</td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {claim.created_at ? new Date(claim.created_at).toLocaleString() : 'N/A'}
                          </td>
                          <td className="px-4 py-3">{getStatusBadge(claim.status)}</td>
                          <td className="px-4 py-3">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleDownload837(claim.id)}
                            >
                              <Download className="mr-1 h-4 w-4" />
                              Download
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* SFTP/EDI Files Tab */}
        {activeTab === "sftp" && (
          <div className="space-y-6" data-testid="sftp-content">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FolderOpen className="h-5 w-5" />
                      EDI File Exchange (Mock SFTP)
                    </CardTitle>
                    <CardDescription>View uploaded claims and downloaded responses</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Select value={sftpFolder} onValueChange={setSftpFolder}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="inbound">Inbound (837)</SelectItem>
                        <SelectItem value="outbound">Outbound (835/999)</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button variant="outline" size="sm" onClick={fetchSftpFiles}>
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {sftpFiles[sftpFolder]?.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FolderOpen className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                    <p>No files in {sftpFolder} folder</p>
                    {sftpFolder === "outbound" && (
                      <Button 
                        className="mt-4"
                        onClick={() => handleGenerate835(["TEST001", "TEST002"], "paid")}
                        disabled={loading}
                      >
                        Generate Sample 835
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Filename</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Type</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Size</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Date</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sftpFiles[sftpFolder].map((file, idx) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm font-medium">{file.filename}</td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                file.file_type === '835' ? 'bg-green-100 text-green-700' :
                                file.file_type === '837' ? 'bg-blue-100 text-blue-700' :
                                file.file_type === '999' ? 'bg-purple-100 text-purple-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {file.file_type || (sftpFolder === 'inbound' ? '837' : '835')}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {(file.size_bytes / 1024).toFixed(1)} KB
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {file.created_at || file.uploaded_at ? 
                                new Date(file.created_at || file.uploaded_at).toLocaleString() : 'N/A'}
                            </td>
                            <td className="px-4 py-3">
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => handleDownloadSftpFile(file.filename)}
                              >
                                <Download className="mr-1 h-4 w-4" />
                                Download
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Generate Section */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Generate Mock Responses</CardTitle>
                <CardDescription>Create sample 835 remittance or 999 acknowledgment files</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4">
                  <Button 
                    variant="outline" 
                    onClick={() => handleGenerate835(["CLM001", "CLM002", "CLM003"], "paid")}
                    disabled={loading}
                  >
                    <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                    Generate 835 (Paid)
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => handleGenerate835(["CLM004", "CLM005"], "partial")}
                    disabled={loading}
                  >
                    <AlertCircle className="mr-2 h-4 w-4 text-yellow-500" />
                    Generate 835 (Partial)
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => handleGenerate835(["CLM006"], "denied")}
                    disabled={loading}
                  >
                    <X className="mr-2 h-4 w-4 text-red-500" />
                    Generate 835 (Denied)
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* ODM Enrollment Tab */}
        {activeTab === "enrollment" && (
          <Card data-testid="enrollment-content">
            <CardHeader className="bg-green-50">
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                ODM Trading Partner Enrollment
              </CardTitle>
              <CardDescription>
                Track your enrollment progress with Ohio Department of Medicaid
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {enrollmentStatus ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">
                        {enrollmentStatus.steps_completed || 0}
                      </p>
                      <p className="text-sm text-gray-500">Steps Completed</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-600">
                        {enrollmentStatus.total_steps || 6}
                      </p>
                      <p className="text-sm text-gray-500">Total Steps</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg col-span-2">
                      <p className="text-lg font-semibold text-green-600">
                        {enrollmentStatus.trading_partner_id || 'Not Assigned'}
                      </p>
                      <p className="text-sm text-gray-500">Trading Partner ID</p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    {(enrollmentStatus.enrollment_steps || []).map((step, idx) => (
                      <div key={idx} className="flex items-center gap-4 p-3 border rounded-lg">
                        <div className={`p-2 rounded-full ${step.completed ? 'bg-green-100' : 'bg-gray-100'}`}>
                          {step.completed ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <Clock className="h-5 w-5 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className={`font-medium ${step.completed ? 'text-green-700' : 'text-gray-700'}`}>
                            Step {step.step_number}: {step.name}
                          </p>
                          <p className="text-sm text-gray-500">{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Settings className="mx-auto h-12 w-12 mb-4 text-gray-300" />
                  <p>Loading enrollment status...</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ClaimsDashboard;
