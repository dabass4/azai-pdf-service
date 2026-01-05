import { useState, useEffect } from "react";
import axios from "axios";
import { DollarSign, Plus, Edit, Trash2, X, ChevronDown, ChevronRight, MapPin, Phone, Globe, Building2, FileText, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Payer types
const PAYER_TYPES = ["State", "Managed Care", "MyCare Ohio", "Medicare", "Private"];
const INSURANCE_TYPES = ["Medicaid", "Medicare", "Private", "Workers Comp", "Other"];

// Common billing codes for contracts
const COMMON_BILLING_CODES = [
  { code: "T1019", name: "Personal Care Aide" },
  { code: "T1020", name: "Personal Care (per diem)" },
  { code: "T1021", name: "Home Health Aide" },
  { code: "G0156", name: "Home Health Aide" },
  { code: "G0299", name: "RN Direct Skilled Nursing" },
  { code: "G0300", name: "LPN Direct Skilled Nursing" },
  { code: "T1000", name: "Private Duty Nursing" },
  { code: "T1001", name: "Nursing Assessment" },
  { code: "T1002", name: "RN Waiver Nursing" },
  { code: "T1003", name: "LPN Waiver Nursing" },
  { code: "G0151", name: "Physical Therapy" },
  { code: "G0152", name: "Occupational Therapy" },
  { code: "G0153", name: "Speech Therapy" },
];

const Payers = () => {
  const [payers, setPayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedPayers, setExpandedPayers] = useState({});
  
  // Payer form state
  const [showPayerForm, setShowPayerForm] = useState(false);
  const [editingPayer, setEditingPayer] = useState(null);
  const [payerFormData, setPayerFormData] = useState({
    name: "",
    short_name: "",
    payer_type: "",
    insurance_type: "",
    edi_payer_id: "",
    address: "",
    city: "",
    state: "",
    zip_code: "",
    phone: "",
    website: "",
    notes: "",
    is_active: true
  });
  
  // Contract form state
  const [showContractForm, setShowContractForm] = useState(false);
  const [editingContract, setEditingContract] = useState(null);
  const [contractPayerId, setContractPayerId] = useState(null);
  const [contractFormData, setContractFormData] = useState({
    contract_name: "",
    contract_number: "",
    start_date: "",
    end_date: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    notes: "",
    billable_services: [],
    is_active: true
  });

  useEffect(() => {
    fetchPayers();
  }, []);

  const fetchPayers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/payers`);
      setPayers(response.data);
    } catch (e) {
      console.error("Error fetching payers:", e);
      toast.error("Failed to load payers");
    } finally {
      setLoading(false);
    }
  };

  const handleSeedOhioPayers = async () => {
    try {
      const response = await axios.post(`${API}/payers/seed-ohio`);
      toast.success(`Ohio payers added: ${response.data.added} new, ${response.data.skipped} already exist`);
      fetchPayers();
    } catch (e) {
      console.error("Error seeding payers:", e);
      toast.error("Failed to seed Ohio payers");
    }
  };

  const toggleExpanded = (payerId) => {
    setExpandedPayers(prev => ({ ...prev, [payerId]: !prev[payerId] }));
  };

  // Payer CRUD
  const handlePayerSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingPayer) {
        await axios.put(`${API}/payers/${editingPayer.id}`, payerFormData);
        toast.success("Payer updated");
      } else {
        await axios.post(`${API}/payers`, payerFormData);
        toast.success("Payer created");
      }
      setShowPayerForm(false);
      setEditingPayer(null);
      resetPayerForm();
      fetchPayers();
    } catch (e) {
      console.error("Error saving payer:", e);
      toast.error("Failed to save payer");
    }
  };

  const handleEditPayer = (payer) => {
    setEditingPayer(payer);
    setPayerFormData({
      name: payer.name || "",
      short_name: payer.short_name || "",
      payer_type: payer.payer_type || "",
      insurance_type: payer.insurance_type || "",
      edi_payer_id: payer.edi_payer_id || "",
      address: payer.address || "",
      city: payer.city || "",
      state: payer.state || "",
      zip_code: payer.zip_code || "",
      phone: payer.phone || "",
      website: payer.website || "",
      notes: payer.notes || "",
      is_active: payer.is_active !== false
    });
    setShowPayerForm(true);
  };

  const handleDeletePayer = async (payerId) => {
    if (!window.confirm("Delete this payer and ALL its contracts?")) return;
    try {
      await axios.delete(`${API}/payers/${payerId}`);
      toast.success("Payer deleted");
      fetchPayers();
    } catch (e) {
      toast.error("Failed to delete payer");
    }
  };

  const resetPayerForm = () => {
    setPayerFormData({
      name: "", short_name: "", payer_type: "", insurance_type: "",
      edi_payer_id: "", address: "", city: "", state: "", zip_code: "",
      phone: "", website: "", notes: "", is_active: true
    });
  };

  // Contract CRUD
  const handleContractSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingContract) {
        await axios.put(`${API}/payers/${contractPayerId}/contracts/${editingContract.id}`, contractFormData);
        toast.success("Contract updated");
      } else {
        await axios.post(`${API}/payers/${contractPayerId}/contracts`, contractFormData);
        toast.success("Contract created");
      }
      setShowContractForm(false);
      setEditingContract(null);
      setContractPayerId(null);
      resetContractForm();
      fetchPayers();
    } catch (e) {
      console.error("Error saving contract:", e);
      toast.error("Failed to save contract");
    }
  };

  const handleAddContract = (payerId) => {
    setContractPayerId(payerId);
    setEditingContract(null);
    resetContractForm();
    setShowContractForm(true);
  };

  const handleEditContract = (payerId, contract) => {
    setContractPayerId(payerId);
    setEditingContract(contract);
    setContractFormData({
      contract_name: contract.contract_name || "",
      contract_number: contract.contract_number || "",
      start_date: contract.start_date || "",
      end_date: contract.end_date || "",
      contact_person: contract.contact_person || "",
      contact_phone: contract.contact_phone || "",
      contact_email: contract.contact_email || "",
      notes: contract.notes || "",
      billable_services: contract.billable_services || [],
      is_active: contract.is_active !== false
    });
    setShowContractForm(true);
  };

  const handleDeleteContract = async (payerId, contractId) => {
    if (!window.confirm("Delete this contract?")) return;
    try {
      await axios.delete(`${API}/payers/${payerId}/contracts/${contractId}`);
      toast.success("Contract deleted");
      fetchPayers();
    } catch (e) {
      toast.error("Failed to delete contract");
    }
  };

  const resetContractForm = () => {
    setContractFormData({
      contract_name: "", contract_number: "", start_date: "", end_date: "",
      contact_person: "", contact_phone: "", contact_email: "",
      notes: "", billable_services: [], is_active: true
    });
  };

  const handleServiceToggle = (code) => {
    setContractFormData(prev => {
      const existing = prev.billable_services.find(s => s.service_code === code);
      if (existing) {
        return {
          ...prev,
          billable_services: prev.billable_services.filter(s => s.service_code !== code)
        };
      } else {
        return {
          ...prev,
          billable_services: [...prev.billable_services, { service_code: code, is_active: true }]
        };
      }
    });
  };

  const isServiceSelected = (code) => {
    return contractFormData.billable_services.some(s => s.service_code === code);
  };

  // Group payers by type
  const groupedPayers = payers.reduce((acc, payer) => {
    const type = payer.payer_type || "Other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(payer);
    return acc;
  }, {});

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Payers & Contracts</h1>
          <p className="text-gray-600 mt-1">Manage payers and their time-bound contracts</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSeedOhioPayers} variant="outline" className="border-green-500 text-green-700">
            <MapPin className="mr-2" size={18} />
            Load Ohio Payers
          </Button>
          <Button onClick={() => { setShowPayerForm(true); setEditingPayer(null); resetPayerForm(); }} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="mr-2" size={18} />
            Add Payer
          </Button>
        </div>
      </div>

      {/* Payer Form Modal */}
      {showPayerForm && (
        <Card className="mb-6 border-2 border-blue-200">
          <CardHeader className="bg-blue-50">
            <div className="flex justify-between items-center">
              <CardTitle>{editingPayer ? "Edit Payer" : "Add New Payer"}</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => { setShowPayerForm(false); setEditingPayer(null); }}>
                <X size={20} />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handlePayerSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <Label>Payer Name *</Label>
                  <Input value={payerFormData.name} onChange={(e) => setPayerFormData({...payerFormData, name: e.target.value})} required />
                </div>
                <div>
                  <Label>Short Name</Label>
                  <Input value={payerFormData.short_name} onChange={(e) => setPayerFormData({...payerFormData, short_name: e.target.value})} placeholder="e.g., ODM" />
                </div>
                <div>
                  <Label>Payer Type *</Label>
                  <Select value={payerFormData.payer_type} onValueChange={(v) => setPayerFormData({...payerFormData, payer_type: v})}>
                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                      {PAYER_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Insurance Type *</Label>
                  <Select value={payerFormData.insurance_type} onValueChange={(v) => setPayerFormData({...payerFormData, insurance_type: v})}>
                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                      {INSURANCE_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>EDI Payer ID</Label>
                  <Input value={payerFormData.edi_payer_id} onChange={(e) => setPayerFormData({...payerFormData, edi_payer_id: e.target.value})} placeholder="e.g., 35374" />
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2"><MapPin size={18} /> Claims Mailing Address</h4>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="md:col-span-2">
                    <Label>Address / P.O. Box</Label>
                    <Input value={payerFormData.address} onChange={(e) => setPayerFormData({...payerFormData, address: e.target.value})} />
                  </div>
                  <div>
                    <Label>City</Label>
                    <Input value={payerFormData.city} onChange={(e) => setPayerFormData({...payerFormData, city: e.target.value})} />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label>State</Label>
                      <Input value={payerFormData.state} onChange={(e) => setPayerFormData({...payerFormData, state: e.target.value})} />
                    </div>
                    <div>
                      <Label>ZIP</Label>
                      <Input value={payerFormData.zip_code} onChange={(e) => setPayerFormData({...payerFormData, zip_code: e.target.value})} />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Phone</Label>
                  <Input value={payerFormData.phone} onChange={(e) => setPayerFormData({...payerFormData, phone: e.target.value})} placeholder="1-800-XXX-XXXX" />
                </div>
                <div>
                  <Label>Website</Label>
                  <Input value={payerFormData.website} onChange={(e) => setPayerFormData({...payerFormData, website: e.target.value})} placeholder="example.com" />
                </div>
              </div>
              
              <div>
                <Label>Notes</Label>
                <Input value={payerFormData.notes} onChange={(e) => setPayerFormData({...payerFormData, notes: e.target.value})} placeholder="Disputes address, special instructions..." />
              </div>
              
              <div className="flex items-center gap-2">
                <Switch checked={payerFormData.is_active} onCheckedChange={(c) => setPayerFormData({...payerFormData, is_active: c})} />
                <Label>Payer Active</Label>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => { setShowPayerForm(false); setEditingPayer(null); }}>Cancel</Button>
                <Button type="submit" className="bg-blue-600">{editingPayer ? "Update Payer" : "Create Payer"}</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Contract Form Modal */}
      {showContractForm && (
        <Card className="mb-6 border-2 border-green-200">
          <CardHeader className="bg-green-50">
            <div className="flex justify-between items-center">
              <CardTitle>{editingContract ? "Edit Contract" : "Add New Contract"}</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => { setShowContractForm(false); setEditingContract(null); }}>
                <X size={20} />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handleContractSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Contract Name</Label>
                  <Input value={contractFormData.contract_name} onChange={(e) => setContractFormData({...contractFormData, contract_name: e.target.value})} placeholder="e.g., 2025 Rate Agreement" />
                </div>
                <div>
                  <Label>Contract Number</Label>
                  <Input value={contractFormData.contract_number} onChange={(e) => setContractFormData({...contractFormData, contract_number: e.target.value})} />
                </div>
                <div>
                  <Label>Start Date *</Label>
                  <Input type="date" value={contractFormData.start_date} onChange={(e) => setContractFormData({...contractFormData, start_date: e.target.value})} required />
                </div>
                <div>
                  <Label>End Date</Label>
                  <Input type="date" value={contractFormData.end_date} onChange={(e) => setContractFormData({...contractFormData, end_date: e.target.value})} />
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Your Contact (Internal)</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>Contact Person</Label>
                    <Input value={contractFormData.contact_person} onChange={(e) => setContractFormData({...contractFormData, contact_person: e.target.value})} />
                  </div>
                  <div>
                    <Label>Phone</Label>
                    <Input value={contractFormData.contact_phone} onChange={(e) => setContractFormData({...contractFormData, contact_phone: e.target.value})} />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input type="email" value={contractFormData.contact_email} onChange={(e) => setContractFormData({...contractFormData, contact_email: e.target.value})} />
                  </div>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Billable Services ({contractFormData.billable_services.length} selected)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-48 overflow-y-auto p-2 bg-gray-50 rounded">
                  {COMMON_BILLING_CODES.map(bc => (
                    <label key={bc.code} className={`flex items-center p-2 rounded cursor-pointer text-sm ${isServiceSelected(bc.code) ? 'bg-blue-100 border border-blue-300' : 'bg-white border'}`}>
                      <input type="checkbox" checked={isServiceSelected(bc.code)} onChange={() => handleServiceToggle(bc.code)} className="mr-2" />
                      <span className="font-mono text-blue-700 font-semibold">{bc.code}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <Label>Notes</Label>
                <Input value={contractFormData.notes} onChange={(e) => setContractFormData({...contractFormData, notes: e.target.value})} placeholder="Contract-specific notes..." />
              </div>
              
              <div className="flex items-center gap-2">
                <Switch checked={contractFormData.is_active} onCheckedChange={(c) => setContractFormData({...contractFormData, is_active: c})} />
                <Label>Contract Active</Label>
              </div>
              
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => { setShowContractForm(false); setEditingContract(null); }}>Cancel</Button>
                <Button type="submit" className="bg-green-600">{editingContract ? "Update Contract" : "Create Contract"}</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Payers List */}
      {loading ? (
        <div className="text-center py-12">Loading payers...</div>
      ) : payers.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <Building2 className="mx-auto text-gray-400 mb-4" size={64} />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No Payers Yet</h3>
            <p className="text-gray-500 mb-4">Add your first payer or load Ohio Medicaid payers</p>
            <Button onClick={handleSeedOhioPayers} variant="outline" className="border-green-500 text-green-700">
              <MapPin className="mr-2" size={18} />
              Load Ohio Payers
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {Object.entries(groupedPayers).map(([type, payerList]) => (
            <div key={type}>
              <h2 className="text-lg font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${type === 'State' ? 'bg-purple-500' : type === 'Managed Care' ? 'bg-blue-500' : type === 'MyCare Ohio' ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                {type} ({payerList.length})
              </h2>
              <div className="space-y-3">
                {payerList.map(payer => (
                  <Card key={payer.id} className="overflow-hidden">
                    {/* Payer Header */}
                    <div 
                      className="p-4 bg-white cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                      onClick={() => toggleExpanded(payer.id)}
                    >
                      <div className="flex items-center gap-4 flex-1">
                        {expandedPayers[payer.id] ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-lg">{payer.name}</h3>
                            {payer.short_name && <span className="text-sm text-gray-500">({payer.short_name})</span>}
                            <span className={`px-2 py-0.5 rounded text-xs ${payer.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                              {payer.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                            {payer.phone && (
                              <span className="flex items-center gap-1">
                                <Phone size={14} />
                                <a href={`tel:${payer.phone}`} className="text-blue-600 hover:underline" onClick={e => e.stopPropagation()}>{payer.phone}</a>
                              </span>
                            )}
                            {payer.edi_payer_id && <span className="font-mono">ID: {payer.edi_payer_id}</span>}
                            {payer.address && (
                              <span className="flex items-center gap-1 text-xs">
                                <MapPin size={12} />
                                {payer.address}, {payer.city}, {payer.state} {payer.zip_code}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                        <Button size="sm" onClick={() => handleAddContract(payer.id)} className="bg-green-600 hover:bg-green-700 text-white">
                          <Plus size={14} className="mr-1" /> Add Contract
                        </Button>
                        <span className="text-sm text-gray-500 mx-2">{payer.contracts?.length || 0} contract(s)</span>
                        <Button size="sm" variant="ghost" onClick={() => handleEditPayer(payer)}><Edit size={16} /></Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDeletePayer(payer.id)}><Trash2 size={16} className="text-red-500" /></Button>
                      </div>
                    </div>
                    
                    {/* Expanded: Contracts */}
                    {expandedPayers[payer.id] && (
                      <div className="border-t bg-gray-50 p-4">
                        {payer.notes && (
                          <p className="text-sm text-gray-600 mb-4 p-2 bg-yellow-50 rounded">{payer.notes}</p>
                        )}
                        
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-gray-700">Contracts</h4>
                          <Button size="sm" onClick={() => handleAddContract(payer.id)} className="bg-green-600 hover:bg-green-700">
                            <Plus size={16} className="mr-1" /> Add Contract
                          </Button>
                        </div>
                        
                        {(!payer.contracts || payer.contracts.length === 0) ? (
                          <p className="text-sm text-gray-500 italic">No contracts yet. Click "Add Contract" to create one.</p>
                        ) : (
                          <div className="space-y-2">
                            {payer.contracts.map(contract => (
                              <div key={contract.id} className="bg-white p-3 rounded border flex justify-between items-center">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <FileText size={16} className="text-blue-600" />
                                    <span className="font-semibold">{contract.contract_name || contract.contract_number || "Unnamed Contract"}</span>
                                    <span className={`px-2 py-0.5 rounded text-xs ${contract.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                      {contract.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                  </div>
                                  <div className="text-sm text-gray-600 flex items-center gap-4 mt-1">
                                    <span className="flex items-center gap-1">
                                      <Calendar size={14} />
                                      {contract.start_date} - {contract.end_date || "Ongoing"}
                                    </span>
                                    <span>{contract.billable_services?.length || 0} services</span>
                                  </div>
                                </div>
                                <div className="flex gap-1">
                                  <Button size="sm" variant="ghost" onClick={() => handleEditContract(payer.id, contract)}><Edit size={14} /></Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleDeleteContract(payer.id, contract.id)}><Trash2 size={14} className="text-red-500" /></Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Payers;
