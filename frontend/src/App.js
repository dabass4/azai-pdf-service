import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import axios from "axios";
import { Upload, FileText, CheckCircle, XCircle, Clock, Trash2, Users, Home as HomeIcon, UserCheck, Edit2, DollarSign, Menu, X, ClipboardCheck, Activity, Code, Download, LogOut, Settings as SettingsIcon, TrendingUp, Heart, Stethoscope, Shield, Sparkles, ChevronRight, Bell, User, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import SearchFilter from "@/components/SearchFilter";
import BulkActionToolbar from "@/components/BulkActionToolbar";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { NotificationProvider } from "@/contexts/NotificationContext";
import NotificationBell from "@/components/NotificationBell";
import Login from "@/pages/Login";
import Signup from "@/pages/Signup";
import LandingPage from "@/pages/LandingPage";
import Patients from "@/pages/Patients";
import TestForm from "@/pages/TestForm";
import Employees from "@/pages/Employees";
import TimesheetEditor from "@/pages/TimesheetEditor";
import ManualClockIn from "@/pages/ManualClockIn";
import NotificationCenter from "@/pages/NotificationCenter";
import NotificationPreferences from "@/pages/NotificationPreferences";
import Payers from "@/pages/Payers";
import ClaimsDashboard from "@/pages/ClaimsDashboard";
import ClaimsAnalytics from "@/pages/ClaimsAnalytics";
import EVVManagement from "@/pages/EVVManagement";
import ServiceCodes from "@/pages/ServiceCodes";
import BillingCodes from "@/pages/BillingCodes";
import Settings from "@/pages/Settings";
import { formatDateForDisplay} from "./utils/dateUtils";

// Admin pages
import AdminDashboard from "@/pages/admin/AdminDashboard";
import AdminOrganizations from "@/pages/admin/AdminOrganizations";
import AdminCredentials from "@/pages/admin/AdminCredentials";
import AdminSupport from "@/pages/admin/AdminSupport";
import AdminLogs from "@/pages/admin/AdminLogs";
import AdminCreateOrg from "@/pages/admin/AdminCreateOrg";

// Claims pages
import EligibilityCheck from "@/pages/EligibilityCheck";
import ClaimTracking from "@/pages/ClaimTracking";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Navigation = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, organization, logout, isAuthenticated } = useAuth();
  
  const navLinks = [
    { to: "/", icon: LayoutDashboard, label: "Timesheets" },
    { to: "/patients", icon: Users, label: "Patients" },
    { to: "/employees", icon: UserCheck, label: "Employees" },
    { to: "/payers", icon: DollarSign, label: "Payers" },
    { to: "/claims", icon: ClipboardCheck, label: "Claims" },
    { to: "/claims/analytics", icon: TrendingUp, label: "Analytics" },
    { to: "/evv", icon: Activity, label: "EVV" },
    { to: "/service-codes", icon: Code, label: "Codes" },
    { to: "/settings", icon: SettingsIcon, label: "Settings" }
  ];
  
  return (
    <nav className="nav-glass sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl gradient-teal flex items-center justify-center shadow-lg glow-teal">
                <Heart className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full pulse-dot"></div>
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold gradient-text">AZAI Health</h1>
              <p className="text-xs text-gray-500">Healthcare Management</p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-1">
            {navLinks.map(({ to, icon: Icon, label }) => (
              <Link
                key={to}
                to={to}
                className={`nav-link flex items-center gap-2 ${
                  location.pathname === to ? "active" : ""
                }`}
                data-testid={`nav-${label.toLowerCase()}`}
              >
                <Icon size={16} />
                <span>{label}</span>
              </Link>
            ))}
          </div>

          {/* User Info & Actions */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center gap-4">
              <NotificationBell />
              
              <div className="flex items-center gap-3 glass-card px-4 py-2 rounded-xl">
                <div className="w-9 h-9 rounded-lg gradient-purple flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-white">{user?.first_name} {user?.last_name}</p>
                  <p className="text-xs text-gray-400">{organization?.name}</p>
                </div>
              </div>
              
              <button
                onClick={() => {
                  logout();
                  toast.success('Logged out successfully');
                }}
                className="p-2.5 rounded-xl glass-card hover:bg-red-500/20 transition-all duration-300 group"
                title="Logout"
              >
                <LogOut size={18} className="text-gray-400 group-hover:text-red-400 transition-colors" />
              </button>
            </div>
          )}

          {/* Mobile menu button */}
          <div className="lg:hidden flex items-center gap-3">
            {isAuthenticated && <NotificationBell />}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl glass-card text-gray-400 hover:text-white transition-colors"
              data-testid="mobile-menu-button"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-white/5 animate-slide-up">
            <div className="space-y-1 stagger-children">
              {navLinks.map(({ to, icon: Icon, label }) => (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                    location.pathname === to
                      ? "bg-teal-500/20 text-teal-400"
                      : "text-gray-400 hover:bg-white/5 hover:text-white"
                  }`}
                  data-testid={`mobile-nav-${label.toLowerCase()}`}
                >
                  <Icon size={20} />
                  <span className="font-medium">{label}</span>
                  <ChevronRight size={16} className="ml-auto opacity-50" />
                </Link>
              ))}
            </div>
            
            {isAuthenticated && (
              <div className="mt-4 pt-4 border-t border-white/5">
                <div className="flex items-center gap-3 px-4 py-3 glass-card rounded-xl mb-3">
                  <div className="w-10 h-10 rounded-lg gradient-purple flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{user?.first_name} {user?.last_name}</p>
                    <p className="text-xs text-gray-400">{organization?.name}</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                    toast.success('Logged out successfully');
                  }}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all"
                >
                  <LogOut size={18} />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center healthcare-pattern">
        <div className="text-center glass-card p-8 rounded-2xl animate-fade-in">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl gradient-teal flex items-center justify-center glow-teal">
            <Heart className="w-8 h-8 text-white animate-pulse" />
          </div>
          <div className="w-12 h-12 mx-auto mb-4">
            <svg className="animate-spin" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <p className="text-gray-400">Loading your healthcare dashboard...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/landing" replace />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

const Home = () => {
  const [timesheets, setTimesheets] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [searchFilters, setSearchFilters] = useState({});
  const [selectedTimesheets, setSelectedTimesheets] = useState([]);
  const autoRefreshRef = useRef(true); // Track if auto-refresh should preserve selection

  const fetchTimesheets = useCallback(async (preserveSelection = false) => {
    try {
      const params = new URLSearchParams();
      if (searchFilters.search) params.append('search', searchFilters.search);
      if (searchFilters.date_from) params.append('date_from', searchFilters.date_from);
      if (searchFilters.date_to) params.append('date_to', searchFilters.date_to);
      if (searchFilters.submission_status) params.append('submission_status', searchFilters.submission_status);
      
      const response = await axios.get(`${API}/timesheets?${params.toString()}`);
      setTimesheets(response.data);
      
      // Only clear selection on user-initiated refresh, not auto-refresh
      if (!preserveSelection) {
        setSelectedTimesheets([]);
      } else {
        // Filter out any selected IDs that no longer exist in the new data
        const currentIds = response.data.map(ts => ts.id);
        setSelectedTimesheets(prev => prev.filter(id => currentIds.includes(id)));
      }
    } catch (e) {
      console.error("Error fetching timesheets:", e);
      toast.error("Failed to load timesheets");
    }
  }, [searchFilters]);

  // Initial load and filter changes
  useEffect(() => {
    fetchTimesheets(true); // Preserve selection, handleSearch already clears it
  }, [searchFilters, fetchTimesheets]);

  // Auto-refresh with selection preservation
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTimesheets(true); // Always preserve selection on auto-refresh
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchTimesheets]);

  const handleFileUpload = async (file) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      const response = await axios.post(`${API}/timesheets/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      // Check if it's a batch upload response
      if (response.data.message && response.data.total_pages > 1) {
        toast.success(`Batch upload complete! ${response.data.total_pages} pages processed as separate timesheets.`);
      } else {
        toast.success("Timesheet uploaded and processing!");
      }
      
      await fetchTimesheets(false);
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
      await fetchTimesheets(false);
    } catch (e) {
      console.error("Delete error:", e);
      toast.error("Failed to delete timesheet");
    }
  };

  const handleSearch = (filters) => {
    setSearchFilters(filters);
    setSelectedTimesheets([]); // Clear selection when user changes filters
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (searchFilters.search) params.append('search', searchFilters.search);
      if (searchFilters.date_from) params.append('date_from', searchFilters.date_from);
      if (searchFilters.date_to) params.append('date_to', searchFilters.date_to);
      if (searchFilters.submission_status) params.append('submission_status', searchFilters.submission_status);
      params.append('format', 'csv');
      
      // Create download link
      const downloadUrl = `${API}/timesheets/export?${params.toString()}`;
      window.open(downloadUrl, '_blank');
      toast.success("Export started! Check your downloads.");
    } catch (e) {
      console.error("Export error:", e);
      toast.error("Failed to export timesheets");
    }
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedTimesheets(timesheets.map(t => t.id));
    } else {
      setSelectedTimesheets([]);
    }
  };

  const handleSelectTimesheet = (timesheetId, checked) => {
    if (checked) {
      setSelectedTimesheets(prev => [...prev, timesheetId]);
    } else {
      setSelectedTimesheets(prev => prev.filter(id => id !== timesheetId));
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${selectedTimesheets.length} timesheet(s)? This cannot be undone.`)) return;
    
    try {
      await axios.post(`${API}/timesheets/bulk-delete`, {
        ids: selectedTimesheets
      });
      toast.success(`${selectedTimesheets.length} timesheet(s) deleted`);
      setSelectedTimesheets([]); // Clear selection after deletion
      await fetchTimesheets(false);
    } catch (e) {
      console.error("Bulk delete error:", e);
      toast.error("Failed to bulk delete timesheets");
    }
  };

  const handleBulkSubmitSandata = async () => {
    if (!window.confirm(`Submit ${selectedTimesheets.length} timesheet(s) to Sandata API?`)) return;
    
    try {
      const response = await axios.post(`${API}/timesheets/bulk-submit-sandata`, {
        ids: selectedTimesheets
      });
      
      const { success_count, failed_count } = response.data;
      
      if (success_count > 0) {
        toast.success(`${success_count} timesheet(s) submitted to Sandata successfully`);
      }
      if (failed_count > 0) {
        toast.error(`${failed_count} timesheet(s) failed to submit. Check profiles are complete.`);
      }
      
      setSelectedTimesheets([]); // Clear selection after submission
      await fetchTimesheets(false);
    } catch (e) {
      console.error("Bulk Sandata submission error:", e);
      toast.error("Failed to submit timesheets to Sandata");
    }
  };

  const handleBulkSubmitClaims = async () => {
    if (!window.confirm(`Submit ${selectedTimesheets.length} claim(s) to Ohio Medicaid?`)) return;
    
    try {
      // Get selected timesheets data
      const selectedTimesheetData = timesheets.filter(ts => selectedTimesheets.includes(ts.id));
      
      // Check if all selected timesheets have required data
      const missingData = selectedTimesheetData.filter(ts => 
        !ts.patient_id || ts.sandata_status !== "submitted"
      );
      
      if (missingData.length > 0) {
        toast.error(`${missingData.length} timesheet(s) must be submitted to Sandata first before creating claims`);
        return;
      }
      
      let successCount = 0;
      let failedCount = 0;
      
      // Create claims for each timesheet
      for (const timesheet of selectedTimesheetData) {
        try {
          await axios.post(`${API}/claims`, {
            patient_id: timesheet.patient_id,
            payer_id: timesheet.payer_id || "", // May need to select payer
            timesheet_ids: [timesheet.id],
            status: "pending"
          });
          successCount++;
        } catch (e) {
          failedCount++;
          console.error(`Failed to create claim for timesheet ${timesheet.id}:`, e);
        }
      }
      
      if (successCount > 0) {
        toast.success(`${successCount} claim(s) submitted to Ohio Medicaid successfully`);
      }
      if (failedCount > 0) {
        toast.error(`${failedCount} claim(s) failed to submit`);
      }
      
      setSelectedTimesheets([]); // Clear selection after claims submission
      await fetchTimesheets(false);
    } catch (e) {
      console.error("Bulk claims submission error:", e);
      toast.error("Failed to submit claims to Medicaid");
    }
  };

  const handleBulkExport = async () => {
    try {
      // Build query with selected timesheet IDs
      const selectedTimesheetData = timesheets.filter(ts => selectedTimesheets.includes(ts.id));
      
      if (selectedTimesheetData.length === 0) {
        toast.error("No timesheets selected for export");
        return;
      }
      
      // Create CSV content manually for selected timesheets
      const params = new URLSearchParams();
      params.append('format', 'csv');
      
      // Apply current filters and add export trigger
      if (searchFilters.search) params.append('search', searchFilters.search);
      if (searchFilters.date_from) params.append('date_from', searchFilters.date_from);
      if (searchFilters.date_to) params.append('date_to', searchFilters.date_to);
      if (searchFilters.submission_status) params.append('submission_status', searchFilters.submission_status);
      
      const downloadUrl = `${API}/timesheets/export?${params.toString()}`;
      window.open(downloadUrl, '_blank');
      
      toast.success(`Exporting ${selectedTimesheets.length} timesheet(s) to CSV`);
    } catch (e) {
      console.error("Bulk export error:", e);
      toast.error("Failed to export timesheets");
    }
  };

  const getStatusIcon = (status, sandataStatus) => {
    if (status === "failed") return <XCircle className="text-red-400" size={18} />;
    if (status === "processing") return <Clock className="text-blue-400 animate-pulse" size={18} />;
    if (sandataStatus === "submitted") return <CheckCircle className="text-green-400" size={18} />;
    if (sandataStatus === "blocked") return <XCircle className="text-amber-400" size={18} />;
    return <CheckCircle className="text-teal-400" size={18} />;
  };

  const getStatusText = (status, sandataStatus) => {
    if (status === "failed") return "Failed";
    if (status === "processing") return "Processing...";
    if (sandataStatus === "submitted") return "Submitted to Sandata";
    if (sandataStatus === "blocked") return "Blocked - Incomplete Profiles";
    return "Extracted";
  };

  const getStatusBadgeClass = (status, sandataStatus) => {
    if (status === "failed") return "status-error";
    if (status === "processing") return "status-processing";
    if (sandataStatus === "submitted") return "status-completed";
    if (sandataStatus === "blocked") return "status-pending";
    return "status-completed";
  };

  // Calculate stats
  const stats = {
    total: timesheets.length,
    completed: timesheets.filter(t => t.status === 'completed').length,
    processing: timesheets.filter(t => t.status === 'processing').length,
    submitted: timesheets.filter(t => t.sandata_status === 'submitted').length,
  };

  return (
    <div className="min-h-screen healthcare-pattern">
      {/* Animated background */}
      <div className="animated-bg"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-4 mb-2">
            <div className="icon-container">
              <Stethoscope className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Timesheet Dashboard
              </h1>
              <p className="text-gray-400">Manage and track your healthcare timesheets</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <FileText className="w-5 h-5 text-teal-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">Total</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.total}</p>
            <p className="text-sm text-gray-400">Timesheets</p>
          </div>
          
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">Completed</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.completed}</p>
            <p className="text-sm text-gray-400">Processed</p>
          </div>
          
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <Clock className="w-5 h-5 text-blue-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">In Progress</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.processing}</p>
            <p className="text-sm text-gray-400">Processing</p>
          </div>
          
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <Shield className="w-5 h-5 text-purple-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">Submitted</span>
            </div>
            <p className="text-3xl font-bold text-white">{stats.submitted}</p>
            <p className="text-sm text-gray-400">To Sandata</p>
          </div>
        </div>

        {/* Upload Section */}
        <div className="glass-card rounded-2xl p-6 mb-8 animate-slide-up" data-testid="upload-card">
          <div className="flex items-center gap-3 mb-4">
            <div className="icon-container">
              <Upload className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Upload Timesheet</h2>
              <p className="text-sm text-gray-400">Drag and drop or click to upload PDF or image files</p>
            </div>
          </div>
          
          <div
            data-testid="upload-dropzone"
            className={`upload-zone ${dragActive ? "dragging" : ""}`}
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
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl gradient-teal flex items-center justify-center glow-teal">
                  <Clock className="w-8 h-8 text-white animate-spin" />
                </div>
                <p className="text-lg font-medium text-white">Uploading and processing...</p>
                <div className="w-48 progress-bar">
                  <div className="progress-bar-fill" style={{width: '60%'}}></div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl gradient-border flex items-center justify-center healthcare-float">
                  <FileText className="w-8 h-8 text-teal-400" />
                </div>
                <p className="text-lg font-medium text-white">Drop your timesheet here</p>
                <p className="text-sm text-gray-400">or click to browse</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="px-3 py-1 rounded-full text-xs bg-white/5 text-gray-400 border border-white/10">PDF</span>
                  <span className="px-3 py-1 rounded-full text-xs bg-white/5 text-gray-400 border border-white/10">JPG</span>
                  <span className="px-3 py-1 rounded-full text-xs bg-white/5 text-gray-400 border border-white/10">PNG</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mb-6">
          <SearchFilter
            onSearch={handleSearch}
            placeholder="Search by client name, patient ID, or employee..."
            filters={{
              date_from: {
                type: "date",
                label: "From Date",
                placeholder: "Start date"
              },
              date_to: {
                type: "date",
                label: "To Date",
                placeholder: "End date"
              },
              submission_status: {
                type: "select",
                label: "Submission Status",
                placeholder: "Filter by status",
                options: [
                  { value: "pending", label: "Pending" },
                  { value: "submitted", label: "Submitted" },
                  { value: "failed", label: "Failed" }
                ]
              }
            }}
          />
        </div>

        {/* Bulk Actions Toolbar */}
        <BulkActionToolbar
          selectedCount={selectedTimesheets.length}
          onClearSelection={() => setSelectedTimesheets([])}
          actions={[
            {
              label: "Transmit to Sandata",
              icon: Upload,
              onClick: handleBulkSubmitSandata,
              variant: "default",
              show: selectedTimesheets.length > 0
            },
            {
              label: "Submit Claims to Medicaid",
              icon: ClipboardCheck,
              onClick: handleBulkSubmitClaims,
              variant: "default",
              show: selectedTimesheets.length > 0
            },
            {
              label: "Export CSV",
              icon: Download,
              onClick: handleBulkExport,
              variant: "outline",
              show: selectedTimesheets.length > 0
            },
            {
              label: "Delete Selected",
              icon: Trash2,
              onClick: handleBulkDelete,
              variant: "destructive",
              show: selectedTimesheets.length > 0
            }
          ]}
        />

        {/* Timesheets List */}
        <div className="glass-card rounded-2xl p-6 animate-slide-up">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="icon-container-sm">
                <FileText className="w-5 h-5 text-teal-400" />
              </div>
              <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Recent Timesheets
              </h2>
            </div>
            <span className="text-sm text-gray-400">{timesheets.length} total</span>
          </div>
          
          {timesheets.length === 0 ? (
            <div className="py-16 text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-white/5 flex items-center justify-center">
                <FileText className="w-10 h-10 text-gray-600" />
              </div>
              <p className="text-gray-400 text-lg mb-2">No timesheets uploaded yet</p>
              <p className="text-gray-500 text-sm">Upload your first timesheet to get started</p>
            </div>
          ) : (
            <>
              {/* Select All Checkbox */}
              <div className="mb-4 flex items-center gap-3 px-2">
                <Checkbox
                  checked={selectedTimesheets.length === timesheets.length && timesheets.length > 0}
                  onCheckedChange={handleSelectAll}
                  id="select-all-timesheets"
                  className="border-gray-600"
                />
                <label htmlFor="select-all-timesheets" className="text-sm font-medium text-gray-400 cursor-pointer">
                  Select All ({timesheets.length})
                </label>
              </div>
              
              <div className="space-y-3" data-testid="timesheets-list">
                {timesheets.map((timesheet, index) => (
                  <div 
                    key={timesheet.id} 
                    className="glass-card-hover rounded-xl p-4 animate-slide-up"
                    style={{ animationDelay: `${index * 0.05}s` }}
                    data-testid={`timesheet-${timesheet.id}`}
                  >
                    <div className="flex items-center gap-4">
                      {/* Selection Checkbox */}
                      <Checkbox
                        checked={selectedTimesheets.includes(timesheet.id)}
                        onCheckedChange={(checked) => handleSelectTimesheet(timesheet.id, checked)}
                        className="border-gray-600"
                      />
                      
                      {/* Status Icon */}
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        timesheet.status === 'failed' ? 'bg-red-500/20' :
                        timesheet.status === 'processing' ? 'bg-blue-500/20' :
                        timesheet.sandata_status === 'submitted' ? 'bg-green-500/20' :
                        'bg-teal-500/20'
                      }`}>
                        {getStatusIcon(timesheet.status, timesheet.sandata_status)}
                      </div>
                      
                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-medium truncate">{timesheet.filename}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`status-badge ${getStatusBadgeClass(timesheet.status, timesheet.sandata_status)}`}>
                            {getStatusText(timesheet.status, timesheet.sandata_status)}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(timesheet.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <Link to={`/timesheet/edit/${timesheet.id}`}>
                          <button
                            className="p-2 rounded-lg bg-white/5 hover:bg-teal-500/20 text-gray-400 hover:text-teal-400 transition-all"
                            data-testid={`edit-timesheet-${timesheet.id}`}
                            title="Edit timesheet"
                          >
                            <Edit2 size={16} />
                          </button>
                        </Link>
                        <button
                          className="p-2 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                          onClick={() => handleDelete(timesheet.id)}
                          data-testid={`delete-timesheet-${timesheet.id}`}
                          title="Delete timesheet"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  
                    {timesheet.extracted_data && timesheet.status === "completed" && (
                      <div className="mt-4 pt-4 border-t border-white/5">
                        {/* Client Information */}
                        <div className="glass-card rounded-lg p-4 mb-4">
                          <p className="text-xs text-teal-400 uppercase font-semibold mb-1 flex items-center gap-2">
                            <Heart size={12} />
                            Patient/Client
                          </p>
                          <p className="text-lg font-bold text-white">{timesheet.extracted_data.client_name || "N/A"}</p>
                        </div>

                        {/* Chronological Time Entries */}
                        {timesheet.extracted_data.employee_entries && timesheet.extracted_data.employee_entries.length > 0 && (() => {
                          // Flatten all time entries from all employees and add employee info
                          const allEntries = [];
                          let totalUnits = 0;
                          
                          // Helper function to calculate units from time in and time out
                          const calculateUnits = (timeIn, timeOut, date) => {
                            try {
                              if (!timeIn || !timeOut) return 0;
                              
                              // Parse time strings (e.g., "08:00 AM")
                              const dateStr = date || '2025-01-01';
                              const timeInDate = new Date(`${dateStr} ${timeIn}`);
                              const timeOutDate = new Date(`${dateStr} ${timeOut}`);
                            
                            if (isNaN(timeInDate.getTime()) || isNaN(timeOutDate.getTime())) {
                              return 0;
                            }
                            
                            let diffMinutes = (timeOutDate - timeInDate) / (1000 * 60);
                            
                            if (diffMinutes < 0) {
                              diffMinutes += 24 * 60;
                            }
                            
                            if (isNaN(diffMinutes) || !isFinite(diffMinutes)) {
                              return 0;
                            }
                            
                            if (diffMinutes > 35 && diffMinutes < 45) {
                              return 3;
                            }
                            
                            const units = Math.round(diffMinutes / 15);
                            return isNaN(units) ? 0 : units;
                          } catch (e) {
                            console.error('Error calculating units:', e);
                            return 0;
                          }
                        };
                        
                          let entryIndex = 0;
                          timesheet.extracted_data.employee_entries.forEach(employee => {
                            if (employee.time_entries) {
                              employee.time_entries.forEach(entry => {
                                const units = entry.units || calculateUnits(entry.time_in, entry.time_out, entry.date);
                                totalUnits += (isNaN(units) ? 0 : units);
                                
                                allEntries.push({
                                  ...entry,
                                  employee_name: employee.employee_name,
                                  service_code: employee.service_code,
                                  signature: employee.signature,
                                  units: isNaN(units) ? 0 : units,
                                  scan_order: entryIndex++
                                });
                              });
                            }
                          });

                          return allEntries.length > 0 && (
                            <div data-testid={`chronological-entries-${timesheet.id}`}>
                              <div className="flex items-center gap-3 mb-3">
                                <span className="px-3 py-1 rounded-full text-xs bg-teal-500/20 text-teal-400 border border-teal-500/30">
                                  {allEntries.length} Time Entr{allEntries.length === 1 ? 'y' : 'ies'}
                                </span>
                                <span className="text-xs text-gray-500">
                                  • {timesheet.extracted_data.employee_entries.length} Employee{timesheet.extracted_data.employee_entries.length !== 1 ? 's' : ''}
                                </span>
                                <span className="px-3 py-1 rounded-full text-xs bg-purple-500/20 text-purple-400 border border-purple-500/30 font-semibold">
                                  {isNaN(totalUnits) ? 0 : totalUnits} Units
                                </span>
                              </div>
                              
                              <div className="overflow-x-auto rounded-lg border border-white/10">
                                <table className="modern-table">
                                  <thead>
                                    <tr>
                                      <th>Date</th>
                                      <th>Employee</th>
                                      <th>Code</th>
                                      <th>Time In</th>
                                      <th>Time Out</th>
                                      <th>Hours</th>
                                      <th>Units</th>
                                      <th>Signed</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {allEntries.map((entry, index) => (
                                      <tr key={index} data-testid={`chronological-entry-${timesheet.id}-${index}`}>
                                        <td className="text-white font-medium">{formatDateForDisplay(entry.date)}</td>
                                        <td className="text-gray-300">{entry.employee_name || "N/A"}</td>
                                        <td className="text-gray-400">{entry.service_code || "N/A"}</td>
                                        <td className="text-teal-400 font-medium">{entry.time_in || "N/A"}</td>
                                        <td className="text-teal-400 font-medium">{entry.time_out || "N/A"}</td>
                                        <td className="text-white font-semibold">{entry.formatted_hours || entry.hours_worked || "N/A"}</td>
                                        <td className="text-purple-400 font-bold">{entry.units}</td>
                                        <td>
                                          {entry.signature === "Yes" ? (
                                            <CheckCircle className="w-4 h-4 text-green-400" />
                                          ) : (
                                            <XCircle className="w-4 h-4 text-gray-600" />
                                          )}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                      
                      {timesheet.sandata_status === "submitted" && (
                        <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg" data-testid={`sandata-success-${timesheet.id}`}>
                          <p className="text-sm text-green-400 font-medium flex items-center gap-2">
                            <CheckCircle size={16} />
                            Successfully submitted to Sandata API
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {timesheet.error_message && (
                    <div className="mt-4">
                      <div className={`p-3 rounded-lg ${
                        timesheet.sandata_status === "blocked" 
                          ? "bg-amber-500/10 border border-amber-500/30" 
                          : "bg-red-500/10 border border-red-500/30"
                      }`} data-testid={`error-message-${timesheet.id}`}>
                        <p className={`text-sm ${
                          timesheet.sandata_status === "blocked" 
                            ? "text-amber-400" 
                            : "text-red-400"
                        }`}>{timesheet.error_message}</p>
                      </div>
                    </div>
                  )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <NotificationProvider>
      <AuthProvider>
        <div className="App">
        <BrowserRouter>
          <Routes>
            {/* Public Routes - redirect to /timesheets if authenticated */}
            <Route path="/landing" element={
              <PublicRoute>
                <LandingPage />
              </PublicRoute>
            } />
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            <Route path="/signup" element={
              <PublicRoute>
                <Signup />
              </PublicRoute>
            } />
            
            {/* Protected Routes - redirect to /landing if not authenticated */}
            <Route path="/*" element={
              <ProtectedRoute>
                <Navigation />
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/timesheets" element={<Home />} />
                  <Route path="/clock-in" element={<ManualClockIn />} />
                  <Route path="/notifications" element={<NotificationCenter />} />
                  <Route path="/notification-preferences" element={<NotificationPreferences />} />
                  <Route path="/patients" element={<Patients />} />
                  <Route path="/test-form" element={<TestForm />} />
                  <Route path="/employees" element={<Employees />} />
                  <Route path="/payers" element={<Payers />} />
                  <Route path="/claims" element={<ClaimsDashboard />} />
                  <Route path="/claims/analytics" element={<ClaimsAnalytics />} />
                  <Route path="/evv" element={<EVVManagement />} />
                  <Route path="/service-codes" element={<ServiceCodes />} />
                  <Route path="/billing-codes" element={<BillingCodes />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/timesheet/edit/:id" element={<TimesheetEditor />} />
                  
                  {/* Admin Routes */}
                  <Route path="/admin" element={<AdminDashboard />} />
                  <Route path="/admin/organizations" element={<AdminOrganizations />} />
                  <Route path="/admin/organizations/create" element={<AdminCreateOrg />} />
                  <Route path="/admin/organizations/:organizationId/credentials" element={<AdminCredentials />} />
                  <Route path="/admin/credentials" element={<AdminCredentials />} />
                  <Route path="/admin/support" element={<AdminSupport />} />
                  <Route path="/admin/logs" element={<AdminLogs />} />
                  
                  {/* Claims Routes */}
                  <Route path="/eligibility-check" element={<EligibilityCheck />} />
                  <Route path="/claim-tracking" element={<ClaimTracking />} />
                </Routes>
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
    </NotificationProvider>
  );
}

export default App;