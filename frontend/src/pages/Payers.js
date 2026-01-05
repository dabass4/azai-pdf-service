import { useState, useEffect } from "react";
import axios from "axios";
import { DollarSign, Plus, Edit, Trash2, X, ToggleLeft, ToggleRight, MapPin, Phone, Globe, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Ohio Payer Directory with Official Addresses
const OHIO_PAYERS = {
  // State Agencies
  "ODM": {
    name: "Ohio Department of Medicaid",
    type: "State",
    category: "state",
    address: "P.O. Box 182709",
    city: "Columbus",
    state: "OH",
    zip: "43218-2709",
    phone: "1-800-686-1516",
    website: "medicaid.ohio.gov",
    payerId: "OHMED",
    notes: "Provider Hotline: 1-800-686-1516, Consumer: 1-800-324-8680"
  },
  "DODD": {
    name: "Ohio Department of Developmental Disabilities",
    type: "State",
    category: "state",
    address: "30 E Broad St, 13th Floor",
    city: "Columbus",
    state: "OH",
    zip: "43215",
    phone: "1-800-617-6733",
    website: "dodd.ohio.gov",
    payerId: "DODD",
    notes: "Electronic claims only via PAWS system"
  },
  // Managed Care Organizations
  "AmeriHealth": {
    name: "AmeriHealth Caritas Ohio",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 7346",
    city: "London",
    state: "KY",
    zip: "40742",
    phone: "1-800-575-4114",
    website: "amerihealthcaritasoh.com",
    payerId: "35374",
    notes: "Claims Disputes: P.O. Box 7126, London, KY 40742"
  },
  "Anthem": {
    name: "Anthem Blue Cross Blue Shield",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 105187",
    city: "Atlanta",
    state: "GA",
    zip: "30348-5187",
    phone: "1-855-223-0747",
    website: "anthem.com",
    payerId: "OHBCBS",
    notes: "Electronic claims preferred via EDI"
  },
  "Buckeye": {
    name: "Buckeye Health Plan",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 6200",
    city: "Farmington",
    state: "MO",
    zip: "63640",
    phone: "1-866-246-4358",
    website: "buckeyehealthplan.com",
    payerId: "BUCKEYE",
    notes: "Main office: 4349 Easton Way, Columbus, OH 43219"
  },
  "CareSource": {
    name: "CareSource",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 8738",
    city: "Dayton",
    state: "OH",
    zip: "45401-8738",
    phone: "1-800-488-0134",
    website: "caresource.com",
    payerId: "31114",
    notes: "Electronic claims via Provider Portal preferred"
  },
  "Humana": {
    name: "Humana Healthy Horizons",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 14601",
    city: "Lexington",
    state: "KY",
    zip: "40512-4601",
    phone: "1-800-282-4548",
    website: "humana.com",
    payerId: "HUMANA",
    notes: "Provider Relations: OHMedicaidProviderRelations@humana.com"
  },
  "Molina": {
    name: "Molina Healthcare of Ohio",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 22712",
    city: "Long Beach",
    state: "CA",
    zip: "90801",
    phone: "1-800-578-0775",
    website: "molinahealthcare.com",
    payerId: "20149",
    notes: "Disputes: P.O. Box 349020, Columbus, OH 43234-9020"
  },
  "UHC": {
    name: "UnitedHealthcare Community Plan",
    type: "Managed Care",
    category: "mco",
    address: "P.O. Box 31364",
    city: "Salt Lake City",
    state: "UT",
    zip: "84131",
    phone: "1-800-600-9007",
    website: "uhccommunityplan.com",
    payerId: "87726",
    notes: "Appeals Fax: (801) 994-1082"
  },
  // MyCare Ohio (Dual Eligible)
  "Aetna-MyCare": {
    name: "Aetna Better Health (MyCare Ohio)",
    type: "MyCare Ohio",
    category: "mycare",
    address: "P.O. Box 982966",
    city: "El Paso",
    state: "TX",
    zip: "79998-2966",
    phone: "1-855-364-0974",
    website: "aetnabetterhealth.com/ohio",
    payerId: "50023",
    notes: "Grievances: P.O. Box 818070, Cleveland, OH 44181"
  },
  "Buckeye-MyCare": {
    name: "Buckeye Community Health Plan (MyCare Ohio)",
    type: "MyCare Ohio",
    category: "mycare",
    address: "P.O. Box 6200",
    city: "Farmington",
    state: "MO",
    zip: "63640",
    phone: "1-866-246-4358",
    website: "buckeyehealthplan.com",
    payerId: "BUCKEYE-MC",
    notes: "Same as Buckeye Health Plan"
  },
  "CareSource-MyCare": {
    name: "CareSource (MyCare Ohio)",
    type: "MyCare Ohio",
    category: "mycare",
    address: "P.O. Box 8738",
    city: "Dayton",
    state: "OH",
    zip: "45401-8738",
    phone: "1-855-475-3163",
    website: "caresource.com",
    payerId: "31114-MC",
    notes: "MyCare Ohio dual eligible program"
  },
  "Molina-MyCare": {
    name: "Molina Dual Options (MyCare Ohio)",
    type: "MyCare Ohio",
    category: "mycare",
    address: "P.O. Box 22712",
    city: "Long Beach",
    state: "CA",
    zip: "90801",
    phone: "1-855-665-4623",
    website: "molinahealthcare.com",
    payerId: "20149-MC",
    notes: "Molina MyCare Ohio dual eligible"
  },
  "UHC-MyCare": {
    name: "UnitedHealthcare (MyCare Ohio)",
    type: "MyCare Ohio",
    category: "mycare",
    address: "P.O. Box 31364",
    city: "Salt Lake City",
    state: "UT",
    zip: "84131",
    phone: "1-877-542-9236",
    website: "uhccommunityplan.com",
    payerId: "87726-MC",
    notes: "UHC MyCare Ohio dual eligible"
  }
};

// Ohio Medicaid Billable Services (Complete list from RhinoBill)
const OHIO_MEDICAID_SERVICES = [
  // Therapy Services
  { code: "G0151", name: "Physical Therapy", description: "Physical therapy services", category: "Therapy" },
  { code: "G0152", name: "Occupational Therapy", description: "Occupational therapy services", category: "Therapy" },
  { code: "G0153", name: "Speech Therapy", description: "Speech-language pathology services", category: "Therapy" },
  
  // Nursing Services
  { code: "G0154", name: "LPN Services", description: "Direct skilled services of a licensed practical nurse", category: "Nursing", modifier: "LPN" },
  { code: "G0154", name: "RN Services", description: "Direct skilled services of a registered nurse", category: "Nursing", modifier: "RN" },
  { code: "G0156", name: "Home Health Aide", description: "Aide, Medicare Certified Agency", category: "Nursing" },
  { code: "G0299", name: "RN Direct Skilled Nursing", description: "Direct skilled nursing services of a registered nurse", category: "Nursing" },
  { code: "G0300", name: "LPN Direct Skilled Nursing", description: "Direct skilled nursing services of a licensed practical nurse", category: "Nursing" },
  
  // Waiver Nursing
  { code: "G0493", name: "Waiver Nursing Delegation/Assessment (RN)", description: "Waiver Nursing Delegation/Assessment by a Registered Nurse", category: "Waiver Nursing", modifier: "Assessment" },
  { code: "G0493", name: "Waiver Nursing Delegation/Consultation (RN)", description: "Waiver Nursing Delegation/Consultation by a Registered Nurse", category: "Waiver Nursing", modifier: "Consultation" },
  { code: "G0494", name: "Waiver Nursing Delegation/Consultation (LPN)", description: "Waiver Nursing Delegation/Consultation by a Licensed Practical Nurse", category: "Waiver Nursing" },
  
  // Supplemental Services
  { code: "S0215", name: "Supplemental Transportation", description: "Non-emergency transportation", category: "Supplemental" },
  
  // Day Care Services
  { code: "S5101", name: "Day Care Services (½ day)", description: "Adult day care services per half day", category: "Day Care" },
  { code: "S5102", name: "Day Care Services (full day)", description: "Adult day care services per full day", category: "Day Care" },
  { code: "S5150", name: "Adult Day Care (half day)", description: "Adult day care per half day", category: "Day Care" },
  { code: "S5151", name: "Adult Day Care (per diem)", description: "Adult day care per diem", category: "Day Care" },
  
  // Meal Services
  { code: "S5170", name: "Delivered Meals (Therapeutic)", description: "Home delivered meals - therapeutic or kosher", category: "Meals", modifier: "Therapeutic" },
  { code: "S5170", name: "Delivered Meals", description: "Home delivered meals", category: "Meals" },
  
  // PDN (Private Duty Nursing)
  { code: "T1000", name: "PDN - LPN", description: "Private Duty Nursing - Licensed Practical Nurse per 15 minutes", category: "PDN", modifier: "LPN" },
  { code: "T1000", name: "PDN - RN", description: "Private Duty Nursing - Registered Nurse per 15 minutes", category: "PDN", modifier: "RN" },
  
  // Assessment & Consultation
  { code: "T1001", name: "RN Assessment", description: "Nursing assessment/evaluation per visit", category: "Assessment", modifier: "Assessment" },
  { code: "T1001", name: "RN Consultation", description: "Nursing consultation per visit", category: "Assessment", modifier: "Consultation" },
  
  // Waiver Nursing T-Codes
  { code: "T1002", name: "RN Waiver Nursing", description: "RN services per diem", category: "Waiver Nursing" },
  { code: "T1003", name: "LPN/LVN Waiver Nursing", description: "LPN/LVN services", category: "Waiver Nursing", modifier: "LPN/LVN" },
  { code: "T1003", name: "Waiver Nursing LPN", description: "LPN waiver nursing services", category: "Waiver Nursing", modifier: "LPN" },
  { code: "T1004", name: "Behavioral Health Services", description: "Services of a qualified behavioral health aide per 15 minutes", category: "Behavioral Health" },
  { code: "T1005", name: "Respite Care", description: "Respite care services per diem", category: "Respite" },
  
  // Personal Care
  { code: "T1019", name: "Personal Care Aide", description: "Personal care services per 15 minutes", category: "Personal Care" },
  { code: "T1020", name: "Personal Care Services (per diem)", description: "Personal care services per diem", category: "Personal Care" },
  { code: "T1021", name: "Home Health Aide (per visit)", description: "Home health aide services per visit", category: "Personal Care" },
  
  // Attendant Care
  { code: "S5125", name: "Attendant Care Services", description: "Attendant care services", category: "Personal Care" },
  { code: "S5126", name: "Attendant Care (per 15 min)", description: "Attendant care services per 15 minutes", category: "Personal Care" },
  
  // Homemaker
  { code: "S5130", name: "Homemaker Services", description: "Homemaker services", category: "Personal Care" },
  { code: "S5131", name: "Homemaker (per 15 min)", description: "Homemaker services per 15 minutes", category: "Personal Care" },
  
  // Other Services
  { code: "T1502", name: "Home Management Training", description: "Administration of oral, intramuscular and/or subcutaneous medication per 15 minutes", category: "Training" },
  { code: "T1999", name: "Miscellaneous Therapeutic", description: "Miscellaneous therapeutic items and supplies per 15 minutes", category: "Other" },
  { code: "T2003", name: "Non-Emergency Transportation (encounter)", description: "Non-emergency transportation encounter/trip", category: "Transportation" },
  { code: "T2004", name: "Non-Emergency Transportation (per diem)", description: "Non-emergency transportation per diem", category: "Transportation" },
  { code: "T2024", name: "Service Assessment", description: "Service assessment/plan of care development per 15 minutes", category: "Assessment" },
  { code: "T2025", name: "Waiver Services", description: "Waiver services per 15 minutes", category: "Waiver" },
  { code: "T2031", name: "Assisted Living (monthly)", description: "Assisted living services per month", category: "Residential" },
  { code: "T2032", name: "Residential Care (per diem)", description: "Residential care services per diem", category: "Residential" },
  { code: "T2033", name: "Community Transition", description: "Community transition services per service", category: "Transition" },
  { code: "A0130", name: "Non-Emergency Transport (wheelchair)", description: "Non-emergency transportation: wheelchair van", category: "Transportation" },
  { code: "S9122", name: "Home Health Aide (hourly)", description: "Home health aide services per hour", category: "Personal Care" },
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
    payer_id: "",
    payer_address: "",
    payer_city: "",
    payer_state: "",
    payer_zip: "",
    payer_phone: "",
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
                  
                  {/* Quick Select Ohio Payer */}
                  <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <Label className="text-blue-800 font-semibold mb-2 flex items-center gap-2">
                      <Building2 size={18} />
                      Quick Select: Ohio Payer
                    </Label>
                    <Select 
                      onValueChange={(payerKey) => {
                        if (payerKey && OHIO_PAYERS[payerKey]) {
                          const payer = OHIO_PAYERS[payerKey];
                          setFormData(prev => ({
                            ...prev,
                            payer_name: payer.name,
                            insurance_type: payer.type === "State" ? "Medicaid" : "Medicaid",
                            payer_address: payer.address,
                            payer_city: payer.city,
                            payer_state: payer.state,
                            payer_zip: payer.zip,
                            payer_phone: payer.phone,
                            payer_id: payer.payerId,
                            notes: payer.notes
                          }));
                          toast.success(`Loaded ${payer.name} with official address`);
                        }
                      }}
                    >
                      <SelectTrigger className="bg-white" data-testid="ohio-payer-select">
                        <SelectValue placeholder="Select an Ohio payer to auto-fill address..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="header-state" disabled className="font-bold text-gray-500">— State Agencies —</SelectItem>
                        {Object.entries(OHIO_PAYERS).filter(([_, p]) => p.category === "state").map(([key, payer]) => (
                          <SelectItem key={key} value={key}>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{payer.name}</span>
                              <span className="text-xs text-gray-500">({payer.payerId})</span>
                            </div>
                          </SelectItem>
                        ))}
                        <SelectItem value="header-mco" disabled className="font-bold text-gray-500">— Managed Care —</SelectItem>
                        {Object.entries(OHIO_PAYERS).filter(([_, p]) => p.category === "mco").map(([key, payer]) => (
                          <SelectItem key={key} value={key}>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{payer.name}</span>
                              <span className="text-xs text-gray-500">({payer.payerId})</span>
                            </div>
                          </SelectItem>
                        ))}
                        <SelectItem value="header-mycare" disabled className="font-bold text-gray-500">— MyCare Ohio —</SelectItem>
                        {Object.entries(OHIO_PAYERS).filter(([_, p]) => p.category === "mycare").map(([key, payer]) => (
                          <SelectItem key={key} value={key}>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{payer.name}</span>
                              <span className="text-xs text-gray-500">({payer.payerId})</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
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
                      <Label htmlFor="payer_id">Payer ID / EDI ID</Label>
                      <Input
                        id="payer_id"
                        name="payer_id"
                        value={formData.payer_id || ""}
                        onChange={handleInputChange}
                        placeholder="e.g., 35374"
                        data-testid="payer-id-input"
                      />
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
                  </div>
                  
                  {/* Payer Address */}
                  <div className="mt-4 pt-4 border-t">
                    <Label className="text-base font-semibold mb-3 flex items-center gap-2">
                      <MapPin size={18} />
                      Payer Address (Claims Submission)
                    </Label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <Label htmlFor="payer_address">Street Address / P.O. Box</Label>
                        <Input
                          id="payer_address"
                          name="payer_address"
                          value={formData.payer_address || ""}
                          onChange={handleInputChange}
                          placeholder="e.g., P.O. Box 182709"
                          data-testid="payer-address-input"
                        />
                      </div>
                      <div>
                        <Label htmlFor="payer_city">City</Label>
                        <Input
                          id="payer_city"
                          name="payer_city"
                          value={formData.payer_city || ""}
                          onChange={handleInputChange}
                          placeholder="e.g., Columbus"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <Label htmlFor="payer_state">State</Label>
                          <Input
                            id="payer_state"
                            name="payer_state"
                            value={formData.payer_state || ""}
                            onChange={handleInputChange}
                            placeholder="OH"
                          />
                        </div>
                        <div>
                          <Label htmlFor="payer_zip">ZIP</Label>
                          <Input
                            id="payer_zip"
                            name="payer_zip"
                            value={formData.payer_zip || ""}
                            onChange={handleInputChange}
                            placeholder="43218"
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="payer_phone">Phone</Label>
                        <Input
                          id="payer_phone"
                          name="payer_phone"
                          value={formData.payer_phone || ""}
                          onChange={handleInputChange}
                          placeholder="1-800-XXX-XXXX"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex items-center space-x-2">
                    <Label htmlFor="is_active">Contract Active</Label>
                    <Switch
                      id="is_active"
                      checked={formData.is_active}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
                      data-testid="is-active-switch"
                    />
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
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">Billable Services (Ohio Medicaid HCPCS Codes)</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Toggle services that are billable under this contract. 
                    <span className="font-medium"> {formData.billable_services.filter(s => s.is_active).length} of {OHIO_MEDICAID_SERVICES.length}</span> services enabled.
                  </p>
                  <div className="border border-gray-200 rounded-lg bg-gray-50 max-h-[500px] overflow-y-auto">
                    {/* Group services by category */}
                    {Object.entries(
                      OHIO_MEDICAID_SERVICES.reduce((acc, service) => {
                        const cat = service.category || 'Other';
                        if (!acc[cat]) acc[cat] = [];
                        acc[cat].push(service);
                        return acc;
                      }, {})
                    ).map(([category, services]) => (
                      <div key={category} className="border-b border-gray-200 last:border-b-0">
                        <div className="bg-gray-100 px-4 py-2 sticky top-0">
                          <h4 className="font-semibold text-gray-700 text-sm">{category}</h4>
                        </div>
                        <div className="p-2 space-y-1">
                          {services.map((service, idx) => {
                            const uniqueKey = `${service.code}-${service.modifier || idx}`;
                            return (
                              <div 
                                key={uniqueKey} 
                                className="flex items-center justify-between p-3 bg-white rounded border border-gray-200 hover:bg-blue-50 transition-colors" 
                                data-testid={`service-${service.code}`}
                              >
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono text-sm font-semibold text-blue-700">{service.code}</span>
                                    {service.modifier && (
                                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded font-medium">
                                        {service.modifier}
                                      </span>
                                    )}
                                    <span className="font-medium text-gray-900 text-sm">{service.name}</span>
                                  </div>
                                  <p className="text-xs text-gray-500 mt-1">{service.description}</p>
                                </div>
                                <Switch
                                  checked={isServiceActive(service.code)}
                                  onCheckedChange={() => handleServiceToggle(service.code)}
                                  data-testid={`toggle-${service.code}`}
                                />
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
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
