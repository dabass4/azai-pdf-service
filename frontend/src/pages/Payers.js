import { useState, useEffect } from "react";
import axios from "axios";
import { DollarSign, Plus, Edit, Trash2, X, ToggleLeft, ToggleRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Ohio Medicaid Billable Services
const OHIO_MEDICAID_SERVICES = [
  { code: "S5125", name: "Attendant Care Services", description: "Personal care services per 15 minutes" },
  { code: "S5126", name: "Homemaker Services", description: "Per 15 minutes" },
  { code: "T1019", name: "Personal Care Services", description: "Per 15 minutes" },
  { code: "T1020", name: "Personal Care Services", description: "Per diem" },
  { code: "G0156", name: "Home Health Aide Services", description: "Per visit" },
  { code: "S9122", name: "Home Health Aide", description: "Per hour" },
  { code: "T1000", name: "Private Duty Nursing", description: "Licensed practical nurse, per 15 minutes" },
  { code: "T1001", name: "Nursing Assessment", description: "Per visit" },
  { code: "T1002", name: "RN Services", description: "Per diem" },
  { code: "T1003", name: "RN Services", description: "Per hour" },
  { code: "T1004", name: "Behavioral Health Services", description: "Per 15 minutes" },
  { code: "T1005", name: "Respite Care", description: "Per diem" },
  { code: "T1502", name: "Home Management Training", description: "Per 15 minutes" },
  { code: "T1999", name: "Miscellaneous Therapeutic Services", description: "Per 15 minutes" },
  { code: "T2024", name: "Service Assessment", description: "Per 15 minutes" },
  { code: "T2025", name: "Waiver Services", description: "Per 15 minutes" },
  { code: "S5170", name: "Home Delivered Meals", description: "Per meal" },
  { code: "A0130", name: "Non-Emergency Transportation", description: "Per trip" },
  { code: "T2003", name: "Non-Emergency Transportation", description: "Encounter/trip" },
  { code: "T2004", name: "Non-Emergency Transportation", description: "Per diem" },
  { code: "S5150", name: "Adult Day Care", description: "Per half day" },
  { code: "S5151", name: "Adult Day Care", description: "Per diem" },
  { code: "T2031", name: "Assisted Living Services", description: "Per month" },
  { code: "T2032", name: "Residential Care Services", description: "Per diem" },
  { code: "T2033", name: "Community Transition Services", description: "Per service" },
];

const INSURANCE_TYPES = [
  "Medicaid",
  "Medicare",
  "Private Insurance",
  "Managed Care",
  "Long-Term Care",
  "Waiver Program",
  "Other"
];

const Payers = () => {
  const [contracts, setContracts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingContract, setEditingContract] = useState(null);
  const [formData, setFormData] = useState({
    payer_name: "",
    insurance_type: "",
    contract_number: "",
    start_date: "",
    end_date: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    notes: "",
    is_active: true,
    billable_services: []
  });

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const response = await axios.get(`${API}/insurance-contracts`);
      setContracts(response.data);
    } catch (e) {
      console.error("Error fetching contracts:", e);
      toast.error("Failed to load contracts");
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: type === "checkbox" ? checked : value 
    }));
  };

  const handleSelectChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleServiceToggle = (serviceCode) => {
    setFormData(prev => {
      const existingIndex = prev.billable_services.findIndex(s => s.service_code === serviceCode);
      let newServices = [...prev.billable_services];
      
      if (existingIndex >= 0) {
        // Toggle existing service
        newServices[existingIndex] = {
          ...newServices[existingIndex],
          is_active: !newServices[existingIndex].is_active
        };
      } else {
        // Add new service
        const service = OHIO_MEDICAID_SERVICES.find(s => s.code === serviceCode);
        if (service) {
          newServices.push({
            service_code: service.code,
            service_name: service.name,
            description: service.description,
            is_active: true
          });
        }
      }
      
      return { ...prev, billable_services: newServices };
    });
  };

  const isServiceActive = (serviceCode) => {
    const service = formData.billable_services.find(s => s.service_code === serviceCode);
    return service?.is_active || false;
  };

  const isServiceAdded = (serviceCode) => {
    return formData.billable_services.some(s => s.service_code === serviceCode);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingContract) {
        await axios.put(`${API}/insurance-contracts/${editingContract.id}`, formData);
        toast.success("Contract updated successfully");
      } else {
        await axios.post(`${API}/insurance-contracts`, formData);
        toast.success("Contract created successfully");
      }
      
      setShowForm(false);
      setEditingContract(null);
      resetForm();
      await fetchContracts();
    } catch (e) {
      console.error("Error saving contract:", e);
      toast.error(e.response?.data?.detail || "Failed to save contract");
    }
  };

  const handleEdit = (contract) => {
    setEditingContract(contract);
    setFormData({
      payer_name: contract.payer_name,
      insurance_type: contract.insurance_type,
      contract_number: contract.contract_number || "",
      start_date: contract.start_date,
      end_date: contract.end_date || "",
      contact_person: contract.contact_person || "",
      contact_phone: contract.contact_phone || "",
      contact_email: contract.contact_email || "",
      notes: contract.notes || "",
      is_active: contract.is_active,
      billable_services: contract.billable_services || []
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this contract?")) return;
    
    try {
      await axios.delete(`${API}/insurance-contracts/${id}`);
      toast.success("Contract deleted");
      await fetchContracts();
    } catch (e) {
      console.error("Delete error:", e);
      toast.error("Failed to delete contract");
    }
  };

  const resetForm = () => {
    setFormData({
      payer_name: "",
      insurance_type: "",
      contract_number: "",
      start_date: "",
      end_date: "",
      contact_person: "",
      contact_phone: "",
      contact_email: "",
      notes: "",
      is_active: true,
      billable_services: []
    });
  };

  const getActiveServicesCount = (contract) => {
    return contract.billable_services?.filter(s => s.is_active).length || 0;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Insurance Contracts & Payers
            </h1>
            <p className="text-gray-600">Manage insurance contracts and billable services</p>
          </div>
          <Button
            onClick={() => {
              resetForm();
              setEditingContract(null);
              setShowForm(true);
            }}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="add-contract-btn"
          >
            <Plus className="mr-2" size={18} />
            Add Contract
          </Button>
        </div>

        {/* Contract Form */}
        {showForm && (
          <Card className="mb-8 border-2 border-blue-200 shadow-lg" data-testid="contract-form">
            <CardHeader className="bg-blue-50">
              <div className="flex justify-between items-center">
                <CardTitle>{editingContract ? "Edit Contract" : "New Insurance Contract"}</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => { setShowForm(false); setEditingContract(null); }}>
                  <X size={20} />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Contract Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Contract Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="payer_name">Payer Name *</Label>
                      <Input
                        id="payer_name"
                        name="payer_name"
                        value={formData.payer_name}
                        onChange={handleInputChange}
                        placeholder="e.g., Ohio Department of Medicaid"
                        required
                        data-testid="payer-name-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="insurance_type">Insurance Type *</Label>
                      <Select value={formData.insurance_type} onValueChange={(value) => handleSelectChange("insurance_type", value)} required>
                        <SelectTrigger data-testid="insurance-type-select">
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          {INSURANCE_TYPES.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="contract_number">Contract Number</Label>
                      <Input
                        id="contract_number"
                        name="contract_number"
                        value={formData.contract_number}
                        onChange={handleInputChange}
                        placeholder="Optional"
                        data-testid="contract-number-input"
                      />
                    </div>
                    <div className="flex items-center space-x-2">
                      <Label htmlFor="is_active">Contract Active</Label>
                      <Switch
                        id="is_active"
                        checked={formData.is_active}
                        onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
                        data-testid="is-active-switch"
                      />
                    </div>
                  </div>
                </div>

                {/* Contract Dates */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Contract Period</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="start_date">Start Date *</Label>
                      <Input
                        id="start_date"
                        name="start_date"
                        type="date"
                        value={formData.start_date}
                        onChange={handleInputChange}
                        required
                        data-testid="start-date-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="end_date">End Date</Label>
                      <Input
                        id="end_date"
                        name="end_date"
                        type="date"
                        value={formData.end_date}
                        onChange={handleInputChange}
                        placeholder="Leave blank for ongoing"
                        data-testid="end-date-input"
                      />
                      <p className="text-xs text-gray-500 mt-1">Leave blank for ongoing contracts</p>
                    </div>
                  </div>
                </div>

                {/* Contact Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Contact Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="contact_person">Contact Person</Label>
                      <Input
                        id="contact_person"
                        name="contact_person"
                        value={formData.contact_person}
                        onChange={handleInputChange}
                        placeholder="Optional"
                        data-testid="contact-person-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="contact_phone">Phone</Label>
                      <Input
                        id="contact_phone"
                        name="contact_phone"
                        value={formData.contact_phone}
                        onChange={handleInputChange}
                        placeholder="Optional"
                        data-testid="contact-phone-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="contact_email">Email</Label>
                      <Input
                        id="contact_email"
                        name="contact_email"
                        type="email"
                        value={formData.contact_email}
                        onChange={handleInputChange}
                        placeholder="Optional"
                        data-testid="contact-email-input"
                      />
                    </div>
                  </div>
                </div>

                {/* Ohio Medicaid Services */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Billable Services (Ohio Medicaid)</h3>
                  <p className="text-sm text-gray-600 mb-4">Toggle services that are billable under this contract</p>
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto">
                    <div className="space-y-2">
                      {OHIO_MEDICAID_SERVICES.map((service) => (
                        <div key={service.code} className="flex items-center justify-between p-3 bg-white rounded border border-gray-200 hover:bg-blue-50" data-testid={`service-${service.code}`}>
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <span className="font-mono text-sm font-semibold text-blue-900">{service.code}</span>
                              <span className="font-medium text-gray-900">{service.name}</span>
                            </div>
                            <p className="text-xs text-gray-600 mt-1">{service.description}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleServiceToggle(service.code)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-full transition-colors ${
                              isServiceActive(service.code)
                                ? "bg-green-100 text-green-700 hover:bg-green-200"
                                : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                            }`}
                            data-testid={`toggle-${service.code}`}
                          >
                            {isServiceActive(service.code) ? (
                              <>
                                <ToggleRight size={20} />
                                <span className="text-sm font-medium">Active</span>
                              </>
                            ) : (
                              <>
                                <ToggleLeft size={20} />
                                <span className="text-sm font-medium">Inactive</span>
                              </>
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    {formData.billable_services.filter(s => s.is_active).length} service(s) selected
                  </p>
                </div>

                {/* Notes */}
                <div>
                  <Label htmlFor="notes">Notes</Label>
                  <textarea
                    id="notes"
                    name="notes"
                    value={formData.notes}
                    onChange={handleInputChange}
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Additional contract notes or terms..."
                    data-testid="notes-input"
                  />
                </div>

                {/* Form Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t">
                  <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingContract(null); }}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-contract-btn">
                    {editingContract ? "Update Contract" : "Create Contract"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Contracts List */}
        <div>
          {contracts.length === 0 ? (
            <Card className="bg-white/70 backdrop-blur-sm shadow-lg">
              <CardContent className="py-12 text-center">
                <DollarSign className="mx-auto text-gray-400 mb-4" size={64} />
                <p className="text-gray-500 text-lg">No contracts added yet</p>
                <p className="text-gray-400 text-sm mt-2">Create your first insurance contract to get started</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6" data-testid="contracts-list">
              {contracts.map((contract) => (
                <Card key={contract.id} className="bg-white/70 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow" data-testid={`contract-${contract.id}`}>
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-4">
                          <h3 className="text-xl font-bold text-gray-900">{contract.payer_name}</h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            contract.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                          }`}>
                            {contract.is_active ? "Active" : "Inactive"}
                          </span>
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                            {contract.insurance_type}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                          <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Contract Details</h4>
                            <div className="space-y-1 text-sm">
                              {contract.contract_number && <p><span className="font-semibold">Number:</span> {contract.contract_number}</p>}
                              <p><span className="font-semibold">Start:</span> {contract.start_date}</p>
                              <p><span className="font-semibold">End:</span> {contract.end_date || "Ongoing"}</p>
                            </div>
                          </div>
                          
                          {(contract.contact_person || contract.contact_phone || contract.contact_email) && (
                            <div>
                              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Contact</h4>
                              <div className="space-y-1 text-sm text-gray-700">
                                {contract.contact_person && <p className="font-semibold">{contract.contact_person}</p>}
                                {contract.contact_phone && <p className="text-xs">{contract.contact_phone}</p>}
                                {contract.contact_email && <p className="text-xs">{contract.contact_email}</p>}
                              </div>
                            </div>
                          )}
                          
                          <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Billable Services</h4>
                            <div className="flex items-center gap-2">
                              <span className="text-3xl font-bold text-blue-900">{getActiveServicesCount(contract)}</span>
                              <span className="text-sm text-gray-600">active service{getActiveServicesCount(contract) !== 1 ? 's' : ''}</span>
                            </div>
                            {contract.billable_services && contract.billable_services.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {contract.billable_services.filter(s => s.is_active).slice(0, 3).map(service => (
                                  <span key={service.service_code} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono">
                                    {service.service_code}
                                  </span>
                                ))}
                                {getActiveServicesCount(contract) > 3 && (
                                  <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                    +{getActiveServicesCount(contract) - 3} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {contract.notes && (
                          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-700">{contract.notes}</p>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex gap-2 ml-4">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(contract)} data-testid={`edit-contract-${contract.id}`}>
                          <Edit className="text-blue-600" size={18} />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(contract.id)} data-testid={`delete-contract-${contract.id}`}>
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

export default Payers;
