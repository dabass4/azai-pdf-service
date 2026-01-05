import { useState, useEffect } from "react";
import axios from "axios";
import { UserCheck, Plus, Edit, Trash2, X, Shield, CheckCircle, BadgeCheck, Users, AlertTriangle, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import SearchFilter from "@/components/SearchFilter";
import BulkActionToolbar from "@/components/BulkActionToolbar";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
];

// Employee categories for healthcare workers
const EMPLOYEE_CATEGORIES = [
  { code: "RN", label: "Registered Nurse", color: "bg-blue-100 text-blue-800" },
  { code: "LPN", label: "Licensed Practical Nurse", color: "bg-green-100 text-green-800" },
  { code: "HHA", label: "Home Health Aide", color: "bg-purple-100 text-purple-800" },
  { code: "DSP", label: "Direct Support Professional", color: "bg-orange-100 text-orange-800" }
];

// Common billing codes for quick selection
const COMMON_BILLING_CODES = [
  { code: "T1019", name: "Personal Care Aide", category: "Personal Care" },
  { code: "T1020", name: "Personal Care (per diem)", category: "Personal Care" },
  { code: "T1021", name: "Home Health Aide (per visit)", category: "Personal Care" },
  { code: "G0156", name: "Home Health Aide", category: "Nursing" },
  { code: "G0299", name: "RN Direct Skilled Nursing", category: "Nursing" },
  { code: "G0300", name: "LPN Direct Skilled Nursing", category: "Nursing" },
  { code: "T1000", name: "Private Duty Nursing", category: "PDN" },
  { code: "T1001", name: "Nursing Assessment", category: "Assessment" },
  { code: "T1002", name: "RN Waiver Nursing", category: "Waiver Nursing" },
  { code: "T1003", name: "LPN Waiver Nursing", category: "Waiver Nursing" },
  { code: "G0151", name: "Physical Therapy", category: "Therapy" },
  { code: "G0152", name: "Occupational Therapy", category: "Therapy" },
  { code: "G0153", name: "Speech Therapy", category: "Therapy" },
  { code: "S5125", name: "Attendant Care Services", category: "Personal Care" },
  { code: "S5126", name: "Attendant Care (per 15 min)", category: "Personal Care" },
];

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [searchFilters, setSearchFilters] = useState({});
  
  // Duplicate management state
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [duplicateData, setDuplicateData] = useState(null);
  const [loadingDuplicates, setLoadingDuplicates] = useState(false);
  const [resolvingDuplicate, setResolvingDuplicate] = useState(null);
  
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    middle_name: "",
    ssn: "",
    date_of_birth: "",
    sex: "",
    email: "",
    phone: "",
    address_street: "",
    address_city: "",
    address_state: "",
    address_zip: "",
    employee_id: "",
    categories: [],  // Array of category codes: RN, LPN, HHA, DSP (REQUIRED)
    billing_codes: []  // Array of HCPCS billing codes employee can bill
  });

  useEffect(() => {
    fetchEmployees();
  }, [searchFilters]);

  const fetchEmployees = async () => {
    try {
      const params = new URLSearchParams();
      if (searchFilters.search) params.append('search', searchFilters.search);
      if (searchFilters.is_complete !== undefined) params.append('is_complete', searchFilters.is_complete);
      
      const response = await axios.get(`${API}/employees?${params.toString()}`);
      setEmployees(response.data);
      setSelectedEmployees([]); // Clear selection when data refreshes
    } catch (e) {
      console.error("Error fetching employees:", e);
      toast.error("Failed to load employees");
    }
  };

  const handleSearch = (filters) => {
    setSearchFilters(filters);
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedEmployees(employees.map(e => e.id));
    } else {
      setSelectedEmployees([]);
    }
  };

  const handleSelectEmployee = (employeeId, checked) => {
    if (checked) {
      setSelectedEmployees(prev => [...prev, employeeId]);
    } else {
      setSelectedEmployees(prev => prev.filter(id => id !== employeeId));
    }
  };

  const handleBulkMarkComplete = async () => {
    if (!window.confirm(`Mark ${selectedEmployees.length} employee(s) as complete?`)) return;
    
    try {
      await axios.post(`${API}/employees/bulk-update`, {
        ids: selectedEmployees,
        updates: { is_complete: true }
      });
      toast.success(`${selectedEmployees.length} employee(s) marked as complete`);
      await fetchEmployees();
    } catch (e) {
      console.error("Bulk update error:", e);
      toast.error("Failed to bulk update employees");
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${selectedEmployees.length} employee(s)? This cannot be undone.`)) return;
    
    try {
      await axios.post(`${API}/employees/bulk-delete`, {
        ids: selectedEmployees
      });
      toast.success(`${selectedEmployees.length} employee(s) deleted`);
      await fetchEmployees();
    } catch (e) {
      console.error("Bulk delete error:", e);
      toast.error("Failed to bulk delete employees");
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Format SSN with dashes
    if (name === "ssn") {
      const cleaned = value.replace(/\D/g, "");
      let formatted = cleaned;
      if (cleaned.length > 3 && cleaned.length <= 5) {
        formatted = `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
      } else if (cleaned.length > 5) {
        formatted = `${cleaned.slice(0, 3)}-${cleaned.slice(3, 5)}-${cleaned.slice(5, 9)}`;
      }
      setFormData(prev => ({ ...prev, [name]: formatted }));
    } else if (name === "phone") {
      // Format phone with dashes
      const cleaned = value.replace(/\D/g, "");
      let formatted = cleaned;
      if (cleaned.length > 3 && cleaned.length <= 6) {
        formatted = `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
      } else if (cleaned.length > 6) {
        formatted = `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
      }
      setFormData(prev => ({ ...prev, [name]: formatted }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSelectChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate SSN (9 digits)
    const ssnDigits = formData.ssn.replace(/\D/g, "");
    if (ssnDigits.length !== 9) {
      toast.error("SSN must be exactly 9 digits");
      return;
    }

    // Validate Phone (10 digits)
    const phoneDigits = formData.phone.replace(/\D/g, "");
    if (phoneDigits.length !== 10) {
      toast.error("Phone number must be exactly 10 digits");
      return;
    }

    // Validate at least one category is selected
    if (!formData.categories || formData.categories.length === 0) {
      toast.error("Please select at least one employee category (RN, LPN, HHA, or DSP)");
      return;
    }

    try {
      // Mark as complete when manually saving
      const submitData = {
        ...formData,
        is_complete: true,
        auto_created_from_timesheet: false
      };

      if (editingEmployee) {
        await axios.put(`${API}/employees/${editingEmployee.id}`, submitData);
        toast.success("Employee updated successfully");
      } else {
        await axios.post(`${API}/employees`, submitData);
        toast.success("Employee created successfully");
      }
      
      setShowForm(false);
      setEditingEmployee(null);
      resetForm();
      await fetchEmployees();
    } catch (e) {
      console.error("Error saving employee:", e);
      const errorDetail = e.response?.data?.detail;
      if (typeof errorDetail === 'object' && errorDetail !== null) {
        const message = errorDetail.message || "Validation failed";
        const missingFields = errorDetail.missing_fields;
        if (missingFields && Array.isArray(missingFields)) {
          toast.error(`${message}: ${missingFields.join(', ')}`);
        } else {
          toast.error(message);
        }
      } else {
        toast.error(errorDetail || "Failed to save employee");
      }
    }
  };

  const handleCategoryChange = (categoryCode, checked) => {
    setFormData(prev => {
      const currentCategories = prev.categories || [];
      if (checked) {
        // Add category if not already present
        if (!currentCategories.includes(categoryCode)) {
          return { ...prev, categories: [...currentCategories, categoryCode] };
        }
      } else {
        // Remove category
        return { ...prev, categories: currentCategories.filter(c => c !== categoryCode) };
      }
      return prev;
    });
  };

  const handleEdit = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      first_name: employee.first_name || "",
      last_name: employee.last_name || "",
      middle_name: employee.middle_name || "",
      ssn: employee.ssn || "000-00-0000",
      date_of_birth: employee.date_of_birth || "1900-01-01",
      sex: employee.sex || "Male",
      email: employee.email || "",
      phone: employee.phone || "",
      address_street: employee.address_street || "",
      address_city: employee.address_city || "",
      address_state: employee.address_state || "OH",
      address_zip: employee.address_zip || "",
      employee_id: employee.employee_id || "",
      categories: employee.categories || [],
      billing_codes: employee.billing_codes || []
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this employee?")) return;
    
    try {
      await axios.delete(`${API}/employees/${id}`);
      toast.success("Employee deleted");
      await fetchEmployees();
    } catch (e) {
      console.error("Delete error:", e);
      toast.error("Failed to delete employee");
    }
  };

  const resetForm = () => {
    setFormData({
      first_name: "",
      last_name: "",
      middle_name: "",
      ssn: "",
      date_of_birth: "",
      sex: "",
      email: "",
      phone: "",
      address_street: "",
      address_city: "",
      address_state: "",
      address_zip: "",
      employee_id: "",
      categories: [],
      billing_codes: []
    });
  };

  const handleBillingCodeToggle = (code) => {
    setFormData(prev => {
      const newCodes = prev.billing_codes.includes(code)
        ? prev.billing_codes.filter(c => c !== code)
        : [...prev.billing_codes, code];
      return { ...prev, billing_codes: newCodes };
    });
  };

  const maskSSN = (ssn) => {
    if (!ssn) return "N/A";
    const digits = ssn.replace(/\D/g, "");
    if (digits.length === 9) {
      return `***-**-${digits.slice(5)}`;
    }
    return ssn;
  };

  // Duplicate Management Functions
  const findDuplicates = async () => {
    setLoadingDuplicates(true);
    try {
      const response = await axios.get(`${API}/employees/duplicates/find`);
      setDuplicateData(response.data);
      setShowDuplicates(true);
      if (response.data.total_duplicate_groups === 0) {
        toast.success("No duplicate employees found!");
      } else {
        toast.info(`Found ${response.data.total_duplicate_groups} group(s) of potential duplicates`);
      }
    } catch (e) {
      console.error("Error finding duplicates:", e);
      toast.error("Failed to find duplicates");
    } finally {
      setLoadingDuplicates(false);
    }
  };

  const resolveDuplicate = async (keepId, deleteIds, groupName) => {
    setResolvingDuplicate(keepId);
    try {
      const response = await axios.post(`${API}/employees/duplicates/resolve`, null, {
        params: { keep_id: keepId, delete_ids: deleteIds }
      });
      toast.success(response.data.message);
      
      // Refresh duplicates list
      await findDuplicates();
      // Refresh employees list
      await fetchEmployees();
    } catch (e) {
      console.error("Error resolving duplicate:", e);
      toast.error("Failed to resolve duplicate");
    } finally {
      setResolvingDuplicate(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString() + " " + date.toLocaleTimeString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Employee Profiles
            </h1>
            <p className="text-gray-600">Manage employee information and records</p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={findDuplicates}
              variant="outline"
              disabled={loadingDuplicates}
              className="border-amber-500 text-amber-700 hover:bg-amber-50"
              data-testid="find-duplicates-btn"
            >
              <Users className="mr-2" size={18} />
              {loadingDuplicates ? "Searching..." : "Find Duplicates"}
            </Button>
            <Button
              onClick={() => {
                resetForm();
                setEditingEmployee(null);
                setShowForm(true);
              }}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="add-employee-btn"
            >
              <Plus className="mr-2" size={18} />
              Add Employee
            </Button>
          </div>
        </div>

        {/* Duplicate Management Panel */}
        {showDuplicates && duplicateData && (
          <Card className="mb-8 border-2 border-amber-200 shadow-lg">
            <CardHeader className="bg-amber-50">
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2 text-amber-800">
                  <AlertTriangle className="text-amber-600" size={20} />
                  Duplicate Employee Detection
                </CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setShowDuplicates(false)}>
                  <X size={20} />
                </Button>
              </div>
              <CardDescription className="text-amber-700">
                Found {duplicateData.total_duplicate_groups} group(s) with {duplicateData.total_duplicate_records} potential duplicate(s)
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              {duplicateData.duplicate_groups.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="mx-auto mb-4 text-green-500" size={48} />
                  <p className="text-lg font-medium text-green-700">No duplicates found!</p>
                  <p className="text-sm">All employee records have unique names.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {duplicateData.duplicate_groups.map((group, idx) => (
                    <div key={idx} className="border rounded-lg p-4 bg-white">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-lg text-gray-800">
                          "{group.display_name}" <span className="text-sm font-normal text-gray-500">({group.total_duplicates} records)</span>
                        </h4>
                      </div>
                      
                      {/* Suggested to KEEP */}
                      <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Check className="text-green-600" size={16} />
                          <span className="text-sm font-semibold text-green-800">Suggested to KEEP</span>
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">{group.suggested_keep.reason}</span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                          <div><span className="text-gray-500">Name:</span> {group.suggested_keep.first_name} {group.suggested_keep.last_name}</div>
                          <div><span className="text-gray-500">Email:</span> {group.suggested_keep.email || "N/A"}</div>
                          <div><span className="text-gray-500">Phone:</span> {group.suggested_keep.phone || "N/A"}</div>
                          <div><span className="text-gray-500">Categories:</span> {group.suggested_keep.categories?.join(", ") || "None"}</div>
                          <div><span className="text-gray-500">Complete:</span> {group.suggested_keep.is_complete ? "Yes" : "No"}</div>
                          <div className="md:col-span-3"><span className="text-gray-500">Updated:</span> {formatDate(group.suggested_keep.updated_at)}</div>
                        </div>
                      </div>
                      
                      {/* Suggested to DELETE */}
                      {group.suggested_delete.map((emp, empIdx) => (
                        <div key={empIdx} className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Trash2 className="text-red-600" size={16} />
                              <span className="text-sm font-semibold text-red-800">Suggested to DELETE</span>
                              <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">{emp.reason}</span>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                            <div><span className="text-gray-500">Name:</span> {emp.first_name} {emp.last_name}</div>
                            <div><span className="text-gray-500">Email:</span> {emp.email || "N/A"}</div>
                            <div><span className="text-gray-500">Phone:</span> {emp.phone || "N/A"}</div>
                            <div><span className="text-gray-500">Categories:</span> {emp.categories?.join(", ") || "None"}</div>
                            <div><span className="text-gray-500">Complete:</span> {emp.is_complete ? "Yes" : "No"}</div>
                            <div className="md:col-span-3"><span className="text-gray-500">Updated:</span> {formatDate(emp.updated_at)}</div>
                          </div>
                        </div>
                      ))}
                      
                      {/* Action Buttons */}
                      <div className="flex gap-2 mt-4 pt-3 border-t">
                        <Button
                          onClick={() => resolveDuplicate(
                            group.suggested_keep.id,
                            group.suggested_delete.map(e => e.id),
                            group.display_name
                          )}
                          disabled={resolvingDuplicate === group.suggested_keep.id}
                          className="bg-green-600 hover:bg-green-700"
                          size="sm"
                        >
                          <Check className="mr-1" size={14} />
                          {resolvingDuplicate === group.suggested_keep.id ? "Processing..." : "Accept Suggestion"}
                        </Button>
                        <Button
                          onClick={() => resolveDuplicate(
                            group.suggested_delete[0].id,
                            [group.suggested_keep.id],
                            group.display_name
                          )}
                          disabled={resolvingDuplicate !== null}
                          variant="outline"
                          className="border-red-300 text-red-700 hover:bg-red-50"
                          size="sm"
                        >
                          Keep Older Instead
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Employee Form Modal */}
        {showForm && (
          <Card className="mb-8 border-2 border-blue-200 shadow-lg" data-testid="employee-form">
            <CardHeader className="bg-blue-50">
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  {editingEmployee ? "Edit Employee" : "New Employee"}
                  <Shield className="text-blue-600" size={20} />
                </CardTitle>
                <Button variant="ghost" size="icon" onClick={() => { setShowForm(false); setEditingEmployee(null); }}>
                  <X size={20} />
                </Button>
              </div>
              <CardDescription>All employee data is securely stored and encrypted</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {/* Sandata Compliance Banner */}
              <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <Shield className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-amber-800">Sandata EVV Compliance</p>
                    <p className="text-xs text-amber-700 mt-1">
                      Fields marked with * are required for Sandata EVV submission. At least one Employee Category must be selected. SSN is stored securely and only the last 4 digits are displayed.
                    </p>
                  </div>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Personal Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Personal Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="first_name">First Name *</Label>
                      <Input
                        id="first_name"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleInputChange}
                        required
                        data-testid="first-name-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="middle_name">Middle Name</Label>
                      <Input
                        id="middle_name"
                        name="middle_name"
                        value={formData.middle_name}
                        onChange={handleInputChange}
                        data-testid="middle-name-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="last_name">Last Name *</Label>
                      <Input
                        id="last_name"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleInputChange}
                        required
                        data-testid="last-name-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="ssn">Social Security Number *</Label>
                      <Input
                        id="ssn"
                        name="ssn"
                        value={formData.ssn}
                        onChange={handleInputChange}
                        placeholder="XXX-XX-XXXX"
                        maxLength="11"
                        required
                        data-testid="ssn-input"
                        className="font-mono"
                      />
                    </div>
                    <div>
                      <Label htmlFor="date_of_birth">Date of Birth *</Label>
                      <Input
                        id="date_of_birth"
                        name="date_of_birth"
                        type="date"
                        value={formData.date_of_birth}
                        onChange={handleInputChange}
                        required
                        data-testid="dob-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="sex">Sex *</Label>
                      <Select value={formData.sex} onValueChange={(value) => handleSelectChange("sex", value)} required>
                        <SelectTrigger data-testid="sex-select">
                          <SelectValue placeholder="Select sex" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Male">Male</SelectItem>
                          <SelectItem value="Female">Female</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                {/* Contact Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Contact Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        data-testid="email-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone">Phone Number *</Label>
                      <Input
                        id="phone"
                        name="phone"
                        value={formData.phone}
                        onChange={handleInputChange}
                        placeholder="XXX-XXX-XXXX"
                        maxLength="12"
                        required
                        data-testid="phone-input"
                        className="font-mono"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor="address_street">Street Address *</Label>
                      <Input
                        id="address_street"
                        name="address_street"
                        value={formData.address_street}
                        onChange={handleInputChange}
                        required
                        data-testid="address-street-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="address_city">City *</Label>
                      <Input
                        id="address_city"
                        name="address_city"
                        value={formData.address_city}
                        onChange={handleInputChange}
                        required
                        data-testid="city-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="address_state">State *</Label>
                      <Select value={formData.address_state} onValueChange={(value) => handleSelectChange("address_state", value)} required>
                        <SelectTrigger data-testid="state-select">
                          <SelectValue placeholder="State" />
                        </SelectTrigger>
                        <SelectContent>
                          {US_STATES.map(state => (
                            <SelectItem key={state} value={state}>{state}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="address_zip">ZIP Code *</Label>
                      <Input
                        id="address_zip"
                        name="address_zip"
                        value={formData.address_zip}
                        onChange={handleInputChange}
                        maxLength="10"
                        required
                        data-testid="zip-input"
                      />
                    </div>
                  </div>
                </div>

                {/* Employment Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Employment Information</h3>
                  
                  {/* Employee Categories - Multi-select (REQUIRED) */}
                  <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
                    <Label className="text-sm font-semibold text-gray-700 mb-3 block">
                      Employee Categories * <span className="text-xs font-normal text-gray-500">(Required - Select all that apply)</span>
                    </Label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {EMPLOYEE_CATEGORIES.map((category) => {
                        const isSelected = formData.categories?.includes(category.code) || false;
                        return (
                          <label 
                            key={category.code}
                            htmlFor={`category-${category.code}`}
                            className={`flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition-all ${
                              isSelected 
                                ? 'border-blue-500 bg-blue-50' 
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <input
                              type="checkbox"
                              id={`category-${category.code}`}
                              checked={isSelected}
                              onChange={(e) => handleCategoryChange(category.code, e.target.checked)}
                              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <div className="flex flex-col">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded ${category.color}`}>
                                {category.code}
                              </span>
                              <span className="text-xs text-gray-600 mt-1">{category.label}</span>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                    {(!formData.categories || formData.categories.length === 0) && (
                      <p className="text-xs text-red-600 mt-2 font-medium">⚠️ Required: Please select at least one category</p>
                    )}
                  </div>

                  {/* Billing Codes Section */}
                  <div>
                    <Label className="text-base font-semibold mb-3 block">
                      Billing Codes (HCPCS)
                      <span className="text-xs font-normal text-gray-500 ml-2">Select codes this employee can bill</span>
                    </Label>
                    <div className="border rounded-lg p-3 max-h-64 overflow-y-auto bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {COMMON_BILLING_CODES.map(bc => {
                          const isSelected = formData.billing_codes?.includes(bc.code) || false;
                          return (
                            <label
                              key={bc.code}
                              className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                                isSelected ? 'bg-blue-100 border border-blue-300' : 'bg-white border border-gray-200 hover:bg-gray-100'
                              }`}
                            >
                              <Checkbox
                                checked={isSelected}
                                onCheckedChange={() => handleBillingCodeToggle(bc.code)}
                                className="mr-2"
                              />
                              <div className="flex-1">
                                <span className="font-mono text-sm font-semibold text-blue-700">{bc.code}</span>
                                <span className="text-xs text-gray-600 ml-2">{bc.name}</span>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      {formData.billing_codes?.length || 0} code(s) selected. These will appear in dropdown when editing timesheets.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="employee_id">Employee ID</Label>
                      <Input
                        id="employee_id"
                        name="employee_id"
                        value={formData.employee_id}
                        onChange={handleInputChange}
                        placeholder="Auto-generated if left blank"
                        data-testid="employee-id-input"
                      />
                    </div>
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t">
                  <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingEmployee(null); }}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-employee-btn">
                    {editingEmployee ? "Update Employee" : "Create Employee"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Search and Filters */}
        {!showForm && (
          <div className="mb-6">
            <SearchFilter
              onSearch={handleSearch}
              placeholder="Search by name or employee ID..."
              filters={{
                is_complete: {
                  type: "select",
                  label: "Status",
                  placeholder: "Filter by status",
                  options: [
                    { value: "true", label: "Complete" },
                    { value: "false", label: "Incomplete" }
                  ]
                }
              }}
            />
          </div>
        )}

        {/* Bulk Action Toolbar */}
        {!showForm && (
          <BulkActionToolbar
            selectedCount={selectedEmployees.length}
            onClearSelection={() => setSelectedEmployees([])}
            actions={[
              {
                label: "Mark Complete",
                icon: CheckCircle,
                onClick: handleBulkMarkComplete,
                variant: "default"
              },
              {
                label: "Delete",
                icon: Trash2,
                onClick: handleBulkDelete,
                variant: "destructive"
              }
            ]}
          />
        )}

        {/* Employees List */}
        <div>
          {employees.length === 0 ? (
            <Card className="bg-white/70 backdrop-blur-sm shadow-lg">
              <CardContent className="py-12 text-center">
                <UserCheck className="mx-auto text-gray-400 mb-4" size={64} />
                <p className="text-gray-500 text-lg">No employees added yet</p>
                <p className="text-gray-400 text-sm mt-2">Create your first employee profile to get started</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Select All Checkbox */}
              <div className="mb-3 flex items-center gap-2 px-2">
                <Checkbox
                  checked={selectedEmployees.length === employees.length && employees.length > 0}
                  onCheckedChange={handleSelectAll}
                  id="select-all-employees"
                />
                <label htmlFor="select-all-employees" className="text-sm font-medium text-gray-700 cursor-pointer">
                  Select All ({employees.length})
                </label>
              </div>
              
              <div className="grid gap-4" data-testid="employees-list">
                {employees.map((employee) => (
                  <Card key={employee.id} className="bg-white/70 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow" data-testid={`employee-${employee.id}`}>
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        {/* Selection Checkbox */}
                        <div className="pt-1">
                          <Checkbox
                            checked={selectedEmployees.includes(employee.id)}
                            onCheckedChange={(checked) => handleSelectEmployee(employee.id, checked)}
                          />
                        </div>
                        
                        <div className="flex-1 flex justify-between items-start">
                          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h3 className="text-lg font-bold text-gray-900 mb-2 flex items-center gap-2">
                            {employee.first_name} {employee.middle_name} {employee.last_name}
                            {employee.is_complete === false && (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                                INCOMPLETE
                              </span>
                            )}
                            {employee.auto_created_from_timesheet && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                                AUTO-CREATED
                              </span>
                            )}
                          </h3>
                          {/* Employee Categories */}
                          <div className="flex flex-wrap gap-1 mb-3">
                            {employee.categories && employee.categories.length > 0 ? (
                              employee.categories.map(code => {
                                const cat = EMPLOYEE_CATEGORIES.find(c => c.code === code);
                                return cat ? (
                                  <span key={code} className={`text-xs font-bold px-2 py-0.5 rounded ${cat.color}`}>
                                    {cat.code}
                                  </span>
                                ) : null;
                              })
                            ) : (
                              <span className="text-xs text-amber-600">⚠️ No category</span>
                            )}
                          </div>
                          <div className="space-y-1 text-sm">
                            <p className="text-gray-600"><span className="font-semibold">DOB:</span> {employee.date_of_birth}</p>
                            <p className="text-gray-600"><span className="font-semibold">Sex:</span> {employee.sex}</p>
                            <p className="text-gray-600"><span className="font-semibold">SSN:</span> <span className="font-mono">{maskSSN(employee.ssn)}</span></p>
                            {employee.email && <p className="text-gray-600 text-xs">{employee.email}</p>}
                            <p className="text-gray-600 font-mono text-xs">{employee.phone}</p>
                          </div>
                        </div>
                        
                        {employee.employee_id && (
                          <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Employee ID</h4>
                            <p className="text-sm text-gray-700 font-mono">{employee.employee_id}</p>
                          </div>
                        )}
                          </div>
                          
                          <div className="flex gap-2 ml-4">
                            <Button variant="ghost" size="icon" onClick={() => handleEdit(employee)} data-testid={`edit-employee-${employee.id}`}>
                              <Edit className="text-blue-600" size={18} />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleDelete(employee.id)} data-testid={`delete-employee-${employee.id}`}>
                              <Trash2 className="text-red-500" size={18} />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Employees;
