import React, { useState, useEffect } from "react";
import axios from "axios";
import { Users, Plus, Edit, Trash2, X, CheckCircle, FileText, Calendar, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import SearchFilter from "@/components/SearchFilter";
import BulkActionToolbar from "@/components/BulkActionToolbar";
import MultiStepForm from "@/components/MultiStepForm";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
];

const Patients = () => {
  const [patients, setPatients] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingPatient, setEditingPatient] = useState(null);
  const [selectedPatients, setSelectedPatients] = useState([]);
  const [searchFilters, setSearchFilters] = useState({});
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedPatientDetails, setSelectedPatientDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    sex: "",
    date_of_birth: "",
    address_street: "",
    address_city: "",
    address_state: "",
    address_zip: "",
    prior_auth_number: "",
    icd10_code: "",
    icd10_description: "",
    physician_name: "",
    physician_npi: "",
    medicaid_number: ""
  });

  useEffect(() => {
    fetchPatients();
  }, [searchFilters]);

  const fetchPatients = async () => {
    try {
      const params = new URLSearchParams();
      if (searchFilters.search) params.append('search', searchFilters.search);
      if (searchFilters.is_complete !== undefined) params.append('is_complete', searchFilters.is_complete);
      
      const response = await axios.get(`${API}/patients?${params.toString()}`);
      setPatients(response.data);
      setSelectedPatients([]); // Clear selection when data refreshes
    } catch (e) {
      console.error("Error fetching patients:", e);
      toast.error("Failed to load patients");
    }
  };

  const handleSearch = (filters) => {
    setSearchFilters(filters);
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedPatients(patients.map(p => p.id));
    } else {
      setSelectedPatients([]);
    }
  };

  const handleSelectPatient = (patientId, checked) => {
    if (checked) {
      setSelectedPatients(prev => [...prev, patientId]);
    } else {
      setSelectedPatients(prev => prev.filter(id => id !== patientId));
    }
  };

  const handleBulkMarkComplete = async () => {
    if (!window.confirm(`Mark ${selectedPatients.length} patient(s) as complete?`)) return;
    
    try {
      await axios.post(`${API}/patients/bulk-update`, {
        ids: selectedPatients,
        updates: { is_complete: true }
      });
      toast.success(`${selectedPatients.length} patient(s) marked as complete`);
      await fetchPatients();
    } catch (e) {
      console.error("Bulk update error:", e);
      toast.error("Failed to bulk update patients");
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${selectedPatients.length} patient(s)? This cannot be undone.`)) return;
    
    try {
      await axios.post(`${API}/patients/bulk-delete`, {
        ids: selectedPatients
      });
      toast.success(`${selectedPatients.length} patient(s) deleted`);
      await fetchPatients();
    } catch (e) {
      console.error("Bulk delete error:", e);
      toast.error("Failed to bulk delete patients");
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (data) => {
    // Validate Medicaid number (12 characters max)
    if (data.medicaid_number && data.medicaid_number.length > 12) {
      toast.error("Medicaid number cannot exceed 12 characters");
      return;
    }
    
    // Validate NPI (10 digits)
    if (data.physician_npi && !/^\d{10}$/.test(data.physician_npi)) {
      toast.error("NPI must be exactly 10 digits");
      return;
    }

    try {
      // Mark as complete when manually saving
      const submitData = {
        ...data,
        is_complete: true,
        auto_created_from_timesheet: false
      };

      if (editingPatient) {
        await axios.put(`${API}/patients/${editingPatient.id}`, submitData);
        toast.success("Patient updated successfully");
      } else {
        await axios.post(`${API}/patients`, submitData);
        toast.success("Patient created successfully");
      }
      
      setShowForm(false);
      setEditingPatient(null);
      resetForm();
      await fetchPatients();
    } catch (e) {
      console.error("Error saving patient:", e);
      toast.error(e.response?.data?.detail || "Failed to save patient");
    }
  };

  const handleEdit = (patient) => {
    setEditingPatient(patient);
    setFormData({
      first_name: patient.first_name || "",
      last_name: patient.last_name || "",
      sex: patient.sex || "Male",
      date_of_birth: patient.date_of_birth || "1900-01-01",
      address_street: patient.address_street || "",
      address_city: patient.address_city || "",
      address_state: patient.address_state || "OH",
      address_zip: patient.address_zip || "",
      prior_auth_number: patient.prior_auth_number || "",
      icd10_code: patient.icd10_code || "",
      icd10_description: patient.icd10_description || "",
      physician_name: patient.physician_name || "",
      physician_npi: patient.physician_npi || "",
      medicaid_number: patient.medicaid_number || ""
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this patient?")) return;
    
    try {
      await axios.delete(`${API}/patients/${id}`);
      toast.success("Patient deleted");
      await fetchPatients();
    } catch (e) {
      console.error("Delete error:", e);
      toast.error("Failed to delete patient");
    }
  };

  const handleViewDetails = async (patientId) => {
    setLoadingDetails(true);
    setShowDetailsModal(true);
    
    try {
      const response = await axios.get(`${API}/patients/${patientId}/details`);
      setSelectedPatientDetails(response.data);
    } catch (e) {
      console.error("Error fetching patient details:", e);
      toast.error("Failed to load patient details");
      setShowDetailsModal(false);
    } finally {
      setLoadingDetails(false);
    }
  };

  const resetForm = () => {
    setFormData({
      first_name: "",
      last_name: "",
      sex: "",
      date_of_birth: "",
      address_street: "",
      address_city: "",
      address_state: "",
      address_zip: "",
      prior_auth_number: "",
      icd10_code: "",
      icd10_description: "",
      physician_name: "",
      physician_npi: "",
      medicaid_number: ""
    });
  };

  // Multi-step form configuration
  const formSteps = [
    {
      title: "Step 1: Basic Information",
      description: "Enter patient's personal and identification details",
      requiredFields: ["first_name", "last_name", "sex", "date_of_birth", "medicaid_number"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="first_name">First Name *</Label>
            <Input
              id="first_name"
              value={formData.first_name || ""}
              onChange={(e) => onFormDataChange({...formData, first_name: e.target.value})}
              className={errors.first_name ? "border-red-500" : ""}
            />
            {errors.first_name && <p className="text-xs text-red-500 mt-1">{errors.first_name}</p>}
          </div>
          <div>
            <Label htmlFor="last_name">Last Name *</Label>
            <Input
              id="last_name"
              value={formData.last_name || ""}
              onChange={(e) => onFormDataChange({...formData, last_name: e.target.value})}
              className={errors.last_name ? "border-red-500" : ""}
            />
            {errors.last_name && <p className="text-xs text-red-500 mt-1">{errors.last_name}</p>}
          </div>
          <div>
            <Label htmlFor="sex">Sex *</Label>
            <Select 
              value={formData.sex || ""} 
              onValueChange={(value) => onFormDataChange({...formData, sex: value})}
            >
              <SelectTrigger className={errors.sex ? "border-red-500" : ""}>
                <SelectValue placeholder="Select sex" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Male">Male</SelectItem>
                <SelectItem value="Female">Female</SelectItem>
                <SelectItem value="Other">Other</SelectItem>
              </SelectContent>
            </Select>
            {errors.sex && <p className="text-xs text-red-500 mt-1">{errors.sex}</p>}
          </div>
          <div>
            <Label htmlFor="date_of_birth">Date of Birth *</Label>
            <Input
              id="date_of_birth"
              type="date"
              value={formData.date_of_birth || ""}
              onChange={(e) => onFormDataChange({...formData, date_of_birth: e.target.value})}
              className={errors.date_of_birth ? "border-red-500" : ""}
            />
            {errors.date_of_birth && <p className="text-xs text-red-500 mt-1">{errors.date_of_birth}</p>}
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="medicaid_number">Medicaid Number (12 chars max) *</Label>
            <Input
              id="medicaid_number"
              value={formData.medicaid_number || ""}
              onChange={(e) => onFormDataChange({...formData, medicaid_number: e.target.value})}
              maxLength="12"
              className={`font-mono ${errors.medicaid_number ? "border-red-500" : ""}`}
            />
            <p className="text-xs text-gray-500 mt-1">{(formData.medicaid_number || "").length}/12 characters</p>
            {errors.medicaid_number && <p className="text-xs text-red-500 mt-1">{errors.medicaid_number}</p>}
          </div>
        </div>
      )
    },
    {
      title: "Step 2: Address & Medical Information",
      description: "Enter patient's address and medical details",
      requiredFields: ["address_street", "address_city", "address_state", "address_zip", "prior_auth_number", "icd10_code"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Address</h3>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label htmlFor="address_street">Street Address *</Label>
                <Input
                  id="address_street"
                  value={formData.address_street || ""}
                  onChange={(e) => onFormDataChange({...formData, address_street: e.target.value})}
                  className={errors.address_street ? "border-red-500" : ""}
                />
                {errors.address_street && <p className="text-xs text-red-500 mt-1">{errors.address_street}</p>}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="address_city">City *</Label>
                  <Input
                    id="address_city"
                    value={formData.address_city || ""}
                    onChange={(e) => onFormDataChange({...formData, address_city: e.target.value})}
                    className={errors.address_city ? "border-red-500" : ""}
                  />
                  {errors.address_city && <p className="text-xs text-red-500 mt-1">{errors.address_city}</p>}
                </div>
                <div>
                  <Label htmlFor="address_state">State *</Label>
                  <Select 
                    value={formData.address_state || ""} 
                    onValueChange={(value) => onFormDataChange({...formData, address_state: value})}
                  >
                    <SelectTrigger className={errors.address_state ? "border-red-500" : ""}>
                      <SelectValue placeholder="State" />
                    </SelectTrigger>
                    <SelectContent>
                      {US_STATES.map(state => (
                        <SelectItem key={state} value={state}>{state}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.address_state && <p className="text-xs text-red-500 mt-1">{errors.address_state}</p>}
                </div>
                <div>
                  <Label htmlFor="address_zip">ZIP Code *</Label>
                  <Input
                    id="address_zip"
                    value={formData.address_zip || ""}
                    onChange={(e) => onFormDataChange({...formData, address_zip: e.target.value})}
                    maxLength="10"
                    className={errors.address_zip ? "border-red-500" : ""}
                  />
                  {errors.address_zip && <p className="text-xs text-red-500 mt-1">{errors.address_zip}</p>}
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Medical Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="prior_auth_number">Prior Authorization Number *</Label>
                <Input
                  id="prior_auth_number"
                  value={formData.prior_auth_number || ""}
                  onChange={(e) => onFormDataChange({...formData, prior_auth_number: e.target.value})}
                  className={errors.prior_auth_number ? "border-red-500" : ""}
                />
                {errors.prior_auth_number && <p className="text-xs text-red-500 mt-1">{errors.prior_auth_number}</p>}
              </div>
              <div>
                <Label htmlFor="icd10_code">ICD-10 Code *</Label>
                <Input
                  id="icd10_code"
                  value={formData.icd10_code || ""}
                  onChange={(e) => onFormDataChange({...formData, icd10_code: e.target.value})}
                  placeholder="e.g., Z99.89"
                  className={errors.icd10_code ? "border-red-500" : ""}
                />
                <a href="https://www.icd10data.com" target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline mt-1 block">
                  Search ICD-10 codes →
                </a>
                {errors.icd10_code && <p className="text-xs text-red-500 mt-1">{errors.icd10_code}</p>}
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="icd10_description">ICD-10 Description (Optional)</Label>
                <Input
                  id="icd10_description"
                  value={formData.icd10_description || ""}
                  onChange={(e) => onFormDataChange({...formData, icd10_description: e.target.value})}
                  placeholder="Optional description"
                />
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Step 3: Physician Information",
      description: "Enter the attending physician's details",
      requiredFields: ["physician_name", "physician_npi"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="physician_name">Physician Name *</Label>
            <Input
              id="physician_name"
              value={formData.physician_name || ""}
              onChange={(e) => onFormDataChange({...formData, physician_name: e.target.value})}
              className={errors.physician_name ? "border-red-500" : ""}
            />
            {errors.physician_name && <p className="text-xs text-red-500 mt-1">{errors.physician_name}</p>}
          </div>
          <div>
            <Label htmlFor="physician_npi">NPI Number (10 digits) *</Label>
            <Input
              id="physician_npi"
              value={formData.physician_npi || ""}
              onChange={(e) => onFormDataChange({...formData, physician_npi: e.target.value})}
              maxLength="10"
              pattern="\d{10}"
              placeholder="1234567890"
              className={`font-mono ${errors.physician_npi ? "border-red-500" : ""}`}
            />
            <a href="https://npiregistry.cms.hhs.gov" target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline mt-1 block">
              Verify NPI via NPPES →
            </a>
            {errors.physician_npi && <p className="text-xs text-red-500 mt-1">{errors.physician_npi}</p>}
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Patient Profiles
            </h1>
            <p className="text-gray-600">Manage patient information and records</p>
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingPatient(null);
              setShowForm(true);
            }}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="add-patient-btn"
          >
            <Plus className="mr-2" size={18} />
            Add Patient
          </Button>
        </div>

        {/* Patient Form Modal */}
        {showForm && (
          <div className="mb-8" data-testid="patient-form">
            <MultiStepForm
              steps={formSteps}
              formData={formData}
              onFormDataChange={setFormData}
              onSubmit={handleSubmit}
              onCancel={() => {
                setShowForm(false);
                setEditingPatient(null);
                resetForm();
              }}
              submitLabel={editingPatient ? "Update Patient" : "Create Patient"}
              storageKey="patient-form-draft"
            />
          </div>
        )}


        {/* Search and Filters */}
        {!showForm && (
          <div className="mb-6">
            <SearchFilter
              onSearch={handleSearch}
              placeholder="Search by name, Medicaid ID, or date of birth (YYYY-MM-DD)..."
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
            selectedCount={selectedPatients.length}
            onClearSelection={() => setSelectedPatients([])}
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

        {/* Patients List */}
        <div>
          {patients.length === 0 ? (
            <Card className="bg-white/70 backdrop-blur-sm shadow-lg">
              <CardContent className="py-12 text-center">
                <Users className="mx-auto text-gray-400 mb-4" size={64} />
                <p className="text-gray-500 text-lg">No patients added yet</p>
                <p className="text-gray-400 text-sm mt-2">Create your first patient profile to get started</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Select All Checkbox */}
              <div className="mb-3 flex items-center gap-2 px-2">
                <Checkbox
                  checked={selectedPatients.length === patients.length && patients.length > 0}
                  onCheckedChange={handleSelectAll}
                  id="select-all"
                />
                <label htmlFor="select-all" className="text-sm font-medium text-gray-700 cursor-pointer">
                  Select All ({patients.length})
                </label>
              </div>
              
              <div className="grid gap-4" data-testid="patients-list">
                {patients.map((patient) => (
                  <Card key={patient.id} className="bg-white/70 backdrop-blur-sm shadow-lg hover:shadow-xl transition-all cursor-pointer" data-testid={`patient-${patient.id}`}>
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        {/* Selection Checkbox */}
                        <div className="pt-1" onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={selectedPatients.includes(patient.id)}
                            onCheckedChange={(checked) => handleSelectPatient(patient.id, checked)}
                          />
                        </div>
                        
                        <div className="flex-1 flex justify-between items-start" onClick={() => handleViewDetails(patient.id)}>
                          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                          <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                            {patient.first_name} {patient.last_name}
                            {patient.is_complete === false && (
                              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                                INCOMPLETE
                              </span>
                            )}
                            {patient.auto_created_from_timesheet && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                                AUTO-CREATED
                              </span>
                            )}
                          </h3>
                          <div className="space-y-1 text-sm">
                            <p className="text-gray-600"><span className="font-semibold">DOB:</span> {patient.date_of_birth}</p>
                            <p className="text-gray-600"><span className="font-semibold">Sex:</span> {patient.sex}</p>
                            <p className="text-gray-600"><span className="font-semibold">Medicaid:</span> <span className="font-mono">{patient.medicaid_number}</span></p>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Address</h4>
                          <div className="space-y-1 text-sm text-gray-700">
                            <p>{patient.address_street}</p>
                            <p>{patient.address_city}, {patient.address_state} {patient.address_zip}</p>
                          </div>
                          <div className="mt-3">
                            <p className="text-sm text-gray-600"><span className="font-semibold">Prior Auth:</span> {patient.prior_auth_number}</p>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Medical Info</h4>
                          <div className="space-y-1 text-sm text-gray-700">
                            <p><span className="font-semibold">ICD-10:</span> {patient.icd10_code}</p>
                            {patient.icd10_description && <p className="text-gray-600 text-xs italic">{patient.icd10_description}</p>}
                            <p className="pt-2"><span className="font-semibold">Physician:</span> {patient.physician_name}</p>
                            <p><span className="font-semibold">NPI:</span> <span className="font-mono">{patient.physician_npi}</span></p>
                          </div>
                        </div>
                          </div>
                          
                          <div className="flex gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
                            <Button variant="ghost" size="icon" onClick={() => handleEdit(patient)} data-testid={`edit-patient-${patient.id}`}>
                              <Edit className="text-blue-600" size={18} />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleDelete(patient.id)} data-testid={`delete-patient-${patient.id}`}>
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

export default Patients;
