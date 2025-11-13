import { useState, useEffect } from "react";
import axios from "axios";
import { FileText, Plus, Edit, Trash2, Send, CheckCircle, Clock, X, AlertCircle, Download, FileCode, List, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Claims = () => {
  const [activeTab, setActiveTab] = useState("claims"); // claims, generate837, enrollment
  const [claims, setClaims] = useState([]);
  const [generated837Claims, setGenerated837Claims] = useState([]);
  const [timesheets, setTimesheets] = useState([]);
  const [selectedTimesheets, setSelectedTimesheets] = useState([]);
  const [enrollmentStatus, setEnrollmentStatus] = useState(null);
  const [patients, setPatients] = useState([]);
  const [payers, setPayers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingClaim, setEditingClaim] = useState(null);
  const [formData, setFormData] = useState({
    patient_id: "",
    payer_id: "",
    service_period_start: "",
    service_period_end: "",
    notes: "",
    line_items: []
  });

  useEffect(() => {
    fetchClaims();
    fetchGenerated837Claims();
    fetchTimesheets();
    fetchPatients();
    fetchPayers();
    fetchEmployees();
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

  const fetchClaims = async () => {
    try {
      const response = await axios.get(`${API}/claims`);
      setClaims(response.data);
    } catch (e) {
      console.error("Error fetching claims:", e);
      toast.error("Failed to load claims");
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (e) {
      console.error("Error fetching patients:", e);
    }
  };

  const fetchPayers = async () => {
    try {
      const response = await axios.get(`${API}/insurance-contracts`);
      setPayers(response.data);
    } catch (e) {
      console.error("Error fetching payers:", e);
    }
  };

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
    } catch (e) {
      console.error("Error fetching employees:", e);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [
        ...prev.line_items,
        {
          date_of_service: "",
          employee_name: "",
          employee_id: "",
          service_code: "",
          service_name: "",
          units: 0,
          rate_per_unit: 0,
          amount: 0
        }
      ]
    }));
  };

  const removeLineItem = (index) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, idx) => idx !== index)
    }));
  };

  const updateLineItem = (index, field, value) => {
    setFormData(prev => {
      const newLineItems = [...prev.line_items];
      newLineItems[index] = {
        ...newLineItems[index],
        [field]: value
      };
      
      // Calculate amount if units or rate changes
      if (field === 'units' || field === 'rate_per_unit') {
        const units = field === 'units' ? parseFloat(value) || 0 : newLineItems[index].units;
        const rate = field === 'rate_per_unit' ? parseFloat(value) || 0 : newLineItems[index].rate_per_unit;
        newLineItems[index].amount = units * rate;
      }
      
      return { ...prev, line_items: newLineItems };
    });
  };

  const calculateTotals = () => {
    const total_units = formData.line_items.reduce((sum, item) => sum + (parseFloat(item.units) || 0), 0);
    const total_amount = formData.line_items.reduce((sum, item) => sum + (parseFloat(item.amount) || 0), 0);
    return { total_units, total_amount };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const patient = patients.find(p => p.id === formData.patient_id);
    const payer = payers.find(p => p.id === formData.payer_id);

    if (!patient || !payer) {
      toast.error("Please select valid patient and payer");
      return;
    }

    const { total_units, total_amount } = calculateTotals();

    const claimData = {
      claim_number: "", // Will be auto-generated
      patient_id: patient.id,
      patient_name: `${patient.first_name} ${patient.last_name}`,
      patient_medicaid_number: patient.medicaid_number,
      payer_id: payer.id,
      payer_name: payer.payer_name,
      contract_number: payer.contract_number || "",
      service_period_start: formData.service_period_start,
      service_period_end: formData.service_period_end,
      line_items: formData.line_items,
      total_units,
      total_amount,
      status: "draft",
      notes: formData.notes,
      timesheet_ids: []
    };

    try {
      if (editingClaim) {
        await axios.put(`${API}/claims/${editingClaim.id}`, { ...claimData, id: editingClaim.id });
        toast.success("Claim updated successfully");
      } else {
        await axios.post(`${API}/claims`, claimData);
        toast.success("Claim created successfully");
      }
      
      setShowForm(false);
      setEditingClaim(null);
      resetForm();
      await fetchClaims();
    } catch (e) {
      console.error("Error saving claim:", e);
      toast.error(e.response?.data?.detail || "Failed to save claim");
    }
  };

  const handleSubmitClaim = async (claimId) => {
    if (!window.confirm("Submit this claim to Ohio Medicaid?")) return;

    try {
      const response = await axios.post(`${API}/claims/${claimId}/submit`);
      toast.success(response.data.message);
      await fetchClaims();
    } catch (e) {
      console.error("Submit error:", e);
      toast.error("Failed to submit claim");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this claim?")) return;
    
    try {
      await axios.delete(`${API}/claims/${id}`);
      toast.success("Claim deleted");
      await fetchClaims();
    } catch (e) {
      console.error("Delete error:", e);
      toast.error("Failed to delete claim");
    }
  };

  // 837P Claim Generation Handlers
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

      // Download the EDI file
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

  const resetForm = () => {
    setFormData({
      patient_id: "",
      payer_id: "",
      service_period_start: "",
      service_period_end: "",
      notes: "",
      line_items: []
    });
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: "bg-gray-100 text-gray-700",
      submitted: "bg-blue-100 text-blue-700",
      pending: "bg-yellow-100 text-yellow-700",
      approved: "bg-green-100 text-green-700",
      denied: "bg-red-100 text-red-700",
      paid: "bg-emerald-100 text-emerald-700"
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${styles[status] || styles.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const { total_units, total_amount } = calculateTotals();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Medicaid Claims
            </h1>
            <p className="text-gray-600">Create and submit claims to Ohio Department of Medicaid</p>
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingClaim(null);
              setShowForm(true);
            }}
            className="bg-blue-600 hover:bg-blue-700 w-full sm:w-auto"
            data-testid="add-claim-btn"
          >
            <Plus className="mr-2" size={18} />
            New Claim
          </Button>
        </div>

        {/* Claim Form */}
        {showForm && (
          <Card className="mb-8 border-2 border-blue-200 shadow-lg" data-testid="claim-form">
            <CardHeader className="bg-blue-50">
              <div className="flex justify-between items-center">
                <CardTitle>{editingClaim ? "Edit Claim" : "New Medicaid Claim"}</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => { setShowForm(false); setEditingClaim(null); }}>
                  <X size={20} />
                </Button>
              </div>
              <CardDescription>Create a claim for Ohio Department of Medicaid</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Patient and Payer */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="patient_id">Patient *</Label>
                    <Select value={formData.patient_id} onValueChange={(value) => handleSelectChange("patient_id", value)} required>
                      <SelectTrigger data-testid="patient-select">
                        <SelectValue placeholder="Select patient" />
                      </SelectTrigger>
                      <SelectContent>
                        {patients.map(patient => (
                          <SelectItem key={patient.id} value={patient.id}>
                            {patient.first_name} {patient.last_name} - {patient.medicaid_number}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="payer_id">Insurance Payer *</Label>
                    <Select value={formData.payer_id} onValueChange={(value) => handleSelectChange("payer_id", value)} required>
                      <SelectTrigger data-testid="payer-select">
                        <SelectValue placeholder="Select payer" />
                      </SelectTrigger>
                      <SelectContent>
                        {payers.filter(p => p.is_active).map(payer => (
                          <SelectItem key={payer.id} value={payer.id}>
                            {payer.payer_name} - {payer.insurance_type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Service Period */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="service_period_start">Service Period Start *</Label>
                    <Input
                      id="service_period_start"
                      name="service_period_start"
                      type="date"
                      value={formData.service_period_start}
                      onChange={handleInputChange}
                      required
                      data-testid="period-start-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="service_period_end">Service Period End *</Label>
                    <Input
                      id="service_period_end"
                      name="service_period_end"
                      type="date"
                      value={formData.service_period_end}
                      onChange={handleInputChange}
                      required
                      data-testid="period-end-input"
                    />
                  </div>
                </div>

                {/* Line Items */}
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <Label className="text-base font-semibold">Service Line Items</Label>
                    <Button type="button" onClick={addLineItem} size="sm" className="bg-green-600 hover:bg-green-700">
                      <Plus className="mr-1" size={16} />
                      Add Service
                    </Button>
                  </div>

                  {formData.line_items.length === 0 ? (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
                      <FileText className="mx-auto mb-2 text-gray-400" size={32} />
                      <p>No service items added yet</p>
                      <p className="text-sm">Click "Add Service" to add billable services</p>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {formData.line_items.map((item, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            <div>
                              <Label className="text-xs">Date of Service</Label>
                              <Input
                                type="date"
                                value={item.date_of_service}
                                onChange={(e) => updateLineItem(index, 'date_of_service', e.target.value)}
                                className="text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Employee</Label>
                              <select
                                value={item.employee_name}
                                onChange={(e) => {
                                  const emp = employees.find(e => e.first_name + ' ' + e.last_name === e.target.value);
                                  updateLineItem(index, 'employee_name', e.target.value);
                                  if (emp) updateLineItem(index, 'employee_id', emp.employee_id || emp.id);
                                }}
                                className="w-full h-10 px-2 text-sm border border-gray-300 rounded-md"
                              >
                                <option value="">Select employee</option>
                                {employees.map(emp => (
                                  <option key={emp.id} value={`${emp.first_name} ${emp.last_name}`}>
                                    {emp.first_name} {emp.last_name}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <Label className="text-xs">Service Code</Label>
                              <Input
                                value={item.service_code}
                                onChange={(e) => updateLineItem(index, 'service_code', e.target.value)}
                                placeholder="e.g., T1019"
                                className="text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Service Name</Label>
                              <Input
                                value={item.service_name}
                                onChange={(e) => updateLineItem(index, 'service_name', e.target.value)}
                                placeholder="e.g., Personal Care"
                                className="text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Units</Label>
                              <Input
                                type="number"
                                value={item.units}
                                onChange={(e) => updateLineItem(index, 'units', e.target.value)}
                                min="0"
                                className="text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Rate/Unit ($)</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={item.rate_per_unit}
                                onChange={(e) => updateLineItem(index, 'rate_per_unit', e.target.value)}
                                min="0"
                                className="text-sm"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Amount ($)</Label>
                              <Input
                                type="number"
                                step="0.01"
                                value={item.amount.toFixed(2)}
                                readOnly
                                className="text-sm bg-gray-100"
                              />
                            </div>
                            <div className="flex items-end">
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeLineItem(index)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 size={16} />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Totals */}
                  {formData.line_items.length > 0 && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="text-sm text-gray-600">Total Units</p>
                          <p className="text-2xl font-bold text-blue-900">{total_units}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">Total Amount</p>
                          <p className="text-2xl font-bold text-green-900">${total_amount.toFixed(2)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Notes */}
                <div>
                  <Label htmlFor="notes">Notes</Label>
                  <textarea
                    id="notes"
                    name="notes"
                    value={formData.notes}
                    onChange={handleInputChange}
                    rows="2"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Additional notes or comments..."
                  />
                </div>

                {/* Form Actions */}
                <div className="flex flex-col sm:flex-row justify-end gap-3 pt-4 border-t">
                  <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingClaim(null); }} className="w-full sm:w-auto">
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700 w-full sm:w-auto">
                    {editingClaim ? "Update Claim" : "Create Claim"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Claims List */}
        <div>
          {claims.length === 0 ? (
            <Card className="bg-white/70 backdrop-blur-sm shadow-lg">
              <CardContent className="py-12 text-center">
                <FileText className="mx-auto text-gray-400 mb-4" size={64} />
                <p className="text-gray-500 text-lg">No claims created yet</p>
                <p className="text-gray-400 text-sm mt-2">Create your first Medicaid claim to get started</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6">
              {claims.map((claim) => (
                <Card key={claim.id} className="bg-white/70 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex flex-col lg:flex-row justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-3 mb-4">
                          <h3 className="text-lg sm:text-xl font-bold text-gray-900">{claim.claim_number}</h3>
                          {getStatusBadge(claim.status)}
                          {claim.status === 'submitted' && claim.submission_date && (
                            <span className="text-xs text-gray-500">Submitted: {claim.submission_date}</span>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                          <div>
                            <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Patient</p>
                            <p className="text-sm font-medium text-gray-900">{claim.patient_name}</p>
                            <p className="text-xs text-gray-600">Medicaid: {claim.patient_medicaid_number}</p>
                          </div>
                          
                          <div>
                            <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Payer</p>
                            <p className="text-sm font-medium text-gray-900">{claim.payer_name}</p>
                            {claim.contract_number && <p className="text-xs text-gray-600">{claim.contract_number}</p>}
                          </div>
                          
                          <div>
                            <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Service Period</p>
                            <p className="text-sm text-gray-900">{claim.service_period_start}</p>
                            <p className="text-sm text-gray-900">to {claim.service_period_end}</p>
                          </div>
                          
                          <div>
                            <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Billing</p>
                            <p className="text-lg font-bold text-green-900">${claim.total_amount.toFixed(2)}</p>
                            <p className="text-xs text-gray-600">{claim.total_units} units • {claim.line_items.length} services</p>
                          </div>
                        </div>
                        
                        {claim.notes && (
                          <div className="mt-3 p-2 bg-gray-50 rounded text-sm text-gray-700">
                            {claim.notes}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex lg:flex-col gap-2">
                        {claim.status === 'draft' && (
                          <Button 
                            size="sm" 
                            onClick={() => handleSubmitClaim(claim.id)}
                            className="bg-green-600 hover:bg-green-700 flex-1 lg:flex-none"
                          >
                            <Send className="mr-1" size={16} />
                            Submit
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" className="lg:w-full">
                          <Edit className="text-blue-600" size={18} />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(claim.id)} className="lg:w-full">
                          <Trash2 className="text-red-500" size={18} />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Claims;
