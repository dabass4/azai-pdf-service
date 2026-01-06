import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { Users, Plus, Edit, Trash2, X, CheckCircle, FileText, Calendar, User, AlertCircle, Heart, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import SearchFilter from "@/components/SearchFilter";
import BulkActionToolbar from "@/components/BulkActionToolbar";
import MultiStepForm from "@/components/MultiStepForm";
import ICD10Badge from "@/components/ICD10Badge";
import PhysicianBadge from "@/components/PhysicianBadge";
import { getPatientFormSteps } from "@/components/PatientFormSteps";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
    medicaid_number: "",
    has_other_insurance: false,
    other_insurance: {
      insurance_name: "",
      subscriber_type: "Person",
      relationship_to_patient: "",
      group_number: "",
      policy_number: "",
      policy_type: ""
    },
    has_second_other_insurance: false,
    second_other_insurance: {
      insurance_name: "",
      subscriber_type: "Person",
      relationship_to_patient: "",
      group_number: "",
      policy_number: "",
      policy_type: ""
    }
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
      setSelectedPatients([]);
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

  const handleSubmit = async (data) => {
    if (data.medicaid_number && data.medicaid_number.length > 12) {
      toast.error("Medicaid number cannot exceed 12 characters");
      return;
    }
    
    if (data.physician_npi && !/^\d{10}$/.test(data.physician_npi)) {
      toast.error("NPI must be exactly 10 digits");
      return;
    }

    try {
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
        toast.error(errorDetail || "Failed to save patient");
      }
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
      medicaid_number: patient.medicaid_number || "",
      has_other_insurance: patient.has_other_insurance || false,
      other_insurance: patient.other_insurance || {
        insurance_name: "",
        subscriber_type: "Person",
        relationship_to_patient: "",
        group_number: "",
        policy_number: "",
        policy_type: ""
      },
      has_second_other_insurance: patient.has_second_other_insurance || false,
      second_other_insurance: patient.second_other_insurance || {
        insurance_name: "",
        subscriber_type: "Person",
        relationship_to_patient: "",
        group_number: "",
        policy_number: "",
        policy_type: ""
      }
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

  const formSteps = useMemo(() => getPatientFormSteps(), []);

  return (
    <div className="min-h-screen healthcare-pattern" data-testid="patients-page">
      <div className="animated-bg"></div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="icon-container">
              <Users className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Patient Profiles
              </h1>
              <p className="text-gray-400">Manage patient information and records</p>
            </div>
          </div>
          <button
            onClick={() => {
              resetForm();
              setEditingPatient(null);
              setShowForm(true);
            }}
            className="btn-primary flex items-center gap-2"
            data-testid="add-patient-btn"
          >
            <Plus size={18} />
            Add Patient
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <Users className="w-5 h-5 text-teal-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Total</span>
            </div>
            <p className="text-3xl font-bold text-white">{patients.length}</p>
            <p className="text-sm text-gray-400">Patients</p>
          </div>
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Complete</span>
            </div>
            <p className="text-3xl font-bold text-white">{patients.filter(p => p.is_complete).length}</p>
            <p className="text-sm text-gray-400">Profiles</p>
          </div>
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <AlertCircle className="w-5 h-5 text-amber-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Incomplete</span>
            </div>
            <p className="text-3xl font-bold text-white">{patients.filter(p => !p.is_complete).length}</p>
            <p className="text-sm text-gray-400">Need Attention</p>
          </div>
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <Heart className="w-5 h-5 text-pink-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Selected</span>
            </div>
            <p className="text-3xl font-bold text-white">{selectedPatients.length}</p>
            <p className="text-sm text-gray-400">For Actions</p>
          </div>
        </div>

        {/* Patient Form Modal */}
        {showForm && (
          <div className="mb-8 glass-card rounded-2xl p-6 animate-slide-up" data-testid="patient-form">
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
        <div className="glass-card rounded-2xl p-6 animate-slide-up">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="icon-container-sm">
                <Users className="w-5 h-5 text-teal-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Patient Records</h2>
            </div>
            <span className="text-sm text-gray-400">{patients.length} total</span>
          </div>
          
          {patients.length === 0 ? (
            <div className="py-16 text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-white/5 flex items-center justify-center">
                <Users className="w-10 h-10 text-gray-600" />
              </div>
              <p className="text-gray-400 text-lg mb-2">No patients added yet</p>
              <p className="text-gray-500 text-sm">Create your first patient profile to get started</p>
            </div>
          ) : (
            <>
              {/* Select All Checkbox */}
              <div className="mb-4 flex items-center gap-3 px-2">
                <Checkbox
                  checked={selectedPatients.length === patients.length && patients.length > 0}
                  onCheckedChange={handleSelectAll}
                  id="select-all"
                  className="border-gray-600"
                />
                <label htmlFor="select-all" className="text-sm font-medium text-gray-400 cursor-pointer">
                  Select All ({patients.length})
                </label>
              </div>
              
              <div className="space-y-3" data-testid="patients-list">
                {patients.map((patient, index) => (
                  <div 
                    key={patient.id} 
                    className="glass-card-hover rounded-xl p-5 cursor-pointer animate-slide-up"
                    style={{ animationDelay: `${index * 0.05}s` }}
                    data-testid={`patient-${patient.id}`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Selection Checkbox */}
                      <div className="pt-1" onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={selectedPatients.includes(patient.id)}
                          onCheckedChange={(checked) => handleSelectPatient(patient.id, checked)}
                          className="border-gray-600"
                        />
                      </div>
                      
                      <div className="flex-1" onClick={() => handleViewDetails(patient.id)}>
                        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                          {/* Patient Name & Basic Info */}
                          <div className="flex-1">
                            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2 flex-wrap">
                              {patient.first_name} {patient.last_name}
                              {patient.is_complete === false && (
                                <span className="status-badge status-pending">INCOMPLETE</span>
                              )}
                              {patient.auto_created_from_timesheet && (
                                <span className="status-badge status-processing">AUTO-CREATED</span>
                              )}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                              <div>
                                <p className="text-gray-400"><span className="text-gray-300 font-medium">DOB:</span> {patient.date_of_birth}</p>
                                <p className="text-gray-400"><span className="text-gray-300 font-medium">Sex:</span> {patient.sex}</p>
                                <p className="text-gray-400"><span className="text-gray-300 font-medium">Medicaid:</span> <span className="font-mono text-teal-400">{patient.medicaid_number}</span></p>
                              </div>
                              
                              <div>
                                <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Address</p>
                                <p className="text-gray-400">{patient.address_street}</p>
                                <p className="text-gray-400">{patient.address_city}, {patient.address_state} {patient.address_zip}</p>
                                <p className="text-gray-400 mt-2"><span className="text-gray-300 font-medium">Prior Auth:</span> {patient.prior_auth_number}</p>
                              </div>
                              
                              <div>
                                <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Medical Info</p>
                                <p className="flex items-center gap-1 text-gray-400">
                                  <span className="text-gray-300 font-medium">ICD-10:</span> 
                                  <ICD10Badge code={patient.icd10_code} description={patient.icd10_description} />
                                </p>
                                {patient.icd10_description && <p className="text-gray-500 text-xs italic">{patient.icd10_description}</p>}
                                <p className="text-gray-400 pt-2"><span className="text-gray-300 font-medium">Physician:</span> {patient.physician_name}</p>
                                <p className="flex items-center gap-1 text-gray-400">
                                  <span className="text-gray-300 font-medium">NPI:</span> 
                                  <PhysicianBadge npi={patient.physician_npi} name={patient.physician_name} />
                                </p>
                              </div>
                            </div>
                          </div>
                          
                          {/* Actions */}
                          <div className="flex gap-2 mt-4 lg:mt-0" onClick={(e) => e.stopPropagation()}>
                            <button 
                              onClick={() => handleEdit(patient)} 
                              className="p-2 rounded-lg bg-white/5 hover:bg-teal-500/20 text-gray-400 hover:text-teal-400 transition-all"
                              data-testid={`edit-patient-${patient.id}`}
                            >
                              <Edit size={16} />
                            </button>
                            <button 
                              onClick={() => handleDelete(patient.id)} 
                              className="p-2 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                              data-testid={`delete-patient-${patient.id}`}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Patient Details Modal */}
        {showDetailsModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowDetailsModal(false)}>
            <div className="glass-card rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto animate-slide-up" onClick={(e) => e.stopPropagation()}>
              {loadingDetails ? (
                <div className="p-12 text-center">
                  <div className="w-12 h-12 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin mx-auto"></div>
                  <p className="mt-4 text-gray-400">Loading patient details...</p>
                </div>
              ) : selectedPatientDetails ? (
                <>
                  {/* Modal Header */}
                  <div className="sticky top-0 glass-card border-b border-white/10 p-6 flex justify-between items-center rounded-t-2xl">
                    <div className="flex items-center gap-4">
                      <div className="icon-container">
                        <User className="w-6 h-6 text-teal-400" />
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-white">
                          {selectedPatientDetails.first_name} {selectedPatientDetails.last_name}
                        </h2>
                        <p className="text-gray-400">Patient Details & Timesheet History</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => setShowDetailsModal(false)}
                      className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-all"
                    >
                      <X size={24} />
                    </button>
                  </div>

                  {/* Modal Content */}
                  <div className="p-6">
                    {/* Patient Information Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                      {/* Basic Info */}
                      <div className="glass-card rounded-xl p-4">
                        <h3 className="text-xs font-semibold text-teal-400 uppercase mb-3">Basic Information</h3>
                        <div className="space-y-2 text-sm">
                          <div className="text-gray-300"><span className="text-gray-500">Name:</span> {selectedPatientDetails.first_name} {selectedPatientDetails.last_name}</div>
                          <div className="text-gray-300"><span className="text-gray-500">DOB:</span> {selectedPatientDetails.date_of_birth}</div>
                          <div className="text-gray-300"><span className="text-gray-500">Sex:</span> {selectedPatientDetails.sex}</div>
                          <div className="text-gray-300"><span className="text-gray-500">Medicaid:</span> <span className="font-mono text-teal-400">{selectedPatientDetails.medicaid_number}</span></div>
                          {selectedPatientDetails.is_complete === false && (
                            <div className="pt-2">
                              <span className="status-badge status-pending">INCOMPLETE PROFILE</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Address Info */}
                      <div className="glass-card rounded-xl p-4">
                        <h3 className="text-xs font-semibold text-teal-400 uppercase mb-3">Address</h3>
                        <div className="space-y-1 text-sm text-gray-300">
                          <div>{selectedPatientDetails.address_street || "N/A"}</div>
                          <div>{selectedPatientDetails.address_city}, {selectedPatientDetails.address_state} {selectedPatientDetails.address_zip}</div>
                          <div className="pt-2"><span className="text-gray-500">Prior Auth:</span> {selectedPatientDetails.prior_auth_number || "N/A"}</div>
                        </div>
                      </div>

                      {/* Medical Info */}
                      <div className="glass-card rounded-xl p-4">
                        <h3 className="text-xs font-semibold text-teal-400 uppercase mb-3">Medical Information</h3>
                        <div className="space-y-2 text-sm text-gray-300">
                          <div className="flex items-center gap-1">
                            <span className="text-gray-500">ICD-10:</span> 
                            <ICD10Badge 
                              code={selectedPatientDetails.icd10_code} 
                              description={selectedPatientDetails.icd10_description} 
                            />
                          </div>
                          {selectedPatientDetails.icd10_description && (
                            <div className="text-gray-500 text-xs italic">{selectedPatientDetails.icd10_description}</div>
                          )}
                          <div className="pt-2"><span className="text-gray-500">Physician:</span> {selectedPatientDetails.physician_name || "N/A"}</div>
                          <div className="flex items-center gap-1">
                            <span className="text-gray-500">NPI:</span> 
                            <PhysicianBadge 
                              npi={selectedPatientDetails.physician_npi} 
                              name={selectedPatientDetails.physician_name} 
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Visit Statistics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <div className="stat-card">
                        <div className="flex items-center gap-4">
                          <div className="icon-container">
                            <FileText className="w-6 h-6 text-teal-400" />
                          </div>
                          <div>
                            <p className="text-sm text-gray-400">Total Visits</p>
                            <p className="text-3xl font-bold text-white">{selectedPatientDetails.total_visits || 0}</p>
                          </div>
                        </div>
                      </div>

                      <div className="stat-card">
                        <div className="flex items-center gap-4">
                          <div className="icon-container">
                            <Calendar className="w-6 h-6 text-green-400" />
                          </div>
                          <div>
                            <p className="text-sm text-gray-400">Last Visit Date</p>
                            <p className="text-xl font-bold text-white">
                              {selectedPatientDetails.last_visit_date || "No visits yet"}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Timesheet History */}
                    <div>
                      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <FileText className="text-teal-400" size={24} />
                        Timesheet History
                      </h3>
                      
                      {selectedPatientDetails.timesheets && selectedPatientDetails.timesheets.length > 0 ? (
                        <div className="space-y-3">
                          {selectedPatientDetails.timesheets.map((timesheet) => (
                            <div key={timesheet.id} className="glass-card-hover rounded-xl p-4">
                              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div>
                                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">File</p>
                                  <p className="text-sm font-mono text-gray-300 truncate">{timesheet.filename}</p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Date</p>
                                  <p className="text-sm text-gray-300">{timesheet.extracted_data?.date || "N/A"}</p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Time</p>
                                  <p className="text-sm text-gray-300">
                                    {timesheet.extracted_data?.time_in && timesheet.extracted_data?.time_out
                                      ? `${timesheet.extracted_data.time_in} - ${timesheet.extracted_data.time_out}`
                                      : "N/A"}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Status</p>
                                  <span className={`status-badge ${
                                    timesheet.status === 'completed' ? 'status-completed' :
                                    timesheet.status === 'failed' ? 'status-error' :
                                    'status-pending'
                                  }`}>
                                    {timesheet.status?.toUpperCase() || "UNKNOWN"}
                                  </span>
                                </div>
                              </div>
                              
                              {timesheet.extracted_data?.employee_name && (
                                <div className="mt-3 pt-3 border-t border-white/10">
                                  <p className="text-xs text-gray-500">Employee: <span className="text-gray-300 font-medium">{timesheet.extracted_data.employee_name}</span></p>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="glass-card rounded-xl p-8 text-center">
                          <FileText className="mx-auto text-gray-600 mb-3" size={48} />
                          <p className="text-gray-400">No timesheet history for this patient</p>
                          <p className="text-sm text-gray-500 mt-1">Timesheets will appear here once uploaded</p>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Patients;
